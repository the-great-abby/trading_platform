"""
Calendar Spread Options Strategy
===============================
A strategy that profits from time decay differences between expiration dates.
Ideal for neutral outlook with time decay advantage.
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

class CalendarSpreadStrategy(BaseStrategy):
    """
    Calendar Spread Options Strategy
    
    Features:
    - Profits from time decay differences
    - Neutral outlook with time advantage
    - Defined risk and reward
    - Multiple expiration management
    - Theta decay optimization
    - Automated strike and expiration selection
    """
    
    # Class attributes for fallback mechanism
    requires_options_data = True
    stock_fallback_strategy = None  # Will be set to RSI strategy by default
    
    def __init__(self, 
                 name: str = "CalendarSpread",
                 short_dte: int = 14,  # Short-term expiration
                 long_dte: int = 45,   # Long-term expiration
                 profit_target_pct: float = 0.7,  # 70% of max profit
                 stop_loss_pct: float = 1.5,  # 1.5x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_theta_ratio: float = 1.5,  # Minimum theta ratio between expirations
                 min_delta: float = 0.3,  # Minimum delta for strike selection
                 max_delta: float = 0.7,  # Maximum delta for strike selection
                 min_dte_spread: int = 21,  # Minimum days between expirations
                 config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.short_dte = short_dte
        self.long_dte = long_dte
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_theta_ratio = min_theta_ratio
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.min_dte_spread = min_dte_spread
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        
    def get_available_expirations(self, symbol: str) -> List[str]:
        """Get available expiration dates for calendar spread"""
        try:
            # Get options chain to extract expirations
            options_chain = self.options_service.get_liquid_options(symbol, min_volume=1)
            if not options_chain:
                return []
            
            # Extract unique expiration dates
            expirations = list(set([opt.expiration for opt in options_chain]))
            expirations.sort()
            
            return expirations
            
        except Exception as e:
            logger.error(f"Error getting expirations for {symbol}: {e}")
            return []
    
    def select_calendar_strikes(self, symbol: str, current_price: float, 
                              short_expiration: str, long_expiration: str,
                              options_chain: List[OptionContract]) -> Optional[Dict[str, float]]:
        """Select optimal strikes for calendar spread"""
        if not options_chain:
            return None
        
        # Filter options by expiration
        short_options = [opt for opt in options_chain if opt.expiration == short_expiration]
        long_options = [opt for opt in options_chain if opt.expiration == long_expiration]
        
        if not short_options or not long_options:
            return None
        
        # Find common strikes
        short_strikes = set(opt.strike for opt in short_options)
        long_strikes = set(opt.strike for opt in long_options)
        common_strikes = short_strikes.intersection(long_strikes)
        
        if not common_strikes:
            return None
        
        # Score strikes based on delta and proximity to current price
        scored_strikes = []
        for strike in common_strikes:
            short_option = self._find_option_by_strike(strike, short_expiration, short_options)
            long_option = self._find_option_by_strike(strike, long_expiration, long_options)
            
            if short_option and long_option:
                score = self._calculate_strike_score(strike, current_price, short_option, long_option)
                scored_strikes.append((strike, score))
        
        if not scored_strikes:
            return None
        
        # Sort by score and return best
        scored_strikes.sort(key=lambda x: x[1], reverse=True)
        best_strike = scored_strikes[0][0]
        
        return {
            'strike': best_strike,
            'short_expiration': short_expiration,
            'long_expiration': long_expiration
        }
    
    def _find_option_by_strike(self, strike: float, expiration: str, 
                              options: List[OptionContract]) -> Optional[OptionContract]:
        """Find option by strike and expiration"""
        for option in options:
            if abs(option.strike - strike) < 0.01:
                return option
        return None
    
    def _calculate_strike_score(self, strike: float, current_price: float,
                              short_option: OptionContract, long_option: OptionContract) -> float:
        """Calculate score for strike selection"""
        score = 0.0
        
        # Delta score (prefer moderate delta)
        if short_option.delta and long_option.delta:
            avg_delta = (abs(short_option.delta) + abs(long_option.delta)) / 2
            if self.min_delta <= avg_delta <= self.max_delta:
                delta_score = 1.0 - abs(avg_delta - 0.5)  # Prefer 0.5 delta
                score += delta_score * 0.4
        
        # Proximity to current price (prefer ATM)
        price_distance = abs(strike - current_price) / current_price
        if price_distance < 0.05:  # Within 5% of current price
            score += (1.0 - price_distance) * 0.3
        
        # Theta ratio score
        if short_option.theta and long_option.theta:
            theta_ratio = abs(long_option.theta) / abs(short_option.theta)
            if theta_ratio >= self.min_theta_ratio:
                score += min(theta_ratio / 3.0, 1.0) * 0.3
        
        return score
    
    def calculate_calendar_metrics(self, strikes: Dict[str, float], 
                                 options_chain: List[OptionContract]) -> Dict[str, float]:
        """Calculate position metrics for calendar spread"""
        # Find options
        short_option = self._find_option_by_strike(
            strikes['strike'], strikes['short_expiration'], options_chain
        )
        long_option = self._find_option_by_strike(
            strikes['strike'], strikes['long_expiration'], options_chain
        )
        
        if not short_option or not long_option:
            return {}
        
        # Calendar spread: Sell short-term, Buy long-term
        net_debit = long_option.price - short_option.price
        max_loss = net_debit
        
        # Maximum profit occurs if short expires worthless and long retains value
        # This is simplified - would need proper options pricing model
        max_profit = short_option.price  # Simplified
        
        # Calculate probability of profit (simplified)
        prob_profit = 0.6  # Placeholder
        
        # Calculate theta advantage
        theta_advantage = 0.0
        if short_option.theta and long_option.theta:
            theta_advantage = abs(long_option.theta) - abs(short_option.theta)
        
        return {
            'net_debit': net_debit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'prob_profit': prob_profit,
            'theta_advantage': theta_advantage,
            'profit_ratio': max_profit / max_loss if max_loss > 0 else 0
        }
    
    def select_expiration_pair(self, symbol: str) -> Optional[Tuple[str, str]]:
        """Select optimal expiration pair for calendar spread"""
        expirations = self.get_available_expirations(symbol)
        
        if len(expirations) < 2:
            return None
        
        # Convert to datetime objects for comparison
        expiration_dates = []
        for exp in expirations:
            try:
                exp_date = datetime.strptime(exp, '%Y-%m-%d')
                expiration_dates.append((exp, exp_date))
            except ValueError:
                continue
        
        if len(expiration_dates) < 2:
            return None
        
        # Sort by date
        expiration_dates.sort(key=lambda x: x[1])
        
        # Find suitable pairs
        suitable_pairs = []
        for i in range(len(expiration_dates) - 1):
            short_exp, short_date = expiration_dates[i]
            long_exp, long_date = expiration_dates[i + 1]
            
            days_diff = (long_date - short_date).days
            
            if days_diff >= self.min_dte_spread:
                # Check if dates are reasonable
                current_date = datetime.now()
                short_days_to_exp = (short_date - current_date).days
                long_days_to_exp = (long_date - current_date).days
                
                if (self.short_dte * 0.5 <= short_days_to_exp <= self.short_dte * 1.5 and
                    self.long_dte * 0.5 <= long_days_to_exp <= self.long_dte * 1.5):
                    suitable_pairs.append((short_exp, long_exp, days_diff))
        
        if not suitable_pairs:
            return None
        
        # Sort by days difference (prefer moderate spread)
        suitable_pairs.sort(key=lambda x: abs(x[2] - (self.long_dte - self.short_dte)))
        
        return suitable_pairs[0][:2]
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for calendar spread"""
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check volatility (prefer moderate volatility)
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            volatility = atr / current_price
            if volatility < 0.015 or volatility > 0.06:  # 1.5-6% daily volatility
                return False
        
        # Check trend (prefer neutral)
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            trend_strength = abs(sma_20 - sma_50) / sma_50
            
            # Avoid strong trends
            if trend_strength > 0.1:
                return False
        
        # Check options liquidity
        if not options_chain:
            return False
        
        liquid_options = [opt for opt in options_chain 
                         if opt.volume > 10 and opt.open_interest > 50]
        
        if len(liquid_options) < 10:
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Calendar Spread signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Check market conditions
        if not self.check_market_conditions(data, options_data or []):
            return None
        
        # Get options chain
        options_chain = self.options_service.get_liquid_options(symbol, min_volume=5)
        if not options_chain:
            return None
        
        # Select expiration pair
        expiration_pair = self.select_expiration_pair(symbol)
        if not expiration_pair:
            return None
        
        short_exp, long_exp = expiration_pair
        
        # Select strikes
        strikes = self.select_calendar_strikes(
            symbol, current_price, short_exp, long_exp, options_chain
        )
        if not strikes:
            return None
        
        # Calculate position metrics
        metrics = self.calculate_calendar_metrics(strikes, options_chain)
        if not metrics:
            return None
        
        # Check if trade meets criteria
        if metrics['profit_ratio'] < 0.2:  # At least 20% profit potential
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, strikes, metrics)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="CALENDAR_SPREAD",
            quantity=1,  # One calendar spread position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strike': strikes['strike'],
                'short_expiration': strikes['short_expiration'],
                'long_expiration': strikes['long_expiration'],
                'net_debit': metrics['net_debit'],
                'max_profit': metrics['max_profit'],
                'max_loss': metrics['max_loss'],
                'theta_advantage': metrics['theta_advantage'],
                'profit_ratio': metrics['profit_ratio'],
                'signal_type': 'calendar_spread',
                'position_size': self.max_risk_per_trade / metrics['max_loss'],
                'profit_target': metrics['max_profit'] * self.profit_target_pct,
                'stop_loss': metrics['max_profit'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"Calendar Spread signal: {symbol} {strikes['strike']} "
                   f"{strikes['short_expiration']}/{strikes['long_expiration']} "
                   f"(confidence: {confidence:.3f}, theta advantage: {metrics['theta_advantage']:.4f})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, strikes: Dict, 
                            metrics: Dict[str, float]) -> float:
        """Calculate confidence score for calendar spread signal"""
        confidence = 0.5  # Base confidence
        
        # Technical analysis factors
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if 40 <= rsi <= 60:  # Neutral RSI
                confidence += 0.1
        
        if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_Signal'].iloc[-1]
            if abs(macd - macd_signal) < 0.01:  # Neutral MACD
                confidence += 0.1
        
        # Position-specific factors
        if metrics['profit_ratio'] > 0.3:  # Good profit ratio
            confidence += 0.1
        
        if metrics['theta_advantage'] > 0:  # Positive theta advantage
            confidence += 0.1
        
        # Expiration spread factor
        short_date = datetime.strptime(strikes['short_expiration'], '%Y-%m-%d')
        long_date = datetime.strptime(strikes['long_expiration'], '%Y-%m-%d')
        days_spread = (long_date - short_date).days
        
        if 21 <= days_spread <= 45:  # Optimal spread
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "options_time_decay",
            "description": "Calendar spread strategy for time decay advantage",
            "parameters": {
                "short_dte": self.short_dte,
                "long_dte": self.long_dte,
                "profit_target_pct": self.profit_target_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "min_theta_ratio": self.min_theta_ratio
            },
            "active_positions": len(self.active_positions),
            "total_positions": len(self.position_history)
        }
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get position summary"""
        return {
            "active_positions": self.active_positions,
            "position_history": self.position_history,
            "total_pnl": sum(pos.get('pnl', 0) for pos in self.position_history),
            "win_rate": self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.position_history:
            return 0.0
        
        winning_trades = sum(1 for pos in self.position_history if pos.get('pnl', 0) > 0)
        return winning_trades / len(self.position_history) 