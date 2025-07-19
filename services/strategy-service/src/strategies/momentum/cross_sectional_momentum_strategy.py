"""
Cross-Sectional Momentum Strategy
================================
A strategy that ranks stocks by past performance and buys top performers
while selling bottom performers. Rebalances periodically for optimal performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from ..base import BaseStrategy
from ...core.types import TradeSignal
from ...utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class CrossSectionalMomentumStrategy(BaseStrategy):
    """
    Cross-Sectional Momentum Strategy
    
    Features:
    - Ranks stocks by past performance
    - Buys top performers, sells bottom performers
    - Periodic rebalancing
    - Risk-adjusted momentum scoring
    - Sector-neutral approach
    """
    
    def __init__(self, 
                 name: str = "CrossSectionalMomentum",
                 lookback_period: int = 60,  # 60 days lookback
                 momentum_periods: List[int] = [20, 60, 120],  # Multiple timeframes
                 top_percentile: float = 0.2,  # Top 20%
                 bottom_percentile: float = 0.2,  # Bottom 20%
                 rebalance_frequency: int = 20,  # Rebalance every 20 days
                 max_position_size: float = 0.1,  # 10% max position
                 volatility_adjustment: bool = True):
        super().__init__(name)
        self.lookback_period = lookback_period
        self.momentum_periods = momentum_periods
        self.top_percentile = top_percentile
        self.bottom_percentile = bottom_percentile
        self.rebalance_frequency = rebalance_frequency
        self.max_position_size = max_position_size
        self.volatility_adjustment = volatility_adjustment
        
        # Strategy state
        self.last_rebalance = None
        self.current_positions = {}
        self.momentum_scores = {}
        
    def calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calculate momentum score using multiple timeframes"""
        if len(data) < max(self.momentum_periods):
            return 0.0
        
        scores = []
        weights = []
        
        for period in self.momentum_periods:
            if len(data) >= period:
                # Calculate return for this period
                start_price = data['Close'].iloc[-period]
                end_price = data['Close'].iloc[-1]
                period_return = (end_price - start_price) / start_price
                
                # Volatility adjustment
                if self.volatility_adjustment:
                    volatility = data['Close'].pct_change().rolling(window=period).std().iloc[-1]
                    if volatility > 0:
                        sharpe_ratio = period_return / volatility
                        scores.append(sharpe_ratio)
                    else:
                        scores.append(period_return)
                else:
                    scores.append(period_return)
                
                # Weight by period (shorter periods get higher weight)
                weights.append(1.0 / period)
        
        if not scores:
            return 0.0
        
        # Calculate weighted average momentum score
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
        else:
            weighted_score = np.mean(scores)
        
        return weighted_score
    
    def rank_stocks_by_momentum(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Rank all stocks by their momentum scores"""
        momentum_scores = {}
        
        for symbol, data in market_data.items():
            if not data.empty and len(data) >= min(self.momentum_periods):
                score = self.calculate_momentum_score(data)
                momentum_scores[symbol] = score
        
        # Sort by momentum score
        sorted_scores = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Store for later use
        self.momentum_scores = dict(sorted_scores)
        
        return momentum_scores
    
    def identify_trading_candidates(self, momentum_scores: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Identify buy and sell candidates based on momentum rankings"""
        if not momentum_scores:
            return [], []
        
        # Sort symbols by momentum score
        sorted_symbols = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate percentile thresholds
        num_symbols = len(sorted_symbols)
        top_count = max(1, int(num_symbols * self.top_percentile))
        bottom_count = max(1, int(num_symbols * self.bottom_percentile))
        
        # Get top and bottom performers
        top_performers = [symbol for symbol, score in sorted_symbols[:top_count]]
        bottom_performers = [symbol for symbol, score in sorted_symbols[-bottom_count:]]
        
        return top_performers, bottom_performers
    
    def should_rebalance(self) -> bool:
        """Check if it's time to rebalance"""
        if self.last_rebalance is None:
            return True
        
        days_since_rebalance = (datetime.now() - self.last_rebalance).days
        return days_since_rebalance >= self.rebalance_frequency
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            market_data: Dict[str, pd.DataFrame] = None) -> Optional[TradeSignal]:
        """Generate cross-sectional momentum signal"""
        
        if not market_data or len(market_data) < 5:
            return None
        
        # Check if rebalancing is needed
        if self.should_rebalance():
            await self._rebalance_portfolio(market_data)
            self.last_rebalance = datetime.now()
        
        # Check if this symbol is in our current positions
        if symbol not in self.current_positions:
            return None
        
        position = self.current_positions[symbol]
        current_price = data['Close'].iloc[-1]
        
        # Generate signal based on position type
        if position['type'] == 'long':
            action = "BUY"
            confidence = min(abs(position['momentum_score']) * 2, 0.9)
        elif position['type'] == 'short':
            action = "SELL"
            confidence = min(abs(position['momentum_score']) * 2, 0.9)
        else:
            return None
        
        # Calculate position size
        position_size = self.max_position_size * confidence
        
        signal = TradeSignal(
            symbol=symbol,
            action=action,
            quantity=position_size / current_price,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'momentum_score': position['momentum_score'],
                'position_type': position['type'],
                'rank': position['rank'],
                'total_symbols': len(self.momentum_scores),
                'signal_type': 'cross_sectional_momentum',
                'is_rebalance_signal': False
            }
        )
        
        logger.info(f"Cross-sectional momentum signal: {symbol} {action} "
                   f"(momentum_score: {position['momentum_score']:.3f}, "
                   f"rank: {position['rank']}/{len(self.momentum_scores)})")
        
        return signal
    
    async def _rebalance_portfolio(self, market_data: Dict[str, pd.DataFrame]):
        """Rebalance the portfolio based on current momentum rankings"""
        logger.info("Rebalancing cross-sectional momentum portfolio...")
        
        # Calculate momentum scores for all symbols
        momentum_scores = self.rank_stocks_by_momentum(market_data)
        
        # Identify trading candidates
        top_performers, bottom_performers = self.identify_trading_candidates(momentum_scores)
        
        # Update current positions
        self.current_positions = {}
        
        # Add long positions for top performers
        for i, symbol in enumerate(top_performers):
            self.current_positions[symbol] = {
                'type': 'long',
                'momentum_score': momentum_scores[symbol],
                'rank': i + 1
            }
        
        # Add short positions for bottom performers
        for i, symbol in enumerate(bottom_performers):
            self.current_positions[symbol] = {
                'type': 'short',
                'momentum_score': momentum_scores[symbol],
                'rank': len(momentum_scores) - i
            }
        
        logger.info(f"Portfolio rebalanced: {len(top_performers)} long positions, "
                   f"{len(bottom_performers)} short positions")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "lookback_period": self.lookback_period,
            "momentum_periods": self.momentum_periods,
            "top_percentile": self.top_percentile,
            "bottom_percentile": self.bottom_percentile,
            "rebalance_frequency": self.rebalance_frequency,
            "current_positions": len(self.current_positions),
            "last_rebalance": self.last_rebalance.isoformat() if self.last_rebalance else None
        }
    
    def get_momentum_rankings(self) -> Dict[str, Any]:
        """Get current momentum rankings"""
        return {
            "rankings": self.momentum_scores,
            "top_performers": [symbol for symbol, score in sorted(self.momentum_scores.items(), 
                                                                 key=lambda x: x[1], reverse=True)[:5]],
            "bottom_performers": [symbol for symbol, score in sorted(self.momentum_scores.items(), 
                                                                   key=lambda x: x[1])[:5]]
        } 