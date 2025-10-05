#!/usr/bin/env python3
"""
Hybrid Options Strategy combining:
- 90% Swing Trading (AdaptiveSectorWaveStrategy on daily charts)
- 10% Aggressive Day Trading (15-minute charts)

This gives us both steady swing trades and quick day trading opportunities.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from src.strategies.base import BaseStrategy
from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
from src.strategies.advanced.aggressive_day_trading_strategy import AggressiveDayTradingStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


class HybridOptionsStrategy(BaseStrategy):
    """
    Hybrid Options Strategy combining swing and day trading
    
    Allocation:
    - 90% Swing Trading (daily charts, multi-day positions)
    - 10% Day Trading (15-minute charts, same-day positions)
    
    This provides:
    - Steady, high-probability swing trades
    - Quick, aggressive day trading opportunities
    - Diversified risk across timeframes
    """
    
    def __init__(self,
                 swing_allocation_pct: float = 0.90,  # 90% for swing trading
                 day_trading_allocation_pct: float = 0.10,  # 10% for day trading
                 enable_swing_trading: bool = True,
                 enable_day_trading: bool = True,
                 **kwargs):
        super().__init__(name="Hybrid_Options_Strategy", config=kwargs)
        
        self.swing_allocation_pct = swing_allocation_pct
        self.day_trading_allocation_pct = day_trading_allocation_pct
        self.enable_swing_trading = enable_swing_trading
        self.enable_day_trading = enable_day_trading
        
        # Initialize sub-strategies
        if self.enable_swing_trading:
            self.swing_strategy = AdaptiveSectorWaveStrategy(
                elliott_wave_min_confidence=0.05,
                ichimoku_min_confidence=0.05,
                enable_ichimoku=True
            )
            logger.info(f"🔄 Swing Trading Strategy initialized ({swing_allocation_pct:.1%} allocation)")
        
        if self.enable_day_trading:
            self.day_trading_strategy = AggressiveDayTradingStrategy(
                momentum_threshold=0.002,
                volatility_threshold=0.015,
                volume_multiplier=1.5,
                max_holding_periods=16,  # 4 hours max
                profit_target=0.008,  # 0.8%
                stop_loss=0.004,  # 0.4%
                allocation_pct=day_trading_allocation_pct
            )
            logger.info(f"⚡ Day Trading Strategy initialized ({day_trading_allocation_pct:.1%} allocation)")
        
        logger.info(f"🎯 Hybrid Options Strategy initialized")
        logger.info(f"   Swing Trading: {'Enabled' if enable_swing_trading else 'Disabled'} ({swing_allocation_pct:.1%})")
        logger.info(f"   Day Trading: {'Enabled' if enable_day_trading else 'Disabled'} ({day_trading_allocation_pct:.1%})")
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate signals from both swing and day trading strategies"""
        
        signals = []
        
        # 1. Generate swing trading signals (daily timeframe)
        if self.enable_swing_trading:
            swing_signal = await self.swing_strategy.generate_signal(symbol, data)
            if swing_signal:
                # Adjust allocation for swing trading
                swing_signal.quantity = int(swing_signal.quantity * self.swing_allocation_pct)
                swing_signal.metadata['strategy_component'] = 'swing_trading'
                swing_signal.metadata['allocation_pct'] = self.swing_allocation_pct
                signals.append(swing_signal)
        
        # 2. Generate day trading signals (15-minute timeframe)
        if self.enable_day_trading:
            # Check if we have 15-minute data available
            if self._is_15min_data(data):
                day_signal = await self.day_trading_strategy.generate_signal(symbol, data)
                if day_signal:
                    day_signal.metadata['strategy_component'] = 'day_trading'
                    day_signal.metadata['allocation_pct'] = self.day_trading_allocation_pct
                    signals.append(day_signal)
        
        # 3. Return the highest confidence signal
        if signals:
            # Sort by confidence and return the best one
            best_signal = max(signals, key=lambda s: s.confidence)
            
            logger.debug(f"🎯 {symbol} - Hybrid signal: {best_signal.metadata['strategy_component']} "
                        f"(confidence: {best_signal.confidence:.3f}, quantity: {best_signal.quantity})")
            
            return best_signal
        
        return None
    
    def _is_15min_data(self, data: pd.DataFrame) -> bool:
        """Check if data is 15-minute timeframe"""
        
        if len(data) < 2:
            return False
        
        # Check time difference between consecutive data points
        time_diff = data.index[1] - data.index[0]
        
        # 15 minutes = 15 * 60 = 900 seconds
        # Allow some tolerance for data irregularities
        return 800 <= time_diff.total_seconds() <= 1000
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get comprehensive strategy statistics"""
        
        stats = {
            'strategy_name': self.name,
            'swing_allocation_pct': self.swing_allocation_pct,
            'day_trading_allocation_pct': self.day_trading_allocation_pct,
            'enable_swing_trading': self.enable_swing_trading,
            'enable_day_trading': self.enable_day_trading
        }
        
        # Add swing trading stats
        if self.enable_swing_trading:
            stats['swing_trading'] = {
                'strategy': 'AdaptiveSectorWaveStrategy',
                'timeframe': 'daily',
                'allocation': self.swing_allocation_pct
            }
        
        # Add day trading stats
        if self.enable_day_trading:
            day_stats = self.day_trading_strategy.get_strategy_stats()
            stats['day_trading'] = {
                'strategy': 'AggressiveDayTradingStrategy',
                'timeframe': '15_minute',
                'allocation': self.day_trading_allocation_pct,
                'active_positions': day_stats['active_positions'],
                'max_holding_periods': day_stats['max_holding_periods'],
                'profit_target': day_stats['profit_target'],
                'stop_loss': day_stats['stop_loss']
            }
        
        return stats
    
    def update_allocation(self, swing_pct: float = None, day_trading_pct: float = None):
        """Update allocation percentages dynamically"""
        
        if swing_pct is not None:
            self.swing_allocation_pct = swing_pct
            logger.info(f"📊 Swing trading allocation updated to {swing_pct:.1%}")
        
        if day_trading_pct is not None:
            self.day_trading_allocation_pct = day_trading_pct
            if hasattr(self, 'day_trading_strategy'):
                self.day_trading_strategy.allocation_pct = day_trading_pct
            logger.info(f"⚡ Day trading allocation updated to {day_trading_pct:.1%}")
        
        # Ensure allocations sum to 1.0
        total = self.swing_allocation_pct + self.day_trading_allocation_pct
        if abs(total - 1.0) > 0.01:
            logger.warning(f"⚠️ Allocations sum to {total:.1%}, not 100%")
    
    def disable_component(self, component: str):
        """Disable swing trading or day trading component"""
        
        if component == 'swing_trading':
            self.enable_swing_trading = False
            logger.info("🔄 Swing trading disabled")
        elif component == 'day_trading':
            self.enable_day_trading = False
            logger.info("⚡ Day trading disabled")
        else:
            logger.warning(f"⚠️ Unknown component: {component}")
    
    def enable_component(self, component: str):
        """Enable swing trading or day trading component"""
        
        if component == 'swing_trading':
            self.enable_swing_trading = True
            logger.info("🔄 Swing trading enabled")
        elif component == 'day_trading':
            self.enable_day_trading = True
            logger.info("⚡ Day trading enabled")
        else:
            logger.warning(f"⚠️ Unknown component: {component}")

