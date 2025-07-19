"""
Centralized Backtesting Configuration

This module provides a comprehensive configuration system for backtesting
that consolidates all parameters in one place for easy management.
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .trading_config import get_symbols, get_options_symbols


class BacktestMode(Enum):
    """Backtest execution modes"""
    FAST = "fast"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"


class RiskProfile(Enum):
    """Risk profile configurations"""
    ULTRA_CONSERVATIVE = "ultra_conservative"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"


@dataclass
class BacktestConfig:
    """Comprehensive backtesting configuration"""
    
    # ============================================================================
    # BASIC CONFIGURATION
    # ============================================================================
    
    # Backtest identification
    backtest_name: Optional[str] = None
    backtest_mode: BacktestMode = BacktestMode.STANDARD
    risk_profile: RiskProfile = RiskProfile.MODERATE
    
    # Date range
    start_date: str = None
    end_date: str = None
    test_period_days: int = 365
    
    # Symbols and strategies
    symbols: List[str] = field(default_factory=list)
    strategies: List[str] = field(default_factory=list)
    max_symbols: int = 50
    
    # ============================================================================
    # CAPITAL AND POSITION SIZING
    # ============================================================================
    
    # Initial capital
    initial_capital: float = 100000.0
    
    # Position sizing
    position_size: float = 0.05  # 5% of portfolio per trade
    max_position_size: float = 0.15  # Max 15% per position
    min_trade_value: float = 50.0  # Minimum $50 per trade
    max_trade_value: float = 15000.0  # Maximum trade value
    
    # Position limits
    max_positions: int = 5
    max_daily_trades: int = 10
    min_trade_interval: int = 1  # Minimum days between trades
    
    # ============================================================================
    # RISK MANAGEMENT
    # ============================================================================
    
    # Stop loss and take profit
    stop_loss_pct: float = 0.08  # 8% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
    trailing_stop_pct: float = 0.05  # 5% trailing stop
    
    # Risk limits
    max_daily_loss: float = 100.0  # Max daily loss in dollars
    max_drawdown_pct: float = 0.25  # 25% max drawdown
    max_portfolio_risk: float = 0.10  # 10% max portfolio risk per trade
    
    # ============================================================================
    # TRADING COSTS
    # ============================================================================
    
    # Commission and fees
    commission_per_trade: float = 1.0  # $1 per trade
    commission_rate: float = 0.001  # 0.1% commission rate
    slippage_percentage: float = 0.0005  # 0.05% slippage
    
    # Fill settings
    partial_fill_probability: float = 0.15  # 15% chance of partial fill
    market_hours_only: bool = True
    
    # ============================================================================
    # PERFORMANCE SETTINGS
    # ============================================================================
    
    # Parallel processing
    use_parallel: bool = True
    max_workers: int = 8
    parallel_strategies: bool = True
    parallel_symbols: bool = True
    
    # Caching and data
    use_cache: bool = True
    use_real_data: bool = True
    database_only: bool = False
    
    # Memory and timeout
    memory_limit: str = "2Gi"
    timeout_hours: int = 24
    batch_size: int = 10
    
    # ============================================================================
    # STRATEGY SETTINGS
    # ============================================================================
    
    # Confidence and thresholds
    confidence_threshold: float = 0.6
    min_volume_ratio: float = 1.2
    min_price_change: float = 0.005
    
    # Trend and momentum
    trend_confirmation: bool = True
    trend_confirmation_weight: float = 0.7
    require_positive_momentum: bool = True
    
    # Market regime
    market_regime_filter: bool = True
    volatility_filter: bool = True
    volatility_threshold: float = 0.02
    trend_strength_threshold: float = 0.6
    correlation_threshold: float = 0.3
    market_regime_lookback: int = 20
    
    # ============================================================================
    # LLM SETTINGS
    # ============================================================================
    
    # LLM evaluation
    use_llm: bool = False
    llm_timeout: float = 10.0
    llm_retry_attempts: int = 2
    fallback_confidence: float = 0.6
    
    # ============================================================================
    # ADVANCED SETTINGS
    # ============================================================================
    
    # Portfolio management
    force_close_positions: bool = True
    cross_strategy_tracking: bool = False
    portfolio_mode: bool = False
    
    # Dynamic features
    dynamic_stop_loss: bool = False
    dynamic_weighting: bool = False
    correlation_analysis: bool = False
    volatility_position_sizing: bool = False
    
    # Rebalancing
    rebalance_frequency: int = 30
    volatility_lookback: int = 20
    
    # ============================================================================
    # DATA SETTINGS
    # ============================================================================
    
    # Data providers
    data_provider: str = "polygon"
    historical_days: int = 30
    
    # Data retention
    days_to_keep: int = 365
    cleanup_enabled: bool = True
    
    # ============================================================================
    # LOGGING AND MONITORING
    # ============================================================================
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_dir: str = "/app/logs"
    
    # Health checks
    health_check_interval: int = 30
    health_check_timeout: int = 10
    
    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090
    
    def __post_init__(self):
        """Initialize default values after creation"""
        # Set default dates if not provided
        if self.end_date is None:
            self.end_date = datetime.now().strftime("%Y-%m-%d")
        if self.start_date is None:
            start_date = datetime.now() - timedelta(days=self.test_period_days)
            self.start_date = start_date.strftime("%Y-%m-%d")
        
        # Set default symbols if not provided
        if not self.symbols:
            self.symbols = get_symbols()[:self.max_symbols]
        
        # Set default strategies based on mode
        if not self.strategies:
            self.strategies = self._get_default_strategies()
        
        # Apply risk profile settings
        self._apply_risk_profile()
        
        # Apply mode settings
        self._apply_mode_settings()
    
    def _get_default_strategies(self) -> List[str]:
        """Get default strategies based on mode"""
        base_strategies = [
            'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
            'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
        ]
        
        if self.backtest_mode == BacktestMode.FAST:
            return base_strategies[:6]  # First 6 strategies
        elif self.backtest_mode == BacktestMode.COMPREHENSIVE:
            return base_strategies + ['Ichimoku', 'Stochastic', 'WilliamsR', 'CCI', 'ADX']
        else:
            return base_strategies
    
    def _apply_risk_profile(self):
        """Apply settings based on risk profile"""
        if self.risk_profile == RiskProfile.ULTRA_CONSERVATIVE:
            self.position_size = 0.02
            self.max_position_size = 0.05
            self.stop_loss_pct = 0.03
            self.take_profit_pct = 0.08
            self.max_daily_trades = 3
            self.confidence_threshold = 0.8
            self.max_drawdown_pct = 0.10
            
        elif self.risk_profile == RiskProfile.CONSERVATIVE:
            self.position_size = 0.03
            self.max_position_size = 0.08
            self.stop_loss_pct = 0.05
            self.take_profit_pct = 0.10
            self.max_daily_trades = 5
            self.confidence_threshold = 0.7
            self.max_drawdown_pct = 0.15
            
        elif self.risk_profile == RiskProfile.MODERATE:
            self.position_size = 0.05
            self.max_position_size = 0.15
            self.stop_loss_pct = 0.08
            self.take_profit_pct = 0.15
            self.max_daily_trades = 10
            self.confidence_threshold = 0.6
            self.max_drawdown_pct = 0.25
            
        elif self.risk_profile == RiskProfile.AGGRESSIVE:
            self.position_size = 0.08
            self.max_position_size = 0.25
            self.stop_loss_pct = 0.12
            self.take_profit_pct = 0.20
            self.max_daily_trades = 15
            self.confidence_threshold = 0.5
            self.max_drawdown_pct = 0.35
            
        elif self.risk_profile == RiskProfile.ULTRA_AGGRESSIVE:
            self.position_size = 0.12
            self.max_position_size = 0.35
            self.stop_loss_pct = 0.15
            self.take_profit_pct = 0.25
            self.max_daily_trades = 20
            self.confidence_threshold = 0.4
            self.max_drawdown_pct = 0.50
    
    def _apply_mode_settings(self):
        """Apply settings based on backtest mode"""
        if self.backtest_mode == BacktestMode.FAST:
            self.max_symbols = 20
            self.test_period_days = 90
            self.max_workers = 4
            self.use_llm = False
            self.database_only = True
            
        elif self.backtest_mode == BacktestMode.COMPREHENSIVE:
            self.max_symbols = 100
            self.test_period_days = 730  # 2 years
            self.max_workers = 12
            self.use_llm = True
            self.cross_strategy_tracking = True
            self.portfolio_mode = True
            
        elif self.backtest_mode == BacktestMode.AGGRESSIVE:
            self.risk_profile = RiskProfile.AGGRESSIVE
            self.max_daily_trades = 20
            self.confidence_threshold = 0.3
            self.min_volume_ratio = 1.0
            self.min_price_change = 0.003
            
        elif self.backtest_mode == BacktestMode.CONSERVATIVE:
            self.risk_profile = RiskProfile.CONSERVATIVE
            self.max_daily_trades = 5
            self.confidence_threshold = 0.7
            self.min_volume_ratio = 1.5
            self.min_price_change = 0.008
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'backtest_name': self.backtest_name,
            'backtest_mode': self.backtest_mode.value,
            'risk_profile': self.risk_profile.value,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'test_period_days': self.test_period_days,
            'symbols': self.symbols,
            'strategies': self.strategies,
            'max_symbols': self.max_symbols,
            'initial_capital': self.initial_capital,
            'position_size': self.position_size,
            'max_position_size': self.max_position_size,
            'min_trade_value': self.min_trade_value,
            'max_trade_value': self.max_trade_value,
            'max_positions': self.max_positions,
            'max_daily_trades': self.max_daily_trades,
            'min_trade_interval': self.min_trade_interval,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'trailing_stop_pct': self.trailing_stop_pct,
            'max_daily_loss': self.max_daily_loss,
            'max_drawdown_pct': self.max_drawdown_pct,
            'max_portfolio_risk': self.max_portfolio_risk,
            'commission_per_trade': self.commission_per_trade,
            'commission_rate': self.commission_rate,
            'slippage_percentage': self.slippage_percentage,
            'partial_fill_probability': self.partial_fill_probability,
            'market_hours_only': self.market_hours_only,
            'use_parallel': self.use_parallel,
            'max_workers': self.max_workers,
            'parallel_strategies': self.parallel_strategies,
            'parallel_symbols': self.parallel_symbols,
            'use_cache': self.use_cache,
            'use_real_data': self.use_real_data,
            'database_only': self.database_only,
            'memory_limit': self.memory_limit,
            'timeout_hours': self.timeout_hours,
            'batch_size': self.batch_size,
            'confidence_threshold': self.confidence_threshold,
            'min_volume_ratio': self.min_volume_ratio,
            'min_price_change': self.min_price_change,
            'trend_confirmation': self.trend_confirmation,
            'trend_confirmation_weight': self.trend_confirmation_weight,
            'require_positive_momentum': self.require_positive_momentum,
            'market_regime_filter': self.market_regime_filter,
            'volatility_filter': self.volatility_filter,
            'volatility_threshold': self.volatility_threshold,
            'trend_strength_threshold': self.trend_strength_threshold,
            'correlation_threshold': self.correlation_threshold,
            'market_regime_lookback': self.market_regime_lookback,
            'use_llm': self.use_llm,
            'llm_timeout': self.llm_timeout,
            'llm_retry_attempts': self.llm_retry_attempts,
            'fallback_confidence': self.fallback_confidence,
            'force_close_positions': self.force_close_positions,
            'cross_strategy_tracking': self.cross_strategy_tracking,
            'portfolio_mode': self.portfolio_mode,
            'dynamic_stop_loss': self.dynamic_stop_loss,
            'dynamic_weighting': self.dynamic_weighting,
            'correlation_analysis': self.correlation_analysis,
            'volatility_position_sizing': self.volatility_position_sizing,
            'rebalance_frequency': self.rebalance_frequency,
            'volatility_lookback': self.volatility_lookback,
            'data_provider': self.data_provider,
            'historical_days': self.historical_days,
            'days_to_keep': self.days_to_keep,
            'cleanup_enabled': self.cleanup_enabled,
            'log_level': self.log_level,
            'log_format': self.log_format,
            'log_dir': self.log_dir,
            'health_check_interval': self.health_check_interval,
            'health_check_timeout': self.health_check_timeout,
            'metrics_enabled': self.metrics_enabled,
            'metrics_port': self.metrics_port
        }
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert config to environment variables"""
        config_dict = self.to_dict()
        env_vars = {}
        
        for key, value in config_dict.items():
            if value is not None:
                env_vars[key.upper()] = str(value)
        
        return env_vars
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate capital settings
        if self.initial_capital <= 0:
            errors.append("Initial capital must be positive")
        
        if self.position_size <= 0 or self.position_size > 1:
            errors.append("Position size must be between 0 and 1")
        
        if self.max_position_size <= 0 or self.max_position_size > 1:
            errors.append("Max position size must be between 0 and 1")
        
        # Validate risk settings
        if self.stop_loss_pct <= 0:
            errors.append("Stop loss percentage must be positive")
        
        if self.take_profit_pct <= 0:
            errors.append("Take profit percentage must be positive")
        
        if self.max_drawdown_pct <= 0 or self.max_drawdown_pct > 1:
            errors.append("Max drawdown percentage must be between 0 and 1")
        
        # Validate date settings
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if start >= end:
                errors.append("Start date must be before end date")
        except ValueError:
            errors.append("Invalid date format (use YYYY-MM-DD)")
        
        # Validate symbol and strategy settings
        if not self.symbols:
            errors.append("At least one symbol must be specified")
        
        if not self.strategies:
            errors.append("At least one strategy must be specified")
        
        return errors


