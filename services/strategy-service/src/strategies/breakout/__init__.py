"""
Breakout trading strategies
"""

from .volatility_breakout_strategy import VolatilityBreakoutStrategy
from .sma_crossover import SMACrossoverStrategy

__all__ = ['VolatilityBreakoutStrategy', 'SMACrossoverStrategy'] 