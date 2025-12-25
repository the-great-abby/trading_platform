#!/usr/bin/env python3
"""
Multi-Indicator Technical Analyzer
Combines multiple technical indicators to complement Elliott Wave analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MultiIndicatorAnalyzer:
    """
    Analyzes market data using multiple technical indicators
    to complement Elliott Wave analysis
    
    Supports dynamic period adjustment based on timeframe:
    - Daily (1d): Standard periods (RSI 14, MA 20/50/200)
    - Hourly (1h): Medium periods (RSI 14, MA 20/50/100)
    - 15-minute (15m): Short periods (RSI 14, MA 10/20/50)
    - 5-minute (5m): Ultra-short periods (RSI 14, MA 5/10/20)
    """
    
    def __init__(self, timeframe: str = "1d"):
        """
        Initialize analyzer with timeframe-specific parameters
        
        Args:
            timeframe: Trading timeframe ('1d', '1h', '15m', '5m')
        """
        self.timeframe = timeframe
        
        # Configurable thresholds (same across timeframes)
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_strong_oversold = 20
        self.rsi_strong_overbought = 80
        
        # Adjust parameters based on timeframe
        if timeframe == "1d":
            # Daily - standard periods
            self.macd_fast = 12
            self.macd_slow = 26
            self.macd_signal = 9
            self.ma_short = 20
            self.ma_medium = 50
            self.ma_long = 200
            self.bb_period = 20
            self.volume_period = 20
            self.min_data_points = 210  # Need 200+ for long MA
        elif timeframe == "1h":
            # Hourly - slightly shorter periods
            self.macd_fast = 12
            self.macd_slow = 26
            self.macd_signal = 9
            self.ma_short = 20
            self.ma_medium = 50
            self.ma_long = 100  # Reduced from 200
            self.bb_period = 20
            self.volume_period = 20
            self.min_data_points = 110  # Need 100+ for long MA
        elif timeframe == "15m":
            # 15-minute - shorter periods for intraday
            self.macd_fast = 8
            self.macd_slow = 17
            self.macd_signal = 9
            self.ma_short = 10
            self.ma_medium = 20
            self.ma_long = 50
            self.bb_period = 14
            self.volume_period = 14
            self.min_data_points = 60  # Need 50+ for long MA
        elif timeframe == "5m":
            # 5-minute - ultra-short periods for scalping
            self.macd_fast = 5
            self.macd_slow = 13
            self.macd_signal = 5
            self.ma_short = 5
            self.ma_medium = 10
            self.ma_long = 20
            self.bb_period = 10
            self.volume_period = 10
            self.min_data_points = 30  # Need 20+ for long MA
        else:
            # Default to daily
            logger.warning(f"Unknown timeframe {timeframe}, using daily defaults")
            self.macd_fast = 12
            self.macd_slow = 26
            self.macd_signal = 9
            self.ma_short = 20
            self.ma_medium = 50
            self.ma_long = 200
            self.bb_period = 20
            self.volume_period = 20
            self.min_data_points = 210
        
        # Bollinger Bands standard deviation (constant)
        self.bb_std = 2
        
        logger.info(f"📊 Initialized MultiIndicatorAnalyzer for {timeframe} timeframe")
        logger.info(f"   MA periods: {self.ma_short}/{self.ma_medium}/{self.ma_long}")
        logger.info(f"   MACD: {self.macd_fast}/{self.macd_slow}/{self.macd_signal}")
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Run full technical analysis on price data
        
        Args:
            data: DataFrame with OHLCV data (columns: High, Low, Close, Volume)
            
        Returns:
            Dict with all indicator signals and composite score
        """
        try:
            if data.empty or len(data) < self.min_data_points:
                return self._empty_analysis(f"Insufficient data for {self.timeframe} analysis (need {self.min_data_points}+ points, got {len(data)})")
            
            # Calculate all indicators
            rsi_analysis = self._calculate_rsi(data)
            macd_analysis = self._calculate_macd(data)
            ma_analysis = self._calculate_moving_averages(data)
            volume_analysis = self._calculate_volume_analysis(data)
            bb_analysis = self._calculate_bollinger_bands(data)
            ichimoku_analysis = self._calculate_ichimoku(data)
            
            # Generate composite signal
            composite = self._generate_composite_signal(
                rsi_analysis, macd_analysis, ma_analysis, 
                volume_analysis, bb_analysis
            )
            
            return {
                'rsi': rsi_analysis,
                'macd': macd_analysis,
                'moving_averages': ma_analysis,
                'volume': volume_analysis,
                'bollinger_bands': bb_analysis,
                'ichimoku': ichimoku_analysis,
                'composite_signal': composite['signal'],
                'composite_confidence': composite['confidence'],
                'composite_score': composite['score'],
                'reasons': composite['reasons'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in multi-indicator analysis: {e}")
            return self._empty_analysis(f"Analysis error: {str(e)}")
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> Dict:
        """Calculate RSI and generate signal"""
        try:
            closes = data['Close'].values
            
            # Calculate price changes
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gain = pd.Series(gains).rolling(window=period).mean()
            avg_loss = pd.Series(losses).rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            
            # Generate signal
            if current_rsi < self.rsi_strong_oversold:
                signal = 'STRONG_BUY'
                confidence = 0.8
            elif current_rsi < self.rsi_oversold:
                signal = 'BUY'
                confidence = 0.6
            elif current_rsi > self.rsi_strong_overbought:
                signal = 'STRONG_SELL'
                confidence = 0.8
            elif current_rsi > self.rsi_overbought:
                signal = 'SELL'
                confidence = 0.6
            else:
                signal = 'NEUTRAL'
                confidence = 0.3
            
            return {
                'value': float(round(current_rsi, 2)),
                'signal': signal,
                'confidence': float(confidence),
                'interpretation': self._interpret_rsi(current_rsi)
            }
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return {'value': 50, 'signal': 'NEUTRAL', 'confidence': 0, 'interpretation': 'Error'}
    
    def _calculate_macd(self, data: pd.DataFrame) -> Dict:
        """Calculate MACD and generate signal"""
        try:
            closes = data['Close']
            
            # Calculate EMAs
            ema_fast = closes.ewm(span=self.macd_fast, adjust=False).mean()
            ema_slow = closes.ewm(span=self.macd_slow, adjust=False).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_hist = float(histogram.iloc[-1])
            prev_hist = float(histogram.iloc[-2])
            
            # Generate signal based on crossovers and histogram
            if current_macd > current_signal and current_hist > 0:
                if prev_hist < 0:  # Just crossed over
                    signal = 'STRONG_BUY'
                    confidence = 0.8
                else:
                    signal = 'BUY'
                    confidence = 0.6
            elif current_macd < current_signal and current_hist < 0:
                if prev_hist > 0:  # Just crossed under
                    signal = 'STRONG_SELL'
                    confidence = 0.8
                else:
                    signal = 'SELL'
                    confidence = 0.6
            else:
                signal = 'NEUTRAL'
                confidence = 0.3
            
            return {
                'macd': float(round(current_macd, 2)),
                'signal_line': float(round(current_signal, 2)),
                'histogram': float(round(current_hist, 2)),
                'signal': signal,
                'confidence': float(confidence),
                'interpretation': 'Bullish' if current_hist > 0 else 'Bearish'
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0, 'signal_line': 0, 'histogram': 0, 'signal': 'NEUTRAL', 'confidence': 0}
    
    def _calculate_moving_averages(self, data: pd.DataFrame) -> Dict:
        """Calculate moving averages and generate trend signal"""
        try:
            closes = data['Close']
            current_price = float(closes.iloc[-1])
            
            # Calculate MAs
            ma_20 = closes.rolling(window=self.ma_short).mean().iloc[-1]
            ma_50 = closes.rolling(window=self.ma_medium).mean().iloc[-1]
            ma_200 = closes.rolling(window=self.ma_long).mean().iloc[-1]
            
            # Trend analysis
            above_20 = current_price > ma_20
            above_50 = current_price > ma_50
            above_200 = current_price > ma_200
            
            # Golden cross / Death cross
            ma_20_above_50 = ma_20 > ma_50
            ma_50_above_200 = ma_50 > ma_200
            
            # Generate signal
            if above_200 and above_50 and above_20 and ma_20_above_50 and ma_50_above_200:
                signal = 'STRONG_BUY'
                confidence = 0.8
                trend = 'Strong Uptrend'
            elif above_200 and above_50:
                signal = 'BUY'
                confidence = 0.6
                trend = 'Uptrend'
            elif not above_200 and not above_50 and not above_20:
                signal = 'STRONG_SELL'
                confidence = 0.8
                trend = 'Strong Downtrend'
            elif not above_200:
                signal = 'SELL'
                confidence = 0.6
                trend = 'Downtrend'
            else:
                signal = 'NEUTRAL'
                confidence = 0.4
                trend = 'Sideways'
            
            return {
                'ma_20': float(round(float(ma_20), 2)),
                'ma_50': float(round(float(ma_50), 2)),
                'ma_200': float(round(float(ma_200), 2)),
                'current_price': float(round(current_price, 2)),
                'signal': signal,
                'confidence': float(confidence),
                'trend': trend,
                'above_200ma': bool(above_200)
            }
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'trend': 'Unknown'}
    
    def _calculate_volume_analysis(self, data: pd.DataFrame) -> Dict:
        """Analyze volume for signal confirmation"""
        try:
            volumes = data['Volume']
            current_volume = float(volumes.iloc[-1])
            avg_volume_20 = float(volumes.rolling(window=self.volume_period).mean().iloc[-1])
            
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
            
            # Volume confirmation
            if volume_ratio > 1.5:
                strength = 'HIGH'
                confidence = 0.7
            elif volume_ratio > 1.2:
                strength = 'ABOVE_AVERAGE'
                confidence = 0.5
            elif volume_ratio < 0.5:
                strength = 'LOW'
                confidence = 0.3
            else:
                strength = 'AVERAGE'
                confidence = 0.4
            
            return {
                'current': int(current_volume),
                'average_20d': int(avg_volume_20),
                'ratio': round(volume_ratio, 2),
                'strength': strength,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume analysis: {e}")
            return {'strength': 'UNKNOWN', 'confidence': 0}
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands and position"""
        try:
            closes = data['Close']
            current_price = float(closes.iloc[-1])
            
            # Calculate middle band (SMA)
            middle_band = closes.rolling(window=self.bb_period).mean()
            
            # Calculate standard deviation
            std = closes.rolling(window=self.bb_period).std()
            
            # Upper and lower bands
            upper_band = middle_band + (std * self.bb_std)
            lower_band = middle_band - (std * self.bb_std)
            
            current_upper = float(upper_band.iloc[-1])
            current_middle = float(middle_band.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            
            # Calculate position within bands
            band_width = current_upper - current_lower
            position = (current_price - current_lower) / band_width if band_width > 0 else 0.5
            
            # Generate signal
            if position < 0.1:  # Near lower band
                signal = 'BUY'
                confidence = 0.7
                interpretation = 'Oversold - near lower band'
            elif position > 0.9:  # Near upper band
                signal = 'SELL'
                confidence = 0.7
                interpretation = 'Overbought - near upper band'
            elif position < 0.3:
                signal = 'WEAK_BUY'
                confidence = 0.5
                interpretation = 'Below middle band'
            elif position > 0.7:
                signal = 'WEAK_SELL'
                confidence = 0.5
                interpretation = 'Above middle band'
            else:
                signal = 'NEUTRAL'
                confidence = 0.3
                interpretation = 'Within normal range'
            
            return {
                'upper': round(current_upper, 2),
                'middle': round(current_middle, 2),
                'lower': round(current_lower, 2),
                'position': round(position, 2),
                'signal': signal,
                'confidence': confidence,
                'interpretation': interpretation
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'signal': 'NEUTRAL', 'confidence': 0}
    
    def _calculate_ichimoku(self, data: pd.DataFrame) -> Dict:
        """Calculate Ichimoku Cloud indicators"""
        try:
            highs = data['High']
            lows = data['Low']
            closes = data['Close']
            current_price = float(closes.iloc[-1])
            
            # Tenkan-sen (Conversion Line): 9-period
            period_9_high = highs.rolling(window=9).max()
            period_9_low = lows.rolling(window=9).min()
            tenkan_sen = (period_9_high + period_9_low) / 2
            
            # Kijun-sen (Base Line): 26-period
            period_26_high = highs.rolling(window=26).max()
            period_26_low = lows.rolling(window=26).min()
            kijun_sen = (period_26_high + period_26_low) / 2
            
            # Senkou Span A (Leading Span A): Average of Tenkan and Kijun, shifted 26 periods
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
            
            # Senkou Span B (Leading Span B): 52-period, shifted 26 periods
            period_52_high = highs.rolling(window=52).max()
            period_52_low = lows.rolling(window=52).min()
            senkou_span_b = ((period_52_high + period_52_low) / 2).shift(26)
            
            # Chikou Span (Lagging Span): Close shifted back 26 periods
            chikou_span = closes.shift(-26)
            
            # Current values
            current_tenkan = float(tenkan_sen.iloc[-1])
            current_kijun = float(kijun_sen.iloc[-1])
            current_senkou_a = float(senkou_span_a.iloc[-1]) if not pd.isna(senkou_span_a.iloc[-1]) else current_price
            current_senkou_b = float(senkou_span_b.iloc[-1]) if not pd.isna(senkou_span_b.iloc[-1]) else current_price
            
            # Cloud analysis
            cloud_top = max(current_senkou_a, current_senkou_b)
            cloud_bottom = min(current_senkou_a, current_senkou_b)
            
            if current_price > cloud_top:
                cloud_position = 'ABOVE'
                signal = 'BUY'
                confidence = 0.6
            elif current_price < cloud_bottom:
                cloud_position = 'BELOW'
                signal = 'SELL'
                confidence = 0.6
            else:
                cloud_position = 'INSIDE'
                signal = 'NEUTRAL'
                confidence = 0.3
            
            # Tenkan/Kijun cross
            if current_tenkan > current_kijun:
                tk_cross = 'BULLISH'
                if signal == 'BUY':
                    confidence = 0.7  # Boost if aligned
            else:
                tk_cross = 'BEARISH'
                if signal == 'SELL':
                    confidence = 0.7
            
            return {
                'tenkan_sen': round(current_tenkan, 2),
                'kijun_sen': round(current_kijun, 2),
                'senkou_span_a': round(current_senkou_a, 2),
                'senkou_span_b': round(current_senkou_b, 2),
                'cloud_top': round(cloud_top, 2),
                'cloud_bottom': round(cloud_bottom, 2),
                'cloud_position': cloud_position,
                'tk_cross': tk_cross,
                'signal': signal,
                'confidence': float(confidence),
                'interpretation': f"Price {cloud_position.lower()} cloud, TK {tk_cross.lower()}"
            }
            
        except Exception as e:
            logger.error(f"Error calculating Ichimoku: {e}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'interpretation': 'Error'}
    
    def _generate_composite_signal(
        self, 
        rsi: Dict, 
        macd: Dict, 
        ma: Dict, 
        volume: Dict, 
        bb: Dict
    ) -> Dict:
        """
        Generate composite signal from all indicators
        
        Uses weighted voting system:
        - Each indicator contributes based on its confidence
        - Signals must align for higher confidence
        """
        signals = []
        weights = []
        reasons = []
        
        # RSI contribution
        if rsi['signal'] != 'NEUTRAL':
            signals.append(self._signal_to_score(rsi['signal']))
            weights.append(rsi['confidence'])
            reasons.append(f"RSI {rsi['value']:.0f} suggests {rsi['signal']}")
        
        # MACD contribution
        if macd['signal'] != 'NEUTRAL':
            signals.append(self._signal_to_score(macd['signal']))
            weights.append(macd['confidence'])
            reasons.append(f"MACD {macd['interpretation']} ({macd['signal']})")
        
        # Moving Average contribution
        if ma['signal'] != 'NEUTRAL':
            signals.append(self._signal_to_score(ma['signal']))
            weights.append(ma['confidence'])
            reasons.append(f"MA Trend: {ma['trend']} ({ma['signal']})")
        
        # Bollinger Bands contribution
        if bb['signal'] != 'NEUTRAL':
            signals.append(self._signal_to_score(bb['signal']))
            weights.append(bb['confidence'] * 0.7)  # Slightly lower weight
            reasons.append(f"Bollinger: {bb['interpretation']}")
        
        # Volume confirmation (boosts confidence if high)
        if volume['strength'] in ['HIGH', 'ABOVE_AVERAGE']:
            reasons.append(f"Volume confirmation: {volume['strength']}")
        
        # Calculate weighted average score
        if signals and weights:
            weighted_score = sum(s * w for s, w in zip(signals, weights)) / sum(weights)
            base_confidence = sum(weights) / len(weights)
            
            # Boost confidence if volume confirms
            if volume['strength'] in ['HIGH', 'ABOVE_AVERAGE']:
                base_confidence *= 1.2
            
            # Cap confidence at 1.0
            final_confidence = min(1.0, base_confidence)
            
            # Determine final signal
            if weighted_score > 60:
                signal = 'STRONG_BUY'
            elif weighted_score > 30:
                signal = 'BUY'
            elif weighted_score > -30:
                signal = 'HOLD'
            elif weighted_score > -60:
                signal = 'SELL'
            else:
                signal = 'STRONG_SELL'
            
            return {
                'signal': signal,
                'confidence': round(final_confidence, 2),
                'score': round(weighted_score, 2),
                'reasons': reasons,
                'indicators_aligned': len(set(np.sign(signals))) == 1  # All pointing same direction
            }
        
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.2,
                'score': 0,
                'reasons': ['No clear signals from indicators'],
                'indicators_aligned': False
            }
    
    def _signal_to_score(self, signal: str) -> float:
        """Convert signal string to numerical score"""
        signal_scores = {
            'STRONG_BUY': 100,
            'BUY': 50,
            'WEAK_BUY': 25,
            'NEUTRAL': 0,
            'HOLD': 0,
            'WEAK_SELL': -25,
            'SELL': -50,
            'STRONG_SELL': -100
        }
        return signal_scores.get(signal, 0)
    
    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if rsi < self.rsi_strong_oversold:
            return 'Extremely Oversold'
        elif rsi < self.rsi_oversold:
            return 'Oversold'
        elif rsi > self.rsi_strong_overbought:
            return 'Extremely Overbought'
        elif rsi > self.rsi_overbought:
            return 'Overbought'
        else:
            return 'Neutral Zone'
    
    def _empty_analysis(self, reason: str) -> Dict:
        """Return empty analysis result"""
        return {
            'rsi': {'value': 50, 'signal': 'NEUTRAL', 'confidence': 0},
            'macd': {'signal': 'NEUTRAL', 'confidence': 0},
            'moving_averages': {'signal': 'NEUTRAL', 'confidence': 0},
            'volume': {'strength': 'UNKNOWN', 'confidence': 0},
            'bollinger_bands': {'signal': 'NEUTRAL', 'confidence': 0},
            'ichimoku': {'signal': 'NEUTRAL', 'confidence': 0, 'interpretation': 'No data'},
            'composite_signal': 'HOLD',
            'composite_confidence': 0,
            'composite_score': 0,
            'reasons': [reason],
            'timestamp': datetime.now().isoformat()
        }


def combine_elliott_wave_and_indicators(
    elliott_wave: Dict,
    technical_indicators: Dict,
    elliott_weight: float = 0.6,
    technical_weight: float = 0.4
) -> Dict:
    """
    Combine Elliott Wave analysis with technical indicators
    
    Args:
        elliott_wave: Elliott Wave analysis result
        technical_indicators: Multi-indicator analysis result
        elliott_weight: Weight for Elliott Wave (default 60%)
        technical_weight: Weight for technical indicators (default 40%)
    
    Returns:
        Combined recommendation with signal and confidence
    """
    # Extract Elliott Wave signal
    ew_signal = elliott_wave.get('signal', 'HOLD')
    ew_confidence = elliott_wave.get('confidence', 0)
    ew_score = _signal_to_numeric(ew_signal) * ew_confidence
    
    # Extract technical indicator signal
    ti_signal = technical_indicators.get('composite_signal', 'HOLD')
    ti_confidence = technical_indicators.get('composite_confidence', 0)
    ti_score = technical_indicators.get('composite_score', 0)
    
    # Weighted combination
    combined_score = (ew_score * elliott_weight) + (ti_score * technical_weight)
    combined_confidence = (ew_confidence * elliott_weight) + (ti_confidence * technical_weight)
    
    # Determine final signal
    if combined_score > 60:
        final_signal = 'STRONG_BUY'
    elif combined_score > 30:
        final_signal = 'BUY'
    elif combined_score > -30:
        final_signal = 'HOLD'
    elif combined_score > -60:
        final_signal = 'SELL'
    else:
        final_signal = 'STRONG_SELL'
    
    # Combine reasons
    reasons = []
    if ew_confidence > 0.3:
        reasons.append(f"Elliott Wave: {ew_signal} ({ew_confidence:.0%} confidence)")
    reasons.extend(technical_indicators.get('reasons', []))
    
    return {
        'signal': final_signal,
        'confidence': round(combined_confidence, 2),
        'score': round(combined_score, 2),
        'elliott_wave_contribution': round(ew_score * elliott_weight, 2),
        'technical_contribution': round(ti_score * technical_weight, 2),
        'reasons': reasons,
        'timestamp': datetime.now().isoformat()
    }


def _signal_to_numeric(signal: str) -> float:
    """Convert signal to numeric value for combination"""
    signal_map = {
        'STRONG_BUY': 100,
        'BUY': 50,
        'WEAK_BUY': 25,
        'HOLD': 0,
        'NEUTRAL': 0,
        'WEAK_SELL': -25,
        'SELL': -50,
        'STRONG_SELL': -100
    }
    return signal_map.get(signal, 0)

