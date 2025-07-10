"""
Volatility Breakout Strategy - Trades breakouts from low volatility periods
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal


class VolatilityBreakoutStrategy(BaseStrategy):
    """Volatility breakout strategy that trades when price breaks out of consolidation"""
    
    def __init__(self, 
                 volatility_period: int = 20,
                 breakout_threshold: float = 1.5,
                 consolidation_threshold: float = 0.8,
                 **kwargs):
        super().__init__(name="Volatility_Breakout_Strategy", **kwargs)
        self.volatility_period = volatility_period
        self.breakout_threshold = breakout_threshold
        self.consolidation_threshold = consolidation_threshold
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate volatility breakout trading signal"""
        if len(data) < self.volatility_period + 10:
            return None
            
        # Calculate indicators
        data = self._calculate_indicators(data)
        
        # Get current values
        current_price = data['Close'].iloc[-1]
        current_volatility = data['Volatility'].iloc[-1]
        avg_volatility = data['Avg_Volatility'].iloc[-1]
        volatility_ratio = data['Volatility_Ratio'].iloc[-1]
        price_change = data['Price_Change'].iloc[-1]
        
        # Check for breakout from low volatility (consolidation)
        if (volatility_ratio > self.breakout_threshold and 
            avg_volatility < self.consolidation_threshold and
            abs(price_change) > avg_volatility * 2):
            
            # Determine direction based on price change
            action = "BUY" if price_change > 0 else "SELL"
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=self._calculate_quantity(current_price, volatility_ratio),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=min(volatility_ratio / 3, 0.9),
                metadata={
                    "volatility": current_volatility,
                    "avg_volatility": avg_volatility,
                    "volatility_ratio": volatility_ratio,
                    "price_change": price_change,
                    "signal_type": "volatility_breakout"
                }
            )
        
        return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility and breakout indicators"""
        df = data.copy()
        
        # Price changes
        df['Price_Change'] = df['Close'].pct_change()
        
        # Volatility (standard deviation of returns)
        df['Volatility'] = df['Price_Change'].rolling(window=self.volatility_period).std()
        
        # Average volatility
        df['Avg_Volatility'] = df['Volatility'].rolling(window=50).mean()
        
        # Volatility ratio (current vs average)
        df['Volatility_Ratio'] = df['Volatility'] / df['Avg_Volatility']
        
        # Price range (high-low)
        df['Price_Range'] = (df['High'] - df['Low']) / df['Close']
        df['Avg_Range'] = df['Price_Range'].rolling(window=20).mean()
        df['Range_Ratio'] = df['Price_Range'] / df['Avg_Range']
        
        # Volume confirmation
        if 'Volume' in df.columns:
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        return df
    
    def _calculate_quantity(self, price: float, volatility_strength: float) -> float:
        """Calculate position size based on volatility strength"""
        base_quantity = 1000 / price  # $1000 base position
        volatility_multiplier = 1.0 + (volatility_strength * 0.5)  # Scale with volatility
        return base_quantity * volatility_multiplier 