"""
Portfolio Configuration Management
Centralized configuration for portfolio management system
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class RiskTolerance(Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class RebalancingFrequency(Enum):
    """Rebalancing frequency options"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"

class OptimizationType(Enum):
    """Portfolio optimization types"""
    MPT = "MPT"
    BLACK_LITTERMAN = "BLACK_LITTERMAN"
    RISK_PARITY = "RISK_PARITY"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"

@dataclass
class OptimizationConfig:
    """Configuration for portfolio optimization"""
    # MPT Configuration
    mpt_risk_free_rate: float = 0.02
    mpt_max_iterations: int = 1000
    mpt_convergence_tolerance: float = 1e-6
    mpt_max_single_asset_weight: float = 0.20
    mpt_min_single_asset_weight: float = 0.0
    
    # Black-Litterman Configuration
    bl_default_confidence: float = 0.5
    bl_default_risk_aversion: float = 3.0
    bl_view_uncertainty: float = 0.1
    bl_tau: float = 0.05
    
    # Risk Parity Configuration
    rp_convergence_tolerance: float = 1e-6
    rp_max_iterations: int = 1000
    rp_risk_budget_method: str = "equal"
    
    # General Optimization
    default_optimization_type: OptimizationType = OptimizationType.MPT
    enable_short_selling: bool = False
    transaction_cost_rate: float = 0.001
    min_trade_size: float = 100.0
    max_trade_size: float = 10000.0

@dataclass
class RiskConfig:
    """Configuration for risk management"""
    # VaR Configuration
    var_confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    cvar_confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    var_lookback_period: int = 252  # 1 year of trading days
    
    # Risk Limits
    max_portfolio_volatility: float = 0.30
    max_single_asset_weight: float = 0.20
    max_sector_weight: float = 0.40
    max_correlation_limit: float = 0.80
    min_cash_reserve: float = 0.05  # 5% cash reserve
    
    # Stress Testing
    stress_test_scenarios: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Market Crash", "shock_return": -0.20},
        {"name": "Interest Rate Shock", "shock_return": 0.02},
        {"name": "Currency Crisis", "shock_return": -0.15}
    ])
    
    # Risk Monitoring
    risk_alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "var_breach": 0.05,
        "volatility_breach": 0.25,
        "concentration_breach": 0.18,
        "correlation_breach": 0.75
    })

@dataclass
class RebalancingConfig:
    """Configuration for portfolio rebalancing"""
    # Rebalancing Triggers
    rebalancing_frequency: RebalancingFrequency = RebalancingFrequency.MONTHLY
    drift_threshold: float = 0.05  # 5% drift triggers rebalancing
    volatility_threshold: float = 0.02  # 2% volatility change triggers rebalancing
    
    # Trade Execution
    rebalancing_strategy: str = "intelligent"  # intelligent, threshold, periodic
    max_rebalancing_trades: int = 20
    min_trade_value: float = 100.0
    max_trade_value: float = 50000.0
    
    # Cost Considerations
    transaction_cost_rate: float = 0.001
    market_impact_rate: float = 0.0005
    slippage_rate: float = 0.0002
    
    # Tax Optimization
    enable_tax_optimization: bool = True
    tax_loss_harvesting_threshold: float = 0.03  # 3% threshold
    wash_sale_period_days: int = 30

@dataclass
class TaxConfig:
    """Configuration for tax optimization"""
    # Tax Rates
    short_term_capital_gains_rate: float = 0.37
    long_term_capital_gains_rate: float = 0.20
    dividend_tax_rate: float = 0.20
    interest_tax_rate: float = 0.37
    
    # Tax Optimization
    enable_tax_loss_harvesting: bool = True
    min_harvest_amount: float = 1000.0
    wash_sale_period_days: int = 30
    tax_lot_method: str = "FIFO"  # FIFO, LIFO, Specific Identification
    
    # Tax Reporting
    enable_tax_reporting: bool = True
    tax_year_end: str = "12-31"
    generate_1099: bool = True

@dataclass
class BacktestingConfig:
    """Configuration for portfolio backtesting"""
    # Backtest Parameters
    default_start_date: str = "2020-01-01"
    default_end_date: str = "2023-12-31"
    benchmark_symbol: str = "SPY"
    
    # Transaction Costs
    default_transaction_cost: float = 0.001
    default_slippage: float = 0.0005
    default_market_impact: float = 0.0002
    
    # Performance Metrics
    risk_free_rate: float = 0.02
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    
    # Walk-Forward Analysis
    enable_walk_forward: bool = True
    walk_forward_window: int = 252  # 1 year
    walk_forward_step: int = 63    # 3 months

