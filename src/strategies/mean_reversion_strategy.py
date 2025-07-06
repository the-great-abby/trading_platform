"""
Mean Reversion Strategy - Trades when prices deviate significantly from moving averages
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseStrategy
from ..core.types import TradeSignal


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy based on price deviations from moving averages"""
    
    def __init__(self, 
                 short_ma: int = 20,
                 long_ma: int = 50,
                 deviation_threshold: float = 0.05,
                 rsi_period: int = 14,
                 **kwargs):
        super().__init__(name="Mean_Reversion_Strategy", **kwargs)
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.deviation_threshold = deviation_threshold
        self.rsi_period = rsi_period
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate mean reversion trading signal"""
        if len(data) < self.long_ma + 10:
            return None
            
        # Calculate indicators
        data = self._calculate_indicators(data)
        
        # Get current values
        current_price = data['Close'].iloc[-1]
        short_ma = data['Short_MA'].iloc[-1]
        long_ma = data['Long_MA'].iloc[-1]
        deviation = data['Price_Deviation'].iloc[-1]
        rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
        
        # Check for oversold condition (price below MA, RSI oversold)
        if (deviation < -self.deviation_threshold and 
            current_price < short_ma and 
            rsi < 35):
            
            return TradeSignal(
                symbol=symbol,
                action="BUY",
                quantity=self._calculate_quantity(current_price, abs(deviation)),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=min(abs(deviation) * 10, 0.85),
                metadata={
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "deviation": deviation,
                    "rsi": rsi,
                    "signal_type": "oversold_reversion"
                }
            )
            
        # Check for overbought condition (price above MA, RSI overbought)
        elif (deviation > self.deviation_threshold and 
              current_price > short_ma and 
              rsi > 65):
            
            return TradeSignal(
                symbol=symbol,
                action="SELL",
                quantity=self._calculate_quantity(current_price, deviation),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=min(deviation * 10, 0.85),
                metadata={
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "deviation": deviation,
                    "rsi": rsi,
                    "signal_type": "overbought_reversion"
                }
            )
        
        return None
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate mean reversion indicators"""
        df = data.copy()
        
        # Moving averages
        df['Short_MA'] = df['Close'].rolling(window=self.short_ma).mean()
        df['Long_MA'] = df['Close'].rolling(window=self.long_ma).mean()
        
        # Price deviation from short MA
        df['Price_Deviation'] = (df['Close'] - df['Short_MA']) / df['Short_MA']
        
        # Z-score of price deviation
        df['Deviation_ZScore'] = (df['Price_Deviation'] - df['Price_Deviation'].rolling(window=20).mean()) / df['Price_Deviation'].rolling(window=20).std()
        
        # Bollinger Bands for additional confirmation
        bb_middle = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = bb_middle + (bb_std * 2)
        df['BB_Lower'] = bb_middle - (bb_std * 2)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        return df
    
    def _calculate_quantity(self, price: float, deviation_strength: float) -> float:
        """Calculate position size based on deviation strength"""
        base_quantity = 1000 / price  # $1000 base position
        deviation_multiplier = 1.0 + (deviation_strength * 3)  # Scale with deviation
        return base_quantity * deviation_multiplier 