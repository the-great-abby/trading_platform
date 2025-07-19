"""
Straddle Options Strategy
=========================
A strategy that buys both call and put options at the same strike price.
Ideal for high volatility expectations and earnings events.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.options_data_service import OptionsDataService, OptionContract

logger = get_trading_logger()

class StraddleStrategy(BaseStrategy):
    """
    Straddle Options Strategy
    
    Features:
    - Long straddle for volatility expansion
    - Earnings event trading
    - High volatility expectations
    - Unlimited profit potential
    - Defined maximum loss
    - Automated strike selection
    """
    
    def __init__(self, 
                 name: str = "Straddle",
                 days_to_expiration: int = 30,
                 profit_target_pct: float = 0.6,  # 60% of max profit
                 stop_loss_pct: float = 2.0,  # 2x max loss
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_iv_percentile: float = 0.4,  # Minimum IV percentile
                 max_iv_percentile: float = 0.8,  # Maximum IV percentile
                 min_delta: float = 0.4,  # Minimum delta for ATM selection
                 max_delta: float = 0.6,  # Maximum delta for ATM selection
                 earnings_days_before: int = 5,  # Days before earnings
                 earnings_days_after: int = 2):  # Days after earnings
        super().__init__(name)
        self.days_to_expiration = days_to_expiration
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_iv_percentile = min_iv_percentile
        self.max_iv_percentile = max_iv_percentile
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.earnings_days_before = earnings_days_before
        self.earnings_days_after = earnings_days_after
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
    
    def check_market_conditions(self, data: pd.DataFrame, options_data: Optional[Dict] = None) -> bool:
        """Check if market conditions are suitable for straddle strategy"""
        
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check volatility conditions
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            volatility = atr / current_price
            if volatility < 0.02:  # Less than 2% daily volatility
                return False
        
        # Check options data availability
        if not options_data:
            return False
        
        # Check IV percentile
        iv_percentile = options_data.get('iv_percentile', 0.5)
        if iv_percentile < self.min_iv_percentile or iv_percentile > self.max_iv_percentile:
            return False
        
        return True
    
    def select_atm_strikes(self, current_price: float, options_chain: List[OptionContract]) -> Optional[Tuple[OptionContract, OptionContract]]:
        """Select at-the-money call and put options"""
        
        # Find ATM options
        atm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and 
                    abs(opt.strike - current_price) / current_price < 0.02]
        atm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and 
                   abs(opt.strike - current_price) / current_price < 0.02]
        
        if not atm_calls or not atm_puts:
            return None
        
        # Select closest to ATM
        call = min(atm_calls, key=lambda x: abs(x.strike - current_price))
        put = min(atm_puts, key=lambda x: abs(x.strike - current_price))
        
        # Verify delta requirements
        if not (self.min_delta <= abs(call.delta) <= self.max_delta and 
                self.min_delta <= abs(put.delta) <= self.max_delta):
            return None
        
        return call, put
    
    def calculate_position_metrics(self, call: OptionContract, put: OptionContract, 
                                 current_price: float) -> Dict[str, Any]:
        """Calculate straddle position metrics"""
        
        total_cost = call.price + put.price
        breakeven_up = call.strike + total_cost
        breakeven_down = put.strike - total_cost
        
        # Calculate Greeks
        total_delta = call.delta + put.delta
        total_gamma = call.gamma + put.gamma
        total_theta = call.theta + put.theta
        total_vega = call.vega + put.vega
        
        return {
            'total_cost': total_cost,
            'breakeven_up': breakeven_up,
            'breakeven_down': breakeven_down,
            'max_loss': total_cost,
            'max_profit': float('inf'),
            'total_delta': total_delta,
            'total_gamma': total_gamma,
            'total_theta': total_theta,
            'total_vega': total_vega,
            'call_strike': call.strike,
            'put_strike': put.strike,
            'call_price': call.price,
            'put_price': put.price
        }
    
    def check_earnings_timing(self, symbol: str) -> bool:
        """Check if we're in the right timing window for earnings trade"""
        # This would integrate with earnings calendar
        # For now, simulate earnings timing
        return random.random() < 0.1  # 10% chance of earnings timing
    
    def calculate_iv_expansion(self, symbol: str, options_chain: List[OptionContract]) -> float:
        """Calculate implied volatility expansion"""
        if not options_chain:
            return 0.0
        
        # Calculate average IV
        avg_iv = np.mean([opt.implied_volatility for opt in options_chain if opt.implied_volatility > 0])
        
        # Compare with historical volatility (simplified)
        historical_vol = 0.25  # Simplified historical volatility
        iv_expansion = (avg_iv - historical_vol) / historical_vol
        
        return max(0.0, iv_expansion)
    
    def _calculate_confidence(self, data: pd.DataFrame, position: Dict, 
                            iv_expansion: float) -> float:
        """Calculate signal confidence"""
        
        confidence = 0.5  # Base confidence
        
        # IV expansion factor
        if iv_expansion > 0.3:
            confidence += 0.2
        elif iv_expansion > 0.1:
            confidence += 0.1
        
        # Volatility factor
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            volatility = atr / current_price
            if volatility > 0.03:  # High volatility
                confidence += 0.15
        
        # Technical indicators
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if 40 <= rsi <= 60:  # Neutral RSI
                confidence += 0.1
        
        # Volume factor
        if 'Volume' in data.columns:
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            if current_volume > avg_volume * 1.5:  # High volume
                confidence += 0.05
        
        return min(0.95, confidence)
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Straddle Strategy signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Check market conditions
        if not self.check_market_conditions(data, options_data):
            return None
        
        # Check earnings timing
        if not self.check_earnings_timing(symbol):
            return None
        
        # Get options chain
        options_chain = self.options_service.get_liquid_options(symbol, min_volume=10)
        if not options_chain:
            return None
        
        # Select ATM strikes
        atm_options = self.select_atm_strikes(current_price, options_chain)
        if not atm_options:
            return None
        
        call, put = atm_options
        
        # Calculate position metrics
        position = self.calculate_position_metrics(call, put, current_price)
        
        # Calculate IV expansion
        iv_expansion = self.calculate_iv_expansion(symbol, options_chain)
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, position, iv_expansion)
        
        # Only trade if confidence is sufficient
        if confidence < 0.6:
            return None
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="STRADDLE",
            quantity=1,  # One straddle position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'call_strike': call.strike,
                'put_strike': put.strike,
                'total_cost': position['total_cost'],
                'breakeven_up': position['breakeven_up'],
                'breakeven_down': position['breakeven_down'],
                'max_loss': position['max_loss'],
                'iv_expansion': iv_expansion,
                'total_delta': position['total_delta'],
                'total_gamma': position['total_gamma'],
                'total_theta': position['total_theta'],
                'total_vega': position['total_vega'],
                'signal_type': 'straddle',
                'position_size': self.max_risk_per_trade / position['max_loss'] if position['max_loss'] > 0 else 0,
                'profit_target': position['max_loss'] * self.profit_target_pct,
                'stop_loss': position['max_loss'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"Straddle signal: {symbol} (confidence: {confidence:.3f}, "
                   f"cost: ${position['total_cost']:.2f}, IV expansion: {iv_expansion:.1%})")
        
        return signal 