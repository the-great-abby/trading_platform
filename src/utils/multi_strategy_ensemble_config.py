"""
MultiStrategyEnsemble Configuration System
=========================================

This file contains separate configurations for MultiStrategyEnsemble
across different systems to allow for testing and evaluation:

- Backtesting: Optimized for historical performance analysis
- Paper Trading: Conservative settings for simulation
- Live Trading: Production-ready settings with risk management

Each system can have its own configuration while maintaining
a base configuration for consistency.
"""

from typing import Dict, Any, List

# Base MultiStrategyEnsemble Configuration
# Default settings that all systems inherit from
BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG = {
    # Strategy weights (can be overridden per system)
    'adaptive_wave_weight': 0.35,      # 35% - Elliott Wave + Options
    'regime_switching_weight': 0.25,   # 25% - Market timing
    'enhanced_multi_weight': 0.25,     # 25% - Sector rotation
    'momentum_weight': 0.15,           # 15% - Cross-sectional momentum
    
    # Performance tracking
    'performance_window': 50,          # Days to track performance
    'rebalance_frequency': 10,         # Rebalance weights every N days
    
    # Risk management
    'max_total_exposure': 0.90,        # 90% max total exposure (10% cash reserve)
    'correlation_threshold': 0.7,      # Max correlation between strategies
    
    # Capital allocation (as requested)
    'cash_reserve_pct': 0.10,          # 10% cash reserve
    'stock_allocation_pct': 0.40,      # 40% stocks swing trading
    'options_day_trading_pct': 0.25,   # 25% day trading options
    'options_swing_trading_pct': 0.25, # 25% swing trading options
}

# Backtesting Configuration
# Optimized for maximum historical returns and analysis
BACKTESTING_MULTI_STRATEGY_ENSEMBLE_CONFIG = {
    **BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG,
    # Override specific settings for backtesting
    'adaptive_wave_weight': 0.40,      # 40% - Higher weight for proven strategy
    'regime_switching_weight': 0.25,   # 25% - Market timing
    'enhanced_multi_weight': 0.20,     # 20% - Sector rotation
    'momentum_weight': 0.15,           # 15% - Cross-sectional momentum
    
    # More aggressive settings for backtesting (but still maintain allocation)
    'max_total_exposure': 0.90,        # 90% max total exposure (10% cash reserve)
    'rebalance_frequency': 5,           # More frequent rebalancing
    
    # Capital allocation (as requested)
    'cash_reserve_pct': 0.10,          # 10% cash reserve
    'stock_allocation_pct': 0.40,      # 40% stocks swing trading
    'options_day_trading_pct': 0.25,   # 25% day trading options
    'options_swing_trading_pct': 0.25, # 25% swing trading options
}

# Paper Trading Configuration
# Conservative settings for simulation and testing
PAPER_TRADING_MULTI_STRATEGY_ENSEMBLE_CONFIG = {
    **BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG,
    # Conservative settings for paper trading
    'adaptive_wave_weight': 0.30,      # 30% - Lower risk
    'regime_switching_weight': 0.30,   # 30% - More market timing focus
    'enhanced_multi_weight': 0.25,     # 25% - Sector rotation
    'momentum_weight': 0.15,           # 15% - Cross-sectional momentum
    
    # Conservative risk management (but maintain allocation)
    'max_total_exposure': 0.90,        # 90% max total exposure (10% cash reserve)
    'correlation_threshold': 0.6,      # Lower correlation threshold
    'rebalance_frequency': 15,          # Less frequent rebalancing
    
    # Capital allocation (as requested)
    'cash_reserve_pct': 0.10,          # 10% cash reserve
    'stock_allocation_pct': 0.40,      # 40% stocks swing trading
    'options_day_trading_pct': 0.25,   # 25% day trading options
    'options_swing_trading_pct': 0.25, # 25% swing trading options
}

# Live Trading Configuration
# Production-ready settings with enhanced risk management
LIVE_TRADING_MULTI_STRATEGY_ENSEMBLE_CONFIG = {
    **BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG,
    # Balanced settings for live trading
    'adaptive_wave_weight': 0.35,      # 35% - Elliott Wave + Options
    'regime_switching_weight': 0.25,   # 25% - Market timing
    'enhanced_multi_weight': 0.25,     # 25% - Sector rotation
    'momentum_weight': 0.15,           # 15% - Cross-sectional momentum
    
    # Enhanced risk management for live trading
    'max_total_exposure': 0.90,        # 90% max total exposure (10% cash reserve)
    'correlation_threshold': 0.65,      # Stricter correlation limits
    'rebalance_frequency': 7,           # Weekly rebalancing
    'performance_window': 30,           # Shorter performance window
    
    # Capital allocation (as requested)
    'cash_reserve_pct': 0.10,          # 10% cash reserve
    'stock_allocation_pct': 0.40,      # 40% stocks swing trading
    'options_day_trading_pct': 0.25,   # 25% day trading options
    'options_swing_trading_pct': 0.25, # 25% swing trading options
}

