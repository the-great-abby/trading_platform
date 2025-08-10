"""
Multi-Timeframe Strategy - Combines signals from multiple timeframes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


@dataclass
class TimeframeSignal:
    """Signal from a specific timeframe"""
    timeframe: str
    action: str
    confidence: float
    price: float
    indicators: Dict[str, float]


class MultiTimeframeStrategy(BaseStrategy):
    """
    Multi-Timeframe Strategy that combines signals from different timeframes.
    
    Timeframes:
    - Short-term (5-15 days): Quick momentum signals
    - Medium-term (20-50 days): Trend confirmation
    - Long-term (100+ days): Major trend direction
    
    Signal Combination:
    - All timeframes must agree for highest confidence
    - Majority vote for medium confidence
    - Short-term signals for quick entries/exits
    """
    
    def __init__(self, 
                 short_lookback: int = 10,      # 10-day short-term
                 medium_lookback: int = 30,     # 30-day medium-term
                 long_lookback: int = 100,      # 100-day long-term
                 min_agreement: int = 2,        # Minimum 2 timeframes must agree
                 confidence_threshold: float = 0.6,  # 60% confidence threshold
                 **kwargs):
        super().__init__("Multi_Timeframe_Strategy", kwargs)
        
        self.short_lookback = short_lookback
        self.medium_lookback = medium_lookback
        self.long_lookback = long_lookback
        self.min_agreement = min_agreement
        self.confidence_threshold = confidence_threshold
        
        # Timeframe weights
        self.timeframe_weights = {
            'short': 0.3,   # 30% weight for short-term
            'medium': 0.5,  # 50% weight for medium-term
            'long': 0.2     # 20% weight for long-term
        }
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signal using multi-timeframe analysis"""
        try:
            if len(data) < self.long_lookback:
                return None
            
            # Generate signals for each timeframe
            short_signal = self._generate_short_term_signal(data)
            medium_signal = self._generate_medium_term_signal(data)
            long_signal = self._generate_long_term_signal(data)
            
            # Combine signals
            combined_signal = self._combine_timeframe_signals(
                symbol, short_signal, medium_signal, long_signal
            )
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _generate_short_term_signal(self, data: pd.DataFrame) -> Optional[TimeframeSignal]:
        """Generate short-term signal (5-15 days)"""
        try:
            if len(data) < self.short_lookback:
                return None
            
            # Use recent data for short-term analysis
            short_data = data.tail(self.short_lookback)
            
            # Calculate short-term indicators
            rsi = self._calculate_rsi(short_data['Close'])
            macd, signal = self._calculate_macd(short_data['Close'])
            sma_5 = short_data['Close'].rolling(5).mean().iloc[-1]
            sma_10 = short_data['Close'].rolling(10).mean().iloc[-1]
            current_price = short_data['Close'].iloc[-1]
            
            # Short-term momentum signals
            price_above_sma = current_price > sma_5 > sma_10
            macd_positive = macd > signal
            rsi_momentum = 30 < rsi < 70
            
            indicators = {
                'rsi': rsi,
                'macd': macd - signal,
                'sma_trend': (sma_5 - sma_10) / sma_10,
                'price_momentum': (current_price - short_data['Close'].iloc[0]) / short_data['Close'].iloc[0]
            }
            
            # Determine signal
            if price_above_sma and macd_positive and rsi_momentum:
                return TimeframeSignal(
                    timeframe='short',
                    action='BUY',
                    confidence=0.7,
                    price=current_price,
                    indicators=indicators
                )
            elif not price_above_sma and not macd_positive and rsi > 70:
                return TimeframeSignal(
                    timeframe='short',
                    action='SELL',
                    confidence=0.6,
                    price=current_price,
                    indicators=indicators
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating short-term signal: {e}")
            return None
    
    def _generate_medium_term_signal(self, data: pd.DataFrame) -> Optional[TimeframeSignal]:
        """Generate medium-term signal (20-50 days)"""
        try:
            if len(data) < self.medium_lookback:
                return None
            
            # Use medium-term data
            medium_data = data.tail(self.medium_lookback)
            
            # Calculate medium-term indicators
            sma_20 = medium_data['Close'].rolling(20).mean().iloc[-1]
            sma_30 = medium_data['Close'].rolling(30).mean().iloc[-1]
            current_price = medium_data['Close'].iloc[-1]
            
            # Bollinger Bands
            bb_upper, bb_lower = self._calculate_bollinger_bands(medium_data['Close'])
            bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            
            # MACD for trend
            macd, signal = self._calculate_macd(medium_data['Close'])
            
            # Volume analysis
            avg_volume = medium_data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = medium_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            indicators = {
                'sma_trend': (sma_20 - sma_30) / sma_30,
                'bb_position': bb_position,
                'macd': macd - signal,
                'volume_ratio': volume_ratio
            }
            
            # Medium-term trend signals
            price_above_sma = current_price > sma_20 > sma_30
            macd_positive = macd > signal
            volume_support = volume_ratio > 1.2
            
            if price_above_sma and macd_positive and volume_support:
                return TimeframeSignal(
                    timeframe='medium',
                    action='BUY',
                    confidence=0.8,
                    price=current_price,
                    indicators=indicators
                )
            elif not price_above_sma and not macd_positive and bb_position > 0.8:
                return TimeframeSignal(
                    timeframe='medium',
                    action='SELL',
                    confidence=0.7,
                    price=current_price,
                    indicators=indicators
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating medium-term signal: {e}")
            return None
    
    def _generate_long_term_signal(self, data: pd.DataFrame) -> Optional[TimeframeSignal]:
        """Generate long-term signal (100+ days)"""
        try:
            if len(data) < self.long_lookback:
                return None
            
            # Use long-term data
            long_data = data.tail(self.long_lookback)
            
            # Calculate long-term indicators
            sma_50 = long_data['Close'].rolling(50).mean().iloc[-1]
            sma_100 = long_data['Close'].rolling(100).mean().iloc[-1]
            current_price = long_data['Close'].iloc[-1]
            
            # Long-term trend strength
            trend_strength = self._calculate_trend_strength(long_data['Close'])
            
            # Support/resistance levels
            support_level = long_data['Low'].rolling(50).min().iloc[-1]
            resistance_level = long_data['High'].rolling(50).max().iloc[-1]
            
            # Distance from support/resistance
            support_distance = (current_price - support_level) / support_level
            resistance_distance = (resistance_level - current_price) / current_price
            
            indicators = {
                'trend_strength': trend_strength,
                'sma_trend': (sma_50 - sma_100) / sma_100,
                'support_distance': support_distance,
                'resistance_distance': resistance_distance
            }
            
            # Long-term trend signals
            price_above_sma = current_price > sma_50 > sma_100
            strong_trend = abs(trend_strength) > 0.02
            near_support = support_distance < 0.05
            near_resistance = resistance_distance < 0.05
            
            if price_above_sma and strong_trend and not near_resistance:
                return TimeframeSignal(
                    timeframe='long',
                    action='BUY',
                    confidence=0.9,
                    price=current_price,
                    indicators=indicators
                )
            elif not price_above_sma and strong_trend and near_resistance:
                return TimeframeSignal(
                    timeframe='long',
                    action='SELL',
                    confidence=0.8,
                    price=current_price,
                    indicators=indicators
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating long-term signal: {e}")
            return None
    
    def _combine_timeframe_signals(self, symbol: str, short_signal: Optional[TimeframeSignal],
                                 medium_signal: Optional[TimeframeSignal],
                                 long_signal: Optional[TimeframeSignal]) -> Optional[TradeSignal]:
        """Combine signals from different timeframes"""
        
        try:
            # Collect all signals
            signals = []
            if short_signal:
                signals.append(short_signal)
            if medium_signal:
                signals.append(medium_signal)
            if long_signal:
                signals.append(long_signal)
            
            if len(signals) < self.min_agreement:
                return None
            
            # Count buy and sell signals
            buy_signals = [s for s in signals if s.action == 'BUY']
            sell_signals = [s for s in signals if s.action == 'SELL']
            
            # Determine final action
            if len(buy_signals) >= self.min_agreement and len(sell_signals) == 0:
                action = 'BUY'
                relevant_signals = buy_signals
            elif len(sell_signals) >= self.min_agreement and len(buy_signals) == 0:
                action = 'SELL'
                relevant_signals = sell_signals
            else:
                return None  # No clear consensus
            
            # Calculate weighted confidence
            total_confidence = 0.0
            total_weight = 0.0
            current_price = relevant_signals[0].price
            
            for signal in relevant_signals:
                weight = self.timeframe_weights[signal.timeframe]
                total_confidence += signal.confidence * weight
                total_weight += weight
            
            final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
            
            # Check confidence threshold
            if final_confidence < self.confidence_threshold:
                return None
            
            # Calculate position size based on agreement level
            position_size = self._calculate_multi_timeframe_position_size(
                current_price, len(relevant_signals), final_confidence
            )
            
            # Prepare metadata
            metadata = {
                'strategy_name': self.name,
                'timeframe_signals': [
                    {
                        'timeframe': s.timeframe,
                        'action': s.action,
                        'confidence': s.confidence,
                        'indicators': s.indicators
                    }
                    for s in relevant_signals
                ],
                'agreement_level': len(relevant_signals),
                'final_confidence': final_confidence
            }
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=position_size,
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=final_confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error combining timeframe signals: {e}")
            return None
    
    def _calculate_multi_timeframe_position_size(self, price: float, agreement_level: int, confidence: float) -> float:
        """Calculate position size based on timeframe agreement"""
        
        try:
            # Base position size
            base_size = 1000
            
            # Adjust for agreement level (more timeframes = larger position)
            agreement_multiplier = min(2.0, 1.0 + (agreement_level - self.min_agreement) * 0.3)
            
            # Adjust for confidence
            confidence_multiplier = confidence
            
            # Calculate final position size
            position_value = base_size * agreement_multiplier * confidence_multiplier
            shares = position_value / price
            
            return shares
            
        except Exception as e:
            logger.error(f"Error calculating multi-timeframe position size: {e}")
            return 0.0
    
    def _calculate_trend_strength(self, prices: pd.Series) -> float:
        """Calculate trend strength using linear regression"""
        try:
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            trend_strength = slope / prices.iloc[0]  # Normalized slope
            return trend_strength
        except:
            return 0.0
    
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