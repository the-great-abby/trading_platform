"""
Enhanced Exit Strategies
=======================
Comprehensive exit strategy system with multiple approaches:
- Fibonacci-based exit targets
- Multi-signal exit confirmation
- Dynamic stop-loss calculation
- Time-based exits
- Trend reversal exits
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class ExitReason(Enum):
    """Exit reason enumeration"""
    FIBONACCI_TARGET = "fibonacci_target"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TREND_REVERSAL = "trend_reversal"
    TIME_BASED = "time_based"
    MULTI_SIGNAL = "multi_signal"
    TRAILING_STOP = "trailing_stop"
    VOLUME_SPIKE = "volume_spike"
    MOMENTUM_LOSS = "momentum_loss"
    VOLATILITY_REGIME = "volatility_regime"
    CORRELATION_BREAK = "correlation_break"
    ML_PREDICTION = "ml_prediction"
    OPTIONS_SIGNAL = "options_signal"
    MARKET_REGIME = "market_regime"

@dataclass
class ExitSignal:
    """Exit signal with detailed information"""
    action: str  # "SELL" for long positions, "BUY" for short positions
    price: float
    confidence: float
    reason: ExitReason
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    metadata: Dict[str, Any] = None

class FibonacciExitStrategy:
    """Fibonacci-based exit strategy with specific price targets"""
    
    def __init__(self, 
                 extension_levels: List[float] = [1.272, 1.618, 2.0, 2.618],
                 retracement_levels: List[float] = [0.236, 0.382, 0.5, 0.618, 0.786]):
        self.extension_levels = extension_levels
        self.retracement_levels = retracement_levels
    
    def calculate_fibonacci_targets(self, 
                                  entry_price: float, 
                                  swing_high: float, 
                                  swing_low: float,
                                  position_type: str) -> Dict[str, float]:
        """Calculate Fibonacci exit targets"""
        
        if position_type == "LONG":
            # For long positions, use extensions above swing high
            swing_range = swing_high - swing_low
            targets = {}
            
            for level in self.extension_levels:
                target_price = swing_high + (swing_range * level)
                targets[f'fib_ext_{int(level * 100)}'] = target_price
            
            # Add retracement levels as stop-losses
            for level in self.retracement_levels:
                stop_price = swing_high - (swing_range * level)
                targets[f'fib_ret_{int(level * 100)}'] = stop_price
                
        else:  # SHORT position
            # For short positions, use extensions below swing low
            swing_range = swing_high - swing_low
            targets = {}
            
            for level in self.extension_levels:
                target_price = swing_low - (swing_range * level)
                targets[f'fib_ext_{int(level * 100)}'] = target_price
            
            # Add retracement levels as stop-losses
            for level in self.retracement_levels:
                stop_price = swing_low + (swing_range * level)
                targets[f'fib_ret_{int(level * 100)}'] = stop_price
        
        return targets
    
    def get_exit_signal(self, 
                       current_price: float,
                       entry_price: float,
                       targets: Dict[str, float],
                       position_type: str) -> Optional[ExitSignal]:
        """Get exit signal based on Fibonacci targets"""
        
        # Check if price reached any target
        for target_name, target_price in targets.items():
            if position_type == "LONG":
                if current_price >= target_price:
                    return ExitSignal(
                        action="SELL",
                        price=target_price,
                        confidence=0.8,
                        reason=ExitReason.FIBONACCI_TARGET,
                        target_price=target_price,
                        metadata={'fibonacci_level': target_name}
                    )
            else:  # SHORT
                if current_price <= target_price:
                    return ExitSignal(
                        action="BUY",
                        price=target_price,
                        confidence=0.8,
                        reason=ExitReason.FIBONACCI_TARGET,
                        target_price=target_price,
                        metadata={'fibonacci_level': target_name}
                    )
        
        return None

class MultiSignalExitStrategy:
    """Exit strategy based on multiple technical signals"""
    
    def __init__(self, 
                 rsi_overbought: float = 70,
                 rsi_oversold: float = 30,
                 macd_threshold: float = 0.0,
                 volume_spike_threshold: float = 2.0):
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.macd_threshold = macd_threshold
        self.volume_spike_threshold = volume_spike_threshold
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       position_type: str,
                       entry_price: float) -> Optional[ExitSignal]:
        """Get exit signal based on multiple technical indicators"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        signals = []
        
        # RSI signals
        rsi = self.calculate_rsi(data['Close']).iloc[-1]
        if position_type == "LONG" and rsi > self.rsi_overbought:
            signals.append(("RSI_OVERBOUGHT", 0.7))
        elif position_type == "SHORT" and rsi < self.rsi_oversold:
            signals.append(("RSI_OVERSOLD", 0.7))
        
        # MACD signals
        macd, signal, histogram = self.calculate_macd(data['Close'])
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        
        if position_type == "LONG" and current_macd < current_signal:
            signals.append(("MACD_BEARISH", 0.6))
        elif position_type == "SHORT" and current_macd > current_signal:
            signals.append(("MACD_BULLISH", 0.6))
        
        # Volume spike signals
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > self.volume_spike_threshold:
            signals.append(("VOLUME_SPIKE", 0.5))
        
        # Price action signals
        price_change = (current_price - entry_price) / entry_price
        if position_type == "LONG" and price_change < -0.05:  # 5% loss
            signals.append(("PRICE_DECLINE", 0.8))
        elif position_type == "SHORT" and price_change > 0.05:  # 5% loss
            signals.append(("PRICE_RISE", 0.8))
        
        # Combine signals
        if len(signals) >= 2:  # Need at least 2 confirming signals
            total_confidence = sum(conf for _, conf in signals) / len(signals)
            
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=min(total_confidence, 0.9),
                reason=ExitReason.MULTI_SIGNAL,
                metadata={
                    'exit_signals': signals,
                    'rsi': rsi,
                    'macd': current_macd,
                    'volume_ratio': volume_ratio,
                    'price_change': price_change
                }
            )
        
        return None

