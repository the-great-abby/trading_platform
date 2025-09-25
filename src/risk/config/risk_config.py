"""
Risk Management Configuration

Configuration management for the comprehensive risk management framework.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class RiskCalculationMethod(Enum):
    """VaR calculation methods."""
    HISTORICAL_SIMULATION = "historical_simulation"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class RiskLimitType(Enum):
    """Risk limit types."""
    POSITION_SIZE = "position_size"
    DAILY_LOSS = "daily_loss"
    SECTOR_CONCENTRATION = "sector_concentration"
    VAR_LIMIT = "var_limit"
    VOLATILITY_LIMIT = "volatility_limit"


class EnforcementAction(Enum):
    """Risk limit enforcement actions."""
    ALERT = "alert"
    REDUCE_POSITION = "reduce_position"
    HALT_TRADING = "halt_trading"


@dataclass
class VaRConfig:
    """VaR calculation configuration."""
    default_method: RiskCalculationMethod = RiskCalculationMethod.HISTORICAL_SIMULATION
    default_confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    default_data_period_days: int = 252
    max_data_period_days: int = 1000
    min_data_period_days: int = 30
    calculation_timeout_seconds: int = 30
    enable_expected_shortfall: bool = True
    enable_risk_contributions: bool = True


@dataclass
class StressTestConfig:
    """Stress testing configuration."""
    default_scenarios: List[str] = field(default_factory=lambda: [
        "market_crash", "volatility_spike", "rate_shock"
    ])
    max_custom_scenarios: int = 10
    calculation_timeout_seconds: int = 60
    enable_position_impacts: bool = True
    enable_sector_impacts: bool = True
    enable_risk_impacts: bool = True


@dataclass
class CorrelationAnalysisConfig:
    """Correlation analysis configuration."""
    default_rolling_period_days: int = 30
    min_rolling_period_days: int = 7
    max_rolling_period_days: int = 252
    correlation_threshold: float = 0.7
    enable_sector_analysis: bool = True
    enable_diversification_recommendations: bool = True
    calculation_timeout_seconds: int = 20


@dataclass
class ComplianceConfig:
    """Compliance reporting configuration."""
    default_report_types: List[str] = field(default_factory=lambda: [
        "daily", "weekly", "monthly", "ad_hoc"
    ])
    supported_formats: List[str] = field(default_factory=lambda: [
        "JSON", "CSV", "PDF"
    ])
    max_history_days: int = 365
    enable_audit_trail: bool = True
    enable_trade_documentation: bool = True
    enable_position_reporting: bool = True
    enable_risk_metrics: bool = True
    enable_regulatory_checks: bool = True


@dataclass
class RiskMonitoringConfig:
    """Risk monitoring configuration."""
    monitoring_frequency_minutes: int = 15
    max_monitoring_frequency_minutes: int = 1440  # 24 hours
    min_monitoring_frequency_minutes: int = 1
    alert_channels: List[str] = field(default_factory=lambda: [
        "email", "dashboard", "api"
    ])
    escalation_timeout_minutes: int = 30
    enable_real_time_monitoring: bool = True
    enable_historical_tracking: bool = True


@dataclass
class RiskLimitsConfig:
    """Risk limits configuration."""
    default_limits: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "position_size": {
            "limit_value": 0.10,
            "limit_unit": "percentage",
            "enforcement_action": "alert"
        },
        "daily_loss": {
            "limit_value": 1000.0,
            "limit_unit": "dollars",
            "enforcement_action": "halt_trading"
        },
        "sector_concentration": {
            "limit_value": 0.30,
            "limit_unit": "percentage",
            "enforcement_action": "alert"
        },
        "var_limit": {
            "limit_value": 5000.0,
            "limit_unit": "dollars",
            "enforcement_action": "reduce_position"
        },
        "volatility_limit": {
            "limit_value": 0.25,
            "limit_unit": "percentage",
            "enforcement_action": "alert"
        }
    })
    max_limits_per_portfolio: int = 20
    enable_default_limits: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "trading_risk"
    user: str = "risk_user"
    password: str = "risk_password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    echo: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    trusted_hosts: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 300  # 5 minutes


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_json_logging: bool = False


@dataclass
class RiskManagementConfig:
    """Main risk management configuration."""
    var: VaRConfig = field(default_factory=VaRConfig)
    stress_test: StressTestConfig = field(default_factory=StressTestConfig)
    correlation: CorrelationAnalysisConfig = field(default_factory=CorrelationAnalysisConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    monitoring: RiskMonitoringConfig = field(default_factory=RiskMonitoringConfig)
    limits: RiskLimitsConfig = field(default_factory=RiskLimitsConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class RiskConfigManager:
    """Risk management configuration manager."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = RiskManagementConfig()
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        logger.info("Loading risk management configuration from environment")
        
        # Database configuration
        self.config.database.host = os.getenv("DB_HOST", self.config.database.host)
        self.config.database.port = int(os.getenv("DB_PORT", self.config.database.port))
        self.config.database.name = os.getenv("DB_NAME", self.config.database.name)
        self.config.database.user = os.getenv("DB_USER", self.config.database.user)
        self.config.database.password = os.getenv("DB_PASSWORD", self.config.database.password)
        self.config.database.redis_host = os.getenv("REDIS_HOST", self.config.database.redis_host)
        self.config.database.redis_port = int(os.getenv("REDIS_PORT", self.config.database.redis_port))
        self.config.database.redis_db = int(os.getenv("REDIS_DB", self.config.database.redis_db))
        self.config.database.redis_password = os.getenv("REDIS_PASSWORD")
        
        # API configuration
        self.config.api.host = os.getenv("API_HOST", self.config.api.host)
        self.config.api.port = int(os.getenv("API_PORT", self.config.api.port))
        self.config.api.debug = os.getenv("API_DEBUG", "false").lower() == "true"
        
        # Risk monitoring configuration
        self.config.monitoring.monitoring_frequency_minutes = int(
            os.getenv("RISK_MONITORING_FREQUENCY_MINUTES", self.config.monitoring.monitoring_frequency_minutes)
        )
        
        # VaR configuration
        self.config.var.default_data_period_days = int(
            os.getenv("VAR_DEFAULT_DATA_PERIOD_DAYS", self.config.var.default_data_period_days)
        )
        self.config.var.calculation_timeout_seconds = int(
            os.getenv("VAR_CALCULATION_TIMEOUT_SECONDS", self.config.var.calculation_timeout_seconds)
        )
        
        # Stress testing configuration
        self.config.stress_test.calculation_timeout_seconds = int(
            os.getenv("STRESS_TEST_TIMEOUT_SECONDS", self.config.stress_test.calculation_timeout_seconds)
        )
        
        # Correlation analysis configuration
        self.config.correlation.default_rolling_period_days = int(
            os.getenv("CORRELATION_DEFAULT_PERIOD_DAYS", self.config.correlation.default_rolling_period_days)
        )
        
        # Logging configuration
        self.config.logging.level = os.getenv("LOG_LEVEL", self.config.logging.level)
        self.config.logging.file_path = os.getenv("LOG_FILE_PATH")
        
        logger.info("Configuration loaded successfully")
    
    def get_config(self) -> RiskManagementConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        logger.info("Updating risk management configuration")
        
        for section, values in updates.items():
            if hasattr(self.config, section):
                section_config = getattr(self.config, section)
                for key, value in values.items():
                    if hasattr(section_config, key):
                        setattr(section_config, key, value)
                        logger.debug(f"Updated {section}.{key} = {value}")
                    else:
                        logger.warning(f"Unknown configuration key: {section}.{key}")
            else:
                logger.warning(f"Unknown configuration section: {section}")
        
        logger.info("Configuration updated successfully")
    
    def validate_config(self) -> List[str]:
        """Validate the current configuration."""
        errors = []
        
        # Validate database configuration
        if not self.config.database.host:
            errors.append("Database host is required")
        
        if self.config.database.port <= 0 or self.config.database.port > 65535:
            errors.append("Database port must be between 1 and 65535")
        
        if not self.config.database.name:
            errors.append("Database name is required")
        
        if not self.config.database.user:
            errors.append("Database user is required")
        
        # Validate API configuration
        if self.config.api.port <= 0 or self.config.api.port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        # Validate VaR configuration
        if self.config.var.default_data_period_days < self.config.var.min_data_period_days:
            errors.append("VaR default data period is below minimum")
        
        if self.config.var.default_data_period_days > self.config.var.max_data_period_days:
            errors.append("VaR default data period exceeds maximum")
        
        # Validate confidence levels
        for level in self.config.var.default_confidence_levels:
            if not (0 < level < 1):
                errors.append(f"Invalid confidence level: {level}")
        
        # Validate monitoring frequency
        if (self.config.monitoring.monitoring_frequency_minutes < 
            self.config.monitoring.min_monitoring_frequency_minutes):
            errors.append("Monitoring frequency is below minimum")
        
        if (self.config.monitoring.monitoring_frequency_minutes > 
            self.config.monitoring.max_monitoring_frequency_minutes):
            errors.append("Monitoring frequency exceeds maximum")
        
        return errors
    
    def get_default_risk_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get default risk limits configuration."""
        return self.config.limits.default_limits.copy()
    
    def get_available_scenarios(self) -> List[str]:
        """Get available stress test scenarios."""
        return self.config.stress_test.default_scenarios.copy()
    
    def get_supported_report_formats(self) -> List[str]:
        """Get supported compliance report formats."""
        return self.config.compliance.supported_formats.copy()
    
    def get_alert_channels(self) -> List[str]:
        """Get available alert channels."""
        return self.config.monitoring.alert_channels.copy()
    
    def is_configuration_valid(self) -> bool:
        """Check if the current configuration is valid."""
        return len(self.validate_config()) == 0


# Global configuration manager instance
_config_manager = RiskConfigManager()


def get_risk_config() -> RiskManagementConfig:
    """Get the global risk management configuration."""
    return _config_manager.get_config()


def get_config_manager() -> RiskConfigManager:
    """Get the global configuration manager."""
    return _config_manager


def update_risk_config(updates: Dict[str, Any]) -> None:
    """Update the global risk management configuration."""
    _config_manager.update_config(updates)


def validate_risk_config() -> List[str]:
    """Validate the global risk management configuration."""
    return _config_manager.validate_config()


def is_risk_config_valid() -> bool:
    """Check if the global risk management configuration is valid."""
    return _config_manager.is_configuration_valid()