@dataclass
class MarketDataConfig:
    """Configuration for market data integration"""
    # Data Sources
    primary_data_source: str = "yfinance"
    backup_data_source: str = "polygon"
    
    # Data Refresh
    data_refresh_interval_minutes: int = 15
    historical_data_days: int = 252 * 5  # 5 years
    real_time_data_enabled: bool = False  # 15-minute delay constraint
    
    # Data Storage
    cache_duration_hours: int = 1
    max_cache_size_mb: int = 1000
    enable_data_compression: bool = True
    
    # API Configuration
    api_rate_limit_per_minute: int = 60
    api_timeout_seconds: int = 30
    retry_attempts: int = 3

@dataclass
class PortfolioConfig:
    """Main portfolio configuration"""
    # Basic Settings
    default_risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    default_base_currency: str = "USD"
    default_rebalancing_frequency: RebalancingFrequency = RebalancingFrequency.MONTHLY
    
    # Sub-configurations
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    rebalancing: RebalancingConfig = field(default_factory=RebalancingConfig)
    tax: TaxConfig = field(default_factory=TaxConfig)
    backtesting: BacktestingConfig = field(default_factory=BacktestingConfig)
    market_data: MarketDataConfig = field(default_factory=MarketDataConfig)
    
    # System Settings
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_retention_days: int = 90
    
    # Performance Settings
    max_concurrent_optimizations: int = 5
    optimization_timeout_seconds: int = 300
    cache_optimization_results: bool = True
    cache_duration_hours: int = 24

