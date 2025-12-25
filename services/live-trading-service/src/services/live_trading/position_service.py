"""
Position Management Service

Handles position tracking and P&L calculations for live trades.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from .models import LivePosition, LiveTrade, PositionStatus, TradeStatus, StrategyType

logger = logging.getLogger(__name__)


@dataclass
class PositionLeg:
    """Position leg data."""
    leg_id: str
    action: str
    option_type: str
    strike_price: float
    expiration_date: datetime
    quantity: int
    premium: float
    current_price: Optional[float] = None


@dataclass
class PositionGreeks:
    """Position Greeks data."""
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0


class PositionService:
    """Service for managing trading positions."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the position management service."""
        self.db_session = db_session
    
    async def create_position(self, account_id: str, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new position.
        
        Args:
            account_id: Trading account ID
            position_data: Position data
            
        Returns:
            Position creation result
        """
        try:
            # Validate position data
            validation_result = await self._validate_position_data(position_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid position data",
                    "details": validation_result["errors"]
                }
            
            # Create position record
            position = LivePosition(
                account_id=account_id,
                symbol=position_data["symbol"],
                strategy=StrategyType(position_data["strategy"]),
                quantity=position_data["total_quantity"],
                average_price=Decimal(str(position_data.get("net_premium", 0))),
                current_price=Decimal(str(position_data.get("current_mark", 0))),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN,
                opened_at=datetime.utcnow(),
                expiration_date=position_data.get("expiration_date"),
                legs_data=json.dumps(position_data.get("legs", [])),
                greeks_data=json.dumps(position_data.get("greeks", {}))
            )
            
            self.db_session.add(position)
            await self.db_session.flush()  # Get the ID
            
            logger.info(f"Position created successfully: {position.position_id}")
            
            return {
                "success": True,
                "position_id": str(position.position_id),
                "status": "OPEN",
                "created_at": position.opened_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Position creation error: {str(e)}")
            return {
                "success": False,
                "error": "Position creation failed",
                "details": str(e)
            }
    
    async def update_position(self, position_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing position.
        
        Args:
            position_id: Position ID
            update_data: Update data
            
        Returns:
            Position update result
        """
        try:
            # Get position
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            # Update position fields
            if "mark_prices" in update_data:
                await self._update_position_mark_prices(position, update_data["mark_prices"])
            
            if "greeks" in update_data:
                position.greeks_data = json.dumps(update_data["greeks"])
            
            if "current_price" in update_data:
                position.current_price = Decimal(str(update_data["current_price"]))
            
            # Recalculate P&L
            await self._recalculate_position_pnl(position)
            
            await self.db_session.commit()
            
            logger.info(f"Position updated successfully: {position_id}")
            
            return {
                "success": True,
                "position_id": position_id,
                "status": "UPDATED",
                "updated_at": position.updated_at.isoformat(),
                "changes": list(update_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Position update error: {str(e)}")
            return {
                "success": False,
                "error": "Position update failed",
                "details": str(e)
            }
    
    async def get_position(self, position_id: str) -> Dict[str, Any]:
        """
        Get position details.
        
        Args:
            position_id: Position ID
            
        Returns:
            Position details
        """
        try:
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            # Parse legs and Greeks data
            legs = json.loads(position.legs_data) if position.legs_data else []
            greeks = json.loads(position.greeks_data) if position.greeks_data else {}
            
            return {
                "success": True,
                "position": {
                    "position_id": str(position.position_id),
                    "account_id": str(position.account_id),
                    "symbol": position.symbol,
                    "strategy": position.strategy.value,
                    "quantity": position.quantity,
                    "average_price": float(position.average_price),
                    "current_price": float(position.current_price) if position.current_price else None,
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "realized_pnl": float(position.realized_pnl),
                    "total_pnl": float(position.unrealized_pnl + position.realized_pnl),
                    "status": position.status.value,
                    "opened_at": position.opened_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None,
                    "expiration_date": position.expiration_date.isoformat() if position.expiration_date else None,
                    "legs": legs,
                    "greeks": greeks
                }
            }
            
        except Exception as e:
            logger.error(f"Get position error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to get position",
                "details": str(e)
            }
    
    async def get_positions(self, account_id: str, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all positions for an account.
        
        Args:
            account_id: Account ID
            status_filter: Optional status filter
            
        Returns:
            Positions list
        """
        try:
            query = select(LivePosition).where(LivePosition.account_id == account_id)
            
            if status_filter:
                query = query.where(LivePosition.status == status_filter)
            
            query = query.order_by(LivePosition.opened_at.desc())
            
            result = await self.db_session.execute(query)
            positions = result.scalars().all()
            
            positions_list = []
            total_unrealized_pnl = Decimal("0.00")
            
            for position in positions:
                legs = json.loads(position.legs_data) if position.legs_data else []
                greeks = json.loads(position.greeks_data) if position.greeks_data else {}
                
                # Handle NULL values safely
                unrealized = float(position.unrealized_pnl) if position.unrealized_pnl is not None else 0.0
                realized = float(position.realized_pnl) if position.realized_pnl is not None else 0.0
                
                total_unrealized_pnl += Decimal(str(unrealized))
                
                positions_list.append({
                    "position_id": str(position.position_id),
                    "symbol": position.symbol,
                    "strategy": position.strategy.value,
                    "quantity": position.quantity,
                    "average_price": float(position.average_price),
                    "current_price": float(position.current_price) if position.current_price else None,
                    "unrealized_pnl": unrealized,
                    "realized_pnl": realized,
                    "total_pnl": unrealized + realized,
                    "status": position.status.value,
                    "opened_at": position.opened_at.isoformat(),
                    "expiration_date": position.expiration_date.isoformat() if position.expiration_date else None,
                    "legs_count": len(legs),
                    "greeks": greeks
                })
            
            return {
                "success": True,
                "positions": positions_list,
                "total_count": len(positions_list),
                "total_unrealized_pnl": float(total_unrealized_pnl)
            }
            
        except Exception as e:
            logger.error(f"Get positions error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to get positions",
                "details": str(e)
            }
    
    async def close_position(self, position_id: str, close_reason: str = "Manual") -> Dict[str, Any]:
        """
        Close a position.
        
        Args:
            position_id: Position ID
            close_reason: Reason for closing
            
        Returns:
            Position closure result
        """
        try:
            # Get position
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            if position.status != PositionStatus.OPEN:
                return {
                    "success": False,
                    "error": f"Position cannot be closed, current status: {position.status.value}"
                }
            
            # Calculate final P&L
            await self._recalculate_position_pnl(position)
            
            # Update position status
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.utcnow()
            
            # Realize the P&L
            position.realized_pnl = position.unrealized_pnl
            position.unrealized_pnl = Decimal("0.00")
            
            await self.db_session.commit()
            
            logger.info(f"Position closed successfully: {position_id}")
            
            return {
                "success": True,
                "position_id": position_id,
                "status": "CLOSED",
                "realized_pnl": float(position.realized_pnl),
                "closed_at": position.closed_at.isoformat(),
                "close_reason": close_reason
            }
            
        except Exception as e:
            logger.error(f"Close position error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to close position",
                "details": str(e)
            }
    
    async def calculate_pnl(self, position_id: str) -> Dict[str, Any]:
        """
        Calculate P&L for a position.
        
        Args:
            position_id: Position ID
            
        Returns:
            P&L calculation result
        """
        try:
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            # Recalculate P&L
            await self._recalculate_position_pnl(position)
            
            await self.db_session.commit()
            
            return {
                "success": True,
                "position_id": position_id,
                "unrealized_pnl": float(position.unrealized_pnl),
                "realized_pnl": float(position.realized_pnl),
                "total_pnl": float(position.unrealized_pnl + position.realized_pnl),
                "current_mark": float(position.current_price) if position.current_price else None,
                "cost_basis": float(position.average_price),
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Calculate P&L error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to calculate P&L",
                "details": str(e)
            }
    
    async def mark_to_market(self, position_id: str) -> Dict[str, Any]:
        """
        Mark position to market prices.
        
        Args:
            position_id: Position ID
            
        Returns:
            Mark-to-market result
        """
        try:
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            # Get current market prices for position legs
            legs = json.loads(position.legs_data) if position.legs_data else []
            mark_prices = await self._get_current_market_prices(position.symbol, legs)
            
            # Update position with current prices
            await self._update_position_mark_prices(position, mark_prices)
            
            # Recalculate P&L
            await self._recalculate_position_pnl(position)
            
            await self.db_session.commit()
            
            return {
                "success": True,
                "position_id": position_id,
                "mark_prices": mark_prices,
                "current_mark": float(position.current_price) if position.current_price else None,
                "unrealized_pnl": float(position.unrealized_pnl),
                "mark_updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Mark to market error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to mark to market",
                "details": str(e)
            }
    
    async def calculate_greeks(self, position_id: str) -> Dict[str, Any]:
        """
        Calculate Greeks for a position.
        
        Args:
            position_id: Position ID
            
        Returns:
            Greeks calculation result
        """
        try:
            position = await self._get_position(position_id)
            if not position:
                return {
                    "success": False,
                    "error": "Position not found"
                }
            
            # Get position legs
            legs = json.loads(position.legs_data) if position.legs_data else []
            
            # Calculate total Greeks
            total_greeks = await self._calculate_position_greeks(position.symbol, legs)
            
            # Update position
            position.greeks_data = json.dumps(total_greeks.__dict__)
            
            await self.db_session.commit()
            
            return {
                "success": True,
                "position_id": position_id,
                "greeks": total_greeks.__dict__,
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Calculate Greeks error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to calculate Greeks",
                "details": str(e)
            }
    
    # Private helper methods
    
    async def _validate_position_data(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate position data."""
        errors = []
        
        required_fields = ["symbol", "strategy", "total_quantity"]
        for field in required_fields:
            if field not in position_data:
                errors.append(f"{field} is required")
        
        if position_data.get("total_quantity", 0) <= 0:
            errors.append("Total quantity must be positive")
        
        if not position_data.get("legs"):
            errors.append("Position legs are required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _get_position(self, position_id: str) -> Optional[LivePosition]:
        """Get position by ID."""
        try:
            result = await self.db_session.execute(
                select(LivePosition).where(LivePosition.position_id == position_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting position: {str(e)}")
            return None
    
    async def _update_position_mark_prices(self, position: LivePosition, mark_prices: List[float]):
        """Update position with current mark prices."""
        if mark_prices:
            # Calculate weighted average current price
            legs = json.loads(position.legs_data) if position.legs_data else []
            total_value = 0
            total_quantity = 0
            
            for i, leg in enumerate(legs):
                if i < len(mark_prices):
                    leg_value = leg["quantity"] * mark_prices[i]
                    total_value += leg_value
                    total_quantity += abs(leg["quantity"])
            
            if total_quantity > 0:
                position.current_price = Decimal(str(total_value / total_quantity))
    
    async def _recalculate_position_pnl(self, position: LivePosition):
        """Recalculate position P&L."""
        try:
            if position.current_price and position.average_price:
                # Simple P&L calculation: (current_price - average_price) * quantity
                price_diff = position.current_price - position.average_price
                position.unrealized_pnl = price_diff * position.quantity
            else:
                position.unrealized_pnl = Decimal("0.00")
                
        except Exception as e:
            logger.error(f"Error recalculating P&L: {str(e)}")
            position.unrealized_pnl = Decimal("0.00")
    
    async def _get_current_market_prices(self, symbol: str, legs: List[Dict[str, Any]]) -> List[float]:
        """Get current market prices for position legs."""
        # This would integrate with market data service
        # For now, return mock prices
        return [1.25, 0.50, 1.00, 0.50]  # Mock prices for 4-leg position
    
    async def _calculate_position_greeks(self, symbol: str, legs: List[Dict[str, Any]]) -> PositionGreeks:
        """Calculate total Greeks for position."""
        # This would integrate with options pricing service
        # For now, return mock Greeks
        return PositionGreeks(
            delta=0.15,
            gamma=-0.05,
            theta=-0.25,
            vega=0.10,
            rho=0.02
        )
    
    async def update_position_after_cancellation(self, position_id: str, trade: LiveTrade):
        """Update position after trade cancellation."""
        # This would adjust position quantities after cancellation
        logger.info(f"Updating position {position_id} after trade cancellation")
    
    async def update_position_from_fill(self, position_id: str, fill_data: Dict[str, Any]):
        """Update position from trade fill."""
        # This would adjust position based on filled trade
        logger.info(f"Updating position {position_id} from trade fill")
