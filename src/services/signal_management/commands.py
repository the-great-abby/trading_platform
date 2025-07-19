"""
Signal Generation & Validation Commands for CQRS Trading Platform
Comprehensive signal lifecycle management commands
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from ...cqrs.base import Command


class SignalType(Enum):
    """Signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SHORT = "short"
    COVER = "cover"
    ALERT = "alert"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SignalSource(Enum):
    """Signal sources"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    NEWS = "news"
    MACHINE_LEARNING = "ml"
    QUANTITATIVE = "quant"
    DISCRETIONARY = "discretionary"
    HYBRID = "hybrid"
    EXTERNAL = "external"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    EXTREME = "extreme"


class SignalStatus(Enum):
    """Signal status"""
    GENERATED = "generated"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class SignalPriority(Enum):
    """Signal priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class GenerateSignalCommand(Command):
    """Command to generate a new trading signal"""
    # Signal details
    signal_type: SignalType
    signal_source: SignalSource
    symbol: str
    strength: SignalStrength
    priority: SignalPriority
    
    # Signal data
    price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    
    # Signal metadata
    confidence_score: Optional[float] = None
    signal_data: Dict[str, Any] = field(default_factory=dict)
    indicators: Dict[str, Any] = field(default_factory=dict)
    
    # Time and validity
    generated_at: datetime = None
    valid_until: Optional[datetime] = None
    timeframes: List[str] = field(default_factory=list)
    
    # Strategy and context
    strategy_id: Optional[str] = None
    strategy_name: Optional[str] = None
    market_context: Dict[str, Any] = field(default_factory=dict)
    
    # User and account
    user_id: str = None
    account_id: str = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.signal_id is None:
            self.signal_id = uuid4()
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


@dataclass
class ValidateSignalCommand(Command):
    """Command to validate a trading signal"""
    signal_id: str
    
    # Validation criteria
    validation_rules: List[str] = field(default_factory=list)
    validation_thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # Validation context
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    risk_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Validation metadata
    validator_id: Optional[str] = None
    validation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApproveSignalCommand(Command):
    """Command to approve a validated signal"""
    signal_id: str
    approval_reason: str = "manual_approval"
    approval_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RejectSignalCommand(Command):
    """Command to reject a signal"""
    signal_id: str
    rejection_reason: str
    rejection_details: Dict[str, Any] = field(default_factory=dict)
    rejection_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecuteSignalCommand(Command):
    """Command to execute a signal"""
    signal_id: str
    execution_strategy: str = "best_execution"
    execution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateSignalCommand(Command):
    """Command to update a signal"""
    signal_id: str
    
    # Updatable fields
    strength: Optional[SignalStrength] = None
    priority: Optional[SignalPriority] = None
    price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    confidence_score: Optional[float] = None
    
    # Metadata updates
    signal_data: Optional[Dict[str, Any]] = None
    indicators: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Reason for update
    update_reason: str = "manual_update"


@dataclass
class CancelSignalCommand(Command):
    """Command to cancel a signal"""
    signal_id: str
    cancellation_reason: str = "manual_cancellation"
    cancellation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpireSignalCommand(Command):
    """Command to expire a signal"""
    signal_id: str
    expiration_reason: str = "time_expired"
    expiration_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveSignalCommand(Command):
    """Command to archive a signal"""
    signal_id: str
    archive_reason: str = "manual_archive"
    archive_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkSignalToOrderCommand(Command):
    """Command to link signal to order"""
    signal_id: str
    order_id: str
    link_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkSignalToStrategyCommand(Command):
    """Command to link signal to strategy"""
    signal_id: str
    strategy_id: str
    link_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateSignalPerformanceCommand(Command):
    """Command to update signal performance metrics"""
    signal_id: str
    performance_metrics: Dict[str, Any]
    performance_type: str = "live"
    performance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateSignalAnalyticsCommand(Command):
    """Command to update signal analytics"""
    signal_id: str
    analytics_type: str
    analytics_data: Dict[str, Any]
    analytics_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalHeartbeatCommand(Command):
    """Command to send heartbeat for signal monitoring"""
    signal_id: str
    heartbeat_time: datetime = None
    heartbeat_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.heartbeat_time is None:
            self.heartbeat_time = datetime.utcnow()


