"""
Trading Strategies Module
"""

from .base import BaseStrategy
from .pairs_trading_strategy import PairsTradingStrategy
from .vwap_strategy import VWAPStrategy
from .momentum.cross_sectional_momentum_strategy import CrossSectionalMomentumStrategy
from .ml_ensemble_strategy import MLEnsembleStrategy
from .kalman_filter_strategy import KalmanFilterStrategy

__all__ = [
    'BaseStrategy',
    'PairsTradingStrategy', 
    'VWAPStrategy',
    'CrossSectionalMomentumStrategy',
    'MLEnsembleStrategy',
    'KalmanFilterStrategy'
] 