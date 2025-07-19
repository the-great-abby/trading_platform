"""
Order Management Commands for CQRS Trading Platform
Comprehensive order lifecycle management commands
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from ...cqrs.base import Command


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"


class TimeInForce(Enum):
    """Time in force options"""
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    GTD = "gtd"  # Good Till Date


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    PENDING_CANCEL = "pending_cancel"


class OrderSource(Enum):
    """Order sources"""
    MANUAL = "manual"
    STRATEGY = "strategy"
    ALGO = "algo"
    API = "api"
    MOBILE = "mobile"
    WEB = "web"


@dataclass
class CreateOrderCommand(Command):
    """Command to create a new order"""
    # Order details
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    
    # Pricing
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    trailing_stop_pct: Optional[Decimal] = None
    
    # Time and execution
    time_in_force: TimeInForce = TimeInForce.DAY
    good_till_date: Optional[datetime] = None
    
    # Strategy and metadata
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    
    # Advanced order types
    iceberg_visible_quantity: Optional[int] = None
    twap_duration: Optional[timedelta] = None
    vwap_volume_target: Optional[Decimal] = None
    
    # Risk and compliance
    max_slippage: Optional[Decimal] = None
    max_impact: Optional[Decimal] = None
    
    # User and account
    user_id: str = None
    account_id: str = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.order_id is None:
            self.order_id = uuid4()


@dataclass
class UpdateOrderCommand(Command):
    """Command to update an existing order"""
    order_id: str
    
    # Updatable fields
    quantity: Optional[int] = None
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[TimeInForce] = None
    good_till_date: Optional[datetime] = None
    
    # Metadata updates
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Reason for update
    update_reason: str = "manual_update"


@dataclass
class CancelOrderCommand(Command):
    """Command to cancel an order"""
    order_id: str
    cancel_reason: str = "manual_cancellation"
    cancel_source: OrderSource = OrderSource.MANUAL


@dataclass
class ReplaceOrderCommand(Command):
    """Command to replace an order with a new one"""
    original_order_id: str
    
    # New order details
    new_quantity: Optional[int] = None
    new_limit_price: Optional[Decimal] = None
    new_stop_price: Optional[Decimal] = None
    new_time_in_force: Optional[TimeInForce] = None
    
    # Replacement reason
    replacement_reason: str = "manual_replacement"


@dataclass
class RouteOrderCommand(Command):
    """Command to route an order to a specific venue"""
    order_id: str
    venue: str
    routing_strategy: str = "best_execution"
    routing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecuteOrderCommand(Command):
    """Command to execute an order"""
    order_id: str
    execution_venue: str
    execution_price: Decimal
    execution_quantity: int
    execution_time: datetime = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.execution_time is None:
            self.execution_time = datetime.utcnow()


@dataclass
class PartialFillCommand(Command):
    """Command to record a partial fill"""
    order_id: str
    fill_quantity: int
    fill_price: Decimal
    fill_time: datetime = None
    fill_venue: str = None
    fill_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.fill_time is None:
            self.fill_time = datetime.utcnow()


@dataclass
class CompleteFillCommand(Command):
    """Command to complete an order fill"""
    order_id: str
    final_fill_quantity: int
    final_fill_price: Decimal
    fill_time: datetime = None
    fill_venue: str = None
    fill_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.fill_time is None:
            self.fill_time = datetime.utcnow()


@dataclass
class RejectOrderCommand(Command):
    """Command to reject an order"""
    order_id: str
    rejection_reason: str
    rejection_code: str = None
    rejection_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpireOrderCommand(Command):
    """Command to expire an order"""
    order_id: str
    expiration_reason: str = "time_expired"
    expiration_time: datetime = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.expiration_time is None:
            self.expiration_time = datetime.utcnow()


@dataclass
class SuspendOrderCommand(Command):
    """Command to suspend an order"""
    order_id: str
    suspension_reason: str
    suspension_duration: Optional[timedelta] = None
    suspension_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResumeOrderCommand(Command):
    """Command to resume a suspended order"""
    order_id: str
    resume_reason: str = "manual_resume"


@dataclass
class UpdateOrderStatusCommand(Command):
    """Command to update order status"""
    order_id: str
    new_status: OrderStatus
    status_reason: str
    status_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AddOrderNoteCommand(Command):
    """Command to add a note to an order"""
    order_id: str
    note: str
    note_type: str = "general"
    note_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderTagsCommand(Command):
    """Command to update order tags"""
    order_id: str
    tags: List[str]
    operation: str = "replace"  # replace, add, remove


@dataclass
class LinkOrdersCommand(Command):
    """Command to link related orders"""
    primary_order_id: str
    linked_order_ids: List[str]
    link_type: str = "parent_child"
    link_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderRiskCommand(Command):
    """Command to update order risk parameters"""
    order_id: str
    max_slippage: Optional[Decimal] = None
    max_impact: Optional[Decimal] = None
    risk_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidateOrderCommand(Command):
    """Command to validate an order before execution"""
    order_id: str
    validation_rules: List[str] = field(default_factory=list)
    validation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreflightOrderCommand(Command):
    """Command to perform preflight checks on an order"""
    order_id: str
    preflight_checks: List[str] = field(default_factory=list)
    preflight_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleOrderCommand(Command):
    """Command to schedule an order for future execution"""
    order_id: str
    scheduled_time: datetime
    schedule_type: str = "absolute"  # absolute, relative, conditional
    schedule_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CancelScheduledOrderCommand(Command):
    """Command to cancel a scheduled order"""
    order_id: str
    cancellation_reason: str = "manual_cancellation"


@dataclass
class UpdateOrderExecutionCommand(Command):
    """Command to update order execution parameters"""
    order_id: str
    execution_strategy: str = None
    execution_venue: str = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderHeartbeatCommand(Command):
    """Command to send heartbeat for order monitoring"""
    order_id: str
    heartbeat_time: datetime = None
    heartbeat_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.heartbeat_time is None:
            self.heartbeat_time = datetime.utcnow()


@dataclass
class UpdateOrderComplianceCommand(Command):
    """Command to update order compliance status"""
    order_id: str
    compliance_status: str
    compliance_checks: List[str] = field(default_factory=list)
    compliance_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderAuditCommand(Command):
    """Command to audit an order"""
    order_id: str
    audit_type: str = "comprehensive"
    audit_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderAnalyticsCommand(Command):
    """Command to update order analytics"""
    order_id: str
    analytics_data: Dict[str, Any]
    analytics_type: str = "execution_quality"


@dataclass
class LinkOrderToSignalCommand(Command):
    """Command to link an order to a trading signal"""
    order_id: str
    signal_id: str
    link_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderStrategyCommand(Command):
    """Command to update order strategy information"""
    order_id: str
    strategy_id: str
    strategy_parameters: Dict[str, Any] = field(default_factory=dict)
    strategy_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderReconciliationCommand(Command):
    """Command to reconcile order with external system"""
    order_id: str
    external_system: str
    reconciliation_data: Dict[str, Any]
    reconciliation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderCostsCommand(Command):
    """Command to update order costs"""
    order_id: str
    commission: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    cost_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderPerformanceCommand(Command):
    """Command to update order performance metrics"""
    order_id: str
    performance_metrics: Dict[str, Any]
    performance_type: str = "execution_quality"


@dataclass
class UpdateOrderRoutingCommand(Command):
    """Command to update order routing information"""
    order_id: str
    routing_strategy: str
    routing_venues: List[str] = field(default_factory=list)
    routing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderLifecycleCommand(Command):
    """Command to manage order lifecycle"""
    order_id: str
    lifecycle_event: str
    lifecycle_data: Dict[str, Any]
    lifecycle_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderPriorityCommand(Command):
    """Command to update order priority"""
    order_id: str
    priority: int
    priority_reason: str = "manual_update"
    priority_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderEscalationCommand(Command):
    """Command to escalate an order"""
    order_id: str
    escalation_level: str
    escalation_reason: str
    escalation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderAlertsCommand(Command):
    """Command to update order alerts"""
    order_id: str
    alert_type: str
    alert_message: str
    alert_severity: str = "info"
    alert_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderSnapshotCommand(Command):
    """Command to create order snapshot"""
    order_id: str
    snapshot_type: str = "state"
    snapshot_data: Dict[str, Any]
    snapshot_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateOrderWorkflowCommand(Command):
    """Command to update order workflow"""
    order_id: str
    workflow_step: str
    workflow_data: Dict[str, Any]
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderIntegrationCommand(Command):
    """Command to integrate order with external systems"""
    order_id: str
    integration_system: str
    integration_data: Dict[str, Any]
    integration_metadata: Dict[str, Any] = field(default_factory=dict) 