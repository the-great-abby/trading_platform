#!/usr/bin/env python3
"""
Trailing Stop Strategy
======================
A strategy that uses trailing stops to protect profits and limit losses.
The stop level moves up as the price increases, but never moves down.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class TrailingStopStrategy(BaseStrategy):
    """
    Trailing Stop Strategy
    
    Features:
    - Dynamic stop-loss that trails behind price
    - Configurable trailing percentage
    - Profit protection and loss limitation
    - Entry signals based on momentum
    """
    
    def __init__(self, name: str = "TrailingStop", trailing_pct: float = 0.03, 
                 entry_threshold: float = 0.01, min_holding_days: int = 3):
        super().__init__(name)
        self.trailing_pct = trailing_pct  # 3% trailing stop (reduced from 5%)
        self.entry_threshold = entry_threshold  # 1% momentum for entry (reduced from 2%)
        self.min_holding_days = min_holding_days
        
    def _calculate_trailing_stop(self, prices: pd.Series, position: int) -> pd.Series:
        """Calculate trailing stop levels"""
        if position == 0:
            return pd.Series(index=prices.index, dtype=float)
        
        # For long positions, trail below the price
        if position > 0:
            trailing_stop = prices * (1 - self.trailing_pct)
            # Stop can only move up, never down
            trailing_stop = trailing_stop.expanding().max()
        else:
            # For short positions, trail above the price
            trailing_stop = prices * (1 + self.trailing_pct)
            # Stop can only move down, never up
            trailing_stop = trailing_stop.expanding().min()
            
        return trailing_stop
    
    def _calculate_momentum(self, data: pd.DataFrame) -> pd.Series:
        """Calculate price momentum for entry signals"""
        # Use 5-day momentum
        return (data['Close'] - data['Close'].shift(5)) / data['Close'].shift(5)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signals based on trailing stops and momentum"""
        if len(data) < 20:
            return None
        
        # Add symbol to data for reference
        data = data.copy()
        data['symbol'] = symbol
        
        signals = self._generate_signals(data)
        
        # Return the most recent signal if any
        return signals[-1] if signals else None
    
    def _generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals based on trailing stops and momentum"""
        if len(data) < 20:
            return []
        
        signals = []
        position = 0
        entry_price = 0
        entry_date = None
        trailing_stop_level = 0
        
        # Calculate momentum
        momentum = self._calculate_momentum(data)
        
        for i in range(20, len(data)):
            current_price = data.iloc[i]['Close']
            current_date = data.index[i]
            
            # Check for exit signals if we have a position
            if position != 0:
                # Check if price hit trailing stop
                if (position > 0 and current_price <= trailing_stop_level) or \
                   (position < 0 and current_price >= trailing_stop_level):
                    
                    # Exit signal
                    exit_signal = TradeSignal(
                        symbol=data.get('symbol', 'UNKNOWN'),
                        timestamp=current_date,
                        action="SELL" if position > 0 else "BUY",
                        price=current_price,
                        quantity=abs(position),
                        strategy=self.name,
                        confidence=0.8,
                        metadata={
                            'strategy': self.name,
                            'exit_reason': 'trailing_stop',
                            'entry_price': entry_price,
                            'entry_date': entry_date,
                            'holding_days': (current_date - entry_date).days if entry_date else 0,
                            'pnl': (current_price - entry_price) * position if position > 0 else (entry_price - current_price) * abs(position)
                        }
                    )
                    signals.append(exit_signal)
                    position = 0
                    entry_price = 0
                    entry_date = None
                    trailing_stop_level = 0
                    continue
            
            # Check for entry signals if we don't have a position
            if position == 0:
                current_momentum = momentum.iloc[i]
                
                # Long entry on positive momentum
                if current_momentum > self.entry_threshold:
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    trailing_stop_level = current_price * (1 - self.trailing_pct)
                    
                    entry_signal = TradeSignal(
                        symbol=data.get('symbol', 'UNKNOWN'),
                        timestamp=current_date,
                        action="BUY",
                        price=current_price,
                        quantity=1,
                        strategy=self.name,
                        confidence=0.7,
                        metadata={
                            'strategy': self.name,
                            'entry_reason': 'momentum',
                            'momentum': current_momentum,
                            'trailing_stop_pct': self.trailing_pct
                        }
                    )
                    signals.append(entry_signal)
                
                # Short entry on negative momentum
                elif current_momentum < -self.entry_threshold:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    trailing_stop_level = current_price * (1 + self.trailing_pct)
                    
                    entry_signal = TradeSignal(
                        symbol=data.get('symbol', 'UNKNOWN'),
                        timestamp=current_date,
                        action="SELL",
                        price=current_price,
                        quantity=1,
                        strategy=self.name,
                        confidence=0.7,
                        metadata={
                            'strategy': self.name,
                            'entry_reason': 'momentum',
                            'momentum': current_momentum,
                            'trailing_stop_pct': self.trailing_pct
                        }
                    )
                    signals.append(entry_signal)
            
            # Update trailing stop if we have a position
            elif position != 0:
                if position > 0:
                    # For long positions, stop can only move up
                    new_stop = current_price * (1 - self.trailing_pct)
                    trailing_stop_level = max(trailing_stop_level, new_stop)
                else:
                    # For short positions, stop can only move down
                    new_stop = current_price * (1 + self.trailing_pct)
                    trailing_stop_level = min(trailing_stop_level, new_stop)
        
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return {
            'trailing_pct': self.trailing_pct,
            'entry_threshold': self.entry_threshold,
            'min_holding_days': self.min_holding_days
        } 