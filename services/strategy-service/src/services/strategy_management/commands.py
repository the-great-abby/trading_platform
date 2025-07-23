"""
Strategy Management Commands for CQRS Trading Platform
Comprehensive strategy lifecycle management commands
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from ...cqrs.base import Command


class StrategyType(Enum):
    """Strategy types"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    ARBITRAGE = "arbitrage"
    OPTIONS = "options"
    SENTIMENT = "sentiment"
    MACHINE_LEARNING = "ml"
    QUANTITATIVE = "quant"
    DISCRETIONARY = "discretionary"
    HYBRID = "hybrid"


class StrategyStatus(Enum):
    """Strategy status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    TESTING = "testing"
    DEPLOYING = "deploying"
    ERROR = "error"


class StrategyRiskLevel(Enum):
    """Strategy risk levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    HIGH_RISK = "high_risk"


class StrategyCategory(Enum):
    """Strategy categories"""
    EQUITY = "equity"
    OPTIONS = "options"
    FUTURES = "futures"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITIES = "commodities"
    FIXED_INCOME = "fixed_income"
    ALTERNATIVES = "alternatives"


@dataclass
class CreateStrategyCommand(Command):
    """Command to create a new strategy"""
    # Strategy details
    name: str
    description: str
    strategy_type: StrategyType
    category: StrategyCategory
    risk_level: StrategyRiskLevel
    
    # Configuration
    parameters: Dict[str, Any] = field(default_factory=dict)
    symbols: List[str] = field(default_factory=list)
    timeframes: List[str] = field(default_factory=list)
    
    # Risk and limits
    max_position_size: Optional[Decimal] = None
    max_daily_loss: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    target_return: Optional[Decimal] = None
    
    # Execution
    execution_strategy: str = "best_execution"
    order_types: List[str] = field(default_factory=list)
    
    # User and account
    user_id: str = None
    account_id: str = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.strategy_id is None:
            self.strategy_id = uuid4()


@dataclass
class UpdateStrategyCommand(Command):
    """Command to update an existing strategy"""
    strategy_id: str
    
    # Updatable fields
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    
    # Risk updates
    max_position_size: Optional[Decimal] = None
    max_daily_loss: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    target_return: Optional[Decimal] = None
    
    # Metadata updates
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Reason for update
    update_reason: str = "manual_update"


