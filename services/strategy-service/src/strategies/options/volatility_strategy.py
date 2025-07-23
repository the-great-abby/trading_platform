"""
Volatility-Based Options Strategy
================================
A strategy that trades options based on implied vs historical volatility.
Profits from volatility mean reversion and volatility expansion opportunities.
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

class VolatilityStrategy(BaseStrategy):
    """
    Volatility-Based Options Strategy
    
    Features:
    - Trades based on implied vs historical volatility
    - Mean reversion in volatility
    - Volatility expansion opportunities
    - Dynamic strategy selection (straddle, strangle, iron condor)
    - Risk management with volatility-based position sizing
    - Earnings and event-driven volatility trading
    """
    
    def __init__(self, 
                 name: str = "VolatilityStrategy",
                 volatility_threshold: float = 0.2,  # 20% volatility threshold
                 iv_percentile_threshold: float = 0.7,  # 70th percentile for high IV
                 iv_percentile_low: float = 0.3,  # 30th percentile for low IV
                 profit_target_pct: float = 0.6,  # 60% of max profit
                 stop_loss_pct: float = 2.0,  # 2x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_dte: int = 14,
                 max_dte: int = 45,
                 earnings_lookback_days: int = 30):
        super().__init__(name)
        self.volatility_threshold = volatility_threshold
        self.iv_percentile_threshold = iv_percentile_threshold
        self.iv_percentile_low = iv_percentile_low
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_dte = min_dte
        self.max_dte = max_dte
        self.earnings_lookback_days = earnings_lookback_days
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        self.volatility_history = {}
        
    def calculate_historical_volatility(self, data: pd.DataFrame, window: int = 20) -> float:
        """Calculate historical volatility from price data"""
        if len(data) < window + 1:
            return 0.0
        
        # Calculate daily returns
        returns = data['Close'].pct_change().dropna()
        
        if len(returns) < window:
            return 0.0
        
        # Calculate rolling volatility
        volatility = returns.rolling(window=window).std().iloc[-1]
        
        # Convert to annualized volatility (assuming daily data)
        annualized_vol = float(volatility * (252 ** 0.5))
        
        return annualized_vol
    
    def calculate_implied_volatility_percentile(self, symbol: str, options_chain: List[OptionContract]) -> float:
        """Calculate implied volatility percentile"""
        if not options_chain:
            return 0.5  # Default to 50th percentile
        
        # Extract implied volatilities
        ivs = []
        for option in options_chain:
            if option.implied_volatility and option.implied_volatility > 0:
                ivs.append(option.implied_volatility)
        
        if not ivs:
            return 0.5
        
        # Calculate current IV
        current_iv = np.mean(ivs)
        
        # Get historical IV data (simplified - would use real historical data)
        # For now, we'll use a simple heuristic
        historical_ivs = self._get_historical_ivs(symbol)
        
        if not historical_ivs:
            return 0.5
        
        # Calculate percentile
        percentile = np.sum(np.array(historical_ivs) < current_iv) / len(historical_ivs)
        
        return percentile
    
    def _get_historical_ivs(self, symbol: str) -> List[float]:
        """Get historical implied volatilities (simplified)"""
        # This would integrate with your historical options data
        # For now, we'll use a simple range
        base_iv = 0.25  # 25% base IV
        iv_range = 0.15  # ±15% range
        
        # Generate synthetic historical IVs
        historical_ivs = []
        for i in range(252):  # One year of trading days
            # Add some randomness to simulate real IV movement
            iv = base_iv + np.random.normal(0, iv_range/3)
            iv = max(0.05, min(0.8, iv))  # Clamp between 5% and 80%
            historical_ivs.append(iv)
        
        return historical_ivs
    
    def select_volatility_strategy(self, current_price: float, historical_vol: float, 
                                 iv_percentile: float, options_chain: List[OptionContract]) -> str:
        """Select the appropriate volatility strategy"""
        
        if iv_percentile > self.iv_percentile_threshold:
            # High IV - sell premium (iron condor, strangle)
            if self._can_create_iron_condor(options_chain, current_price):
                return "iron_condor"
            else:
                return "strangle"
        
        elif iv_percentile < self.iv_percentile_low:
            # Low IV - buy premium (straddle, long strangle)
            if self._can_create_straddle(options_chain, current_price):
                return "straddle"
            else:
                return "long_strangle"
        
        else:
            # Moderate IV - neutral strategies
            return "calendar_spread"
    
    def _can_create_iron_condor(self, options_chain: List[OptionContract], current_price: float) -> bool:
        """Check if we can create an iron condor"""
        calls = [opt for opt in options_chain if opt.option_type == 'call']
        puts = [opt for opt in options_chain if opt.option_type == 'put']
        
        # Need at least 2 calls and 2 puts
        if len(calls) < 2 or len(puts) < 2:
            return False
        
        # Check for suitable strikes
        otm_calls = [c for c in calls if c.strike > current_price * 1.02]
        otm_puts = [p for p in puts if p.strike < current_price * 0.98]
        
        return len(otm_calls) >= 2 and len(otm_puts) >= 2
    
    def _can_create_straddle(self, options_chain: List[OptionContract], current_price: float) -> bool:
        """Check if we can create a straddle"""
        atm_calls = [opt for opt in options_chain 
                    if opt.option_type == 'call' and 
                    abs(opt.strike - current_price) / current_price < 0.02]
        atm_puts = [opt for opt in options_chain 
                   if opt.option_type == 'put' and 
                   abs(opt.strike - current_price) / current_price < 0.02]
        
        return len(atm_calls) > 0 and len(atm_puts) > 0
    
    def create_iron_condor_position(self, symbol: str, current_price: float, 
                                  options_chain: List[OptionContract]) -> Optional[Dict]:
        """Create iron condor position"""
        calls = [opt for opt in options_chain if opt.option_type == 'call']
        puts = [opt for opt in options_chain if opt.option_type == 'put']
        
        # Find suitable strikes
        otm_calls = sorted([c for c in calls if c.strike > current_price * 1.02], key=lambda x: x.strike)
        otm_puts = sorted([p for p in puts if p.strike < current_price * 0.98], key=lambda x: x.strike, reverse=True)
        
        if len(otm_calls) < 2 or len(otm_puts) < 2:
            return None
        
        # Select strikes
        short_call = otm_calls[0]  # Closest OTM call
        long_call = otm_calls[1]   # Further OTM call
        short_put = otm_puts[0]    # Closest OTM put
        long_put = otm_puts[1]     # Further OTM put
        
        # Calculate position metrics
        max_profit = (short_call.price + short_put.price) - (long_call.price + long_put.price)
        max_risk = (long_call.strike - short_call.strike) - max_profit
        
        return {
            'strategy_type': 'iron_condor',
            'short_call_strike': short_call.strike,
            'long_call_strike': long_call.strike,
            'short_put_strike': short_put.strike,
            'long_put_strike': long_put.strike,
            'max_profit': max_profit,
            'max_risk': max_risk,
            'probability': 0.7  # Simplified
        }
    
    def create_straddle_position(self, symbol: str, current_price: float, 
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
        
        # Calculate position metrics
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
            'max_profit': float('inf'),  # Unlimited upside
            'max_loss': total_cost
        }
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for volatility trading"""
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check for sufficient options liquidity
        if not options_chain:
            return False
        
        liquid_options = [opt for opt in options_chain 
                         if opt.volume > 10 and opt.open_interest > 50]
        
        if len(liquid_options) < 10:
            return False
        
        # Check for earnings or events (simplified)
        # This would integrate with earnings calendar
        current_date = data.index[-1]
        if hasattr(current_date, 'to_pydatetime'):
            current_date = current_date.to_pydatetime()
        days_to_earnings = self._get_days_to_earnings(current_date)
        
        # Avoid trading too close to earnings
        if days_to_earnings and days_to_earnings < 5:
            return False
        
        return True
    
    def _get_days_to_earnings(self, current_date: datetime) -> Optional[int]:
        """Get days to next earnings (simplified)"""
        # This would integrate with earnings calendar
        # For now, return None (no earnings soon)
        return None
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate Volatility Strategy signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Get options chain - handle the case where we don't have options data
        try:
            options_chain = self.options_service.get_liquid_options_with_historical_support(
                symbol, min_volume=5, historical_date=historical_date
            )
        except Exception as e:
            # If options service fails, return None instead of crashing
            return None
        
        if not options_chain:
            return None
        
        # Check market conditions
        if not self.check_market_conditions(data, options_chain):
            return None
        
        # Calculate volatilities
        historical_vol = self.calculate_historical_volatility(data)
        iv_percentile = self.calculate_implied_volatility_percentile(symbol, options_chain)
        
        # Select strategy
        strategy_type = self.select_volatility_strategy(
            current_price, historical_vol, iv_percentile, options_chain
        )
        
        # Create position
        position = None
        if strategy_type == "iron_condor":
            position = self.create_iron_condor_position(symbol, current_price, options_chain)
        elif strategy_type == "straddle":
            position = self.create_straddle_position(symbol, current_price, options_chain)
        
        if not position:
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, historical_vol, iv_percentile, position)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action=f"VOLATILITY_{strategy_type.upper()}",
            quantity=1,  # One volatility position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strategy_type': strategy_type,
                'historical_vol': historical_vol,
                'iv_percentile': iv_percentile,
                'position': position,
                'signal_type': 'volatility',
                'position_size': self.max_risk_per_trade / position.get('max_risk', current_price),
                'profit_target': position.get('max_profit', 0) * self.profit_target_pct,
                'stop_loss': position.get('max_profit', 0) * self.stop_loss_pct
            }
        )
        
        logger.info(f"Volatility signal: {symbol} {strategy_type} (confidence: {confidence:.3f}, "
                   f"IV percentile: {iv_percentile:.2%})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, historical_vol: float, 
                            iv_percentile: float, position: Dict) -> float:
        """Calculate confidence score for volatility signal"""
        confidence = 0.5  # Base confidence
        
        # Volatility factors
        if iv_percentile > 0.8:  # Very high IV
            confidence += 0.2
        elif iv_percentile < 0.2:  # Very low IV
            confidence += 0.2
        
        # Historical volatility factor
        if historical_vol > 0.3:  # High historical volatility
            confidence += 0.1
        
        # Technical analysis factors
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            current_vol = atr / data['Close'].iloc[-1]
            if current_vol > 0.02:  # High current volatility
                confidence += 0.1
        
        # Position-specific factors
        if position.get('strategy_type') == 'iron_condor':
            if position.get('probability', 0) > 0.6:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "options_volatility",
            "description": "Volatility-based options strategy for mean reversion and expansion",
            "parameters": {
                "volatility_threshold": self.volatility_threshold,
                "iv_percentile_threshold": self.iv_percentile_threshold,
                "iv_percentile_low": self.iv_percentile_low,
                "profit_target_pct": self.profit_target_pct,
                "stop_loss_pct": self.stop_loss_pct
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
            "volatility_history": self.volatility_history
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.position_history:
            return 0.0
        
        winning_trades = sum(1 for pos in self.position_history if pos.get('pnl', 0) > 0)
        return winning_trades / len(self.position_history) 