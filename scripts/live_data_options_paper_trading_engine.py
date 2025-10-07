#!/usr/bin/env python3
"""
Live Data Options Paper Trading Engine
Uses real market data when available, falls back to realistic simulated data
"""

import sys
import os
import asyncio
import aiohttp
import json
import random
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.market_data.unified_options_pricing_service import unified_options_pricing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveDataOptionsPaperTradingEngine:
    """Options paper trading engine with live market data integration and advanced capital allocation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.initial_capital = config.get('initial_capital', 4000.0)
        self.current_capital = self.initial_capital
        self.trades = []
        self.active_positions = []  # Track open positions
        
        # Advanced capital allocation parameters
        self.allocated_capital = 0.0  # Capital tied up in positions
        self.available_capital = self.initial_capital
        self.max_portfolio_utilization = config.get('max_portfolio_utilization', 0.80)  # Use max 80% of portfolio
        self.min_cash_reserve = config.get('min_cash_reserve', 0.20)  # Keep 20% in cash
        self.max_position_size = config.get('max_position_size', 0.15)  # Max 15% per position
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.05)  # Max 5% risk per trade
        
        # Dynamic sizing parameters
        self.capital_efficiency_threshold = config.get('capital_efficiency_threshold', 0.70)  # Increase sizing when utilization > 70%
        self.capital_scarcity_threshold = config.get('capital_scarcity_threshold', 0.30)  # Decrease sizing when utilization < 30%
        
        # Exit strategy configuration
        self.max_holding_days = config.get('max_holding_days', 30)
        self.min_holding_days = config.get('min_holding_days', 1)
        self.profit_target_pct = config.get('profit_target_pct', 0.10)  # 10% profit target
        self.early_profit_target_pct = config.get('early_profit_target_pct', 0.08)  # 8% early profit target for capital optimization
        self.stop_loss_pct = config.get('stop_loss_pct', 0.05)  # 5% stop loss
        
        # Live data configuration
        self.live_data_enabled = config.get('live_data_enabled', True)
        self.market_data_url = config.get('market_data_url', 'http://localhost:11115/api/market-data/current')
        self.fallback_to_simulated = config.get('fallback_to_simulated', True)
        
        # Elliott Wave strategies (primary)
        self.elliott_wave_strategies = [
            'ELLIOTT_WAVE_IMPULSE',
            'ELLIOTT_WAVE_CORRECTIVE'
        ]
        
        # Options strategies (secondary - used by Elliott Wave)
        self.options_strategies = [
            'IRON_CONDOR',
            'BUTTERFLY_SPREAD', 
            'CALENDAR_SPREAD',
            'STRADDLE',
            'STRANGLE'
        ]
        
        # Use Elliott Wave strategies as primary
        self.strategies = self.elliott_wave_strategies
        
        # Elliott Wave configuration
        elliott_wave_config = config.get('elliott_wave', {})
        self.elliott_wave_enabled = elliott_wave_config.get('enabled', True)
        self.elliott_wave_service_url = elliott_wave_config.get('service_url', 'http://elliott-wave-service.trading-system.svc.cluster.local:8000')
        self.min_confidence_threshold = elliott_wave_config.get('min_confidence_threshold', 0.65)
        
        # Historical data for Elliott Wave analysis
        self.price_history = {}  # Store price history for each symbol
        self.elliott_wave_cache = {}  # Cache Elliott Wave analysis results
        
        # Symbols to trade
        self.symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 
            'SPY', 'QQQ', 'AMZN', 'META', 'NFLX'
        ]
        
        # Realistic current prices (updated periodically)
        self.current_prices = {
            'AAPL': 150.0, 'MSFT': 306.0, 'GOOGL': 139.0, 'TSLA': 201.0, 'NVDA': 450.0,
            'SPY': 420.0, 'QQQ': 350.0, 'AMZN': 130.0, 'META': 280.0, 'NFLX': 400.0
        }
        
        logger.info(f"🚀 Live Data Options Paper Trading Engine initialized")
        logger.info(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"📊 Live Data Enabled: {self.live_data_enabled}")
        logger.info(f"🔄 Fallback to Simulated: {self.fallback_to_simulated}")
        logger.info(f"🎯 Advanced Capital Allocation: Enabled")
        logger.info(f"📊 Max Portfolio Utilization: {self.max_portfolio_utilization:.0%}")
        logger.info(f"💰 Min Cash Reserve: {self.min_cash_reserve:.0%}")
        logger.info(f"🎯 Early Profit Target: {self.early_profit_target_pct:.0%}")
        logger.info(f"🌊 Elliott Wave Analysis: {'Enabled' if self.elliott_wave_enabled else 'Disabled'}")

    def update_price_history(self, symbol: str, price: float):
        """Update price history for Elliott Wave analysis"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'timestamp': datetime.now(),
            'price': price
        })
        
        # Keep only last 100 prices for analysis
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]

    async def analyze_elliott_wave_pattern(self, symbol: str) -> Optional[Dict]:
        """Analyze Elliott Wave pattern for a symbol using historical data"""
        
        if not self.elliott_wave_enabled:
            return None
        
        # Check cache first
        cache_key = f"{symbol}_historical"
        if cache_key in self.elliott_wave_cache:
            return self.elliott_wave_cache[cache_key]
        
        try:
            # Get historical data from market data service
            historical_data = await self._get_historical_data(symbol)
            
            if historical_data is None or len(historical_data) < 50:
                logger.warning(f"⚠️ Insufficient historical data for Elliott Wave analysis: {symbol}")
                return None
            
            # Perform Elliott Wave analysis
            analysis = await self._simulate_elliott_wave_analysis(symbol, historical_data)
            
            # Cache the result
            self.elliott_wave_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing Elliott Wave pattern for {symbol}: {e}")
            return None

    async def _get_historical_data(self, symbol: str, days: int = 730) -> Optional[pd.DataFrame]:
        """Get historical data from market data service"""
        
        try:
            # Calculate date range (2 years for options, 5 years for stocks)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Call the market data service
            url = "http://localhost:11084/market-data/historical"
            payload = {
                "symbol": symbol,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "interval": "1d"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('data') and len(data['data']) > 0:
                            # Convert to DataFrame
                            df_data = []
                            for item in data['data']:
                                df_data.append({
                                    'date': item['date'],
                                    'open': item['open'],
                                    'high': item['high'],
                                    'low': item['low'],
                                    'close': item['close'],
                                    'volume': item['volume']
                                })
                            
                            df = pd.DataFrame(df_data)
                            df['date'] = pd.to_datetime(df['date'])
                            df.set_index('date', inplace=True)
                            
                            logger.info(f"✅ Retrieved {len(df)} historical data points for {symbol}")
                            return df
                        else:
                            logger.warning(f"⚠️ No historical data returned for {symbol}")
                            return None
                    else:
                        logger.error(f"❌ Historical data request failed for {symbol}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error fetching historical data for {symbol}: {e}")
            return None

    async     def _simulate_elliott_wave_analysis(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Simulate Elliott Wave analysis using historical data (enhanced with backtest logic)"""
        
        # Use close prices for analysis
        prices = data['close'].values
        current_price = prices[-1]
        
        # Calculate moving averages
        sma_20 = data['close'].rolling(window=min(20, len(prices))).mean().iloc[-1]
        sma_50 = data['close'].rolling(window=min(50, len(prices))).mean().iloc[-1]
        
        # Enhanced wave count analysis (from backtest)
        wave_count = self._simulate_wave_count_enhanced(prices)
        pattern_type = self._determine_pattern_type_enhanced(wave_count, current_price, sma_20, sma_50)
        confidence = self._calculate_confidence_enhanced(wave_count, pattern_type, data)
        
        # Only proceed if confidence meets threshold
        if confidence < self.min_confidence_threshold:
            return None
        
        # Determine trading signal
        signal = self._generate_trading_signal_enhanced(pattern_type, confidence, current_price, sma_20)
        
        # Map to options strategy
        options_strategy = self._map_to_options_strategy(pattern_type, signal)
        
        # Map to Elliott Wave strategy
        elliott_strategy = self._map_to_elliott_strategy(pattern_type)
        
        result = {
            'symbol': symbol,
            'elliott_strategy': elliott_strategy,
            'options_strategy': options_strategy,
            'pattern_type': pattern_type,
            'wave_count': wave_count,
            'confidence': confidence,
            'signal': signal,
            'target_price': self._calculate_target_price(current_price, pattern_type),
            'stop_loss': self._calculate_stop_loss(current_price, pattern_type),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🌊 Elliott Wave analysis for {symbol}: {elliott_strategy} -> {options_strategy} (confidence: {confidence:.2f})")
        return result

    def _simulate_wave_count(self, prices: np.ndarray) -> Dict:
        """Simulate Elliott Wave count analysis using historical data"""
        
        # Find significant peaks and troughs with better detection
        peaks, troughs = self._find_peaks_and_troughs_advanced(prices)
        
        # Analyze price trends for wave classification
        price_trend = self._analyze_price_trend(prices)
        
        # Simulate wave counting based on historical patterns
        impulse_waves = self._count_impulse_waves(prices, peaks, troughs)
        corrective_waves = self._count_corrective_waves(prices, peaks, troughs)
        
        # Determine current wave position
        current_wave = self._determine_current_wave(impulse_waves, corrective_waves, price_trend)
        
        # Calculate completion percentage
        total_waves = impulse_waves + corrective_waves
        completion_percentage = min(100, (total_waves / 8) * 100)  # Assume 8-wave cycle
        
        wave_count = {
            'impulse_waves': impulse_waves,
            'corrective_waves': corrective_waves,
            'current_wave': current_wave,
            'completion_percentage': completion_percentage,
            'trend_direction': price_trend,
            'total_peaks': len(peaks),
            'total_troughs': len(troughs)
        }
        
        return wave_count

    def _simulate_wave_count_enhanced(self, prices: np.ndarray) -> Dict:
        """Enhanced Elliott Wave count analysis (from backtest)"""
        
        # Find significant peaks and troughs with better detection
        peaks, troughs = self._find_peaks_and_troughs_advanced(prices)
        
        # Analyze price trends for wave classification
        price_trend = self._analyze_price_trend(prices)
        
        # Enhanced wave counting based on backtest logic
        impulse_waves = self._count_impulse_waves_enhanced(prices, peaks, troughs)
        corrective_waves = self._count_corrective_waves_enhanced(prices, peaks, troughs)
        
        # Determine current wave position
        current_wave = self._determine_current_wave_enhanced(impulse_waves, corrective_waves, price_trend)
        
        # Calculate completion percentage with enhanced logic
        total_waves = impulse_waves + corrective_waves
        completion_percentage = min(100, (total_waves / 8) * 100)
        
        # Add enhanced metrics
        wave_strength = self._calculate_wave_strength(prices, peaks, troughs)
        pattern_clarity = self._calculate_pattern_clarity(prices, peaks, troughs)
        
        wave_count = {
            'impulse_waves': impulse_waves,
            'corrective_waves': corrective_waves,
            'current_wave': current_wave,
            'completion_percentage': completion_percentage,
            'trend_direction': price_trend,
            'total_peaks': len(peaks),
            'total_troughs': len(troughs),
            'wave_strength': wave_strength,
            'pattern_clarity': pattern_clarity
        }
        
        return wave_count

    def _find_peaks_and_troughs_advanced(self, prices: np.ndarray) -> Tuple[List, List]:
        """Advanced peak and trough detection for Elliott Wave analysis"""
        peaks = []
        troughs = []
        
        # Use a larger window for more significant peaks/troughs
        window = max(5, len(prices) // 20)  # Adaptive window size
        
        for i in range(window, len(prices) - window):
            # Check for peak
            is_peak = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] >= prices[i]:
                    is_peak = False
                    break
            
            if is_peak:
                peaks.append(i)
            
            # Check for trough
            is_trough = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] <= prices[i]:
                    is_trough = False
                    break
            
            if is_trough:
                troughs.append(i)
        
        return peaks, troughs

    def _analyze_price_trend(self, prices: np.ndarray) -> str:
        """Analyze overall price trend"""
        if len(prices) < 20:
            return 'neutral'
        
        # Calculate trend using linear regression
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        # Normalize slope by price level
        normalized_slope = slope / prices[-1]
        
        if normalized_slope > 0.001:  # 0.1% per day
            return 'bullish'
        elif normalized_slope < -0.001:
            return 'bearish'
        else:
            return 'neutral'

    def _count_impulse_waves(self, prices: np.ndarray, peaks: List, troughs: List) -> int:
        """Count impulse waves based on price action"""
        # Simplified impulse wave counting
        # In reality, this would be much more complex
        return min(len(peaks), 5)  # Max 5 impulse waves

    def _count_corrective_waves(self, prices: np.ndarray, peaks: List, troughs: List) -> int:
        """Count corrective waves based on price action"""
        # Simplified corrective wave counting
        return min(len(troughs), 3)  # Max 3 corrective waves

    def _determine_current_wave(self, impulse_waves: int, corrective_waves: int, trend: str) -> str:
        """Determine current wave position"""
        total_waves = impulse_waves + corrective_waves
        
        if total_waves <= 2:
            return 'wave_1'
        elif total_waves <= 4:
            return 'wave_2'
        elif total_waves <= 6:
            return 'wave_3'
        elif total_waves <= 8:
            return 'wave_4'
        else:
            return 'wave_5'

    def _find_peaks_and_troughs(self, prices: np.ndarray) -> Tuple[List, List]:
        """Find peaks and troughs in price data"""
        peaks = []
        troughs = []
        
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                peaks.append(i)
            elif prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                troughs.append(i)
        
        return peaks, troughs

    def _determine_pattern_type(self, wave_count: Dict, current_price: float, sma_20: float, sma_50: float) -> str:
        """Determine Elliott Wave pattern type"""
        
        if current_price > sma_20 > sma_50:
            if wave_count['impulse_waves'] >= 3:
                return 'impulse_completion'
            else:
                return 'impulse'
        elif current_price < sma_20 < sma_50:
            if wave_count['corrective_waves'] >= 2:
                return 'corrective_completion'
            else:
                return 'corrective'
        elif abs(current_price - sma_20) / sma_20 < 0.02:
            return 'fibonacci_retracement'
        else:
            return 'wave_extension'

    def _calculate_confidence(self, wave_count: Dict, pattern_type: str, data: pd.DataFrame) -> float:
        """Calculate confidence score for the pattern"""
        
        base_confidence = 0.5
        
        # Adjust based on pattern clarity
        if pattern_type in ['impulse_completion', 'corrective_completion']:
            base_confidence += 0.2
        
        # Adjust based on wave count completeness
        completion_pct = wave_count['completion_percentage']
        if completion_pct > 80:
            base_confidence += 0.2
        elif completion_pct > 60:
            base_confidence += 0.1
        
        # Adjust based on price momentum
        if len(data) >= 20:
            momentum = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            if abs(momentum) > 0.05:
                base_confidence += 0.1
        
        return min(0.95, max(0.3, base_confidence))

    def _generate_trading_signal(self, pattern_type: str, confidence: float, current_price: float, sma_20: float) -> str:
        """Generate trading signal based on Elliott Wave analysis"""
        
        if confidence < self.min_confidence_threshold:
            return 'HOLD'
        
        if pattern_type in ['impulse_completion', 'wave_extension']:
            if current_price > sma_20:
                return 'BULLISH'
            else:
                return 'BEARISH'
        elif pattern_type in ['corrective_completion', 'fibonacci_retracement']:
            return 'NEUTRAL'
        else:
            return 'HOLD'

    def _map_to_options_strategy(self, pattern_type: str, signal: str) -> str:
        """Map Elliott Wave pattern to options strategy"""
        
        if pattern_type == 'impulse_completion':
            return 'STRADDLE' if signal in ['BULLISH', 'BEARISH'] else 'STRANGLE'
        elif pattern_type == 'corrective_completion':
            return 'IRON_CONDOR'
        elif pattern_type == 'fibonacci_retracement':
            return 'CALENDAR_SPREAD'
        elif pattern_type == 'wave_extension':
            return 'STRADDLE' if signal in ['BULLISH', 'BEARISH'] else 'STRANGLE'
        else:
            return 'BUTTERFLY_SPREAD'

    def _map_to_elliott_strategy(self, pattern_type: str) -> str:
        """Map pattern type to Elliott Wave strategy"""
        
        if pattern_type in ['impulse', 'impulse_completion', 'wave_extension']:
            return 'ELLIOTT_WAVE_IMPULSE'
        else:
            return 'ELLIOTT_WAVE_CORRECTIVE'

    def _calculate_target_price(self, current_price: float, pattern_type: str) -> float:
        """Calculate target price based on Elliott Wave analysis"""
        
        if pattern_type in ['impulse_completion', 'wave_extension']:
            move_pct = 0.10  # 10% target
            return current_price * (1 + move_pct)
        elif pattern_type == 'corrective_completion':
            move_pct = 0.05  # 5% target
            return current_price * (1 + move_pct)
        else:
            return current_price * 1.03  # 3% default

    def _calculate_stop_loss(self, current_price: float, pattern_type: str) -> float:
        """Calculate stop loss based on Elliott Wave analysis"""
        
        if pattern_type in ['impulse_completion', 'wave_extension']:
            return current_price * 0.95  # 5% stop loss
        else:
            return current_price * 0.92  # 8% stop loss

    # Enhanced methods from backtest
    def _count_impulse_waves_enhanced(self, prices: np.ndarray, peaks: List, troughs: List) -> int:
        """Enhanced impulse wave counting (from backtest)"""
        if len(peaks) < 2:
            return 0
        
        impulse_count = 0
        for i in range(1, len(peaks)):
            if peaks[i] > peaks[i-1] and prices[peaks[i]] > prices[peaks[i-1]]:
                impulse_count += 1
        
        return min(impulse_count, 5)

    def _count_corrective_waves_enhanced(self, prices: np.ndarray, peaks: List, troughs: List) -> int:
        """Enhanced corrective wave counting (from backtest)"""
        if len(troughs) < 2:
            return 0
        
        corrective_count = 0
        for i in range(1, len(troughs)):
            if troughs[i] > troughs[i-1] and prices[troughs[i]] < prices[troughs[i-1]]:
                corrective_count += 1
        
        return min(corrective_count, 3)

    def _determine_current_wave_enhanced(self, impulse_waves: int, corrective_waves: int, trend: str) -> str:
        """Enhanced current wave determination (from backtest)"""
        total_waves = impulse_waves + corrective_waves
        
        if total_waves <= 2:
            return 'wave_1'
        elif total_waves <= 4:
            return 'wave_2'
        elif total_waves <= 6:
            return 'wave_3'
        elif total_waves <= 8:
            return 'wave_4'
        else:
            return 'wave_5'

    def _calculate_wave_strength(self, prices: np.ndarray, peaks: List, troughs: List) -> float:
        """Calculate wave strength (from backtest)"""
        if len(prices) < 10:
            return 0.5
        
        recent_prices = prices[-10:]
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        volatility = np.std(recent_prices) / np.mean(recent_prices)
        strength = abs(momentum) * (1 + volatility)
        return min(1.0, max(0.0, strength))

    def _calculate_pattern_clarity(self, prices: np.ndarray, peaks: List, troughs: List) -> float:
        """Calculate pattern clarity (from backtest)"""
        if len(peaks) < 2 or len(troughs) < 2:
            return 0.3
        
        peak_ratios = []
        for i in range(1, len(peaks)):
            if peaks[i] > peaks[i-1]:
                ratio = prices[peaks[i]] / prices[peaks[i-1]]
                peak_ratios.append(ratio)
        
        trough_ratios = []
        for i in range(1, len(troughs)):
            if troughs[i] > troughs[i-1]:
                ratio = prices[troughs[i]] / prices[troughs[i-1]]
                trough_ratios.append(ratio)
        
        all_ratios = peak_ratios + trough_ratios
        if not all_ratios:
            return 0.3
        
        consistency = 1.0 - np.std(all_ratios) / np.mean(all_ratios)
        return min(1.0, max(0.0, consistency))

    def _determine_pattern_type_enhanced(self, wave_count: Dict, current_price: float, sma_20: float, sma_50: float) -> str:
        """Enhanced pattern type determination (from backtest)"""
        wave_strength = wave_count.get('wave_strength', 0.5)
        pattern_clarity = wave_count.get('pattern_clarity', 0.5)
        
        if current_price > sma_20 > sma_50:
            if wave_count['impulse_waves'] >= 3 and wave_strength > 0.6:
                return 'impulse_completion'
            elif pattern_clarity > 0.7:
                return 'impulse'
            else:
                return 'wave_extension'
        elif current_price < sma_20 < sma_50:
            if wave_count['corrective_waves'] >= 2 and wave_strength > 0.6:
                return 'corrective_completion'
            elif pattern_clarity > 0.7:
                return 'corrective'
            else:
                return 'fibonacci_retracement'
        elif abs(current_price - sma_20) / sma_20 < 0.02:
            return 'fibonacci_retracement'
        else:
            if wave_strength > 0.8:
                return 'wave_extension'
            else:
                return 'fibonacci_retracement'

    def _calculate_confidence_enhanced(self, wave_count: Dict, pattern_type: str, data: pd.DataFrame) -> float:
        """Enhanced confidence calculation (from backtest)"""
        base_confidence = 0.5
        
        if pattern_type in ['impulse_completion', 'corrective_completion']:
            base_confidence += 0.2
        elif pattern_type in ['impulse', 'corrective']:
            base_confidence += 0.1
        
        completion_pct = wave_count['completion_percentage']
        if completion_pct > 80:
            base_confidence += 0.2
        elif completion_pct > 60:
            base_confidence += 0.1
        
        wave_strength = wave_count.get('wave_strength', 0.5)
        pattern_clarity = wave_count.get('pattern_clarity', 0.5)
        
        if wave_strength > 0.8:
            base_confidence += 0.15
        elif wave_strength > 0.6:
            base_confidence += 0.1
        
        if pattern_clarity > 0.8:
            base_confidence += 0.15
        elif pattern_clarity > 0.6:
            base_confidence += 0.1
        
        if len(data) >= 20:
            momentum = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            if abs(momentum) > 0.05:
                base_confidence += 0.1
            elif abs(momentum) > 0.03:
                base_confidence += 0.05
        
        return min(0.95, max(0.3, base_confidence))

    def _generate_trading_signal_enhanced(self, pattern_type: str, confidence: float, current_price: float, sma_20: float) -> str:
        """Enhanced trading signal generation (from backtest)"""
        if confidence < self.min_confidence_threshold:
            return 'HOLD'
        
        if pattern_type in ['impulse_completion', 'wave_extension']:
            if current_price > sma_20:
                return 'BULLISH'
            else:
                return 'BEARISH'
        elif pattern_type in ['corrective_completion', 'fibonacci_retracement']:
            if confidence > 0.8:
                return 'NEUTRAL'
            else:
                return 'HOLD'
        else:
            return 'HOLD'

    def calculate_available_capital(self) -> float:
        """Calculate available capital for new trades"""
        self.allocated_capital = sum(pos['trade_value'] for pos in self.active_positions)
        self.available_capital = self.current_capital - self.allocated_capital
        
        # Ensure minimum cash reserve
        min_cash = self.current_capital * self.min_cash_reserve
        self.available_capital = max(0, self.available_capital - min_cash)
        
        return self.available_capital

    def can_open_new_position(self) -> bool:
        """Check if we can open a new position"""
        available_capital = self.calculate_available_capital()
        
        # Need minimum capital for a meaningful trade
        min_trade_capital = self.current_capital * 0.05  # 5% minimum
        
        return (
            available_capital >= min_trade_capital and
            len(self.active_positions) < 5  # Max 5 positions
        )

    def optimize_capital_allocation(self):
        """Optimize capital allocation by closing low-performing positions early"""
        
        if len(self.active_positions) < 3:
            return  # Don't optimize with few positions
        
        # Find positions that are close to profit targets
        positions_to_close = []
        
        for position in self.active_positions:
            # Calculate current P&L percentage
            current_pnl_pct = (position['pnl'] / (position['trade_value'] * 0.1))
            
            # Close positions that are close to profit target (8% instead of 10%)
            if current_pnl_pct >= self.early_profit_target_pct:
                positions_to_close.append(position)
                logger.info(f"🎯 Early exit for capital optimization: {position['symbol']} {position['strategy']} - {current_pnl_pct:.1%} profit")
        
        # Close positions to free up capital
        for position in positions_to_close:
            self.close_position(position, "capital_optimization")

    def close_position(self, position: Dict, reason: str):
        """Close a position and free up capital"""
        position['status'] = 'closed'
        position['exit_reason'] = reason
        position['exit_timestamp'] = datetime.now().isoformat()
        
        # Update capital
        self.current_capital += position['pnl']
        
        # Remove from active positions
        self.active_positions.remove(position)
        
        logger.info(f"📤 Position closed ({reason}): {position['strategy']} {position['contracts']} contracts {position['symbol']} | P&L: ${position['pnl']:+.2f}")

    async def get_live_price(self, symbol: str) -> Optional[float]:
        """Get live price directly from Polygon API (bypassing stale market data service)"""
        if not self.live_data_enabled:
            return None
            
        try:
            api_key = 'PwSQb2yBh2aYqEs0lZIqnTX_nT2b7CHr'
            url = f'https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}'
            params = {'apiKey': api_key}
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"🔍 Fetching live price for {symbol} directly from Polygon API")
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if 'ticker' in data and data['ticker']:
                        ticker = data['ticker']
                        # Try to get current price from day or min data
                        if 'day' in ticker and 'c' in ticker['day']:
                            price = float(ticker['day']['c'])
                            logger.info(f"✅ Got live price for {symbol}: ${price:.2f}")
                            # Update our current prices cache
                            self.current_prices[symbol] = price
                            return price
                        elif 'min' in ticker and 'c' in ticker['min']:
                            price = float(ticker['min']['c'])
                            logger.info(f"✅ Got live price for {symbol}: ${price:.2f}")
                            # Update our current prices cache
                            self.current_prices[symbol] = price
                            return price
                    
                    logger.warning(f"⚠️ No price data found in Polygon response for {symbol}")
                        
        except Exception as e:
            logger.error(f"❌ Error fetching live price for {symbol}: {e}")
        
        return None

    async def get_realistic_price(self, symbol: str) -> float:
        """Get realistic price (live data or simulated)"""
        # Try live data first
        if self.live_data_enabled:
            live_price = await self.get_live_price(symbol)
            if live_price:
                # Update price history for Elliott Wave analysis
                self.update_price_history(symbol, live_price)
                return live_price
        
        # Fallback to realistic simulated price
        base_price = self.current_prices.get(symbol, 100.0)
        
        # Add realistic market movement (-2% to +2%)
        movement = random.uniform(-0.02, 0.02)
        new_price = base_price * (1 + movement)
        
        # Update cache
        self.current_prices[symbol] = new_price
        
        # Update price history for Elliott Wave analysis
        self.update_price_history(symbol, new_price)
        
        logger.info(f"📊 Using simulated price for {symbol}: ${new_price:.2f}")
        return new_price

    async def calculate_options_position_size(self, symbol: str, strategy: str, premium: float) -> int:
        """Calculate position size using advanced capital allocation"""
        if premium <= 0:
            return 0

        available_capital = self.calculate_available_capital()
        
        if available_capital <= 0:
            logger.warning(f"⚠️ No available capital for {symbol} {strategy}")
            return 0
        
        # Base position sizing
        max_position_value = min(
            self.current_capital * self.max_position_size,
            available_capital * 0.5  # Use max 50% of available capital
        )
        
        max_risk_value = self.current_capital * self.max_risk_per_trade
        
        # Calculate max contracts
        premium_per_contract = premium * 100
        max_contracts_position = int(max_position_value / premium_per_contract)
        max_contracts_risk = int(max_risk_value / premium_per_contract)
        
        max_contracts = min(max_contracts_position, max_contracts_risk)
        
        # More aggressive minimum - allow smaller positions
        if max_contracts < 1 and premium_per_contract < available_capital * 0.1:
            max_contracts = 1
        
        if max_contracts < 1:
            logger.warning(f"⚠️ Position too small for {symbol} {strategy}")
            logger.warning(f"   Max contracts: {max_contracts}")
            logger.warning(f"   Premium per contract: ${premium_per_contract:.2f}")
            logger.warning(f"   Available capital: ${available_capital:.2f}")
            return 0
        
        # Dynamic sizing based on capital utilization
        utilization = self.allocated_capital / self.current_capital
        
        if utilization > self.capital_efficiency_threshold:
            # High utilization - be more conservative
            contracts = random.randint(1, min(max_contracts, 3))  # Increased from 2
        elif utilization < self.capital_scarcity_threshold:
            # Low utilization - can be more aggressive
            contracts = random.randint(1, min(max_contracts, 5))  # Increased from 4
        else:
            # Normal utilization
            contracts = random.randint(1, min(max_contracts, 4))  # Increased from 3
        
        logger.info(f"📊 Advanced position sizing for {symbol} {strategy}:")
        logger.info(f"   Available capital: ${available_capital:.2f}")
        logger.info(f"   Capital utilization: {utilization:.1%}")
        logger.info(f"   Max contracts: {max_contracts}")
        logger.info(f"   Selected contracts: {contracts}")
        logger.info(f"   Premium per contract: ${premium_per_contract:.2f}")
        
        return contracts

    def get_realistic_options_price(self, symbol: str, strategy: str, current_price: float) -> Tuple[float, Dict]:
        """Generate realistic options pricing based on live underlying price"""
        
        # Days to expiration (30-60 days for most strategies)
        dte = random.randint(30, 60)
        
        # Volatility (20-40% for most stocks)
        volatility = random.uniform(0.20, 0.40)
        
        # Risk-free rate (current ~5%)
        risk_free_rate = 0.05
        
        if strategy == 'IRON_CONDOR':
            # Iron Condor: Sell call spread + put spread
            # Premium: $0.50 - $2.00 per contract
            premium = random.uniform(0.50, 2.00)
            
            # Greeks calculation
            delta = random.uniform(-0.15, 0.15)  # Near delta-neutral
            gamma = random.uniform(0.01, 0.05)
            theta = random.uniform(-0.05, -0.15)  # Time decay
            vega = random.uniform(0.10, 0.30)
            
        elif strategy == 'BUTTERFLY_SPREAD':
            # Butterfly: Buy outer strikes, sell middle
            # Premium: $0.20 - $1.50 per contract
            premium = random.uniform(0.20, 1.50)
            
            delta = random.uniform(-0.10, 0.10)
            gamma = random.uniform(0.02, 0.08)
            theta = random.uniform(-0.10, -0.25)
            vega = random.uniform(0.05, 0.20)
            
        elif strategy == 'CALENDAR_SPREAD':
            # Calendar: Sell near-term, buy far-term
            # Premium: $0.30 - $2.50 per contract
            premium = random.uniform(0.30, 2.50)
            
            delta = random.uniform(-0.20, 0.20)
            gamma = random.uniform(0.01, 0.06)
            theta = random.uniform(0.05, 0.20)  # Positive theta
            vega = random.uniform(0.15, 0.40)
            
        elif strategy == 'STRADDLE':
            # Straddle: Buy call + put at same strike
            # Premium: $1.00 - $4.00 per contract (adjusted for small portfolio)
            premium = random.uniform(1.00, 4.00)
            
            delta = random.uniform(-0.05, 0.05)  # Delta-neutral
            gamma = random.uniform(0.05, 0.15)
            theta = random.uniform(-0.20, -0.50)
            vega = random.uniform(0.30, 0.80)
            
        elif strategy == 'STRANGLE':
            # Strangle: Buy OTM call + put
            # Premium: $0.50 - $2.50 per contract (adjusted for small portfolio)
            premium = random.uniform(0.50, 2.50)
            
            delta = random.uniform(-0.10, 0.10)
            gamma = random.uniform(0.03, 0.10)
            theta = random.uniform(-0.15, -0.40)
            vega = random.uniform(0.20, 0.60)
            
        else:
            # Default pricing
            premium = random.uniform(0.50, 3.00)
            delta = random.uniform(-0.20, 0.20)
            gamma = random.uniform(0.01, 0.05)
            theta = random.uniform(-0.10, -0.30)
            vega = random.uniform(0.10, 0.40)
        
        greeks = {
            'delta': round(delta, 3),
            'gamma': round(gamma, 3),
            'theta': round(theta, 3),
            'vega': round(vega, 3),
            'dte': dte,
            'volatility': round(volatility, 3)
        }
        
        return round(premium, 2), greeks

    def simulate_pnl(self, strategy: str, contracts: int, premium: float, greeks: Dict) -> float:
        """Simulate realistic P&L for options trade"""
        
        # Base P&L from premium
        base_pnl = contracts * premium * 100
        
        # Add some realistic market movement impact
        # This is simplified - real options P&L is much more complex
        
        # Random market movement (-1% to +1%)
        market_movement = random.uniform(-0.01, 0.01)
        
        # Delta impact
        delta_pnl = base_pnl * greeks['delta'] * market_movement
        
        # Theta decay (time decay)
        theta_decay = greeks['theta'] * contracts * 100 * 0.1  # Daily decay
        
        # Random volatility impact
        vol_impact = random.uniform(-0.5, 0.5) * greeks['vega'] * contracts * 100
        
        # Total P&L
        total_pnl = base_pnl + delta_pnl + theta_decay + vol_impact
        
        # Add some randomness for realism
        random_factor = random.uniform(0.8, 1.2)
        total_pnl *= random_factor
        
        return round(total_pnl, 2)

    async def generate_options_trade(self) -> Dict:
        """Generate a realistic options trade using Elliott Wave analysis with advanced capital allocation"""
        
        # Check if we can open a new position
        if not self.can_open_new_position():
            logger.info(f"📊 Cannot open new position - Active: {len(self.active_positions)}, Available capital: ${self.calculate_available_capital():.2f}")
            return None
        
        # Try Elliott Wave analysis first
        elliott_analysis = None
        symbol = None
        strategy = None
        
        if self.elliott_wave_enabled:
            # Analyze all symbols for Elliott Wave patterns
            for test_symbol in self.symbols:
                analysis = await self.analyze_elliott_wave_pattern(test_symbol)
                if analysis and analysis.get('confidence', 0) >= self.min_confidence_threshold:
                    elliott_analysis = analysis
                    symbol = test_symbol
                    strategy = analysis['elliott_strategy']
                    logger.info(f"🌊 Elliott Wave signal found for {symbol}: {strategy} (confidence: {analysis['confidence']:.2f})")
                    break
        
        # Fallback to random selection if no Elliott Wave signal
        if not elliott_analysis:
            strategy = random.choice(self.strategies)
            symbol = random.choice(self.symbols)
            logger.info(f"🎲 Using random strategy: {strategy} for {symbol}")
        
        # Get realistic current price (live data preferred)
        current_price = await self.get_realistic_price(symbol)
        
        # Generate realistic options pricing based on Elliott Wave analysis
        if elliott_analysis:
            # Use Elliott Wave analysis to determine options strategy
            options_strategy = elliott_analysis['options_strategy']
            premium, greeks = self.get_realistic_options_price(symbol, options_strategy, current_price)
            logger.info(f"🌊 Using Elliott Wave options strategy: {options_strategy}")
        else:
            # Use the selected strategy directly
            premium, greeks = self.get_realistic_options_price(symbol, strategy, current_price)
        
        # Calculate position size using advanced capital allocation
        contracts = await self.calculate_options_position_size(symbol, strategy, premium)
        
        if contracts == 0:
            logger.warning(f"⚠️ Position too small for {symbol} {strategy}")
            return None
        
        # Simulate P&L
        pnl = self.simulate_pnl(strategy, contracts, premium, greeks)
        
        # Calculate trade value
        trade_value = contracts * premium * 100
        position_pct = (trade_value / self.current_capital) * 100
        
        # Update portfolio (subtract trade value first, then add P&L)
        self.current_capital -= trade_value  # Reserve capital for the trade
        self.current_capital += pnl  # Add P&L
        
        # Create trade record
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': strategy,
            'contracts': contracts,
            'premium': premium,
            'current_price': current_price,
            'trade_value': trade_value,
            'pnl': pnl,
            'position_pct': position_pct,
            'greeks': greeks,
            'data_source': 'live' if self.live_data_enabled else 'simulated',
            'status': 'open',  # Track position status
            'elliott_wave_analysis': elliott_analysis,  # Include Elliott Wave analysis
            'options_strategy': elliott_analysis['options_strategy'] if elliott_analysis else strategy,
            'exit_strategy': {
                'max_holding_days': self.max_holding_days,
                'min_holding_days': self.min_holding_days,
                'profit_target_pct': self.profit_target_pct,
                'stop_loss_pct': self.stop_loss_pct,
                'early_profit_target_pct': self.early_profit_target_pct
            }
        }
        
        # Add to active positions for exit tracking
        self.active_positions.append(trade.copy())
        
        # Send trade to paper trading service
        await self.send_trade_to_paper_service(trade)
        
        # Log trade
        if elliott_analysis:
            logger.info(f"🌊 Elliott Wave Trade: {strategy} -> {trade['options_strategy']} {contracts} contracts {symbol} @ ${current_price:.2f}")
            logger.info(f"   Pattern: {elliott_analysis['pattern_type']} | Confidence: {elliott_analysis['confidence']:.2f}")
            logger.info(f"   Signal: {elliott_analysis['signal']} | Target: ${elliott_analysis['target_price']:.2f}")
        else:
            logger.info(f"📈 Options Trade: {strategy} {contracts} contracts {symbol} @ ${current_price:.2f}")
        
        logger.info(f"   Premium: ${premium:.2f} | P&L: ${pnl:.2f}")
        logger.info(f"   Trade Value: ${trade_value:.2f} | Position: {position_pct:.1f}%")
        logger.info(f"   Data Source: {trade['data_source']}")
        logger.info(f"📊 Portfolio: ${self.current_capital:,.2f} | Trades: {len(self.trades)} | P&L: ${self.current_capital - self.initial_capital:,.2f}")
        
        # Save status for monitoring
        self.save_portfolio_status()
        
        return trade
    
    async def send_trade_to_paper_service(self, trade: Dict):
        """Send trade to the paper trading service"""
        try:
            paper_service_url = "http://localhost:11190"
            account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
            
            # Convert trade to order format expected by paper trading service
            order_data = {
                "symbol": trade['symbol'],
                "strategy": trade.get('options_strategy', trade['strategy']),
                "legs": [
                    {
                        "action": "BUY",
                        "option_type": "CALL",  # Default to CALL for butterfly spread
                        "strike_price": trade['current_price'] * 1.02,  # 2% OTM
                        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                        "quantity": trade['contracts'],
                        "premium": trade['premium']
                    }
                ],
                "order_type": "MARKET",
                "time_in_force": "DAY",
                "estimated_premium": trade['premium'],
                "estimated_risk": trade['trade_value'],
                "greeks": trade.get('greeks', {})
            }
            
            async with aiohttp.ClientSession() as session:
                # Send order to paper trading service
                async with session.post(
                    f"{paper_service_url}/api/v1/trading/orders",
                    json=order_data,
                    params={"account_id": account_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Trade sent to paper trading service: Order ID {result.get('order_id', 'unknown')}")
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Failed to send trade to paper service: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending trade to paper service: {e}")

    async def run_continuous_trading(self, interval_seconds: int = 60):
        """Run continuous options trading with live data and advanced capital allocation"""
        logger.info(f"🚀 Starting continuous options trading with advanced capital allocation (interval: {interval_seconds}s)")
        logger.info(f"📊 Live data enabled: {self.live_data_enabled}")
        logger.info(f"⏰ Exit Strategy: Max {self.max_holding_days} days, {self.profit_target_pct:.0%} profit target, {self.stop_loss_pct:.0%} stop loss")
        logger.info(f"🎯 Capital Optimization: Early profit target at {self.early_profit_target_pct:.0%}")
        
        optimization_counter = 0
        
        try:
            while True:
                # First, process any exits
                self.process_exits()
                
                # Optimize capital allocation every 10 iterations
                optimization_counter += 1
                if optimization_counter % 10 == 0:
                    self.optimize_capital_allocation()
                
                # Then generate a new trade (if we have capacity and capital)
                if self.can_open_new_position():
                    try:
                        trade = await self.generate_options_trade()
                        if trade:
                            logger.info("✅ Trade generated successfully!")
                            # Log capital utilization
                            utilization = (self.allocated_capital / self.current_capital) * 100
                            logger.info(f"📊 Capital Utilization: {utilization:.1f}% | Available: ${self.calculate_available_capital():.2f}")
                    except Exception as e:
                        logger.error(f"❌ Error generating trade: {e}")
                else:
                    logger.info(f"📊 Cannot open new position - Active: {len(self.active_positions)}, Available: ${self.calculate_available_capital():.2f}")
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("🛑 Trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Trading error: {e}")

    def save_portfolio_status(self):
        """Save current portfolio status to file for monitoring with advanced capital allocation metrics"""
        available_capital = self.calculate_available_capital()
        utilization = (self.allocated_capital / self.current_capital) * 100 if self.current_capital > 0 else 0
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'allocated_capital': self.allocated_capital,
            'available_capital': available_capital,
            'capital_utilization': utilization,
            'total_pnl': self.current_capital - self.initial_capital,
            'pnl_percentage': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'total_trades': len(self.trades),
            'active_positions': len(self.active_positions),
            'live_data_enabled': self.live_data_enabled,
            'current_prices': self.current_prices,
            'recent_trades': self.trades[-5:] if self.trades else [],  # Last 5 trades
            'active_positions_detail': self.active_positions,  # Current open positions
            'capital_allocation_settings': {
                'max_portfolio_utilization': self.max_portfolio_utilization,
                'min_cash_reserve': self.min_cash_reserve,
                'max_position_size': self.max_position_size,
                'max_risk_per_trade': self.max_risk_per_trade,
                'early_profit_target_pct': self.early_profit_target_pct
            }
        }
        
        # Save to file for monitoring
        with open('config/paper_trading_status.json', 'w') as f:
            json.dump(status, f, indent=2, default=str)
        
        logger.info(f"💾 Portfolio status saved: ${self.current_capital:,.2f} ({len(self.trades)} trades) | Utilization: {utilization:.1f}% | Available: ${available_capital:.2f}")

    def check_exit_conditions(self, position: Dict) -> Optional[Dict]:
        """Check if a position should be exited based on various conditions"""
        current_time = datetime.now()
        entry_time = datetime.fromisoformat(position['timestamp'])
        holding_days = (current_time - entry_time).days
        
        # Get current price for the symbol
        current_price = self.current_prices.get(position['symbol'], position['current_price'])
        
        # Calculate current P&L percentage
        current_pnl_pct = (position['pnl'] / (position['trade_value'] * 0.1))  # Rough P&L calculation
        
        exit_reason = None
        exit_price = current_price
        
        # 1. Time-based exit (max holding period)
        if holding_days >= self.max_holding_days:
            exit_reason = f"max_holding_period_{holding_days}_days"
            logger.info(f"⏰ Exiting {position['symbol']} {position['strategy']} - Max holding period reached ({holding_days} days)")
        
        # 2. Profit target exit
        elif current_pnl_pct >= self.profit_target_pct:
            exit_reason = f"profit_target_{current_pnl_pct:.1%}"
            logger.info(f"🎯 Exiting {position['symbol']} {position['strategy']} - Profit target reached ({current_pnl_pct:.1%})")
        
        # 3. Stop loss exit
        elif current_pnl_pct <= -self.stop_loss_pct:
            exit_reason = f"stop_loss_{current_pnl_pct:.1%}"
            logger.info(f"🛑 Exiting {position['symbol']} {position['strategy']} - Stop loss triggered ({current_pnl_pct:.1%})")
        
        # 4. Minimum holding period check (don't exit too early)
        elif holding_days < self.min_holding_days:
            return None
        
        if exit_reason:
            return {
                'exit_reason': exit_reason,
                'exit_price': exit_price,
                'holding_days': holding_days,
                'final_pnl': position['pnl'],
                'exit_timestamp': current_time.isoformat()
            }
        
        return None

    def process_exits(self):
        """Process all active positions for potential exits"""
        positions_to_close = []
        
        for position in self.active_positions:
            exit_info = self.check_exit_conditions(position)
            if exit_info:
                # Close the position
                position.update(exit_info)
                position['status'] = 'closed'
                self.trades.append(position.copy())
                positions_to_close.append(position)
                
                # Update portfolio
                self.current_capital += position['final_pnl']
                
                logger.info(f"📤 Position closed: {position['strategy']} {position['contracts']} contracts {position['symbol']}")
                logger.info(f"   Entry: ${position['current_price']:.2f} | Exit: ${exit_info['exit_price']:.2f}")
                logger.info(f"   Holding: {exit_info['holding_days']} days | P&L: ${position['final_pnl']:+.2f}")
                logger.info(f"   Reason: {exit_info['exit_reason']}")
        
        # Remove closed positions from active positions
        for position in positions_to_close:
            self.active_positions.remove(position)
        
        if positions_to_close:
            logger.info(f"📊 Portfolio: ${self.current_capital:,.2f} | Active Positions: {len(self.active_positions)} | Closed: {len(positions_to_close)}")
            self.save_portfolio_status()

    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_pnl = self.current_capital - self.initial_capital
        pnl_pct = (total_pnl / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_pnl': total_pnl,
            'pnl_percentage': pnl_pct,
            'total_trades': len(self.trades),
            'live_data_enabled': self.live_data_enabled,
            'current_prices': self.current_prices
        }

async def main():
    """Main function for testing"""
    config = {
        'initial_capital': 4000.0,
        'max_position_size': 0.12,
        'max_risk_per_trade': 0.05,
        'min_position_value': 50.0,
        'live_data_enabled': True,
        'fallback_to_simulated': True,
        'market_data_url': 'http://localhost:11115/api/market-data/current',
        'elliott_wave': {
            'enabled': True,
            'min_confidence_threshold': 0.65,
            'service_url': 'http://elliott-wave-service.trading-system.svc.cluster.local:8000'
        }
    }
    
    engine = LiveDataOptionsPaperTradingEngine(config)
    
    # Test single trade
    logger.info("🧪 Testing single trade generation...")
    trade = await engine.generate_options_trade()
    
    if trade:
        logger.info("✅ Trade generated successfully!")
        logger.info(f"📊 Portfolio Summary: {engine.get_portfolio_summary()}")
    else:
        logger.warning("⚠️ No trade generated")
    
    # Uncomment to run continuous trading
    # await engine.run_continuous_trading(interval_seconds=60)

if __name__ == "__main__":
    asyncio.run(main())
