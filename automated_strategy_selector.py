#!/usr/bin/env python3
"""
Automated Strategy Selector
==========================

A comprehensive system that automatically selects the best trading strategy
based on market conditions, performance history, and risk parameters.

Features:
- Multi-layer market analysis
- Performance-based strategy weighting
- Risk-adjusted selection
- Real-time adaptation
- Portfolio optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MarketCondition(Enum):
    """Market condition classifications"""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS_RANGE = "sideways_range"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    EARNINGS_EVENT = "earnings_event"

class StrategyCategory(Enum):
    """Strategy category classifications"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    INCOME_GENERATION = "income_generation"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    AI_ENHANCED = "ai_enhanced"
    OPTIONS = "options"

@dataclass
class StrategyScore:
    """Strategy performance score"""
    strategy_name: str
    category: StrategyCategory
    market_condition: MarketCondition
    performance_score: float
    risk_score: float
    confidence: float
    recent_performance: float
    volatility_adjusted_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    last_updated: datetime

@dataclass
class MarketAnalysis:
    """Comprehensive market analysis"""
    condition: MarketCondition
    confidence: float
    volatility_level: float
    trend_strength: float
    momentum: float
    volume_profile: float
    support_resistance: Dict[str, float]
    technical_indicators: Dict[str, float]
    sentiment_score: float
    options_iv_percentile: float
    earnings_proximity: int  # days to next earnings
    market_cap_tier: str
    sector_performance: float

