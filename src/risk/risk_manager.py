"""
Risk management system for the trading bot
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from ..core.types import TradeSignal
from ..models.portfolio import Portfolio
from ..utils.config import Config


class RiskManager:
    """Risk management system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
    async def validate_signal(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Validate a trading signal against risk rules"""
        try:
            # Check if daily loss limit exceeded
            if not self._check_daily_loss_limit():
                logger.warning("Daily loss limit exceeded")
                return False
            
            # Check position size limits
            if not self._check_position_size(signal, portfolio):
                logger.warning("Position size exceeds limits")
                return False
            
            # Check maximum positions
            if not self._check_max_positions(portfolio):
                logger.warning("Maximum positions limit reached")
                return False
            
            # Check portfolio concentration
            if not self._check_concentration(signal, portfolio):
                logger.warning("Portfolio concentration limit exceeded")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
    
    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit is exceeded"""
        current_date = datetime.now().date()
        
        # Reset daily metrics if it's a new day
        if current_date > self.last_reset_date:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
        
        # Check if daily loss exceeds limit
        max_daily_loss = self.config.initial_capital * self.config.max_daily_loss
        return self.daily_loss <= max_daily_loss
    
    def _check_position_size(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Check if position size is within limits"""
        position_value = signal.quantity * signal.price
        max_position_value = portfolio.total_value * self.config.max_position_size
        
        return position_value <= max_position_value
    
    def _check_max_positions(self, portfolio: Portfolio) -> bool:
        """Check if maximum number of positions is reached"""
        return len(portfolio.positions) < self.config.max_positions
    
    def _check_concentration(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Check portfolio concentration limits"""
        # Calculate what the new position would add to portfolio
        new_position_value = signal.quantity * signal.price
        total_portfolio_value = portfolio.total_value + new_position_value
        
        # Check if any single position would exceed 20% of portfolio
        max_concentration = 0.20
        return new_position_value / total_portfolio_value <= max_concentration
    
    def update_daily_loss(self, pnl: float):
        """Update daily loss tracking"""
        self.daily_loss += abs(pnl) if pnl < 0 else 0
        self.daily_trades += 1
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            "daily_loss": self.daily_loss,
            "daily_trades": self.daily_trades,
            "max_daily_loss": self.config.initial_capital * self.config.max_daily_loss,
            "daily_loss_remaining": (self.config.initial_capital * self.config.max_daily_loss) - self.daily_loss
        } 