"""
Momentum Strategy - Trades based on price momentum and volume confirmation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal


class MomentumStrategy(BaseStrategy):
    """Momentum-based trading strategy with volume confirmation"""
    
    def __init__(self, 
                 momentum_period: int = 10,
                 volume_period: int = 20,
                 momentum_threshold: float = 0.02,
                 volume_threshold: float = 1.5,
                 **kwargs):
        super().__init__(name="Momentum_Strategy", **kwargs)
        self.momentum_period = momentum_period
        self.volume_period = volume_period
        self.momentum_threshold = momentum_threshold
        self.volume_threshold = volume_threshold
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate momentum-based trading signal"""
        if len(data) < max(self.momentum_period, self.volume_period) + 5:
            return None
            
        # Calculate momentum indicators
        data = self._calculate_momentum_indicators(data)
        
        # Get current values
        current_price = data['Close'].iloc[-1]
        current_momentum = data['Momentum'].iloc[-1]
        current_volume_ratio = data['Volume_Ratio'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
        
        # Check for strong positive momentum with volume confirmation
        if (current_momentum > self.momentum_threshold and 
            current_volume_ratio > self.volume_threshold and
            current_rsi < 80):  # Not overbought
            
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price, current_momentum),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=min(current_momentum * 10, 0.9),  # Scale confidence with momentum
                metadata={
                    "momentum": current_momentum,
                    "volume_ratio": current_volume_ratio,
                    "rsi": current_rsi,
                    "signal_type": "momentum_breakout"
                }
            )
            
        # Check for strong negative momentum (short opportunity)
        elif (current_momentum < -self.momentum_threshold and 
              current_volume_ratio > self.volume_threshold and
              current_rsi > 20):  # Not oversold
            
            return TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price, abs(current_momentum)),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=min(abs(current_momentum) * 10, 0.9),
                metadata={
                    "momentum": current_momentum,
                    "volume_ratio": current_volume_ratio,
                    "rsi": current_rsi,
                    "signal_type": "momentum_breakdown"
                }
            )
        
        return None
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum and volume indicators"""
        df = data.copy()
        
        # Price momentum (rate of change)
        df['Momentum'] = df['Close'].pct_change(self.momentum_period)
        
        # Volume ratio (current volume vs average)
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=self.volume_period).mean()
        
        # Price acceleration (change in momentum)
        df['Momentum_Accel'] = df['Momentum'].diff()
        
        # Volatility-adjusted momentum
        volatility = df['Close'].rolling(window=20).std()
        df['Volatility_Adj_Momentum'] = df['Momentum'] / volatility
        
        return df
    
    def _calculate_quantity(self, price: float, momentum_strength: float) -> float:
        """Calculate position size based on momentum strength"""
        base_quantity = 1000 / price  # $1000 base position
        momentum_multiplier = 1.0 + (abs(momentum_strength) * 2)  # Scale with momentum
        return base_quantity * momentum_multiplier 