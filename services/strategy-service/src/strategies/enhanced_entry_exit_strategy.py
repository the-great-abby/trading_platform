"""
Enhanced Entry-Exit Strategy
============================
Combines sophisticated entry signals with advanced exit strategies for optimal performance.
Integrates multiple entry approaches with comprehensive exit management.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from .exit_strategies import EnhancedExitManager, ExitSignal, ExitReason
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class EnhancedEntryExitStrategy(BaseStrategy):
    """
    Enhanced Entry-Exit Strategy
    
    Features:
    - Multiple entry signal confirmation
    - Fibonacci-based exit targets
    - Multi-signal exit confirmation
    - Dynamic stop-loss management
    - Time-based exit rules
    - Position tracking and management
    """
    
    def __init__(self, 
                 name: str = "EnhancedEntryExit",
                 entry_confidence_threshold: float = 0.6,
                 exit_confidence_threshold: float = 0.5,
                 max_position_size: float = 0.1,
                 enable_fibonacci_exits: bool = True,
                 enable_multi_signal_exits: bool = True,
                 enable_dynamic_stops: bool = True,
                 enable_time_exits: bool = True):
        super().__init__(name)
        self.entry_confidence_threshold = entry_confidence_threshold
        self.exit_confidence_threshold = exit_confidence_threshold
        self.max_position_size = max_position_size
        
        # Exit strategy configuration
        self.enable_fibonacci_exits = enable_fibonacci_exits
        self.enable_multi_signal_exits = enable_multi_signal_exits
        self.enable_dynamic_stops = enable_dynamic_stops
        self.enable_time_exits = enable_time_exits
        
        # Initialize exit manager
        self.exit_manager = EnhancedExitManager()
        
        # Position tracking
        self.active_positions = {}
        self.position_history = []
        
        # Entry signal weights
        self.entry_weights = {
            'rsi': 0.25,
            'macd': 0.25,
            'bollinger_bands': 0.20,
            'volume': 0.15,
            'momentum': 0.15
        }
    
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
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    def get_entry_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get multiple entry signals with confidence scores"""
        if len(data) < 50:
            return []
        
        signals = []
        current_price = data['Close'].iloc[-1]
        
        # RSI signals
        rsi = self.calculate_rsi(data['Close']).iloc[-1]
        if not pd.isna(rsi):
            if rsi < 30:  # Oversold
                signals.append({
                    'type': 'rsi',
                    'action': 'BUY',
                    'confidence': 0.8,
                    'value': rsi,
                    'reason': 'oversold'
                })
            elif rsi > 70:  # Overbought
                signals.append({
                    'type': 'rsi',
                    'action': 'SELL',
                    'confidence': 0.8,
                    'value': rsi,
                    'reason': 'overbought'
                })
        
        # MACD signals
        macd, signal, histogram = self.calculate_macd(data['Close'])
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        if not pd.isna(current_macd) and not pd.isna(current_signal):
            if current_macd > current_signal and current_histogram > 0:
                signals.append({
                    'type': 'macd',
                    'action': 'BUY',
                    'confidence': 0.7,
                    'value': current_histogram,
                    'reason': 'bullish_crossover'
                })
            elif current_macd < current_signal and current_histogram < 0:
                signals.append({
                    'type': 'macd',
                    'action': 'SELL',
                    'confidence': 0.7,
                    'value': current_histogram,
                    'reason': 'bearish_crossover'
                })
        
        # Bollinger Bands signals
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data['Close'])
        current_upper = bb_upper.iloc[-1]
        current_lower = bb_lower.iloc[-1]
        
        if not pd.isna(current_upper) and not pd.isna(current_lower):
            if current_price <= current_lower:
                signals.append({
                    'type': 'bollinger_bands',
                    'action': 'BUY',
                    'confidence': 0.6,
                    'value': (current_price - current_lower) / current_lower,
                    'reason': 'below_lower_band'
                })
            elif current_price >= current_upper:
                signals.append({
                    'type': 'bollinger_bands',
                    'action': 'SELL',
                    'confidence': 0.6,
                    'value': (current_price - current_upper) / current_upper,
                    'reason': 'above_upper_band'
                })
        
        # Volume signals
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > 1.5:
            price_change = (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
            if price_change > 0.01:  # 1% price increase
                signals.append({
                    'type': 'volume',
                    'action': 'BUY',
                    'confidence': 0.5,
                    'value': volume_ratio,
                    'reason': 'high_volume_breakout'
                })
            elif price_change < -0.01:  # 1% price decrease
                signals.append({
                    'type': 'volume',
                    'action': 'SELL',
                    'confidence': 0.5,
                    'value': volume_ratio,
                    'reason': 'high_volume_breakdown'
                })
        
        # Momentum signals
        momentum_5 = (current_price - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
        momentum_10 = (current_price - data['Close'].iloc[-10]) / data['Close'].iloc[-10]
        
        if momentum_5 > 0.02 and momentum_10 > 0.05:  # Strong uptrend
            signals.append({
                'type': 'momentum',
                'action': 'BUY',
                'confidence': 0.6,
                'value': momentum_5,
                'reason': 'strong_uptrend'
            })
        elif momentum_5 < -0.02 and momentum_10 < -0.05:  # Strong downtrend
            signals.append({
                'type': 'momentum',
                'action': 'SELL',
                'confidence': 0.6,
                'value': momentum_5,
                'reason': 'strong_downtrend'
            })
        
        return signals
    
    def combine_entry_signals(self, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Combine multiple entry signals into a single decision"""
        if not signals:
            return None
        
        # Group signals by action
        buy_signals = [s for s in signals if s['action'] == 'BUY']
        sell_signals = [s for s in signals if s['action'] == 'SELL']
        
        # Calculate weighted scores
        buy_score = sum(s['confidence'] * self.entry_weights.get(s['type'], 0.1) for s in buy_signals)
        sell_score = sum(s['confidence'] * self.entry_weights.get(s['type'], 0.1) for s in sell_signals)
        
        # Determine action
        if buy_score > sell_score and buy_score > self.entry_confidence_threshold:
            return {
                'action': 'BUY',
                'confidence': buy_score,
                'signals': buy_signals,
                'score': buy_score
            }
        elif sell_score > buy_score and sell_score > self.entry_confidence_threshold:
            return {
                'action': 'SELL',
                'confidence': sell_score,
                'signals': sell_signals,
                'score': sell_score
            }
        
        return None
    
    def find_swing_points(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Find recent swing high and low for Fibonacci calculations"""
        if len(data) < 20:
            return None, None
        
        # Look back 20 periods for swing points
        recent_data = data.tail(20)
        swing_high = recent_data['High'].max()
        swing_low = recent_data['Low'].min()
        
        return swing_high, swing_low
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate enhanced entry-exit signal"""
        
        if len(data) < 50:
            return None
        
        current_price = data['Close'].iloc[-1]
        current_date = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
        
        # Check for exit signals if we have an active position
        if symbol in self.active_positions:
            position = self.active_positions[symbol]
            exit_signal = self._check_exit_signals(data, position, current_date)
            
            if exit_signal:
                # Remove from active positions
                del self.active_positions[symbol]
                self.position_history.append(position)
                
                return TradeSignal(
                    symbol=symbol,
                    action=exit_signal.action,
                    quantity=position['quantity'],
                    price=exit_signal.price,
                    timestamp=current_date,
                    strategy=self.name,
                    confidence=exit_signal.confidence,
                    metadata={
                        'exit_reason': exit_signal.reason.value,
                        'entry_price': position['entry_price'],
                        'entry_date': position['entry_date'],
                        'holding_days': (current_date - position['entry_date']).days,
                        'pnl': (exit_signal.price - position['entry_price']) * position['quantity'] if position['position_type'] == 'LONG' else (position['entry_price'] - exit_signal.price) * position['quantity'],
                        'exit_targets': position.get('exit_targets', {}),
                        'signal_type': 'exit'
                    }
                )
        
        # Generate entry signals
        entry_signals = self.get_entry_signals(data)
        combined_entry = self.combine_entry_signals(entry_signals)
        
        if combined_entry:
            # Calculate position size
            position_size = self._calculate_position_size(current_price, combined_entry['confidence'])
            
            # Find swing points for exit targets
            swing_high, swing_low = self.find_swing_points(data)
            
            # Calculate exit targets
            exit_targets = {}
            if swing_high is not None and swing_low is not None:
                exit_targets = self.exit_manager.get_exit_targets(
                    current_price, swing_high, swing_low, 
                    'LONG' if combined_entry['action'] == 'BUY' else 'SHORT'
                )
            
            # Store position information
            position_type = 'LONG' if combined_entry['action'] == 'BUY' else 'SHORT'
            self.active_positions[symbol] = {
                'entry_price': current_price,
                'entry_date': current_date,
                'position_type': position_type,
                'quantity': position_size,
                'exit_targets': exit_targets,
                'entry_signals': combined_entry['signals']
            }
            
            return TradeSignal(
                symbol=symbol,
                action=combined_entry['action'],
                quantity=position_size,
                price=current_price,
                timestamp=current_date,
                strategy=self.name,
                confidence=combined_entry['confidence'],
                metadata={
                    'entry_signals': [s['type'] for s in combined_entry['signals']],
                    'entry_score': combined_entry['score'],
                    'exit_targets': exit_targets,
                    'position_type': position_type,
                    'signal_type': 'entry'
                }
            )
        
        return None
    
    def _check_exit_signals(self, data: pd.DataFrame, position: Dict[str, Any], current_date: datetime) -> Optional[ExitSignal]:
        """Check for exit signals on active position"""
        
        current_price = data['Close'].iloc[-1]
        
        # Get exit signal from manager
        exit_signal = self.exit_manager.get_exit_signal(
            data=data,
            entry_price=position['entry_price'],
            entry_date=position['entry_date'],
            position_type=position['position_type'],
            swing_high=position.get('exit_targets', {}).get('swing_high'),
            swing_low=position.get('exit_targets', {}).get('swing_low')
        )
        
        return exit_signal
    
    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_size = 1000  # Base position size
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
        return (base_size * confidence_multiplier) / price
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "entry_confidence_threshold": self.entry_confidence_threshold,
            "exit_confidence_threshold": self.exit_confidence_threshold,
            "max_position_size": self.max_position_size,
            "active_positions": len(self.active_positions),
            "position_history": len(self.position_history),
            "exit_strategies": {
                "fibonacci": self.enable_fibonacci_exits,
                "multi_signal": self.enable_multi_signal_exits,
                "dynamic_stops": self.enable_dynamic_stops,
                "time_exits": self.enable_time_exits
            }
        }
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of active positions"""
        if not self.active_positions:
            return {"message": "No active positions"}
        
        total_positions = len(self.active_positions)
        total_value = sum(pos['quantity'] * pos['entry_price'] for pos in self.active_positions.values())
        
        return {
            "total_positions": total_positions,
            "total_value": total_value,
            "positions": list(self.active_positions.keys())
        } 