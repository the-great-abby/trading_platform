"""
Enhanced Risk Management Wrapper
Integrates trailing stops with existing strategies for better risk control
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

logger = logging.getLogger(__name__)

class EnhancedRiskManager:
    """
    Enhanced Risk Management with Trailing Stops
    
    Features:
    - Trailing stop integration
    - Dynamic position sizing
    - Risk-adjusted position limits
    - Portfolio-level risk controls
    """
    
    def __init__(self, 
                 trailing_stop_pct: float = 0.03,  # 3% trailing stop
                 max_loss_pct: float = 0.02,       # 2% max loss per trade
                 max_position_pct: float = 0.15,   # 15% max position size
                 min_profit_before_trail: float = 0.01,  # 1% profit before trailing starts
                 atr_multiplier: float = 2.0):    # 2x ATR for dynamic stops
        
        self.trailing_stop_pct = trailing_stop_pct
        self.max_loss_pct = max_loss_pct
        self.max_position_pct = max_position_pct
        self.min_profit_before_trail = min_profit_before_trail
        self.atr_multiplier = atr_multiplier
        
        # Track active positions and their trailing stops
        self.active_positions = {}
        self.trailing_stops = {}
        
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range for dynamic stops"""
        if len(data) < period:
            return data['Close'].iloc[-1] * 0.02  # Default 2% if not enough data
        
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else data['Close'].iloc[-1] * 0.02
    
    def calculate_position_size(self, 
                               capital: float, 
                               price: float, 
                               confidence: float,
                               volatility: float = 0.02) -> int:
        """Calculate risk-adjusted position size"""
        
        # Base position size from risk management
        risk_amount = capital * self.max_loss_pct
        
        # Adjust for confidence (0.5 to 1.0 multiplier)
        confidence_multiplier = 0.5 + (confidence * 0.5)
        
        # Adjust for volatility (smaller positions in high volatility)
        volatility_multiplier = max(0.3, 1.0 - (volatility * 10))
        
        # Calculate final position value
        position_value = risk_amount * confidence_multiplier * volatility_multiplier
        
        # Convert to shares
        shares = int(position_value / price)
        
        # Apply maximum position size limit
        max_shares = int(capital * self.max_position_pct / price)
        shares = min(shares, max_shares)
        
        # Ensure minimum viable position
        min_shares = max(1, int(capital * 0.001 / price))  # 0.1% minimum
        shares = max(shares, min_shares)
        
        return shares
    
    def set_trailing_stop(self, 
                         symbol: str, 
                         entry_price: float, 
                         current_price: float,
                         position_type: str,
                         data: pd.DataFrame) -> float:
        """Set initial trailing stop"""
        
        # Calculate ATR-based stop distance
        atr = self.calculate_atr(data)
        atr_stop_distance = atr * self.atr_multiplier
        
        # Calculate percentage-based stop distance
        pct_stop_distance = current_price * self.trailing_stop_pct
        
        # Use the smaller of the two for tighter risk control
        stop_distance = min(atr_stop_distance, pct_stop_distance)
        
        if position_type == 'BUY':
            trailing_stop = current_price - stop_distance
        else:  # SELL
            trailing_stop = current_price + stop_distance
        
        # Store trailing stop info
        self.trailing_stops[symbol] = {
            'entry_price': entry_price,
            'current_stop': trailing_stop,
            'position_type': position_type,
            'highest_price': current_price if position_type == 'BUY' else current_price,
            'lowest_price': current_price if position_type == 'SELL' else current_price,
            'created_at': datetime.now()
        }
        
        logger.info(f"🛑 Trailing stop set for {symbol}: ${trailing_stop:.2f}")
        return trailing_stop
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> Optional[float]:
        """Update trailing stop as price moves favorably"""
        if symbol not in self.trailing_stops:
            return None
        
        stop_data = self.trailing_stops[symbol]
        position_type = stop_data['position_type']
        entry_price = stop_data['entry_price']
        
        # Calculate current profit
        if position_type == 'BUY':
            profit_pct = (current_price - entry_price) / entry_price
            # Update highest price seen
            stop_data['highest_price'] = max(stop_data['highest_price'], current_price)
        else:  # SELL
            profit_pct = (entry_price - current_price) / entry_price
            # Update lowest price seen
            stop_data['lowest_price'] = min(stop_data['lowest_price'], current_price)
        
        # Only start trailing after minimum profit is reached
        if profit_pct < self.min_profit_before_trail:
            return stop_data['current_stop']
        
        # Calculate new trailing stop
        if position_type == 'BUY':
            new_stop = current_price * (1 - self.trailing_stop_pct)
            # Stop can only move up, never down
            if new_stop > stop_data['current_stop']:
                stop_data['current_stop'] = new_stop
                logger.info(f"📈 Trailing stop updated for {symbol}: ${new_stop:.2f} (Profit: {profit_pct:.1%})")
        else:  # SELL
            new_stop = current_price * (1 + self.trailing_stop_pct)
            # Stop can only move down, never up
            if new_stop < stop_data['current_stop']:
                stop_data['current_stop'] = new_stop
                logger.info(f"📈 Trailing stop updated for {symbol}: ${new_stop:.2f} (Profit: {profit_pct:.1%})")
        
        return stop_data['current_stop']
    
    def check_stop_triggered(self, symbol: str, current_price: float) -> bool:
        """Check if trailing stop is triggered"""
        if symbol not in self.trailing_stops:
            return False
        
        stop_data = self.trailing_stops[symbol]
        position_type = stop_data['position_type']
        
        if position_type == 'BUY':
            return current_price <= stop_data['current_stop']
        else:  # SELL
            return current_price >= stop_data['current_stop']
    
    def remove_trailing_stop(self, symbol: str):
        """Remove trailing stop when position is closed"""
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
            logger.info(f"🛑 Trailing stop removed for {symbol}")
    
    def get_stop_price(self, symbol: str) -> Optional[float]:
        """Get current trailing stop price"""
        if symbol in self.trailing_stops:
            return self.trailing_stops[symbol]['current_stop']
        return None