class DynamicStopLossStrategy:
    """Dynamic stop-loss strategy with ATR-based stops"""
    
    def __init__(self, 
                 atr_period: int = 14,
                 atr_multiplier: float = 2.0,
                 trailing_stop: bool = True,
                 max_loss_pct: float = 0.05):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trailing_stop = trailing_stop
        self.max_loss_pct = max_loss_pct
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        
        return atr
    
    def calculate_stop_loss(self, 
                           entry_price: float,
                           position_type: str,
                           atr: float) -> float:
        """Calculate dynamic stop-loss"""
        
        if position_type == "LONG":
            stop_loss = entry_price - (atr * self.atr_multiplier)
        else:  # SHORT
            stop_loss = entry_price + (atr * self.atr_multiplier)
        
        return stop_loss
    
    def update_trailing_stop(self, 
                            current_price: float,
                            current_stop: float,
                            position_type: str,
                            atr: float) -> float:
        """Update trailing stop-loss"""
        
        if position_type == "LONG":
            new_stop = current_price - (atr * self.atr_multiplier)
            return max(current_stop, new_stop)  # Stop can only move up
        else:  # SHORT
            new_stop = current_price + (atr * self.atr_multiplier)
            return min(current_stop, new_stop)  # Stop can only move down
    
    def get_exit_signal(self, 
                       current_price: float,
                       stop_loss: float,
                       position_type: str) -> Optional[ExitSignal]:
        """Check if stop-loss is hit"""
        
        if position_type == "LONG" and current_price <= stop_loss:
            return ExitSignal(
                action="SELL",
                price=stop_loss,
                confidence=0.9,
                reason=ExitReason.STOP_LOSS,
                stop_loss=stop_loss,
                metadata={'stop_type': 'dynamic_atr'}
            )
        elif position_type == "SHORT" and current_price >= stop_loss:
            return ExitSignal(
                action="BUY",
                price=stop_loss,
                confidence=0.9,
                reason=ExitReason.STOP_LOSS,
                stop_loss=stop_loss,
                metadata={'stop_type': 'dynamic_atr'}
            )
        
        return None

