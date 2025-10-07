"""
Enhanced Options-Enabled Multi-Strategy Trading System
====================================================
Combines multiple strategies with options trading capabilities:

1. Entry Strategies:
   - AdaptiveSectorWaveStrategy (Elliott Wave-based)
   - IchimokuStrategy (high-performing: 51.8% return)
   - Options Wheel Strategy (income generation)

2. Exit Strategies:
   - Multiple exit conditions (profit targets, stop losses)
   - Options-specific exits (time decay, volatility changes)

3. Asset Classes:
   - Stocks (fractional shares)
   - Options (Iron Condor, Cash Secured Puts, Covered Calls)
   - Dynamic allocation based on market conditions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import asyncio

from .base import BaseStrategy
from .advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
from .ichimoku_strategy import IchimokuStrategy
from .options.options_wheel_strategy import OptionsWheelStrategy
from .advanced_exit_strategies import (
    MomentumExitStrategy, 
    VolatilityExitStrategy, 
    MarketRegimeExitStrategy
)
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


class EnhancedOptionsMultiStrategy(BaseStrategy):
    """
    Enhanced Multi-Strategy with Options Trading Capabilities
    
    Features:
    - Multiple entry strategies (Elliott Wave, Ichimoku, Options Wheel)
    - Options trading (Iron Condor, Cash Secured Puts, Covered Calls)
    - Dynamic asset allocation (stocks vs options)
    - Advanced exit management
    - Risk management with cash reserves
    """
    
    def __init__(self, 
                 # Strategy selection
                 enable_elliott_wave: bool = True,  # Restored - Elliott Wave is important
                 enable_ichimoku: bool = True,
                 enable_options_wheel: bool = True,  # Enable options wheel for income generation
                 
                 # Asset allocation
                 stock_allocation_pct: float = 0.20,  # 30% stocks
                 options_allocation_pct: float = 0.50,  # 50% options
                 cash_reserve_pct: float = 0.20,  # 20% cash reserve
                 
                 # Position sizing
                 max_position_size_pct: float = 0.15,  # 15% max per position
                 min_position_size_pct: float = 0.05,  # 5% min per position
                 
                 # Risk management
                 max_concurrent_positions: int = 5,
                 max_position_duration_days: int = 14,
                 
                 # Exit strategies
                 profit_target_pct: float = 0.08,  # 8% profit target
                 stop_loss_pct: float = 0.04,  # 4% stop loss
                 
                 **kwargs):
        
        super().__init__("EnhancedOptionsMultiStrategy", **kwargs)
        
        # Strategy configuration
        self.enable_elliott_wave = enable_elliott_wave
        self.enable_ichimoku = enable_ichimoku
        self.enable_options_wheel = enable_options_wheel
        
        # Asset allocation
        self.stock_allocation_pct = stock_allocation_pct
        self.options_allocation_pct = options_allocation_pct
        self.cash_reserve_pct = cash_reserve_pct
        
        # Position sizing
        self.max_position_size_pct = max_position_size_pct
        self.min_position_size_pct = min_position_size_pct
        
        # Risk management
        self.max_concurrent_positions = max_concurrent_positions
        self.max_position_duration_days = max_position_duration_days
        
        # Exit strategies
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        
        # Initialize strategies
        self.entry_strategies = {}
        self.exit_strategies = {}
        self.active_positions = {}
        self.position_entry_day = {}
        self.position_entry_price = {}
        self.position_entry_strategy = {}
        
        # Performance tracking
        self.strategy_performance = {
            'elliott_wave': {'trades': 0, 'wins': 0, 'total_return': 0.0},
            'ichimoku': {'trades': 0, 'wins': 0, 'total_return': 0.0},
            'options_wheel': {'trades': 0, 'wins': 0, 'total_return': 0.0}
        }
        
        # Market regime tracking
        self.current_market_regime = 'neutral'
        self.volatility_regime = 'normal'
        
    async def initialize_strategies(self):
        """Initialize all trading strategies"""
        try:
            if self.enable_elliott_wave:
                self.entry_strategies['elliott_wave'] = AdaptiveSectorWaveStrategy()
                
            if self.enable_ichimoku:
                self.entry_strategies['ichimoku'] = IchimokuStrategy()
                
            if self.enable_options_wheel:
                self.entry_strategies['options_wheel'] = OptionsWheelStrategy()
            
            # Initialize exit strategies
            self.exit_strategies['momentum'] = MomentumExitStrategy()
            self.exit_strategies['volatility'] = VolatilityExitStrategy()
            self.exit_strategies['regime'] = MarketRegimeExitStrategy()
            
            logger.info(f"✅ Initialized {len(self.entry_strategies)} entry strategies and {len(self.exit_strategies)} exit strategies")
            
        except Exception as e:
            logger.error(f"❌ Error initializing strategies: {e}")
            raise
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal using multi-strategy approach"""
        
        # Initialize strategies if not done yet
        if not self.entry_strategies:
            await self.initialize_strategies()
        
        # Check if we already have a position in this symbol
        if symbol in self.active_positions:
            return await self._check_exit_signals(symbol, data, historical_date)
        else:
            return await self._check_entry_signals(symbol, data, historical_date)
    
    async def _check_entry_signals(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Check for entry signals from multiple strategies"""
        
        # Check if we're at max positions
        if len(self.active_positions) >= self.max_concurrent_positions:
            logger.debug(f"⚠️ {symbol} - Max positions reached ({self.max_concurrent_positions})")
            return None
        
        # Get signals from all entry strategies
        strategy_signals = {}
        
        for strategy_name, strategy in self.entry_strategies.items():
            try:
                # Fix data format for OptionsWheelStrategy
                if strategy_name == 'options_wheel':
                    # Convert 'Close' to 'close' for OptionsWheelStrategy
                    data_fixed = data.copy()
                    if 'Close' in data_fixed.columns:
                        data_fixed['close'] = data_fixed['Close']
                    if 'Volume' in data_fixed.columns:
                        data_fixed['volume'] = data_fixed['Volume']
                    signal = await strategy.generate_signal(symbol, data_fixed, historical_date)
                else:
                    signal = await strategy.generate_signal(symbol, data, historical_date)
                    
                if signal and signal.confidence > 0.5:  # Minimum confidence threshold
                    strategy_signals[strategy_name] = signal
                    logger.info(f"🎯 {symbol} - {strategy_name} signal: {signal.action} at ${signal.price:.2f} (confidence: {signal.confidence:.2f})")
            except Exception as e:
                logger.warning(f"⚠️ {symbol} - {strategy_name} error: {e}")
                continue
        
        if not strategy_signals:
            return None
        
        # Select best signal based on confidence and strategy performance
        best_signal = self._select_best_entry_signal(symbol, strategy_signals)
        
        if best_signal:
            # Calculate position size based on asset class
            position_size, asset_class = self._calculate_position_size(symbol, best_signal, data)
            
            if position_size > 0:
                # Create enhanced signal
                enhanced_signal = TradeSignal(
                    symbol=symbol,
                    action=best_signal.action,
                    price=best_signal.price,
                    quantity=position_size,
                    confidence=best_signal.confidence,
                    timestamp=best_signal.timestamp,
                    strategy=f"{self.name}_{best_signal.strategy}",
                    metadata={
                        **best_signal.metadata,
                        'entry_strategy': best_signal.strategy,
                        'asset_class': asset_class,
                        'position_size_pct': position_size / (best_signal.price * position_size) if position_size > 0 else 0,
                        'multi_strategy': True
                    }
                )
                
                # Track the position
                self.active_positions[symbol] = {
                    'entry_price': best_signal.price,
                    'entry_day': len(data),
                    'entry_strategy': best_signal.strategy,
                    'asset_class': asset_class,
                    'quantity': position_size
                }
                
                logger.info(f"🎯 ENTRY: {symbol} at ${best_signal.price:.2f} ({asset_class}) - {best_signal.strategy} (confidence: {best_signal.confidence:.2f})")
                
                return enhanced_signal
        
        return None
    
    def _select_best_entry_signal(self, symbol: str, strategy_signals: Dict[str, TradeSignal]) -> Optional[TradeSignal]:
        """Select the best entry signal based on confidence and strategy performance"""
        
        if not strategy_signals:
            return None
        
        # Score each signal
        scored_signals = []
        
        for strategy_name, signal in strategy_signals.items():
            # Base score from confidence
            score = signal.confidence
            
            # Adjust based on strategy performance
            perf = self.strategy_performance.get(strategy_name, {'trades': 0, 'wins': 0, 'total_return': 0.0})
            
            if perf['trades'] > 0:
                win_rate = perf['wins'] / perf['trades']
                avg_return = perf['total_return'] / perf['trades']
                
                # Boost score for high-performing strategies
                score += win_rate * 0.2  # Up to 20% boost for win rate
                score += max(0, avg_return) * 0.1  # Up to 10% boost for positive returns
            
            # Prefer Ichimoku strategy (known high performer)
            if strategy_name == 'ichimoku':
                score += 0.1
            
            scored_signals.append((score, signal, strategy_name))
        
        # Sort by score and return best
        scored_signals.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_signal, best_strategy = scored_signals[0]
        logger.info(f"🏆 {symbol} - Selected {best_strategy} signal (score: {best_score:.3f})")
        
        # Log all available signals for comparison
        logger.info(f"📊 {symbol} - Available signals:")
        for i, (score, signal, strategy_name) in enumerate(scored_signals):
            logger.info(f"  {i+1}. {strategy_name}: score={score:.3f}, confidence={signal.confidence:.2f}")
        
        return best_signal
    
    def _calculate_position_size(self, symbol: str, signal: TradeSignal, data: pd.DataFrame) -> Tuple[float, str]:
        """Calculate position size based on asset class and market conditions"""
        
        current_price = signal.price
        confidence = signal.confidence
        
        # Determine asset class based on strategy and market conditions
        asset_class = self._determine_asset_class(signal, data)
        
        # Calculate available capital for this asset class (5% cash reserve)
        if asset_class == 'STOCK':
            available_capital = 4000 * 0.95 * 0.20  # 20% of available $3,800 = $760
        elif asset_class == 'OPTIONS':
            available_capital = 4000 * 0.95 * 0.75  # 75% of available $3,800 = $2,850
        else:
            available_capital = 4000 * 0.95 * 0.20  # Default to stocks
        
        # Calculate position size based on confidence
        base_position_pct = self.min_position_size_pct + (confidence - 0.5) * (self.max_position_size_pct - self.min_position_size_pct)
        position_pct = min(base_position_pct, self.max_position_size_pct)
        
        position_value = available_capital * position_pct
        quantity = position_value / current_price
        
        # Ensure minimum trade value
        if position_value < 50:  # Minimum $50 trade
            return 0, asset_class
        
        logger.info(f"💰 {symbol} - Position size: ${position_value:.2f} ({position_pct:.1%} of {asset_class} allocation)")
        
        return quantity, asset_class
    
    def _determine_asset_class(self, signal: TradeSignal, data: pd.DataFrame) -> str:
        """Determine whether to trade stocks or options based on signal and market conditions"""
        
        # Check if signal already specifies asset class
        if 'asset_class' in signal.metadata:
            return signal.metadata['asset_class']
        
        # Check if it's an options strategy
        if 'options_strategy' in signal.metadata:
            return 'OPTIONS'
        
        # Determine based on market conditions
        volatility = self._calculate_volatility(data)
        trend_strength = self._calculate_trend_strength(data)
        
        # High volatility + strong trend -> Options (straddle/strangle)
        if volatility > 0.3 and abs(trend_strength) > 0.02:
            return 'OPTIONS'
        
        # Low volatility + weak trend -> Options (Iron Condor)
        elif volatility < 0.15 and abs(trend_strength) < 0.01:
            return 'OPTIONS'
        
        # Default to stocks
        return 'STOCK'
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate recent volatility"""
        if len(data) < 20:
            return 0.2  # Default moderate volatility
        
        returns = data['Close'].pct_change().dropna()
        return returns.tail(20).std() * np.sqrt(252)  # Annualized volatility
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength"""
        if len(data) < 20:
            return 0.0
        
        sma_20 = data['Close'].tail(20).mean()
        sma_5 = data['Close'].tail(5).mean()
        
        return (sma_5 - sma_20) / sma_20
    
    async def _check_exit_signals(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Check for exit signals from multiple strategies"""
        
        if symbol not in self.active_positions:
            return None
        
        position = self.active_positions[symbol]
        current_price = data['Close'].iloc[-1]
        entry_price = position['entry_price']
        entry_day = position['entry_day']
        current_day = len(data)
        
        # Calculate position metrics
        days_held = current_day - entry_day
        price_change = (current_price - entry_price) / entry_price
        
        # Check exit conditions
        exit_reasons = []
        
        # 1. Profit target
        if price_change >= self.profit_target_pct:
            exit_reasons.append('PROFIT_TARGET')
            logger.info(f"🎯 PROFIT TARGET: {symbol} - {price_change:.2%} profit")
        
        # 2. Stop loss
        elif price_change <= -self.stop_loss_pct:
            exit_reasons.append('STOP_LOSS')
            logger.info(f"🛑 STOP LOSS: {symbol} - {price_change:.2%} loss")
        
        # 3. Time-based exit
        elif days_held >= self.max_position_duration_days:
            exit_reasons.append('TIME_LIMIT')
            logger.info(f"⏰ TIME LIMIT: {symbol} - {days_held} days held")
        
        # 4. Strategy-specific exits
        else:
            strategy_exits = await self._check_strategy_exits(symbol, data, historical_date)
            if strategy_exits:
                exit_reasons.extend(strategy_exits)
        
        # Generate exit signal if any conditions met
        if exit_reasons:
            exit_signal = TradeSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=position['quantity'],
                confidence=0.8,
                timestamp=datetime.now(),
                strategy=f"{self.name}_exit",
                metadata={
                    'exit_reasons': exit_reasons,
                    'days_held': days_held,
                    'price_change_pct': price_change,
                    'entry_strategy': position['entry_strategy'],
                    'asset_class': position['asset_class']
                }
            )
            
            # Clean up position tracking
            del self.active_positions[symbol]
            
            logger.info(f"🚪 EXIT: {symbol} - {', '.join(exit_reasons)} (P&L: {price_change:.2%})")
            
            return exit_signal
        
        return None
    
    async def _check_strategy_exits(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> List[str]:
        """Check for strategy-specific exit signals"""
        
        exit_reasons = []
        
        for exit_name, exit_strategy in self.exit_strategies.items():
            try:
                # Check if exit strategy recommends exit
                if hasattr(exit_strategy, 'should_exit'):
                    should_exit = await exit_strategy.should_exit(symbol, data, historical_date)
                    if should_exit:
                        exit_reasons.append(exit_name.upper())
            except Exception as e:
                logger.warning(f"⚠️ {symbol} - {exit_name} exit check error: {e}")
                continue
        
        return exit_reasons
    
    def update_performance(self, symbol: str, strategy_name: str, pnl: float):
        """Update strategy performance tracking"""
        
        if strategy_name in self.strategy_performance:
            perf = self.strategy_performance[strategy_name]
            perf['trades'] += 1
            perf['total_return'] += pnl
            
            if pnl > 0:
                perf['wins'] += 1
            
            logger.debug(f"📊 Updated {strategy_name} performance: {perf['wins']}/{perf['trades']} wins, {perf['total_return']:.2f} total return")
