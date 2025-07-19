"""
Ichimoku Strategy
================

The Ichimoku strategy uses the Ichimoku Cloud (Ichimoku Kinko Hyo) to provide
comprehensive entry and exit signals. It combines multiple indicators:

- Tenkan-sen (Conversion Line): 9-period average
- Kijun-sen (Base Line): 26-period average  
- Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted 26 periods
- Senkou Span B (Leading Span B): 52-period average, shifted 26 periods
- Chikou Span (Lagging Span): Current price, shifted 26 periods back

Key signals:
- Price above/below the cloud (trend direction)
- Cloud color (bullish/bearish)
- Tenkan/Kijun crossovers
- Chikou Span position relative to price
- Support/resistance from cloud boundaries
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)

class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku Cloud Strategy
    
    Features:
    - Trend direction identification
    - Entry/exit price levels
    - Support/resistance zones
    - Multiple confirmation signals
    - Cloud color analysis
    """
    
    def __init__(self, 
                 tenkan_period: int = 9,
                 kijun_period: int = 26,
                 senkou_b_period: int = 52,
                 displacement: int = 26,
                 **kwargs):
        super().__init__(name="Ichimoku_Strategy", **kwargs)
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement
        
        # Signal thresholds
        self.cloud_threshold = 0.02  # 2% minimum cloud thickness
        self.crossover_threshold = 0.01  # 1% minimum crossover distance
        self.confidence_threshold = 0.6  # Minimum confidence for signals
    
    def calculate_ichimoku(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all Ichimoku indicators"""
        if len(data) < self.senkou_b_period + self.displacement:
            return data
        
        # Calculate Tenkan-sen (Conversion Line)
        high_9 = data['High'].rolling(window=self.tenkan_period).max()
        low_9 = data['Low'].rolling(window=self.tenkan_period).min()
        data['Tenkan'] = (high_9 + low_9) / 2
        
        # Calculate Kijun-sen (Base Line)
        high_26 = data['High'].rolling(window=self.kijun_period).max()
        low_26 = data['Low'].rolling(window=self.kijun_period).min()
        data['Kijun'] = (high_26 + low_26) / 2
        
        # Calculate Senkou Span A (Leading Span A)
        data['Senkou_A'] = ((data['Tenkan'] + data['Kijun']) / 2).shift(self.displacement)
        
        # Calculate Senkou Span B (Leading Span B)
        high_52 = data['High'].rolling(window=self.senkou_b_period).max()
        low_52 = data['Low'].rolling(window=self.senkou_b_period).min()
        data['Senkou_B'] = ((high_52 + low_52) / 2).shift(self.displacement)
        
        # Calculate Chikou Span (Lagging Span)
        data['Chikou'] = data['Close'].shift(-self.displacement)
        
        return data
    
    def analyze_cloud_position(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price position relative to the cloud"""
        if len(data) < 2:
            return {}
        
        current_price = data['Close'].iloc[-1]
        senkou_a = data['Senkou_A'].iloc[-1]
        senkou_b = data['Senkou_B'].iloc[-1]
        
        # Determine cloud position
        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)
        
        # Check if price is above/below cloud
        above_cloud = current_price > cloud_top
        below_cloud = current_price < cloud_bottom
        inside_cloud = not above_cloud and not below_cloud
        
        # Cloud color (bullish if Senkou A > Senkou B)
        cloud_bullish = senkou_a > senkou_b if not pd.isna(senkou_a) and not pd.isna(senkou_b) else False
        
        # Cloud thickness
        cloud_thickness = (cloud_top - cloud_bottom) / current_price if cloud_top > cloud_bottom else 0
        
        return {
            'above_cloud': above_cloud,
            'below_cloud': below_cloud,
            'inside_cloud': inside_cloud,
            'cloud_bullish': cloud_bullish,
            'cloud_thickness': cloud_thickness,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'current_price': current_price
        }
    
    def analyze_tenkan_kijun_crossover(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Tenkan/Kijun crossover signals"""
        if len(data) < 2:
            return {}
        
        current_tenkan = data['Tenkan'].iloc[-1]
        current_kijun = data['Kijun'].iloc[-1]
        prev_tenkan = data['Tenkan'].iloc[-2]
        prev_kijun = data['Kijun'].iloc[-2]
        
        # Check for crossovers
        bullish_crossover = (prev_tenkan <= prev_kijun) and (current_tenkan > current_kijun)
        bearish_crossover = (prev_tenkan >= prev_kijun) and (current_tenkan < current_kijun)
        
        # Calculate crossover strength
        crossover_distance = abs(current_tenkan - current_kijun) / current_tenkan if current_tenkan > 0 else 0
        
        return {
            'bullish_crossover': bullish_crossover,
            'bearish_crossover': bearish_crossover,
            'crossover_distance': crossover_distance,
            'tenkan_above_kijun': current_tenkan > current_kijun,
            'current_tenkan': current_tenkan,
            'current_kijun': current_kijun
        }
    
    def analyze_chikou_position(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Chikou Span position"""
        if len(data) < self.displacement + 1:
            return {}
        
        current_price = data['Close'].iloc[-1]
        chikou_value = data['Chikou'].iloc[-self.displacement-1]  # 26 periods back
        
        if pd.isna(chikou_value):
            return {}
        
        # Chikou should be above price for bullish signal
        chikou_bullish = chikou_value > current_price
        chikou_bearish = chikou_value < current_price
        
        # Calculate strength
        chikou_strength = abs(chikou_value - current_price) / current_price
        
        return {
            'chikou_bullish': chikou_bullish,
            'chikou_bearish': chikou_bearish,
            'chikou_strength': chikou_strength,
            'chikou_value': chikou_value,
            'current_price': current_price
        }
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels"""
        if len(data) < 2:
            return {}
        
        current_price = data['Close'].iloc[-1]
        senkou_a = data['Senkou_A'].iloc[-1]
        senkou_b = data['Senkou_B'].iloc[-1]
        kijun = data['Kijun'].iloc[-1]
        
        # Support levels
        support_levels = []
        if not pd.isna(senkou_a):
            support_levels.append(senkou_a)
        if not pd.isna(senkou_b):
            support_levels.append(senkou_b)
        if not pd.isna(kijun):
            support_levels.append(kijun)
        
        # Resistance levels
        resistance_levels = []
        if not pd.isna(senkou_a):
            resistance_levels.append(senkou_a)
        if not pd.isna(senkou_b):
            resistance_levels.append(senkou_b)
        if not pd.isna(kijun):
            resistance_levels.append(kijun)
        
        # Find nearest support and resistance
        nearest_support = max([s for s in support_levels if s < current_price], default=None)
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
        
        return {
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }
    
    def calculate_signal_confidence(self, 
                                  cloud_analysis: Dict[str, Any],
                                  crossover_analysis: Dict[str, Any],
                                  chikou_analysis: Dict[str, Any],
                                  support_resistance: Dict[str, Any]) -> float:
        """Calculate overall signal confidence"""
        confidence = 0.0
        
        # Cloud position (40% weight)
        if cloud_analysis.get('above_cloud') and cloud_analysis.get('cloud_bullish'):
            confidence += 0.4
        elif cloud_analysis.get('below_cloud') and not cloud_analysis.get('cloud_bullish'):
            confidence += 0.4
        elif cloud_analysis.get('inside_cloud'):
            confidence += 0.2
        
        # Crossover signals (30% weight)
        if crossover_analysis.get('bullish_crossover'):
            confidence += 0.3
        elif crossover_analysis.get('bearish_crossover'):
            confidence += 0.3
        elif crossover_analysis.get('crossover_distance', 0) > self.crossover_threshold:
            confidence += 0.15
        
        # Chikou position (20% weight)
        if chikou_analysis.get('chikou_bullish'):
            confidence += 0.2
        elif chikou_analysis.get('chikou_bearish'):
            confidence += 0.2
        elif chikou_analysis.get('chikou_strength', 0) > 0.02:
            confidence += 0.1
        
        # Cloud thickness (10% weight)
        cloud_thickness = cloud_analysis.get('cloud_thickness', 0)
        if cloud_thickness > self.cloud_threshold:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Ichimoku-based trading signal"""
        
        if len(data) < self.senkou_b_period + self.displacement:
            return None
        
        # Calculate Ichimoku indicators
        data = self.calculate_ichimoku(data)
        
        # Analyze different components
        cloud_analysis = self.analyze_cloud_position(data)
        crossover_analysis = self.analyze_tenkan_kijun_crossover(data)
        chikou_analysis = self.analyze_chikou_position(data)
        support_resistance = self.calculate_support_resistance(data)
        
        # Calculate confidence
        confidence = self.calculate_signal_confidence(
            cloud_analysis, crossover_analysis, chikou_analysis, support_resistance
        )
        
        if confidence < self.confidence_threshold:
            return None
        
        # Determine signal direction
        current_price = data['Close'].iloc[-1]
        action = None
        
        # Bullish conditions
        bullish_conditions = (
            cloud_analysis.get('above_cloud', False) and
            cloud_analysis.get('cloud_bullish', False) and
            (crossover_analysis.get('bullish_crossover', False) or 
             crossover_analysis.get('tenkan_above_kijun', False)) and
            chikou_analysis.get('chikou_bullish', False)
        )
        
        # Bearish conditions
        bearish_conditions = (
            cloud_analysis.get('below_cloud', False) and
            not cloud_analysis.get('cloud_bullish', False) and
            (crossover_analysis.get('bearish_crossover', False) or 
             not crossover_analysis.get('tenkan_above_kijun', False)) and
            chikou_analysis.get('chikou_bearish', False)
        )
        
        if bullish_conditions:
            action = "BUY"
        elif bearish_conditions:
            action = "SELL"
        else:
            return None
        
        # Calculate position size based on confidence
        quantity = self._calculate_quantity(current_price, confidence)
        
        # Prepare metadata
        metadata = {
            'strategy_name': self.name,
            'cloud_analysis': cloud_analysis,
            'crossover_analysis': crossover_analysis,
            'chikou_analysis': chikou_analysis,
            'support_resistance': support_resistance,
            'tenkan': data['Tenkan'].iloc[-1],
            'kijun': data['Kijun'].iloc[-1],
            'senkou_a': data['Senkou_A'].iloc[-1],
            'senkou_b': data['Senkou_B'].iloc[-1],
            'chikou': data['Chikou'].iloc[-1],
            'signal_type': 'ichimoku_cloud'
        }
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata=metadata
        )
    
    def _calculate_quantity(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_quantity = 1000 / price  # $1000 base position
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1x based on confidence
        return base_quantity * confidence_multiplier
    
    def get_entry_exit_prices(self, data: pd.DataFrame) -> Dict[str, float]:
        """Get recommended entry and exit prices"""
        if len(data) < self.senkou_b_period + self.displacement:
            return {}
        
        data = self.calculate_ichimoku(data)
        current_price = data['Close'].iloc[-1]
        
        # Entry prices
        tenkan = data['Tenkan'].iloc[-1]
        kijun = data['Kijun'].iloc[-1]
        senkou_a = data['Senkou_A'].iloc[-1]
        senkou_b = data['Senkou_B'].iloc[-1]
        
        # Support and resistance levels
        support_resistance = self.calculate_support_resistance(data)
        nearest_support = support_resistance.get('nearest_support')
        nearest_resistance = support_resistance.get('nearest_resistance')
        
        return {
            'entry_price': current_price,
            'stop_loss': nearest_support if nearest_support else current_price * 0.95,
            'take_profit': nearest_resistance if nearest_resistance else current_price * 1.05,
            'tenkan_level': tenkan,
            'kijun_level': kijun,
            'senkou_a_level': senkou_a,
            'senkou_b_level': senkou_b,
            'support_level': nearest_support,
            'resistance_level': nearest_resistance
        } 