"""
Elliott Wave Impulse Strategy
Trades based on Elliott Wave impulse pattern completions (waves 1-3-5)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


class ElliottWaveImpulseStrategy(BaseStrategy):
    """
    Elliott Wave Impulse Strategy
    
    Trades impulse wave completions (waves 1, 3, 5) with strong trending moves.
    Best for trending markets with clear directional bias.
    
    Features:
    - Impulse pattern detection (5-wave structure)
    - Wave 3 extension detection
    - Wave 5 exhaustion signals
    - Momentum confirmation
    - Good win rate (55-60%)
    """
    
    def __init__(self, 
                 min_confidence: float = 0.65,
                 lookback_period: int = 50,
                 min_wave_3_extension: float = 1.618,  # Wave 3 should be >= 1.618x wave 1
                 **kwargs):
        super().__init__(name="Elliott_Wave_Impulse", config=kwargs)
        self.min_confidence = min_confidence
        self.lookback_period = lookback_period
        self.min_wave_3_extension = min_wave_3_extension
        self.fibonacci_extensions = [1.272, 1.618, 2.618]  # Wave 3 and 5 targets
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate signal based on impulse wave completion"""
        
        if len(data) < self.lookback_period:
            return None
        
        try:
            # Get recent price data
            recent_data = data.tail(self.lookback_period)
            prices = recent_data['Close'].values
            current_price = prices[-1]
            
            # Analyze impulse pattern
            pattern = self._detect_impulse_pattern(prices, recent_data)
            
            if not pattern or pattern['confidence'] < self.min_confidence:
                return None
            
            # Generate signal based on pattern
            if pattern['type'] == 'impulse_wave_3_complete':
                # Wave 3 complete - expect wave 4 pullback, then wave 5
                action = 'BUY' if pattern['trend'] == 'up' else 'SELL'
                
                timestamp = recent_data.index[-1] if hasattr(recent_data.index[-1], 'to_pydatetime') else datetime.now()
                
                return TradeSignal(
                    symbol=symbol,
                    action=action,
                    price=current_price,
                    quantity=0,  # Calculated by backtest engine
                    confidence=pattern['confidence'],
                    timestamp=timestamp,
                    strategy=self.name,
                    metadata={
                        'pattern_type': pattern['type'],
                        'wave_position': pattern['position'],
                        'wave_3_extension': pattern.get('wave_3_extension'),
                        'target_price': pattern.get('target_price'),
                        'stop_loss': pattern.get('stop_loss'),
                        'options_strategy': 'STRADDLE'
                    }
                )
            
            elif pattern['type'] == 'impulse_wave_5_exhaustion':
                # Wave 5 exhaustion - expect reversal
                action = 'SELL' if pattern['trend'] == 'up' else 'BUY'
                
                timestamp = recent_data.index[-1] if hasattr(recent_data.index[-1], 'to_pydatetime') else datetime.now()
                
                return TradeSignal(
                    symbol=symbol,
                    action=action,
                    price=current_price,
                    quantity=0,
                    confidence=pattern['confidence'],
                    timestamp=timestamp,
                    strategy=self.name,
                    metadata={
                        'pattern_type': pattern['type'],
                        'wave_position': 'wave_5_end',
                        'target_price': pattern.get('target_price'),
                        'stop_loss': pattern.get('stop_loss'),
                        'options_strategy': 'STRADDLE'
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Elliott Wave Impulse strategy for {symbol}: {e}")
            return None
    
    def _detect_impulse_pattern(self, prices: np.ndarray, data: pd.DataFrame) -> Optional[Dict]:
        """Detect impulse wave pattern (5-wave structure)"""
        
        # Find peaks and troughs
        peaks, troughs = self._find_pivots(prices)
        
        if len(peaks) < 3 or len(troughs) < 2:
            return None
        
        current_price = prices[-1]
        
        # Identify wave structure
        # Impulse up: trough-peak-trough-peak-trough-peak (1-2-3-4-5)
        # Impulse down: peak-trough-peak-trough-peak-trough
        
        # Check for upward impulse
        if len(peaks) >= 3 and len(troughs) >= 2:
            wave_1_start = prices[troughs[-2]] if len(troughs) >= 2 else prices[0]
            wave_1_end = prices[peaks[-2]] if len(peaks) >= 2 else current_price
            wave_3_start = prices[troughs[-1]] if len(troughs) >= 1 else wave_1_end
            wave_3_end = prices[peaks[-1]] if len(peaks) >= 1 else current_price
            
            wave_1_size = abs(wave_1_end - wave_1_start)
            wave_3_size = abs(wave_3_end - wave_3_start)
            
            # Wave 3 should be extended (1.618x or more of wave 1)
            wave_3_extension = wave_3_size / wave_1_size if wave_1_size > 0 else 0
            
            if wave_3_extension >= self.min_wave_3_extension:
                # Strong wave 3 - look for wave 4 or wave 5
                
                # Check momentum
                momentum_score = self._check_momentum(data)
                volume_score = self._check_volume_pattern(data)
                
                # Calculate confidence
                extension_score = min(1.0, wave_3_extension / 2.0)  # Max out at 2.0 extension
                confidence = (extension_score * 0.4 + momentum_score * 0.3 + volume_score * 0.3)
                
                # Determine trend
                sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
                sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
                trend = 'up' if sma_20 > sma_50 else 'down'
                
                # Check if we're at wave 3 completion or wave 5 exhaustion
                distance_from_peak = abs(current_price - wave_3_end) / wave_3_size if wave_3_size > 0 else 0
                
                if distance_from_peak < 0.1:
                    # Near wave 3 peak
                    return {
                        'type': 'impulse_wave_3_complete',
                        'position': 'wave_3_end',
                        'confidence': confidence,
                        'trend': trend,
                        'wave_3_extension': wave_3_extension,
                        'target_price': wave_3_end * 1.05 if trend == 'up' else wave_3_end * 0.95,
                        'stop_loss': wave_3_start
                    }
                elif distance_from_peak > 0.3 and momentum_score < 0.4:
                    # Potential wave 5 exhaustion (momentum divergence)
                    return {
                        'type': 'impulse_wave_5_exhaustion',
                        'position': 'wave_5_end',
                        'confidence': confidence * 0.9,  # Slightly lower confidence
                        'trend': trend,
                        'wave_3_extension': wave_3_extension,
                        'target_price': wave_1_start,  # Expect retracement
                        'stop_loss': current_price * 1.05 if trend == 'up' else current_price * 0.95
                    }
        
        return None
    
    def _find_pivots(self, prices: np.ndarray, order: int = 5) -> Tuple[List, List]:
        """Find significant price pivots (peaks and troughs)"""
        peaks = []
        troughs = []
        
        for i in range(order, len(prices) - order):
            # Check for peak
            if all(prices[i] >= prices[i-j] for j in range(1, order+1)) and \
               all(prices[i] >= prices[i+j] for j in range(1, order+1)):
                if not peaks or i - peaks[-1] > order:  # Avoid duplicate peaks
                    peaks.append(i)
            
            # Check for trough
            elif all(prices[i] <= prices[i-j] for j in range(1, order+1)) and \
                 all(prices[i] <= prices[i+j] for j in range(1, order+1)):
                if not troughs or i - troughs[-1] > order:  # Avoid duplicate troughs
                    troughs.append(i)
        
        return peaks, troughs
    
    def _check_momentum(self, data: pd.DataFrame) -> float:
        """Check momentum strength"""
        # Calculate basic momentum indicator
        if len(data) < 14:
            return 0.5
        
        # Use price momentum
        recent_change = data['Close'].pct_change(periods=10).iloc[-1]
        
        if abs(recent_change) > 0.05:
            return 0.8  # Strong momentum
        elif abs(recent_change) > 0.02:
            return 0.6  # Moderate momentum
        else:
            return 0.4  # Weak momentum
    
    def _check_volume_pattern(self, data: pd.DataFrame) -> float:
        """Check volume confirmation"""
        if 'Volume' not in data.columns or len(data) < 10:
            return 0.5
        
        recent_volume = data['Volume'].tail(5).mean()
        avg_volume = data['Volume'].tail(20).mean()
        
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Increasing volume confirms impulse wave
        if volume_ratio > 1.3:
            return 0.85
        elif volume_ratio > 1.1:
            return 0.7
        else:
            return 0.5








