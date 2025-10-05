"""
Bollinger Bands Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Strategy implementation"""
    
    def __init__(self, 
                 period: int = 20,
                 std_dev: float = 2.0,
                 threshold: float = 0.02,
                 **kwargs):
        super().__init__(name="BollingerBands", **kwargs)
        self.period = period
        self.std_dev = std_dev
        self.threshold = threshold
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Bollinger Bands-based trading signal"""
        if len(data) < self.period:
            return None
            
        # Calculate Bollinger Bands
        sma = data['Close'].rolling(window=self.period).mean()
        std = data['Close'].rolling(window=self.period).std()
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        # Get current values
        current_price = data['Close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_sma = sma.iloc[-1]
        
        # Calculate bandwidth and %B
        bandwidth = (current_upper - current_lower) / current_sma
        percent_b = (current_price - current_lower) / (current_upper - current_lower)
        
        signal = None
        
        # FIXED LOGIC: Only generate BUY signals (oversold bounce)
        # This ensures we only buy when oversold, not sell when overbought
        if (current_price <= current_lower * (1 + self.threshold) and 
            percent_b < 0.2):
            
            signal = TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.8,
                metadata={
                    "upper_band": current_upper,
                    "lower_band": current_lower,
                    "sma": current_sma,
                    "percent_b": percent_b,
                    "bandwidth": bandwidth,
                    "signal_type": "oversold_bounce",
                    "historical_date": historical_date
                }
            )
            logger.info(f"✅ BollingerBands BUY signal: {symbol} at ${current_price:.2f} (oversold: {percent_b:.2f})")
        
        # REMOVED SELL LOGIC: Only buy on oversold, let other strategies handle selling
        # This prevents selling stocks we don't own
        
        return signal
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size"""
        return 1000 / price  # $1000 per trade 