"""
Market Regime Adaptive Strategy - Adapts to different market conditions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RegimeMetrics:
    """Market regime metrics"""
    regime: MarketRegime
    trend_strength: float
    volatility: float
    momentum: float
    mean_reversion_strength: float
    regime_confidence: float


class MarketRegimeAdaptiveStrategy(BaseStrategy):
    """
    Market Regime Adaptive Strategy that adjusts trading approach based on market conditions.
    
    Regime Detection:
    - Trending Up: Strong positive momentum, low volatility
    - Trending Down: Strong negative momentum, low volatility  
    - Sideways: Low momentum, low volatility
    - Volatile: High volatility, mixed momentum
    - Low Volatility: Very low volatility, range-bound
    
    Strategy Adaptation:
    - Trending: Momentum strategies, trend following
    - Sideways: Mean reversion, range trading
    - Volatile: Volatility strategies, options
    - Low Volatility: Breakout strategies, momentum
    """
    
    def __init__(self, 
                 regime_lookback: int = 50,      # 50-day regime detection
                 volatility_threshold: float = 0.2,  # 20% volatility threshold
                 trend_threshold: float = 0.02,      # 2% trend threshold
                 regime_confidence_threshold: float = 0.6,  # 60% confidence
                 **kwargs):
        super().__init__("Market_Regime_Adaptive_Strategy", kwargs)
        
        self.regime_lookback = regime_lookback
        self.volatility_threshold = volatility_threshold
        self.trend_threshold = trend_threshold
        self.regime_confidence_threshold = regime_confidence_threshold
        
        # Regime state
        self.current_regime = MarketRegime.SIDEWAYS
        self.regime_history = []
        self.regime_metrics = None
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signal adapted to current market regime"""
        try:
            if len(data) < self.regime_lookback:
                return None
            
            # Detect current market regime
            regime_metrics = self._detect_market_regime(data)
            self.regime_metrics = regime_metrics
            
            # Only trade if regime confidence is high enough
            if regime_metrics.regime_confidence < self.regime_confidence_threshold:
                return None
            
            # Generate regime-specific signal
            signal = self._generate_regime_specific_signal(symbol, data, regime_metrics)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _detect_market_regime(self, data: pd.DataFrame) -> RegimeMetrics:
        """Detect current market regime using multiple indicators"""
        
        try:
            # Calculate returns
            returns = data['Close'].pct_change().dropna()
            
            # Volatility (annualized)
            volatility = returns.rolling(self.regime_lookback).std().iloc[-1] * np.sqrt(252)
            
            # Trend strength (linear regression slope)
            prices = data['Close'].iloc[-self.regime_lookback:]
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            trend_strength = slope / prices.iloc[0]  # Normalized slope
            
            # Momentum (rate of change)
            momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
            
            # Mean reversion strength (autocorrelation)
            autocorr = returns.autocorr(lag=1) if len(returns) > 1 else 0
            mean_reversion_strength = abs(autocorr)
            
            # Determine regime based on metrics
            regime, confidence = self._classify_regime(
                volatility, trend_strength, momentum, mean_reversion_strength
            )
            
            return RegimeMetrics(
                regime=regime,
                trend_strength=trend_strength,
                volatility=volatility,
                momentum=momentum,
                mean_reversion_strength=mean_reversion_strength,
                regime_confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return RegimeMetrics(
                MarketRegime.SIDEWAYS, 0.0, 0.2, 0.0, 0.0, 0.5
            )
    
    def _classify_regime(self, volatility: float, trend_strength: float, 
                        momentum: float, mean_reversion: float) -> Tuple[MarketRegime, float]:
        """Classify market regime based on metrics"""
        
        confidence = 0.0
        
        # High volatility regime
        if volatility > self.volatility_threshold:
            if abs(momentum) > self.trend_threshold:
                regime = MarketRegime.TRENDING_UP if momentum > 0 else MarketRegime.TRENDING_DOWN
                confidence = min(0.9, abs(momentum) / 0.05)
            else:
                regime = MarketRegime.VOLATILE
                confidence = min(0.8, volatility / 0.3)
        
        # Low volatility regime
        elif volatility < self.volatility_threshold * 0.5:
            if abs(trend_strength) > self.trend_threshold:
                regime = MarketRegime.TRENDING_UP if trend_strength > 0 else MarketRegime.TRENDING_DOWN
                confidence = min(0.9, abs(trend_strength) / 0.05)
            else:
                regime = MarketRegime.LOW_VOLATILITY
                confidence = 0.7
        
        # Medium volatility regime
        else:
            if abs(trend_strength) > self.trend_threshold:
                regime = MarketRegime.TRENDING_UP if trend_strength > 0 else MarketRegime.TRENDING_DOWN
                confidence = min(0.8, abs(trend_strength) / 0.05)
            elif mean_reversion > 0.3:
                regime = MarketRegime.SIDEWAYS
                confidence = min(0.8, mean_reversion)
            else:
                regime = MarketRegime.SIDEWAYS
                confidence = 0.6
        
        return regime, confidence
    
    def _generate_regime_specific_signal(self, symbol: str, data: pd.DataFrame, 
                                       regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Generate signal based on current market regime"""
        
        try:
            current_price = data['Close'].iloc[-1]
            
            if regime_metrics.regime == MarketRegime.TRENDING_UP:
                signal = self._trending_up_strategy(symbol, data, regime_metrics)
            elif regime_metrics.regime == MarketRegime.TRENDING_DOWN:
                signal = self._trending_down_strategy(symbol, data, regime_metrics)
            elif regime_metrics.regime == MarketRegime.SIDEWAYS:
                signal = self._sideways_strategy(symbol, data, regime_metrics)
            elif regime_metrics.regime == MarketRegime.VOLATILE:
                signal = self._volatile_strategy(symbol, data, regime_metrics)
            elif regime_metrics.regime == MarketRegime.LOW_VOLATILITY:
                signal = self._low_volatility_strategy(symbol, data, regime_metrics)
            else:
                return None
            
            if signal:
                # Add regime information to metadata
                signal.metadata['market_regime'] = regime_metrics.regime.value
                signal.metadata['regime_confidence'] = regime_metrics.regime_confidence
                signal.metadata['regime_metrics'] = {
                    'trend_strength': regime_metrics.trend_strength,
                    'volatility': regime_metrics.volatility,
                    'momentum': regime_metrics.momentum,
                    'mean_reversion_strength': regime_metrics.mean_reversion_strength
                }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating regime-specific signal: {e}")
            return None
    
    def _trending_up_strategy(self, symbol: str, data: pd.DataFrame, 
                             regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Momentum strategy for trending up markets"""
        
        try:
            # Calculate momentum indicators
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            # MACD for trend confirmation
            macd, signal = self._calculate_macd(data['Close'])
            macd_histogram = macd - signal
            
            # RSI for overbought/oversold
            rsi = self._calculate_rsi(data['Close'])
            
            # Momentum signals
            price_above_sma = current_price > sma_20 > sma_50
            macd_positive = macd_histogram > 0
            rsi_not_overbought = rsi < 80
            
            if price_above_sma and macd_positive and rsi_not_overbought:
                # Calculate position size based on trend strength
                position_size = self._calculate_trend_position_size(
                    current_price, regime_metrics.trend_strength
                )
                
                confidence = min(0.8, regime_metrics.regime_confidence)
                
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    quantity=position_size,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=confidence,
                    metadata={'regime': 'trending_up', 'trend_strength': regime_metrics.trend_strength}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in trending up strategy: {e}")
            return None
    
    def _trending_down_strategy(self, symbol: str, data: pd.DataFrame, 
                               regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Short strategy for trending down markets"""
        
        try:
            # Calculate momentum indicators
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            # MACD for trend confirmation
            macd, signal = self._calculate_macd(data['Close'])
            macd_histogram = macd - signal
            
            # RSI for oversold conditions
            rsi = self._calculate_rsi(data['Close'])
            
            # Downward momentum signals
            price_below_sma = current_price < sma_20 < sma_50
            macd_negative = macd_histogram < 0
            rsi_not_oversold = rsi > 20
            
            if price_below_sma and macd_negative and rsi_not_oversold:
                position_size = self._calculate_trend_position_size(
                    current_price, abs(regime_metrics.trend_strength)
                )
                
                confidence = min(0.8, regime_metrics.regime_confidence)
                
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    quantity=position_size,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=confidence,
                    metadata={'regime': 'trending_down', 'trend_strength': regime_metrics.trend_strength}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in trending down strategy: {e}")
            return None
    
    def _sideways_strategy(self, symbol: str, data: pd.DataFrame, 
                          regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Mean reversion strategy for sideways markets"""
        
        try:
            current_price = data['Close'].iloc[-1]
            
            # Bollinger Bands for range trading
            bb_upper, bb_lower = self._calculate_bollinger_bands(data['Close'])
            bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            
            # RSI for mean reversion
            rsi = self._calculate_rsi(data['Close'])
            
            # Mean reversion signals
            if bb_position < 0.2 and rsi < 30:  # Oversold
                position_size = self._calculate_mean_reversion_position_size(
                    current_price, regime_metrics.mean_reversion_strength
                )
                
                confidence = min(0.7, regime_metrics.regime_confidence)
                
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    quantity=position_size,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=confidence,
                    metadata={'regime': 'sideways', 'bb_position': bb_position, 'rsi': rsi}
                )
            
            elif bb_position > 0.8 and rsi > 70:  # Overbought
                position_size = self._calculate_mean_reversion_position_size(
                    current_price, regime_metrics.mean_reversion_strength
                )
                
                confidence = min(0.7, regime_metrics.regime_confidence)
                
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    quantity=position_size,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=confidence,
                    metadata={'regime': 'sideways', 'bb_position': bb_position, 'rsi': rsi}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in sideways strategy: {e}")
            return None
    
    def _volatile_strategy(self, symbol: str, data: pd.DataFrame, 
                          regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Volatility-based strategy for volatile markets"""
        
        try:
            current_price = data['Close'].iloc[-1]
            
            # ATR for volatility measurement
            atr = self._calculate_atr(data)
            atr_percent = atr / current_price
            
            # Volatility breakout signals
            if atr_percent > 0.03:  # High volatility
                # Look for breakout patterns
                sma_20 = data['Close'].rolling(20).mean().iloc[-1]
                
                if current_price > sma_20 * 1.02:  # 2% breakout above SMA
                    position_size = self._calculate_volatility_position_size(
                        current_price, regime_metrics.volatility
                    )
                    
                    confidence = min(0.6, regime_metrics.regime_confidence)
                    
                    return TradeSignal(
                        symbol=symbol,
                        action='BUY',
                        quantity=position_size,
                        price=current_price,
                        timestamp=datetime.now(),
                        strategy=self.name,
                        confidence=confidence,
                        metadata={'regime': 'volatile', 'atr_percent': atr_percent}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in volatile strategy: {e}")
            return None
    
    def _low_volatility_strategy(self, symbol: str, data: pd.DataFrame, 
                                regime_metrics: RegimeMetrics) -> Optional[TradeSignal]:
        """Breakout strategy for low volatility markets"""
        
        try:
            current_price = data['Close'].iloc[-1]
            
            # Calculate range
            high_20 = data['High'].rolling(20).max().iloc[-1]
            low_20 = data['Low'].rolling(20).min().iloc[-1]
            range_percent = (high_20 - low_20) / low_20
            
            # Breakout signals
            if current_price > high_20 * 1.01:  # 1% breakout above range
                position_size = self._calculate_breakout_position_size(
                    current_price, range_percent
                )
                
                confidence = min(0.7, regime_metrics.regime_confidence)
                
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    quantity=position_size,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=confidence,
                    metadata={'regime': 'low_volatility', 'range_percent': range_percent}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in low volatility strategy: {e}")
            return None
    
    def _calculate_trend_position_size(self, price: float, trend_strength: float) -> float:
        """Calculate position size for trend strategies"""
        base_size = 1000  # Base position value
        trend_multiplier = min(2.0, 1.0 + abs(trend_strength) * 10)
        position_value = base_size * trend_multiplier
        return position_value / price
    
    def _calculate_mean_reversion_position_size(self, price: float, mean_reversion_strength: float) -> float:
        """Calculate position size for mean reversion strategies"""
        base_size = 800  # Smaller base for mean reversion
        reversion_multiplier = 1.0 + mean_reversion_strength
        position_value = base_size * reversion_multiplier
        return position_value / price
    
    def _calculate_volatility_position_size(self, price: float, volatility: float) -> float:
        """Calculate position size for volatility strategies"""
        base_size = 600  # Smaller base for volatile markets
        volatility_multiplier = max(0.5, 1.0 - volatility)
        position_value = base_size * volatility_multiplier
        return position_value / price
    
    def _calculate_breakout_position_size(self, price: float, range_percent: float) -> float:
        """Calculate position size for breakout strategies"""
        base_size = 1200  # Larger base for breakouts
        range_multiplier = 1.0 + range_percent
        position_value = base_size * range_multiplier
        return position_value / price
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            return macd.iloc[-1], signal_line.iloc[-1]
        except:
            return 0.0, 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std_dev = prices.rolling(window=period).std()
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            return upper_band, lower_band
        except:
            return pd.Series([prices.iloc[-1] * 1.1]), pd.Series([prices.iloc[-1] * 0.9])
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()
            return atr.iloc[-1]
        except:
            return data['Close'].iloc[-1] * 0.02  # 2% default 