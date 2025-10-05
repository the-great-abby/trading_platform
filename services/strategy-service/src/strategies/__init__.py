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

try:
    from .hybrid_ichimoku_strategy import HybridIchimokuStrategy
    __all__.append('HybridIchimokuStrategy')
except ImportError:
    pass

try:
    from .options.cash_secured_put_strategy import CashSecuredPutStrategy
    __all__.append('CashSecuredPutStrategy')
except ImportError:
    pass

try:
    from .momentum.momentum_strategy import MomentumStrategy
    __all__.append('MomentumStrategy')
except ImportError:
    pass

try:
    from .enhanced_elliott_wave_strategies import ElliottWaveImpulseStrategy
    __all__.append('ElliottWaveImpulseStrategy')
except ImportError:
    pass

try:
    from .enhanced_elliott_wave_strategies import ElliottWaveCorrectiveStrategy
    __all__.append('ElliottWaveCorrectiveStrategy')
except ImportError:
    pass

try:
    from .regime_switching_strategy import RegimeSwitchingStrategy
    __all__.append('RegimeSwitchingStrategy')
except ImportError:
    pass

try:
    from .advanced_options_strategies import IronCondorStrategy
    __all__.append('IronCondorStrategy')
except ImportError:
    pass

try:
    from .advanced_options_strategies import ButterflyStrategy
    __all__.append('ButterflyStrategy')
except ImportError:
    pass

try:
    from .momentum.rsi_strategy import RSIStrategy
    __all__.append('RSIStrategy')
except ImportError:
    pass

try:
    from .momentum.macd_strategy import MACDStrategy
    __all__.append('MACDStrategy')
except ImportError:
    pass

try:
    from .mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
    __all__.append('BollingerBandsStrategy')
except ImportError:
    pass

try:
    from .ichimoku_strategy import IchimokuStrategy
    __all__.append('IchimokuStrategy')
except ImportError:
    pass

try:
    from .simplified_elliott_wave_strategies import SimplifiedElliottWaveImpulseStrategy
    __all__.append('SimplifiedElliottWaveImpulseStrategy')
except ImportError:
    pass

try:
    from .simplified_elliott_wave_strategies import SimplifiedElliottWaveCorrectiveStrategy
    __all__.append('SimplifiedElliottWaveCorrectiveStrategy')
except ImportError:
    pass

try:
    from .elliott_wave_strategies import ElliottWaveCorrectiveStrategy as ServiceElliottWaveCorrectiveStrategy
    __all__.append('ServiceElliottWaveCorrectiveStrategy')
except ImportError:
    pass
