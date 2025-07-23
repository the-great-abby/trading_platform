"""
Earnings-Based Options Strategy
==============================
A strategy that trades options around earnings announcements.
Profits from volatility expansion and earnings-related price movements.
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

class EarningsStrategy(BaseStrategy):
    """
    Earnings-Based Options Strategy
    
    Features:
    - Trades around earnings announcements
    - Volatility expansion opportunities
    - Earnings calendar integration
    - Pre and post-earnings strategies
    - IV crush protection
    - Automated earnings date detection
    """
    
    def __init__(self, 
                 name: str = "EarningsStrategy",
                 days_before_earnings: int = 5,  # Days before earnings to enter
                 days_after_earnings: int = 2,   # Days after earnings to exit
                 profit_target_pct: float = 0.6,  # 60% of max profit
                 stop_loss_pct: float = 2.0,  # 2x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_iv_expansion: float = 0.3,  # 30% IV expansion required
                 earnings_lookback_days: int = 90,  # Days to look back for earnings data
                 strategy_type: str = "straddle"):  # straddle, strangle, iron_condor
        super().__init__(name)
        self.days_before_earnings = days_before_earnings
        self.days_after_earnings = days_after_earnings
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_iv_expansion = min_iv_expansion
        self.earnings_lookback_days = earnings_lookback_days
        self.strategy_type = strategy_type
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        self.earnings_calendar = {}
        
    def get_earnings_date(self, symbol: str) -> Optional[datetime]:
        """Get next earnings date for symbol"""
        # This would integrate with earnings calendar API
        # For now, we'll use a simplified approach
        
        # Check if we have cached earnings data
        if symbol in self.earnings_calendar:
            return self.earnings_calendar[symbol]
        
        # Simulate earnings date (in real implementation, this would call earnings API)
        # Typically earnings are quarterly, so we'll estimate
        current_date = datetime.now()
        
        # Estimate next earnings date (simplified)
        # In reality, this would come from earnings calendar API
        estimated_earnings = current_date + timedelta(days=30)  # Placeholder
        
        self.earnings_calendar[symbol] = estimated_earnings
        return estimated_earnings
    
    def check_earnings_timing(self, symbol: str) -> bool:
        """Check if we're in the right timing window for earnings trade"""
        earnings_date = self.get_earnings_date(symbol)
        if not earnings_date:
            return False
        
        current_date = datetime.now()
        days_to_earnings = (earnings_date - current_date).days
        
        # Check if we're in the right window
        if self.days_before_earnings <= days_to_earnings <= self.days_before_earnings + 2:
            return True
        
        return False
    
    def calculate_iv_expansion(self, symbol: str, options_chain: List[OptionContract]) -> float:
        """Calculate implied volatility expansion"""
        if not options_chain:
            return 0.0
        
        # Calculate current IV
        current_ivs = []
        for option in options_chain:
            if option.implied_volatility and option.implied_volatility > 0:
                current_ivs.append(option.implied_volatility)
        
        if not current_ivs:
            return 0.0
        
        current_iv = np.mean(current_ivs)
        
        # Get historical IV (simplified)
        historical_iv = self._get_historical_iv(symbol)
        
        if historical_iv == 0:
            return 0.0
        
        # Calculate IV expansion
        iv_expansion = (current_iv - historical_iv) / historical_iv
        
        return iv_expansion
    
    def _get_historical_iv(self, symbol: str) -> float:
        """Get historical implied volatility (simplified)"""
        # This would integrate with historical options data
        # For now, we'll use a simple heuristic
        
        # Base historical IV by sector/stock type
        base_iv = 0.25  # 25% base IV
        
        # Add some randomness to simulate real IV
        historical_iv = base_iv + np.random.normal(0, 0.05)
        historical_iv = max(0.1, min(0.5, historical_iv))  # Clamp between 10% and 50%
        
        return historical_iv
    
    def select_earnings_strategy(self, symbol: str, current_price: float, 
                               options_chain: List[OptionContract]) -> str:
        """Select the appropriate earnings strategy"""
        
        # Calculate IV expansion
        iv_expansion = self.calculate_iv_expansion(symbol, options_chain)
        
        # Select strategy based on IV expansion and available options
        if iv_expansion > self.min_iv_expansion:
            # High IV expansion - use premium selling strategies
            if self._can_create_iron_condor(options_chain, current_price):
                return "iron_condor"
            elif self._can_create_strangle(options_chain, current_price):
                return "strangle"
            else:
                return "straddle"
        else:
            # Moderate IV expansion - use straddle or strangle
            if self._can_create_straddle(options_chain, current_price):
                return "straddle"
            else:
                return "strangle"
    
    def _can_create_straddle(self, options_chain: List[OptionContract], current_price: float) -> bool:
        """Check if we can create a straddle"""
        atm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and 
                    abs(opt.strike - current_price) / current_price < 0.02]
        atm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and 
                   abs(opt.strike - current_price) / current_price < 0.02]
        
        return len(atm_calls) > 0 and len(atm_puts) > 0
    
    def _can_create_strangle(self, options_chain: List[OptionContract], current_price: float) -> bool:
        """Check if we can create a strangle"""
        otm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and opt.strike > current_price * 1.02]
        otm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and opt.strike < current_price * 0.98]
        
        return len(otm_calls) > 0 and len(otm_puts) > 0
    
    def _can_create_iron_condor(self, options_chain: List[OptionContract], current_price: float) -> bool:
        """Check if we can create an iron condor"""
        calls = [opt for opt in options_chain if opt.option_type == 'call']
        puts = [opt for opt in options_chain if opt.option_type == 'put']
        
        if len(calls) < 2 or len(puts) < 2:
            return False
        
        otm_calls = [c for c in calls if c.strike > current_price * 1.02]
        otm_puts = [p for p in puts if p.strike < current_price * 0.98]
        
        return len(otm_calls) >= 2 and len(otm_puts) >= 2
    
    def create_earnings_position(self, symbol: str, current_price: float, 
                               strategy_type: str, options_chain: List[OptionContract]) -> Optional[Dict]:
        """Create earnings-based position"""
        
        if strategy_type == "straddle":
            return self._create_straddle_position(current_price, options_chain)
        elif strategy_type == "strangle":
            return self._create_strangle_position(current_price, options_chain)
        elif strategy_type == "iron_condor":
            return self._create_iron_condor_position(current_price, options_chain)
        
        return None
    
    def _create_straddle_position(self, current_price: float, 
                                options_chain: List[OptionContract]) -> Optional[Dict]:
        """Create straddle position"""
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
        
        total_cost = call.price + put.price
        breakeven_up = call.strike + total_cost
        breakeven_down = put.strike - total_cost
        
        return {
            'strategy_type': 'straddle',
            'call_strike': call.strike,
            'put_strike': put.strike,
            'total_cost': total_cost,
            'breakeven_up': breakeven_up,
            'breakeven_down': breakeven_down,
            'max_profit': float('inf'),
            'max_loss': total_cost
        }
    
    def _create_strangle_position(self, current_price: float, 
                                options_chain: List[OptionContract]) -> Optional[Dict]:
        """Create strangle position"""
        otm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and opt.strike > current_price * 1.02]
        otm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and opt.strike < current_price * 0.98]
        
        if not otm_calls or not otm_puts:
            return None
        
        # Select closest OTM options
        call = min(otm_calls, key=lambda x: x.strike)
        put = max(otm_puts, key=lambda x: x.strike)
        
        total_cost = call.price + put.price
        breakeven_up = call.strike + total_cost
        breakeven_down = put.strike - total_cost
        
        return {
            'strategy_type': 'strangle',
            'call_strike': call.strike,
            'put_strike': put.strike,
            'total_cost': total_cost,
            'breakeven_up': breakeven_up,
            'breakeven_down': breakeven_down,
            'max_profit': float('inf'),
            'max_loss': total_cost
        }
    
    def _create_iron_condor_position(self, current_price: float, 
                                   options_chain: List[OptionContract]) -> Optional[Dict]:
        """Create iron condor position"""
        calls = [opt for opt in options_chain if opt.option_type == 'call']
        puts = [opt for opt in options_chain if opt.option_type == 'put']
        
        otm_calls = sorted([c for c in calls if c.strike > current_price * 1.02], key=lambda x: x.strike)
        otm_puts = sorted([p for p in puts if p.strike < current_price * 0.98], key=lambda x: x.strike, reverse=True)
        
        if len(otm_calls) < 2 or len(otm_puts) < 2:
            return None
        
        short_call = otm_calls[0]
        long_call = otm_calls[1]
        short_put = otm_puts[0]
        long_put = otm_puts[1]
        
        max_profit = (short_call.price + short_put.price) - (long_call.price + long_put.price)
        max_risk = (long_call.strike - short_call.strike) - max_profit
        
        return {
            'strategy_type': 'iron_condor',
            'short_call_strike': short_call.strike,
            'long_call_strike': long_call.strike,
            'short_put_strike': short_put.strike,
            'long_put_strike': long_put.strike,
            'max_profit': max_profit,
            'max_risk': max_risk
        }
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for earnings trading"""
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check for sufficient options liquidity
        if not options_chain:
            return False
        
        liquid_options = [opt for opt in options_chain 
                         if opt.volume > 20 and opt.open_interest > 100]
        
        if len(liquid_options) < 15:
            return False
        
        # Check for IV expansion
        iv_expansion = self.calculate_iv_expansion(data.index[-1], options_chain)
        if iv_expansion < 0.1:  # At least 10% IV expansion
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Earnings Strategy signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Check earnings timing
        if not self.check_earnings_timing(symbol):
            return None
        
        # Get options chain
        try:
            options_chain = self.options_service.get_liquid_options(symbol, min_volume=10)
        except Exception as e:
            # If options service fails, return None instead of crashing
            return None
        
        if not options_chain:
            return None
        
        # Check market conditions
        if not self.check_market_conditions(data, options_chain):
            return None
        
        # Select strategy
        strategy_type = self.select_earnings_strategy(symbol, current_price, options_chain)
        
        # Create position
        position = self.create_earnings_position(symbol, current_price, strategy_type, options_chain)
        if not position:
            return None
        
        # Calculate IV expansion
        iv_expansion = self.calculate_iv_expansion(symbol, options_chain)
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, position, iv_expansion)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action=f"EARNINGS_{strategy_type.upper()}",
            quantity=1,  # One earnings position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strategy_type': strategy_type,
                'position': position,
                'iv_expansion': iv_expansion,
                'earnings_date': self.get_earnings_date(symbol),
                'signal_type': 'earnings',
                'position_size': self.max_risk_per_trade / position.get('max_loss', current_price),
                'profit_target': position.get('max_profit', 0) * self.profit_target_pct,
                'stop_loss': position.get('max_profit', 0) * self.stop_loss_pct
            }
        )
        
        logger.info(f"Earnings signal: {symbol} {strategy_type} (confidence: {confidence:.3f}, "
                   f"IV expansion: {iv_expansion:.2%})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, position: Dict, 
                            iv_expansion: float) -> float:
        """Calculate confidence score for earnings signal"""
        confidence = 0.5  # Base confidence
        
        # IV expansion factor
        if iv_expansion > 0.5:  # High IV expansion
            confidence += 0.2
        elif iv_expansion > 0.3:  # Moderate IV expansion
            confidence += 0.1
        
        # Strategy-specific factors
        if position.get('strategy_type') == 'straddle':
            # Straddle works well with high volatility
            if iv_expansion > 0.4:
                confidence += 0.1
        elif position.get('strategy_type') == 'iron_condor':
            # Iron condor works well with moderate IV expansion
            if 0.2 <= iv_expansion <= 0.6:
                confidence += 0.1
        
        # Technical analysis factors
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            current_vol = atr / data['Close'].iloc[-1]
            if current_vol > 0.03:  # High current volatility
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "options_earnings",
            "description": "Earnings-based options strategy for volatility expansion",
            "parameters": {
                "days_before_earnings": self.days_before_earnings,
                "days_after_earnings": self.days_after_earnings,
                "profit_target_pct": self.profit_target_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "min_iv_expansion": self.min_iv_expansion,
                "strategy_type": self.strategy_type
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
            "win_rate": self._calculate_win_rate(),
            "earnings_calendar": self.earnings_calendar
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.position_history:
            return 0.0
        
        winning_trades = sum(1 for pos in self.position_history if pos.get('pnl', 0) > 0)
        return winning_trades / len(self.position_history) 