class TimeBasedExitStrategy:
    """Time-based exit strategy"""
    
    def __init__(self, 
                 max_holding_days: int = 30,
                 min_holding_days: int = 1,
                 profit_time_decay: bool = True):
        self.max_holding_days = max_holding_days
        self.min_holding_days = min_holding_days
        self.profit_time_decay = profit_time_decay
    
    def get_exit_signal(self, 
                       entry_date: datetime,
                       current_date: datetime,
                       current_price: float,
                       entry_price: float,
                       position_type: str) -> Optional[ExitSignal]:
        """Check for time-based exits"""
        
        holding_days = (current_date - entry_date).days
        
        # Force exit after max holding period
        if holding_days >= self.max_holding_days:
            return ExitSignal(
                action="SELL" if position_type == "LONG" else "BUY",
                price=current_price,
                confidence=0.8,
                reason=ExitReason.TIME_BASED,
                metadata={
                    'holding_days': holding_days,
                    'max_holding_days': self.max_holding_days,
                    'exit_reason': 'max_holding_period'
                }
            )
        
        # Time decay for profitable positions
        if self.profit_time_decay and holding_days > 10:
            price_change = (current_price - entry_price) / entry_price
            if position_type == "LONG" and price_change > 0.1:  # 10% profit
                return ExitSignal(
                    action="SELL",
                    price=current_price,
                    confidence=0.6,
                    reason=ExitReason.TIME_BASED,
                    metadata={
                        'holding_days': holding_days,
                        'exit_reason': 'profit_time_decay',
                        'price_change': price_change
                    }
                )
            elif position_type == "SHORT" and price_change < -0.1:  # 10% profit
                return ExitSignal(
                    action="BUY",
                    price=current_price,
                    confidence=0.6,
                    reason=ExitReason.TIME_BASED,
                    metadata={
                        'holding_days': holding_days,
                        'exit_reason': 'profit_time_decay',
                        'price_change': price_change
                    }
                )
        
        return None

class EnhancedExitManager:
    """Comprehensive exit strategy manager"""
    
    def __init__(self):
        self.fibonacci_exit = FibonacciExitStrategy()
        self.multi_signal_exit = MultiSignalExitStrategy()
        self.dynamic_stop = DynamicStopLossStrategy()
        self.time_based_exit = TimeBasedExitStrategy()
        
        # Exit strategy weights
        self.exit_weights = {
            'fibonacci': 0.3,
            'multi_signal': 0.3,
            'dynamic_stop': 0.2,
            'time_based': 0.2
        }
    
    def get_exit_signal(self, 
                       data: pd.DataFrame,
                       entry_price: float,
                       entry_date: datetime,
                       position_type: str,
                       swing_high: float = None,
                       swing_low: float = None) -> Optional[ExitSignal]:
        """Get comprehensive exit signal"""
        
        current_price = data['Close'].iloc[-1]
        current_date = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
        
        exit_signals = []
        
        # 1. Fibonacci exit
        if swing_high is not None and swing_low is not None:
            fib_targets = self.fibonacci_exit.calculate_fibonacci_targets(
                entry_price, swing_high, swing_low, position_type
            )
            fib_exit = self.fibonacci_exit.get_exit_signal(
                current_price, entry_price, fib_targets, position_type
            )
            if fib_exit:
                exit_signals.append((fib_exit, self.exit_weights['fibonacci']))
        
        # 2. Multi-signal exit
        multi_exit = self.multi_signal_exit.get_exit_signal(
            data, position_type, entry_price
        )
        if multi_exit:
            exit_signals.append((multi_exit, self.exit_weights['multi_signal']))
        
        # 3. Dynamic stop-loss
        atr = self.dynamic_stop.calculate_atr(data).iloc[-1]
        stop_loss = self.dynamic_stop.calculate_stop_loss(entry_price, position_type, atr)
        stop_exit = self.dynamic_stop.get_exit_signal(current_price, stop_loss, position_type)
        if stop_exit:
            exit_signals.append((stop_exit, self.exit_weights['dynamic_stop']))
        
        # 4. Time-based exit
        time_exit = self.time_based_exit.get_exit_signal(
            entry_date, current_date, current_price, entry_price, position_type
        )
        if time_exit:
            exit_signals.append((time_exit, self.exit_weights['time_based']))
        
        # Combine exit signals
        if exit_signals:
            # Sort by confidence and weight
            exit_signals.sort(key=lambda x: x[0].confidence * x[1], reverse=True)
            best_exit = exit_signals[0][0]
            
            # Boost confidence if multiple signals agree
            if len(exit_signals) > 1:
                best_exit.confidence = min(best_exit.confidence * 1.2, 0.95)
                best_exit.metadata['confirming_signals'] = len(exit_signals)
            
            return best_exit
        
        return None
    
    def get_exit_targets(self, 
                        entry_price: float,
                        swing_high: float,
                        swing_low: float,
                        position_type: str) -> Dict[str, float]:
        """Get all exit targets for planning"""
        
        targets = {}
        
        # Fibonacci targets
        fib_targets = self.fibonacci_exit.calculate_fibonacci_targets(
            entry_price, swing_high, swing_low, position_type
        )
        targets.update(fib_targets)
        
        # Add stop-loss target
        targets['stop_loss'] = entry_price * (0.95 if position_type == "LONG" else 1.05)
        
        return targets 