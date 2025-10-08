"""
Trading API Routes

Handles live trading operations and order management.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.database import get_db_session
from src.services.live_trading.public_api_client import PublicAPIClient
from src.services.live_trading.trading_service import TradingService, OrderRequest, TradeLeg, OrderType
from src.services.live_trading.risk_service import RiskService, OrderRiskData
from src.services.live_trading.position_service import PositionService
from src.services.live_trading.market_hours_service import MarketHoursService
from src.services.live_trading.models import StrategyType, TradeAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])


# Pydantic models
class TradeLegRequest(BaseModel):
    """Trade leg request model."""
    action: str = Field(..., description="Trade action (BUY or SELL)")
    option_type: Optional[str] = Field(None, description="Option type (CALL or PUT)")
    strike_price: Optional[float] = Field(None, description="Strike price")
    expiration_date: Optional[str] = Field(None, description="Expiration date (ISO format)")
    quantity: int = Field(..., description="Quantity")
    premium: Optional[float] = Field(None, description="Premium")


class OrderRequestModel(BaseModel):
    """Order request model."""
    symbol: str = Field(..., description="Trading symbol")
    strategy: str = Field(..., description="Strategy type")
    legs: List[TradeLegRequest] = Field(..., description="Trade legs")
    order_type: str = Field(default="MARKET", description="Order type")
    limit_price: Optional[float] = Field(None, description="Limit price")
    time_in_force: str = Field(default="DAY", description="Time in force")
    estimated_premium: float = Field(..., description="Estimated premium")
    estimated_risk: float = Field(..., description="Estimated risk")
    greeks: Optional[Dict[str, float]] = Field(None, description="Greeks")


class OrderResponse(BaseModel):
    """Order response model."""
    success: bool = Field(..., description="Success status")
    trade_id: Optional[str] = Field(None, description="Trade ID")
    public_order_id: Optional[str] = Field(None, description="Public.com order ID")
    status: Optional[str] = Field(None, description="Order status")
    filled_quantity: Optional[int] = Field(None, description="Filled quantity")
    remaining_quantity: Optional[int] = Field(None, description="Remaining quantity")
    warnings: Optional[List[str]] = Field(None, description="Warnings")
    error: Optional[str] = Field(None, description="Error message")
    details: Optional[List[str]] = Field(None, description="Error details")


class OrderStatusResponse(BaseModel):
    """Order status response model."""
    success: bool = Field(..., description="Success status")
    order_id: Optional[str] = Field(None, description="Order ID")
    status: Optional[str] = Field(None, description="Order status")
    filled_quantity: Optional[int] = Field(None, description="Filled quantity")
    remaining_quantity: Optional[int] = Field(None, description="Remaining quantity")
    average_price: Optional[float] = Field(None, description="Average price")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp")
    error: Optional[str] = Field(None, description="Error message")


class OrdersListResponse(BaseModel):
    """Orders list response model."""
    success: bool = Field(..., description="Success status")
    orders: List[Dict[str, Any]] = Field(..., description="Orders list")
    total_count: int = Field(..., description="Total number of orders")
    error: Optional[str] = Field(None, description="Error message")


@router.post("/orders", response_model=OrderResponse)
async def submit_order(
    account_id: str,
    order_request: OrderRequestModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit a trading order.
    
    Args:
        account_id: Account ID
        order_request: Order request data
        
    Returns:
        Order submission result
    """
    try:
        # Check if we're in paper trading mode
        import os
        if os.getenv("TRADING_MODE") == "paper" or os.getenv("ENVIRONMENT") == "paper":
            # For paper trading, create actual database records
            try:
                # Create a paper trading order record
                order_id = f"paper_order_{int(datetime.utcnow().timestamp())}"
                total_quantity = sum(leg.quantity for leg in order_request.legs)
                
                # Insert order into database
                await db.execute(text("""
                    INSERT INTO paper_trading_orders (
                        order_id, account_id, symbol, strategy, order_type,
                        total_quantity, estimated_premium, estimated_risk,
                        status, created_at, filled_at, filled_quantity,
                        average_price, remaining_quantity, greeks_data
                    ) VALUES (
                        :order_id, :account_id, :symbol, :strategy, :order_type,
                        :total_quantity, :estimated_premium, :estimated_risk,
                        :status, :created_at, :filled_at, :filled_quantity,
                        :average_price, :remaining_quantity, :greeks_data
                    )
                """), {
                    "order_id": order_id,
                    "account_id": account_id,
                    "symbol": order_request.symbol,
                    "strategy": order_request.strategy,
                    "order_type": order_request.order_type,
                    "total_quantity": total_quantity,
                    "estimated_premium": order_request.estimated_premium,
                    "estimated_risk": order_request.estimated_risk,
                    "status": "FILLED",
                    "created_at": datetime.utcnow(),
                    "filled_at": datetime.utcnow(),
                    "filled_quantity": total_quantity,
                    "average_price": order_request.estimated_premium,
                    "remaining_quantity": 0,
                    "greeks_data": json.dumps(order_request.greeks or {})
                })
                
                # Insert trade legs
                for i, leg in enumerate(order_request.legs):
                    await db.execute(text("""
                        INSERT INTO paper_trading_order_legs (
                            order_id, leg_number, action, option_type, strike_price,
                            expiration_date, quantity, premium
                        ) VALUES (
                            :order_id, :leg_number, :action, :option_type, :strike_price,
                            :expiration_date, :quantity, :premium
                        )
                    """), {
                        "order_id": order_id,
                        "leg_number": i + 1,
                        "action": leg.action,
                        "option_type": leg.option_type,
                        "strike_price": leg.strike_price,
                        "expiration_date": leg.expiration_date.isoformat() if leg.expiration_date and hasattr(leg.expiration_date, 'isoformat') else leg.expiration_date,
                        "quantity": leg.quantity,
                        "premium": leg.premium
                    })
                
                await db.commit()
                
                return OrderResponse(
                    success=True,
                    order_id=order_id,
                    status="FILLED",
                    filled_quantity=total_quantity,
                    remaining_quantity=0,
                    average_price=order_request.estimated_premium,
                    warnings=[]
                )
                
            except Exception as e:
                logger.error(f"Error creating paper trading order: {e}")
                await db.rollback()
                return OrderResponse(
                    success=False,
                    error="Failed to create paper trading order",
                    details=[str(e)]
                )
        
        # Check market hours
        market_hours_service = MarketHoursService()
        market_status = await market_hours_service.get_market_status()
        
        if not market_status.is_open:
            return OrderResponse(
                success=False,
                error="Trading not allowed",
                details=[f"Market is closed: {market_status.reason}"]
            )
        
        # Get stored credentials
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id AND c.is_active = true
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            return OrderResponse(
                success=False,
                error="Account not found or not authenticated",
                details=["Account must be connected to Public.com"]
            )
        
        # Create API client and authenticate
        api_client = PublicAPIClient()
        
        # Check if token is expired and refresh if needed
        if account_data[3] and account_data[3] <= datetime.utcnow():
            logger.info(f"Token expired for account {account_id}, refreshing...")
            refresh_token = api_client._decrypt_data(account_data[2])
            api_client.refresh_token = refresh_token
            await api_client.refresh_access_token()
        else:
            access_token = api_client._decrypt_data(account_data[1])
            api_client.access_token = access_token
            api_client.is_authenticated = True
            api_client.client.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
        
        # Create services
        risk_service = RiskService(db)
        position_service = PositionService(db)
        trading_service = TradingService(db, api_client, risk_service, position_service)
        
        # Convert request to internal format
        trade_legs = []
        for leg in order_request.legs:
            trade_legs.append(TradeLeg(
                action=TradeAction(leg.action),
                option_type=leg.option_type,
                strike_price=leg.strike_price,
                expiration_date=datetime.fromisoformat(leg.expiration_date) if leg.expiration_date else None,
                quantity=leg.quantity,
                premium=leg.premium
            ))
        
        order_data = OrderRequest(
            account_id=account_id,
            symbol=order_request.symbol,
            strategy=StrategyType(order_request.strategy),
            legs=trade_legs,
            order_type=OrderType(order_request.order_type),
            limit_price=order_request.limit_price,
            time_in_force=order_request.time_in_force,
            estimated_premium=order_request.estimated_premium,
            estimated_risk=order_request.estimated_risk,
            greeks=order_request.greeks or {}
        )
        
        # Execute order
        result = await trading_service.execute_order(account_id, order_data)
        
        return OrderResponse(**result)
        
    except Exception as e:
        logger.error(f"Error submitting order: {str(e)}")
        return OrderResponse(
            success=False,
            error="Order submission failed",
            details=[str(e)]
        )