@dataclass
class SignalAlertCommand(Command):
    """Command to create signal alert"""
    signal_id: str
    alert_type: str
    alert_message: str
    alert_severity: str = "info"
    alert_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalSnapshotCommand(Command):
    """Command to create signal snapshot"""
    signal_id: str
    snapshot_type: str = "state"
    snapshot_data: Dict[str, Any]
    snapshot_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalAuditCommand(Command):
    """Command to audit a signal"""
    signal_id: str
    audit_type: str = "comprehensive"
    audit_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalReconciliationCommand(Command):
    """Command to reconcile signal with external system"""
    signal_id: str
    external_system: str
    reconciliation_data: Dict[str, Any]
    reconciliation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalIntegrationCommand(Command):
    """Command to integrate signal with external systems"""
    signal_id: str
    integration_system: str
    integration_data: Dict[str, Any]
    integration_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalWorkflowCommand(Command):
    """Command to update signal workflow"""
    signal_id: str
    workflow_step: str
    workflow_data: Dict[str, Any]
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalEscalationCommand(Command):
    """Command to escalate signal"""
    signal_id: str
    escalation_level: str
    escalation_reason: str
    escalation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalComplianceCommand(Command):
    """Command to update signal compliance"""
    signal_id: str
    compliance_status: str
    compliance_checks: List[str] = field(default_factory=list)
    compliance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalCorrelationCommand(Command):
    """Command to update signal correlation analysis"""
    signal_id: str
    correlation_data: Dict[str, Any]
    correlation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalVolatilityCommand(Command):
    """Command to update signal volatility analysis"""
    signal_id: str
    volatility_data: Dict[str, Any]
    volatility_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalAccuracyCommand(Command):
    """Command to update signal accuracy metrics"""
    signal_id: str
    accuracy_metrics: Dict[str, Any]
    accuracy_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalPrecisionCommand(Command):
    """Command to update signal precision metrics"""
    signal_id: str
    precision_metrics: Dict[str, Any]
    precision_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRecallCommand(Command):
    """Command to update signal recall metrics"""
    signal_id: str
    recall_metrics: Dict[str, Any]
    recall_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalF1ScoreCommand(Command):
    """Command to update signal F1 score"""
    signal_id: str
    f1_score: float
    f1_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalROICommand(Command):
    """Command to update signal ROI"""
    signal_id: str
    roi_data: Dict[str, Any]
    roi_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalSharpeCommand(Command):
    """Command to update signal Sharpe ratio"""
    signal_id: str
    sharpe_ratio: Decimal
    sharpe_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalDrawdownCommand(Command):
    """Command to update signal drawdown analysis"""
    signal_id: str
    drawdown_data: Dict[str, Any]
    drawdown_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalAlphaCommand(Command):
    """Command to update signal alpha calculation"""
    signal_id: str
    alpha_value: Decimal
    alpha_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalBetaCommand(Command):
    """Command to update signal beta calculation"""
    signal_id: str
    beta_value: Decimal
    beta_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalInformationRatioCommand(Command):
    """Command to update signal information ratio"""
    signal_id: str
    information_ratio: Decimal
    ir_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalCalmarCommand(Command):
    """Command to update signal Calmar ratio"""
    signal_id: str
    calmar_ratio: Decimal
    calmar_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalSortinoCommand(Command):
    """Command to update signal Sortino ratio"""
    signal_id: str
    sortino_ratio: Decimal
    sortino_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalTreynorCommand(Command):
    """Command to update signal Treynor ratio"""
    signal_id: str
    treynor_ratio: Decimal
    treynor_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalJensenCommand(Command):
    """Command to update signal Jensen's alpha"""
    signal_id: str
    jensen_alpha: Decimal
    jensen_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalTrackingErrorCommand(Command):
    """Command to update signal tracking error"""
    signal_id: str
    tracking_error: Decimal
    tracking_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalVaRCommand(Command):
    """Command to update signal Value at Risk"""
    signal_id: str
    var_data: Dict[str, Any]
    var_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalCVaRCommand(Command):
    """Command to update signal Conditional Value at Risk"""
    signal_id: str
    cvar_data: Dict[str, Any]
    cvar_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalStressTestCommand(Command):
    """Command to perform signal stress test"""
    signal_id: str
    stress_test_config: Dict[str, Any]
    stress_test_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalScenarioCommand(Command):
    """Command to run signal scenario analysis"""
    signal_id: str
    scenario_config: Dict[str, Any]
    scenario_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalMonteCarloCommand(Command):
    """Command to run signal Monte Carlo simulation"""
    signal_id: str
    monte_carlo_config: Dict[str, Any]
    monte_carlo_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRegimeCommand(Command):
    """Command to update signal regime analysis"""
    signal_id: str
    regime_data: Dict[str, Any]
    regime_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalFactorCommand(Command):
    """Command to update signal factor analysis"""
    signal_id: str
    factor_data: Dict[str, Any]
    factor_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalAttributionCommand(Command):
    """Command to update signal attribution analysis"""
    signal_id: str
    attribution_data: Dict[str, Any]
    attribution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalBacktestCommand(Command):
    """Command to backtest a signal"""
    signal_id: str
    start_date: datetime
    end_date: datetime
    backtest_config: Dict[str, Any] = field(default_factory=dict)
    backtest_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalOptimizationCommand(Command):
    """Command to optimize signal parameters"""
    signal_id: str
    optimization_target: str
    optimization_params: Dict[str, Any] = field(default_factory=dict)
    optimization_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalValidationCommand(Command):
    """Command to validate signal parameters"""
    signal_id: str
    validation_rules: List[str] = field(default_factory=list)
    validation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalTestingCommand(Command):
    """Command to test signal"""
    signal_id: str
    test_config: Dict[str, Any] = field(default_factory=dict)
    test_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalDeploymentCommand(Command):
    """Command to deploy signal"""
    signal_id: str
    deployment_target: str
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    deployment_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalMonitoringCommand(Command):
    """Command to update signal monitoring"""
    signal_id: str
    monitoring_data: Dict[str, Any]
    monitoring_type: str = "performance"
    monitoring_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalReportingCommand(Command):
    """Command to generate signal report"""
    signal_id: str
    report_type: str
    report_data: Dict[str, Any]
    report_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalNotificationCommand(Command):
    """Command to send signal notification"""
    signal_id: str
    notification_type: str
    notification_data: Dict[str, Any]
    notification_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalDistributionCommand(Command):
    """Command to distribute signal"""
    signal_id: str
    distribution_targets: List[str] = field(default_factory=list)
    distribution_data: Dict[str, Any] = field(default_factory=dict)
    distribution_metadata: Dict[str, Any] = field(default_factory=dict) 