"""
Simple Moving Average (SMA) Crossover Strategy
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal


class SMACrossoverStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, short_window: int = 20, long_window: int = 50, **kwargs):
        super().__init__(name="SMA_Crossover", **kwargs)
        self.short_window = short_window
        self.long_window = long_window
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal based on SMA crossover"""
        if data.empty or len(data) < self.long_window:
            return None
        
        # Get latest data
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None
        
        if previous is None:
            return None
        
        # Check for crossover signals
        current_price = latest['Close']
        
        # Calculate SMAs
        short_sma = data['Close'].rolling(window=self.short_window).mean().iloc[-1]
        long_sma = data['Close'].rolling(window=self.long_window).mean().iloc[-1]
        
        # Previous SMAs
        prev_short_sma = data['Close'].rolling(window=self.short_window).mean().iloc[-2]
        prev_long_sma = data['Close'].rolling(window=self.long_window).mean().iloc[-2]
        
        # Check for bullish crossover (short SMA crosses above long SMA)
        bullish_crossover = (
            short_sma > long_sma and 
            prev_short_sma <= prev_long_sma
        )
        
        # Check for bearish crossover (short SMA crosses below long SMA)
        bearish_crossover = (
            short_sma < long_sma and 
            prev_short_sma >= prev_long_sma
        )
        
        # Generate signal
        if bullish_crossover:
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "short_sma": short_sma,
                    "long_sma": long_sma,
                    "crossover_type": "bullish"
                }
            )
        
        elif bearish_crossover:
            return TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "short_sma": short_sma,
                    "long_sma": long_sma,
                    "crossover_type": "bearish"
                }
            )
        
        return None
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size"""
        # Simple position sizing - 1000 USD per trade
        return 1000 / price 