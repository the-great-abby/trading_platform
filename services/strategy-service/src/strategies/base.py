"""
Base strategy class for all trading strategies
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from ..core.types import TradeSignal


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.is_active = True
        
    @abstractmethod
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """
        Generate trading signal based on market data
        
        Args:
            symbol: Trading symbol
            data: Market data dataframe with technical indicators
            historical_date: Historical date (YYYY-MM-DD) for backtesting, or None for current date
            
        Returns:
            TradeSignal or None if no signal
        """
        pass
    
    def calculate_position_size(self, capital: float, price: float, risk_percentage: float = 0.02) -> float:
        """Calculate position size based on risk management"""
        risk_amount = capital * risk_percentage
        position_size = risk_amount / price
        return position_size
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "is_active": self.is_active,
            "config": self.config
        }
    
    def activate(self):
        """Activate the strategy"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate the strategy"""
        self.is_active = False 