def get_backtest_config(
    mode: BacktestMode = BacktestMode.STANDARD,
    risk_profile: RiskProfile = RiskProfile.MODERATE,
    **kwargs
) -> BacktestConfig:
    """
    Get a backtest configuration with default settings
    
    Args:
        mode: Backtest execution mode
        risk_profile: Risk profile to use
        **kwargs: Additional configuration overrides
        
    Returns:
        BacktestConfig instance
    """
    config = BacktestConfig(
        backtest_mode=mode,
        risk_profile=risk_profile,
        **kwargs
    )
    
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
    
    return config


def get_preset_config(preset_name: str, **kwargs) -> BacktestConfig:
    """
    Get a preset configuration
    
    Args:
        preset_name: Name of the preset
        **kwargs: Additional overrides
        
    Returns:
        BacktestConfig instance
    """
    presets = {
        'quick_test': {
            'backtest_mode': BacktestMode.FAST,
            'risk_profile': RiskProfile.CONSERVATIVE,
            'test_period_days': 30,
            'max_symbols': 10,
            'max_daily_trades': 5
        },
        'comprehensive_test': {
            'backtest_mode': BacktestMode.COMPREHENSIVE,
            'risk_profile': RiskProfile.MODERATE,
            'test_period_days': 730,
            'max_symbols': 50,
            'use_llm': True
        },
        'aggressive_test': {
            'backtest_mode': BacktestMode.AGGRESSIVE,
            'risk_profile': RiskProfile.AGGRESSIVE,
            'test_period_days': 180,
            'max_symbols': 30,
            'max_daily_trades': 15
        },
        'conservative_test': {
            'backtest_mode': BacktestMode.CONSERVATIVE,
            'risk_profile': RiskProfile.CONSERVATIVE,
            'test_period_days': 365,
            'max_symbols': 20,
            'max_daily_trades': 3
        }
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
    
    preset_config = presets[preset_name].copy()
    preset_config.update(kwargs)
    
    return get_backtest_config(**preset_config)


def load_config_from_env() -> BacktestConfig:
    """
    Load configuration from environment variables
    
    Returns:
        BacktestConfig instance
    """
    # Parse mode and risk profile from environment
    mode_str = os.getenv('BACKTEST_MODE', 'standard')
    risk_str = os.getenv('RISK_PROFILE', 'moderate')
    
    try:
        mode = BacktestMode(mode_str)
    except ValueError:
        mode = BacktestMode.STANDARD
    
    try:
        risk_profile = RiskProfile(risk_str)
    except ValueError:
        risk_profile = RiskProfile.MODERATE
    
    # Create config with environment overrides
    config = get_backtest_config(mode=mode, risk_profile=risk_profile)
    
    # Override with environment variables
    for key, value in config.to_dict().items():
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Convert string to appropriate type
            if isinstance(value, bool):
                setattr(config, key, env_value.lower() == 'true')
            elif isinstance(value, int):
                setattr(config, key, int(env_value))
            elif isinstance(value, float):
                setattr(config, key, float(env_value))
            else:
                setattr(config, key, env_value)
    
    return config 