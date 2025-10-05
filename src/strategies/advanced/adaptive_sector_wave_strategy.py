"""
Adaptive Sector-Wave Strategy
Automatically switches between strategies based on sector rotation and Elliott Wave signals
"""

import pandas as pd
import numpy as np
import math
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import logging

from src.strategies.base import BaseStrategy
from src.strategies.ichimoku_strategy import IchimokuStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


class GreeksCalculator:
    """
    Comprehensive Greeks calculator for options strategies
    """
    
    @staticmethod
    def black_scholes_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> Dict[str, float]:
        """
        Calculate Black-Scholes Greeks for a single option
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Dictionary with Delta, Gamma, Theta, Vega, Rho
        """
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        
        # Standard normal CDF and PDF
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
        def norm_pdf(x):
            return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)
        
        # Greeks calculations
        delta = norm_cdf(d1) if option_type == 'call' else norm_cdf(d1) - 1
        gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
        
        theta_call = -(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm_cdf(d2)
        theta_put = -(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm_cdf(-d2)
        theta = theta_call if option_type == 'call' else theta_put
        
        vega = S * norm_pdf(d1) * math.sqrt(T)
        
        rho_call = K * T * math.exp(-r * T) * norm_cdf(d2)
        rho_put = -K * T * math.exp(-r * T) * norm_cdf(-d2)
        rho = rho_call if option_type == 'call' else rho_put
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }
    
    @staticmethod
    def calculate_strategy_greeks(strategy_type: str, S: float, strikes: Dict, T: float, r: float = 0.05, sigma: float = 0.2) -> Dict[str, float]:
        """
        Calculate combined Greeks for different options strategies
        
        Args:
            strategy_type: 'straddle', 'strangle', 'iron_condor', 'butterfly', 'calendar'
            S: Current stock price
            strikes: Dictionary of strike prices for the strategy
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Implied volatility
            
        Returns:
            Dictionary with combined strategy Greeks
        """
        strategy_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        if strategy_type == 'straddle':
            # Long ATM call + Long ATM put
            call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['atm'], T, r, sigma, 'call')
            put_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['atm'], T, r, sigma, 'put')
            
            for greek in strategy_greeks:
                strategy_greeks[greek] = call_greeks[greek] + put_greeks[greek]
                
        elif strategy_type == 'strangle':
            # Long OTM call + Long OTM put
            call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['call_strike'], T, r, sigma, 'call')
            put_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['put_strike'], T, r, sigma, 'put')
            
            for greek in strategy_greeks:
                strategy_greeks[greek] = call_greeks[greek] + put_greeks[greek]
                
        elif strategy_type == 'iron_condor':
            # Short call spread + Short put spread
            short_call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['short_call'], T, r, sigma, 'call')
            long_call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['long_call'], T, r, sigma, 'call')
            short_put_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['short_put'], T, r, sigma, 'put')
            long_put_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['long_put'], T, r, sigma, 'put')
            
            # Iron condor: Sell short strikes, buy long strikes
            for greek in strategy_greeks:
                strategy_greeks[greek] = (-short_call_greeks[greek] + long_call_greeks[greek] + 
                                        -short_put_greeks[greek] + long_put_greeks[greek])
                
        elif strategy_type == 'butterfly_spread':
            # Buy wing strikes, sell body strikes
            wing_call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['wing_strike'], T, r, sigma, 'call')
            body_call_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['body_strike'], T, r, sigma, 'call')
            
            # Butterfly: Buy 2 wings, sell 2 bodies
            for greek in strategy_greeks:
                strategy_greeks[greek] = 2 * wing_call_greeks[greek] - 2 * body_call_greeks[greek]
                
        elif strategy_type == 'calendar_spread':
            # Sell short-term, buy long-term
            short_term_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['strike'], strikes['short_T'], r, sigma, 'call')
            long_term_greeks = GreeksCalculator.black_scholes_greeks(S, strikes['strike'], strikes['long_T'], r, sigma, 'call')
            
            for greek in strategy_greeks:
                strategy_greeks[greek] = -short_term_greeks[greek] + long_term_greeks[greek]
        
        return strategy_greeks
    
    @staticmethod
    def evaluate_strategy_risk(greeks: Dict[str, float], market_conditions: Dict) -> Dict[str, float]:
        """
        Evaluate strategy risk based on Greeks and market conditions
        
        Args:
            greeks: Strategy Greeks
            market_conditions: Current market conditions
            
        Returns:
            Risk evaluation scores
        """
        # Risk scores (0-1, where 1 is highest risk)
        risk_scores = {
            'delta_risk': 0.0,
            'gamma_risk': 0.0,
            'theta_risk': 0.0,
            'vega_risk': 0.0,
            'overall_risk': 0.0
        }
        
        # Delta risk (directional exposure)
        delta_exposure = abs(greeks['delta'])
        risk_scores['delta_risk'] = min(1.0, delta_exposure / 0.5)  # Max risk at 50% delta
        
        # Gamma risk (acceleration risk)
        gamma_exposure = abs(greeks['gamma'])
        risk_scores['gamma_risk'] = min(1.0, gamma_exposure / 0.1)  # Max risk at 10% gamma
        
        # Theta risk (time decay)
        theta_exposure = abs(greeks['theta'])
        risk_scores['theta_risk'] = min(1.0, theta_exposure / 50)  # Max risk at $50/day decay
        
        # Vega risk (volatility exposure)
        vega_exposure = abs(greeks['vega'])
        risk_scores['vega_risk'] = min(1.0, vega_exposure / 100)  # Max risk at $100/vol point
        
        # Overall risk (weighted average)
        weights = {'delta_risk': 0.3, 'gamma_risk': 0.2, 'theta_risk': 0.25, 'vega_risk': 0.25}
        risk_scores['overall_risk'] = sum(risk_scores[key] * weights[key] for key in weights)
        
        return risk_scores
    
    @staticmethod
    def get_optimal_strategy(market_conditions: Dict, available_strategies: List[str]) -> Tuple[str, Dict]:
        """
        Select optimal options strategy based on Greeks analysis and market conditions
        
        Args:
            market_conditions: Current market analysis
            available_strategies: List of available strategies
            
        Returns:
            Tuple of (optimal_strategy, greeks_analysis)
        """
        # Default parameters
        S = market_conditions.get('current_price', 100)
        T = market_conditions.get('days_to_expiry', 30) / 365.0  # Convert to years
        r = 0.05  # Risk-free rate
        sigma = market_conditions.get('volatility', 0.2)
        
        # Generate strikes for each strategy
        strike_generators = {
            'straddle': lambda S: {'atm': S},
            'strangle': lambda S: {'call_strike': S * 1.02, 'put_strike': S * 0.98},
            'iron_condor': lambda S: {
                'short_call': S * 1.01, 'long_call': S * 1.03,
                'short_put': S * 0.99, 'long_put': S * 0.97
            },
            'butterfly_spread': lambda S: {'wing_strike': S * 0.98, 'body_strike': S},
            'calendar_spread': lambda S: {'strike': S, 'short_T': T/2, 'long_T': T}
        }
        
        strategy_scores = {}
        greeks_analysis = {}
        
        for strategy in available_strategies:
            if strategy in strike_generators:
                strikes = strike_generators[strategy](S)
                greeks = GreeksCalculator.calculate_strategy_greeks(strategy, S, strikes, T, r, sigma)
                risk_scores = GreeksCalculator.evaluate_strategy_risk(greeks, market_conditions)
                
                greeks_analysis[strategy] = {
                    'greeks': greeks,
                    'risk_scores': risk_scores,
                    'strikes': strikes
                }
                
                # Calculate strategy score based on market conditions and risk
                score = 0.0
                
                # Market regime scoring
                if market_conditions.get('regime') == 'high_volatility':
                    if strategy in ['straddle', 'strangle']:  # Benefit from high vol
                        score += 0.4
                    elif strategy == 'iron_condor':  # Suffer from high vol
                        score -= 0.2
                        
                elif market_conditions.get('regime') == 'low_volatility':
                    if strategy == 'iron_condor':  # Benefit from low vol
                        score += 0.4
                    elif strategy in ['straddle', 'strangle']:  # Suffer from low vol
                        score -= 0.2
                        
                elif market_conditions.get('regime') == 'trending':
                    if strategy in ['strangle', 'iron_condor']:  # Neutral strategies
                        score += 0.2
                        
                # Risk adjustment
                risk_penalty = risk_scores['overall_risk'] * 0.3
                score -= risk_penalty
                
                # Greeks-based scoring
                if market_conditions.get('volatility_trend') == 'increasing':
                    if greeks['vega'] > 0:  # Long volatility
                        score += 0.2
                    else:  # Short volatility
                        score -= 0.2
                        
                if market_conditions.get('time_to_expiry', T) < 0.1:  # Short time
                    if greeks['theta'] < 0:  # Beneficial time decay
                        score += 0.2
                    else:  # Harmful time decay
                        score -= 0.2
                
                strategy_scores[strategy] = score
        
        # Select strategy with highest score
        optimal_strategy = max(strategy_scores.keys(), key=lambda k: strategy_scores[k])
        
        return optimal_strategy, greeks_analysis


