"""
Butterfly Spread Options Strategy
================================
A strategy that creates limited risk, limited reward positions with high probability of profit.
Ideal for neutral outlook with specific price targets.
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

class ButterflySpreadStrategy(BaseStrategy):
    """
    Butterfly Spread Options Strategy
    
    Features:
    - Limited risk, limited reward strategy
    - High probability of profit at expiration
    - Specific price targets (body of butterfly)
    - Neutral to slightly directional outlook
    - Defined risk and reward
    - Automated strike selection based on technical analysis
    """
    
    def __init__(self, 
                 name: str = "ButterflySpread",
                 days_to_expiration: int = 30,
                 profit_target_pct: float = 0.8,  # 80% of max profit
                 stop_loss_pct: float = 1.5,  # 1.5x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_width: float = 2.0,  # Minimum width between strikes
                 max_width: float = 10.0,  # Maximum width between strikes
                 min_dte: int = 21,
                 max_dte: int = 45):
        super().__init__(name)
        self.days_to_expiration = days_to_expiration
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_width = min_width
        self.max_width = max_width
        self.min_dte = min_dte
        self.max_dte = max_dte
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        
    def select_butterfly_strikes(self, symbol: str, current_price: float, 
                               options_chain: List[OptionContract]) -> Optional[Dict[str, float]]:
        """Select optimal strikes for butterfly spread"""
        if not options_chain:
            return None
        
        # Filter for calls only (we'll create call butterfly)
        call_options = [opt for opt in options_chain if opt.option_type == 'call']
        
        if len(call_options) < 3:
            return None
        
        # Get unique strikes
        strikes = sorted(list(set([opt.strike for opt in call_options])))
        
        if len(strikes) < 3:
            return None
        
        # Find suitable butterfly combinations
        butterfly_candidates = []
        
        for i in range(len(strikes) - 2):
            lower_strike = strikes[i]
            middle_strike = strikes[i + 1]
            upper_strike = strikes[i + 2]
            
            # Check width constraints
            width1 = middle_strike - lower_strike
            width2 = upper_strike - middle_strike
            
            if (self.min_width <= width1 <= self.max_width and 
                self.min_width <= width2 <= self.max_width and
                width1 == width2):  # Symmetric butterfly
                
                # Check if middle strike is close to current price
                price_distance = abs(middle_strike - current_price) / current_price
                if price_distance <= 0.05:  # Within 5% of current price
                    butterfly_candidates.append({
                        'lower_strike': lower_strike,
                        'middle_strike': middle_strike,
                        'upper_strike': upper_strike,
                        'width': width1,
                        'price_distance': price_distance
                    })
        
        if not butterfly_candidates:
            return None
        
        # Score candidates
        scored_candidates = []
        for candidate in butterfly_candidates:
            score = self._calculate_butterfly_score(candidate, current_price, options_chain)
            scored_candidates.append((candidate, score))
        
        # Sort by score and return best
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        if scored_candidates:
            best_candidate = scored_candidates[0][0]
            logger.info(f"Selected butterfly strikes: {best_candidate['lower_strike']}, "
                       f"{best_candidate['middle_strike']}, {best_candidate['upper_strike']}")
            return best_candidate
        
        return None
    
    def _calculate_butterfly_score(self, candidate: Dict, current_price: float, 
                                 options_chain: List[OptionContract]) -> float:
        """Calculate score for butterfly spread candidate"""
        score = 0.0
        
        # Price distance score (closer to current price is better)
        score += (1.0 - candidate['price_distance']) * 0.4
        
        # Width score (prefer moderate width)
        optimal_width = 5.0
        width_score = 1.0 - abs(candidate['width'] - optimal_width) / optimal_width
        score += width_score * 0.3
        
        # Liquidity score
        liquidity_score = self._calculate_liquidity_score(candidate, options_chain)
        score += liquidity_score * 0.3
        
        return score
    
    def _calculate_liquidity_score(self, candidate: Dict, options_chain: List[OptionContract]) -> float:
        """Calculate liquidity score for butterfly strikes"""
        strikes = [candidate['lower_strike'], candidate['middle_strike'], candidate['upper_strike']]
        
        total_volume = 0
        total_oi = 0
        count = 0
        
        for strike in strikes:
            for option in options_chain:
                if (option.option_type == 'call' and 
                    abs(option.strike - strike) < 0.01):
                    total_volume += option.volume or 0
                    total_oi += option.open_interest or 0
                    count += 1
                    break
        
        if count == 0:
            return 0.0
        
        avg_volume = total_volume / count
        avg_oi = total_oi / count
        
        # Normalize scores
        volume_score = min(avg_volume / 100, 1.0)
        oi_score = min(avg_oi / 500, 1.0)
        
        return (volume_score + oi_score) / 2
    
    def calculate_butterfly_metrics(self, strikes: Dict[str, float], 
                                  options_chain: List[OptionContract]) -> Dict[str, float]:
        """Calculate position metrics for butterfly spread"""
        # Find option prices
        lower_call = self._find_option_price(strikes['lower_strike'], 'call', options_chain)
        middle_call = self._find_option_price(strikes['middle_strike'], 'call', options_chain)
        upper_call = self._find_option_price(strikes['upper_strike'], 'call', options_chain)
        
        if not all([lower_call, middle_call, upper_call]):
            return {}
        
        # Butterfly spread: Buy 1 lower call, Sell 2 middle calls, Buy 1 upper call
        net_debit = lower_call + upper_call - (2 * middle_call)
        
        # Maximum profit occurs at middle strike
        max_profit = strikes['middle_strike'] - strikes['lower_strike'] - net_debit
        max_loss = net_debit
        
        # Calculate probability of profit (simplified)
        # This would be more sophisticated with proper options pricing
        prob_profit = 0.7  # Placeholder
        
        return {
            'net_debit': net_debit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'prob_profit': prob_profit,
            'breakeven_lower': strikes['lower_strike'] + net_debit,
            'breakeven_upper': strikes['upper_strike'] - net_debit,
            'profit_ratio': max_profit / max_loss if max_loss > 0 else 0
        }
    
    def _find_option_price(self, strike: float, option_type: str, 
                          options_chain: List[OptionContract]) -> Optional[float]:
        """Find option price for given strike and type"""
        for option in options_chain:
            if (option.option_type == option_type and 
                abs(option.strike - strike) < 0.01):
                return option.price
        return None
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for butterfly spread"""
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check volatility (prefer moderate volatility)
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            volatility = atr / current_price
            if volatility < 0.01 or volatility > 0.06:  # 1-6% daily volatility
                return False
        
        # Check trend (prefer neutral)
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            trend_strength = abs(sma_20 - sma_50) / sma_50
            
            # Avoid strong trends
            if trend_strength > 0.08:
                return False
        
        # Check options liquidity
        if not options_chain:
            return False
        
        liquid_calls = [opt for opt in options_chain 
                       if opt.option_type == 'call' and opt.volume > 10]
        
        if len(liquid_calls) < 5:
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Butterfly Spread signal"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Get options chain
        options_chain = self.options_service.get_liquid_options_with_historical_support(
            symbol, min_volume=5, historical_date=options_data.get('historical_date') if options_data else None
        )
        if not options_chain:
            return None
        
        # Check market conditions
        if not self.check_market_conditions(data, options_chain):
            return None
        
        # Select butterfly strikes
        butterfly_strikes = self.select_butterfly_strikes(symbol, current_price, options_chain)
        if not butterfly_strikes:
            return None
        
        # Create butterfly position
        position = self.calculate_butterfly_metrics(butterfly_strikes, options_chain)
        if not position:
            return None
        
        # Check if trade meets criteria
        if position['profit_ratio'] < 0.3:  # At least 30% profit potential
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(data, butterfly_strikes, position)
        
        # Only trade if confidence is sufficient
        if confidence < 0.6:
            return None
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="BUTTERFLY_SPREAD",
            quantity=1,  # One butterfly spread position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'lower_strike': butterfly_strikes['lower_strike'],
                'middle_strike': butterfly_strikes['middle_strike'],
                'upper_strike': butterfly_strikes['upper_strike'],
                'net_debit': position['net_debit'],
                'max_profit': position['max_profit'],
                'max_loss': position['max_loss'],
                'prob_profit': position['prob_profit'],
                'profit_ratio': position['profit_ratio'],
                'signal_type': 'butterfly_spread',
                'position_size': self.max_risk_per_trade / position['max_loss'],
                'profit_target': position['max_profit'] * self.profit_target_pct,
                'stop_loss': position['max_profit'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"Butterfly Spread signal: {symbol} {butterfly_strikes['lower_strike']}-"
                   f"{butterfly_strikes['middle_strike']}-{butterfly_strikes['upper_strike']} "
                   f"(confidence: {confidence:.3f}, profit ratio: {position['profit_ratio']:.2f})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, strikes: Dict, 
                            metrics: Dict[str, float]) -> float:
        """Calculate confidence score for butterfly spread signal"""
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
        if metrics['profit_ratio'] > 0.5:  # Good profit ratio
            confidence += 0.1
        
        if metrics['prob_profit'] > 0.6:  # High probability of profit
            confidence += 0.1
        
        # Price proximity to middle strike
        current_price = data['Close'].iloc[-1]
        middle_strike = strikes['middle_strike']
        price_distance = abs(current_price - middle_strike) / current_price
        
        if price_distance < 0.02:  # Very close to middle strike
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "options_limited_risk",
            "description": "Butterfly spread strategy for limited risk, high probability trades",
            "parameters": {
                "days_to_expiration": self.days_to_expiration,
                "profit_target_pct": self.profit_target_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "min_width": self.min_width,
                "max_width": self.max_width
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