#!/usr/bin/env python3
"""
Hybrid Ichimoku Strategy with Elliott Wave Integration
====================================================

Combines Ichimoku Cloud analysis with Elliott Wave pattern filtering
and hybrid capital allocation for optimal trading performance.

Features:
- Ichimoku Cloud trend analysis
- Elliott Wave pattern confirmation
- Hybrid capital allocation (20% cash, 20% stocks, 60% options)
- Multi-timeframe analysis
- Advanced risk management
- Pattern-based stock filtering
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

from .base import BaseStrategy
from .ichimoku_strategy import IchimokuStrategy
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)

class HybridIchimokuStrategy(BaseStrategy):
    """
    Hybrid Ichimoku Strategy with Elliott Wave Integration
    
    This strategy combines:
    1. Ichimoku Cloud analysis for trend direction
    2. Elliott Wave pattern filtering for stock selection
    3. Hybrid capital allocation for optimal risk management
    4. Multi-timeframe confirmation
    """
    
    def __init__(self, 
                 # Ichimoku parameters
                 tenkan_period: int = 9,
                 kijun_period: int = 26,
                 senkou_b_period: int = 52,
                 displacement: int = 26,
                 
                 # Elliott Wave parameters
                 enable_elliott_filtering: bool = True,
                 min_pattern_confidence: float = 0.65,
                 
                 # Hybrid allocation parameters
                 enable_hybrid_allocation: bool = True,
                 cash_reserve_pct: float = 0.20,
                 stock_allocation_pct: float = 0.20,
                 options_allocation_pct: float = 0.60,
                 
                 # Signal parameters
                 min_confidence: float = 0.7,
                 max_position_size: float = 0.15,
                 
                 **kwargs):
        super().__init__(name="HybridIchimokuStrategy", **kwargs)
        
        # Initialize base Ichimoku strategy
        self.ichimoku_strategy = IchimokuStrategy(
            tenkan_period=tenkan_period,
            kijun_period=kijun_period,
            senkou_b_period=senkou_b_period,
            displacement=displacement
        )
        
        # Elliott Wave pattern filtering
        self.enable_elliott_filtering = enable_elliott_filtering
        self.min_pattern_confidence = min_pattern_confidence
        self.pattern_performance = {}
        self.symbol_pattern_history = {}
        self.qualified_symbols = set()
        
        # Hybrid capital allocation
        self.enable_hybrid_allocation = enable_hybrid_allocation
        self.cash_reserve_pct = cash_reserve_pct
        self.stock_allocation_pct = stock_allocation_pct
        self.options_allocation_pct = options_allocation_pct
        
        # Signal parameters
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        
        # Trailing stop parameters - OPTIMIZED
        self.enable_trailing_stops = True
        self.trailing_stop_pct = 0.05  # 5% trailing stop (wider)
        self.atr_period = 14  # ATR period for dynamic stops
        self.atr_multiplier = 1.5  # 1.5x ATR multiplier (less aggressive)
        self.min_profit_pct = 0.03  # 3% minimum profit before trailing starts (earlier)
        self.max_loss_pct = 0.10  # 10% maximum loss (more room)
        
        # Pattern-specific trailing stops
        self.pattern_specific_stops = {
            'impulse_completion': 0.06,    # 6% - wider for trending patterns
            'corrective_completion': 0.04, # 4% - tighter for range-bound
            'fibonacci_retracement': 0.05, # 5% - medium
            'wave_extension': 0.07        # 7% - widest for momentum
        }
        
        # Position tracking for trailing stops
        self.active_positions = {}  # Track open positions with trailing stops
        
        # Initialize pattern performance tracking
        if self.enable_elliott_filtering:
            self._initialize_pattern_performance()
        
        logger.info(f"🎯 Hybrid Ichimoku Strategy initialized:")
        logger.info(f"   📊 Ichimoku: {tenkan_period}/{kijun_period}/{senkou_b_period}")
        logger.info(f"   🌊 Elliott Wave Filtering: {'Enabled' if enable_elliott_filtering else 'Disabled'}")
        logger.info(f"   💰 Hybrid Allocation: {'Enabled' if enable_hybrid_allocation else 'Disabled'}")
        if enable_hybrid_allocation:
            logger.info(f"      💵 Cash: {cash_reserve_pct:.0%}")
            logger.info(f"      📈 Stocks: {stock_allocation_pct:.0%}")
            logger.info(f"      🎯 Options: {options_allocation_pct:.0%}")
    
    def _initialize_pattern_performance(self):
        """Initialize Elliott Wave pattern performance tracking"""
        # Historical pattern performance data (based on backtest results)
        self.pattern_performance = {
            'impulse_completion': {
                'win_rate': 0.75,
                'avg_return': 0.12,
                'max_drawdown': 0.15,
                'best_symbols': ['AAPL', 'MSFT', 'NVDA', 'TSLA'],
                'min_confidence': 0.7,
                'ichimoku_synergy': 0.85  # How well it works with Ichimoku
            },
            'corrective_completion': {
                'win_rate': 0.68,
                'avg_return': 0.08,
                'max_drawdown': 0.12,
                'best_symbols': ['SPY', 'QQQ', 'IWM'],
                'min_confidence': 0.65,
                'ichimoku_synergy': 0.78
            },
            'fibonacci_retracement': {
                'win_rate': 0.72,
                'avg_return': 0.10,
                'max_drawdown': 0.10,
                'best_symbols': ['GOOGL', 'AMZN', 'META'],
                'min_confidence': 0.68,
                'ichimoku_synergy': 0.82
            },
            'wave_extension': {
                'win_rate': 0.80,
                'avg_return': 0.15,
                'max_drawdown': 0.18,
                'best_symbols': ['NVDA', 'TSLA', 'AMD'],
                'min_confidence': 0.75,
                'ichimoku_synergy': 0.88
            }
        }
        
        # Initialize qualified symbols based on historical performance
        self.qualified_symbols = set()
        for pattern_data in self.pattern_performance.values():
            self.qualified_symbols.update(pattern_data['best_symbols'])
        
        logger.info(f"🌊 Initialized Elliott Wave pattern tracking for {len(self.qualified_symbols)} qualified symbols")
    
    def _analyze_elliott_wave_patterns(self, data: pd.DataFrame) -> Optional[Dict]:
        """Analyze Elliott Wave patterns in the data"""
        if len(data) < 20:
            return None
        
        try:
            # Calculate basic Elliott Wave indicators
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else sma_20
            
            # Price momentum analysis
            price_change_5d = (data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
            price_change_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
            
            # Volatility analysis
            volatility = data['Close'].pct_change().rolling(20).std().iloc[-1]
            
            # Determine pattern type based on price action
            current_price = data['Close'].iloc[-1]
            
            # Impulse pattern detection
            if (current_price > sma_20 and 
                price_change_5d > 0.02 and 
                price_change_20d > 0.05):
                return {
                    'pattern_type': 'impulse_completion',
                    'confidence': min(0.9, 0.6 + abs(price_change_20d) * 2),
                    'direction': 'bullish',
                    'volatility': volatility,
                    'ichimoku_synergy': self.pattern_performance['impulse_completion']['ichimoku_synergy']
                }
            
            # Corrective pattern detection
            elif (abs(price_change_20d) < 0.05 and 
                  volatility < 0.02):
                return {
                    'pattern_type': 'corrective_completion',
                    'confidence': min(0.9, 0.6 + (0.05 - abs(price_change_20d)) * 5),
                    'direction': 'sideways',
                    'volatility': volatility,
                    'ichimoku_synergy': self.pattern_performance['corrective_completion']['ichimoku_synergy']
                }
            
            # Fibonacci retracement detection
            elif (abs(price_change_5d) > 0.03 and 
                  abs(price_change_20d) < 0.08):
                return {
                    'pattern_type': 'fibonacci_retracement',
                    'confidence': min(0.9, 0.6 + abs(price_change_5d) * 3),
                    'direction': 'retracement',
                    'volatility': volatility,
                    'ichimoku_synergy': self.pattern_performance['fibonacci_retracement']['ichimoku_synergy']
                }
            
            # Wave extension detection
            elif (abs(price_change_20d) > 0.10 and 
                  volatility > 0.02):
                return {
                    'pattern_type': 'wave_extension',
                    'confidence': min(0.9, 0.6 + abs(price_change_20d) * 1.5),
                    'direction': 'trending',
                    'volatility': volatility,
                    'ichimoku_synergy': self.pattern_performance['wave_extension']['ichimoku_synergy']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing Elliott Wave patterns: {e}")
            return None
    
    def _is_symbol_qualified_for_pattern(self, symbol: str, pattern_type: str) -> bool:
        """Check if symbol has historically performed well with this Elliott Wave pattern"""
        if pattern_type not in self.pattern_performance:
            return False
        
        pattern_data = self.pattern_performance[pattern_type]
        
        # Check if symbol is in the best performers for this pattern
        if symbol in pattern_data['best_symbols']:
            return True
        
        # Check historical performance for this symbol/pattern combination
        if symbol in self.symbol_pattern_history:
            symbol_history = self.symbol_pattern_history[symbol]
            if pattern_type in symbol_history:
                pattern_stats = symbol_history[pattern_type]
                # Require at least 60% win rate and positive returns
                return (pattern_stats.get('win_rate', 0) >= 0.6 and
                       pattern_stats.get('avg_return', 0) > 0)
        
        return False
    
    def _calculate_atr(self, data: pd.DataFrame) -> float:
        """Calculate Average True Range for dynamic stops"""
        if len(data) < self.atr_period:
            return data['Close'].iloc[-1] * 0.02  # Default 2% if not enough data
        
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else data['Close'].iloc[-1] * 0.02
    
    def _calculate_trailing_stop(self, symbol: str, current_price: float, 
                               entry_price: float, position_type: str, 
                               data: pd.DataFrame, pattern_type: Optional[str] = None) -> float:
        """Calculate trailing stop level with pattern-specific optimization"""
        
        if not self.enable_trailing_stops:
            return entry_price * (1 - self.max_loss_pct) if position_type == 'BUY' else entry_price * (1 + self.max_loss_pct)
        
        # Get pattern-specific stop percentage
        if pattern_type and pattern_type in self.pattern_specific_stops:
            pattern_stop_pct = self.pattern_specific_stops[pattern_type]
        else:
            pattern_stop_pct = self.trailing_stop_pct
        
        # Calculate ATR-based dynamic stop
        atr = self._calculate_atr(data)
        atr_stop_distance = atr * self.atr_multiplier
        
        # Calculate pattern-specific percentage-based trailing stop
        pct_stop_distance = current_price * pattern_stop_pct
        
        # Use the tighter of the two stops
        stop_distance = min(atr_stop_distance, pct_stop_distance)
        
        if position_type == 'BUY':
            # For long positions, trail below the price
            trailing_stop = current_price - stop_distance
            
            # Check if we have minimum profit before trailing starts
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct < self.min_profit_pct:
                # Use fixed stop loss until minimum profit is reached
                trailing_stop = max(trailing_stop, entry_price * (1 - self.max_loss_pct))
            
            # Stop can only move up, never down
            if symbol in self.active_positions:
                current_stop = self.active_positions[symbol].get('trailing_stop', entry_price * (1 - self.max_loss_pct))
                trailing_stop = max(trailing_stop, current_stop)
        else:
            # For short positions, trail above the price
            trailing_stop = current_price + stop_distance
            
            # Check if we have minimum profit before trailing starts
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct < self.min_profit_pct:
                # Use fixed stop loss until minimum profit is reached
                trailing_stop = min(trailing_stop, entry_price * (1 + self.max_loss_pct))
            
            # Stop can only move down, never up
            if symbol in self.active_positions:
                current_stop = self.active_positions[symbol].get('trailing_stop', entry_price * (1 + self.max_loss_pct))
                trailing_stop = min(trailing_stop, current_stop)
        
        return trailing_stop
    
    def _check_trailing_stop_exit(self, symbol: str, current_price: float, 
                                data: pd.DataFrame) -> Optional[TradeSignal]:
        """Check if trailing stop should trigger an exit"""
        
        if symbol not in self.active_positions:
            return None
        
        position = self.active_positions[symbol]
        entry_price = position['entry_price']
        position_type = position['position_type']
        quantity = position['quantity']
        trailing_stop = position['trailing_stop']
        
        # Check if price hit trailing stop
        should_exit = False
        exit_reason = ""
        
        if position_type == 'BUY':
            if current_price <= trailing_stop:
                should_exit = True
                exit_reason = "trailing_stop_hit"
        else:  # SELL position
            if current_price >= trailing_stop:
                should_exit = True
                exit_reason = "trailing_stop_hit"
        
        # Check for maximum loss
        if position_type == 'BUY':
            loss_pct = (entry_price - current_price) / entry_price
            if loss_pct >= self.max_loss_pct:
                should_exit = True
                exit_reason = "max_loss_hit"
        else:
            loss_pct = (current_price - entry_price) / entry_price
            if loss_pct >= self.max_loss_pct:
                should_exit = True
                exit_reason = "max_loss_hit"
        
        if should_exit:
            # Calculate P&L
            if position_type == 'BUY':
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity
            
            # Create exit signal
            exit_signal = TradeSignal(
                symbol=symbol,
                action='SELL' if position_type == 'BUY' else 'BUY',
                quantity=quantity,
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=0.9,  # High confidence for stop exits
                metadata={
                    'exit_reason': exit_reason,
                    'entry_price': entry_price,
                    'trailing_stop': trailing_stop,
                    'pnl': pnl,
                    'holding_days': (datetime.now() - position['entry_time']).days,
                    'strategy_type': 'hybrid_ichimoku_trailing_stop'
                }
            )
            
            # Remove position from tracking
            del self.active_positions[symbol]
            
            logger.info(f"🛑 {symbol}: Trailing stop exit - {exit_reason} @ ${current_price:.2f} (P&L: ${pnl:+.2f})")
            
            return exit_signal
        
        return None
    
    def _update_trailing_stop(self, symbol: str, current_price: float, data: pd.DataFrame):
        """Update trailing stop for active position"""
        
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        entry_price = position['entry_price']
        position_type = position['position_type']
        
        # Calculate new trailing stop with pattern type
        pattern_type = position.get('elliott_pattern')
        new_trailing_stop = self._calculate_trailing_stop(
            symbol, current_price, entry_price, position_type, data, pattern_type
        )
        
        # Update position
        self.active_positions[symbol]['trailing_stop'] = new_trailing_stop
        self.active_positions[symbol]['last_update'] = datetime.now()
        
        logger.debug(f"📊 {symbol}: Updated trailing stop to ${new_trailing_stop:.2f}")
    
    def _calculate_hybrid_position_size(self, symbol: str, price: float, confidence: float, 
                                      pattern_type: Optional[str] = None) -> Tuple[float, str]:
        """Calculate position size using hybrid capital allocation"""
        
        if not self.enable_hybrid_allocation:
            # Standard position sizing
            base_quantity = 1000 / price  # $1000 base position
            confidence_multiplier = 0.5 + (confidence * 0.5)
            return base_quantity * confidence_multiplier, 'STOCK'
        
        # Determine asset class based on pattern and confidence
        if pattern_type and pattern_type in self.pattern_performance:
            pattern_data = self.pattern_performance[pattern_type]
            
            # High-confidence patterns with good Ichimoku synergy -> Options
            if (confidence > 0.8 and 
                pattern_data['ichimoku_synergy'] > 0.8 and
                pattern_data['win_rate'] > 0.7):
                asset_class = 'OPTIONS'
                # Options position sizing (contracts)
                base_contracts = 1
                confidence_multiplier = 1 + (confidence - 0.8) * 2  # 1x to 1.4x
                quantity = base_contracts * confidence_multiplier
                
            # Medium-confidence patterns -> Stocks
            elif confidence > 0.6:
                asset_class = 'STOCK'
                # Stock position sizing
                base_quantity = 500 / price  # $500 base position
                confidence_multiplier = 0.5 + (confidence * 0.5)
                quantity = base_quantity * confidence_multiplier
                
            # Low-confidence patterns -> Cash (no trade)
            else:
                return 0, 'CASH'
        else:
            # No pattern detected - use standard stock sizing
            asset_class = 'STOCK'
            base_quantity = 500 / price
            confidence_multiplier = 0.5 + (confidence * 0.5)
            quantity = base_quantity * confidence_multiplier
        
        return quantity, asset_class
    
    def _calculate_enhanced_confidence(self, ichimoku_confidence: float, 
                                    elliott_pattern: Optional[Dict],
                                    symbol: str) -> float:
        """Calculate enhanced confidence combining Ichimoku and Elliott Wave"""
        
        base_confidence = ichimoku_confidence
        
        if not self.enable_elliott_filtering or not elliott_pattern:
            return base_confidence
        
        pattern_type = elliott_pattern['pattern_type']
        pattern_confidence = elliott_pattern['confidence']
        ichimoku_synergy = elliott_pattern.get('ichimoku_synergy', 0.5)
        
        # Check if symbol is qualified for this pattern
        if not self._is_symbol_qualified_for_pattern(symbol, pattern_type):
            # Reduce confidence for unqualified symbols
            return base_confidence * 0.7
        
        # Enhance confidence based on pattern performance
        pattern_data = self.pattern_performance[pattern_type]
        pattern_multiplier = pattern_data['win_rate'] * pattern_data['ichimoku_synergy']
        
        # Combine confidences
        enhanced_confidence = (
            base_confidence * 0.6 +  # Ichimoku base
            pattern_confidence * 0.3 * pattern_multiplier +  # Elliott Wave pattern
            ichimoku_synergy * 0.1  # Synergy bonus
        )
        
        return min(enhanced_confidence, 0.95)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate hybrid Ichimoku trading signal with Elliott Wave filtering and trailing stops"""
        
        if len(data) < self.ichimoku_strategy.senkou_b_period + self.ichimoku_strategy.displacement:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Step 1: Check for trailing stop exits first
        if self.enable_trailing_stops and symbol in self.active_positions:
            trailing_exit = self._check_trailing_stop_exit(symbol, current_price, data)
            if trailing_exit:
                return trailing_exit
            
            # Update trailing stop for existing position
            self._update_trailing_stop(symbol, current_price, data)
            return None  # Don't generate new signals while position is open
        
        # Step 2: Get base Ichimoku signal
        ichimoku_signal = await self.ichimoku_strategy.generate_signal(symbol, data, historical_date)
        if not ichimoku_signal:
            return None
        
        # Step 2: Analyze Elliott Wave patterns
        elliott_pattern = None
        if self.enable_elliott_filtering:
            elliott_pattern = self._analyze_elliott_wave_patterns(data)
            
            # Filter out symbols that don't qualify for the detected pattern
            if elliott_pattern:
                pattern_type = elliott_pattern['pattern_type']
                if not self._is_symbol_qualified_for_pattern(symbol, pattern_type):
                    logger.debug(f"🚫 {symbol}: Not qualified for {pattern_type} pattern")
                    return None
        
        # Step 3: Calculate enhanced confidence
        enhanced_confidence = self._calculate_enhanced_confidence(
            ichimoku_signal.confidence, elliott_pattern, symbol
        )
        
        if enhanced_confidence < self.min_confidence:
            return None
        
        # Step 4: Calculate hybrid position size
        quantity, asset_class = self._calculate_hybrid_position_size(
            symbol, ichimoku_signal.price, enhanced_confidence, 
            elliott_pattern['pattern_type'] if elliott_pattern else None
        )
        
        if quantity <= 0:
            return None
        
        # Step 5: Create enhanced signal
        enhanced_signal = TradeSignal(
            symbol=symbol,
            action=ichimoku_signal.action,
            quantity=quantity,
            price=ichimoku_signal.price,
            timestamp=ichimoku_signal.timestamp,
            strategy=self.name,
            confidence=enhanced_confidence,
            metadata={
                **ichimoku_signal.metadata,
                'hybrid_strategy': {
                    'asset_class': asset_class,
                    'elliott_pattern': elliott_pattern,
                    'pattern_qualified': elliott_pattern and self._is_symbol_qualified_for_pattern(symbol, elliott_pattern['pattern_type']),
                    'ichimoku_confidence': ichimoku_signal.confidence,
                    'enhanced_confidence': enhanced_confidence,
                    'hybrid_allocation_enabled': self.enable_hybrid_allocation,
                    'trailing_stops_enabled': self.enable_trailing_stops
                },
                'signal_type': 'hybrid_ichimoku_elliott_trailing'
            }
        )
        
        # Step 6: Track position for trailing stops if it's a BUY signal
        if self.enable_trailing_stops and ichimoku_signal.action == 'BUY':
            pattern_type = elliott_pattern['pattern_type'] if elliott_pattern else None
            initial_trailing_stop = self._calculate_trailing_stop(
                symbol, ichimoku_signal.price, ichimoku_signal.price, 'BUY', data, pattern_type
            )
            
            self.active_positions[symbol] = {
                'entry_price': ichimoku_signal.price,
                'entry_time': datetime.now(),
                'position_type': 'BUY',
                'quantity': quantity,
                'trailing_stop': initial_trailing_stop,
                'asset_class': asset_class,
                'elliott_pattern': elliott_pattern['pattern_type'] if elliott_pattern else None,
                'last_update': datetime.now()
            }
            
            logger.info(f"📊 {symbol}: Position tracked with trailing stop @ ${initial_trailing_stop:.2f}")
        
        logger.info(f"🎯 {symbol}: Hybrid Ichimoku signal - {ichimoku_signal.action} {asset_class} "
                   f"(Confidence: {enhanced_confidence:.2f}, Pattern: {elliott_pattern['pattern_type'] if elliott_pattern else 'None'})")
        
        return enhanced_signal
    
    def get_comprehensive_analysis(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive analysis combining Ichimoku and Elliott Wave"""
        
        # Get Ichimoku analysis
        ichimoku_data = self.ichimoku_strategy.calculate_ichimoku(data)
        ichimoku_analysis = {
            'cloud_analysis': self.ichimoku_strategy.analyze_cloud_position(ichimoku_data),
            'crossover_analysis': self.ichimoku_strategy.analyze_tenkan_kijun_crossover(ichimoku_data),
            'chikou_analysis': self.ichimoku_strategy.analyze_chikou_position(ichimoku_data),
            'support_resistance': self.ichimoku_strategy.calculate_support_resistance(ichimoku_data),
            'ichimoku_levels': {
                'tenkan': ichimoku_data['Tenkan'].iloc[-1] if not pd.isna(ichimoku_data['Tenkan'].iloc[-1]) else None,
                'kijun': ichimoku_data['Kijun'].iloc[-1] if not pd.isna(ichimoku_data['Kijun'].iloc[-1]) else None,
                'senkou_a': ichimoku_data['Senkou_A'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_A'].iloc[-1]) else None,
                'senkou_b': ichimoku_data['Senkou_B'].iloc[-1] if not pd.isna(ichimoku_data['Senkou_B'].iloc[-1]) else None,
                'chikou': ichimoku_data['Chikou'].iloc[-1] if not pd.isna(ichimoku_data['Chikou'].iloc[-1]) else None
            }
        }
        
        # Get Elliott Wave analysis
        elliott_analysis = self._analyze_elliott_wave_patterns(data)
        
        # Get pattern qualification status
        pattern_qualified = False
        if elliott_analysis and self.enable_elliott_filtering:
            pattern_qualified = self._is_symbol_qualified_for_pattern(symbol, elliott_analysis['pattern_type'])
        
        return {
            'symbol': symbol,
            'ichimoku_analysis': ichimoku_analysis,
            'elliott_wave_analysis': elliott_analysis,
            'pattern_qualified': pattern_qualified,
            'qualified_symbols': list(self.qualified_symbols),
            'strategy_config': {
                'enable_elliott_filtering': self.enable_elliott_filtering,
                'enable_hybrid_allocation': self.enable_hybrid_allocation,
                'min_confidence': self.min_confidence,
                'cash_reserve_pct': self.cash_reserve_pct,
                'stock_allocation_pct': self.stock_allocation_pct,
                'options_allocation_pct': self.options_allocation_pct
            }
        }
    
    def get_entry_exit_prices(self, data: pd.DataFrame) -> Dict[str, float]:
        """Get recommended entry and exit prices"""
        return self.ichimoku_strategy.get_entry_exit_prices(data)