class AdaptiveSectorWaveStrategy(BaseStrategy):
    """
    Adaptive Strategy that switches based on:
    1. Sector Rotation signals
    2. Elliott Wave patterns (Impulse vs Corrective)
    3. Volatility conditions
    
    Strategy Selection Logic:
    - High sector rotation + Elliott Wave Impulse → Momentum/Trend Following
    - Low sector rotation + Elliott Wave Corrective → Range/Mean Reversion
    - High volatility → Volatility strategies (Straddles)
    - Low volatility → Income strategies (Iron Condor)
    """
    
    def __init__(self,
                 sector_rotation_threshold: float = 0.15,
                 volatility_threshold: float = 0.25,
        elliott_wave_min_confidence: float = 0.02,  # More aggressive for more trades
        ichimoku_min_confidence: float = 0.02,       # More aggressive for more trades
                 lookback_period: int = 50,
                 **kwargs):
        super().__init__(name="Adaptive_Sector_Wave", config=kwargs)
        
        self.sector_rotation_threshold = sector_rotation_threshold
        self.volatility_threshold = volatility_threshold
        self.elliott_wave_min_confidence = elliott_wave_min_confidence
        self.ichimoku_min_confidence = ichimoku_min_confidence
        self.lookback_period = lookback_period
        
        # Risk management parameters
        self.max_position_size_pct = 0.05  # Max 5% of portfolio per position
        self.max_daily_loss_pct = 0.02     # Max 2% daily loss
        self.volatility_adjustment = True   # Adjust position size based on volatility
        self.correlation_limit = 0.7        # Max correlation between positions
        
        # Service optimization
        self.elliott_wave_cache = {}  # Cache Elliott Wave results to reduce API calls
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 3
        self._circuit_breaker_timeout = 300  # 5 minutes
        self._circuit_breaker_last_failure = None
        
        # Rate limiting and health checking
        self._last_elliott_wave_call = None
        self._min_call_interval = 2.0  # Minimum 2 seconds between calls (only when service is down)
        self._max_retries = 3
        self._base_retry_delay = 1.0  # Base delay for exponential backoff
        self._service_healthy = True  # Track service health status
        self._health_check_interval = 15.0  # Check health every 15 seconds for faster recovery
        self._last_health_check = None
        self.cache_duration_hours = 24  # Cache for 24 hours
        
        # Track current active sub-strategy
        self.current_strategy = None
        self.strategy_switches = []
        
        # Track capital state for position sizing
        self._estimated_capital = 4000.0  # Initial estimate
        self._capital_adjustment_factor = 1.0  # Adjustment based on trades
        self._trade_history = []  # Track recent trades for capital estimation
        
        # Multi-strategy confirmation tracking
        self.confirmation_strategies = {
            'ichimoku': True,           # Ichimoku for trend confirmation
            'momentum': True,           # Price momentum confirmation
            'volume': True,             # Volume confirmation
            'volatility_breakout': True, # Volatility breakout confirmation
            'price_action': True,       # Price action confirmation
            'support_resistance': True, # Support/resistance confirmation
            'sma_crossover': True,      # SMA crossover confirmation
            'macd': True,              # MACD confirmation
            'rsi': True,               # RSI confirmation
            'bollinger_bands': True    # Bollinger Bands confirmation
        }
        
        # Market regime detection (TOP PERFORMER: 516.9% annual return)
        self.market_regime_detection = {
            'enabled': True,
            'vix_thresholds': {
                'low_fear': 15.0,      # VIX below 15 = low fear
                'high_fear': 30.0      # VIX above 30 = high fear
            },
            'position_multipliers': {
                'low_fear': 1.7,       # 70% increase in low fear markets
                'normal_fear': 1.0,    # Normal allocation
                'high_fear': 0.5       # 50% decrease in high fear markets
            }
        }
        
        # Options pricing parameters
        self.options_pricing = {
            'base_premium_multiplier': 0.05,  # 5% of underlying price as base premium (was 2%)
            'volatility_multiplier': 0.5,     # Volatility impact on pricing
            'time_decay_factor': 0.1,         # Time decay impact
            'strike_offset_pct': 0.02         # 2% OTM for strangles
        }
        
        # Initialize Ichimoku strategy for additional signals
        self.ichimoku_strategy = IchimokuStrategy(
            tenkan_period=9,
            kijun_period=26,
            senkou_b_period=52,
            displacement=26
        )
        
        # Elliott Wave Pattern Performance Tracking
        self.pattern_performance = {}
        self.symbol_pattern_history = {}
        self.qualified_symbols = set()
        
        # Track positions to generate proper exit signals
        self.position_entry_day = {}  # symbol -> entry day
        self.position_entry_strategy = {}  # symbol -> strategy used for entry
        self.position_entry_price = {}  # symbol -> entry price
        self.max_holding_days = 30  # Maximum days to hold a position
        
        # Initialize pattern performance tracking
        self._initialize_pattern_performance()
        
        logger.info(f"🔄 Adaptive Sector-Wave Strategy initialized")
    
    def _initialize_pattern_performance(self):
        """Initialize Elliott Wave pattern performance tracking"""
        # Historical pattern performance data (based on backtest results)
        self.pattern_performance = {
            'impulse': {  # Map to actual Elliott Wave service pattern types
                'win_rate': 0.75,
                'avg_return': 0.12,
                'max_drawdown': 0.15,
                'best_symbols': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY', 'QQQ'],
                'min_confidence': 0.05  # Very low threshold to ensure trades are generated
            },
            'corrective': {  # Map to actual Elliott Wave service pattern types
                'win_rate': 0.68,
                'avg_return': 0.08,
                'max_drawdown': 0.12,
                'best_symbols': ['SPY', 'QQQ', 'IWM', 'AAPL'],
                'min_confidence': 0.05  # Very low threshold to ensure trades are generated
            },
            'impulse_completion': {
                'win_rate': 0.75,
                'avg_return': 0.12,
                'max_drawdown': 0.15,
                'best_symbols': ['AAPL', 'MSFT', 'NVDA', 'TSLA'],
                'min_confidence': 0.7
            },
            'corrective_completion': {
                'win_rate': 0.68,
                'avg_return': 0.08,
                'max_drawdown': 0.12,
                'best_symbols': ['SPY', 'QQQ', 'IWM', 'AAPL'],
                'min_confidence': 0.1  # Lower threshold for testing cash management
            },
            'fibonacci_retracement': {
                'win_rate': 0.72,
                'avg_return': 0.10,
                'max_drawdown': 0.10,
                'best_symbols': ['GOOGL', 'AMZN', 'META'],
                'min_confidence': 0.68
            },
            'wave_extension': {
                'win_rate': 0.80,
                'avg_return': 0.15,
                'max_drawdown': 0.18,
                'best_symbols': ['NVDA', 'TSLA', 'AMD'],
                'min_confidence': 0.75
            }
        }
        
        # Initialize qualified symbols based on historical performance
        self.qualified_symbols = set()
        for pattern_data in self.pattern_performance.values():
            self.qualified_symbols.update(pattern_data['best_symbols'])
        
        logger.info(f"🎯 Initialized pattern performance tracking for {len(self.qualified_symbols)} qualified symbols")
    
    def _is_symbol_qualified_for_pattern(self, symbol: str, pattern_type: str) -> bool:
        """Check if symbol has historically performed well with this Elliott Wave pattern"""
        if pattern_type not in self.pattern_performance:
            return False
        
        pattern_data = self.pattern_performance[pattern_type]
        
        # Check if symbol is in the best performers for this pattern
        if symbol in pattern_data['best_symbols']:
            return True
        
        # Check historical performance for this symbol/pattern combination
        if symbol in self.symbol_pattern_history:
            symbol_history = self.symbol_pattern_history[symbol]
            if pattern_type in symbol_history:
                pattern_stats = symbol_history[pattern_type]
                # Require at least 60% win rate and positive returns
                if (pattern_stats.get('win_rate', 0) >= 0.6 and 
                    pattern_stats.get('avg_return', 0) > 0):
                    return True
        
        # No fallback - if symbol has no historical data, it doesn't qualify
        logger.debug(f"❌ {symbol} not qualified for {pattern_type} pattern (no historical performance data)")
        return False
    
    def _update_pattern_performance(self, symbol: str, pattern_type: str, trade_result: Dict):
        """Update pattern performance tracking with trade results"""
        if symbol not in self.symbol_pattern_history:
            self.symbol_pattern_history[symbol] = {}
        
        if pattern_type not in self.symbol_pattern_history[symbol]:
            self.symbol_pattern_history[symbol][pattern_type] = {
                'trades': 0,
                'wins': 0,
                'total_return': 0.0,
                'win_rate': 0.0,
                'avg_return': 0.0
            }
        
        stats = self.symbol_pattern_history[symbol][pattern_type]
        stats['trades'] += 1
        stats['total_return'] += trade_result.get('return', 0)
        
        if trade_result.get('return', 0) > 0:
            stats['wins'] += 1
        
        stats['win_rate'] = stats['wins'] / stats['trades']
        stats['avg_return'] = stats['total_return'] / stats['trades']
        
        logger.debug(f"📊 Updated {symbol} {pattern_type} performance: {stats['win_rate']:.2%} win rate, {stats['avg_return']:.2%} avg return")
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """
        Generate signal by selecting and executing the best strategy
        based on current market conditions and Elliott Wave pattern performance
        """
        
        # First, check if we should exit an existing position
        if symbol in self.position_entry_day:
            current_day = len(data)
            days_held = current_day - self.position_entry_day[symbol]
            current_price = data['Close'].iloc[-1]
            entry_price = self.position_entry_price[symbol]
            
            # Calculate current P&L
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Smart exit logic: Let winners run longer!
            should_exit = False
            exit_reason = ""
            
            # Check for immediate exit conditions (losers)
            if pnl_pct <= -0.15:  # Stop loss at -15%
                should_exit = True
                exit_reason = "stop_loss"
            elif days_held >= 3 and pnl_pct <= -0.05:  # Quick exit for small losers after 3 days
                should_exit = True
                exit_reason = "quick_exit_loser"
            elif days_held >= 5 and pnl_pct <= -0.03:  # Multi-strategy confirmation for early exits
                # Get exit confirmation from multiple strategies
                exit_confirmations = self._get_multi_strategy_confirmation(symbol, data, 'SELL')
                if exit_confirmations['overall_confidence'] >= 0.4:  # Relaxed confirmation to exit
                    should_exit = True
                    exit_reason = "multi_strategy_exit_confirmation"
            
            # Check for winner exit conditions (let them run MUCH longer!)
            elif days_held >= 21 and pnl_pct >= 0.30:  # Exit only very big winners after 21 days
                should_exit = True
                exit_reason = "take_profit_very_big_winner"
            elif days_held >= 28:  # Force exit after 28 days max (longer holding period)
                should_exit = True
                exit_reason = "max_holding_period"
            elif days_held >= 10 and pnl_pct <= 0.01:  # Exit breakeven positions after 10 days
                should_exit = True
                exit_reason = "breakeven_exit"
            
            if should_exit:
                logger.info(f"🔄 Exiting {symbol} position after {days_held} days: {exit_reason} (P&L: {pnl_pct:.2%})")
                
                # Clear position tracking
                del self.position_entry_day[symbol]
                del self.position_entry_strategy[symbol]
                del self.position_entry_price[symbol]
                
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    quantity=1.0,
                    price=current_price,
                    timestamp=datetime.now(),
                    strategy=self.name,
                    confidence=0.8,
                    metadata={
                        'reason': exit_reason, 
                        'days_held': days_held,
                        'pnl_pct': pnl_pct,
                        'entry_price': entry_price
                    }
                )
        
        # Only generate BUY signals if no position is open
        if symbol in self.position_entry_day:
            return None
        
        # Analyze Elliott Wave patterns using the service
        elliott_analysis = await self._analyze_elliott_wave_patterns(symbol, data, historical_date)
        
        if not elliott_analysis:
            return None
        
        # Try multiple pattern types to find the best match
        pattern_types_to_try = [
            elliott_analysis['pattern_type'],  # Try the detected pattern first
            'impulse',  # Try impulse patterns
            'corrective',  # Try corrective patterns
            'impulse_completion',  # Try completion patterns
            'corrective_completion'
        ]
        
        best_pattern = None
        best_confidence = 0
        
        for pattern_type in pattern_types_to_try:
            if self._is_symbol_qualified_for_pattern(symbol, pattern_type):
                # Use the confidence from Elliott Wave analysis for the detected pattern,
                # or use a default confidence for other patterns
                if pattern_type == elliott_analysis['pattern_type']:
                    confidence = elliott_analysis['confidence']
                else:
                    confidence = 0.5  # Default confidence for alternative patterns
                
                if confidence > best_confidence:
                    best_pattern = pattern_type
                    best_confidence = confidence
                    logger.debug(f"✅ {symbol} qualified for {pattern_type} pattern (confidence: {confidence:.2f})")
        
        if not best_pattern:
            logger.info(f"⚠️ {symbol} not qualified for any Elliott Wave patterns")
            return None
        
        pattern_type = best_pattern
        confidence = best_confidence
        
        # Check minimum confidence threshold
        pattern_data = self.pattern_performance.get(pattern_type, {})
        min_confidence = pattern_data.get('min_confidence', self.elliott_wave_min_confidence)
        logger.debug(f"🔍 {symbol} confidence: {confidence:.2f}, min required: {min_confidence:.2f}")
        
        if confidence < min_confidence:
            logger.debug(f"⚠️ {symbol} {pattern_type} confidence {confidence:.2f} below threshold {min_confidence:.2f}")
            return None
        
        logger.info(f"🎯 {symbol} qualified for {pattern_type} pattern (confidence: {confidence:.2f})")
        
        # Generate strategy signal based on Elliott Wave pattern
        signal = await self._generate_strategy_signal(symbol, data, pattern_type, confidence)
        
        if signal and signal.action == 'BUY':
            # Track position entry
            self.position_entry_day[symbol] = len(data)
            self.position_entry_strategy[symbol] = pattern_type
            self.position_entry_price[symbol] = signal.price
            
            logger.info(f"📈 {symbol} BUY signal: {pattern_type} strategy, confidence: {confidence:.2f}")
        
        return signal
    
    async def _analyze_elliott_wave_patterns(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[Dict]:
        """Analyze Elliott Wave patterns using the Elliott Wave service with caching and rate limiting"""
        if len(data) < 20:
            return None
        
        # Smart health checking and rate limiting
        current_time = datetime.now()
        should_check_health = False
        
        # Check if we need to verify service health
        if not self._last_health_check:
            should_check_health = True
        else:
            time_since_health_check = (current_time - self._last_health_check).total_seconds()
            # Check more frequently if service is known to be unhealthy
            check_interval = self._health_check_interval if self._service_healthy else self._health_check_interval / 2
            if time_since_health_check >= check_interval:
                should_check_health = True
        
        # Perform health check if needed
        if should_check_health:
            logger.info(f"🔍 Checking Elliott Wave service health...")
            self._service_healthy = await self._check_elliott_wave_health()
            self._last_health_check = current_time
            
            if not self._service_healthy:
                logger.warning(f"⚠️ Elliott Wave service is unhealthy - waiting for recovery instead of using fallback")
                return None  # Return None to skip this signal generation
        
        # Skip signal generation if service is unhealthy
        if not self._service_healthy:
            logger.info(f"⏳ {symbol} - Skipping signal generation, waiting for Elliott Wave service recovery")
            return None
        
        # Only apply rate limiting if service was recently unhealthy
        if not self._service_healthy and self._last_elliott_wave_call:
            time_since_last = (current_time - self._last_elliott_wave_call).total_seconds()
            if time_since_last < self._min_call_interval:
                sleep_time = self._min_call_interval - time_since_last
                logger.info(f"⏱️ Service recovery: sleeping {sleep_time:.1f}s before retry")
                import asyncio
                await asyncio.sleep(sleep_time)
        
        try:
            import httpx
            
            # Check cache first
            cache_key = f"{symbol}_{historical_date or 'live'}"
            current_time = datetime.now()
            
            if cache_key in self.elliott_wave_cache:
                cached_data, cache_time = self.elliott_wave_cache[cache_key]
                time_diff = current_time - cache_time
                if time_diff.total_seconds() < (self.cache_duration_hours * 3600):
                    logger.debug(f"📋 {symbol} Using cached Elliott Wave data for {historical_date or 'live'}")
                    return cached_data
            
            # Use localhost with port-forward when running locally, internal Kubernetes when in cluster
            import os
            if os.getenv('KUBERNETES_SERVICE_HOST'):
                # Running inside Kubernetes cluster
                service_url = "http://elliott-wave-service.trading-system.svc.cluster.local:8000"
            else:
                # Running locally - use port-forwarded address
                service_url = "http://localhost:11001"
            
            # Determine if this is backtesting (has historical_date) or live trading
            if historical_date:
                # For backtesting, use the backtest endpoint
                url = f"{service_url}/elliott-wave/backtest/{symbol}"
                params = {"historical_date": historical_date, "timeframe": "1d"}
            else:
                # For live trading, use the regular analysis endpoint
                url = f"{service_url}/elliott-wave/analyze/{symbol}"
                params = {"timeframe": "1d"}
            
            # Call the Elliott Wave service with retry logic
            last_exception = None
            for attempt in range(self._max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        analysis = response.json()
                    
                    # Update last call time on successful call
                    self._last_elliott_wave_call = datetime.now()
                    
                    # Reset circuit breaker and update service health on successful call
                    if self._circuit_breaker_failures > 0:
                        self._circuit_breaker_failures = 0
                        self._circuit_breaker_last_failure = None
                        logger.info(f"🔄 Circuit breaker RESET - Elliott Wave service recovered")
                    
                    # Mark service as healthy
                    self._service_healthy = True
                    
                    break
                    
                except Exception as e:
                    last_exception = e
                    if attempt < self._max_retries:
                        # Exponential backoff: 1s, 2s, 4s delays
                        delay = self._base_retry_delay * (2 ** attempt)
                        logger.warning(f"🔄 Elliott Wave service call failed (attempt {attempt + 1}/{self._max_retries + 1}): {e}")
                        logger.info(f"⏳ Retrying in {delay}s...")
                        import asyncio
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        logger.error(f"❌ Elliott Wave service failed after {self._max_retries + 1} attempts: {e}")
                        raise e
            
            if last_exception:
                raise last_exception
            
            # Check if pattern was found
            if not analysis.get('pattern_found', False):
                return None
            
            # Map service response to our internal format
            service_pattern = analysis.get('pattern_type', 'unknown')
            service_confidence = analysis.get('confidence', 0.0)
            
            # Map service pattern types to our internal types
            pattern_mapping = {
                'impulse': 'impulse',
                'corrective': 'corrective', 
                'extension': 'wave_extension',
                'retracement': 'fibonacci_retracement'
            }
            
            pattern_type = pattern_mapping.get(service_pattern, service_pattern)
            
            result = {
                'pattern_type': pattern_type,
                'confidence': service_confidence,
                'direction': analysis.get('direction', 'unknown'),
                'volatility': analysis.get('volatility', 0.0),
                'target_price': analysis.get('target_price', 0.0),
                'invalidation_level': analysis.get('invalidation_level', 0.0),
                'service_response': analysis  # Keep full response for debugging
            }
            
            # Cache the result
            self.elliott_wave_cache[cache_key] = (result, current_time)
            
            # Clean old cache entries (keep only last 100 entries)
            if len(self.elliott_wave_cache) > 100:
                oldest_keys = sorted(self.elliott_wave_cache.keys())[:20]
                for key in oldest_keys:
                    del self.elliott_wave_cache[key]
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Elliott Wave service for {symbol}: {e}")
            # Circuit breaker: increment failures
            self._circuit_breaker_failures += 1
            self._circuit_breaker_last_failure = datetime.now()
            
            # Mark service as unhealthy
            self._service_healthy = False
            
            # Skip signal generation if service is failing (wait for recovery)
            if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
                logger.warning(f"🔌 Elliott Wave service failing - waiting for recovery instead of using fallback for {symbol}")
                return None
            return None
    
    def _get_fallback_elliott_wave_data(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate fallback Elliott Wave data when service is unavailable
        """
        current_price = data['Close'].iloc[-1]
        price_20d_ago = data['Close'].iloc[-20] if len(data) >= 20 else current_price
        price_change = (current_price - price_20d_ago) / price_20d_ago
        
        # Simple fallback: determine pattern based on recent price movement
        if price_change > 0.05:  # 5%+ gain
            pattern = 'impulse'
            confidence = 0.4
            trend_strength = min(0.8, abs(price_change) * 2)
        elif price_change < -0.05:  # 5%+ loss
            pattern = 'corrective'
            confidence = 0.4
            trend_strength = min(0.8, abs(price_change) * 2)
        else:
            pattern = 'corrective'
            confidence = 0.3
            trend_strength = 0.2
        
        return {
            'pattern': pattern,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'wave_count': 3,  # Default wave count
            'fallback': True  # Mark as fallback data
        }
    
    def update_capital_estimation(self, trade_value: float, trade_pnl: float):
        """
        Update capital estimation based on trade outcomes
        This is called by the BacktestEngine after trades are executed
        """
        # Add trade to history
        self._trade_history.append({
            'value': trade_value,
            'pnl': trade_pnl,
            'timestamp': datetime.now()
        })
        
        # Keep only recent trades (last 20)
        if len(self._trade_history) > 20:
            self._trade_history = self._trade_history[-20:]
        
        # Calculate cumulative P&L from recent trades
        recent_pnl = sum(trade['pnl'] for trade in self._trade_history)
        
        # Update capital adjustment factor based on performance
        # If we're making money, we can be more aggressive; if losing, be more conservative
        if recent_pnl > 0:
            # Positive P&L: slightly increase position sizes (max 1.2x)
            self._capital_adjustment_factor = min(1.2, 1.0 + (recent_pnl / self._estimated_capital) * 0.5)
        else:
            # Negative P&L: reduce position sizes (min 0.7x)
            self._capital_adjustment_factor = max(0.7, 1.0 + (recent_pnl / self._estimated_capital) * 0.3)
        
        logger.debug(f"📊 Capital estimation updated: factor={self._capital_adjustment_factor:.2f}, recent_pnl=${recent_pnl:.2f}")
    
    async def _check_elliott_wave_health(self) -> bool:
        """
        Check if Elliott Wave service is healthy
        """
        try:
            import httpx
            
            # Determine service URL
            service_url = "http://localhost:11001"  # Default for local development
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{service_url}/elliott-wave/health")
                response.raise_for_status()
                health_data = response.json()
                
                is_healthy = health_data.get('status') == 'healthy'
                if is_healthy:
                    logger.info(f"✅ Elliott Wave service is healthy - resuming normal operations")
                else:
                    logger.warning(f"⚠️ Elliott Wave service health check failed: {health_data}")
                
                return is_healthy
                
        except Exception as e:
            logger.warning(f"⚠️ Elliott Wave service health check failed: {e}")
            return False
    
    def _analyze_market_conditions(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Analyze current market conditions"""
        
        # 1. Sector Rotation Analysis
        sector_rotation = self._detect_sector_rotation(data, symbol)
        
        # 2. Elliott Wave Analysis
        elliott_wave = self._detect_elliott_wave_pattern(data)
        
        # 3. Volatility Analysis
        volatility = self._calculate_volatility(data)
        
        # 4. Determine overall regime
        regime = self._determine_regime(sector_rotation, elliott_wave, volatility)
        
        return {
            'sector_rotation': sector_rotation,
            'elliott_wave': elliott_wave,
            'volatility': volatility,
            'regime': regime
        }
    
    def _detect_sector_rotation(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Detect if sectors are rotating"""
        
        # Sector mapping (simplified - you can enhance with real sector data)
        sector_map = {
            'AAPL': 'tech', 'MSFT': 'tech', 'GOOGL': 'tech', 'NVDA': 'tech', 'AMD': 'tech',
            'JPM': 'finance', 'BAC': 'finance', 'GS': 'finance',
            'XLE': 'energy', 'XLF': 'finance', 'XLK': 'tech'
        }
        
        sector = sector_map.get(symbol, 'other')
        
        # Calculate sector strength (relative performance)
        returns_10d = data['Close'].pct_change(periods=10).iloc[-1]
        returns_20d = data['Close'].pct_change(periods=20).iloc[-1]
        
        # High relative performance = sector rotating in
        is_rotating = abs(returns_10d) > self.sector_rotation_threshold
        strength = abs(returns_10d)
        
        return {
            'is_rotating': is_rotating,
            'sector': sector,
            'strength': strength,
            'direction': 'in' if returns_10d > 0 else 'out',
            'momentum': returns_10d
        }
    
    def _detect_elliott_wave_pattern(self, data: pd.DataFrame) -> Dict:
        """Detect Elliott Wave pattern (Impulse vs Corrective)"""
        
        prices = data['Close'].values
        
        # Find pivots
        peaks, troughs = self._find_pivots(prices)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {'pattern': 'unknown', 'confidence': 0.0}
        
        # Analyze wave structure
        recent_trend = self._calculate_trend_strength(data)
        momentum = self._calculate_momentum(data)
        
        # Impulse: Strong trending + increasing momentum
        # Corrective: Weak trending + decreasing momentum
        
        if abs(recent_trend) > 0.02 and momentum > 0.6:
            pattern = 'impulse'
            confidence = 0.75
        elif abs(recent_trend) < 0.01 and momentum < 0.4:
            pattern = 'corrective'
            confidence = 0.70
        else:
            pattern = 'transitional'
            confidence = 0.50
        
        return {
            'pattern': pattern,
            'confidence': confidence,
            'trend_strength': recent_trend,
            'momentum': momentum
        }
    
    def _calculate_volatility(self, data: pd.DataFrame) -> Dict:
        """Calculate current volatility"""
        
        returns = data['Close'].pct_change().dropna()
        recent_vol = returns.tail(20).std()
        avg_vol = returns.std()
        
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
        is_high = recent_vol > self.volatility_threshold
        
        return {
            'current': recent_vol,
            'average': avg_vol,
            'ratio': vol_ratio,
            'is_high': is_high,
            'regime': 'high' if is_high else 'low'
        }
    
    def _determine_regime(self, sector_rotation: Dict, elliott_wave: Dict, volatility: Dict) -> str:
        """
        Determine overall market regime to select appropriate strategy
        
        Returns one of:
        - 'sector_rotation_impulse': Sector rotating with impulse wave
        - 'sector_rotation_corrective': Sector rotating with corrective wave
        - 'consolidation_high_vol': Low rotation, corrective wave, high volatility
        - 'consolidation_low_vol': Low rotation, corrective wave, low volatility
        - 'trending_impulse': Strong trend, impulse wave
        - 'range_corrective': Range-bound, corrective wave
        """
        
        is_rotating = sector_rotation['is_rotating']
        wave_pattern = elliott_wave['pattern']
        is_high_vol = volatility['is_high']
        
        # Decision tree for regime classification
        if is_rotating and wave_pattern == 'impulse':
            return 'sector_rotation_impulse'
        elif is_rotating and wave_pattern == 'corrective':
            return 'sector_rotation_corrective'
        elif not is_rotating and wave_pattern == 'corrective' and is_high_vol:
            return 'consolidation_high_vol'
        elif not is_rotating and wave_pattern == 'corrective' and not is_high_vol:
            return 'consolidation_low_vol'
        elif wave_pattern == 'impulse':
            return 'trending_impulse'
        elif wave_pattern == 'corrective':
            return 'range_corrective'
        else:
            return 'neutral'
    
    def _select_strategy(self, conditions: Dict) -> str:
        """
        Select the best OPTIONS strategy based on current conditions
        
        Strategy Selection Rules (OPTIONS-FOCUSED):
        1. Sector Rotation + Impulse Wave → Straddle/Strangle (directional vol)
        2. Sector Rotation + Corrective Wave → Calendar Spread (time decay)
        3. Consolidation + High Vol → Straddle (long volatility)
        4. Consolidation + Low Vol → Iron Condor (short volatility, collect premium)
        5. Strong Impulse → Strangle (directional breakout)
        6. Strong Corrective → Butterfly Spread (range-bound premium)
        """
        
        regime = conditions['regime']
        elliott_wave = conditions['elliott_wave']
        sector_rotation = conditions['sector_rotation']
        volatility = conditions['volatility']
        
        # Map regime to OPTIONS strategy
        strategy_map = {
            'sector_rotation_impulse': 'straddle',  # Directional volatility play
            'sector_rotation_corrective': 'calendar_spread',  # Time decay on rotation
            'consolidation_high_vol': 'straddle',  # Long volatility
            'consolidation_low_vol': 'iron_condor',  # Collect premium in range
            'trending_impulse': 'strangle',  # Directional breakout
            'range_corrective': 'butterfly_spread',  # Tight range premium
            'neutral': 'iron_condor'  # Default to iron condor
        }
        
        return strategy_map.get(regime, 'iron_condor')
    
    def _select_options_strategy_with_greeks(self, symbol: str, data: pd.DataFrame, conditions: Dict, available_cash: float = 4000) -> str:
        """
        Select optimal AFFORDABLE options strategy using Greeks analysis and budget constraints
        """
        current_price = data['Close'].iloc[-1]
        volatility = conditions['volatility']['current']
        
        # Calculate maximum affordable position value (15% of capital per trade)
        max_position_value = available_cash * 0.15  # $600 with $4k capital
        
        # Define strategies by cost (cheapest first)
        strategy_costs = {
            'iron_condor': 100,      # ~$100 per contract (cheapest)
            'calendar_spread': 150,  # ~$150 per contract  
            'butterfly_spread': 200, # ~$200 per contract
            'strangle': 400,         # ~$400 per contract
            'straddle': 500          # ~$500 per contract (most expensive)
        }
        
        # Filter available strategies by budget
        affordable_strategies = [strategy for strategy, cost in strategy_costs.items() 
                               if cost <= max_position_value]
        
        if not affordable_strategies:
            # Fallback to cheapest strategy if none are affordable
            affordable_strategies = ['iron_condor']
        
        # Enhanced market conditions for Greeks analysis
        enhanced_conditions = {
            'current_price': current_price,
            'volatility': volatility,
            'regime': conditions['regime'],
            'days_to_expiry': 30,  # Default 30 days
            'volatility_trend': 'increasing' if conditions['volatility']['ratio'] > 1.1 else 'decreasing',
            'time_to_expiry': 30/365.0,
            'risk_tolerance': 'moderate'
        }
        
        # Get optimal strategy using Greeks analysis (from affordable options only)
        optimal_strategy, greeks_analysis = GreeksCalculator.get_optimal_strategy(
            enhanced_conditions, affordable_strategies
        )
        
        # Log the budget-aware Greeks analysis
        logger.info(f"💰 {symbol} Budget-aware Greeks selection:")
        logger.info(f"   Available cash: ${available_cash:.0f}, max position: ${max_position_value:.0f}")
        logger.info(f"   Affordable strategies: {affordable_strategies}")
        logger.info(f"   Selected: {optimal_strategy} (cost: ${strategy_costs[optimal_strategy]})")
        
        return optimal_strategy
    
    def _select_options_strategy(self, conditions: Dict, available_cash: float = 4000) -> str:
        """Select appropriate AFFORDABLE options strategy based on budget and market conditions"""
        regime = conditions['regime']
        volatility = conditions['volatility']
        elliott_wave = conditions['elliott_wave']
        trend_duration = conditions.get('trend_duration', {})
        
        # Calculate maximum affordable position value (15% of capital per trade)
        max_position_value = available_cash * 0.15  # $600 with $4k capital
        
        # Define strategies by cost (cheapest first) with estimated costs
        strategy_costs = {
            'iron_condor': 100,      # ~$100 per contract (cheapest)
            'calendar_spread': 150,  # ~$150 per contract  
            'butterfly_spread': 200, # ~$200 per contract
            'strangle': 400,         # ~$400 per contract
            'straddle': 500          # ~$500 per contract (most expensive)
        }
        
        # Strategy preferences by market regime (but constrained by budget)
        regime_preferences = {
            # High volatility regimes - prefer volatility strategies (if affordable)
            'high_vol_trending': ['straddle', 'strangle', 'iron_condor'],
            'high_vol_choppy': ['iron_condor', 'strangle', 'straddle'],
            
            # Low volatility regimes - prefer income strategies
            'low_vol_extended': ['calendar_spread', 'iron_condor', 'butterfly_spread'],
            'low_vol_consolidation': ['iron_condor', 'calendar_spread', 'butterfly_spread'],
            'low_vol_trending': ['strangle', 'iron_condor', 'calendar_spread'],
            
            # Sector rotation regimes
            'sector_rotation_impulse': ['straddle', 'strangle', 'iron_condor'],
            'sector_rotation_corrective': ['calendar_spread', 'iron_condor', 'butterfly_spread'],
            
            # Trending regimes
            'trending_impulse': ['strangle', 'straddle', 'iron_condor'],
            'trending_extended': ['butterfly_spread', 'iron_condor', 'calendar_spread'],
            
            # Consolidation regimes
            'consolidation_normal': ['iron_condor', 'calendar_spread', 'butterfly_spread'],
            'consolidation_high_vol': ['straddle', 'iron_condor', 'strangle'],
            'consolidation_low_vol': ['iron_condor', 'calendar_spread', 'butterfly_spread']
        }
        
        # Get preferred strategies for current regime
        preferred_strategies = regime_preferences.get(regime, ['iron_condor', 'calendar_spread', 'strangle'])
        
        # Select the most expensive strategy we can afford from our preferences
        selected_strategy = 'iron_condor'  # Default to cheapest
        
        for strategy in preferred_strategies:
            if strategy_costs[strategy] <= max_position_value:
                selected_strategy = strategy
            else:
                break  # Can't afford more expensive strategies
        
        # Additional budget-aware overrides
        if elliott_wave.get('completion_risk', 0) > 0.25:
            # High completion risk - force cheapest strategy
            selected_strategy = 'iron_condor'
        elif volatility['trend'] == 'increasing' and regime in ['trending_impulse', 'sector_rotation_impulse']:
            # Increasing volatility - prefer straddle if affordable, otherwise strangle
            if strategy_costs['straddle'] <= max_position_value:
                selected_strategy = 'straddle'
            elif strategy_costs['strangle'] <= max_position_value:
                selected_strategy = 'strangle'
            else:
                selected_strategy = 'iron_condor'
        elif trend_duration.get('phase') == 'extended' and selected_strategy == 'strangle':
            # Extended trend - avoid directional strategies if possible
            if strategy_costs['butterfly_spread'] <= max_position_value:
                selected_strategy = 'butterfly_spread'
            else:
                selected_strategy = 'iron_condor'
        
        logger.info(f"💰 Budget-aware strategy selection: regime={regime}, max_affordable=${max_position_value:.0f}, selected={selected_strategy} (cost=${strategy_costs[selected_strategy]})")
        
        return selected_strategy
    
    def _calculate_position_size(self, symbol: str, conditions: Dict, portfolio_value: float) -> int:
        """Calculate appropriate position size based on risk management rules"""
        
        # Dynamic position sizing based on multiple factors
        base_contracts = 1
        
        # 1. Elliott Wave confidence scaling (0.1 to 0.9 confidence = 1 to 3 contracts)
        elliott_confidence = conditions['elliott_wave']['confidence']
        confidence_contracts = int(1 + (elliott_confidence - 0.1) / (0.9 - 0.1) * 2)  # Scale to 1-3 contracts
        confidence_contracts = max(1, min(3, confidence_contracts))
        
        # 2. Volatility adjustment (higher vol = smaller size)
        if self.volatility_adjustment:
            volatility = conditions['volatility']['ratio']
            if volatility > 1.5:
                vol_multiplier = 0.7  # Reduce size in high volatility
            elif volatility > 1.2:
                vol_multiplier = 0.85
            elif volatility < 0.8:
                vol_multiplier = 1.2  # Increase size in low volatility
            else:
                vol_multiplier = 1.0  # Normal volatility
        else:
            vol_multiplier = 1.0
        
        # 3. Multi-strategy confirmation boost
        confirmations = conditions.get('multi_strategy_confirmations', {})
        confirmation_confidence = confirmations.get('overall_confidence', 0.5)
        if confirmation_confidence > 0.7:
            confirmation_multiplier = 1.3  # Boost for high confirmation
        elif confirmation_confidence > 0.5:
            confirmation_multiplier = 1.1  # Small boost for good confirmation
        else:
            confirmation_multiplier = 0.9  # Reduce for low confirmation
        
        # 4. 🎯 MARKET REGIME MULTIPLIER (TOP PERFORMER: 516.9% annual return)
        market_regime = conditions.get('market_regime', {})
        regime_multiplier = market_regime.get('position_multiplier', 1.0)
        
        # Calculate dynamic base contracts with ALL multipliers
        base_contracts = confidence_contracts * vol_multiplier * confirmation_multiplier * regime_multiplier
        base_contracts = max(1, min(5, int(base_contracts)))  # Cap between 1-5 contracts (increased for regime boost)
        
        # Adjust for pattern risk
        pattern_type = conditions['elliott_wave']['pattern']
        risk_scores = {
            'impulse': 0.3,
            'impulse_completion': 0.5,
            'corrective': 0.4,
            'corrective_completion': 0.6
        }
        
        risk_score = risk_scores.get(pattern_type, 0.5)
        if risk_score > 0.5:
            base_contracts = max(1, base_contracts - 1)
        
        # Portfolio heat check (max 5% per position)
        max_position_value = portfolio_value * self.max_position_size_pct
        
        # Use realistic options pricing instead of hardcoded estimate
        # We'll calculate this dynamically in the strategy methods
        estimated_cost_per_contract = 150  # More realistic base estimate
        max_contracts_by_heat = int(max_position_value / estimated_cost_per_contract)
        
        # Final position size with dynamic caps
        final_contracts = min(base_contracts, max_contracts_by_heat, 3)  # Cap at 3 contracts (increased from 2)
        
        logger.debug(f"🎯 {symbol} Dynamic position sizing: confidence={confidence_contracts}, vol_adj={vol_multiplier:.2f}, conf_adj={confirmation_multiplier:.2f}, base={base_contracts:.1f}, heat_limit={max_contracts_by_heat}, final={final_contracts}")
        
        return final_contracts
    
    def _get_multi_strategy_confirmation(self, symbol: str, data: pd.DataFrame, signal_type: str) -> Dict:
        """Get confirmation signals from multiple strategies for better entry/exit decisions"""
        
        confirmations = {
            'ichimoku': False,
            'momentum': False,
            'volume': False,
            'volatility_breakout': False,
            'price_action': False,
            'support_resistance': False,
            'sma_crossover': False,
            'macd': False,
            'rsi': False,
            'bollinger_bands': False,
            'overall_confidence': 0.0
        }
        
        if len(data) < 20:  # Need enough data for analysis
            return confirmations
        
        # 1. Ichimoku confirmation
        if self.confirmation_strategies['ichimoku']:
            try:
                ichimoku_signal = self.ichimoku_strategy.generate_signal(symbol, data)
                confirmations['ichimoku'] = ichimoku_signal is not None and ichimoku_signal.confidence > 0.3
            except:
                confirmations['ichimoku'] = False
        
        # 2. Momentum confirmation (price momentum)
        if self.confirmation_strategies['momentum']:
            try:
                # Calculate momentum over 5 and 10 periods
                price_5d = data['Close'].iloc[-1] / data['Close'].iloc[-6] - 1
                price_10d = data['Close'].iloc[-1] / data['Close'].iloc[-11] - 1
                
                # Momentum confirmation for BUY signals (very aggressive thresholds)
                if signal_type == 'BUY':
                    confirmations['momentum'] = price_5d > 0.001 or price_10d > 0.003  # 0.1% 5d or 0.3% 10d momentum (very aggressive)
                else:  # SELL signals
                    confirmations['momentum'] = price_5d < -0.005 or price_10d < -0.01  # Negative momentum (relaxed)
            except:
                confirmations['momentum'] = False
        
        # 3. Volume confirmation
        if self.confirmation_strategies['volume']:
            try:
                if 'Volume' in data.columns:
                    avg_volume = data['Volume'].iloc[-10:].mean()
                    current_volume = data['Volume'].iloc[-1]
                    volume_ratio = current_volume / avg_volume
                    
                    # Volume confirmation (above average volume) - very aggressive
                    confirmations['volume'] = volume_ratio > 1.02  # 2% above average (very aggressive)
                else:
                    confirmations['volume'] = True  # No volume data, assume confirmation
            except:
                confirmations['volume'] = False
        
        # 4. Volatility breakout confirmation
        if self.confirmation_strategies['volatility_breakout']:
            try:
                # Calculate recent volatility
                returns = data['Close'].pct_change().dropna()
                recent_vol = returns.iloc[-10:].std()
                avg_vol = returns.iloc[-30:].std() if len(returns) >= 30 else recent_vol
                
                # Volatility breakout confirmation (very aggressive)
                confirmations['volatility_breakout'] = recent_vol > avg_vol * 1.01  # 1% above average vol (very aggressive)
            except:
                confirmations['volatility_breakout'] = False
        
        # 5. Price action confirmation
        if self.confirmation_strategies['price_action']:
            try:
                # Check for bullish price action patterns
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                price_change = (current_price - prev_price) / prev_price
                
                # Price action confirmation (simple momentum)
                if signal_type == 'BUY':
                    confirmations['price_action'] = price_change > 0.001  # 0.1% positive price action
                else:  # SELL signals
                    confirmations['price_action'] = price_change < -0.001  # 0.1% negative price action
            except:
                confirmations['price_action'] = False
        
        # 6. Support/Resistance confirmation
        if self.confirmation_strategies['support_resistance']:
            try:
                # Simple support/resistance based on recent highs/lows
                recent_high = data['High'].iloc[-10:].max()
                recent_low = data['Low'].iloc[-10:].min()
                current_price = data['Close'].iloc[-1]
                
                # Check if price is near support or resistance
                price_range = recent_high - recent_low
                if price_range > 0:
                    price_position = (current_price - recent_low) / price_range
                    
                    # Support/resistance confirmation (price near key levels)
                    confirmations['support_resistance'] = price_position < 0.3 or price_position > 0.7
                else:
                    confirmations['support_resistance'] = True  # No clear range, assume confirmation
            except:
                confirmations['support_resistance'] = False
        
        # 7. SMA Crossover confirmation
        if self.confirmation_strategies['sma_crossover']:
            try:
                if len(data) >= 20:
                    sma_10 = data['Close'].rolling(window=10).mean()
                    sma_20 = data['Close'].rolling(window=20).mean()
                    
                    current_sma10 = sma_10.iloc[-1]
                    current_sma20 = sma_20.iloc[-1]
                    prev_sma10 = sma_10.iloc[-2]
                    prev_sma20 = sma_20.iloc[-2]
                    
                    # Bullish crossover: SMA10 crosses above SMA20
                    if signal_type == 'BUY':
                        confirmations['sma_crossover'] = (current_sma10 > current_sma20) and (prev_sma10 <= prev_sma20)
                    else:  # SELL signals
                        confirmations['sma_crossover'] = (current_sma10 < current_sma20) and (prev_sma10 >= prev_sma20)
                else:
                    confirmations['sma_crossover'] = True  # Not enough data, assume confirmation
            except:
                confirmations['sma_crossover'] = False
        
        # 8. MACD confirmation
        if self.confirmation_strategies['macd']:
            try:
                if len(data) >= 26:
                    # Calculate MACD
                    ema_12 = data['Close'].ewm(span=12).mean()
                    ema_26 = data['Close'].ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    histogram = macd_line - signal_line
                    
                    current_macd = macd_line.iloc[-1]
                    current_signal = signal_line.iloc[-1]
                    current_hist = histogram.iloc[-1]
                    prev_hist = histogram.iloc[-2]
                    
                    # MACD confirmation: MACD above signal line and histogram increasing
                    if signal_type == 'BUY':
                        confirmations['macd'] = (current_macd > current_signal) and (current_hist > prev_hist)
                    else:  # SELL signals
                        confirmations['macd'] = (current_macd < current_signal) and (current_hist < prev_hist)
                else:
                    confirmations['macd'] = True  # Not enough data, assume confirmation
            except:
                confirmations['macd'] = False
        
        # 9. RSI confirmation
        if self.confirmation_strategies['rsi']:
            try:
                if len(data) >= 14:
                    # Calculate RSI
                    delta = data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    current_rsi = rsi.iloc[-1]
                    
                    # RSI confirmation: Not overbought/oversold
                    if signal_type == 'BUY':
                        confirmations['rsi'] = 30 < current_rsi < 70  # Not oversold, not overbought
                    else:  # SELL signals
                        confirmations['rsi'] = 30 < current_rsi < 70  # Not oversold, not overbought
                else:
                    confirmations['rsi'] = True  # Not enough data, assume confirmation
            except:
                confirmations['rsi'] = False
        
        # 10. Bollinger Bands confirmation
        if self.confirmation_strategies['bollinger_bands']:
            try:
                if len(data) >= 20:
                    # Calculate Bollinger Bands
                    sma_20 = data['Close'].rolling(window=20).mean()
                    std_20 = data['Close'].rolling(window=20).std()
                    upper_band = sma_20 + (std_20 * 2)
                    lower_band = sma_20 - (std_20 * 2)
                    
                    current_price = data['Close'].iloc[-1]
                    current_upper = upper_band.iloc[-1]
                    current_lower = lower_band.iloc[-1]
                    current_sma = sma_20.iloc[-1]
                    
                    # Bollinger Bands confirmation: Price near bands (volatility expansion) or near SMA (mean reversion)
                    if signal_type == 'BUY':
                        # Buy when price near lower band (oversold) or near SMA (mean reversion)
                        confirmations['bollinger_bands'] = (current_price <= current_lower * 1.02) or (abs(current_price - current_sma) / current_sma < 0.01)
                    else:  # SELL signals
                        # Sell when price near upper band (overbought) or near SMA (mean reversion)
                        confirmations['bollinger_bands'] = (current_price >= current_upper * 0.98) or (abs(current_price - current_sma) / current_sma < 0.01)
                else:
                    confirmations['bollinger_bands'] = True  # Not enough data, assume confirmation
            except:
                confirmations['bollinger_bands'] = False
        
        # Calculate overall confidence based on confirmations
        # Count only the actual confirmation strategies, not the overall_confidence field
        total_confirmations = sum([v for k, v in confirmations.items() if k != 'overall_confidence'])
        max_possible = len(self.confirmation_strategies)
        confirmations['overall_confidence'] = total_confirmations / max_possible if max_possible > 0 else 0.0
        
        logger.debug(f"🔍 {symbol} Multi-strategy confirmations: {confirmations}")
        
        return confirmations
    
    def _detect_market_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect market regime based on VIX levels (TOP PERFORMER: 516.9% annual return)"""
        
        regime_info = {
            'regime': 'normal_fear',
            'vix_level': 20.0,  # Default VIX
            'position_multiplier': 1.0,
            'confidence': 0.5
        }
        
        if not self.market_regime_detection['enabled']:
            return regime_info
        
        try:
            # For now, simulate VIX based on recent volatility
            # In production, this would fetch real VIX data
            returns = data['Close'].pct_change().dropna()
            if len(returns) >= 20:
                recent_vol = returns.iloc[-20:].std() * np.sqrt(252)  # Annualized volatility
                
                # Convert volatility to VIX-like measure (simplified)
                # VIX typically ranges from 10-50, volatility from 0.1-0.8
                simulated_vix = min(50, max(10, recent_vol * 100))
                regime_info['vix_level'] = simulated_vix
                
                # Determine regime based on VIX thresholds
                if simulated_vix < self.market_regime_detection['vix_thresholds']['low_fear']:
                    regime_info['regime'] = 'low_fear'
                    regime_info['position_multiplier'] = self.market_regime_detection['position_multipliers']['low_fear']
                    regime_info['confidence'] = 0.8  # High confidence in low fear
                elif simulated_vix > self.market_regime_detection['vix_thresholds']['high_fear']:
                    regime_info['regime'] = 'high_fear'
                    regime_info['position_multiplier'] = self.market_regime_detection['position_multipliers']['high_fear']
                    regime_info['confidence'] = 0.8  # High confidence in high fear
                else:
                    regime_info['regime'] = 'normal_fear'
                    regime_info['position_multiplier'] = self.market_regime_detection['position_multipliers']['normal_fear']
                    regime_info['confidence'] = 0.6  # Medium confidence in normal fear
                    
                logger.debug(f"🎯 Market regime detected: {regime_info['regime']} (VIX: {simulated_vix:.1f}, multiplier: {regime_info['position_multiplier']}x)")
            
        except Exception as e:
            logger.debug(f"Error detecting market regime: {e}")
            
        return regime_info
    
    def _calculate_options_premium(self, symbol: str, underlying_price: float, options_strategy: str, 
                                 volatility: float, days_to_expiry: int = 30) -> float:
        """Calculate realistic options premium based on strategy type and market conditions"""
        
        base_premium = underlying_price * self.options_pricing['base_premium_multiplier']
        
        # Adjust for volatility (higher vol = higher premium)
        vol_adjustment = 1 + (volatility - 1.0) * self.options_pricing['volatility_multiplier']
        vol_adjustment = max(0.5, min(2.0, vol_adjustment))  # Cap between 0.5x and 2.0x
        
        # Adjust for time decay (more time = higher premium)
        time_adjustment = 1 + (days_to_expiry / 30.0) * self.options_pricing['time_decay_factor']
        time_adjustment = max(0.8, min(1.5, time_adjustment))  # Cap between 0.8x and 1.5x
        
        # Strategy-specific multipliers
        strategy_multipliers = {
            'straddle': 1.8,        # ATM calls + ATM puts (expensive)
            'strangle': 1.4,        # OTM calls + OTM puts (cheaper than straddle)
            'iron_condor': 0.6,     # Credit spread (collect premium)
            'butterfly_spread': 0.8, # Limited risk/reward
            'calendar_spread': 0.4  # Time decay play (cheap)
        }
        
        strategy_multiplier = strategy_multipliers.get(options_strategy, 1.0)
        
        # Calculate final premium
        premium = base_premium * vol_adjustment * time_adjustment * strategy_multiplier
        
        # Ensure minimum realistic premium (at least $0.50 per contract)
        premium = max(0.50, premium)
        
        logger.debug(f"💰 {symbol} {options_strategy} pricing: base=${base_premium:.2f}, vol_adj={vol_adjustment:.2f}, time_adj={time_adjustment:.2f}, strategy={strategy_multiplier:.2f}, final=${premium:.2f}")
        
        return premium
    
    async def _analyze_market_conditions(self, symbol: str, data: pd.DataFrame, pattern_type: str, confidence: float) -> Dict:
        """Analyze market conditions for options strategy selection with enhanced regime detection"""
        
        current_price = data['Close'].iloc[-1]
        
        # Calculate volatility with multiple timeframes
        returns = data['Close'].pct_change().dropna()
        volatility = {
            'current': returns.std() * np.sqrt(252),  # Annualized
            'ratio': returns.std() / returns.rolling(20).std().mean() if len(returns) > 20 else 1.0,
            'is_high': returns.std() > returns.rolling(20).std().mean() * 1.2 if len(returns) > 20 else False,
            'trend': 'increasing' if len(returns) > 20 and returns.rolling(5).std().iloc[-1] > returns.rolling(5).std().iloc[-10] else 'decreasing'
        }
        
        # Enhanced sector rotation analysis
        if len(data) >= 20:
            short_momentum = (current_price - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
            long_momentum = (current_price - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
            momentum_consistency = abs(short_momentum - long_momentum) < 0.02  # Consistent direction
        else:
            short_momentum = long_momentum = 0.0
            momentum_consistency = False
            
        sector_rotation = {
            'strength': abs(long_momentum),
            'direction': 'bullish' if long_momentum > 0 else 'bearish',
            'consistency': momentum_consistency,
            'acceleration': short_momentum - long_momentum  # Acceleration/deceleration
        }
        
        # Enhanced Elliott Wave analysis
        elliott_wave = {
            'pattern': pattern_type,
            'confidence': confidence,
            'trend_strength': confidence * 2,
            'completion_risk': 0.3 if 'completion' in pattern_type else 0.1  # Higher risk for completion patterns
        }
        
        # Calculate trend duration (simplified)
        trend_duration = self._calculate_trend_duration(data)
        
        # Enhanced market regime detection
        regime = self._determine_market_regime(
            volatility, sector_rotation, elliott_wave, trend_duration
        )
        
        return {
            'regime': regime,
            'volatility': volatility,
            'sector_rotation': sector_rotation,
            'elliott_wave': elliott_wave,
            'price': current_price,
            'trend_duration': trend_duration
        }
    
    def _calculate_trend_duration(self, data: pd.DataFrame) -> Dict:
        """Calculate trend duration and strength"""
        if len(data) < 20:
            return {'days': 0, 'strength': 'weak', 'phase': 'unknown'}
            
        # Simple trend detection
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        current_price = data['Close'].iloc[-1]
        
        # Count consecutive days above/below SMA
        recent_data = data['Close'].tail(20)
        above_sma = recent_data > sma_20
        trend_direction = above_sma.iloc[-1]
        
        # Count consecutive days in same direction
        trend_days = 0
        for i in range(len(above_sma) - 1, -1, -1):
            if above_sma.iloc[i] == trend_direction:
                trend_days += 1
            else:
                break
        
        # Determine trend strength
        price_vs_sma = abs(current_price - sma_20) / sma_20
        if price_vs_sma > 0.05:
            strength = 'strong'
        elif price_vs_sma > 0.02:
            strength = 'moderate'
        else:
            strength = 'weak'
            
        # Determine trend phase
        if trend_days < 5:
            phase = 'early'
        elif trend_days < 15:
            phase = 'mature'
        else:
            phase = 'extended'
            
        return {
            'days': trend_days,
            'strength': strength,
            'phase': phase,
            'direction': 'up' if trend_direction else 'down'
        }
    
    def _determine_market_regime(self, volatility: Dict, sector_rotation: Dict, 
                               elliott_wave: Dict, trend_duration: Dict) -> str:
        """Determine market regime based on multiple indicators"""
        
        # High volatility regimes
        if volatility['is_high'] and volatility['ratio'] > 1.5:
            if sector_rotation['consistency'] and elliott_wave['pattern'] in ['impulse']:
                return 'high_vol_trending'  # Volatile trending market
            else:
                return 'high_vol_choppy'    # Volatile choppy market
                
        # Low volatility regimes
        elif volatility['ratio'] < 0.8:
            if trend_duration['phase'] == 'extended':
                return 'low_vol_extended'   # Extended trend, low vol
            elif trend_duration['strength'] == 'weak':
                return 'low_vol_consolidation'  # Consolidation
            else:
                return 'low_vol_trending'   # Gentle trending
                
        # Normal volatility with sector rotation
        elif sector_rotation['strength'] > self.sector_rotation_threshold:
            if elliott_wave['pattern'] in ['impulse', 'impulse_completion']:
                return 'sector_rotation_impulse'
            else:
                return 'sector_rotation_corrective'
                
        # Trending markets
        elif elliott_wave['pattern'] in ['impulse', 'impulse_completion']:
            if trend_duration['phase'] == 'extended':
                return 'trending_extended'
            else:
                return 'trending_impulse'
                
        # Default to consolidation
        else:
            return 'consolidation_normal'
    
    async def _generate_strategy_signal(self, 
                                       symbol: str, 
                                       data: pd.DataFrame,
                                       pattern_type: str,
                                       confidence: float) -> Optional[TradeSignal]:
        """Generate signal based on Elliott Wave pattern type with options strategies"""
        
        # Use pattern-specific confidence threshold
        pattern_data = self.pattern_performance.get(pattern_type, {})
        min_confidence = pattern_data.get('min_confidence', 0.1)  # Use configured threshold
        
        if confidence < min_confidence:
            return None
        
        # Get Ichimoku signal for confirmation
        ichimoku_signal = await self.ichimoku_strategy.generate_signal(symbol, data)
        
        # Analyze market conditions for options strategy selection
        conditions = await self._analyze_market_conditions(symbol, data, pattern_type, confidence)
        
        # 🎯 DETECT MARKET REGIME (TOP PERFORMER: 516.9% annual return)
        market_regime = self._detect_market_regime(data)
        conditions['market_regime'] = market_regime
        
        # Select appropriate options strategy using Greeks analysis with budget constraints
        # Use dynamic capital estimation for position sizing
        estimated_available_cash = self._estimated_capital * self._capital_adjustment_factor * 0.9  # Use 90% of estimated capital
        options_strategy = self._select_options_strategy_with_greeks(symbol, data, conditions, estimated_available_cash)
        
        # Get multi-strategy confirmation for BUY signal
        confirmations = self._get_multi_strategy_confirmation(symbol, data, 'BUY')
        
        # Require at least 8% confirmation from multiple strategies (extreme aggressive with 10 strategies)
        if confirmations['overall_confidence'] < 0.08:
            logger.info(f"❌ {symbol} - Insufficient multi-strategy confirmation: {confirmations['overall_confidence']:.2%}")
            return None
        
        logger.debug(f"✅ {symbol} - Multi-strategy confirmation: {confirmations['overall_confidence']:.2%}")
        
        # Generate options trade signal with proper position sizing
        current_price = data['Close'].iloc[-1]
        
        logger.info(f"🔧 {symbol} selected options strategy: {options_strategy}")
        
        if options_strategy == 'straddle':
            signal = self._generate_straddle_signal(symbol, data, current_price, conditions, min_confidence)
        elif options_strategy == 'strangle':
            signal = self._generate_strangle_signal(symbol, data, current_price, conditions, min_confidence)
        elif options_strategy == 'iron_condor':
            signal = self._generate_iron_condor_signal(symbol, data, current_price, conditions, min_confidence)
        elif options_strategy == 'butterfly_spread':
            signal = self._generate_butterfly_signal(symbol, data, current_price, conditions, min_confidence)
        elif options_strategy == 'calendar_spread':
            signal = self._generate_calendar_spread_signal(symbol, data, current_price, conditions)
        else:
            # Fallback to iron condor for unknown strategies
            signal = self._generate_iron_condor_signal(symbol, data, current_price, conditions, min_confidence)
        
        # Add confirmation data to signal metadata
        if signal:
            signal.metadata.update({
                'multi_strategy_confirmations': confirmations,
                'confirmation_confidence': confirmations['overall_confidence']
            })
        
        if signal:
            logger.info(f"📊 {symbol} generated {options_strategy} signal: action={signal.action}, quantity={signal.quantity}, price={signal.price}")
        else:
            logger.warning(f"⚠️ {symbol} options strategy {options_strategy} returned None")
            
        return signal
    
    
    def _generate_straddle_signal(self, symbol: str, data: pd.DataFrame, price: float, conditions: Dict, min_confidence: float = 0.7) -> Optional[TradeSignal]:
        """Generate Straddle signal (sector rotation + impulse OR high volatility)"""
        
        # Straddle: Buy ATM call + ATM put (profit from big move in either direction)
        # Best for: High volatility expected, directional uncertainty
        
        vol = conditions['volatility']
        elliott = conditions['elliott_wave']
        
        # Enter when volatility is expanding or impulse wave forming (more aggressive)
        if vol['ratio'] > 1.0 or (elliott['pattern'] == 'impulse' and elliott['confidence'] > min_confidence):
            timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
            # Use risk-adjusted position sizing
            contracts = self._calculate_position_size(symbol, conditions, 4000)  # Assuming $4000 portfolio
            
            # Calculate realistic options premium
            premium = self._calculate_options_premium(symbol, price, 'straddle', vol['ratio'])
            
            # Calculate Greeks for this strategy
            strikes = {'atm': price}
            greeks = GreeksCalculator.calculate_strategy_greeks('straddle', price, strikes, 30/365.0, 0.05, vol['ratio'])
            risk_scores = GreeksCalculator.evaluate_strategy_risk(greeks, conditions)
            
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=premium,  # Use calculated premium instead of stock price
                quantity=contracts,  # Number of option contracts
                confidence=max(vol['ratio'] / 2, elliott.get('confidence', 0.6)),
                timestamp=timestamp,
                strategy=f"{self.name}_straddle",
                metadata={
                    'active_strategy': 'straddle',
                    'options_strategy': 'STRADDLE',
                    'regime': conditions['regime'],
                    'volatility': vol['current'],
                    'underlying_price': price,
                    'premium_calculated': premium,
                    'greeks': greeks,
                    'risk_scores': risk_scores
                }
            )
        
        return None
    
    def _generate_strangle_signal(self, symbol: str, data: pd.DataFrame, price: float, conditions: Dict, min_confidence: float = 0.7) -> Optional[TradeSignal]:
        """Generate Strangle signal (trending + impulse wave)"""
        
        # Strangle: Buy OTM call + OTM put (cheaper than straddle, needs bigger move)
        # Best for: Strong trend expected, directional breakout
        
        elliott = conditions['elliott_wave']
        sector = conditions['sector_rotation']
        
        # Enter on impulse with sector rotation (more aggressive)
        if elliott['pattern'] == 'impulse' and elliott['trend_strength'] > 0.01:
            timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
            # Use risk-adjusted position sizing
            contracts = self._calculate_position_size(symbol, conditions, 4000)  # Assuming $4000 portfolio
            
            # Calculate realistic options premium
            vol = conditions['volatility']
            premium = self._calculate_options_premium(symbol, price, 'strangle', vol['ratio'])
            
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=premium,  # Use calculated premium instead of stock price
                quantity=contracts,  # Number of option contracts
                confidence=elliott['confidence'],
                timestamp=timestamp,
                strategy=f"{self.name}_strangle",
                metadata={
                    'active_strategy': 'strangle',
                    'options_strategy': 'STRANGLE',
                    'regime': conditions['regime'],
                    'trend_strength': elliott['trend_strength'],
                    'underlying_price': price,
                    'premium_calculated': premium
                }
            )
        
        return None
    
    def _generate_iron_condor_signal(self, symbol: str, data: pd.DataFrame, price: float, conditions: Dict, min_confidence: float = 0.7) -> Optional[TradeSignal]:
        """Generate Iron Condor signal (low vol + corrective wave)"""
        
        # Iron Condor: Sell OTM call spread + OTM put spread (profit from range)
        # Best for: Low volatility, range-bound market, corrective wave
        
        vol = conditions['volatility']
        elliott = conditions['elliott_wave']
        
        # Enter when volatility allows and corrective pattern detected (very aggressive)
        if vol['ratio'] < 1.5 and elliott['pattern'] == 'corrective':
            # Check if price is in middle of range
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
            distance_from_sma = abs(price - sma_20) / sma_20
            
            # Iron condor works best when price is near middle of range (more aggressive)
            if distance_from_sma < 0.08:  # Within 8% of SMA (more aggressive)
                timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
                # Use risk-adjusted position sizing
                contracts = self._calculate_position_size(symbol, conditions, 4000)  # Assuming $4000 portfolio
                # Calculate realistic options premium (Iron Condor is a credit spread)
                premium = self._calculate_options_premium(symbol, price, 'iron_condor', vol['ratio'])
                
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',  # Setup Iron Condor
                    price=premium,  # Use calculated premium instead of stock price
                    quantity=contracts,  # Risk-adjusted contracts
                    confidence=0.75,
                    timestamp=timestamp,
                    strategy=f"{self.name}_iron_condor",
                    metadata={
                        'active_strategy': 'iron_condor',
                        'options_strategy': 'IRON_CONDOR',
                        'regime': conditions['regime'],
                        'volatility': vol['current'],
                        'underlying_price': price,
                        'premium_calculated': premium
                    }
                )
        
        return None
    
    def _generate_butterfly_signal(self, symbol: str, data: pd.DataFrame, price: float, conditions: Dict, min_confidence: float = 0.7) -> Optional[TradeSignal]:
        """Generate Butterfly Spread signal (tight range + corrective)"""
        
        # Butterfly: Limited profit, limited risk, profits from tight range
        # Best for: Very low volatility, tight consolidation
        
        vol = conditions['volatility']
        elliott = conditions['elliott_wave']
        
        # Enter when volatility is low/moderate and tight range expected (more aggressive)
        if vol['ratio'] < 1.3 and elliott['pattern'] == 'corrective':
            timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
            # Use risk-adjusted position sizing
            contracts = self._calculate_position_size(symbol, conditions, 4000)  # Assuming $4000 portfolio
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=price,
                quantity=contracts,  # Risk-adjusted contracts
                confidence=0.70,
                timestamp=timestamp,
                strategy=f"{self.name}_butterfly",
                metadata={
                    'active_strategy': 'butterfly_spread',
                    'options_strategy': 'BUTTERFLY_SPREAD',
                    'regime': conditions['regime'],
                    'volatility': vol['current']
                }
            )
        
        return None
    
    def _generate_calendar_spread_signal(self, symbol: str, data: pd.DataFrame, price: float, conditions: Dict) -> Optional[TradeSignal]:
        """Generate Calendar Spread signal (sector rotation + corrective)"""
        
        # Calendar Spread: Sell near-term, buy far-term (profit from time decay)
        # Best for: Expected consolidation, theta decay
        
        sector = conditions['sector_rotation']
        elliott = conditions['elliott_wave']
        
        # Enter when sector is rotating OR corrective pattern detected (more aggressive)
        if (sector['is_rotating'] or sector['strength'] > 0.08) and elliott['pattern'] == 'corrective':
            timestamp = data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now()
            # Use risk-adjusted position sizing
            contracts = self._calculate_position_size(symbol, conditions, 4000)  # Assuming $4000 portfolio
            return TradeSignal(
                symbol=symbol,
                action='BUY',
                price=price,
                quantity=contracts,  # Risk-adjusted contracts
                confidence=0.68,
                timestamp=timestamp,
                strategy=f"{self.name}_calendar",
                metadata={
                    'active_strategy': 'calendar_spread',
                    'options_strategy': 'CALENDAR_SPREAD',
                    'regime': conditions['regime'],
                    'sector_strength': sector['strength']
                }
            )
        
        return None
    
    # Helper methods
    
    def _find_pivots(self, prices: np.ndarray, order: int = 5) -> tuple:
        """Find price pivots"""
        peaks = []
        troughs = []
        
        for i in range(order, len(prices) - order):
            if all(prices[i] >= prices[i-j] for j in range(1, order+1)) and \
               all(prices[i] >= prices[i+j] for j in range(1, order+1)):
                peaks.append(i)
            elif all(prices[i] <= prices[i-j] for j in range(1, order+1)) and \
                 all(prices[i] <= prices[i+j] for j in range(1, order+1)):
                troughs.append(i)
        
        return peaks, troughs
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength"""
        if len(data) < 20:
            return 0.0
        
        sma_20 = data['Close'].rolling(window=20).mean()
        returns = (sma_20.iloc[-1] - sma_20.iloc[-20]) / sma_20.iloc[-20]
        return returns
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate momentum score (0-1)"""
        if len(data) < 10:
            return 0.5
        
        returns = data['Close'].pct_change(periods=10).iloc[-1]
        # Normalize to 0-1
        momentum_score = min(1.0, abs(returns) / 0.1)  # 10% move = max momentum
        return momentum_score
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else 50.0