class PortfolioConfigManager:
    """Manages portfolio configuration"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("PORTFOLIO_CONFIG_FILE", "portfolio_config.json")
        self.config: PortfolioConfig = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> PortfolioConfig:
        """Load default configuration"""
        return PortfolioConfig()
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                self.config = self._merge_config(self.config, config_data)
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                logger.info("Using default configuration")
        else:
            logger.info(f"Configuration file {self.config_file} not found, using defaults")
            self._save_config()  # Create default config file
    
    def _merge_config(self, default_config: PortfolioConfig, config_data: Dict[str, Any]) -> PortfolioConfig:
        """Merge configuration data with defaults"""
        # Convert to dict for easier merging
        default_dict = self._config_to_dict(default_config)
        
        # Deep merge configuration
        merged_dict = self._deep_merge(default_dict, config_data)
        
        # Convert back to PortfolioConfig
        return self._dict_to_config(merged_dict)
    
    def _config_to_dict(self, config: PortfolioConfig) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        # This is a simplified conversion - in practice, you'd use a more robust method
        return {
            "default_risk_tolerance": config.default_risk_tolerance.value,
            "default_base_currency": config.default_base_currency,
            "default_rebalancing_frequency": config.default_rebalancing_frequency.value,
            "optimization": {
                "mpt_risk_free_rate": config.optimization.mpt_risk_free_rate,
                "mpt_max_iterations": config.optimization.mpt_max_iterations,
                "mpt_convergence_tolerance": config.optimization.mpt_convergence_tolerance,
                "mpt_max_single_asset_weight": config.optimization.mpt_max_single_asset_weight,
                "mpt_min_single_asset_weight": config.optimization.mpt_min_single_asset_weight,
                "bl_default_confidence": config.optimization.bl_default_confidence,
                "bl_default_risk_aversion": config.optimization.bl_default_risk_aversion,
                "bl_view_uncertainty": config.optimization.bl_view_uncertainty,
                "bl_tau": config.optimization.bl_tau,
                "rp_convergence_tolerance": config.optimization.rp_convergence_tolerance,
                "rp_max_iterations": config.optimization.rp_max_iterations,
                "rp_risk_budget_method": config.optimization.rp_risk_budget_method,
                "default_optimization_type": config.optimization.default_optimization_type.value,
                "enable_short_selling": config.optimization.enable_short_selling,
                "transaction_cost_rate": config.optimization.transaction_cost_rate,
                "min_trade_size": config.optimization.min_trade_size,
                "max_trade_size": config.optimization.max_trade_size
            },
            "risk": {
                "var_confidence_levels": config.risk.var_confidence_levels,
                "cvar_confidence_levels": config.risk.cvar_confidence_levels,
                "var_lookback_period": config.risk.var_lookback_period,
                "max_portfolio_volatility": config.risk.max_portfolio_volatility,
                "max_single_asset_weight": config.risk.max_single_asset_weight,
                "max_sector_weight": config.risk.max_sector_weight,
                "max_correlation_limit": config.risk.max_correlation_limit,
                "min_cash_reserve": config.risk.min_cash_reserve,
                "stress_test_scenarios": config.risk.stress_test_scenarios,
                "risk_alert_thresholds": config.risk.risk_alert_thresholds
            },
            "rebalancing": {
                "rebalancing_frequency": config.rebalancing.rebalancing_frequency.value,
                "drift_threshold": config.rebalancing.drift_threshold,
                "volatility_threshold": config.rebalancing.volatility_threshold,
                "rebalancing_strategy": config.rebalancing.rebalancing_strategy,
                "max_rebalancing_trades": config.rebalancing.max_rebalancing_trades,
                "min_trade_value": config.rebalancing.min_trade_value,
                "max_trade_value": config.rebalancing.max_trade_value,
                "transaction_cost_rate": config.rebalancing.transaction_cost_rate,
                "market_impact_rate": config.rebalancing.market_impact_rate,
                "slippage_rate": config.rebalancing.slippage_rate,
                "enable_tax_optimization": config.rebalancing.enable_tax_optimization,
                "tax_loss_harvesting_threshold": config.rebalancing.tax_loss_harvesting_threshold,
                "wash_sale_period_days": config.rebalancing.wash_sale_period_days
            },
            "tax": {
                "short_term_capital_gains_rate": config.tax.short_term_capital_gains_rate,
                "long_term_capital_gains_rate": config.tax.long_term_capital_gains_rate,
                "dividend_tax_rate": config.tax.dividend_tax_rate,
                "interest_tax_rate": config.tax.interest_tax_rate,
                "enable_tax_loss_harvesting": config.tax.enable_tax_loss_harvesting,
                "min_harvest_amount": config.tax.min_harvest_amount,
                "wash_sale_period_days": config.tax.wash_sale_period_days,
                "tax_lot_method": config.tax.tax_lot_method,
                "enable_tax_reporting": config.tax.enable_tax_reporting,
                "tax_year_end": config.tax.tax_year_end,
                "generate_1099": config.tax.generate_1099
            },
            "backtesting": {
                "default_start_date": config.backtesting.default_start_date,
                "default_end_date": config.backtesting.default_end_date,
                "benchmark_symbol": config.backtesting.benchmark_symbol,
                "default_transaction_cost": config.backtesting.default_transaction_cost,
                "default_slippage": config.backtesting.default_slippage,
                "default_market_impact": config.backtesting.default_market_impact,
                "risk_free_rate": config.backtesting.risk_free_rate,
                "confidence_levels": config.backtesting.confidence_levels,
                "enable_walk_forward": config.backtesting.enable_walk_forward,
                "walk_forward_window": config.backtesting.walk_forward_window,
                "walk_forward_step": config.backtesting.walk_forward_step
            },
            "market_data": {
                "primary_data_source": config.market_data.primary_data_source,
                "backup_data_source": config.market_data.backup_data_source,
                "data_refresh_interval_minutes": config.market_data.data_refresh_interval_minutes,
                "historical_data_days": config.market_data.historical_data_days,
                "real_time_data_enabled": config.market_data.real_time_data_enabled,
                "cache_duration_hours": config.market_data.cache_duration_hours,
                "max_cache_size_mb": config.market_data.max_cache_size_mb,
                "enable_data_compression": config.market_data.enable_data_compression,
                "api_rate_limit_per_minute": config.market_data.api_rate_limit_per_minute,
                "api_timeout_seconds": config.market_data.api_timeout_seconds,
                "retry_attempts": config.market_data.retry_attempts
            },
            "system": {
                "enable_logging": config.enable_logging,
                "log_level": config.log_level,
                "enable_metrics": config.enable_metrics,
                "metrics_retention_days": config.metrics_retention_days,
                "max_concurrent_optimizations": config.max_concurrent_optimizations,
                "optimization_timeout_seconds": config.optimization_timeout_seconds,
                "cache_optimization_results": config.cache_optimization_results,
                "cache_duration_hours": config.cache_duration_hours
            }
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> PortfolioConfig:
        """Convert dictionary to configuration"""
        # This is a simplified conversion - in practice, you'd use a more robust method
        config = PortfolioConfig()
        
        # Update basic settings
        if "default_risk_tolerance" in config_dict:
            config.default_risk_tolerance = RiskTolerance(config_dict["default_risk_tolerance"])
        if "default_base_currency" in config_dict:
            config.default_base_currency = config_dict["default_base_currency"]
        if "default_rebalancing_frequency" in config_dict:
            config.default_rebalancing_frequency = RebalancingFrequency(config_dict["default_rebalancing_frequency"])
        
        # Update sub-configurations
        if "optimization" in config_dict:
            opt_config = config_dict["optimization"]
            config.optimization = OptimizationConfig(**opt_config)
        
        if "risk" in config_dict:
            risk_config = config_dict["risk"]
            config.risk = RiskConfig(**risk_config)
        
        if "rebalancing" in config_dict:
            reb_config = config_dict["rebalancing"]
            config.rebalancing = RebalancingConfig(**reb_config)
        
        if "tax" in config_dict:
            tax_config = config_dict["tax"]
            config.tax = TaxConfig(**tax_config)
        
        if "backtesting" in config_dict:
            bt_config = config_dict["backtesting"]
            config.backtesting = BacktestingConfig(**bt_config)
        
        if "market_data" in config_dict:
            md_config = config_dict["market_data"]
            config.market_data = MarketDataConfig(**md_config)
        
        if "system" in config_dict:
            sys_config = config_dict["system"]
            config.enable_logging = sys_config.get("enable_logging", config.enable_logging)
            config.log_level = sys_config.get("log_level", config.log_level)
            config.enable_metrics = sys_config.get("enable_metrics", config.enable_metrics)
            config.metrics_retention_days = sys_config.get("metrics_retention_days", config.metrics_retention_days)
            config.max_concurrent_optimizations = sys_config.get("max_concurrent_optimizations", config.max_concurrent_optimizations)
            config.optimization_timeout_seconds = sys_config.get("optimization_timeout_seconds", config.optimization_timeout_seconds)
            config.cache_optimization_results = sys_config.get("cache_optimization_results", config.cache_optimization_results)
            config.cache_duration_hours = sys_config.get("cache_duration_hours", config.cache_duration_hours)
        
        return config
    
    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base_dict.copy()
        
        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = self._config_to_dict(self.config)
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_config(self) -> PortfolioConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """Update configuration"""
        self.config = self._merge_config(self.config, config_updates)
        self._save_config()
        logger.info("Configuration updated")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self._load_default_config()
        self._save_config()
        logger.info("Configuration reset to defaults")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Validate optimization config
        if self.config.optimization.mpt_risk_free_rate < 0 or self.config.optimization.mpt_risk_free_rate > 1:
            issues.append("Risk-free rate must be between 0 and 1")
        
        if self.config.optimization.mpt_max_iterations <= 0:
            issues.append("Max iterations must be positive")
        
        if self.config.optimization.mpt_max_single_asset_weight <= 0 or self.config.optimization.mpt_max_single_asset_weight > 1:
            issues.append("Max single asset weight must be between 0 and 1")
        
        # Validate risk config
        if self.config.risk.max_portfolio_volatility <= 0 or self.config.risk.max_portfolio_volatility > 1:
            issues.append("Max portfolio volatility must be between 0 and 1")
        
        if self.config.risk.max_single_asset_weight <= 0 or self.config.risk.max_single_asset_weight > 1:
            issues.append("Max single asset weight must be between 0 and 1")
        
        # Validate rebalancing config
        if self.config.rebalancing.drift_threshold <= 0 or self.config.rebalancing.drift_threshold > 1:
            issues.append("Drift threshold must be between 0 and 1")
        
        if self.config.rebalancing.min_trade_value <= 0:
            issues.append("Min trade value must be positive")
        
        # Validate tax config
        if self.config.tax.short_term_capital_gains_rate < 0 or self.config.tax.short_term_capital_gains_rate > 1:
            issues.append("Short-term capital gains rate must be between 0 and 1")
        
        if self.config.tax.long_term_capital_gains_rate < 0 or self.config.tax.long_term_capital_gains_rate > 1:
            issues.append("Long-term capital gains rate must be between 0 and 1")
        
        return issues

# Global configuration manager instance
_config_manager: Optional[PortfolioConfigManager] = None

def get_config_manager() -> PortfolioConfigManager:
    """Get global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = PortfolioConfigManager()
    return _config_manager

def get_portfolio_config() -> PortfolioConfig:
    """Get current portfolio configuration"""
    return get_config_manager().get_config()

def update_portfolio_config(config_updates: Dict[str, Any]) -> None:
    """Update portfolio configuration"""
    get_config_manager().update_config(config_updates)

def reset_portfolio_config() -> None:
    """Reset portfolio configuration to defaults"""
    get_config_manager().reset_to_defaults()

def validate_portfolio_config() -> List[str]:
    """Validate portfolio configuration"""
    return get_config_manager().validate_config()
