@dataclass
class ActivateStrategyCommand(Command):
    """Command to activate a strategy"""
    strategy_id: str
    activation_reason: str = "manual_activation"
    activation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PauseStrategyCommand(Command):
    """Command to pause a strategy"""
    strategy_id: str
    pause_reason: str = "manual_pause"
    pause_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StopStrategyCommand(Command):
    """Command to stop a strategy"""
    strategy_id: str
    stop_reason: str = "manual_stop"
    stop_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveStrategyCommand(Command):
    """Command to archive a strategy"""
    strategy_id: str
    archive_reason: str = "manual_archive"
    archive_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeployStrategyCommand(Command):
    """Command to deploy a strategy"""
    strategy_id: str
    deployment_target: str
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    deployment_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestStrategyCommand(Command):
    """Command to test a strategy"""
    strategy_id: str
    test_config: Dict[str, Any] = field(default_factory=dict)
    test_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidateStrategyCommand(Command):
    """Command to validate a strategy"""
    strategy_id: str
    validation_rules: List[str] = field(default_factory=list)
    validation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizeStrategyCommand(Command):
    """Command to optimize strategy parameters"""
    strategy_id: str
    optimization_target: str
    optimization_params: Dict[str, Any] = field(default_factory=dict)
    optimization_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestStrategyCommand(Command):
    """Command to backtest a strategy"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    backtest_config: Dict[str, Any] = field(default_factory=dict)
    backtest_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateStrategyPerformanceCommand(Command):
    """Command to update strategy performance metrics"""
    strategy_id: str
    performance_metrics: Dict[str, Any]
    performance_type: str = "live"
    performance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateStrategyRiskCommand(Command):
    """Command to update strategy risk parameters"""
    strategy_id: str
    risk_metrics: Dict[str, Any]
    risk_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateStrategyStatusCommand(Command):
    """Command to update strategy status"""
    strategy_id: str
    new_status: StrategyStatus
    status_reason: str
    status_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AddStrategyNoteCommand(Command):
    """Command to add a note to a strategy"""
    strategy_id: str
    note: str
    note_type: str = "general"
    note_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateStrategyTagsCommand(Command):
    """Command to update strategy tags"""
    strategy_id: str
    tags: List[str]
    operation: str = "replace"


@dataclass
class LinkStrategyToSignalCommand(Command):
    """Command to link strategy to trading signal"""
    strategy_id: str
    signal_id: str
    link_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateStrategyConfigurationCommand(Command):
    """Command to update strategy configuration"""
    strategy_id: str
    configuration: Dict[str, Any]
    config_type: str = "parameters"
    config_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyHeartbeatCommand(Command):
    """Command to send heartbeat for strategy monitoring"""
    strategy_id: str
    heartbeat_time: datetime = None
    heartbeat_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.heartbeat_time is None:
            self.heartbeat_time = datetime.utcnow()


@dataclass
class StrategyAlertCommand(Command):
    """Command to create strategy alert"""
    strategy_id: str
    alert_type: str
    alert_message: str
    alert_severity: str = "info"
    alert_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategySnapshotCommand(Command):
    """Command to create strategy snapshot"""
    strategy_id: str
    snapshot_type: str = "state"
    snapshot_data: Dict[str, Any]
    snapshot_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyAuditCommand(Command):
    """Command to audit a strategy"""
    strategy_id: str
    audit_type: str = "comprehensive"
    audit_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyReconciliationCommand(Command):
    """Command to reconcile strategy with external system"""
    strategy_id: str
    external_system: str
    reconciliation_data: Dict[str, Any]
    reconciliation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyIntegrationCommand(Command):
    """Command to integrate strategy with external systems"""
    strategy_id: str
    integration_system: str
    integration_data: Dict[str, Any]
    integration_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyWorkflowCommand(Command):
    """Command to update strategy workflow"""
    strategy_id: str
    workflow_step: str
    workflow_data: Dict[str, Any]
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyEscalationCommand(Command):
    """Command to escalate strategy"""
    strategy_id: str
    escalation_level: str
    escalation_reason: str
    escalation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyComplianceCommand(Command):
    """Command to update strategy compliance"""
    strategy_id: str
    compliance_status: str
    compliance_checks: List[str] = field(default_factory=list)
    compliance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyAnalyticsCommand(Command):
    """Command to update strategy analytics"""
    strategy_id: str
    analytics_type: str
    analytics_data: Dict[str, Any]
    analytics_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyCostsCommand(Command):
    """Command to update strategy costs"""
    strategy_id: str
    costs_data: Dict[str, Any]
    costs_type: str = "execution"
    costs_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyTimingCommand(Command):
    """Command to update strategy timing"""
    strategy_id: str
    timing_data: Dict[str, Any]
    timing_type: str = "execution"
    timing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyCorrelationCommand(Command):
    """Command to update strategy correlation analysis"""
    strategy_id: str
    correlation_data: Dict[str, Any]
    correlation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyVolatilityCommand(Command):
    """Command to update strategy volatility analysis"""
    strategy_id: str
    volatility_data: Dict[str, Any]
    volatility_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategySharpeCommand(Command):
    """Command to update strategy Sharpe ratio"""
    strategy_id: str
    sharpe_ratio: Decimal
    sharpe_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyDrawdownCommand(Command):
    """Command to update strategy drawdown analysis"""
    strategy_id: str
    drawdown_data: Dict[str, Any]
    drawdown_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyAlphaCommand(Command):
    """Command to update strategy alpha calculation"""
    strategy_id: str
    alpha_value: Decimal
    alpha_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyBetaCommand(Command):
    """Command to update strategy beta calculation"""
    strategy_id: str
    beta_value: Decimal
    beta_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyInformationRatioCommand(Command):
    """Command to update strategy information ratio"""
    strategy_id: str
    information_ratio: Decimal
    ir_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyCalmarCommand(Command):
    """Command to update strategy Calmar ratio"""
    strategy_id: str
    calmar_ratio: Decimal
    calmar_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategySortinoCommand(Command):
    """Command to update strategy Sortino ratio"""
    strategy_id: str
    sortino_ratio: Decimal
    sortino_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyTreynorCommand(Command):
    """Command to update strategy Treynor ratio"""
    strategy_id: str
    treynor_ratio: Decimal
    treynor_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyJensenCommand(Command):
    """Command to update strategy Jensen's alpha"""
    strategy_id: str
    jensen_alpha: Decimal
    jensen_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyTrackingErrorCommand(Command):
    """Command to update strategy tracking error"""
    strategy_id: str
    tracking_error: Decimal
    tracking_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyVaRCommand(Command):
    """Command to update strategy Value at Risk"""
    strategy_id: str
    var_data: Dict[str, Any]
    var_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyCVaRCommand(Command):
    """Command to update strategy Conditional Value at Risk"""
    strategy_id: str
    cvar_data: Dict[str, Any]
    cvar_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyStressTestCommand(Command):
    """Command to perform strategy stress test"""
    strategy_id: str
    stress_test_config: Dict[str, Any]
    stress_test_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyScenarioCommand(Command):
    """Command to run strategy scenario analysis"""
    strategy_id: str
    scenario_config: Dict[str, Any]
    scenario_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyMonteCarloCommand(Command):
    """Command to run strategy Monte Carlo simulation"""
    strategy_id: str
    monte_carlo_config: Dict[str, Any]
    monte_carlo_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyRegimeCommand(Command):
    """Command to update strategy regime analysis"""
    strategy_id: str
    regime_data: Dict[str, Any]
    regime_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyFactorCommand(Command):
    """Command to update strategy factor analysis"""
    strategy_id: str
    factor_data: Dict[str, Any]
    factor_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyAttributionCommand(Command):
    """Command to update strategy attribution analysis"""
    strategy_id: str
    attribution_data: Dict[str, Any]
    attribution_metadata: Dict[str, Any] = field(default_factory=dict) 