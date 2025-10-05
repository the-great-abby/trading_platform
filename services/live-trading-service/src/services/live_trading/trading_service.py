"""
Trading Service

Handles live trading operations and order execution.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from .models import LiveTrade, LivePosition, TradeStatus, OrderStatus, TradeAction, StrategyType
from .public_api_client import PublicAPIClient
from .risk_service import RiskService, OrderRiskData
from .position_service import PositionService

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


@dataclass
class TradeLeg:
    """Individual trade leg for multi-leg strategies."""
    action: TradeAction
    option_type: Optional[str] = None
    strike_price: Optional[float] = None
    expiration_date: Optional[datetime] = None
    quantity: int = 1
    premium: Optional[float] = None


@dataclass
class OrderRequest:
    """Order request data."""
    account_id: str
    symbol: str
    strategy: StrategyType
    legs: List[TradeLeg]
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    time_in_force: str = "DAY"
    estimated_premium: float = 0.0
    estimated_risk: float = 0.0
    greeks: Dict[str, float] = None


class TradingService:
    """Service for executing live trades."""
    
    def __init__(self, db_session: AsyncSession, public_api_client: PublicAPIClient, risk_service: RiskService, position_service: PositionService):
        """Initialize the trading service."""
        self.db_session = db_session
        self.public_api_client = public_api_client
        self.risk_service = risk_service
        self.position_service = position_service
    
    async def execute_order(self, account_id: str, order_data: OrderRequest) -> Dict[str, Any]:
        """
        Execute an order through the trading system.
        
        Args:
            account_id: Trading account ID
            order_data: Order request data
            
        Returns:
            Order execution result
        """
        try:
            # Validate order data
            validation_result = await self._validate_order_data(order_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid order data",
                    "details": validation_result["errors"]
                }
            
            # Risk validation
            risk_data = OrderRiskData(
                symbol=order_data.symbol,
                strategy=order_data.strategy.value,
                quantity=sum(leg.quantity for leg in order_data.legs),
                estimated_premium=order_data.estimated_premium,
                estimated_risk=order_data.estimated_risk,
                greeks=order_data.greeks or {},
                position_size=order_data.estimated_premium
            )
            
            risk_result = await self.risk_service.validate_order(account_id, risk_data)
            if not risk_result.approved:
                return {
                    "success": False,
                    "error": "Risk validation failed",
                    "details": risk_result.errors,
                    "warnings": risk_result.warnings
                }
            
            # Create trade record
            trade = await self._create_trade_record(account_id, order_data)
            
            try:
                # Submit order to Public.com
                order_response = await self._submit_order_to_public(account_id, order_data, trade)
                
                # Update trade with order response
                await self._update_trade_with_order_response(trade, order_response)
                
                # Create position if needed
                if order_response.get("status") == "SUBMITTED":
                    await self._create_or_update_position(account_id, trade, order_data)
                
                await self.db_session.commit()
                
                logger.info(f"Order executed successfully: {trade.trade_id}")
                
                return {
                    "success": True,
                    "trade_id": str(trade.trade_id),
                    "public_order_id": trade.public_order_id,
                    "status": trade.status.value,
                    "filled_quantity": trade.filled_quantity,
                    "remaining_quantity": trade.remaining_quantity,
                    "warnings": risk_result.warnings
                }
                
            except Exception as e:
                # Update trade status to rejected
                trade.status = TradeStatus.REJECTED
                trade.rejection_reason = str(e)
                await self.db_session.commit()
                
                logger.error(f"Order execution failed: {str(e)}")
                
                return {
                    "success": False,
                    "error": "Order execution failed",
                    "details": str(e),
                    "trade_id": str(trade.trade_id)
                }
            
        except Exception as e:
            logger.error(f"Trading service error: {str(e)}")
            return {
                "success": False,
                "error": "Trading service error",
                "details": str(e)
            }
    
    async def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            account_id: Trading account ID
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            # Get trade record
            trade = await self._get_trade_by_order_id(order_id)
            if not trade:
                return {
                    "success": False,
                    "error": "Order not found"
                }
            
            # Check if order can be cancelled
            if trade.status in [TradeStatus.FILLED, TradeStatus.CANCELLED, TradeStatus.EXPIRED]:
                return {
                    "success": False,
                    "error": f"Order cannot be cancelled, current status: {trade.status.value}"
                }
            
            # Cancel order on Public.com
            cancel_response = await self.public_api_client.cancel_order(account_id, order_id)
            
            # Update trade status
            trade.status = TradeStatus.CANCELLED
            trade.cancelled_at = datetime.utcnow()
            
            # Update position if needed
            if trade.position_id:
                await self.position_service.update_position_after_cancellation(str(trade.position_id), trade)
            
            await self.db_session.commit()
            
            logger.info(f"Order cancelled successfully: {order_id}")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": "CANCELLED",
                "cancelled_at": trade.cancelled_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Order cancellation error: {str(e)}")
            return {
                "success": False,
                "error": "Order cancellation failed",
                "details": str(e)
            }
    
    async def get_order_status(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """
        Get order status from Public.com and update local records.
        
        Args:
            account_id: Trading account ID
            order_id: Order ID
            
        Returns:
            Order status information
        """
        try:
            # Get trade record
            trade = await self._get_trade_by_order_id(order_id)
            if not trade:
                return {
                    "success": False,
                    "error": "Order not found"
                }
            
            # Get status from Public.com
            status_response = await self.public_api_client.get_order_status(account_id, order_id)
            
            # Update trade record
            await self._update_trade_from_public_status(trade, status_response)
            
            # Create order status history record
            await self._create_order_status_record(trade, status_response)
            
            # Update position if filled
            if status_response.get("status") == "FILLED" and trade.position_id:
                await self.position_service.update_position_from_fill(str(trade.position_id), status_response)
            
            await self.db_session.commit()
            
            return {
                "success": True,
                "order_id": order_id,
                "status": trade.status.value,
                "filled_quantity": trade.filled_quantity,
                "remaining_quantity": trade.remaining_quantity,
                "average_price": float(trade.price) if trade.price else None,
                "last_updated": trade.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get order status error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to get order status",
                "details": str(e)
            }
    
    async def get_account_orders(self, account_id: str, status_filter: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get orders for an account.
        
        Args:
            account_id: Trading account ID
            status_filter: Optional status filter
            limit: Maximum number of orders to return
            
        Returns:
            Orders list
        """
        try:
            query = select(LiveTrade).where(LiveTrade.account_id == account_id)
            
            if status_filter:
                query = query.where(LiveTrade.status == status_filter)
            
            query = query.order_by(LiveTrade.created_at.desc()).limit(limit)
            
            result = await self.db_session.execute(query)
            trades = result.scalars().all()
            
            orders = []
            for trade in trades:
                orders.append({
                    "trade_id": str(trade.trade_id),
                    "public_order_id": trade.public_order_id,
                    "symbol": trade.symbol,
                    "strategy": trade.strategy.value if trade.strategy else None,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "price": float(trade.price),
                    "status": trade.status.value,
                    "filled_quantity": trade.filled_quantity,
                    "remaining_quantity": trade.remaining_quantity,
                    "created_at": trade.created_at.isoformat(),
                    "filled_at": trade.filled_at.isoformat() if trade.filled_at else None
                })
            
            return {
                "success": True,
                "orders": orders,
                "total_count": len(orders)
            }
            
        except Exception as e:
            logger.error(f"Get account orders error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to get orders",
                "details": str(e)
            }
    
    # Private helper methods
    
    async def _validate_order_data(self, order_data: OrderRequest) -> Dict[str, Any]:
        """Validate order data."""
        errors = []
        
        if not order_data.symbol:
            errors.append("Symbol is required")
        
        if not order_data.legs or len(order_data.legs) == 0:
            errors.append("At least one trade leg is required")
        
        if order_data.estimated_premium < 0:
            errors.append("Estimated premium cannot be negative")
        
        if order_data.estimated_risk < 0:
            errors.append("Estimated risk cannot be negative")
        
        # Validate legs
        for i, leg in enumerate(order_data.legs):
            if leg.quantity <= 0:
                errors.append(f"Leg {i+1}: Quantity must be positive")
            
            if leg.action == TradeAction.BUY and leg.premium is None:
                errors.append(f"Leg {i+1}: Premium is required for BUY orders")
            
            if leg.action == TradeAction.SELL and leg.premium is None:
                errors.append(f"Leg {i+1}: Premium is required for SELL orders")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _create_trade_record(self, account_id: str, order_data: OrderRequest) -> LiveTrade:
        """Create trade record in database."""
        trade = LiveTrade(
            account_id=account_id,
            public_order_id=f"TEMP_{datetime.utcnow().timestamp()}",
            symbol=order_data.symbol,
            action=TradeAction.BUY,  # Will be updated based on legs
            quantity=sum(leg.quantity for leg in order_data.legs),
            price=Decimal(str(order_data.estimated_premium)),
            total_amount=Decimal(str(order_data.estimated_premium)),
            remaining_quantity=sum(leg.quantity for leg in order_data.legs),
            strategy=order_data.strategy,
            leg_data=json.dumps([self._leg_to_dict(leg) for leg in order_data.legs])
        )
        
        self.db_session.add(trade)
        await self.db_session.flush()  # Get the ID
        
        return trade
    
    async def _submit_order_to_public(self, account_id: str, order_data: OrderRequest, trade: LiveTrade) -> Dict[str, Any]:
        """Submit order to Public.com API."""
        # Convert order data to Public.com format
        public_order = {
            "symbol": order_data.symbol,
            "side": "buy",  # Will be determined by strategy
            "quantity": trade.quantity,
            "type": order_data.order_type.value.lower(),
            "time_in_force": order_data.time_in_force.lower(),
            "strategy": order_data.strategy.value.lower(),
            "legs": [self._leg_to_public_format(leg) for leg in order_data.legs]
        }
        
        if order_data.limit_price:
            public_order["price"] = order_data.limit_price
        
        # Submit to Public.com
        response = await self.public_api_client.submit_order(account_id, public_order)
        
        return response
    
    async def _update_trade_with_order_response(self, trade: LiveTrade, order_response: Dict[str, Any]):
        """Update trade record with order response from Public.com."""
        trade.public_order_id = order_response.get("order_id", trade.public_order_id)
        
        # Map Public.com status to our status
        status_mapping = {
            "submitted": TradeStatus.SUBMITTED,
            "filled": TradeStatus.FILLED,
            "partially_filled": TradeStatus.PARTIALLY_FILLED,
            "cancelled": TradeStatus.CANCELLED,
            "rejected": TradeStatus.REJECTED,
            "expired": TradeStatus.EXPIRED
        }
        
        public_status = order_response.get("status", "pending").lower()
        trade.status = status_mapping.get(public_status, TradeStatus.PENDING)
        
        trade.filled_quantity = order_response.get("filled_quantity", 0)
        trade.remaining_quantity = order_response.get("remaining_quantity", trade.quantity)
        
        if order_response.get("average_price"):
            trade.price = Decimal(str(order_response["average_price"]))
        
        if trade.status == TradeStatus.FILLED:
            trade.filled_at = datetime.utcnow()
        elif trade.status == TradeStatus.REJECTED:
            trade.rejection_reason = order_response.get("rejection_reason", "Unknown rejection reason")
    
    async def _create_or_update_position(self, account_id: str, trade: LiveTrade, order_data: OrderRequest):
        """Create or update position based on trade."""
        # This would integrate with the position service
        # For now, just log the action
        logger.info(f"Creating/updating position for trade {trade.trade_id}")
    
    async def _get_trade_by_order_id(self, order_id: str) -> Optional[LiveTrade]:
        """Get trade record by order ID."""
        try:
            result = await self.db_session.execute(
                select(LiveTrade).where(LiveTrade.public_order_id == order_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting trade by order ID: {str(e)}")
            return None
    
    async def _update_trade_from_public_status(self, trade: LiveTrade, status_response: Dict[str, Any]):
        """Update trade record from Public.com status response."""
        # Map status
        status_mapping = {
            "submitted": TradeStatus.SUBMITTED,
            "filled": TradeStatus.FILLED,
            "partially_filled": TradeStatus.PARTIALLY_FILLED,
            "cancelled": TradeStatus.CANCELLED,
            "rejected": TradeStatus.REJECTED,
            "expired": TradeStatus.EXPIRED
        }
        
        public_status = status_response.get("status", "pending").lower()
        trade.status = status_mapping.get(public_status, trade.status)
        
        # Update quantities and prices
        if "filled_quantity" in status_response:
            trade.filled_quantity = status_response["filled_quantity"]
        
        if "remaining_quantity" in status_response:
            trade.remaining_quantity = status_response["remaining_quantity"]
        
        if "average_price" in status_response:
            trade.price = Decimal(str(status_response["average_price"]))
        
        # Update timestamps
        if trade.status == TradeStatus.FILLED and not trade.filled_at:
            trade.filled_at = datetime.utcnow()
    
    async def _create_order_status_record(self, trade: LiveTrade, status_response: Dict[str, Any]):
        """Create order status history record."""
        status_record = OrderStatus(
            trade_id=trade.trade_id,
            order_id=trade.public_order_id,
            status=trade.status,
            status_message=status_response.get("status_message"),
            filled_quantity=status_response.get("filled_quantity", 0),
            remaining_quantity=status_response.get("remaining_quantity", trade.remaining_quantity),
            average_price=Decimal(str(status_response["average_price"])) if status_response.get("average_price") else None,
            external_status=json.dumps(status_response)
        )
        
        self.db_session.add(status_record)
    
    def _leg_to_dict(self, leg: TradeLeg) -> Dict[str, Any]:
        """Convert trade leg to dictionary."""
        return {
            "action": leg.action.value,
            "option_type": leg.option_type,
            "strike_price": leg.strike_price,
            "expiration_date": leg.expiration_date.isoformat() if leg.expiration_date else None,
            "quantity": leg.quantity,
            "premium": leg.premium
        }
    
    def _leg_to_public_format(self, leg: TradeLeg) -> Dict[str, Any]:
        """Convert trade leg to Public.com API format."""
        return {
            "side": leg.action.value.lower(),
            "quantity": leg.quantity,
            "option_type": leg.option_type,
            "strike_price": leg.strike_price,
            "expiration_date": leg.expiration_date.isoformat() if leg.expiration_date else None,
            "premium": leg.premium
        }