class RiskManagedStrategy(BaseStrategy):
    """
    Risk-Managed Strategy Wrapper
    
    Wraps any strategy with enhanced risk management including trailing stops
    """
    
    def __init__(self, 
                 base_strategy: BaseStrategy,
                 risk_manager: Optional[EnhancedRiskManager] = None,
                 **kwargs):
        super().__init__(name=f"RiskManaged_{base_strategy.name}", **kwargs)
        self.base_strategy = base_strategy
        self.risk_manager = risk_manager or EnhancedRiskManager()
        
        # Track positions for risk management
        self.active_positions = {}
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate signal with risk management"""
        
        # First, check if we need to exit any existing positions due to trailing stops
        if symbol in self.active_positions:
            current_price = data['Close'].iloc[-1]
            
            # Update trailing stop
            self.risk_manager.update_trailing_stop(symbol, current_price)
            
            # Check if trailing stop is triggered
            if self.risk_manager.check_stop_triggered(symbol, current_price):
                # Generate exit signal
                position = self.active_positions[symbol]
                exit_signal = TradeSignal(
                    symbol=symbol,
                    action="SELL" if position['action'] == "BUY" else "BUY",
                    quantity=position['quantity'],
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=0.9,  # High confidence for risk management exits
                    metadata={
                        'exit_reason': 'trailing_stop',
                        'entry_price': position['entry_price'],
                        'entry_date': position['entry_date'],
                        'stop_price': self.risk_manager.get_stop_price(symbol),
                        'risk_managed': True
                    }
                )
                
                # Remove position and trailing stop
                del self.active_positions[symbol]
                self.risk_manager.remove_trailing_stop(symbol)
                
                return exit_signal
        
        # Generate signal from base strategy
        base_signal = await self.base_strategy.generate_signal(symbol, data, historical_date)
        
        if not base_signal:
            return None
        
        # Apply risk management to the signal
        current_price = data['Close'].iloc[-1]
        
        # Calculate volatility for position sizing
        returns = data['Close'].pct_change().dropna()
        volatility = returns.tail(10).std() if len(returns) >= 10 else 0.02
        
        # Calculate risk-adjusted position size
        capital_allocation = 1000.0  # $1000 per strategy
        risk_adjusted_quantity = self.risk_manager.calculate_position_size(
            capital_allocation, 
            current_price, 
            base_signal.confidence,
            volatility
        )
        
        # Create risk-managed signal
        risk_managed_signal = TradeSignal(
            symbol=base_signal.symbol,
            action=base_signal.action,
            quantity=risk_adjusted_quantity,
            price=base_signal.price,
            timestamp=base_signal.timestamp,
            strategy=self.name,
            confidence=base_signal.confidence,
            metadata={
                **base_signal.metadata,
                'risk_managed': True,
                'original_quantity': base_signal.quantity,
                'risk_adjusted_quantity': risk_adjusted_quantity,
                'volatility': volatility
            }
        )
        
        # Track new positions for trailing stop management
        if base_signal.action in ['BUY', 'SELL']:
            self.active_positions[symbol] = {
                'action': base_signal.action,
                'quantity': risk_adjusted_quantity,
                'entry_price': current_price,
                'entry_date': datetime.now()
            }
            
            # Set trailing stop
            self.risk_manager.set_trailing_stop(
                symbol, 
                current_price, 
                current_price, 
                base_signal.action,
                data
            )
        
        return risk_managed_signal

