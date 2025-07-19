"""
Regime Switching Strategy
========================

A sophisticated strategy that identifies market regimes and switches
between different trading approaches based on market conditions.
This strategy adapts to bull markets, bear markets, sideways markets,
and high/low volatility environments.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class RegimeSwitchingStrategy(BaseStrategy):
    """
    Regime Switching Strategy
    
    Features:
    - Market regime identification (bull, bear, sideways, volatile)
    - Dynamic strategy switching based on regime
    - Regime-specific parameter optimization
    - Multi-timeframe regime confirmation
    - Risk management per regime
    - Smooth regime transitions
    """
    
    def __init__(self, 
                 lookback_period: int = 100,
                 regime_confidence_threshold: float = 0.7,
                 min_regime_duration: int = 20,
                 **kwargs):
        super().__init__(name="Regime_Switching_Strategy", **kwargs)
        
        # Core parameters
        self.lookback_period = lookback_period
        self.regime_confidence_threshold = regime_confidence_threshold
        self.min_regime_duration = min_regime_duration
        
        # Regime-specific strategies
        self.regime_strategies = {
            'bull_market': self._bull_market_strategy,
            'bear_market': self._bear_market_strategy,
            'sideways_market': self._sideways_market_strategy,
            'high_volatility': self._high_volatility_strategy,
            'low_volatility': self._low_volatility_strategy
        }
        
        # Regime weights (how much to weight each regime)
        self.regime_weights = {
            'bull_market': 0.4,
            'bear_market': 0.3,
            'sideways_market': 0.2,
            'high_volatility': 0.05,
            'low_volatility': 0.05
        }
        
        # Regime state tracking
        self.current_regime = None
        self.regime_confidence = 0.0
        self.regime_duration = 0
        self.regime_history = []
        
    def identify_market_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify the current market regime"""
        
        if len(data) < self.lookback_period:
            return self._get_default_regime()
        
        # Calculate regime indicators
        trend_indicators = self._calculate_trend_indicators(data)
        volatility_indicators = self._calculate_volatility_indicators(data)
        momentum_indicators = self._calculate_momentum_indicators(data)
        
        # Determine primary regime
        regime_scores = self._calculate_regime_scores(
            trend_indicators, volatility_indicators, momentum_indicators
        )
        
        # Find dominant regime
        dominant_regime = max(regime_scores.items(), key=lambda x: x[1])
        regime_name = dominant_regime[0]
        regime_confidence = dominant_regime[1]
        
        # Update regime state
        if self.current_regime == regime_name:
            self.regime_duration += 1
        else:
            self.regime_duration = 1
            self.current_regime = regime_name
        
        # Store regime history
        self.regime_history.append({
            'regime': regime_name,
            'confidence': regime_confidence,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.regime_history) > 50:
            self.regime_history = self.regime_history[-50:]
        
        return {
            'regime': regime_name,
            'confidence': regime_confidence,
            'duration': self.regime_duration,
            'trend_indicators': trend_indicators,
            'volatility_indicators': volatility_indicators,
            'momentum_indicators': momentum_indicators,
            'regime_scores': regime_scores
        }
    
    def _calculate_trend_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate trend indicators"""
        
        # Price trend
        returns = data['Close'].pct_change().dropna()
        trend_strength = self._calculate_trend_strength(data)
        
        # Moving average alignment
        ma_alignment = self._calculate_ma_alignment(data)
        
        # Trend consistency
        trend_consistency = self._calculate_trend_consistency(data)
        
        return {
            'trend_strength': trend_strength,
            'ma_alignment': ma_alignment,
            'trend_consistency': trend_consistency,
            'avg_return': returns.mean(),
            'return_std': returns.std()
        }
    
    def _calculate_volatility_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volatility indicators"""
        
        returns = data['Close'].pct_change().dropna()
        
        # Current volatility
        current_volatility = returns.tail(20).std()
        
        # Historical volatility
        historical_volatility = returns.std()
        
        # Volatility ratio
        volatility_ratio = current_volatility / historical_volatility if historical_volatility > 0 else 1.0
        
        # Volatility trend
        volatility_trend = self._calculate_volatility_trend(data)
        
        return {
            'current_volatility': current_volatility,
            'historical_volatility': historical_volatility,
            'volatility_ratio': volatility_ratio,
            'volatility_trend': volatility_trend
        }
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate momentum indicators"""
        
        # RSI
        rsi = self._calculate_rsi(data, 14)
        
        # MACD
        macd_indicators = self._calculate_macd_indicators(data)
        
        # Price momentum
        price_momentum = self._calculate_price_momentum(data)
        
        # Volume momentum
        volume_momentum = self._calculate_volume_momentum(data)
        
        return {
            'rsi': rsi,
            'macd': macd_indicators,
            'price_momentum': price_momentum,
            'volume_momentum': volume_momentum
        }
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength"""
        
        if len(data) < 50:
            return 0.0
        
        # Linear regression slope
        x = np.arange(len(data))
        y = data['Close'].values
        
        slope, _ = np.polyfit(x, y, 1)
        
        # Normalize slope
        normalized_slope = abs(slope) / data['Close'].iloc[-1]
        
        return min(normalized_slope * 1000, 1.0)
    
    def _calculate_ma_alignment(self, data: pd.DataFrame) -> float:
        """Calculate moving average alignment"""
        
        if len(data) < 200:
            return 0.0
        
        current_price = data['Close'].iloc[-1]
        
        # Multiple moving averages
        ma_20 = data['Close'].rolling(20).mean().iloc[-1]
        ma_50 = data['Close'].rolling(50).mean().iloc[-1]
        ma_200 = data['Close'].rolling(200).mean().iloc[-1]
        
        # Check alignment
        above_ma20 = current_price > ma_20 if not pd.isna(ma_20) else False
        above_ma50 = current_price > ma_50 if not pd.isna(ma_50) else False
        above_ma200 = current_price > ma_200 if not pd.isna(ma_200) else False
        
        # Calculate alignment score
        alignment_score = 0.0
        if above_ma20:
            alignment_score += 0.3
        if above_ma50:
            alignment_score += 0.4
        if above_ma200:
            alignment_score += 0.3
        
        return alignment_score
    
    def _calculate_trend_consistency(self, data: pd.DataFrame) -> float:
        """Calculate trend consistency"""
        
        if len(data) < 20:
            return 0.0
        
        # Calculate directional consistency
        returns = data['Close'].pct_change().dropna()
        positive_returns = (returns > 0).sum()
        total_returns = len(returns)
        
        if total_returns == 0:
            return 0.0
        
        consistency = abs(positive_returns / total_returns - 0.5) * 2
        
        return consistency
    
    def _calculate_volatility_trend(self, data: pd.DataFrame) -> float:
        """Calculate volatility trend"""
        
        if len(data) < 40:
            return 0.0
        
        # Rolling volatility
        returns = data['Close'].pct_change().dropna()
        rolling_vol = returns.rolling(20).std()
        
        # Volatility trend
        recent_vol = rolling_vol.tail(10).mean()
        past_vol = rolling_vol.tail(30).head(20).mean()
        
        if past_vol == 0:
            return 0.0
        
        vol_trend = (recent_vol - past_vol) / past_vol
        
        return np.clip(vol_trend, -1, 1)
    
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
    
    def _calculate_macd_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD indicators"""
        
        if len(data) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'macd': macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0,
            'signal': signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0,
            'histogram': histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0
        }
    
    def _calculate_price_momentum(self, data: pd.DataFrame) -> float:
        """Calculate price momentum"""
        
        if len(data) < 20:
            return 0.0
        
        # Price change over 20 periods
        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-20]
        
        price_change = (current_price - past_price) / past_price
        
        return np.clip(price_change * 5, -1, 1)
    
    def _calculate_volume_momentum(self, data: pd.DataFrame) -> float:
        """Calculate volume momentum"""
        
        if len(data) < 20:
            return 0.0
        
        # Volume ratio
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        
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
    
    def _calculate_regime_scores(self, trend_indicators: Dict, 
                                volatility_indicators: Dict, 
                                momentum_indicators: Dict) -> Dict[str, float]:
        """Calculate scores for each market regime"""
        
        # Bull market score
        bull_score = (
            trend_indicators['trend_strength'] * 0.3 +
            trend_indicators['ma_alignment'] * 0.3 +
            (momentum_indicators['rsi'] - 50) / 50 * 0.2 +
            momentum_indicators['price_momentum'] * 0.2
        )
        
        # Bear market score
        bear_score = (
            -trend_indicators['trend_strength'] * 0.3 +
            (1 - trend_indicators['ma_alignment']) * 0.3 +
            (50 - momentum_indicators['rsi']) / 50 * 0.2 +
            -momentum_indicators['price_momentum'] * 0.2
        )
        
        # Sideways market score
        sideways_score = (
            (1 - abs(trend_indicators['trend_strength'])) * 0.4 +
            (1 - abs(momentum_indicators['price_momentum'])) * 0.3 +
            trend_indicators['trend_consistency'] * 0.3
        )
        
        # High volatility score
        high_vol_score = (
            volatility_indicators['volatility_ratio'] * 0.5 +
            volatility_indicators['volatility_trend'] * 0.3 +
            abs(momentum_indicators['price_momentum']) * 0.2
        )
        
        # Low volatility score
        low_vol_score = (
            (1 / volatility_indicators['volatility_ratio']) * 0.5 +
            -volatility_indicators['volatility_trend'] * 0.3 +
            (1 - abs(momentum_indicators['price_momentum'])) * 0.2
        )
        
        return {
            'bull_market': max(bull_score, 0),
            'bear_market': max(bear_score, 0),
            'sideways_market': max(sideways_score, 0),
            'high_volatility': max(high_vol_score, 0),
            'low_volatility': max(low_vol_score, 0)
        }
    
    def _get_default_regime(self) -> Dict[str, Any]:
        """Get default regime when insufficient data"""
        return {
            'regime': 'sideways_market',
            'confidence': 0.5,
            'duration': 0,
            'trend_indicators': {},
            'volatility_indicators': {},
            'momentum_indicators': {},
            'regime_scores': {}
        }
    
    def _bull_market_strategy(self, data: pd.DataFrame, regime_analysis: Dict) -> Dict[str, Any]:
        """Bull market strategy - trend following with momentum"""
        
        # Use trend following indicators
        rsi = regime_analysis['momentum_indicators']['rsi']
        macd = regime_analysis['momentum_indicators']['macd']
        price_momentum = regime_analysis['momentum_indicators']['price_momentum']
        
        # Bull market signals
        if (rsi < 70 and  # Not overbought
            macd['histogram'] > 0 and  # Positive MACD histogram
            price_momentum > 0.1):  # Positive momentum
            return {
                'signal': 'BUY',
                'confidence': min(0.8, 0.6 + price_momentum * 0.2),
                'reason': 'Bull market trend following'
            }
        elif rsi > 80:  # Overbought
            return {
                'signal': 'SELL',
                'confidence': 0.7,
                'reason': 'Bull market overbought'
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': 'Bull market waiting'
            }
    
    def _bear_market_strategy(self, data: pd.DataFrame, regime_analysis: Dict) -> Dict[str, Any]:
        """Bear market strategy - mean reversion and shorting"""
        
        # Use mean reversion indicators
        rsi = regime_analysis['momentum_indicators']['rsi']
        price_momentum = regime_analysis['momentum_indicators']['price_momentum']
        
        # Bear market signals
        if (rsi < 30 and  # Oversold
            price_momentum < -0.1):  # Negative momentum
            return {
                'signal': 'BUY',
                'confidence': 0.7,
                'reason': 'Bear market oversold bounce'
            }
        elif (rsi > 50 and  # Above neutral
              price_momentum > 0.1):  # Positive momentum
            return {
                'signal': 'SELL',
                'confidence': 0.8,
                'reason': 'Bear market rally short'
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': 'Bear market waiting'
            }
    
    def _sideways_market_strategy(self, data: pd.DataFrame, regime_analysis: Dict) -> Dict[str, Any]:
        """Sideways market strategy - range trading"""
        
        # Use range trading indicators
        rsi = regime_analysis['momentum_indicators']['rsi']
        price_momentum = regime_analysis['momentum_indicators']['price_momentum']
        
        # Sideways market signals
        if rsi < 30:  # Oversold
            return {
                'signal': 'BUY',
                'confidence': 0.6,
                'reason': 'Sideways market oversold'
            }
        elif rsi > 70:  # Overbought
            return {
                'signal': 'SELL',
                'confidence': 0.6,
                'reason': 'Sideways market overbought'
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': 'Sideways market neutral'
            }
    
    def _high_volatility_strategy(self, data: pd.DataFrame, regime_analysis: Dict) -> Dict[str, Any]:
        """High volatility strategy - breakout trading"""
        
        # Use breakout indicators
        volatility_ratio = regime_analysis['volatility_indicators']['volatility_ratio']
        price_momentum = regime_analysis['momentum_indicators']['price_momentum']
        
        # High volatility signals
        if (volatility_ratio > 1.5 and  # High volatility
            abs(price_momentum) > 0.2):  # Strong momentum
            if price_momentum > 0:
                return {
                    'signal': 'BUY',
                    'confidence': 0.7,
                    'reason': 'High volatility breakout up'
                }
            else:
                return {
                    'signal': 'SELL',
                    'confidence': 0.7,
                    'reason': 'High volatility breakout down'
                }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': 'High volatility waiting'
            }
    
    def _low_volatility_strategy(self, data: pd.DataFrame, regime_analysis: Dict) -> Dict[str, Any]:
        """Low volatility strategy - premium selling"""
        
        # Use premium selling indicators
        volatility_ratio = regime_analysis['volatility_indicators']['volatility_ratio']
        rsi = regime_analysis['momentum_indicators']['rsi']
        
        # Low volatility signals
        if (volatility_ratio < 0.7 and  # Low volatility
            rsi > 60):  # Slightly overbought
            return {
                'signal': 'SELL',
                'confidence': 0.6,
                'reason': 'Low volatility premium selling'
            }
        elif (volatility_ratio < 0.7 and  # Low volatility
              rsi < 40):  # Slightly oversold
            return {
                'signal': 'BUY',
                'confidence': 0.6,
                'reason': 'Low volatility value buying'
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': 'Low volatility waiting'
            }
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate regime switching trading signal"""
        
        if len(data) < self.lookback_period:
            return None
        
        # Identify market regime
        regime_analysis = self.identify_market_regime(data)
        current_regime = regime_analysis['regime']
        regime_confidence = regime_analysis['confidence']
        
        # Check regime confidence
        if regime_confidence < self.regime_confidence_threshold:
            return None
        
        # Get regime-specific strategy
        if current_regime in self.regime_strategies:
            strategy_result = self.regime_strategies[current_regime](data, regime_analysis)
        else:
            return None
        
        # Check if we have a valid signal
        if strategy_result['signal'] == 'HOLD':
            return None
        
        # Calculate position size based on regime
        base_position_size = 0.05  # 5% base position
        regime_weight = self.regime_weights.get(current_regime, 0.1)
        position_size = base_position_size * regime_weight
        
        # Adjust position size based on regime confidence
        position_size *= regime_confidence
        
        # Generate trade signal
        current_price = data['Close'].iloc[-1]
        quantity = (position_size * 10000) / current_price  # $10k base position
        
        # Prepare metadata
        metadata = {
            'strategy_name': self.name,
            'current_regime': current_regime,
            'regime_confidence': regime_confidence,
            'regime_duration': regime_analysis['duration'],
            'regime_analysis': regime_analysis,
            'strategy_result': strategy_result,
            'signal_type': 'regime_switching'
        }
        
        return TradeSignal(
            symbol=symbol,
            action=strategy_result['signal'],
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=strategy_result['confidence'],
            metadata=metadata
        ) 