# Component strategy configurations (shared across all systems)
COMPONENT_STRATEGY_CONFIGS = {
    'adaptive_wave': {
        'elliott_wave_min_confidence': 0.05,
        'ichimoku_min_confidence': 0.05,
        'enable_ichimoku': True
    },
    'regime_switching': {
        'lookback_period': 100,
        'regime_confidence_threshold': 0.7,
        'min_regime_duration': 20
    },
    'enhanced_multi': {
        'entry_confidence_threshold': 0.5,
        'momentum_exit_threshold': 0.02,
        'volatility_exit_threshold': 0.03,
        'max_position_duration_days': 30,
        'min_profit_target': 0.05,
        'max_loss_stop': 0.03,
        'max_concurrent_positions': 3,
        'position_size_pct': 0.05
    },
    'momentum': {
        'lookback_period': 60,
        'momentum_periods': [20, 60, 120],
        'top_percentile': 0.2,
        'bottom_percentile': 0.2,
        'rebalance_frequency': 20,
        'max_position_size': 0.1,
        'volatility_adjustment': True
    }
}

def get_multi_strategy_ensemble_config(system: str = 'base') -> Dict[str, Any]:
    """Get MultiStrategyEnsemble configuration for a specific system"""
    configs = {
        'base': BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG,
        'backtesting': BACKTESTING_MULTI_STRATEGY_ENSEMBLE_CONFIG,
        'paper_trading': PAPER_TRADING_MULTI_STRATEGY_ENSEMBLE_CONFIG,
        'live_trading': LIVE_TRADING_MULTI_STRATEGY_ENSEMBLE_CONFIG
    }
    return configs.get(system, BASE_MULTI_STRATEGY_ENSEMBLE_CONFIG).copy()

def get_component_strategy_config(strategy_name: str) -> Dict[str, Any]:
    """Get configuration for a specific component strategy"""
    return COMPONENT_STRATEGY_CONFIGS.get(strategy_name, {})

def get_strategy_weights(system: str = 'base') -> Dict[str, float]:
    """Get strategy weights for a specific system"""
    config = get_multi_strategy_ensemble_config(system)
    return {
        'adaptive_wave': config['adaptive_wave_weight'],
        'regime_switching': config['regime_switching_weight'],
        'enhanced_multi': config['enhanced_multi_weight'],
        'momentum': config['momentum_weight']
    }

def get_backtesting_config() -> Dict[str, Any]:
    """Get backtesting-specific configuration"""
    return get_multi_strategy_ensemble_config('backtesting')

def get_paper_trading_config() -> Dict[str, Any]:
    """Get paper trading-specific configuration"""
    return get_multi_strategy_ensemble_config('paper_trading')

def get_live_trading_config() -> Dict[str, Any]:
    """Get live trading-specific configuration"""
    return get_multi_strategy_ensemble_config('live_trading')

# Symbol Configuration - Aligned across all systems
# Based on backtesting performance and market coverage
BACKTESTING_SYMBOLS = [
    # Core high-performance symbols (from backtesting results)
    'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
    
    # Additional high-volume symbols for diversification
    'AMD', 'INTC', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
    
    # Financial sector (important for regime switching)
    'JPM', 'BAC', 'WFC', 'GS', 'MS',
    
    # Healthcare (defensive sector)
    'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',
    
    # Consumer sectors
    'HD', 'DIS', 'V', 'MA', 'PYPL',
    
    # Sector ETFs for broad market exposure
    'XLK', 'XLF', 'XLV', 'XLE', 'XLY', 'XLP', 'XLI', 'XLB', 'XLU', 'XLRE',
    
    # Additional ETFs
    'VTI', 'VOO', 'VUG', 'IWM', 'TLT', 'GLD', 'SLV'
]

PAPER_TRADING_SYMBOLS = [
    # Core high-performance symbols (from backtesting results)
    'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'
]

LIVE_TRADING_SYMBOLS = [
    # Core high-performance symbols (from backtesting results)
    'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'
]

def get_symbols(system: str = 'backtesting') -> List[str]:
    """Get symbol list for a specific system"""
    symbol_lists = {
        'backtesting': BACKTESTING_SYMBOLS,
        'paper_trading': PAPER_TRADING_SYMBOLS,
        'live_trading': LIVE_TRADING_SYMBOLS
    }
    return symbol_lists.get(system, BACKTESTING_SYMBOLS).copy()

def get_backtesting_symbols() -> List[str]:
    """Get backtesting symbol list"""
    return get_symbols('backtesting')

def get_paper_trading_symbols() -> List[str]:
    """Get paper trading symbol list"""
    return get_symbols('paper_trading')

def get_live_trading_symbols() -> List[str]:
    """Get live trading symbol list"""
    return get_symbols('live_trading')
