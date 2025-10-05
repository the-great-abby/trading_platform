"""
Simplified Volatility Strategy for Backtesting
Uses stock data to simulate volatility trading behavior
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class VolatilityStrategy(BaseStrategy):
    """
    Simplified Volatility Strategy for Backtesting
    
    Simulates volatility trading using stock price volatility patterns
    and mean reversion signals.
    """
    
    def __init__(self, 
                 name: str = "VolatilityStrategy",
                 confidence_threshold: float = 0.2,  # Lowered from 0.3
                 lookback_period: int = 20,
                 volatility_threshold: float = 0.015,  # Lowered from 0.02
                 high_volatility_threshold: float = 0.04,  # Lowered from 0.05
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.confidence_threshold = confidence_threshold
        self.lookback_period = lookback_period
        self.volatility_threshold = volatility_threshold
        self.high_volatility_threshold = high_volatility_threshold
        
    def analyze_volatility_pattern(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility patterns for trading signals"""
        if len(data) < self.lookback_period:
            return {'pattern_found': False, 'confidence': 0.0}
        
        # Calculate current volatility
        returns = data['Close'].pct_change().dropna()
        current_volatility = returns.tail(5).std()
        
        # Calculate historical volatility
        historical_volatility = returns.tail(self.lookback_period).std()
        
        # Calculate volatility percentile (simplified)
        vol_percentile = min(current_volatility / (historical_volatility * 1.5), 1.0)
        
        # Calculate price range
        recent_data = data.tail(10)
        price_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Close'].mean()
        
        # Volatility expansion signal
        volatility_expansion = current_volatility > historical_volatility * 1.2
        
        # Volatility contraction signal
        volatility_contraction = current_volatility < historical_volatility * 0.8
        
        # Determine pattern type
        pattern_found = False
        pattern_type = 'none'
        
        if volatility_expansion and current_volatility > self.high_volatility_threshold:
            pattern_found = True
            pattern_type = 'expansion'
        elif volatility_contraction and current_volatility < self.volatility_threshold:
            pattern_found = True
            pattern_type = 'contraction'
        elif current_volatility > self.volatility_threshold:
            pattern_found = True
            pattern_type = 'moderate'
        
        # Calculate confidence
        confidence = min(vol_percentile * 2, 1.0)
        
        return {
            'pattern_found': pattern_found,
            'confidence': confidence,
            'pattern_type': pattern_type,
            'current_volatility': current_volatility,
            'historical_volatility': historical_volatility,
            'vol_percentile': vol_percentile,
            'price_range': price_range,
            'volatility_expansion': volatility_expansion,
            'volatility_contraction': volatility_contraction
        }
    
    def determine_volatility_signal(self, data: pd.DataFrame, pattern_analysis: Dict[str, Any]) -> Optional[str]:
        """Determine signal direction based on volatility pattern"""
        pattern_type = pattern_analysis.get('pattern_type', 'none')
        current_volatility = pattern_analysis.get('current_volatility', 0.0)
        
        if len(data) < 10:
            return None
        
        current_price = data['Close'].iloc[-1]
        sma = data['Close'].tail(10).mean()
        deviation = (current_price - sma) / sma
        
        if pattern_type == 'expansion':
            # High volatility - expect mean reversion
            if deviation > 0.01:  # Price above mean
                return 'SELL'  # Expect reversion down
            elif deviation < -0.01:  # Price below mean
                return 'BUY'   # Expect reversion up
        
        elif pattern_type == 'contraction':
            # Low volatility - expect breakout
            if abs(deviation) < 0.005:  # Price near mean
                # Random direction for breakout
                import random
                return 'BUY' if random.random() > 0.5 else 'SELL'
        
        elif pattern_type == 'moderate':
            # Moderate volatility - trend following
            if deviation > 0.005:
                return 'BUY'   # Follow trend up
            elif deviation < -0.005:
                return 'SELL'  # Follow trend down
        
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate volatility trading signal"""
        
        if len(data) < self.lookback_period:
            return None
        
        # Analyze volatility pattern
        pattern_analysis = self.analyze_volatility_pattern(data)
        
        if not pattern_analysis.get('pattern_found', False):
            return None
        
        confidence = pattern_analysis.get('confidence', 0.0)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Determine signal direction
        action = self.determine_volatility_signal(data, pattern_analysis)
        
        if not action:
            return None
        
        # Calculate position size with ULTRA-CONSERVATIVE risk management
        current_price = data['Close'].iloc[-1]
        # Use paper trading capital allocation: 5% max position size, 0.5% risk per trade
        capital_allocation = 1000.0  # $1000 per strategy (from $4000 total / 4 strategies)
        risk_percentage = min(0.005, confidence * 0.01)  # 0.5% max risk, scaled by confidence
        quantity = self.calculate_position_size(capital_allocation, current_price, risk_percentage)
        
        # Additional safety: limit maximum position size to 5% of capital
        max_shares = int(capital_allocation * 0.05 / current_price)  # 5% of capital max
        quantity = min(quantity, max_shares)
        
        # Ensure minimum viable position
        if quantity < 1:
            quantity = 1
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'pattern_type': pattern_analysis.get('pattern_type', 'unknown'),
                'current_volatility': pattern_analysis.get('current_volatility', 0.0),
                'historical_volatility': pattern_analysis.get('historical_volatility', 0.0),
                'vol_percentile': pattern_analysis.get('vol_percentile', 0.0),
                'price_range': pattern_analysis.get('price_range', 0.0),
                'volatility_expansion': pattern_analysis.get('volatility_expansion', False),
                'volatility_contraction': pattern_analysis.get('volatility_contraction', False)
            }
        )
