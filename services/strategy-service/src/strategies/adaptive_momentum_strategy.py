"""
Adaptive Momentum Strategy
==========================

An advanced momentum strategy that dynamically adjusts its parameters
based on market conditions, volatility regimes, and trend strength.
This strategy adapts to changing market environments for optimal performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class AdaptiveMomentumStrategy(BaseStrategy):
    """
    Adaptive Momentum Strategy
    
    Features:
    - Dynamic parameter adjustment based on market conditions
    - Volatility regime detection and adaptation
    - Trend strength analysis
    - Multi-timeframe momentum confirmation
    - Risk-adjusted position sizing
    - Market regime classification
    """
    
    def __init__(self, 
                 base_momentum_period: int = 20,
                 volatility_lookback: int = 50,
                 trend_lookback: int = 100,
                 min_confidence: float = 0.6,
                 max_position_size: float = 0.1,
                 **kwargs):
        super().__init__(name="Adaptive_Momentum_Strategy", **kwargs)
        
        # Base parameters
        self.base_momentum_period = base_momentum_period
        self.volatility_lookback = volatility_lookback
        self.trend_lookback = trend_lookback
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        
        # Market regime thresholds
        self.high_volatility_threshold = 0.03  # 3% daily volatility
        self.low_volatility_threshold = 0.01   # 1% daily volatility
        self.trend_strength_threshold = 0.6    # 60% trend strength
        
        # Adaptive parameters
        self.current_momentum_period = base_momentum_period
        self.current_confidence_threshold = min_confidence
        self.current_position_size = max_position_size
        
        # Market state tracking
        self.market_regime = "normal"  # normal, high_vol, low_vol, trending, sideways
        self.volatility_regime = "normal"  # low, normal, high
        self.trend_strength = 0.0
        
    def calculate_adaptive_parameters(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate adaptive parameters based on market conditions"""
        
        if len(data) < self.trend_lookback:
            return self._get_default_parameters()
        
        # Calculate volatility
        returns = data['Close'].pct_change().dropna()
        current_volatility = returns.std()
        historical_volatility = returns.rolling(self.volatility_lookback).std().iloc[-1]
        
        # Calculate trend strength
        trend_strength = self._calculate_trend_strength(data)
        
        # Determine market regime
        market_regime = self._classify_market_regime(current_volatility, trend_strength)
        volatility_regime = self._classify_volatility_regime(current_volatility)
        
        # Update adaptive parameters
        adaptive_params = self._adapt_parameters(
            market_regime, volatility_regime, trend_strength, current_volatility
        )
        
        # Update state
        self.market_regime = market_regime
        self.volatility_regime = volatility_regime
        self.trend_strength = trend_strength
        
        return {
            'market_regime': market_regime,
            'volatility_regime': volatility_regime,
            'trend_strength': trend_strength,
            'current_volatility': current_volatility,
            'historical_volatility': historical_volatility,
            'adaptive_params': adaptive_params
        }
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength using multiple indicators"""
        
        if len(data) < 50:
            return 0.0
        
        # 1. Price trend strength
        price_trend = self._calculate_price_trend_strength(data)
        
        # 2. Volume trend strength
        volume_trend = self._calculate_volume_trend_strength(data)
        
        # 3. Momentum trend strength
        momentum_trend = self._calculate_momentum_trend_strength(data)
        
        # 4. Moving average alignment
        ma_alignment = self._calculate_ma_alignment(data)
        
        # Combine all trend strength indicators
        trend_strength = (price_trend * 0.4 + 
                         volume_trend * 0.2 + 
                         momentum_trend * 0.3 + 
                         ma_alignment * 0.1)
        
        return min(trend_strength, 1.0)
    
    def _calculate_price_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate price trend strength"""
        
        # Linear regression slope
        x = np.arange(len(data))
        y = data['Close'].values
        
        if len(x) < 2:
            return 0.0
        
        slope, _ = np.polyfit(x, y, 1)
        
        # Normalize slope by price level
        normalized_slope = abs(slope) / data['Close'].iloc[-1]
        
        # Convert to 0-1 scale
        trend_strength = min(normalized_slope * 1000, 1.0)
        
        return trend_strength
    
    def _calculate_volume_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate volume trend strength"""
        
        if len(data) < 20:
            return 0.0
        
        # Volume trend
        volume_ma = data['Volume'].rolling(20).mean()
        current_volume = data['Volume'].iloc[-1]
        avg_volume = volume_ma.iloc[-1]
        
        if avg_volume == 0:
            return 0.0
        
        volume_ratio = current_volume / avg_volume
        
        # Volume trend strength (0-1)
        if volume_ratio > 1.5:
            return min((volume_ratio - 1.5) / 0.5, 1.0)
        elif volume_ratio < 0.5:
            return 0.0
        else:
            return (volume_ratio - 0.5) / 1.0
    
    def _calculate_momentum_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate momentum trend strength"""
        
        if len(data) < 20:
            return 0.0
        
        # RSI trend
        rsi = self._calculate_rsi(data, 14)
        rsi_trend = abs(rsi - 50) / 50  # Distance from neutral
        
        # MACD trend
        macd_trend = self._calculate_macd_trend(data)
        
        # Combine momentum indicators
        momentum_strength = (rsi_trend * 0.6 + macd_trend * 0.4)
        
        return momentum_strength
    
    def _calculate_ma_alignment(self, data: pd.DataFrame) -> float:
        """Calculate moving average alignment"""
        
        if len(data) < 50:
            return 0.0
        
        # Multiple moving averages
        ma_20 = data['Close'].rolling(20).mean()
        ma_50 = data['Close'].rolling(50).mean()
        ma_200 = data['Close'].rolling(200).mean()
        
        current_price = data['Close'].iloc[-1]
        
        # Check alignment
        above_ma20 = current_price > ma_20.iloc[-1] if not pd.isna(ma_20.iloc[-1]) else False
        above_ma50 = current_price > ma_50.iloc[-1] if not pd.isna(ma_50.iloc[-1]) else False
        above_ma200 = current_price > ma_200.iloc[-1] if not pd.isna(ma_200.iloc[-1]) else False
        
        # Calculate alignment score
        alignment_score = 0.0
        if above_ma20:
            alignment_score += 0.3
        if above_ma50:
            alignment_score += 0.4
        if above_ma200:
            alignment_score += 0.3
        
        return alignment_score
    
    def _calculate_macd_trend(self, data: pd.DataFrame) -> float:
        """Calculate MACD trend strength"""
        
        if len(data) < 26:
            return 0.0
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        # MACD trend strength
        current_histogram = histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0
        prev_histogram = histogram.iloc[-2] if len(histogram) > 1 and not pd.isna(histogram.iloc[-2]) else 0
        
        # Normalize by price
        price_level = data['Close'].iloc[-1]
        normalized_histogram = abs(current_histogram) / price_level
        
        # Trend strength based on histogram change
        if current_histogram > 0 and current_histogram > prev_histogram:
            return min(normalized_histogram * 1000, 1.0)
        else:
            return 0.0
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate RSI"""
        
        if len(data) < period + 1:
            return 50.0
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _classify_market_regime(self, volatility: float, trend_strength: float) -> str:
        """Classify market regime"""
        
        if volatility > self.high_volatility_threshold:
            return "high_vol"
        elif volatility < self.low_volatility_threshold:
            return "low_vol"
        elif trend_strength > self.trend_strength_threshold:
            return "trending"
        elif trend_strength < 0.3:
            return "sideways"
        else:
            return "normal"
    
    def _classify_volatility_regime(self, volatility: float) -> str:
        """Classify volatility regime"""
        
        if volatility > self.high_volatility_threshold:
            return "high"
        elif volatility < self.low_volatility_threshold:
            return "low"
        else:
            return "normal"
    
    def _adapt_parameters(self, market_regime: str, volatility_regime: str, 
                         trend_strength: float, volatility: float) -> Dict[str, Any]:
        """Adapt strategy parameters based on market conditions"""
        
        # Base parameters
        momentum_period = self.base_momentum_period
        confidence_threshold = self.min_confidence
        position_size = self.max_position_size
        
        # Adapt based on market regime
        if market_regime == "high_vol":
            momentum_period = int(self.base_momentum_period * 0.7)  # Shorter period
            confidence_threshold = self.min_confidence * 1.2  # Higher confidence required
            position_size = self.max_position_size * 0.7  # Smaller positions
            
        elif market_regime == "low_vol":
            momentum_period = int(self.base_momentum_period * 1.3)  # Longer period
            confidence_threshold = self.min_confidence * 0.8  # Lower confidence threshold
            position_size = self.max_position_size * 1.2  # Larger positions
            
        elif market_regime == "trending":
            momentum_period = int(self.base_momentum_period * 0.8)  # Shorter period
            confidence_threshold = self.min_confidence * 0.9  # Lower confidence threshold
            position_size = self.max_position_size * 1.1  # Larger positions
            
        elif market_regime == "sideways":
            momentum_period = int(self.base_momentum_period * 1.5)  # Much longer period
            confidence_threshold = self.min_confidence * 1.3  # Higher confidence required
            position_size = self.max_position_size * 0.6  # Smaller positions
        
        # Adapt based on volatility regime
        if volatility_regime == "high":
            confidence_threshold *= 1.1
            position_size *= 0.8
        elif volatility_regime == "low":
            confidence_threshold *= 0.9
            position_size *= 1.1
        
        # Adapt based on trend strength
        if trend_strength > 0.8:
            confidence_threshold *= 0.8  # Lower threshold for strong trends
            position_size *= 1.2
        elif trend_strength < 0.3:
            confidence_threshold *= 1.2  # Higher threshold for weak trends
            position_size *= 0.7
        
        return {
            'momentum_period': max(momentum_period, 5),  # Minimum period
            'confidence_threshold': min(confidence_threshold, 0.9),  # Maximum threshold
            'position_size': min(position_size, 0.15)  # Maximum position size
        }
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters"""
        return {
            'market_regime': 'normal',
            'volatility_regime': 'normal',
            'trend_strength': 0.0,
            'current_volatility': 0.02,
            'historical_volatility': 0.02,
            'adaptive_params': {
                'momentum_period': self.base_momentum_period,
                'confidence_threshold': self.min_confidence,
                'position_size': self.max_position_size
            }
        }
    
    def calculate_momentum_signal(self, data: pd.DataFrame, adaptive_params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate momentum signal with adaptive parameters"""
        
        momentum_period = adaptive_params['momentum_period']
        
        if len(data) < momentum_period:
            return {'signal': 'HOLD', 'confidence': 0.0, 'strength': 0.0}
        
        # Calculate momentum indicators
        price_momentum = self._calculate_price_momentum(data, momentum_period)
        volume_momentum = self._calculate_volume_momentum(data, momentum_period)
        rsi_momentum = self._calculate_rsi_momentum(data)
        
        # Combine momentum signals
        momentum_score = (price_momentum * 0.5 + 
                         volume_momentum * 0.3 + 
                         rsi_momentum * 0.2)
        
        # Determine signal
        if momentum_score > 0.3:
            signal = "BUY"
            confidence = min(momentum_score, 0.95)
        elif momentum_score < -0.3:
            signal = "SELL"
            confidence = min(abs(momentum_score), 0.95)
        else:
            signal = "HOLD"
            confidence = 0.0
        
        return {
            'signal': signal,
            'confidence': confidence,
            'strength': momentum_score,
            'price_momentum': price_momentum,
            'volume_momentum': volume_momentum,
            'rsi_momentum': rsi_momentum
        }
    
    def _calculate_price_momentum(self, data: pd.DataFrame, period: int) -> float:
        """Calculate price momentum"""
        
        if len(data) < period:
            return 0.0
        
        # Price change over period
        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-period]
        
        price_change = (current_price - past_price) / past_price
        
        # Normalize to -1 to 1 range
        return np.clip(price_change * 10, -1, 1)
    
    def _calculate_volume_momentum(self, data: pd.DataFrame, period: int) -> float:
        """Calculate volume momentum"""
        
        if len(data) < period:
            return 0.0
        
        # Volume ratio
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(period).mean().iloc[-1]
        
        if avg_volume == 0:
            return 0.0
        
        volume_ratio = current_volume / avg_volume
        
        # Normalize to -1 to 1 range
        if volume_ratio > 1.5:
            return min((volume_ratio - 1.5) / 0.5, 1.0)
        elif volume_ratio < 0.5:
            return -min((0.5 - volume_ratio) / 0.5, 1.0)
        else:
            return (volume_ratio - 1.0) * 2
    
    def _calculate_rsi_momentum(self, data: pd.DataFrame) -> float:
        """Calculate RSI momentum"""
        
        rsi = self._calculate_rsi(data, 14)
        
        # RSI momentum (distance from neutral)
        rsi_momentum = (rsi - 50) / 50
        
        return np.clip(rsi_momentum, -1, 1)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate adaptive momentum trading signal"""
        
        if len(data) < self.trend_lookback:
            return None
        
        # Calculate adaptive parameters
        market_analysis = self.calculate_adaptive_parameters(data)
        adaptive_params = market_analysis['adaptive_params']
        
        # Calculate momentum signal
        momentum_signal = self.calculate_momentum_signal(data, adaptive_params)
        
        # Check confidence threshold
        if momentum_signal['confidence'] < adaptive_params['confidence_threshold']:
            return None
        
        # Generate trade signal
        current_price = data['Close'].iloc[-1]
        position_size = adaptive_params['position_size']
        
        # Calculate quantity based on position size
        quantity = (position_size * 10000) / current_price  # $10k base position
        
        # Prepare metadata
        metadata = {
            'strategy_name': self.name,
            'market_regime': market_analysis['market_regime'],
            'volatility_regime': market_analysis['volatility_regime'],
            'trend_strength': market_analysis['trend_strength'],
            'current_volatility': market_analysis['current_volatility'],
            'adaptive_params': adaptive_params,
            'momentum_signal': momentum_signal,
            'signal_type': 'adaptive_momentum'
        }
        
        return TradeSignal(
            symbol=symbol,
            action=momentum_signal['signal'],
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=momentum_signal['confidence'],
            metadata=metadata
        ) 