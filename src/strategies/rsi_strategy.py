"""
Relative Strength Index (RSI) Strategy
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from .base import BaseStrategy
from ..core.types import TradeSignal


class RSIStrategy(BaseStrategy):
    """Relative Strength Index Strategy"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs):
        super().__init__("RSI_Strategy", kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signal based on RSI"""
        if data.empty or len(data) < self.period + 1:
            return None
        
        # Get latest RSI value
        current_rsi = data['RSI'].iloc[-1]
        previous_rsi = data['RSI'].iloc[-2]
        current_price = data['Close'].iloc[-1]
        
        # Check for oversold condition (RSI < 30)
        if current_rsi < self.oversold and previous_rsi >= self.oversold:
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.8,
                metadata={
                    "rsi": current_rsi,
                    "signal_type": "oversold"
                }
            )
        
        # Check for overbought condition (RSI > 70)
        elif current_rsi > self.overbought and previous_rsi <= self.overbought:
            return TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.8,
                metadata={
                    "rsi": current_rsi,
                    "signal_type": "overbought"
                }
            )
        
        return None
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size"""
        return 1000 / price 