"""
Enhanced Multi-Strategy Trading System
=====================================
Combines multiple strategies for better entry/exit timing:
- AdaptiveSectorWaveStrategy for entry signals (Elliott Wave-based)
- Multiple exit strategies to let winners run longer
- Combined signal validation for improved risk management
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import asyncio

from .base import BaseStrategy
from .advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
from .advanced_exit_strategies import (
    MomentumExitStrategy, 
    VolatilityExitStrategy, 
    MarketRegimeExitStrategy
)
from ..core.types import TradeSignal

logger = logging.getLogger(__name__)


class EnhancedMultiStrategy(BaseStrategy):
    """
    Enhanced Multi-Strategy Trading System
    
    Features:
    - Uses AdaptiveSectorWaveStrategy for entry signals
    - Multiple exit strategies to optimize exit timing
    - Let winners run until clear exit signals
    - Better risk management through combined signals
    - Position tracking with multiple exit conditions
    """
    
    def __init__(self, 
                 # Entry strategy parameters
                 entry_confidence_threshold: float = 0.5,
                 
                 # Exit strategy parameters
                 momentum_exit_threshold: float = 0.02,
                 volatility_exit_threshold: float = 0.03,
                 
                 # Position management
                 max_position_duration_days: int = 30,
                 min_profit_target: float = 0.05,  # 5% profit target
                 max_loss_stop: float = 0.03,      # 3% stop loss
                 
                 # Risk management
                 max_concurrent_positions: int = 3,
                 position_size_pct: float = 0.05,  # 5% of available cash per trade
                 
                 **kwargs):
        super().__init__(name="Enhanced_Multi_Strategy", **kwargs)
        
        # Strategy type for ensemble compatibility
        self.strategy_type = 'swing_trading'
        
        # Entry strategy
        self.entry_strategy = AdaptiveSectorWaveStrategy()
        
        # Exit strategies
        self.momentum_exit = MomentumExitStrategy(
            momentum_threshold=momentum_exit_threshold
        )
        self.volatility_exit = VolatilityExitStrategy(
            volatility_threshold=volatility_exit_threshold
        )
        self.regime_exit = MarketRegimeExitStrategy()
        
        # Parameters
        self.entry_confidence_threshold = entry_confidence_threshold
        self.max_position_duration_days = max_position_duration_days
        self.min_profit_target = min_profit_target
        self.max_loss_stop = max_loss_stop
        self.max_concurrent_positions = max_concurrent_positions
        self.position_size_pct = position_size_pct
        
        # Position tracking
        self.active_positions: Dict[str, Dict[str, Any]] = {}
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal using multi-strategy approach"""
        
        if len(data) < 50:  # Need sufficient data
            return None
        
        # Check if we already have a position in this symbol
        if symbol in self.active_positions:
            exit_signal = await self._check_exit_signals(symbol, data, historical_date)
            if exit_signal:
                return exit_signal
        else:
            entry_signal = await self._check_entry_signals(symbol, data, historical_date)
            if entry_signal:
                return entry_signal
        
        return None
    
    async def _check_entry_signals(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Check for entry signals using AdaptiveSectorWaveStrategy"""
        
        # Check if we have too many concurrent positions
        if len(self.active_positions) >= self.max_concurrent_positions:
            logger.debug(f"Max concurrent positions reached ({self.max_concurrent_positions}), skipping {symbol}")
            return None
        
        # Get entry signal from AdaptiveSectorWaveStrategy
        entry_signal = await self.entry_strategy.generate_signal(symbol, data, historical_date)
        
        if not entry_signal or entry_signal.confidence < self.entry_confidence_threshold:
            return None
        
        # Adjust position size based on available cash (from configuration)
        available_cash = 3800  # $4,000 - $200 cash reserve (5% cash reserve)
        position_size_pct = self.position_size_pct
        quantity = (available_cash * position_size_pct) / entry_signal.price
        
        # Create enhanced entry signal (always BUY for entries)
        enhanced_signal = TradeSignal(
            symbol=symbol,
            action="BUY",  # Always BUY for entry signals
            price=entry_signal.price,
            quantity=quantity,
            confidence=entry_signal.confidence,
            timestamp=entry_signal.timestamp,
            strategy=f"{self.name}_entry",
            metadata={
                **entry_signal.metadata,
                'entry_strategy': 'AdaptiveSectorWaveStrategy',
                'position_size_pct': position_size_pct,
                'multi_strategy': True,
                'original_action': entry_signal.action  # Track original action
            }
        )
        
        # Track the position
        self.active_positions[symbol] = {
            'entry_price': entry_signal.price,
            'entry_date': entry_signal.timestamp,
            'quantity': quantity,
            'entry_signal': entry_signal,
            'exit_signals_checked': 0
        }
        
        logger.info(f"🎯 ENTRY: {symbol} at ${entry_signal.price:.2f} (confidence: {entry_signal.confidence:.2f})")
        return enhanced_signal
    
    async def _check_exit_signals(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Check for exit signals using multiple exit strategies"""
        
        if symbol not in self.active_positions:
            return None
        
        position = self.active_positions[symbol]
        entry_price = position['entry_price']
        entry_date = position['entry_date']
        quantity = position['quantity']
        
        # Check position duration (realistic holding periods)
        # Use historical_date for backtesting, current time for live trading
        if historical_date:
            current_date = datetime.strptime(historical_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        position_duration = (current_date - entry_date).days
        
        # Realistic holding periods based on strategy type
        max_holding_days = 7 if self.strategy_type == 'day_trading' else 30
        
        if position_duration > max_holding_days:
            logger.info(f"⏰ TIME EXIT: {symbol} - Position held for {position_duration} days (max: {max_holding_days})")
            return self._create_exit_signal(symbol, data, "TIME_EXIT", 0.8)
        
        # Check profit/loss targets
        current_price = data['Close'].iloc[-1]
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct >= self.min_profit_target:
            logger.info(f"🎯 PROFIT TARGET: {symbol} - {pnl_pct:.2%} profit")
            return self._create_exit_signal(symbol, data, "PROFIT_TARGET", 0.9)
        
        if pnl_pct <= -self.max_loss_stop:
            logger.info(f"🛑 STOP LOSS: {symbol} - {pnl_pct:.2%} loss")
            return self._create_exit_signal(symbol, data, "STOP_LOSS", 0.9)
        
        # Check exit strategies
        exit_signals = []
        
        # 1. Momentum-based exit
        momentum_exit = self.momentum_exit.get_exit_signal(
            data, "LONG", entry_price
        )
        if momentum_exit:
            exit_signals.append(("MOMENTUM", momentum_exit.confidence))
        
        # 2. Volatility-based exit
        volatility_exit = self.volatility_exit.get_exit_signal(
            data, "LONG", entry_price
        )
        if volatility_exit:
            exit_signals.append(("VOLATILITY", volatility_exit.confidence))
        
        # 3. Market regime exit
        regime_exit = self.regime_exit.get_exit_signal(
            data, "LONG", entry_price
        )
        if regime_exit:
            exit_signals.append(("REGIME", regime_exit.confidence))
        
        # Combine exit signals - require at least 2 strategies to agree
        if len(exit_signals) >= 2:
            avg_confidence = sum(conf for _, conf in exit_signals) / len(exit_signals)
            exit_reasons = [reason for reason, _ in exit_signals]
            
            logger.info(f"🚪 MULTI EXIT: {symbol} - {exit_reasons} (avg confidence: {avg_confidence:.2f})")
            return self._create_exit_signal(symbol, data, f"MULTI_EXIT_{'_'.join(exit_reasons)}", avg_confidence)
        
        # Update position tracking
        position['exit_signals_checked'] += 1
        
        return None
    
    def _create_exit_signal(self, symbol: str, data: pd.DataFrame, reason: str, confidence: float) -> TradeSignal:
        """Create exit signal and clean up position tracking"""
        
        current_price = data['Close'].iloc[-1]
        position = self.active_positions[symbol]
        quantity = position['quantity']
        
        # Remove from active positions
        del self.active_positions[symbol]
        
        return TradeSignal(
            symbol=symbol,
            action="SELL",
            price=current_price,
            quantity=quantity,
            confidence=confidence,
            timestamp=datetime.now(),
            strategy=f"{self.name}_exit",
            metadata={
                'exit_reason': reason,
                'entry_price': position['entry_price'],
                'entry_date': position['entry_date'],
                'position_duration_days': (datetime.now() - position['entry_date']).days,
                'multi_strategy': True
            }
        )
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of current positions"""
        return {
            'active_positions': len(self.active_positions),
            'max_concurrent_positions': self.max_concurrent_positions,
            'positions': {
                symbol: {
                    'entry_price': pos['entry_price'],
                    'entry_date': pos['entry_date'],
                    'quantity': pos['quantity'],
                    'days_held': (datetime.now() - pos['entry_date']).days
                }
                for symbol, pos in self.active_positions.items()
            }
        }
    
    def reset_positions(self):
        """Reset all position tracking (useful for backtesting)"""
        self.active_positions.clear()
        logger.info("🔄 Position tracking reset")
