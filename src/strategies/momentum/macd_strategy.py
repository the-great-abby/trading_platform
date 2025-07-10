"""
MACD (Moving Average Convergence Divergence) Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal


class MACDStrategy(BaseStrategy):
    """MACD Strategy implementation"""
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26,
                 signal_period: int = 9,
                 threshold: float = 0.001,
                 **kwargs):
        super().__init__(name="MACD", **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.threshold = threshold
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate MACD-based trading signal"""
        if len(data) < self.slow_period + self.signal_period:
            return None
            
        # Calculate MACD
        exp1 = data['Close'].ewm(span=self.fast_period).mean()
        exp2 = data['Close'].ewm(span=self.slow_period).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=self.signal_period).mean()
        histogram = macd - signal_line
        
        # Get current values
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
        current_price = data['Close'].iloc[-1]
        
        # Generate signals
        signal = None
        
        # Bullish signal: MACD crosses above signal line and histogram is increasing
        if (current_macd > current_signal and 
            current_histogram > prev_histogram and 
            abs(current_histogram) > self.threshold):
            
            signal = TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "macd": current_macd,
                    "signal": current_signal,
                    "histogram": current_histogram,
                    "signal_type": "bullish_crossover"
                }
            )
            
        # Bearish signal: MACD crosses below signal line and histogram is decreasing
        elif (current_macd < current_signal and 
              current_histogram < prev_histogram and 
              abs(current_histogram) > self.threshold):
            
            signal = TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "macd": current_macd,
                    "signal": current_signal,
                    "histogram": current_histogram,
                    "signal_type": "bearish_crossover"
                }
            )
        
        return signal
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size based on MACD strength"""
        return 1000 / price  # $1000 per trade 