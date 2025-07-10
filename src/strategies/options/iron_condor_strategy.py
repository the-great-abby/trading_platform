"""
Iron Condor Options Strategy
============================
A strategy that sells out-of-the-money calls and puts to profit from low volatility environments.
Defined risk and reward with high probability of profit in sideways markets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class IronCondorStrategy(BaseStrategy):
    """
    Iron Condor Options Strategy
    
    Features:
    - Sells out-of-the-money calls and puts
    - Profits from low volatility environments
    - Defined risk and reward
    - High probability of profit in sideways markets
    - Dynamic strike selection based on volatility
    """
    
    def __init__(self, 
                 name: str = "IronCondor",
                 days_to_expiration: int = 45,
                 profit_target_pct: float = 0.5,  # 50% of max profit
                 stop_loss_pct: float = 2.0,  # 2x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 volatility_threshold: float = 0.3,  # 30% IV threshold
                 min_dte: int = 30,
                 max_dte: int = 60):
        super().__init__(name)
        self.days_to_expiration = days_to_expiration
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.volatility_threshold = volatility_threshold
        self.min_dte = min_dte
        self.max_dte = max_dte
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        
    def calculate_implied_volatility(self, options_data: Dict[str, Any]) -> float:
        """Calculate implied volatility from options data"""
        if not options_data or 'implied_volatility' not in options_data:
            return 0.0
        
        return options_data['implied_volatility']
    
    def select_strikes(self, current_price: float, options_data: Dict[str, Any]) -> Dict[str, float]:
        """Select strikes for Iron Condor based on current price and volatility"""
        
        # Calculate standard deviation for strike selection
        iv = self.calculate_implied_volatility(options_data)
        if iv == 0:
            iv = 0.3  # Default IV if not available
        
        # Calculate expected move
        expected_move = current_price * iv * np.sqrt(self.days_to_expiration / 365)
        
        # Select strikes based on expected move
        # Sell put spread: 1/3 of expected move below current price
        put_strike_distance = expected_move / 3
        put_strike = current_price - put_strike_distance
        
        # Sell call spread: 1/3 of expected move above current price
        call_strike_distance = expected_move / 3
        call_strike = current_price + call_strike_distance
        
        # Round strikes to nearest standard increment
        put_strike = self._round_to_strike_increment(put_strike)
        call_strike = self._round_to_strike_increment(call_strike)
        
        # Calculate spread width (typically 2-5 points)
        spread_width = max(2, min(5, expected_move / 4))
        
        return {
            'put_strike': put_strike,
            'call_strike': call_strike,
            'put_spread_width': spread_width,
            'call_spread_width': spread_width,
            'expected_move': expected_move,
            'implied_volatility': iv
        }
    
    def _round_to_strike_increment(self, strike: float) -> float:
        """Round strike to nearest standard increment"""
        if strike < 50:
            increment = 0.5
        elif strike < 100:
            increment = 1.0
        elif strike < 200:
            increment = 2.5
        else:
            increment = 5.0
        
        return round(strike / increment) * increment
    
    def calculate_max_risk(self, strikes: Dict[str, float]) -> float:
        """Calculate maximum risk for Iron Condor position"""
        put_spread_width = strikes['put_spread_width']
        call_spread_width = strikes['call_spread_width']
        
        # Max risk is the width of the wider spread
        max_risk = max(put_spread_width, call_spread_width)
        return max_risk
    
    def calculate_max_profit(self, strikes: Dict[str, float]) -> float:
        """Calculate maximum profit for Iron Condor position"""
        put_spread_width = strikes['put_spread_width']
        call_spread_width = strikes['call_spread_width']
        
        # Max profit is the width of the narrower spread
        max_profit = min(put_spread_width, call_spread_width)
        return max_profit
    
    def check_market_conditions(self, data: pd.DataFrame, options_data: Dict[str, Any]) -> bool:
        """Check if market conditions are suitable for Iron Condor"""
        
        if len(data) < 20:
            return False
        
        # Check volatility
        iv = self.calculate_implied_volatility(options_data)
        if iv < self.volatility_threshold:
            return False
        
        # Check for strong trending market (avoid in strong trends)
        price_change_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        if abs(price_change_20d) > 0.1:  # More than 10% move in 20 days
            return False
        
        # Check for high volatility period
        volatility_20d = data['Close'].pct_change().rolling(20).std().iloc[-1]
        if volatility_20d > 0.03:  # More than 3% daily volatility
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Iron Condor signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Check market conditions
        if not self.check_market_conditions(data, options_data or {}):
            return None
        
        # Select strikes
        strikes = self.select_strikes(current_price, options_data or {})
        
        # Calculate risk/reward
        max_risk = self.calculate_max_risk(strikes)
        max_profit = self.calculate_max_profit(strikes)
        risk_reward_ratio = max_profit / max_risk if max_risk > 0 else 0
        
        # Only trade if risk/reward is acceptable
        if risk_reward_ratio < 0.3:  # At least 30% profit potential
            return None
        
        # Calculate confidence based on market conditions
        confidence = self._calculate_confidence(data, options_data or {}, strikes)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="IRON_CONDOR",
            quantity=1,  # One Iron Condor position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strikes': strikes,
                'max_risk': max_risk,
                'max_profit': max_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'days_to_expiration': self.days_to_expiration,
                'signal_type': 'iron_condor',
                'position_size': self.max_risk_per_trade / max_risk if max_risk > 0 else 0,
                'profit_target': max_profit * self.profit_target_pct,
                'stop_loss': max_risk * self.stop_loss_pct
            }
        )
        
        logger.info(f"Iron Condor signal: {symbol} (confidence: {confidence:.3f}, "
                   f"risk/reward: {risk_reward_ratio:.3f})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, options_data: Dict[str, Any], 
                            strikes: Dict[str, float]) -> float:
        """Calculate confidence for Iron Condor position"""
        
        confidence = 0.5  # Base confidence
        
        # Volatility factor
        iv = self.calculate_implied_volatility(options_data)
        if 0.2 <= iv <= 0.4:  # Optimal IV range
            confidence += 0.2
        elif iv > 0.4:
            confidence -= 0.1
        
        # Market trend factor
        price_change_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        if abs(price_change_20d) < 0.05:  # Low trend
            confidence += 0.2
        elif abs(price_change_20d) > 0.15:  # High trend
            confidence -= 0.3
        
        # Risk/reward factor
        max_risk = self.calculate_max_risk(strikes)
        max_profit = self.calculate_max_profit(strikes)
        risk_reward_ratio = max_profit / max_risk if max_risk > 0 else 0
        
        if risk_reward_ratio > 0.5:
            confidence += 0.1
        elif risk_reward_ratio < 0.2:
            confidence -= 0.2
        
        # Time to expiration factor
        if self.min_dte <= self.days_to_expiration <= self.max_dte:
            confidence += 0.1
        
        return min(max(confidence, 0.1), 0.9)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "days_to_expiration": self.days_to_expiration,
            "profit_target_pct": self.profit_target_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "max_risk_per_trade": self.max_risk_per_trade,
            "volatility_threshold": self.volatility_threshold,
            "active_positions": len(self.active_positions)
        }
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of active positions"""
        if not self.active_positions:
            return {"message": "No active positions"}
        
        total_positions = len(self.active_positions)
        total_max_risk = sum(pos.get('max_risk', 0) for pos in self.active_positions.values())
        total_max_profit = sum(pos.get('max_profit', 0) for pos in self.active_positions.values())
        
        return {
            "total_positions": total_positions,
            "total_max_risk": total_max_risk,
            "total_max_profit": total_max_profit,
            "average_risk_reward": total_max_profit / total_max_risk if total_max_risk > 0 else 0
        } 