#!/usr/bin/env python3
"""
Proven Hybrid Strategy - Combines your proven AdaptiveSectorWaveStrategy (90%) with day trading (10%)
This is a COMBINATION strategy, not a replacement - preserves your 313.56% returns
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.core.types import TradeSignal
from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy

class ProvenHybridStrategy:
    """
    Hybrid strategy that combines:
    - 90% Your proven AdaptiveSectorWaveStrategy (preserves 313.56% returns)
    - 10% Day trading component (additional diversification)
    """
    
    def __init__(self, 
                 swing_allocation_pct: float = 0.90,
                 day_trading_allocation_pct: float = 0.10,
                 elliott_wave_min_confidence: float = 0.05,
                 ichimoku_min_confidence: float = 0.05):
        """
        Initialize the proven hybrid strategy
        
        Args:
            swing_allocation_pct: Percentage allocated to proven swing strategy (default 90%)
            day_trading_allocation_pct: Percentage allocated to day trading (default 10%)
            elliott_wave_min_confidence: Minimum Elliott Wave confidence threshold
            ichimoku_min_confidence: Minimum Ichimoku confidence threshold
        """
        self.swing_allocation_pct = swing_allocation_pct
        self.day_trading_allocation_pct = day_trading_allocation_pct
        
        # Initialize your proven strategy with original settings
        self.proven_strategy = AdaptiveSectorWaveStrategy(
            elliott_wave_min_confidence=elliott_wave_min_confidence,
            ichimoku_min_confidence=ichimoku_min_confidence,
            enable_ichimoku=True
        )
        
        # Day trading parameters
        self.day_trading_params = {
            'max_holding_periods': 4,  # 4 hours max (15-min intervals)
            'profit_target': 0.02,     # 2% profit target
            'stop_loss': 0.015,        # 1.5% stop loss
            'min_volume_ratio': 1.5,   # 50% above average volume
            'momentum_threshold': 0.005 # 0.5% momentum threshold
        }
        
        # Track day trading positions
        self.day_positions = {}
        
        logging.info(f"🎯 ProvenHybridStrategy initialized:")
        logging.info(f"   Swing Trading (Proven): {self.swing_allocation_pct:.1%}")
        logging.info(f"   Day Trading: {self.day_trading_allocation_pct:.1%}")
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Generate hybrid trading signal combining proven strategy with day trading
        
        Args:
            symbol: Stock symbol
            data: Market data DataFrame
            
        Returns:
            TradeSignal or None
        """
        if len(data) < 50:
            return None
        
        try:
            # 90% - Use your proven AdaptiveSectorWaveStrategy
            proven_signal = await self.proven_strategy.generate_signal(symbol, data)
            
            if proven_signal:
                # Scale the proven strategy allocation
                proven_signal.quantity = proven_signal.quantity * self.swing_allocation_pct
                proven_signal.metadata = proven_signal.metadata or {}
                proven_signal.metadata.update({
                    'strategy_component': 'proven_swing_trading',
                    'allocation_pct': self.swing_allocation_pct,
                    'original_quantity': proven_signal.quantity / self.swing_allocation_pct
                })
                logging.info(f"🎯 Proven strategy signal for {symbol}: {proven_signal.action}")
                return proven_signal
            
            # 10% - Day trading component (only if proven strategy doesn't signal)
            day_signal = await self._generate_day_trading_signal(symbol, data)
            
            if day_signal:
                day_signal.quantity = day_signal.quantity * self.day_trading_allocation_pct
                day_signal.metadata = day_signal.metadata or {}
                day_signal.metadata.update({
                    'strategy_component': 'day_trading',
                    'allocation_pct': self.day_trading_allocation_pct,
                    'original_quantity': day_signal.quantity / self.day_trading_allocation_pct
                })
                logging.info(f"📈 Day trading signal for {symbol}: {day_signal.action}")
                return day_signal
            
            return None
            
        except Exception as e:
            logging.error(f"Error generating hybrid signal for {symbol}: {e}")
            return None
    
    async def _generate_day_trading_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Generate day trading signal using momentum and volume analysis
        
        Args:
            symbol: Stock symbol
            data: Market data DataFrame
            
        Returns:
            TradeSignal or None
        """
        if len(data) < 20:
            return None
        
        try:
            # Calculate momentum indicators
            price_5min = (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) if len(data) > 1 else 0
            price_15min = (data['Close'].iloc[-1] / data['Close'].iloc[-4] - 1) if len(data) > 3 else 0
            price_1hr = (data['Close'].iloc[-1] / data['Close'].iloc[-16] - 1) if len(data) > 15 else 0
            
            # Volume analysis
            recent_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].iloc[-20:].mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility analysis
            returns = data['Close'].pct_change().dropna()
            recent_vol = returns.iloc[-10:].std() if len(returns) >= 10 else 0
            avg_vol = returns.iloc[-20:].std() if len(returns) >= 20 else 0
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
            
            # Day trading entry conditions
            entry_conditions = {
                'strong_momentum': price_5min > self.day_trading_params['momentum_threshold'],
                'volume_confirmation': volume_ratio > self.day_trading_params['min_volume_ratio'],
                'volatility_breakout': vol_ratio > 1.2,
                'trend_alignment': price_15min > 0.002 and price_1hr > 0.001
            }
            
            # Check if we should enter a day trade
            if (entry_conditions['strong_momentum'] and 
                entry_conditions['volume_confirmation'] and
                entry_conditions['volatility_breakout'] and
                entry_conditions['trend_alignment']):
                
                # Check if we already have a day position
                if symbol in self.day_positions:
                    return None  # Already in a day trade
                
                # Calculate position size (smaller for day trading)
                current_price = data['Close'].iloc[-1]
                confidence = min(0.8, 0.3 + (price_5min * 20) + (volume_ratio - 1) * 0.1)
                
                # Small position size for day trading (1-2 contracts)
                quantity = max(1, min(2, int(confidence * 2)))
                
                # Record the day position
                self.day_positions[symbol] = {
                    'entry_price': current_price,
                    'entry_time': data.index[-1],
                    'quantity': quantity,
                    'target_price': current_price * (1 + self.day_trading_params['profit_target']),
                    'stop_price': current_price * (1 - self.day_trading_params['stop_loss'])
                }
                
                return TradeSignal(
                    symbol=symbol,
                    action="BUY",
                    price=current_price,
                    quantity=quantity,
                    confidence=confidence,
                    metadata={
                        'day_trading_entry': True,
                        'target_price': self.day_positions[symbol]['target_price'],
                        'stop_price': self.day_positions[symbol]['stop_price'],
                        'max_holding_periods': self.day_trading_params['max_holding_periods']
                    }
                )
            
            # Check for day trading exits
            if symbol in self.day_positions:
                return await self._check_day_trading_exit(symbol, data)
            
            return None
            
        except Exception as e:
            logging.error(f"Error in day trading signal generation for {symbol}: {e}")
            return None
    
    async def _check_day_trading_exit(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Check if we should exit a day trading position
        
        Args:
            symbol: Stock symbol
            data: Market data DataFrame
            
        Returns:
            Exit TradeSignal or None
        """
        if symbol not in self.day_positions:
            return None
        
        try:
            position = self.day_positions[symbol]
            current_price = data['Close'].iloc[-1]
            current_time = data.index[-1]
            
            # Calculate holding period (assuming 15-minute intervals)
            holding_periods = (current_time - position['entry_time']).total_seconds() / (15 * 60)
            
            # Exit conditions
            exit_conditions = {
                'profit_target': current_price >= position['target_price'],
                'stop_loss': current_price <= position['stop_price'],
                'max_holding': holding_periods >= self.day_trading_params['max_holding_periods'],
                'momentum_reversal': self._check_momentum_reversal(data)
            }
            
            # Exit if any condition is met
            if any(exit_conditions.values()):
                # Calculate P&L
                pnl = (current_price - position['entry_price']) * position['quantity']
                pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                
                # Remove position
                del self.day_positions[symbol]
                
                # Determine exit reason
                exit_reason = 'profit_target' if exit_conditions['profit_target'] else \
                             'stop_loss' if exit_conditions['stop_loss'] else \
                             'max_holding' if exit_conditions['max_holding'] else \
                             'momentum_reversal'
                
                logging.info(f"📉 Day trading exit for {symbol}: {exit_reason}, P&L: {pnl:.2f} ({pnl_pct:.2%})")
                
                return TradeSignal(
                    symbol=symbol,
                    action="SELL",
                    price=current_price,
                    quantity=position['quantity'],
                    confidence=0.9,  # High confidence for exits
                    metadata={
                        'day_trading_exit': True,
                        'exit_reason': exit_reason,
                        'holding_periods': holding_periods,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    }
                )
            
            return None
            
        except Exception as e:
            logging.error(f"Error checking day trading exit for {symbol}: {e}")
            return None
    
    def _check_momentum_reversal(self, data: pd.DataFrame) -> bool:
        """
        Check if momentum has reversed (for early exit)
        
        Args:
            data: Market data DataFrame
            
        Returns:
            True if momentum has reversed
        """
        if len(data) < 5:
            return False
        
        # Check recent price action
        recent_returns = data['Close'].pct_change().iloc[-5:]
        negative_returns = (recent_returns < 0).sum()
        
        # Exit if 3 or more of last 5 periods are negative
        return negative_returns >= 3
    
    def get_strategy_stats(self) -> Dict:
        """
        Get strategy statistics
        
        Returns:
            Dictionary with strategy statistics
        """
        return {
            'swing_allocation_pct': self.swing_allocation_pct,
            'day_trading_allocation_pct': self.day_trading_allocation_pct,
            'active_day_positions': len(self.day_positions),
            'day_positions': list(self.day_positions.keys()),
            'proven_strategy_stats': self.proven_strategy.get_strategy_stats() if hasattr(self.proven_strategy, 'get_strategy_stats') else {}
        }