@router.get("/orders/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(
    account_id: str,
    order_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get order status.
    
    Args:
        account_id: Account ID
        order_id: Order ID
        
    Returns:
        Order status information
    """
    try:
        # Get stored credentials
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id AND c.is_active = true
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            return OrderStatusResponse(
                success=False,
                error="Account not found or not authenticated"
            )
        
        # Create API client and authenticate
        api_client = PublicAPIClient()
        
        # Check if token is expired and refresh if needed
        if account_data[3] and account_data[3] <= datetime.utcnow():
            logger.info(f"Token expired for account {account_id}, refreshing...")
            refresh_token = api_client._decrypt_data(account_data[2])
            api_client.refresh_token = refresh_token
            await api_client.refresh_access_token()
        else:
            access_token = api_client._decrypt_data(account_data[1])
            api_client.access_token = access_token
            api_client.is_authenticated = True
            api_client.client.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
        
        # Create services
        risk_service = RiskService(db)
        position_service = PositionService(db)
        trading_service = TradingService(db, api_client, risk_service, position_service)
        
        # Get order status
        result = await trading_service.get_order_status(account_id, order_id)
        
        return OrderStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting order status: {str(e)}")
        return OrderStatusResponse(
            success=False,
            error="Failed to get order status",
            details=str(e)
        )


@router.delete("/orders/{order_id}")
async def cancel_order(
    account_id: str,
    order_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Cancel an order.
    
    Args:
        account_id: Account ID
        order_id: Order ID to cancel
        
    Returns:
        Cancellation result
    """
    try:
        # Get stored credentials
        result = await db.execute(text("""
            SELECT 
                a.public_account_id,
                c.access_token,
                c.refresh_token,
                c.token_expires_at
            FROM live_trading_accounts a
            JOIN api_credentials c ON a.account_id = c.account_id
            WHERE a.account_id = :account_id AND c.is_active = true
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        
        if not account_data:
            return {
                "success": False,
                "error": "Account not found or not authenticated"
            }
        
        # Create API client and authenticate
        api_client = PublicAPIClient()
        
        # Check if token is expired and refresh if needed
        if account_data[3] and account_data[3] <= datetime.utcnow():
            logger.info(f"Token expired for account {account_id}, refreshing...")
            refresh_token = api_client._decrypt_data(account_data[2])
            api_client.refresh_token = refresh_token
            await api_client.refresh_access_token()
        else:
            access_token = api_client._decrypt_data(account_data[1])
            api_client.access_token = access_token
            api_client.is_authenticated = True
            api_client.client.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
        
        # Create services
        risk_service = RiskService(db)
        position_service = PositionService(db)
        trading_service = TradingService(db, api_client, risk_service, position_service)
        
        # Cancel order
        result = await trading_service.cancel_order(account_id, order_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        return {
            "success": False,
            "error": "Failed to cancel order",
            "details": str(e)
        }


@router.get("/orders", response_model=OrdersListResponse)
async def get_account_orders(
    account_id: str,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get orders for an account.
    
    Args:
        account_id: Account ID
        status_filter: Optional status filter
        limit: Maximum number of orders to return
        
    Returns:
        Orders list
    """
    try:
        # Always query live_trades table (contains real stock trades)
        query = """
            SELECT 
                trade_id, public_order_id, symbol, strategy, action,
                quantity, price, commission, status, created_at,
                filled_at, rejection_reason
            FROM live_trades 
            WHERE account_id = :account_id
        """
        params = {"account_id": account_id}
        
        if status_filter:
            query += " AND status = :status_filter"
            params["status_filter"] = status_filter
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        result = await db.execute(text(query), params)
        trades = result.fetchall()
        
        orders_list = []
        for trade in trades:
            orders_list.append({
                "order_id": str(trade[0]),  # trade_id
                "public_order_id": trade[1],
                "symbol": trade[2],
                "strategy": trade[3],
                "order_type": "MARKET",  # Default
                "action": trade[4],
                "quantity": trade[5],
                "price": float(trade[6]) if trade[6] else 0.0,
                "average_price": float(trade[6]) if trade[6] else 0.0,
                "commission": float(trade[7]) if trade[7] else 0.0,
                "status": trade[8],
                "created_at": trade[9].isoformat() if trade[9] else None,
                "filled_at": trade[10].isoformat() if trade[10] else None,
                "rejection_reason": trade[11],
                "greeks": {}
            })
        
        return OrdersListResponse(
            success=True,
            orders=orders_list,
            total_count=len(orders_list),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error getting account orders: {str(e)}")
        return OrdersListResponse(
            success=False,
            orders=[],
            total_count=0,
            error=f"Failed to get orders: {str(e)}"
        )


@router.get("/positions")
async def get_positions(
    account_id: str,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get positions for an account.
    
    Args:
        account_id: Account ID
        status_filter: Optional status filter
        
    Returns:
        Positions list
    """
    try:
        # Create position service
        position_service = PositionService(db)
        
        # Get positions
        result = await position_service.get_positions(account_id, status_filter)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get positions: {str(e)}",
            "positions": [],
            "total_count": 0
        }


@router.post("/positions/{position_id}/close")
async def close_position(
    account_id: str,
    position_id: str,
    close_reason: str = "Manual",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Close a position.
    
    Args:
        account_id: Account ID
        position_id: Position ID
        close_reason: Reason for closing
        
    Returns:
        Position closure result
    """
    try:
        # Create position service
        position_service = PositionService(db)
        
        # Close position
        result = await position_service.close_position(position_id, close_reason)
        
        return result
        
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to close position: {str(e)}"
        }
