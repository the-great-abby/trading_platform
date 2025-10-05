#!/usr/bin/env python3
"""
Aggressive Day Trading Strategy for 15-minute charts
- Targets 10% of options allocation for quick, high-frequency trades
- Uses momentum, volatility breakouts, and scalping techniques
- Designed for intraday positions (same-day entry/exit)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


class AggressiveDayTradingStrategy(BaseStrategy):
    """
    Aggressive Day Trading Strategy for 15-minute charts
    
    Features:
    - Momentum scalping (quick entries/exits)
    - Volatility breakout trades
    - Support/resistance bounces
    - Volume confirmation
    - Same-day position management
    """
    
    def __init__(self,
                 momentum_threshold: float = 0.002,  # 0.2% momentum threshold
                 volatility_threshold: float = 0.015,  # 1.5% volatility threshold
                 volume_multiplier: float = 1.5,  # 50% above average volume
                 max_holding_periods: int = 16,  # 4 hours max (16 * 15min)
                 profit_target: float = 0.008,  # 0.8% profit target
                 stop_loss: float = 0.004,  # 0.4% stop loss
                 allocation_pct: float = 0.10,  # 10% of options allocation
                 **kwargs):
        super().__init__(name="Aggressive_Day_Trading", config=kwargs)
        
        self.momentum_threshold = momentum_threshold
        self.volatility_threshold = volatility_threshold
        self.volume_multiplier = volume_multiplier
        self.max_holding_periods = max_holding_periods
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.allocation_pct = allocation_pct
        
        # Track active positions for same-day management
        self.active_positions = {}
        
        logger.info(f"🎯 Aggressive Day Trading Strategy initialized")
        logger.info(f"   Momentum Threshold: {momentum_threshold:.3f}")
        logger.info(f"   Volatility Threshold: {volatility_threshold:.3f}")
        logger.info(f"   Volume Multiplier: {volume_multiplier:.1f}x")
        logger.info(f"   Max Holding: {max_holding_periods} periods ({max_holding_periods * 15} minutes)")
        logger.info(f"   Profit Target: {profit_target:.3f}")
        logger.info(f"   Stop Loss: {stop_loss:.3f}")
        logger.info(f"   Allocation: {allocation_pct:.1%}")
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate aggressive day trading signals on 15-minute data"""
        
        if len(data) < 20:  # Need enough data for indicators
            return None
        
        current_time = data.index[-1]
        current_price = data['Close'].iloc[-1]
        
        # Check if we already have an active position for this symbol today
        position_key = f"{symbol}_{current_time.date()}"
        if position_key in self.active_positions:
            return await self._check_exit_conditions(symbol, data, position_key)
        
        # Generate entry signals
        signal = await self._generate_entry_signal(symbol, data)
        
        if signal:
            # Track the position
            self.active_positions[position_key] = {
                'entry_time': current_time,
                'entry_price': current_price,
                'entry_signal': signal,
                'periods_held': 0
            }
            
        return signal
    
    async def _generate_entry_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate entry signals using multiple aggressive strategies"""
        
        # Strategy 1: Momentum Scalping
        momentum_signal = self._check_momentum_scalping(symbol, data)
        if momentum_signal:
            logger.debug(f"🚀 {symbol} - Momentum scalping signal generated")
            return momentum_signal
        
        # Strategy 2: Volatility Breakout
        volatility_signal = self._check_volatility_breakout(symbol, data)
        if volatility_signal:
            logger.debug(f"⚡ {symbol} - Volatility breakout signal generated")
            return volatility_signal
        
        # Strategy 3: Support/Resistance Bounce
        sr_signal = self._check_support_resistance_bounce(symbol, data)
        if sr_signal:
            logger.debug(f"🎯 {symbol} - Support/Resistance bounce signal generated")
            return sr_signal
        
        return None
    
    def _check_momentum_scalping(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Check for momentum scalping opportunities"""
        
        if len(data) < 5:
            return None
        
        # Calculate short-term momentum (3 periods = 45 minutes)
        price_3p = data['Close'].iloc[-1] / data['Close'].iloc[-4] - 1
        price_1p = data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1
        
        # Check volume confirmation
        avg_volume = data['Volume'].iloc[-10:].mean()
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        # Momentum scalping conditions
        if (price_3p > self.momentum_threshold and 
            price_1p > self.momentum_threshold * 0.5 and
            volume_ratio > self.volume_multiplier):
            
            # Calculate position size (10% of allocation)
            position_size = self._calculate_aggressive_position_size(data)
            
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=data['Close'].iloc[-1],
                quantity=position_size,
                confidence=min(0.9, 0.5 + (price_3p * 100)),  # Higher momentum = higher confidence
                timestamp=data.index[-1],
                strategy=f"{self.name}_momentum_scalp",
                metadata={
                    'strategy_type': 'momentum_scalping',
                    'momentum_3p': price_3p,
                    'momentum_1p': price_1p,
                    'volume_ratio': volume_ratio,
                    'allocation_pct': self.allocation_pct,
                    'profit_target': self.profit_target,
                    'stop_loss': self.stop_loss
                }
            )
        
        return None
    
    def _check_volatility_breakout(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Check for volatility breakout opportunities"""
        
        if len(data) < 20:
            return None
        
        # Calculate recent volatility (last 10 periods)
        returns = data['Close'].pct_change().dropna()
        recent_vol = returns.iloc[-10:].std()
        avg_vol = returns.iloc[-20:].std()
        
        # Calculate price movement in current period
        current_movement = abs(data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1]
        
        # Volatility breakout conditions
        if (recent_vol > avg_vol * 1.5 and  # High volatility
            current_movement > self.volatility_threshold):  # Strong current movement
            
            # Determine direction
            price_change = data['Close'].iloc[-1] - data['Open'].iloc[-1]
            action = 'BUY' if price_change > 0 else 'SELL'
            
            position_size = self._calculate_aggressive_position_size(data)
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                price=data['Close'].iloc[-1],
                quantity=position_size,
                confidence=min(0.85, 0.6 + (current_movement * 20)),
                timestamp=data.index[-1],
                strategy=f"{self.name}_volatility_breakout",
                metadata={
                    'strategy_type': 'volatility_breakout',
                    'recent_vol': recent_vol,
                    'avg_vol': avg_vol,
                    'vol_ratio': recent_vol / avg_vol,
                    'current_movement': current_movement,
                    'allocation_pct': self.allocation_pct,
                    'profit_target': self.profit_target,
                    'stop_loss': self.stop_loss
                }
            )
        
        return None
    
    def _check_support_resistance_bounce(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Check for support/resistance bounce opportunities"""
        
        if len(data) < 15:
            return None
        
        current_price = data['Close'].iloc[-1]
        current_low = data['Low'].iloc[-1]
        current_high = data['High'].iloc[-1]
        
        # Find recent support and resistance levels
        recent_lows = data['Low'].iloc[-15:].rolling(window=3).min()
        recent_highs = data['High'].iloc[-15:].rolling(window=3).max()
        
        # Check for support bounce (price near recent low)
        support_level = recent_lows.iloc[-5:].min()
        support_distance = abs(current_low - support_level) / support_level
        
        # Check for resistance break (price above recent high)
        resistance_level = recent_highs.iloc[-5:].max()
        resistance_distance = abs(current_high - resistance_level) / resistance_level
        
        # Support bounce conditions
        if support_distance < 0.005 and current_price > data['Open'].iloc[-1]:  # Bouncing off support
            position_size = self._calculate_aggressive_position_size(data)
            
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=current_price,
                quantity=position_size,
                confidence=0.75,
                timestamp=data.index[-1],
                strategy=f"{self.name}_support_bounce",
                metadata={
                    'strategy_type': 'support_bounce',
                    'support_level': support_level,
                    'support_distance': support_distance,
                    'allocation_pct': self.allocation_pct,
                    'profit_target': self.profit_target,
                    'stop_loss': self.stop_loss
                }
            )
        
        # Resistance break conditions
        if resistance_distance < 0.005 and current_price > resistance_level:
            position_size = self._calculate_aggressive_position_size(data)
            
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=current_price,
                quantity=position_size,
                confidence=0.8,
                timestamp=data.index[-1],
                strategy=f"{self.name}_resistance_break",
                metadata={
                    'strategy_type': 'resistance_break',
                    'resistance_level': resistance_level,
                    'resistance_distance': resistance_distance,
                    'allocation_pct': self.allocation_pct,
                    'profit_target': self.profit_target,
                    'stop_loss': self.stop_loss
                }
            )
        
        return None
    
    def _calculate_aggressive_position_size(self, data: pd.DataFrame) -> float:
        """Calculate position size for aggressive day trading"""
        
        # Base position size (10% of allocation)
        base_allocation = self.allocation_pct
        
        # Adjust based on volatility (higher vol = smaller size)
        if len(data) >= 20:
            returns = data['Close'].pct_change().dropna()
            recent_vol = returns.iloc[-10:].std()
            avg_vol = returns.iloc[-20:].std()
            
            # Reduce size if volatility is very high
            vol_adjustment = 1.0 if recent_vol <= avg_vol * 2 else 0.7
            
            # Adjust based on current price movement
            current_movement = abs(data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1]
            movement_adjustment = 1.0 if current_movement < 0.02 else 0.8
            
            final_allocation = base_allocation * vol_adjustment * movement_adjustment
        else:
            final_allocation = base_allocation
        
        # Convert to contract quantity (assuming $4,000 portfolio)
        portfolio_value = 4000.0
        options_allocation = portfolio_value * 0.5  # 50% for options
        aggressive_allocation = options_allocation * final_allocation
        
        # Estimate contract value (rough calculation)
        estimated_contract_value = 150  # $150 per contract estimate
        
        contracts = int(aggressive_allocation / estimated_contract_value)
        return max(1, min(contracts, 3))  # 1-3 contracts max
    
    async def _check_exit_conditions(self, symbol: str, data: pd.DataFrame, position_key: str) -> Optional[TradeSignal]:
        """Check exit conditions for active positions"""
        
        if position_key not in self.active_positions:
            return None
        
        position = self.active_positions[position_key]
        entry_price = position['entry_price']
        entry_time = position['entry_time']
        current_price = data['Close'].iloc[-1]
        current_time = data.index[-1]
        
        # Update holding periods
        position['periods_held'] += 1
        
        # Calculate P&L
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Exit conditions
        exit_reason = None
        
        # 1. Profit target hit
        if pnl_pct >= self.profit_target:
            exit_reason = "profit_target"
        
        # 2. Stop loss hit
        elif pnl_pct <= -self.stop_loss:
            exit_reason = "stop_loss"
        
        # 3. Max holding period reached
        elif position['periods_held'] >= self.max_holding_periods:
            exit_reason = "max_holding_period"
        
        # 4. End of trading day (force exit)
        elif current_time.date() != entry_time.date():
            exit_reason = "end_of_day"
        
        if exit_reason:
            # Clean up position
            del self.active_positions[position_key]
            
            return TradeSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=position['entry_signal'].quantity,
                confidence=0.9,
                timestamp=current_time,
                strategy=f"{self.name}_exit_{exit_reason}",
                metadata={
                    'exit_reason': exit_reason,
                    'holding_periods': position['periods_held'],
                    'pnl_pct': pnl_pct,
                    'entry_price': entry_price,
                    'exit_price': current_price
                }
            )
        
        return None
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get current strategy statistics"""
        
        return {
            'active_positions': len(self.active_positions),
            'allocation_pct': self.allocation_pct,
            'momentum_threshold': self.momentum_threshold,
            'volatility_threshold': self.volatility_threshold,
            'max_holding_periods': self.max_holding_periods,
            'profit_target': self.profit_target,
            'stop_loss': self.stop_loss
        }

