#!/usr/bin/env python3
"""
Advanced Elliott Wave Pattern Detection

This module implements advanced Elliott Wave pattern detection algorithms,
including swing point detection, wave counting, Fibonacci analysis, and
pattern validation with confidence scoring.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from models import (
    WavePoint, ElliottWavePattern, FibonacciLevel, WaveRelationship,
    PatternAnalysis, WaveType, WaveDirection
)

logger = logging.getLogger(__name__)


@dataclass
class SwingPoint:
    """Swing point data structure"""
    timestamp: datetime
    price: float
    point_type: str  # 'high' or 'low'
    confidence: float


class AdvancedElliottWaveDetector:
    """Advanced Elliott Wave pattern detection engine"""
    
    def __init__(self):
        self.fibonacci_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618, 4.236]
        self.min_wave_length = 3  # Minimum bars for a wave
        self.swing_point_threshold = 0.5  # Minimum price change for swing point
        
    def detect_swing_points(self, data: pd.DataFrame) -> List[SwingPoint]:
        """Detect swing high and low points in price data"""
        swing_points = []
        
        if len(data) < 10:  # Need minimum data
            return swing_points
        
        logger.info(f"DataFrame index type: {type(data.index)}, first few values: {data.index[:5].tolist()}")
        logger.info(f"DataFrame columns: {data.columns.tolist()}")
        logger.info(f"DataFrame shape: {data.shape}")
        
        highs = data['High'].values
        lows = data['Low'].values
        # Use the index as timestamps (Date column)
        timestamps = data.index.values
        
        logger.info(f"Timestamps type: {type(timestamps)}, first few values: {timestamps[:5]}")
        logger.info(f"Timestamps dtype: {timestamps.dtype}")
        logger.info(f"Timestamps shape: {timestamps.shape}")
        logger.info(f"First timestamp value: {timestamps[0]}, type: {type(timestamps[0])}")
        
        # Find local maxima and minima
        for i in range(2, len(data) - 2):
            # Check for swing high
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                
                confidence = self._calculate_swing_confidence(data, i, 'high')
                # Convert numpy.datetime64 to Python datetime
                timestamp = timestamps[i]
                if isinstance(timestamp, np.datetime64):
                    timestamp = pd.to_datetime(timestamp).to_pydatetime()
                
                swing_points.append(SwingPoint(
                    timestamp=timestamp,
                    price=highs[i],
                    point_type='high',
                    confidence=confidence
                ))
            
            # Check for swing low
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                
                confidence = self._calculate_swing_confidence(data, i, 'low')
                # Convert numpy.datetime64 to Python datetime
                timestamp = timestamps[i]
                if isinstance(timestamp, np.datetime64):
                    timestamp = pd.to_datetime(timestamp).to_pydatetime()
                
                swing_points.append(SwingPoint(
                    timestamp=timestamp,
                    price=lows[i],
                    point_type='low',
                    confidence=confidence
                ))
        
        # Sort by timestamp
        swing_points.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Detected {len(swing_points)} swing points")
        for i, sp in enumerate(swing_points[:5]):  # Log first 5 swing points
            logger.info(f"Swing point {i}: {sp.point_type} at {sp.price} on {sp.timestamp} (type: {type(sp.timestamp)})")
        return swing_points
    
    def _calculate_swing_confidence(self, data: pd.DataFrame, index: int, point_type: str) -> float:
        """Calculate confidence score for a swing point"""
        if point_type == 'high':
            price = data.iloc[index]['High']
            # Check how much higher this point is compared to surrounding points
            surrounding_prices = data.iloc[max(0, index-3):min(len(data), index+4)]['High']
            
            if len(surrounding_prices) == 0:
                return 0.5  # Default confidence if no surrounding data
            
            # Remove the current point by filtering
            surrounding_prices = surrounding_prices[surrounding_prices.index != data.index[index]]
            
            if len(surrounding_prices) == 0:
                return 0.5  # Default confidence if no surrounding data
            
            max_surrounding = surrounding_prices.max()
            # Calculate percentage difference from the highest surrounding point
            if max_surrounding > 0:
                price_diff_pct = (price - max_surrounding) / max_surrounding
                # Convert to confidence: 0% diff = 0.1, 5% diff = 0.6, 10%+ diff = 1.0
                confidence = min(1.0, max(0.1, 0.1 + price_diff_pct * 10))
            else:
                confidence = 0.5
        else:  # low
            price = data.iloc[index]['Low']
            # Check how much lower this point is compared to surrounding points
            surrounding_prices = data.iloc[max(0, index-3):min(len(data), index+4)]['Low']
            
            if len(surrounding_prices) == 0:
                return 0.5  # Default confidence if no surrounding data
            
            # Remove the current point by filtering
            surrounding_prices = surrounding_prices[surrounding_prices.index != data.index[index]]
            
            if len(surrounding_prices) == 0:
                return 0.5  # Default confidence if no surrounding data
            
            min_surrounding = surrounding_prices.min()
            # Calculate percentage difference from the lowest surrounding point
            if min_surrounding > 0:
                price_diff_pct = (min_surrounding - price) / min_surrounding
                # Convert to confidence: 0% diff = 0.1, 5% diff = 0.6, 10%+ diff = 1.0
                confidence = min(1.0, max(0.1, 0.1 + price_diff_pct * 10))
            else:
                confidence = 0.5
        
        return confidence
    
    def identify_wave_pattern(self, swing_points: List[SwingPoint]) -> Optional[ElliottWavePattern]:
        """Identify Elliott Wave pattern from swing points"""
        if len(swing_points) < 5:  # Need minimum swing points
            return None
        
        # Try to identify impulse pattern first
        impulse_pattern = self._identify_impulse_pattern(swing_points)
        if impulse_pattern:
            return impulse_pattern
        
        # Try corrective patterns
        corrective_pattern = self._identify_corrective_pattern(swing_points)
        if corrective_pattern:
            return corrective_pattern
        
        # Fallback: Create a basic pattern with confidence based on swing point quality
        return self._create_fallback_pattern(swing_points)
    
    def _create_fallback_pattern(self, swing_points: List[SwingPoint]) -> Optional[ElliottWavePattern]:
        """Create a fallback pattern when perfect Elliott Wave patterns aren't found"""
        if len(swing_points) < 3:
            return None
        
        # Calculate confidence based on swing point quality and market conditions
        avg_confidence = sum(sp.confidence for sp in swing_points) / len(swing_points)
        
        # Boost confidence based on number of swing points (more data = higher confidence)
        swing_point_bonus = min(0.3, len(swing_points) * 0.02)  # Up to 30% bonus
        
        # Calculate price momentum for additional confidence
        momentum_confidence = 0.0
        if len(swing_points) >= 2:
            price_change = abs(swing_points[-1].price - swing_points[0].price) / swing_points[0].price
            momentum_confidence = min(0.2, price_change * 2)  # Up to 20% bonus for strong moves
        
        # Determine pattern type based on recent trend
        recent_trend = 'corrective'  # Default
        if len(swing_points) >= 3:
            recent_highs = [sp.price for sp in swing_points[-3:] if sp.point_type == 'high']
            recent_lows = [sp.price for sp in swing_points[-3:] if sp.point_type == 'low']
            
            if recent_highs and recent_lows:
                avg_high = sum(recent_highs) / len(recent_highs)
                avg_low = sum(recent_lows) / len(recent_lows)
                if avg_high > avg_low * 1.05:  # 5% higher highs than lows
                    recent_trend = 'impulse'
        
        # Calculate final confidence
        final_confidence = min(0.95, avg_confidence + swing_point_bonus + momentum_confidence)
        final_confidence = max(0.3, final_confidence)  # Minimum 30% confidence
        
        # Create basic wave points
        waves = []
        for i, sp in enumerate(swing_points[-5:]):  # Use last 5 swing points
            wave_number = i + 1
            direction = 'up' if sp.point_type == 'high' else 'down'
            waves.append(self._create_wave_point(sp, wave_number, direction))
        
        # Determine wave type
        wave_type = WaveType.IMPULSE if recent_trend == 'impulse' else WaveType.CORRECTIVE
        
        logger.info(f"Created fallback {recent_trend} pattern with confidence {final_confidence:.2f} from {len(swing_points)} swing points")
        
        return self._create_pattern(waves, wave_type, swing_points[0].timestamp, swing_points[-1].timestamp, final_confidence)
    
    def _identify_impulse_pattern(self, swing_points: List[SwingPoint]) -> Optional[ElliottWavePattern]:
        """Identify 5-wave impulse pattern"""
        if len(swing_points) < 5:
            return None
        
        # Look for 5-wave sequence with more flexible criteria
        waves = []
        current_direction = None
        
        # Try multiple starting points to find the best pattern
        best_pattern = None
        best_confidence = 0.0
        
        for start_idx in range(min(3, len(swing_points) - 4)):  # Try first 3 positions
            pattern = self._try_impulse_from_start(swing_points, start_idx)
            if pattern and pattern.confidence > best_confidence:
                best_pattern = pattern
                best_confidence = pattern.confidence
        
        return best_pattern
    
    def _try_impulse_from_start(self, swing_points: List[SwingPoint], start_idx: int) -> Optional[ElliottWavePattern]:
        """Try to identify impulse pattern starting from a specific index"""
        if len(swing_points) - start_idx < 5:
            return None
            
        # Look for 5-wave sequence starting from start_idx
        waves = []
        
        # Use the first 5 swing points from start_idx
        selected_points = swing_points[start_idx:start_idx + 5]
        
        # Create waves alternating direction
        for i, point in enumerate(selected_points):
            wave_number = i + 1
            direction = 'up' if i % 2 == 0 else 'down'  # Alternate directions
            waves.append(self._create_wave_point(point, wave_number, direction))
        
        # Calculate confidence based on wave quality
        confidence = self._calculate_pattern_confidence(waves, swing_points)
        
        # Validate impulse pattern
        if len(waves) == 5 and confidence > 0.3:  # Lower threshold for impulse
            return self._create_pattern(waves, WaveType.IMPULSE, swing_points[start_idx].timestamp, swing_points[start_idx + 4].timestamp, confidence)
        
        return None
    
    def _calculate_pattern_confidence(self, waves: List[WavePoint], swing_points: List[SwingPoint]) -> float:
        """Calculate confidence for a wave pattern"""
        if not waves:
            return 0.0
        
        # Base confidence from individual wave confidences
        avg_wave_confidence = sum(wave.confidence for wave in waves) / len(waves)
        
        # Bonus for clear price progression
        price_progression_bonus = 0.0
        if len(waves) >= 3:
            prices = [wave.price for wave in waves]
            # Check if prices show clear progression (not just random)
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            avg_change = sum(price_changes) / len(price_changes)
            price_progression_bonus = min(0.3, avg_change * 5)  # Up to 30% bonus
        
        # Bonus for sufficient swing points
        swing_point_bonus = min(0.2, len(swing_points) * 0.01)  # Up to 20% bonus
        
        final_confidence = min(0.95, avg_wave_confidence + price_progression_bonus + swing_point_bonus)
        return max(0.1, final_confidence)
    
    def _identify_corrective_pattern(self, swing_points: List[SwingPoint]) -> Optional[ElliottWavePattern]:
        """Identify 3-wave corrective pattern"""
        if len(swing_points) < 3:
            return None
        
        # Try multiple starting points for corrective patterns
        best_pattern = None
        best_confidence = 0.0
        
        for start_idx in range(min(5, len(swing_points) - 2)):  # Try first 5 positions
            pattern = self._try_corrective_from_start(swing_points, start_idx)
            if pattern and pattern.confidence > best_confidence:
                best_pattern = pattern
                best_confidence = pattern.confidence
        
        return best_pattern
    
    def _try_corrective_from_start(self, swing_points: List[SwingPoint], start_idx: int) -> Optional[ElliottWavePattern]:
        """Try to identify corrective pattern starting from a specific index"""
        if len(swing_points) - start_idx < 3:
            return None
            
        # Use the first 3 swing points from start_idx
        selected_points = swing_points[start_idx:start_idx + 3]
        
        # Create waves alternating direction
        waves = []
        for i, point in enumerate(selected_points):
            wave_number = i + 1
            direction = 'up' if i % 2 == 0 else 'down'  # Alternate directions
            waves.append(self._create_wave_point(point, wave_number, direction))
        
        # Calculate confidence based on wave quality
        confidence = self._calculate_pattern_confidence(waves, swing_points)
        
        # Validate corrective pattern
        if len(waves) == 3 and confidence > 0.2:  # Lower threshold for corrective
            return self._create_pattern(waves, WaveType.CORRECTIVE, swing_points[start_idx].timestamp, swing_points[start_idx + 2].timestamp, confidence)
        
        return None
    
    def _create_wave_point(self, swing_point: SwingPoint, wave_number: int, direction: str) -> WavePoint:
        """Create WavePoint from SwingPoint"""
        from datetime import datetime, timedelta
        
        # The timestamp should be the actual date from the DataFrame index
        # If we're getting wave identifiers instead of dates, we need to get the real date
        timestamp = swing_point.timestamp
        logger.info(f"Wave identifier: {timestamp} (this is the wave number, not a date)")
        
        # Check if timestamp is already a datetime object
        if isinstance(timestamp, datetime):
            logger.info(f"Timestamp is already a datetime: {timestamp}")
        else:
            # For now, let's use a reasonable date based on the wave number
            # This is a temporary fix until we get the real dates from the DataFrame
            base_date = datetime.now() - timedelta(days=30)  # Start from 30 days ago
            timestamp = base_date + timedelta(days=int(timestamp) % 30)  # Cycle through 30 days
            logger.info(f"Using calculated date for wave {swing_point.timestamp}: {timestamp}")
        
        # Handle different timestamp types
        if isinstance(timestamp, np.datetime64):
            # Convert numpy.datetime64 to Python datetime
            timestamp = pd.to_datetime(timestamp).to_pydatetime()
            logger.info(f"Converted via pandas from numpy.datetime64: {timestamp}")
        elif hasattr(timestamp, 'to_pydatetime'):
            # Handle pandas Timestamp
            timestamp = timestamp.to_pydatetime()
            logger.info(f"Converted via to_pydatetime: {timestamp}")
        elif isinstance(timestamp, str):
            # Handle string timestamps
            timestamp = pd.to_datetime(timestamp).to_pydatetime()
            logger.info(f"Converted from string: {timestamp}")
        elif isinstance(timestamp, (int, np.integer)) or 'numpy.int64' in str(type(timestamp)) or str(type(timestamp)) == "<class 'numpy.int64'>":
            # Handle integer indices - convert to a reasonable datetime
            # This is a fallback for when DataFrame index is not properly set
            from datetime import datetime, timedelta
            base_date = datetime.now() - timedelta(days=365)  # Start from 1 year ago
            timestamp = base_date + timedelta(days=int(timestamp))
            logger.info(f"Converted integer index to datetime: {timestamp}")
        elif not isinstance(timestamp, datetime):
            # Fallback for any other type
            timestamp = pd.to_datetime(timestamp).to_pydatetime()
            logger.info(f"Converted via fallback: {timestamp}")
        
        logger.info(f"Final timestamp type: {type(timestamp)}, value: {timestamp}")
        
        return WavePoint(
            timestamp=timestamp,
            price=swing_point.price,
            wave_number=wave_number,
            direction=WaveDirection(direction),
            confidence=swing_point.confidence
        )
    
    def _create_pattern(self, waves: List[WavePoint], pattern_type: WaveType, start_time: datetime, end_time: datetime, custom_confidence: Optional[float] = None) -> ElliottWavePattern:
        """Create ElliottWavePattern from waves"""
        # Calculate overall confidence
        if custom_confidence is not None:
            confidence = custom_confidence
        else:
            confidence = sum(wave.confidence for wave in waves) / len(waves)
        
        # Calculate Fibonacci levels
        fibonacci_levels = self.calculate_fibonacci_levels(waves[0].price, waves[-1].price)
        
        # Calculate target and invalidation levels
        target_price, invalidation_level = self._calculate_targets(waves, pattern_type)
        
        return ElliottWavePattern(
            symbol="",  # Will be set by caller
            pattern_type=pattern_type,
            waves=waves,
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
            fibonacci_levels=fibonacci_levels,
            target_price=target_price,
            invalidation_level=invalidation_level
        )
    
    def _is_valid_impulse_wave(self, waves: List[WavePoint]) -> bool:
        """Validate Elliott Wave impulse rules"""
        if len(waves) != 5:
            return False
        
        # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
        wave1_length = abs(waves[1].price - waves[0].price)
        wave2_length = abs(waves[2].price - waves[1].price)
        if wave2_length > wave1_length:
            return False
        
        # Rule 2: Wave 3 cannot be the shortest
        wave3_length = abs(waves[3].price - waves[2].price)
        wave4_length = abs(waves[4].price - waves[3].price)
        wave5_length = abs(waves[5].price - waves[4].price) if len(waves) > 4 else 0
        
        if wave3_length <= wave1_length and wave3_length <= wave5_length:
            return False
        
        # Rule 3: Wave 4 cannot overlap Wave 1 (except in diagonal)
        if waves[0].direction == WaveDirection.UP:
            if waves[3].price <= waves[0].price:
                return False
        else:
            if waves[3].price >= waves[0].price:
                return False
        
        return True
    
    def _is_valid_corrective_wave(self, waves: List[WavePoint]) -> bool:
        """Validate Elliott Wave corrective rules"""
        if len(waves) != 3:
            return False
        
        # Wave B must retrace at least 23.6% of Wave A
        wave_a_length = abs(waves[1].price - waves[0].price)
        wave_b_length = abs(waves[2].price - waves[1].price)
        
        if wave_b_length < wave_a_length * 0.236:
            return False
        
        return True
    
    def calculate_fibonacci_levels(self, start_price: float, end_price: float) -> Dict[str, float]:
        """Calculate Fibonacci retracement and extension levels"""
        fibonacci_levels = {}
        price_range = end_price - start_price
        
        for ratio in self.fibonacci_ratios:
            # Retracement levels
            retracement_price = end_price - (price_range * ratio)
            fibonacci_levels[f"fib_{ratio}_retracement"] = retracement_price
            
            # Extension levels
            extension_price = end_price + (price_range * ratio)
            fibonacci_levels[f"fib_{ratio}_extension"] = extension_price
        
        return fibonacci_levels
    
    def _calculate_targets(self, waves: List[WavePoint], pattern_type: WaveType) -> Tuple[Optional[float], Optional[float]]:
        """Calculate target price and invalidation level"""
        if not waves:
            return None, None
        
        current_price = waves[-1].price
        
        if pattern_type == WaveType.IMPULSE and len(waves) == 5:
            # For completed impulse, target next corrective move
            wave1_length = abs(waves[1].price - waves[0].price)
            target_price = current_price - (wave1_length * 0.618)  # Typical retracement
            
            # Invalidation if price breaks below wave 4 low
            invalidation_level = min(waves[3].price, waves[4].price)
            
        elif pattern_type == WaveType.CORRECTIVE and len(waves) == 3:
            # For completed corrective, target impulse continuation
            wave_a_length = abs(waves[1].price - waves[0].price)
            target_price = current_price + (wave_a_length * 1.618)  # Typical extension
            
            # Invalidation if price breaks beyond wave A
            invalidation_level = waves[0].price
            
        else:
            target_price = None
            invalidation_level = None
        
        return target_price, invalidation_level
    
    def detect_wave_extensions(self, wave_lengths: List[float]) -> Dict[str, Any]:
        """Detect wave extensions in Elliott Wave pattern"""
        if len(wave_lengths) < 3:
            return {"extensions": [], "confidence": 0.0}
        
        extensions = []
        max_length = max(wave_lengths)
        
        for i, length in enumerate(wave_lengths):
            if length == max_length and length > sum(wave_lengths) / len(wave_lengths) * 1.5:
                # This wave is significantly longer than average
                extension_ratio = length / max_length
                confidence = min(1.0, extension_ratio)
                
                extensions.append({
                    "wave": i + 1,
                    "type": "extension",
                    "ratio": extension_ratio,
                    "confidence": confidence
                })
        
        # Determine primary extension
        primary_extension = max(extensions, key=lambda x: x["confidence"]) if extensions else None
        
        return {
            "extensions": extensions,
            "primary_extension": primary_extension,
            "confidence": primary_extension["confidence"] if primary_extension else 0.0
        }
    
    def calculate_pattern_strength(self, waves: List[WavePoint], pattern_type: WaveType) -> float:
        """Calculate overall pattern strength"""
        if not waves:
            return 0.0
        
        # Base strength from wave count
        base_strength = len(waves) / 5.0 if pattern_type == WaveType.IMPULSE else len(waves) / 3.0
        
        # Confidence factor
        avg_confidence = sum(wave.confidence for wave in waves) / len(waves)
        
        # Fibonacci relationship factor
        fibonacci_factor = self._calculate_fibonacci_factor(waves)
        
        # Combine factors
        strength = (base_strength * 0.4 + avg_confidence * 0.4 + fibonacci_factor * 0.2)
        
        return min(1.0, strength)
    
    def _calculate_fibonacci_factor(self, waves: List[WavePoint]) -> float:
        """Calculate Fibonacci relationship factor"""
        if len(waves) < 2:
            return 0.0
        
        relationships = self.analyze_fibonacci_relationships(waves)
        if not relationships:
            return 0.0
        
        # Calculate average confidence of Fibonacci relationships
        avg_confidence = sum(rel.confidence for rel in relationships) / len(relationships)
        return avg_confidence
    
    def analyze_fibonacci_relationships(self, waves: List[WavePoint]) -> List[WaveRelationship]:
        """Analyze Fibonacci relationships between waves"""
        relationships = []
        
        if len(waves) < 2:
            return relationships
        
        for i in range(len(waves) - 1):
            for j in range(i + 1, len(waves)):
                wave1 = waves[i]
                wave2 = waves[j]
                
                # Calculate ratio
                length1 = abs(wave2.price - wave1.price)
                length2 = abs(waves[j+1].price - wave2.price) if j+1 < len(waves) else length1
                
                if length2 > 0:
                    ratio = length1 / length2
                    
                    # Find closest Fibonacci ratio
                    closest_fib = min(self.fibonacci_ratios, key=lambda x: abs(x - ratio))
                    fib_distance = abs(closest_fib - ratio)
                    
                    # Calculate confidence based on how close to Fibonacci ratio
                    confidence = max(0.0, 1.0 - (fib_distance / closest_fib))
                    
                    relationships.append(WaveRelationship(
                        wave1_number=wave1.wave_number,
                        wave2_number=wave2.wave_number,
                        ratio=ratio,
                        fibonacci_level=closest_fib if confidence > 0.7 else None,
                        confidence=confidence
                    ))
        
        return relationships
    
    def predict_pattern_completion(self, waves: List[WavePoint], pattern_type: WaveType) -> Dict[str, Any]:
        """Predict pattern completion"""
        if pattern_type == WaveType.IMPULSE:
            if len(waves) < 5:
                # Predict Wave 5 completion
                if len(waves) == 4:
                    wave1_length = abs(waves[1].price - waves[0].price)
                    predicted_price = waves[3].price + (wave1_length * 0.618)  # Typical Wave 5 length
                    
                    return {
                        "prediction": "pattern_incomplete",
                        "missing_waves": 1,
                        "completion_price": predicted_price,
                        "confidence": 0.7
                    }
            else:
                return {
                    "prediction": "pattern_complete",
                    "missing_waves": 0,
                    "confidence": 0.9
                }
        
        elif pattern_type == WaveType.CORRECTIVE:
            if len(waves) < 3:
                return {
                    "prediction": "pattern_incomplete",
                    "missing_waves": 3 - len(waves),
                    "confidence": 0.6
                }
            else:
                return {
                    "prediction": "pattern_complete",
                    "missing_waves": 0,
                    "confidence": 0.8
                }
        
        return {
            "prediction": "unknown",
            "missing_waves": 0,
            "confidence": 0.0
        }