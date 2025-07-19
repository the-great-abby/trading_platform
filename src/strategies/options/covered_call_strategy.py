"""
Covered Call Options Strategy
============================
A strategy that sells call options against owned stock to generate income.
Automated with dynamic strike selection and risk management.
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

class CoveredCallStrategy(BaseStrategy):
    """
    Covered Call Options Strategy
    
    Features:
    - Sells call options against owned stock
    - Generates income from premium collection
    - Dynamic strike selection based on technical analysis
    - Risk management with stop-loss and profit targets
    - Automated expiration selection
    - Portfolio integration for stock ownership tracking
    """
    
    def __init__(self, 
                 name: str = "CoveredCall",
                 days_to_expiration: int = 30,
                 profit_target_pct: float = 0.7,  # 70% of max profit
                 stop_loss_pct: float = 1.5,  # 1.5x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 min_delta: float = 0.3,  # Minimum delta for strike selection
                 max_delta: float = 0.7,  # Maximum delta for strike selection
                 min_premium_pct: float = 0.02,  # 2% minimum premium relative to stock price
                 min_dte: int = 21,
                 max_dte: int = 45):
        super().__init__(name)
        self.days_to_expiration = days_to_expiration
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.min_premium_pct = min_premium_pct
        self.min_dte = min_dte
        self.max_dte = max_dte
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        
    def check_stock_ownership(self, symbol: str, portfolio_value: float) -> bool:
        """Check if we own the stock for covered call strategy"""
        # This would integrate with your portfolio management system
        # For now, we'll assume we can buy the stock if needed
        return True
    
    def select_optimal_strike(self, symbol: str, current_price: float, 
                            options_chain: List[OptionContract]) -> Optional[float]:
        """Select optimal strike price for covered call"""
        if not options_chain:
            return None
        
        # Filter for calls only
        call_options = [opt for opt in options_chain if opt.option_type == 'call']
        
        if not call_options:
            return None
        
        # Filter by delta range
        suitable_calls = []
        for option in call_options:
            if option.delta and self.min_delta <= abs(option.delta) <= self.max_delta:
                # Check minimum premium requirement
                premium_pct = option.price / current_price
                if premium_pct >= self.min_premium_pct:
                    suitable_calls.append(option)
        
        if not suitable_calls:
            return None
        
        # Score each option based on multiple factors
        scored_options = []
        for option in suitable_calls:
            score = self._calculate_strike_score(option, current_price)
            scored_options.append((option, score))
        
        # Sort by score and return best strike
        scored_options.sort(key=lambda x: x[1], reverse=True)
        
        if scored_options:
            best_option = scored_options[0][0]
            logger.info(f"Selected strike {best_option.strike} for {symbol} covered call")
            return best_option.strike
        
        return None
    
    def _calculate_strike_score(self, option: OptionContract, current_price: float) -> float:
        """Calculate score for strike selection"""
        score = 0.0
        
        # Delta score (prefer 0.4-0.5 delta)
        if option.delta:
            delta_score = 1.0 - abs(abs(option.delta) - 0.45)  # Prefer 0.45 delta
            score += delta_score * 0.4
        
        # Premium score (higher premium is better)
        premium_pct = option.price / current_price
        score += premium_pct * 0.3
        
        # Liquidity score
        if option.volume and option.open_interest:
            liquidity_score = min(option.volume / 100, option.open_interest / 500)
            score += liquidity_score * 0.2
        
        # Distance from current price (prefer slightly OTM)
        distance_pct = abs(option.strike - current_price) / current_price
        if 0.02 <= distance_pct <= 0.08:  # 2-8% OTM
            score += 0.1
        
        return score
    
    def calculate_position_metrics(self, strike: float, option_price: float, 
                                 current_price: float) -> Dict[str, float]:
        """Calculate position metrics for covered call"""
        max_profit = option_price  # Premium received
        max_loss = float('inf')  # Unlimited if stock goes to zero
        breakeven = strike + option_price  # Stock price where we break even if assigned
        
        # Calculate probability of profit (simplified)
        # This would be more sophisticated with proper options pricing model
        prob_profit = 0.6  # Placeholder - would calculate from delta
        
        return {
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'prob_profit': prob_profit,
            'premium_pct': option_price / current_price
        }
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for covered call"""
        if len(data) < 20:
            return False
        
        current_price = data['Close'].iloc[-1]
        
        # Check volatility (prefer moderate volatility)
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            volatility = atr / current_price
            if volatility < 0.01 or volatility > 0.05:  # 1-5% daily volatility
                return False
        
        # Check trend (prefer neutral to slightly bullish)
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            trend_strength = (sma_20 - sma_50) / sma_50
            
            # Avoid strongly bearish trends
            if trend_strength < -0.05:
                return False
        
        # Check options liquidity
        if not options_chain:
            return False
        
        liquid_calls = [opt for opt in options_chain 
                       if opt.option_type == 'call' and opt.volume > 10]
        
        if len(liquid_calls) < 3:
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate Covered Call signal"""
        
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
        
        # Select optimal strike
        strike = self.select_optimal_strike(symbol, current_price, options_chain)
        if not strike:
            return None
        
        # Find the selected option
        selected_option = None
        for option in options_chain:
            if (option.option_type == 'call' and 
                abs(option.strike - strike) < 0.01):
                selected_option = option
                break
        
        if not selected_option:
            return None
        
        # Calculate position metrics
        metrics = self.calculate_position_metrics(
            strike, selected_option.price, current_price
        )
        
        # Calculate confidence based on market conditions and metrics
        confidence = self._calculate_confidence(data, selected_option, metrics)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="COVERED_CALL",
            quantity=1,  # One covered call position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strike': strike,
                'option_price': selected_option.price,
                'expiration': selected_option.expiration,
                'delta': selected_option.delta,
                'max_profit': metrics['max_profit'],
                'breakeven': metrics['breakeven'],
                'prob_profit': metrics['prob_profit'],
                'premium_pct': metrics['premium_pct'],
                'signal_type': 'covered_call',
                'position_size': self.max_risk_per_trade / current_price,
                'profit_target': metrics['max_profit'] * self.profit_target_pct,
                'stop_loss': metrics['max_profit'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"Covered Call signal: {symbol} @ {strike} (confidence: {confidence:.3f}, "
                   f"premium: {metrics['premium_pct']:.2%})")
        
        return signal
    
    def _calculate_confidence(self, data: pd.DataFrame, option: OptionContract, 
                            metrics: Dict[str, float]) -> float:
        """Calculate confidence score for covered call signal"""
        confidence = 0.5  # Base confidence
        
        # Technical analysis factors
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if 40 <= rsi <= 70:  # Neutral RSI
                confidence += 0.1
        
        if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_Signal'].iloc[-1]
            if macd > macd_signal:  # Bullish MACD
                confidence += 0.1
        
        # Options-specific factors
        if option.delta:
            # Prefer moderate delta (0.3-0.5)
            delta_score = 1.0 - abs(abs(option.delta) - 0.4)
            confidence += delta_score * 0.2
        
        # Premium factor
        if metrics['premium_pct'] > 0.03:  # 3%+ premium
            confidence += 0.1
        
        # Liquidity factor
        if option.volume and option.open_interest:
            liquidity_score = min(option.volume / 100, option.open_interest / 500)
            confidence += liquidity_score * 0.1
        
        return min(confidence, 1.0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "options_income",
            "description": "Covered Call strategy for income generation",
            "parameters": {
                "days_to_expiration": self.days_to_expiration,
                "profit_target_pct": self.profit_target_pct,
                "stop_loss_pct": self.stop_loss_pct,
                "min_delta": self.min_delta,
                "max_delta": self.max_delta,
                "min_premium_pct": self.min_premium_pct
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