#!/usr/bin/env python3
"""
Fibonacci Strategy
=================
A strategy that uses Fibonacci retracement levels for entry and exit signals.
Identifies swing highs/lows and uses Fibonacci ratios for trade decisions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class FibonacciStrategy(BaseStrategy):
    """
    Fibonacci Retracement Strategy
    
    Features:
    - Identifies swing highs and lows
    - Uses Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%)
    - Entry signals at retracement levels
    - Exit signals at trend continuation
    """
    
    def __init__(self, name: str = "Fibonacci", 
                 lookback_period: int = 15,
                 retracement_levels: List[float] = None,
                 min_swing_threshold: float = 0.02):
        super().__init__(name)
        self.lookback_period = lookback_period  # Reduced from 20
        self.retracement_levels = retracement_levels or [0.236, 0.382, 0.5, 0.618, 0.786]  # Added 0.786
        self.min_swing_threshold = min_swing_threshold  # Reduced from 0.05 to 0.02
        
    def _find_swing_points(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Find swing highs and lows"""
        highs = data['High'].rolling(window=self.lookback_period, center=True).max()
        lows = data['Low'].rolling(window=self.lookback_period, center=True).min()
        
        # Identify swing highs and lows
        swing_highs = pd.Series(index=data.index, dtype=bool)
        swing_lows = pd.Series(index=data.index, dtype=bool)
        
        for i in range(self.lookback_period, len(data) - self.lookback_period):
            # Check if current point is a swing high
            if data.iloc[i]['High'] == highs.iloc[i]:
                swing_highs.iloc[i] = True
            
            # Check if current point is a swing low
            if data.iloc[i]['Low'] == lows.iloc[i]:
                swing_lows.iloc[i] = True
        
        return swing_highs, swing_lows
    
    def _calculate_fibonacci_levels(self, swing_high: float, swing_low: float) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        diff = swing_high - swing_low
        levels = {}
        
        for level in self.retracement_levels:
            if swing_high > swing_low:  # Uptrend
                levels[f'fib_{int(level * 100)}'] = swing_high - (diff * level)
            else:  # Downtrend
                levels[f'fib_{int(level * 100)}'] = swing_low + (diff * level)
        
        return levels
    
    def _find_nearest_fib_level(self, price: float, fib_levels: Dict[str, float]) -> Tuple[str, float]:
        """Find the nearest Fibonacci level to current price"""
        nearest_level = None
        min_distance = float('inf')
        
        for level_name, level_price in fib_levels.items():
            distance = abs(price - level_price)
            if distance < min_distance:
                min_distance = distance
                nearest_level = (level_name, level_price)
        
        return nearest_level
    
    def _is_significant_swing(self, swing_high: float, swing_low: float, current_price: float) -> bool:
        """Check if swing is significant enough for Fibonacci analysis"""
        swing_range = abs(swing_high - swing_low)
        return swing_range / current_price > self.min_swing_threshold
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signals based on Fibonacci retracement levels"""
        if len(data) < self.lookback_period * 2:
            return None
        
        # Add symbol to data for reference
        data = data.copy()
        data['symbol'] = symbol
        
        signals = self._generate_signals(data)
        
        # Return the most recent signal if any
        return signals[-1] if signals else None
    
    def _generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals based on Fibonacci retracement levels"""
        if len(data) < self.lookback_period * 2:
            return []
        
        signals = []
        position = 0
        entry_price = 0
        entry_date = None
        current_trend = None  # 'up' or 'down'
        
        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(data)
        
        for i in range(self.lookback_period, len(data)):
            current_price = data.iloc[i]['Close']
            current_date = data.index[i]
            
            # Check for exit signals if we have a position
            if position != 0:
                # Exit on trend continuation beyond Fibonacci levels
                if current_trend == 'up' and current_price > entry_price * 1.05:
                    # Exit long position on strong uptrend continuation
                    exit_signal = TradeSignal(
                        symbol=data.get('symbol', 'UNKNOWN'),
                        timestamp=current_date,
                        action="SELL",
                        price=current_price,
                        quantity=abs(position),
                        strategy=self.name,
                        confidence=0.9,
                        metadata={
                            'strategy': self.name,
                            'exit_reason': 'trend_continuation',
                            'entry_price': entry_price,
                            'entry_date': entry_date,
                            'holding_days': (current_date - entry_date).days if entry_date else 0,
                            'pnl': (current_price - entry_price) * position
                        }
                    )
                    signals.append(exit_signal)
                    position = 0
                    entry_price = 0
                    entry_date = None
                    current_trend = None
                    continue
                
                elif current_trend == 'down' and current_price < entry_price * 0.95:
                    # Exit short position on strong downtrend continuation
                    exit_signal = TradeSignal(
                        symbol=data.get('symbol', 'UNKNOWN'),
                        timestamp=current_date,
                        action="BUY",
                        price=current_price,
                        quantity=abs(position),
                        strategy=self.name,
                        confidence=0.9,
                        metadata={
                            'strategy': self.name,
                            'exit_reason': 'trend_continuation',
                            'entry_price': entry_price,
                            'entry_date': entry_date,
                            'holding_days': (current_date - entry_date).days if entry_date else 0,
                            'pnl': (entry_price - current_price) * abs(position)
                        }
                    )
                    signals.append(exit_signal)
                    position = 0
                    entry_price = 0
                    entry_date = None
                    current_trend = None
                    continue
            
            # Look for new swing points and Fibonacci levels
            if swing_highs.iloc[i] or swing_lows.iloc[i]:
                # Find recent swing high and low
                recent_high = data['High'].iloc[max(0, i-self.lookback_period):i+1].max()
                recent_low = data['Low'].iloc[max(0, i-self.lookback_period):i+1].min()
                
                if self._is_significant_swing(recent_high, recent_low, current_price):
                    # Determine trend direction
                    if recent_high > recent_low:
                        current_trend = 'up'
                        fib_levels = self._calculate_fibonacci_levels(recent_high, recent_low)
                    else:
                        current_trend = 'down'
                        fib_levels = self._calculate_fibonacci_levels(recent_low, recent_high)
                    
                    # Check if current price is near a Fibonacci level
                    nearest_level_name, nearest_level_price = self._find_nearest_fib_level(current_price, fib_levels)
                    price_distance = abs(current_price - nearest_level_price) / current_price
                    
                    # Entry signal if price is near Fibonacci level (within 1%)
                    if price_distance < 0.01 and position == 0:
                        if current_trend == 'up':
                            # Long entry on uptrend retracement
                            position = 1
                            entry_price = current_price
                            entry_date = current_date
                            
                            entry_signal = TradeSignal(
                                symbol=data.get('symbol', 'UNKNOWN'),
                                timestamp=current_date,
                                action="BUY",
                                price=current_price,
                                quantity=1,
                                strategy=self.name,
                                confidence=0.8,
                                metadata={
                                    'strategy': self.name,
                                    'entry_reason': 'fibonacci_retracement',
                                    'fib_level': nearest_level_name,
                                    'fib_price': nearest_level_price,
                                    'trend': current_trend,
                                    'swing_high': recent_high,
                                    'swing_low': recent_low
                                }
                            )
                            signals.append(entry_signal)
                        
                        elif current_trend == 'down':
                            # Short entry on downtrend retracement
                            position = -1
                            entry_price = current_price
                            entry_date = current_date
                            
                            entry_signal = TradeSignal(
                                symbol=data.get('symbol', 'UNKNOWN'),
                                timestamp=current_date,
                                action="SELL",
                                price=current_price,
                                quantity=1,
                                strategy=self.name,
                                confidence=0.8,
                                metadata={
                                    'strategy': self.name,
                                    'entry_reason': 'fibonacci_retracement',
                                    'fib_level': nearest_level_name,
                                    'fib_price': nearest_level_price,
                                    'trend': current_trend,
                                    'swing_high': recent_high,
                                    'swing_low': recent_low
                                }
                            )
                            signals.append(entry_signal)
        
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return {
            'lookback_period': self.lookback_period,
            'retracement_levels': self.retracement_levels,
            'min_swing_threshold': self.min_swing_threshold
        } 