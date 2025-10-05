"""
Simplified Elliott Wave Strategies for Backtesting
Uses technical analysis to detect Elliott Wave patterns directly from price data
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.data_cache import get_cached_elliott_wave_data, cache_elliott_wave_data

logger = logging.getLogger(__name__)

class ElliottWaveImpulseStrategy(BaseStrategy):
    """
    Simplified Elliott Wave Impulse Strategy
    
    Detects impulse patterns using price momentum and trend analysis
    """
    
    def __init__(self, 
                 name: str = "ElliottWaveImpulseStrategy",
                 confidence_threshold: float = 0.6,
                 lookback_period: int = 20,
                 momentum_threshold: float = 0.02,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.confidence_threshold = confidence_threshold
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        
    def detect_swing_points(self, data: pd.DataFrame) -> Dict[str, List]:
        """Detect swing highs and lows"""
        highs = []
        lows = []
        
        for i in range(2, len(data) - 2):
            # Swing high: higher than 2 points on each side
            if (data['High'].iloc[i] > data['High'].iloc[i-1] and 
                data['High'].iloc[i] > data['High'].iloc[i-2] and
                data['High'].iloc[i] > data['High'].iloc[i+1] and 
                data['High'].iloc[i] > data['High'].iloc[i+2]):
                highs.append({'index': i, 'price': data['High'].iloc[i], 'date': data.index[i]})
            
            # Swing low: lower than 2 points on each side
            if (data['Low'].iloc[i] < data['Low'].iloc[i-1] and 
                data['Low'].iloc[i] < data['Low'].iloc[i-2] and
                data['Low'].iloc[i] < data['Low'].iloc[i+1] and 
                data['Low'].iloc[i] < data['Low'].iloc[i+2]):
                lows.append({'index': i, 'price': data['Low'].iloc[i], 'date': data.index[i]})
        
        return {'highs': highs, 'lows': lows}
    
    def analyze_impulse_pattern(self, swing_points: Dict[str, List]) -> Dict[str, Any]:
        """Analyze for impulse patterns"""
        highs = swing_points['highs']
        lows = swing_points['lows']
        
        if len(highs) < 2 or len(lows) < 2:
            return {'pattern_found': False, 'confidence': 0.0}
        
        # Look for 5-wave impulse pattern
        # Wave 1: Initial move up
        # Wave 2: Pullback (but not below wave 1 start)
        # Wave 3: Strong move up (usually longest)
        # Wave 4: Pullback (but not into wave 1 territory)
        # Wave 5: Final move up
        
        # Simplified: Look for 3 consecutive higher highs and 2 higher lows
        recent_highs = highs[-3:] if len(highs) >= 3 else highs
        recent_lows = lows[-2:] if len(lows) >= 2 else lows
        
        if len(recent_highs) >= 3 and len(recent_lows) >= 2:
            # Check for ascending pattern
            if (recent_highs[0]['price'] < recent_highs[1]['price'] < recent_highs[2]['price'] and
                recent_lows[0]['price'] < recent_lows[1]['price']):
                
                # Calculate confidence based on pattern strength
                price_momentum = (recent_highs[2]['price'] - recent_highs[0]['price']) / recent_highs[0]['price']
                confidence = min(price_momentum * 10, 1.0)  # Scale momentum to confidence
                
                return {
                    'pattern_found': True,
                    'pattern_type': 'impulse',
                    'direction': 'bullish',
                    'confidence': confidence,
                    'wave_count': 5,
                    'price_momentum': price_momentum
                }
        
        return {'pattern_found': False, 'confidence': 0.0}
    
    def calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate price momentum"""
        if len(data) < self.lookback_period:
            return 0.0
        
        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-self.lookback_period]
        momentum = (current_price - past_price) / past_price
        
        return momentum
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave impulse trading signal"""
        
        if len(data) < 50:  # Need sufficient data
            return None
        
        # Detect swing points
        swing_points = self.detect_swing_points(data)
        
        # Analyze for impulse pattern
        pattern_analysis = self.analyze_impulse_pattern(swing_points)
        
        if not pattern_analysis.get('pattern_found', False):
            return None
        
        # Calculate momentum
        momentum = self.calculate_momentum(data)
        
        # Check momentum threshold
        if abs(momentum) < self.momentum_threshold:
            return None
        
        # Calculate confidence
        confidence = pattern_analysis.get('confidence', 0.0)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Determine signal direction
        direction = pattern_analysis.get('direction', '')
        if direction == 'bullish' and momentum > 0:
            action = 'BUY'
        elif direction == 'bearish' and momentum < 0:
            action = 'SELL'
        else:
            return None
        
        # Calculate position size
        current_price = data['Close'].iloc[-1]
        quantity = self.calculate_position_size(current_price, confidence)
        
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
                'direction': direction,
                'momentum': momentum,
                'wave_count': pattern_analysis.get('wave_count', 0),
                'swing_points': len(swing_points['highs']) + len(swing_points['lows'])
            }
        )

class ElliottWaveCorrectiveStrategy(BaseStrategy):
    """
    Simplified Elliott Wave Corrective Strategy
    
    Detects corrective patterns using mean reversion analysis
    """
    
    def __init__(self, 
                 name: str = "ElliottWaveCorrectiveStrategy",
                 confidence_threshold: float = 0.6,
                 lookback_period: int = 20,
                 volatility_threshold: float = 0.01,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.confidence_threshold = confidence_threshold
        self.lookback_period = lookback_period
        self.volatility_threshold = volatility_threshold
        
    def detect_swing_points(self, data: pd.DataFrame) -> Dict[str, List]:
        """Detect swing highs and lows"""
        highs = []
        lows = []
        
        for i in range(2, len(data) - 2):
            # Swing high: higher than 2 points on each side
            if (data['High'].iloc[i] > data['High'].iloc[i-1] and 
                data['High'].iloc[i] > data['High'].iloc[i-2] and
                data['High'].iloc[i] > data['High'].iloc[i+1] and 
                data['High'].iloc[i] > data['High'].iloc[i+2]):
                highs.append({'index': i, 'price': data['High'].iloc[i], 'date': data.index[i]})
            
            # Swing low: lower than 2 points on each side
            if (data['Low'].iloc[i] < data['Low'].iloc[i-1] and 
                data['Low'].iloc[i] < data['Low'].iloc[i-2] and
                data['Low'].iloc[i] < data['Low'].iloc[i+1] and 
                data['Low'].iloc[i] < data['Low'].iloc[i+2]):
                lows.append({'index': i, 'price': data['Low'].iloc[i], 'date': data.index[i]})
        
        return {'highs': highs, 'lows': lows}
    
    def analyze_corrective_pattern(self, swing_points: Dict[str, List]) -> Dict[str, Any]:
        """Analyze for corrective patterns"""
        highs = swing_points['highs']
        lows = swing_points['lows']
        
        if len(highs) < 2 or len(lows) < 2:
            return {'pattern_found': False, 'confidence': 0.0}
        
        # Look for corrective patterns (ABC, triangle, flat)
        # Simplified: Look for sideways movement with alternating highs/lows
        
        recent_highs = highs[-3:] if len(highs) >= 3 else highs
        recent_lows = lows[-3:] if len(lows) >= 3 else lows
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Check for sideways pattern (corrective)
            high_range = max(h['price'] for h in recent_highs) - min(h['price'] for h in recent_highs)
            low_range = max(l['price'] for l in recent_lows) - min(l['price'] for l in recent_lows)
            avg_price = (max(h['price'] for h in recent_highs) + min(l['price'] for l in recent_lows)) / 2
            
            # Calculate range as percentage of average price
            range_pct = (high_range + low_range) / (2 * avg_price)
            
            # Corrective patterns have smaller ranges
            if range_pct < 0.05:  # Less than 5% range
                confidence = (0.05 - range_pct) * 20  # Scale to confidence
                confidence = min(confidence, 1.0)
                
                return {
                    'pattern_found': True,
                    'pattern_type': 'corrective',
                    'direction': 'sideways',
                    'confidence': confidence,
                    'range_pct': range_pct
                }
        
        return {'pattern_found': False, 'confidence': 0.0}
    
    def calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate price volatility"""
        if len(data) < self.lookback_period:
            return 0.0
        
        recent_data = data['Close'].tail(self.lookback_period)
        returns = recent_data.pct_change().dropna()
        volatility = returns.std()
        
        return volatility
    
    def calculate_mean_reversion_signal(self, data: pd.DataFrame) -> Optional[str]:
        """Calculate mean reversion signal"""
        if len(data) < self.lookback_period:
            return None
        
        current_price = data['Close'].iloc[-1]
        sma = data['Close'].tail(self.lookback_period).mean()
        
        # Calculate deviation from mean
        deviation = (current_price - sma) / sma
        
        # Mean reversion signals
        if deviation > 0.02:  # 2% above mean
            return 'SELL'  # Expect reversion down
        elif deviation < -0.02:  # 2% below mean
            return 'BUY'   # Expect reversion up
        
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Elliott Wave corrective trading signal"""
        
        if len(data) < 50:  # Need sufficient data
            return None
        
        # Detect swing points
        swing_points = self.detect_swing_points(data)
        
        # Analyze for corrective pattern
        pattern_analysis = self.analyze_corrective_pattern(swing_points)
        
        if not pattern_analysis.get('pattern_found', False):
            return None
        
        # Calculate volatility
        volatility = self.calculate_volatility(data)
        
        # Check volatility threshold
        if volatility < self.volatility_threshold:
            return None
        
        # Calculate confidence
        confidence = pattern_analysis.get('confidence', 0.0)
        
        if confidence < self.confidence_threshold:
            return None
        
        # Get mean reversion signal
        action = self.calculate_mean_reversion_signal(data)
        
        if not action:
            return None
        
        # Calculate position size
        current_price = data['Close'].iloc[-1]
        quantity = self.calculate_position_size(current_price, confidence)
        
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
                'direction': pattern_analysis.get('direction', 'unknown'),
                'volatility': volatility,
                'range_pct': pattern_analysis.get('range_pct', 0.0),
                'swing_points': len(swing_points['highs']) + len(swing_points['lows'])
            }
        )
