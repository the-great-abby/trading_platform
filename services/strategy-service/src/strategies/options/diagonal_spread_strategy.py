"""
Diagonal Spread Options Strategy
===============================
A strategy that combines calendar and vertical spreads by buying a longer-term option
and selling a shorter-term option at different strikes.
Ideal for directional trades with time decay advantage.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import random

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.options_data_service import OptionsDataService, OptionContract

logger = get_trading_logger()

class DiagonalSpreadStrategy(BaseStrategy):
    """
    Diagonal Spread Options Strategy
    
    Features:
    - Combines calendar and vertical spreads
    - Directional bias with time decay advantage
    - Lower cost than outright options
    - Defined risk and reward
    - Automated strike and expiration selection
    - Theta decay optimization
    """
    
    def __init__(self, 
                 name: str = "DiagonalSpread",
                 short_dte: int = 14,  # Short-term expiration
                 long_dte: int = 45,   # Long-term expiration
                 profit_target_pct: float = 0.7,  # 70% of max profit
                 stop_loss_pct: float = 1.5,  # 1.5x max loss
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_delta: float = 0.3,  # Minimum delta for strike selection
                 max_delta: float = 0.7,  # Maximum delta for strike selection
                 min_dte_spread: int = 21,  # Minimum days between expirations
                 direction: str = "bullish",  # "bullish" or "bearish"
                 min_theta_ratio: float = 1.5):  # Minimum theta ratio
        super().__init__(name)
        self.short_dte = short_dte
        self.long_dte = long_dte
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.min_dte_spread = min_dte_spread
        self.direction = direction
        self.min_theta_ratio = min_theta_ratio
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
    
    def check_market_conditions(self, data: pd.DataFrame, options_data: Optional[Dict] = None) -> bool:
        """Check if market conditions are suitable for diagonal spread strategy"""
        
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check trend conditions
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            trend = (sma_20 - sma_50) / sma_50
            
            # Check if trend aligns with strategy direction
            if self.direction == "bullish" and trend < 0.02:
                return False
            elif self.direction == "bearish" and trend > -0.02:
                return False
        
        # Check volatility conditions
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            volatility = atr / current_price
            if volatility < 0.015:  # Less than 1.5% daily volatility
                return False
        
        return True
    
    def select_diagonal_strikes(self, current_price: float, 
                               short_options: List[OptionContract],
                               long_options: List[OptionContract]) -> Optional[Tuple[OptionContract, OptionContract]]:
        """Select strikes for diagonal spread"""
        
        if self.direction == "bullish":
            # For bullish diagonal: buy long-term call, sell short-term call
            long_calls = [opt for opt in long_options 
                         if opt.option_type == 'call' and 
                         self.min_delta <= abs(opt.delta) <= self.max_delta]
            short_calls = [opt for opt in short_options 
                          if opt.option_type == 'call' and 
                          opt.strike > current_price * 1.02]  # OTM short call
            
            if not long_calls or not short_calls:
                return None
            
            # Select long call (closer to ATM)
            long_call = min(long_calls, key=lambda x: abs(x.strike - current_price))
            
            # Select short call (further OTM)
            short_call = min(short_calls, key=lambda x: x.strike)
            
            return long_call, short_call
            
        else:  # bearish
            # For bearish diagonal: buy long-term put, sell short-term put
            long_puts = [opt for opt in long_options 
                        if opt.option_type == 'put' and 
                        self.min_delta <= abs(opt.delta) <= self.max_delta]
            short_puts = [opt for opt in short_options 
                         if opt.option_type == 'put' and 
                         opt.strike < current_price * 0.98]  # OTM short put
            
            if not long_puts or not short_puts:
                return None
            
            # Select long put (closer to ATM)
            long_put = min(long_puts, key=lambda x: abs(x.strike - current_price))
            
            # Select short put (further OTM)
            short_put = max(short_puts, key=lambda x: x.strike)
            
            return long_put, short_put
    
    def calculate_position_metrics(self, long_option: OptionContract, short_option: OptionContract, 
                                 current_price: float) -> Dict[str, Any]:
        """Calculate diagonal spread position metrics"""
        
        # Net debit/credit
        net_cost = long_option.price - short_option.price
        
        # Calculate Greeks
        total_delta = long_option.delta - short_option.delta
        total_gamma = long_option.gamma - short_option.gamma
        total_theta = long_option.theta - short_option.theta
        total_vega = long_option.vega - short_option.vega
        
        # Risk/reward calculations
        if self.direction == "bullish":
            max_loss = net_cost
            max_profit = float('inf')  # Unlimited upside
            breakeven = long_option.strike + net_cost
        else:  # bearish
            max_loss = net_cost
            max_profit = short_option.strike - long_option.strike - net_cost
            breakeven = long_option.strike - net_cost
        
        return {
            'net_cost': net_cost,
            'breakeven': breakeven,
            'max_loss': max_loss,
            'max_profit': max_profit,
            'total_delta': total_delta,
            'total_gamma': total_gamma,
            'total_theta': total_theta,
            'total_vega': total_vega,
            'long_strike': long_option.strike,
            'short_strike': short_option.strike,
            'long_price': long_option.price,
            'short_price': short_option.price,
            'direction': self.direction
        }
    
    def calculate_theta_ratio(self, long_option: OptionContract, short_option: OptionContract) -> float:
        """Calculate theta ratio between long and short options"""
        if abs(short_option.theta) == 0:
            return 0
        
        return abs(long_option.theta) / abs(short_option.theta)
    
    def _calculate_confidence(self, data: pd.DataFrame, position: Dict, 
                            theta_ratio: float) -> float:
        """Calculate signal confidence"""
        
        confidence = 0.5  # Base confidence
        
        # Theta ratio factor
        if theta_ratio > self.min_theta_ratio:
            confidence += 0.2
        elif theta_ratio > 1.0:
            confidence += 0.1
        
        # Trend alignment factor
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            trend = (sma_20 - sma_50) / sma_50
            
            if self.direction == "bullish" and trend > 0.02:
                confidence += 0.15
            elif self.direction == "bearish" and trend < -0.02:
                confidence += 0.15
        
        # Volatility factor
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            volatility = atr / current_price
            if volatility > 0.02:  # Moderate volatility
                confidence += 0.1
        
        # Technical indicators
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if self.direction == "bullish" and rsi < 70:
                confidence += 0.1
            elif self.direction == "bearish" and rsi > 30:
                confidence += 0.1
        
        return min(0.95, confidence)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Diagonal Spread Strategy signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Check market conditions
        if not self.check_market_conditions(data, options_data):
            return None
        
        # Get options chains for different expirations
        short_options = self.options_service.get_liquid_options(symbol, min_volume=10, dte=self.short_dte)
        long_options = self.options_service.get_liquid_options(symbol, min_volume=10, dte=self.long_dte)
        
        if not short_options or not long_options:
            return None
        
        # Select diagonal strikes
        diagonal_options = self.select_diagonal_strikes(current_price, short_options, long_options)
        if not diagonal_options:
            return None
        
        long_option, short_option = diagonal_options
        
        # Calculate position metrics
        position = self.calculate_position_metrics(long_option, short_option, current_price)
        
        # Calculate theta ratio
        theta_ratio = self.calculate_theta_ratio(long_option, short_option)
        
        # Only trade if theta ratio is sufficient
        if theta_ratio < self.min_theta_ratio:
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, position, theta_ratio)
        
        # Only trade if confidence is sufficient
        if confidence < 0.6:
            return None
        
        # Generate signal
        action = f"DIAGONAL_SPREAD_{self.direction.upper()}"
        
        signal = TradeSignal(
            symbol=symbol,
            action=action,
            quantity=1,  # One diagonal spread position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'long_strike': long_option.strike,
                'short_strike': short_option.strike,
                'net_cost': position['net_cost'],
                'breakeven': position['breakeven'],
                'max_loss': position['max_loss'],
                'max_profit': position['max_profit'],
                'theta_ratio': theta_ratio,
                'total_delta': position['total_delta'],
                'total_gamma': position['total_gamma'],
                'total_theta': position['total_theta'],
                'total_vega': position['total_vega'],
                'signal_type': 'diagonal_spread',
                'direction': self.direction,
                'position_size': self.max_risk_per_trade / position['max_loss'] if position['max_loss'] > 0 else 0,
                'profit_target': position['max_profit'] * self.profit_target_pct if position['max_profit'] != float('inf') else position['net_cost'] * self.profit_target_pct,
                'stop_loss': position['max_loss'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"Diagonal spread signal: {symbol} {self.direction} (confidence: {confidence:.3f}, "
                   f"cost: ${position['net_cost']:.2f}, theta ratio: {theta_ratio:.2f})")
        
        return signal 