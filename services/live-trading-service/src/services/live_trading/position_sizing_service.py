"""
Position Sizing Service

Calculates optimal position sizes based on buying power, risk limits, and signal confidence.
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

logger = logging.getLogger(__name__)


class PositionSizingService:
    """Service for calculating position sizes based on buying power and risk."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the position sizing service."""
        self.db_session = db_session
    
    async def calculate_position_size(
        self,
        account_id: str,
        symbol: str,
        current_price: float,
        signal_confidence: float,
        max_position_pct: float = 0.15  # Default 15% max position size
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on buying power and risk.
        
        Args:
            account_id: Trading account ID
            symbol: Stock symbol
            current_price: Current price per share
            signal_confidence: Signal confidence (0.0 to 1.0)
            max_position_pct: Maximum position size as % of portfolio (default 15%)
            
        Returns:
            Dict with position size details
        """
        try:
            # Get account buying power and equity
            result = await self.db_session.execute(text("""
                SELECT 
                    cash_balance,
                    equity,
                    buying_power
                FROM live_trading_accounts
                WHERE account_id = :account_id
            """), {"account_id": account_id})
            
            account_data = result.fetchone()
            
            if not account_data:
                logger.warning(f"No account data found for {account_id}, using defaults")
                cash_balance = 4000.0
                equity = 0.0
                buying_power = 4000.0
            else:
                cash_balance = float(account_data[0]) if account_data[0] else 4000.0
                equity = float(account_data[1]) if account_data[1] else 0.0
                buying_power = float(account_data[2]) if account_data[2] else cash_balance
            
            # Portfolio value = cash + equity
            portfolio_value = cash_balance + equity
            
            # Use buying power for position sizing (can be higher than cash if margin available)
            available_capital = buying_power
            
            # Calculate max position value based on risk limit
            max_position_value = portfolio_value * max_position_pct
            
            # Adjust by signal confidence (higher confidence = larger position)
            # Scale from 50% to 100% of max based on confidence
            confidence_multiplier = 0.5 + (signal_confidence * 0.5)
            target_position_value = max_position_value * confidence_multiplier
            
            # Ensure we don't exceed available buying power
            target_position_value = min(target_position_value, available_capital)
            
            # Calculate number of shares
            quantity = int(target_position_value / current_price) if current_price > 0 else 0
            
            # Ensure at least 1 share if we have enough buying power
            if quantity == 0 and available_capital >= current_price:
                quantity = 1
            
            # Calculate actual position value and percentage
            actual_position_value = quantity * current_price
            actual_position_pct = (actual_position_value / portfolio_value) if portfolio_value > 0 else 0
            
            logger.info(f"📊 Position size for {symbol}:")
            logger.info(f"   Portfolio value: ${portfolio_value:.2f}")
            logger.info(f"   Buying power: ${buying_power:.2f}")
            logger.info(f"   Signal confidence: {signal_confidence:.2%}")
            logger.info(f"   Max position: {max_position_pct:.2%} = ${max_position_value:.2f}")
            logger.info(f"   Target (confidence adjusted): ${target_position_value:.2f}")
            logger.info(f"   → {quantity} shares @ ${current_price:.2f} = ${actual_position_value:.2f} ({actual_position_pct:.2%})")
            
            return {
                "quantity": quantity,
                "estimated_cost": actual_position_value,
                "position_pct": actual_position_pct,
                "portfolio_value": portfolio_value,
                "buying_power": buying_power,
                "available_capital": available_capital,
                "confidence_used": signal_confidence,
                "can_afford": quantity > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate position size: {e}", exc_info=True)
            # Return conservative defaults on error
            return {
                "quantity": 1,
                "estimated_cost": current_price,
                "position_pct": 0.0,
                "portfolio_value": 0.0,
                "buying_power": 0.0,
                "available_capital": 0.0,
                "confidence_used": signal_confidence,
                "can_afford": True,
                "error": str(e)
            }
    
    async def validate_buying_power(
        self,
        account_id: str,
        required_capital: float
    ) -> Dict[str, Any]:
        """
        Check if account has sufficient buying power for a trade.
        
        Args:
            account_id: Trading account ID
            required_capital: Required capital for trade
            
        Returns:
            Dict with validation result
        """
        try:
            result = await self.db_session.execute(text("""
                SELECT buying_power, cash_balance
                FROM live_trading_accounts
                WHERE account_id = :account_id
            """), {"account_id": account_id})
            
            account_data = result.fetchone()
            
            if not account_data:
                return {
                    "approved": False,
                    "message": "Account not found",
                    "buying_power": 0.0,
                    "required": required_capital
                }
            
            buying_power = float(account_data[0]) if account_data[0] else 0.0
            cash_balance = float(account_data[1]) if account_data[1] else 0.0
            
            # Check both buying power and cash balance
            has_buying_power = buying_power >= required_capital
            has_cash = cash_balance >= required_capital
            
            if has_buying_power:
                return {
                    "approved": True,
                    "message": f"Sufficient buying power: ${buying_power:.2f} >= ${required_capital:.2f}",
                    "buying_power": buying_power,
                    "cash_balance": cash_balance,
                    "required": required_capital,
                    "uses_margin": not has_cash
                }
            else:
                return {
                    "approved": False,
                    "message": f"Insufficient buying power: ${buying_power:.2f} < ${required_capital:.2f}",
                    "buying_power": buying_power,
                    "cash_balance": cash_balance,
                    "required": required_capital
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to validate buying power: {e}")
            return {
                "approved": False,
                "message": f"Validation error: {str(e)}",
                "error": str(e)
            }