class AutomatedStrategySelector:
    """
    Automated Strategy Selector
    
    This class automatically selects the best trading strategy based on:
    1. Current market conditions
    2. Historical strategy performance
    3. Risk parameters
    4. Portfolio constraints
    5. Real-time market data
    """
    
    def __init__(self, 
                 performance_lookback: int = 90,
                 min_confidence_threshold: float = 0.6,
                 max_risk_per_strategy: float = 0.05,
                 rebalance_frequency: str = "daily",
                 **kwargs):
        
        self.performance_lookback = performance_lookback
        self.min_confidence_threshold = min_confidence_threshold
        self.max_risk_per_strategy = max_risk_per_strategy
        self.rebalance_frequency = rebalance_frequency
        
        # Strategy registry
        self.strategy_registry = self._initialize_strategy_registry()
        
        # Performance tracking
        self.strategy_performance = {}
        self.market_analysis_cache = {}
        
        # Selection history
        self.selection_history = []
        
    def _initialize_strategy_registry(self) -> Dict[str, Dict]:
        """Initialize the strategy registry with all available strategies"""
        
        return {
            # Trend Following Strategies
            "SMACrossover": {
                "category": StrategyCategory.TREND_FOLLOWING,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BEAR_TRENDING],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"short_window": 20, "long_window": 50}
            },
            "MACD": {
                "category": StrategyCategory.TREND_FOLLOWING,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BEAR_TRENDING],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9}
            },
            "Ichimoku": {
                "category": StrategyCategory.TREND_FOLLOWING,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BEAR_TRENDING, MarketCondition.BREAKOUT],
                "risk_level": "medium",
                "timeframe": "long",
                "parameters": {"tenkan_period": 9, "kijun_period": 26, "senkou_b_period": 52}
            },
            
            # Mean Reversion Strategies
            "BollingerBands": {
                "category": StrategyCategory.MEAN_REVERSION,
                "market_conditions": [MarketCondition.SIDEWAYS_RANGE, MarketCondition.MEAN_REVERSION],
                "risk_level": "low",
                "timeframe": "short",
                "parameters": {"period": 20, "std_dev": 2}
            },
            "RSI": {
                "category": StrategyCategory.MEAN_REVERSION,
                "market_conditions": [MarketCondition.SIDEWAYS_RANGE, MarketCondition.MEAN_REVERSION],
                "risk_level": "low",
                "timeframe": "short",
                "parameters": {"period": 14, "oversold": 30, "overbought": 70}
            },
            "MeanReversion": {
                "category": StrategyCategory.MEAN_REVERSION,
                "market_conditions": [MarketCondition.SIDEWAYS_RANGE, MarketCondition.MEAN_REVERSION],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"short_ma": 20, "long_ma": 50, "deviation_threshold": 0.05}
            },
            
            # Volatility Strategies
            "VolatilityBreakout": {
                "category": StrategyCategory.VOLATILITY,
                "market_conditions": [MarketCondition.HIGH_VOLATILITY, MarketCondition.BREAKOUT],
                "risk_level": "high",
                "timeframe": "short",
                "parameters": {"volatility_period": 20, "breakout_threshold": 2.0}
            },
            "VWAP": {
                "category": StrategyCategory.VOLATILITY,
                "market_conditions": [MarketCondition.HIGH_VOLATILITY, MarketCondition.BREAKOUT],
                "risk_level": "medium",
                "timeframe": "short",
                "parameters": {"vwap_period": 20, "volume_threshold": 1.5}
            },
            
            # Momentum Strategies
            "Momentum": {
                "category": StrategyCategory.MOMENTUM,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BREAKOUT],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"momentum_period": 20, "volume_threshold": 1.5}
            },
            "AdaptiveMomentum": {
                "category": StrategyCategory.MOMENTUM,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BEAR_TRENDING],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"base_period": 20, "adaptation_factor": 0.1}
            },
            
            # AI Enhanced Strategies
            "RSI_AI_Enhanced": {
                "category": StrategyCategory.AI_ENHANCED,
                "market_conditions": [MarketCondition.SIDEWAYS_RANGE, MarketCondition.MEAN_REVERSION],
                "risk_level": "low",
                "timeframe": "short",
                "parameters": {"period": 14, "ai_confidence_threshold": 0.7}
            },
            "MACD_AI_Enhanced": {
                "category": StrategyCategory.AI_ENHANCED,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.BEAR_TRENDING],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"fast_period": 12, "slow_period": 26, "ai_confidence_threshold": 0.7}
            },
            
            # Options Strategies
            "CoveredCall": {
                "category": StrategyCategory.OPTIONS,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.SIDEWAYS_RANGE],
                "risk_level": "low",
                "timeframe": "medium",
                "parameters": {"delta_threshold": 0.3, "days_to_expiration": 30}
            },
            "CashSecuredPut": {
                "category": StrategyCategory.OPTIONS,
                "market_conditions": [MarketCondition.BULL_TRENDING, MarketCondition.SIDEWAYS_RANGE],
                "risk_level": "medium",
                "timeframe": "medium",
                "parameters": {"delta_threshold": -0.3, "days_to_expiration": 30}
            },
            "IronCondor": {
                "category": StrategyCategory.OPTIONS,
                "market_conditions": [MarketCondition.SIDEWAYS_RANGE, MarketCondition.LOW_VOLATILITY],
                "risk_level": "low",
                "timeframe": "medium",
                "parameters": {"days_to_expiration": 45, "profit_target_pct": 0.5}
            },
            "Straddle": {
                "category": StrategyCategory.OPTIONS,
                "market_conditions": [MarketCondition.HIGH_VOLATILITY, MarketCondition.EARNINGS_EVENT],
                "risk_level": "high",
                "timeframe": "short",
                "parameters": {"days_to_expiration": 30, "iv_percentile_threshold": 70}
            }
        }
    
    async def analyze_market_conditions(self, symbol: str, data: pd.DataFrame, 
                                      options_data: Optional[Dict] = None) -> MarketAnalysis:
        """Comprehensive market condition analysis"""
        
        try:
            # Basic technical analysis
            current_price = data['Close'].iloc[-1]
            returns = data['Close'].pct_change().dropna()
            
            # Volatility analysis
            volatility = returns.tail(20).std() * np.sqrt(252)
            atr = data['ATR'].iloc[-1] if 'ATR' in data.columns else 0
            volatility_level = atr / current_price if atr > 0 else 0
            
            # Trend analysis
            sma_20 = data['SMA_20'].iloc[-1] if 'SMA_20' in data.columns else current_price
            sma_50 = data['SMA_50'].iloc[-1] if 'SMA_50' in data.columns else current_price
            trend_strength = abs(sma_20 - sma_50) / sma_50
            
            # Momentum analysis
            rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
            macd = data['MACD'].iloc[-1] if 'MACD' in data.columns else 0
            macd_signal = data['MACD_Signal'].iloc[-1] if 'MACD_Signal' in data.columns else 0
            momentum = (macd - macd_signal) / macd_signal if macd_signal != 0 else 0
            
            # Volume analysis
            volume_sma = data['Volume'].rolling(20).mean().iloc[-1] if 'Volume' in data.columns else 0
            current_volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 0
            volume_profile = current_volume / volume_sma if volume_sma > 0 else 1
            
            # Support/Resistance analysis
            support_resistance = self._calculate_support_resistance(data)
            
            # Technical indicators
            technical_indicators = {
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'bollinger_position': self._calculate_bollinger_position(data),
                'stochastic': self._calculate_stochastic(data),
                'williams_r': self._calculate_williams_r(data)
            }
            
            # Options analysis
            options_iv_percentile = 50.0  # Default
            if options_data:
                options_iv_percentile = options_data.get('iv_percentile', 50.0)
            
            # Earnings proximity
            earnings_proximity = self._get_earnings_proximity(symbol)
            
            # Market condition classification
            condition = self._classify_market_condition(
                trend_strength, volatility_level, momentum, rsi, 
                volume_profile, options_iv_percentile, earnings_proximity
            )
            
            # Confidence calculation
            confidence = self._calculate_analysis_confidence(
                data, technical_indicators, volatility_level, trend_strength
            )
            
            return MarketAnalysis(
                condition=condition,
                confidence=confidence,
                volatility_level=volatility_level,
                trend_strength=trend_strength,
                momentum=momentum,
                volume_profile=volume_profile,
                support_resistance=support_resistance,
                technical_indicators=technical_indicators,
                sentiment_score=0.0,  # Would integrate with sentiment service
                options_iv_percentile=options_iv_percentile,
                earnings_proximity=earnings_proximity,
                market_cap_tier="large",  # Would determine from symbol
                sector_performance=0.0  # Would integrate with sector analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions for {symbol}: {e}")
            return self._get_default_market_analysis()
    
    def _classify_market_condition(self, trend_strength: float, volatility_level: float,
                                 momentum: float, rsi: float, volume_profile: float,
                                 iv_percentile: float, earnings_proximity: int) -> MarketCondition:
        """Classify market condition based on analysis"""
        
        # High volatility condition
        if volatility_level > 0.03 or iv_percentile > 70:
            return MarketCondition.HIGH_VOLATILITY
        
        # Low volatility condition
        if volatility_level < 0.01 or iv_percentile < 30:
            return MarketCondition.LOW_VOLATILITY
        
        # Earnings event condition
        if earnings_proximity <= 5:
            return MarketCondition.EARNINGS_EVENT
        
        # Trending conditions
        if trend_strength > 0.05:
            if momentum > 0 and rsi > 50:
                return MarketCondition.BULL_TRENDING
            elif momentum < 0 and rsi < 50:
                return MarketCondition.BEAR_TRENDING
        
        # Breakout condition
        if volume_profile > 1.5 and (rsi > 70 or rsi < 30):
            return MarketCondition.BREAKOUT
        
        # Mean reversion condition
        if (rsi > 70 or rsi < 30) and trend_strength < 0.02:
            return MarketCondition.MEAN_REVERSION
        
        # Default to sideways
        return MarketCondition.SIDEWAYS_RANGE
    
    async def select_optimal_strategy(self, symbol: str, data: pd.DataFrame,
                                    options_data: Optional[Dict] = None,
                                    portfolio_constraints: Optional[Dict] = None) -> Optional[StrategyScore]:
        """Select the optimal strategy based on market conditions and performance"""
        
        try:
            # Analyze market conditions
            market_analysis = await self.analyze_market_conditions(symbol, data, options_data)
            
            # Get candidate strategies
            candidate_strategies = self._get_candidate_strategies(market_analysis)
            
            if not candidate_strategies:
                logger.warning(f"No candidate strategies found for {symbol}")
                return None
            
            # Score each candidate strategy
            strategy_scores = []
            for strategy_name in candidate_strategies:
                score = await self._score_strategy(
                    strategy_name, market_analysis, data, portfolio_constraints
                )
                if score:
                    strategy_scores.append(score)
            
            if not strategy_scores:
                logger.warning(f"No valid strategy scores for {symbol}")
                return None
            
            # Select best strategy
            best_strategy = max(strategy_scores, key=lambda x: x.performance_score)
            
            # Log selection
            logger.info(f"Selected strategy {best_strategy.strategy_name} for {symbol} "
                       f"(score: {best_strategy.performance_score:.3f}, "
                       f"confidence: {best_strategy.confidence:.3f})")
            
            # Store selection history
            self.selection_history.append({
                'symbol': symbol,
                'strategy': best_strategy.strategy_name,
                'market_condition': market_analysis.condition.value,
                'score': best_strategy.performance_score,
                'confidence': best_strategy.confidence,
                'timestamp': datetime.now()
            })
            
            return best_strategy
            
        except Exception as e:
            logger.error(f"Error selecting strategy for {symbol}: {e}")
            return None
    
    def _get_candidate_strategies(self, market_analysis: MarketAnalysis) -> List[str]:
        """Get candidate strategies based on market condition"""
        
        candidates = []
        for strategy_name, strategy_info in self.strategy_registry.items():
            if market_analysis.condition in strategy_info['market_conditions']:
                candidates.append(strategy_name)
        
        return candidates
    
    async def _score_strategy(self, strategy_name: str, market_analysis: MarketAnalysis,
                            data: pd.DataFrame, portfolio_constraints: Optional[Dict] = None) -> Optional[StrategyScore]:
        """Score a strategy based on multiple factors"""
        
        try:
            strategy_info = self.strategy_registry[strategy_name]
            
            # Get historical performance
            performance_data = self.strategy_performance.get(strategy_name, {})
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(
                strategy_name, market_analysis, performance_data
            )
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                strategy_info, market_analysis, performance_data
            )
            
            # Calculate confidence
            confidence = self._calculate_strategy_confidence(
                strategy_name, market_analysis, performance_data
            )
            
            # Check constraints
            if portfolio_constraints:
                if not self._check_portfolio_constraints(
                    strategy_name, strategy_info, portfolio_constraints
                ):
                    return None
            
            return StrategyScore(
                strategy_name=strategy_name,
                category=strategy_info['category'],
                market_condition=market_analysis.condition,
                performance_score=performance_score,
                risk_score=risk_score,
                confidence=confidence,
                recent_performance=performance_data.get('recent_return', 0.0),
                volatility_adjusted_return=performance_data.get('sharpe_ratio', 0.0),
                max_drawdown=performance_data.get('max_drawdown', 0.0),
                win_rate=performance_data.get('win_rate', 0.0),
                profit_factor=performance_data.get('profit_factor', 0.0),
                sharpe_ratio=performance_data.get('sharpe_ratio', 0.0),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error scoring strategy {strategy_name}: {e}")
            return None
    
    def _calculate_performance_score(self, strategy_name: str, market_analysis: MarketAnalysis,
                                   performance_data: Dict) -> float:
        """Calculate performance score for a strategy"""
        
        # Base score from historical performance
        base_score = performance_data.get('sharpe_ratio', 0.0) * 0.4
        
        # Market condition alignment
        condition_bonus = 0.2 if market_analysis.condition in self.strategy_registry[strategy_name]['market_conditions'] else 0.0
        
        # Confidence bonus
        confidence_bonus = market_analysis.confidence * 0.2
        
        # Recent performance bonus
        recent_performance = performance_data.get('recent_return', 0.0)
        recent_bonus = min(recent_performance * 0.1, 0.2) if recent_performance > 0 else 0.0
        
        # Volatility adjustment
        volatility_penalty = 0.0
        if market_analysis.volatility_level > 0.05:  # High volatility
            if self.strategy_registry[strategy_name]['risk_level'] == 'high':
                volatility_penalty = -0.1
        
        return max(0.0, base_score + condition_bonus + confidence_bonus + recent_bonus + volatility_penalty)
    
    def _calculate_risk_score(self, strategy_info: Dict, market_analysis: MarketAnalysis,
                            performance_data: Dict) -> float:
        """Calculate risk score for a strategy"""
        
        # Base risk from strategy type
        risk_levels = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        base_risk = risk_levels.get(strategy_info['risk_level'], 0.5)
        
        # Volatility adjustment
        volatility_risk = min(market_analysis.volatility_level * 10, 0.5)
        
        # Historical drawdown
        max_drawdown = performance_data.get('max_drawdown', 0.0)
        drawdown_risk = min(max_drawdown * 2, 0.3)
        
        return min(1.0, base_risk + volatility_risk + drawdown_risk)
    
    def _calculate_strategy_confidence(self, strategy_name: str, market_analysis: MarketAnalysis,
                                     performance_data: Dict) -> float:
        """Calculate confidence in strategy selection"""
        
        # Market condition confidence
        condition_confidence = market_analysis.confidence * 0.4
        
        # Historical performance confidence
        win_rate = performance_data.get('win_rate', 0.5)
        performance_confidence = win_rate * 0.3
        
        # Data quality confidence
        data_confidence = 0.3  # Would be based on data quality metrics
        
        return min(1.0, condition_confidence + performance_confidence + data_confidence)
    
    def _check_portfolio_constraints(self, strategy_name: str, strategy_info: Dict,
                                   portfolio_constraints: Dict) -> bool:
        """Check if strategy meets portfolio constraints"""
        
        # Risk constraint
        max_risk = portfolio_constraints.get('max_risk_per_strategy', 0.05)
        if strategy_info['risk_level'] == 'high' and max_risk < 0.05:
            return False
        
        # Category constraint
        allowed_categories = portfolio_constraints.get('allowed_categories', [])
        if allowed_categories and strategy_info['category'] not in allowed_categories:
            return False
        
        # Timeframe constraint
        allowed_timeframes = portfolio_constraints.get('allowed_timeframes', [])
        if allowed_timeframes and strategy_info['timeframe'] not in allowed_timeframes:
            return False
        
        return True
    
    def _calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        
        # Simple support/resistance calculation
        highs = data['High'].rolling(20).max()
        lows = data['Low'].rolling(20).min()
        
        return {
            'resistance': highs.iloc[-1],
            'support': lows.iloc[-1],
            'resistance_strength': 0.5,  # Would calculate based on touches
            'support_strength': 0.5
        }
    
    def _calculate_bollinger_position(self, data: pd.DataFrame) -> float:
        """Calculate position within Bollinger Bands"""
        
        if 'BB_Upper' not in data.columns or 'BB_Lower' not in data.columns:
            return 0.5
        
        current_price = data['Close'].iloc[-1]
        upper_band = data['BB_Upper'].iloc[-1]
        lower_band = data['BB_Lower'].iloc[-1]
        
        if upper_band == lower_band:
            return 0.5
        
        return (current_price - lower_band) / (upper_band - lower_band)
    
    def _calculate_stochastic(self, data: pd.DataFrame) -> float:
        """Calculate stochastic oscillator"""
        
        if 'Stochastic' not in data.columns:
            return 50.0
        
        return data['Stochastic'].iloc[-1]
    
    def _calculate_williams_r(self, data: pd.DataFrame) -> float:
        """Calculate Williams %R"""
        
        if 'Williams_R' not in data.columns:
            return -50.0
        
        return data['Williams_R'].iloc[-1]
    
    def _get_earnings_proximity(self, symbol: str) -> int:
        """Get days to next earnings (mock implementation)"""
        
        # This would integrate with earnings calendar service
        return 30  # Default to 30 days
    
    def _calculate_analysis_confidence(self, data: pd.DataFrame, technical_indicators: Dict,
                                     volatility_level: float, trend_strength: float) -> float:
        """Calculate confidence in market analysis"""
        
        # Data quality confidence
        data_quality = min(len(data) / 100, 1.0) * 0.3
        
        # Technical indicator confidence
        indicator_confidence = 0.3
        if all(key in technical_indicators for key in ['rsi', 'macd', 'bollinger_position']):
            indicator_confidence = 0.5
        
        # Market condition clarity
        condition_clarity = 0.4
        if volatility_level > 0.02 or trend_strength > 0.03:
            condition_clarity = 0.6
        
        return min(1.0, data_quality + indicator_confidence + condition_clarity)
    
    def _get_default_market_analysis(self) -> MarketAnalysis:
        """Get default market analysis when analysis fails"""
        
        return MarketAnalysis(
            condition=MarketCondition.SIDEWAYS_RANGE,
            confidence=0.3,
            volatility_level=0.02,
            trend_strength=0.01,
            momentum=0.0,
            volume_profile=1.0,
            support_resistance={'resistance': 0, 'support': 0, 'resistance_strength': 0.5, 'support_strength': 0.5},
            technical_indicators={},
            sentiment_score=0.0,
            options_iv_percentile=50.0,
            earnings_proximity=30,
            market_cap_tier="large",
            sector_performance=0.0
        )

# Example usage
async def main():
    """Example usage of the Automated Strategy Selector"""
    
    # Initialize selector
    selector = AutomatedStrategySelector()
    
    # Mock data (in practice, this would come from your data services)
    data = pd.DataFrame({
        'Close': [100, 101, 102, 101, 103, 104, 103, 105, 106, 107],
        'High': [101, 102, 103, 102, 104, 105, 104, 106, 107, 108],
        'Low': [99, 100, 101, 100, 102, 103, 102, 104, 105, 106],
        'Volume': [1000, 1100, 1200, 1050, 1300, 1400, 1250, 1500, 1600, 1700],
        'SMA_20': [100.5, 100.7, 101.0, 101.2, 101.5, 101.8, 102.0, 102.3, 102.6, 102.9],
        'SMA_50': [100.0, 100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 101.4, 101.6, 101.8],
        'RSI': [45, 47, 50, 48, 52, 55, 53, 57, 60, 62],
        'MACD': [0.1, 0.15, 0.2, 0.18, 0.25, 0.3, 0.28, 0.35, 0.4, 0.45],
        'MACD_Signal': [0.05, 0.08, 0.12, 0.15, 0.18, 0.22, 0.25, 0.28, 0.32, 0.35],
        'ATR': [0.5, 0.52, 0.54, 0.53, 0.56, 0.58, 0.57, 0.6, 0.62, 0.64]
    })
    
    # Select optimal strategy
    optimal_strategy = await selector.select_optimal_strategy("AAPL", data)
    
    if optimal_strategy:
        print(f"Selected Strategy: {optimal_strategy.strategy_name}")
        print(f"Category: {optimal_strategy.category.value}")
        print(f"Market Condition: {optimal_strategy.market_condition.value}")
        print(f"Performance Score: {optimal_strategy.performance_score:.3f}")
        print(f"Confidence: {optimal_strategy.confidence:.3f}")
        print(f"Risk Score: {optimal_strategy.risk_score:.3f}")
    else:
        print("No optimal strategy found")

if __name__ == "__main__":
    asyncio.run(main())

















