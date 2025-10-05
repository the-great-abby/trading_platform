"""
Relative Strength Index (RSI) Strategy
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """Relative Strength Index Strategy"""
    
    def __init__(self, period: int = 7, oversold: float = 25, overbought: float = 75, **kwargs):
        super().__init__("RSI_Strategy", kwargs)
        self.period = period  # Reduced from 14 to 7 for faster signals
        self.oversold = oversold  # Reduced from 30 to 25 for more sensitive signals
        self.overbought = overbought  # Increased from 70 to 75 for more sensitive signals
        
    def _calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI from price data"""
        if len(data) < self.period + 1:
            return pd.Series([np.nan] * len(data), index=data.index)
        
        # Calculate price changes
        delta = data['Close'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=self.period).mean()
        avg_losses = losses.rolling(window=self.period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal based on RSI"""
        if data.empty or len(data) < self.period + 1:
            return None
        
        # Calculate RSI
        rsi_values = self._calculate_rsi(data)
        
        # Check if we have enough data
        if rsi_values.isna().all() or len(rsi_values.dropna()) < 2:
            return None
        
        # Get latest RSI values
        current_rsi = rsi_values.iloc[-1]
        previous_rsi = rsi_values.iloc[-2]
        current_price = data['Close'].iloc[-1]
        
        # Skip if RSI is not available
        if pd.isna(current_rsi) or pd.isna(previous_rsi):
            return None
        
        # DEBUG: Log RSI values for troubleshooting
        logger.info(f"🔍 RSI DEBUG - {symbol}: current_rsi={current_rsi:.2f}, previous_rsi={previous_rsi:.2f}, oversold={self.oversold}, overbought={self.overbought}")
        
        # Check for oversold condition (RSI < 25) - Simple threshold, not crossover
        if current_rsi < self.oversold:
            logger.info(f"✅ RSI BUY SIGNAL - {symbol}: RSI is oversold at {current_rsi:.2f} (threshold: {self.oversold})")
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
        
        # Check for overbought condition (RSI > 75) - Simple threshold, not crossover
        elif current_rsi > self.overbought:
            logger.info(f"✅ RSI SELL SIGNAL - {symbol}: RSI is overbought at {current_rsi:.2f} (threshold: {self.overbought})")
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
        
        # Check for crossover signals (more sensitive)
        elif current_rsi < self.oversold + 5 and previous_rsi >= self.oversold + 5:
            logger.info(f"✅ RSI BUY CROSSOVER - {symbol}: RSI crossed below {self.oversold + 5} ({previous_rsi:.2f} -> {current_rsi:.2f})")
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "rsi": current_rsi,
                    "signal_type": "crossover"
                }
            )
        
        elif current_rsi > self.overbought - 5 and previous_rsi <= self.overbought - 5:
            logger.info(f"✅ RSI SELL CROSSOVER - {symbol}: RSI crossed above {self.overbought - 5} ({previous_rsi:.2f} -> {current_rsi:.2f})")
            return TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.7,
                metadata={
                    "rsi": current_rsi,
                    "signal_type": "crossover"
                }
            )
        
        logger.info(f"RSI NO SIGNAL - {symbol}: RSI={current_rsi:.2f} (oversold: {self.oversold}, overbought: {self.overbought})")
        return None
    
    def _calculate_quantity(self, price: float) -> float:
        """Calculate position size"""
        return 1000 / price 