"""
Trading Strategies Module
"""

from .base import BaseStrategy

# Import strategies with optional dependencies
__all__ = ['BaseStrategy']

try:
    from .pairs_trading_strategy import PairsTradingStrategy
    __all__.append('PairsTradingStrategy')
except ImportError:
    pass

try:
    from .vwap_strategy import VWAPStrategy
    __all__.append('VWAPStrategy')
except ImportError:
    pass

try:
    from .momentum.cross_sectional_momentum_strategy import CrossSectionalMomentumStrategy
    __all__.append('CrossSectionalMomentumStrategy')
except ImportError:
    pass

try:
    from .ml_ensemble_strategy import MLEnsembleStrategy
    __all__.append('MLEnsembleStrategy')
except ImportError:
    pass

try:
    from .kalman_filter_strategy import KalmanFilterStrategy
    __all__.append('KalmanFilterStrategy')
except ImportError:
    pass 