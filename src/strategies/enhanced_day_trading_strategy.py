"""
Enhanced Day Trading Strategy
Combines multiple technical indicators with advanced risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from .advanced_risk_management import AdvancedRiskManager, RiskParameters
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


class EnhancedDayTradingStrategy(BaseStrategy):
    """
    Enhanced day trading strategy with advanced risk management
    
    Features:
    - Multi-timeframe signal confirmation
    - Volume-weighted indicators
    - ATR-based dynamic stops
    - Kelly Criterion position sizing
    - Portfolio heat management
    - RSI divergence detection
    - MACD histogram analysis
    - Bollinger Band squeeze detection
    """
    
    def __init__(self, 
                 risk_params: Optional[RiskParameters] = None,
                 portfolio_value: float = 100000.0):
        super().__init__(name="EnhancedDayTradingStrategy")
        self.risk_manager = AdvancedRiskManager(risk_params or RiskParameters())
        self.portfolio_value = portfolio_value
        
        # Strategy parameters
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
        self.vwap_period = 20
        self.atr_period = 14
        
        # Signal thresholds
        self.min_volume_ratio = 1.5  # Volume should be 1.5x average
        self.min_price_change = 0.002  # 0.2% minimum price change (more signals)
        self.confidence_threshold = 0.5  # Reduced from 0.6 to generate more signals
        
    def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        vwap = (typical_price * data['Volume']).rolling(window=self.vwap_period).sum() / \
               data['Volume'].rolling(window=self.vwap_period).sum()
        return vwap
    
    def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = data['Volume'].iloc[0]
        
        for i in range(1, len(data)):
            if data['Close'].iloc[i] > data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['Volume'].iloc[i]
            elif data['Close'].iloc[i] < data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['Volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def detect_rsi_divergence(self, data: pd.DataFrame) -> Tuple[bool, bool]:
        """
        Detect RSI divergence (bullish and bearish)
        
        Returns:
            (bullish_divergence, bearish_divergence)
        """
        if len(data) < 20:
            return False, False
        
        # Calculate RSI
        rsi = self._calculate_rsi(data['Close'].astype(float))
        
        # Look for divergence in last 10 periods
        lookback = min(10, len(data) // 2)
        
        # Find recent highs and lows
        price_highs = data['High'].rolling(window=5, center=True).max()
        price_lows = data['Low'].rolling(window=5, center=True).min()
        rsi_highs = rsi.rolling(window=5, center=True).max()
        rsi_lows = rsi.rolling(window=5, center=True).min()
        
        # Bullish divergence: price makes lower low, RSI makes higher low
        recent_price_low = price_lows.iloc[-lookback:].min()
        recent_rsi_low = rsi_lows.iloc[-lookback:].min()
        prev_price_low = price_lows.iloc[-2*lookback:-lookback].min()
        prev_rsi_low = rsi_lows.iloc[-2*lookback:-lookback].min()
        
        bullish_div = (recent_price_low < prev_price_low and 
                      recent_rsi_low > prev_rsi_low and
                      recent_rsi_low < 40)  # RSI should be oversold
        
        # Bearish divergence: price makes higher high, RSI makes lower high
        recent_price_high = price_highs.iloc[-lookback:].max()
        recent_rsi_high = rsi_highs.iloc[-lookback:].max()
        prev_price_high = price_highs.iloc[-2*lookback:-lookback].max()
        prev_rsi_high = rsi_highs.iloc[-2*lookback:-lookback].max()
        
        bearish_div = (recent_price_high > prev_price_high and 
                      recent_rsi_high < prev_rsi_high and
                      recent_rsi_high > 60)  # RSI should be overbought
        
        return bullish_div, bearish_div
    
    def detect_bollinger_squeeze(self, data: pd.DataFrame) -> bool:
        """Detect Bollinger Band squeeze (low volatility)"""
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(data['Close'].astype(float))
        
        # Calculate bandwidth (distance between upper and lower bands)
        bandwidth = (bb_upper - bb_lower) / bb_middle
        
        # Squeeze when bandwidth is low (volatility contraction)
        current_bandwidth = bandwidth.iloc[-1]
        avg_bandwidth = bandwidth.rolling(window=20).mean().iloc[-1]
        
        return current_bandwidth < avg_bandwidth * 0.8
    
    def analyze_macd_histogram(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze MACD histogram for momentum signals"""
        macd, signal, histogram = self._calculate_macd(data['Close'].astype(float))
        
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]
        hist_change = current_hist - prev_hist
        
        # MACD histogram analysis
        analysis = {
            'histogram_rising': hist_change > 0,
            'histogram_above_zero': current_hist > 0,
            'macd_above_signal': macd.iloc[-1] > signal.iloc[-1],
            'momentum_strength': abs(current_hist),
            'histogram_divergence': False
        }
        
        # Check for histogram divergence
        if len(histogram) >= 10:
            recent_high = histogram.iloc[-5:].max()
            prev_high = histogram.iloc[-10:-5].max()
            if recent_high < prev_high and data['Close'].iloc[-1] > data['Close'].iloc[-5:].max():
                analysis['histogram_divergence'] = True
        
        return analysis
    
    def calculate_signal_confidence(self, 
                                  data: pd.DataFrame,
                                  signal_type: str) -> float:
        """Calculate signal confidence based on multiple factors"""
        confidence = 0.3  # Reduced base confidence for stricter filtering
        
        # Volume confirmation (weighted more heavily)
        avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > self.min_volume_ratio:
            confidence += 0.25  # Increased weight for volume
        elif volume_ratio > 1.2:  # Even moderate volume gets some credit
            confidence += 0.15
        
        # Price momentum and trend alignment
        price_change_5 = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
        price_change_10 = (data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10]
        
        # Trend alignment check
        if signal_type == 'BUY':
            if price_change_5 > 0 and price_change_10 > 0:
                confidence += 0.15  # Strong uptrend
            elif price_change_5 > 0:
                confidence += 0.10  # Short-term uptrend
        elif signal_type == 'SELL':
            if price_change_5 < 0 and price_change_10 < 0:
                confidence += 0.15  # Strong downtrend
            elif price_change_5 < 0:
                confidence += 0.10  # Short-term downtrend
        
        # Price action confirmation
        if abs(price_change_5) > self.min_price_change:
            confidence += 0.10
        
        # RSI confirmation with stricter thresholds
        rsi = self._calculate_rsi(data['Close'].astype(float)).iloc[-1]
        if signal_type == 'BUY' and rsi < 60:  # Not overbought
            confidence += 0.10
        elif signal_type == 'SELL' and rsi > 40:  # Not oversold
            confidence += 0.10
        
        # MACD confirmation with trend alignment
        macd_analysis = self.analyze_macd_histogram(data)
        if signal_type == 'BUY' and macd_analysis['histogram_rising'] and macd_analysis['macd_above_signal']:
            confidence += 0.15  # Strong bullish MACD
        elif signal_type == 'SELL' and not macd_analysis['histogram_rising'] and not macd_analysis['macd_above_signal']:
            confidence += 0.15  # Strong bearish MACD
        
        # VWAP confirmation with price action
        vwap = self.calculate_vwap(data).iloc[-1]
        current_price = data['Close'].iloc[-1]
        vwap_distance = abs(current_price - vwap) / vwap
        
        if signal_type == 'BUY' and current_price > vwap and vwap_distance > 0.005:
            confidence += 0.10  # Price above VWAP with some distance
        elif signal_type == 'SELL' and current_price < vwap and vwap_distance > 0.005:
            confidence += 0.10  # Price below VWAP with some distance
        
        # Bollinger Bands confirmation
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(data['Close'].astype(float))
        bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        
        if signal_type == 'BUY' and bb_position < 0.3:  # Near lower band
            confidence += 0.10
        elif signal_type == 'SELL' and bb_position > 0.7:  # Near upper band
            confidence += 0.10
        
        # Volatility check (avoid low volatility periods)
        atr = self.risk_manager.calculate_atr(data, self.atr_period)
        avg_atr = atr.rolling(window=20).mean().iloc[-1]
        current_atr = atr.iloc[-1]
        
        if current_atr > avg_atr * 0.8:  # Sufficient volatility
            confidence += 0.05
        
        # Multiple timeframe confirmation
        if len(data) >= 50:
            # Check if signal aligns with longer-term trend
            long_term_sma = data['Close'].rolling(window=50).mean().iloc[-1]
            if signal_type == 'BUY' and current_price > long_term_sma:
                confidence += 0.05
            elif signal_type == 'SELL' and current_price < long_term_sma:
                confidence += 0.05
        
        return min(1.0, confidence)
    
    def generate_signals(self, data: pd.DataFrame, options_data: Optional[pd.DataFrame] = None) -> List[TradeSignal]:
        """Generate trading signals with advanced risk management"""
        if len(data) < 50:
            return []
        
        signals = []
        current_price = data['Close'].iloc[-1]
        
        # Calculate all indicators
        rsi = self._calculate_rsi(data['Close'].astype(float))
        macd, signal, histogram = self._calculate_macd(data['Close'].astype(float))
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(data['Close'].astype(float))
        vwap = self.calculate_vwap(data)
        obv = self.calculate_obv(data)
        atr = self.risk_manager.calculate_atr(data, self.atr_period)
        
        # Detect divergences
        bullish_div, bearish_div = self.detect_rsi_divergence(data)
        bollinger_squeeze = self.detect_bollinger_squeeze(data)
        macd_analysis = self.analyze_macd_histogram(data)
        
        # Strategy statistics (would come from historical backtesting)
        strategy_stats = {
            'win_rate': 0.55,  # Example values
            'avg_win': 150,
            'avg_loss': 100
        }
        
        # BUY Signals
        buy_signals = []
        
        # 1. RSI oversold with bullish divergence
        if rsi.iloc[-1] < self.rsi_oversold and bullish_div:
            confidence = self.calculate_signal_confidence(data, 'BUY')
            if confidence > self.confidence_threshold:
                buy_signals.append(('RSI_DIVERGENCE', confidence))
        
        # 2. Bollinger Band bounce from lower band
        if (data['Close'].iloc[-1] <= bb_lower.iloc[-1] * 1.01 and 
            data['Close'].iloc[-2] > bb_lower.iloc[-2]):
            confidence = self.calculate_signal_confidence(data, 'BUY')
            if confidence > self.confidence_threshold:
                buy_signals.append(('BB_BOUNCE', confidence))
        
        # 3. MACD histogram turning positive
        if (histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 and 
            macd_analysis['histogram_rising']):
            confidence = self.calculate_signal_confidence(data, 'BUY')
            if confidence > self.confidence_threshold:
                buy_signals.append(('MACD_CROSS', confidence))
        
        # 4. VWAP bounce with volume
        if (data['Close'].iloc[-1] > vwap.iloc[-1] and 
            data['Close'].iloc[-2] <= vwap.iloc[-2] and
            data['Volume'].iloc[-1] > data['Volume'].rolling(window=20).mean().iloc[-1]):
            confidence = self.calculate_signal_confidence(data, 'BUY')
            if confidence > self.confidence_threshold:
                buy_signals.append(('VWAP_BOUNCE', confidence))
        
        # 5. Momentum breakout (price breaks above recent high with volume)
        if len(data) >= 20:
            recent_high = data['High'].iloc[-20:-1].max()
            if (data['Close'].iloc[-1] > recent_high and 
                data['Volume'].iloc[-1] > data['Volume'].rolling(window=20).mean().iloc[-1] * 1.3):
                confidence = self.calculate_signal_confidence(data, 'BUY')
                if confidence > self.confidence_threshold:
                    buy_signals.append(('MOMENTUM_BREAKOUT', confidence))
        
        # 6. Gap up with continuation (opening gap that continues higher)
        if len(data) >= 5:
            gap_up = data['Open'].iloc[-1] > data['Close'].iloc[-2] * 1.01  # 1% gap up
            continuation = data['Close'].iloc[-1] > data['Open'].iloc[-1]  # Continues higher
            if gap_up and continuation:
                confidence = self.calculate_signal_confidence(data, 'BUY')
                if confidence > self.confidence_threshold:
                    buy_signals.append(('GAP_CONTINUATION', confidence))
        
        # 7. RSI oversold bounce (without divergence)
        if rsi.iloc[-1] < self.rsi_oversold and rsi.iloc[-1] > rsi.iloc[-2]:
            confidence = self.calculate_signal_confidence(data, 'BUY')
            if confidence > self.confidence_threshold:
                buy_signals.append(('RSI_BOUNCE', confidence))
        
        # 8. OBV divergence (price down, volume up)
        if len(obv) >= 10:
            price_trend = data['Close'].iloc[-5:].iloc[-1] < data['Close'].iloc[-5:].iloc[0]
            obv_trend = obv.iloc[-5:].iloc[-1] > obv.iloc[-5:].iloc[0]
            if price_trend and obv_trend:
                confidence = self.calculate_signal_confidence(data, 'BUY')
                if confidence > self.confidence_threshold:
                    buy_signals.append(('OBV_DIVERGENCE', confidence))
        
        # SELL Signals
        sell_signals = []
        
        # 1. RSI overbought with bearish divergence
        if rsi.iloc[-1] > self.rsi_overbought and bearish_div:
            confidence = self.calculate_signal_confidence(data, 'SELL')
            if confidence > self.confidence_threshold:
                sell_signals.append(('RSI_DIVERGENCE', confidence))
        
        # 2. Bollinger Band rejection from upper band
        if (data['Close'].iloc[-1] >= bb_upper.iloc[-1] * 0.99 and 
            data['Close'].iloc[-2] < bb_upper.iloc[-2]):
            confidence = self.calculate_signal_confidence(data, 'SELL')
            if confidence > self.confidence_threshold:
                sell_signals.append(('BB_REJECTION', confidence))
        
        # 3. MACD histogram turning negative
        if (histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 and 
            not macd_analysis['histogram_rising']):
            confidence = self.calculate_signal_confidence(data, 'SELL')
            if confidence > self.confidence_threshold:
                sell_signals.append(('MACD_CROSS', confidence))
        
        # 4. VWAP rejection with volume
        if (data['Close'].iloc[-1] < vwap.iloc[-1] and 
            data['Close'].iloc[-2] >= vwap.iloc[-2] and
            data['Volume'].iloc[-1] > data['Volume'].rolling(window=20).mean().iloc[-1]):
            confidence = self.calculate_signal_confidence(data, 'SELL')
            if confidence > self.confidence_threshold:
                sell_signals.append(('VWAP_REJECTION', confidence))
        
        # 5. Momentum breakdown (price breaks below recent low with volume)
        if len(data) >= 20:
            recent_low = data['Low'].iloc[-20:-1].min()
            if (data['Close'].iloc[-1] < recent_low and 
                data['Volume'].iloc[-1] > data['Volume'].rolling(window=20).mean().iloc[-1] * 1.3):
                confidence = self.calculate_signal_confidence(data, 'SELL')
                if confidence > self.confidence_threshold:
                    sell_signals.append(('MOMENTUM_BREAKDOWN', confidence))
        
        # 6. Gap down with continuation (opening gap that continues lower)
        if len(data) >= 5:
            gap_down = data['Open'].iloc[-1] < data['Close'].iloc[-2] * 0.99  # 1% gap down
            continuation = data['Close'].iloc[-1] < data['Open'].iloc[-1]  # Continues lower
            if gap_down and continuation:
                confidence = self.calculate_signal_confidence(data, 'SELL')
                if confidence > self.confidence_threshold:
                    sell_signals.append(('GAP_CONTINUATION_DOWN', confidence))
        
        # 7. RSI overbought rejection (without divergence)
        if rsi.iloc[-1] > self.rsi_overbought and rsi.iloc[-1] < rsi.iloc[-2]:
            confidence = self.calculate_signal_confidence(data, 'SELL')
            if confidence > self.confidence_threshold:
                sell_signals.append(('RSI_REJECTION', confidence))
        
        # 8. OBV divergence (price up, volume down)
        if len(obv) >= 10:
            price_trend = data['Close'].iloc[-5:].iloc[-1] > data['Close'].iloc[-5:].iloc[0]
            obv_trend = obv.iloc[-5:].iloc[-1] < obv.iloc[-5:].iloc[0]
            if price_trend and obv_trend:
                confidence = self.calculate_signal_confidence(data, 'SELL')
                if confidence > self.confidence_threshold:
                    sell_signals.append(('OBV_DIVERGENCE_BEARISH', confidence))
        
        # Generate signals with risk management
        for signal_type, signals_list in [('BUY', buy_signals), ('SELL', sell_signals)]:
            for signal_name, confidence in signals_list:
                # Calculate position size using Kelly Criterion
                volatility = atr.iloc[-1] / current_price if current_price > 0 else 0
                shares = self.risk_manager.calculate_position_size(
                    confidence, volatility, current_price, strategy_stats
                )
                
                if shares > 0:
                    # Check portfolio heat
                    position_value = shares * current_price
                    symbol_for_heat = getattr(data, 'name', 'UNKNOWN')
                    if symbol_for_heat == 'UNKNOWN' and hasattr(self, 'current_symbol'):
                        symbol_for_heat = self.current_symbol
                    allowed, reason = self.risk_manager.check_portfolio_heat(position_value, symbol_for_heat)
                    
                    if allowed:
                        # Calculate dynamic stop loss
                        stop_loss = self.risk_manager.calculate_dynamic_stop_loss(
                            data, current_price, signal_type
                        )
                        
                        # Get symbol from data name or use a default
                        symbol = getattr(data, 'name', 'UNKNOWN')
                        if symbol == 'UNKNOWN' and hasattr(self, 'current_symbol'):
                            symbol = self.current_symbol
                        
                        # --- OPTIONS LOGIC ---
                        trade_type = 'stock'
                        trade_metadata = {
                            'signal_type': signal_name,
                            'stop_loss': stop_loss,
                            'atr': atr.iloc[-1],
                            'rsi': rsi.iloc[-1],
                            'volume_ratio': data['Volume'].iloc[-1] / data['Volume'].rolling(window=20).mean().iloc[-1],
                            'bollinger_squeeze': bollinger_squeeze,
                            'macd_analysis': macd_analysis,
                            'risk_managed': True
                        }
                        if confidence > 0.7 and options_data is not None and hasattr(options_data, 'calls') and len(options_data.calls) > 0:
                            # Pick nearest expiry, closest strike to current price, call for BUY, put for SELL
                            if signal_type == 'BUY' and options_data.calls:
                                # Find closest strike call option
                                calls_df = pd.DataFrame(options_data.calls)
                                if not calls_df.empty:
                                    calls_df['strike_diff'] = abs(calls_df['strike'] - current_price)
                                    closest_call = calls_df.loc[calls_df['strike_diff'].idxmin()]
                                    option = closest_call
                            elif signal_type == 'SELL' and hasattr(options_data, 'puts') and options_data.puts:
                                # Find closest strike put option
                                puts_df = pd.DataFrame(options_data.puts)
                                if not puts_df.empty:
                                    puts_df['strike_diff'] = abs(puts_df['strike'] - current_price)
                                    closest_put = puts_df.loc[puts_df['strike_diff'].idxmin()]
                                    option = closest_put
                            else:
                                option = None
                            
                            if option is not None:
                                trade_type = 'option'
                                trade_metadata.update({
                                    'trade_type': 'option',
                                    'option_type': 'CALL' if signal_type == 'BUY' else 'PUT',
                                    'strike': option['strike_price'],
                                    'expiry': option.get('expiration_date', 'Unknown'),
                                    'option_price': option.get('last_price', option.get('bid', 0)),
                                    'implied_volatility': option.get('implied_volatility', 0),
                                    'delta': option.get('delta', 0),
                                    'gamma': option.get('gamma', 0),
                                    'theta': option.get('theta', 0),
                                    'vega': option.get('vega', 0)
                                })
                                # Use option price for trade
                                current_price = option.get('last_price', option.get('bid', 0))
                        signal = TradeSignal(
                            symbol=symbol,
                            action=signal_type,
                            quantity=shares,
                            price=current_price,
                            timestamp=datetime.now(),
                            strategy=f"EnhancedDayTrading_{signal_name}",
                            confidence=confidence,
                            metadata=trade_metadata
                        )
                        signals.append(signal)
                    else:
                        logger.info(f"Signal rejected due to portfolio heat: {reason}")
        
        return signals
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, options_data: Optional[pd.DataFrame] = None) -> Optional[TradeSignal]:
        """Generate a single trading signal for a symbol"""
        if len(data) < 50:
            return None
        
        # Set the current symbol for the strategy
        self.current_symbol = symbol
        
        signals = self.generate_signals(data, options_data=options_data)
        
        if signals:
            return signals[0]  # Return the first signal
        return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=self.macd_fast).mean()
        ema_slow = prices.ewm(span=self.macd_slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.macd_signal).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()
        upper = middle + (std * self.bb_std)
        lower = middle - (std * self.bb_std)
        return upper, middle, lower 