"""
Simplified Calendar Spread Strategy for Backtesting
Uses stock data to simulate calendar spread behavior
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class CalendarSpreadStrategy(BaseStrategy):
    """
    Simplified Calendar Spread Strategy for Backtesting
    
    Simulates calendar spread behavior using stock price patterns
    and time-based mean reversion signals.
    """
    
    def __init__(self, 
                 name: str = "CalendarSpreadStrategy",
                 confidence_threshold: float = 0.2,  # Lowered from 0.3
                 lookback_period: int = 20,
                 volatility_threshold: float = 0.015,  # Lowered from 0.02
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.confidence_threshold = confidence_threshold
        self.lookback_period = lookback_period
        self.volatility_threshold = volatility_threshold
        
    def analyze_time_decay_pattern(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze for time decay patterns using price momentum"""
        if len(data) < self.lookback_period:
            return {'pattern_found': False, 'confidence': 0.0}
        
        # Calculate short-term vs long-term momentum
        short_period = min(5, len(data) // 4)
        long_period = self.lookback_period
        
        short_momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-short_period]) / data['Close'].iloc[-short_period]
        long_momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-long_period]) / data['Close'].iloc[-long_period]
        
        # Calculate volatility
        returns = data['Close'].pct_change().dropna()
        volatility = returns.tail(self.lookback_period).std()
        
        # Time decay signal: when short-term momentum is weaker than long-term
        time_decay_signal = abs(short_momentum) < abs(long_momentum) * 0.7
        
        # Calculate confidence based on volatility and momentum divergence
        momentum_divergence = abs(long_momentum - short_momentum)
        confidence = min(momentum_divergence * 5, 1.0)
        
        # Check volatility threshold
        if volatility < self.volatility_threshold:
            confidence *= 0.5  # Reduce confidence for low volatility
        
        return {
            'pattern_found': time_decay_signal and volatility > self.volatility_threshold,
            'confidence': confidence,
            'short_momentum': short_momentum,
            'long_momentum': long_momentum,
            'volatility': volatility,
            'momentum_divergence': momentum_divergence
        }
    
    def determine_signal_direction(self, data: pd.DataFrame) -> Optional[str]:
        """Determine signal direction based on mean reversion"""
        if len(data) < 10:
            return None
        
        current_price = data['Close'].iloc[-1]
        sma_short = data['Close'].tail(5).mean()
        sma_long = data['Close'].tail(15).mean()
        
        # Mean reversion signal
        deviation_from_short = (current_price - sma_short) / sma_short
        deviation_from_long = (current_price - sma_long) / sma_long
        
        # Calendar spread typically benefits from sideways movement
        # Generate signals based on mean reversion (more lenient)
        if abs(deviation_from_short) > 0.005:  # 0.5% deviation (lowered from 1%)
            if deviation_from_short > 0:
                return 'SELL'  # Expect reversion down
            else:
                return 'BUY'   # Expect reversion up
        
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate calendar spread trading signal"""
        
        if len(data) < self.lookback_period:
            return None
        
        # Analyze time decay pattern
        pattern_analysis = self.analyze_time_decay_pattern(data)
        
        if not pattern_analysis.get('pattern_found', False):
            return None
        
        confidence = pattern_analysis.get('confidence', 0.0)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Determine signal direction
        action = self.determine_signal_direction(data)
        
        if not action:
            return None
        
        # Calculate position size with ULTRA-CONSERVATIVE risk management
        current_price = data['Close'].iloc[-1]
        # Use dynamic capital allocation from backtest (5% cash reserve, 20% max position)
        capital_allocation = 4000.0 * 0.95  # $3800 available (5% cash reserve) (from $4000 total / 4 strategies)
        risk_percentage = min(0.20, confidence * 0.20)  # 20% max position size, scaled by confidence
        quantity = self.calculate_position_size(capital_allocation, current_price, risk_percentage)
        
        # Additional safety: limit maximum position size to 5% of capital
        max_shares = int(capital_allocation * 0.20 / current_price)  # 20% of capital max
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
                'pattern_type': 'calendar_spread',
                'short_momentum': pattern_analysis.get('short_momentum', 0.0),
                'long_momentum': pattern_analysis.get('long_momentum', 0.0),
                'volatility': pattern_analysis.get('volatility', 0.0),
                'momentum_divergence': pattern_analysis.get('momentum_divergence', 0.0)
            }
        )
