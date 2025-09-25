"""
Options Wheel Strategy
=====================
A comprehensive options income strategy that combines cash-secured puts and covered calls
in a systematic cycle to generate consistent income while potentially acquiring stocks at a discount.

The wheel strategy operates in two phases:
1. Put Phase: Sell cash-secured puts to collect premium and potentially acquire stock
2. Call Phase: Sell covered calls against owned stock to generate additional income

This strategy is ideal for:
- Income generation in sideways or slightly bullish markets
- Stock acquisition at discounted prices
- Systematic options trading with defined risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.options_data_service import OptionsDataService, OptionContract

logger = get_trading_logger()

class WheelPhase(Enum):
    """Options wheel strategy phases"""
    PUT_PHASE = "put_phase"  # Selling cash-secured puts
    CALL_PHASE = "call_phase"  # Selling covered calls against owned stock
    TRANSITION = "transition"  # Between phases

class OptionsWheelStrategy(BaseStrategy):
    """
    Options Wheel Strategy
    
    A systematic approach to options income generation that combines:
    - Cash-secured put selling for income and stock acquisition
    - Covered call selling for additional income on owned positions
    
    Key Features:
    - Two-phase operation (Put Phase → Call Phase)
    - Dynamic strike selection based on technical analysis
    - Comprehensive risk management
    - Portfolio integration for cash and stock management
    - Automated phase transitions
    - Income tracking and performance metrics
    """
    
    def __init__(self, 
                 name: str = "OptionsWheel",
                 # Put Phase Configuration
                 put_days_to_expiration: int = 30,
                 put_profit_target_pct: float = 0.7,
                 put_stop_loss_pct: float = 1.5,
                 put_min_delta: float = -0.7,
                 put_max_delta: float = -0.3,
                 put_min_premium_pct: float = 0.015,
                 
                 # Call Phase Configuration  
                 call_days_to_expiration: int = 30,
                 call_profit_target_pct: float = 0.7,
                 call_stop_loss_pct: float = 1.5,
                 call_min_delta: float = 0.3,
                 call_max_delta: float = 0.7,
                 call_min_premium_pct: float = 0.02,
                 
                 # General Configuration
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio per trade
                 max_cash_utilization: float = 0.8,  # 80% max cash utilization
                 min_dte: int = 21,
                 max_dte: int = 45,
                 
                 # Wheel-specific Configuration
                 max_wheel_cycles: int = 5,  # Maximum cycles per symbol
                 min_cycle_interval_days: int = 7,  # Minimum days between cycles
                 assignment_buffer_days: int = 3,  # Days to wait after assignment before selling calls
                 
                 # Stock Selection Criteria
                 min_stock_price: float = 50.0,
                 max_stock_price: float = 500.0,
                 min_volume: int = 1000000,  # 1M daily volume
                 min_options_volume: int = 100,  # Minimum options volume
                 
                 # Technical Analysis Weights
                 technical_weight: float = 0.4,
                 volatility_weight: float = 0.3,
                 momentum_weight: float = 0.3):
        
        super().__init__(name)
        
        # Put Phase Configuration
        self.put_days_to_expiration = put_days_to_expiration
        self.put_profit_target_pct = put_profit_target_pct
        self.put_stop_loss_pct = put_stop_loss_pct
        self.put_min_delta = put_min_delta
        self.put_max_delta = put_max_delta
        self.put_min_premium_pct = put_min_premium_pct
        
        # Call Phase Configuration
        self.call_days_to_expiration = call_days_to_expiration
        self.call_profit_target_pct = call_profit_target_pct
        self.call_stop_loss_pct = call_stop_loss_pct
        self.call_min_delta = call_min_delta
        self.call_max_delta = call_max_delta
        self.call_min_premium_pct = call_min_premium_pct
        
        # General Configuration
        self.max_risk_per_trade = max_risk_per_trade
        self.max_cash_utilization = max_cash_utilization
        self.min_dte = min_dte
        self.max_dte = max_dte
        
        # Wheel-specific Configuration
        self.max_wheel_cycles = max_wheel_cycles
        self.min_cycle_interval_days = min_cycle_interval_days
        self.assignment_buffer_days = assignment_buffer_days
        
        # Stock Selection Criteria
        self.min_stock_price = min_stock_price
        self.max_stock_price = max_stock_price
        self.min_volume = min_volume
        self.min_options_volume = min_options_volume
        
        # Technical Analysis Weights
        self.technical_weight = technical_weight
        self.volatility_weight = volatility_weight
        self.momentum_weight = momentum_weight
        
        # Initialize services
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.wheel_positions = {}  # symbol -> wheel position data
        self.phase_history = []  # Track phase transitions
        self.income_tracking = {}  # Track income per symbol
        self.cycle_count = {}  # Track cycles per symbol
        
    def get_wheel_position(self, symbol: str) -> Dict[str, Any]:
        """Get current wheel position for a symbol"""
        return self.wheel_positions.get(symbol, {
            'phase': WheelPhase.PUT_PHASE,
            'cycles_completed': 0,
            'total_income': 0.0,
            'current_position': None,
            'last_cycle_date': None,
            'assignment_date': None,
            'shares_owned': 0,
            'average_cost': 0.0
        })
    
    def update_wheel_position(self, symbol: str, updates: Dict[str, Any]):
        """Update wheel position for a symbol"""
        if symbol not in self.wheel_positions:
            self.wheel_positions[symbol] = self.get_wheel_position(symbol)
        
        self.wheel_positions[symbol].update(updates)
    
    def is_eligible_for_wheel(self, symbol: str, current_price: float, 
                            volume: float, options_volume: float) -> bool:
        """Check if symbol is eligible for wheel strategy"""
        # Price range check
        if not (self.min_stock_price <= current_price <= self.max_stock_price):
            return False
        
        # Volume checks
        if volume < self.min_volume or options_volume < self.min_options_volume:
            return False
        
        # Cycle limit check
        position = self.get_wheel_position(symbol)
        if position['cycles_completed'] >= self.max_wheel_cycles:
            return False
        
        # Cycle interval check
        if position['last_cycle_date']:
            days_since_last = (datetime.now() - position['last_cycle_date']).days
            if days_since_last < self.min_cycle_interval_days:
                return False
        
        return True
    
    def calculate_technical_score(self, data: pd.DataFrame) -> float:
        """Calculate technical analysis score for stock selection"""
        if len(data) < 20:
            return 0.0
        
        score = 0.0
        
        # RSI analysis
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[-1]
            if 30 <= rsi <= 70:  # Not overbought/oversold
                score += 0.2
            elif 40 <= rsi <= 60:  # Neutral zone
                score += 0.3
        
        # Moving average trend
        if 'sma_20' in data.columns and 'sma_50' in data.columns:
            sma_20 = data['sma_20'].iloc[-1]
            sma_50 = data['sma_50'].iloc[-1]
            current_price = data['close'].iloc[-1]
            
            if sma_20 > sma_50:  # Uptrend
                score += 0.2
            if current_price > sma_20:  # Above short-term MA
                score += 0.2
        
        # Bollinger Bands position
        if 'bb_upper' in data.columns and 'bb_lower' in data.columns:
            bb_upper = data['bb_upper'].iloc[-1]
            bb_lower = data['bb_lower'].iloc[-1]
            current_price = data['close'].iloc[-1]
            
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            if 0.3 <= bb_position <= 0.7:  # Middle of bands
                score += 0.3
        
        return min(score, 1.0)
    
    def calculate_volatility_score(self, data: pd.DataFrame) -> float:
        """Calculate volatility score for options pricing"""
        if len(data) < 20:
            return 0.0
        
        # Calculate historical volatility
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Higher volatility is better for options selling
        if volatility > 0.3:  # 30%+ annual volatility
            return 1.0
        elif volatility > 0.2:  # 20%+ annual volatility
            return 0.7
        elif volatility > 0.15:  # 15%+ annual volatility
            return 0.4
        else:
            return 0.1
    
    def calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calculate momentum score for trend analysis"""
        if len(data) < 20:
            return 0.0
        
        score = 0.0
        
        # Price momentum
        if len(data) >= 5:
            price_change_5d = (data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]
            if -0.05 <= price_change_5d <= 0.05:  # Stable price
                score += 0.5
            elif -0.10 <= price_change_5d <= 0.10:  # Moderate movement
                score += 0.3
        
        # Volume momentum
        if 'volume' in data.columns and len(data) >= 5:
            avg_volume = data['volume'].rolling(5).mean().iloc[-1]
            current_volume = data['volume'].iloc[-1]
            if current_volume > avg_volume * 1.2:  # Above average volume
                score += 0.3
            elif current_volume > avg_volume:  # Above average volume
                score += 0.2
        
        return min(score, 1.0)
    
    def select_optimal_put_strike(self, symbol: str, current_price: float, 
                                options_chain: List[OptionContract]) -> Optional[float]:
        """Select optimal strike for cash-secured put"""
        if not options_chain:
            return None
        
        # Filter puts within delta range
        valid_puts = [
            opt for opt in options_chain
            if (opt.option_type == 'put' and 
                self.put_min_delta <= opt.delta <= self.put_max_delta and
                self.min_dte <= opt.days_to_expiration <= self.max_dte)
        ]
        
        if not valid_puts:
            return None
        
        # Select based on premium percentage and delta
        best_strike = None
        best_score = 0.0
        
        for option in valid_puts:
            premium_pct = option.bid / current_price
            
            if premium_pct >= self.put_min_premium_pct:
                # Score based on delta position and premium
                delta_score = 1.0 - abs(option.delta - (self.put_min_delta + self.put_max_delta) / 2) / 0.2
                premium_score = min(premium_pct / 0.05, 1.0)  # Cap at 5%
                
                total_score = delta_score * 0.6 + premium_score * 0.4
                
                if total_score > best_score:
                    best_score = total_score
                    best_strike = option.strike
        
        return best_strike
    
    def select_optimal_call_strike(self, symbol: str, current_price: float, 
                                 options_chain: List[OptionContract]) -> Optional[float]:
        """Select optimal strike for covered call"""
        if not options_chain:
            return None
        
        # Filter calls within delta range
        valid_calls = [
            opt for opt in options_chain
            if (opt.option_type == 'call' and 
                self.call_min_delta <= opt.delta <= self.call_max_delta and
                self.min_dte <= opt.days_to_expiration <= self.max_dte)
        ]
        
        if not valid_calls:
            return None
        
        # Select based on premium percentage and delta
        best_strike = None
        best_score = 0.0
        
        for option in valid_calls:
            premium_pct = option.bid / current_price
            
            if premium_pct >= self.call_min_premium_pct:
                # Score based on delta position and premium
                delta_score = 1.0 - abs(option.delta - (self.call_min_delta + self.call_max_delta) / 2) / 0.2
                premium_score = min(premium_pct / 0.05, 1.0)  # Cap at 5%
                
                total_score = delta_score * 0.6 + premium_score * 0.4
                
                if total_score > best_score:
                    best_score = total_score
                    best_strike = option.strike
        
        return best_strike
    
    def check_cash_availability(self, symbol: str, strike: float, portfolio_value: float) -> bool:
        """Check if we have sufficient cash for cash-secured put"""
        required_cash = strike * 100  # 100 shares per contract
        available_cash = portfolio_value * self.max_cash_utilization
        return required_cash <= available_cash
    
    def check_stock_ownership(self, symbol: str, required_shares: int) -> bool:
        """Check if we own sufficient shares for covered call"""
        position = self.get_wheel_position(symbol)
        return position['shares_owned'] >= required_shares
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """
        Generate trading signal for options wheel strategy
        
        Args:
            symbol: Trading symbol
            data: Market data dataframe with technical indicators
            historical_date: Historical date for backtesting
            
        Returns:
            TradeSignal or None if no signal
        """
        if not self.is_active or len(data) < 20:
            return None
        
        current_price = data['close'].iloc[-1]
        volume = data['volume'].iloc[-1] if 'volume' in data.columns else 0
        
        # Check eligibility
        if not self.is_eligible_for_wheel(symbol, current_price, volume, 1000):  # Assume options volume
            return None
        
        # Get current wheel position
        position = self.get_wheel_position(symbol)
        
        # Calculate scores
        technical_score = self.calculate_technical_score(data)
        volatility_score = self.calculate_volatility_score(data)
        momentum_score = self.calculate_momentum_score(data)
        
        # Combined score
        combined_score = (
            technical_score * self.technical_weight +
            volatility_score * self.volatility_weight +
            momentum_score * self.momentum_weight
        )
        
        # Minimum score threshold
        if combined_score < 0.6:
            return None
        
        # Get options chain (simplified - would use real options data service)
        options_chain = []  # This would be populated from OptionsDataService
        
        if position['phase'] == WheelPhase.PUT_PHASE:
            # Check if we can sell puts
            if not self.check_cash_availability(symbol, current_price * 0.95, 100000):  # Assume portfolio value
                return None
            
            # Select put strike
            put_strike = self.select_optimal_put_strike(symbol, current_price, options_chain)
            if not put_strike:
                return None
            
            # Create put selling signal
            signal = TradeSignal(
                symbol=symbol,
                action="SELL_PUT",
                quantity=1,  # 1 contract = 100 shares
                price=put_strike,
                confidence=combined_score,
                strategy=self.name,
                metadata={
                    'phase': 'put_phase',
                    'strike': put_strike,
                    'expiration_days': self.put_days_to_expiration,
                    'expected_premium': put_strike * 0.02,  # Estimate 2% premium
                    'max_loss': put_strike * 100,
                    'technical_score': technical_score,
                    'volatility_score': volatility_score,
                    'momentum_score': momentum_score
                }
            )
            
            # Update position
            self.update_wheel_position(symbol, {
                'phase': WheelPhase.PUT_PHASE,
                'current_position': {
                    'type': 'put',
                    'strike': put_strike,
                    'entry_date': datetime.now(),
                    'expiration_days': self.put_days_to_expiration
                },
                'last_cycle_date': datetime.now()
            })
            
            return signal
        
        elif position['phase'] == WheelPhase.CALL_PHASE:
            # Check if we own stock
            if not self.check_stock_ownership(symbol, 100):
                return None
            
            # Select call strike
            call_strike = self.select_optimal_call_strike(symbol, current_price, options_chain)
            if not call_strike:
                return None
            
            # Create call selling signal
            signal = TradeSignal(
                symbol=symbol,
                action="SELL_CALL",
                quantity=1,  # 1 contract = 100 shares
                price=call_strike,
                confidence=combined_score,
                strategy=self.name,
                metadata={
                    'phase': 'call_phase',
                    'strike': call_strike,
                    'expiration_days': self.call_days_to_expiration,
                    'expected_premium': call_strike * 0.02,  # Estimate 2% premium
                    'shares_covered': 100,
                    'technical_score': technical_score,
                    'volatility_score': volatility_score,
                    'momentum_score': momentum_score
                }
            )
            
            # Update position
            self.update_wheel_position(symbol, {
                'phase': WheelPhase.CALL_PHASE,
                'current_position': {
                    'type': 'call',
                    'strike': call_strike,
                    'entry_date': datetime.now(),
                    'expiration_days': self.call_days_to_expiration
                },
                'last_cycle_date': datetime.now()
            })
            
            return signal
        
        return None
    
    def handle_assignment(self, symbol: str, strike: float, shares: int):
        """Handle option assignment (put assignment = stock acquisition)"""
        position = self.get_wheel_position(symbol)
        
        if position['current_position'] and position['current_position']['type'] == 'put':
            # Put assignment - we now own stock
            new_shares = position['shares_owned'] + shares
            total_cost = (position['shares_owned'] * position['average_cost'] + 
                         shares * strike)
            new_average_cost = total_cost / new_shares
            
            self.update_wheel_position(symbol, {
                'phase': WheelPhase.TRANSITION,
                'shares_owned': new_shares,
                'average_cost': new_average_cost,
                'assignment_date': datetime.now(),
                'current_position': None
            })
            
            logger.info(f"Put assignment for {symbol}: {shares} shares at ${strike}, "
                       f"new total: {new_shares} shares at ${new_average_cost:.2f} avg cost")
    
    def handle_call_assignment(self, symbol: str, strike: float, shares: int):
        """Handle call assignment (call assignment = stock sale)"""
        position = self.get_wheel_position(symbol)
        
        if position['current_position'] and position['current_position']['type'] == 'call':
            # Call assignment - we sold stock
            remaining_shares = max(0, position['shares_owned'] - shares)
            
            # Calculate profit/loss
            cost_basis = shares * position['average_cost']
            sale_proceeds = shares * strike
            profit = sale_proceeds - cost_basis
            
            self.update_wheel_position(symbol, {
                'phase': WheelPhase.PUT_PHASE,  # Back to put phase
                'shares_owned': remaining_shares,
                'cycles_completed': position['cycles_completed'] + 1,
                'total_income': position['total_income'] + profit,
                'current_position': None
            })
            
            logger.info(f"Call assignment for {symbol}: {shares} shares at ${strike}, "
                       f"profit: ${profit:.2f}, remaining shares: {remaining_shares}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information"""
        base_info = super().get_strategy_info()
        
        wheel_info = {
            'active_wheels': len(self.wheel_positions),
            'total_cycles': sum(pos['cycles_completed'] for pos in self.wheel_positions.values()),
            'total_income': sum(pos['total_income'] for pos in self.wheel_positions.values()),
            'phase_distribution': {
                'put_phase': sum(1 for pos in self.wheel_positions.values() 
                               if pos['phase'] == WheelPhase.PUT_PHASE),
                'call_phase': sum(1 for pos in self.wheel_positions.values() 
                                if pos['phase'] == WheelPhase.CALL_PHASE),
                'transition': sum(1 for pos in self.wheel_positions.values() 
                               if pos['phase'] == WheelPhase.TRANSITION)
            },
            'wheel_positions': self.wheel_positions
        }
        
        return {**base_info, **wheel_info}


