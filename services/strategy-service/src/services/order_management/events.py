"""
Order Management Events for CQRS Trading Platform
Comprehensive order lifecycle events for event sourcing
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal
from enum import Enum
from uuid import UUID

from ...cqrs.base import Event
from .commands import OrderType, OrderSide, TimeInForce, OrderStatus, OrderSource


@dataclass
class OrderCreatedEvent(Event):
    """Event when an order is created"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: TimeInForce
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    user_id: str
    account_id: str
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class OrderSubmittedEvent(Event):
    """Event when an order is submitted to market"""
    order_id: str
    submitted_at: datetime = None
    submission_venue: str = None
    submission_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.submitted_at is None:
            self.submitted_at = datetime.utcnow()


@dataclass
class OrderUpdatedEvent(Event):
    """Event when an order is updated"""
    order_id: str
    updated_fields: Dict[str, Any]
    update_reason: str
    updated_at: datetime = None
    update_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderCancelledEvent(Event):
    """Event when an order is cancelled"""
    order_id: str
    cancel_reason: str
    cancel_source: OrderSource
    cancelled_at: datetime = None
    cancel_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.cancelled_at is None:
            self.cancelled_at = datetime.utcnow()


@dataclass
class OrderReplacedEvent(Event):
    """Event when an order is replaced"""
    original_order_id: str
    new_order_id: str
    replacement_reason: str
    replaced_at: datetime = None
    replacement_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.replaced_at is None:
            self.replaced_at = datetime.utcnow()


@dataclass
class OrderRoutedEvent(Event):
    """Event when an order is routed to a venue"""
    order_id: str
    venue: str
    routing_strategy: str
    routed_at: datetime = None
    routing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.routed_at is None:
            self.routed_at = datetime.utcnow()


@dataclass
class OrderExecutedEvent(Event):
    """Event when an order is executed"""
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
class OrderPartiallyFilledEvent(Event):
    """Event when an order is partially filled"""
    order_id: str
    fill_quantity: int
    fill_price: Decimal
    remaining_quantity: int
    fill_time: datetime = None
    fill_venue: str = None
    fill_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.fill_time is None:
            self.fill_time = datetime.utcnow()


@dataclass
class OrderFilledEvent(Event):
    """Event when an order is completely filled"""
    order_id: str
    total_fill_quantity: int
    average_fill_price: Decimal
    fill_time: datetime = None
    fill_venue: str = None
    fill_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.fill_time is None:
            self.fill_time = datetime.utcnow()


@dataclass
class OrderRejectedEvent(Event):
    """Event when an order is rejected"""
    order_id: str
    rejection_reason: str
    rejection_code: str = None
    rejected_at: datetime = None
    rejection_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.rejected_at is None:
            self.rejected_at = datetime.utcnow()


@dataclass
class OrderExpiredEvent(Event):
    """Event when an order expires"""
    order_id: str
    expiration_reason: str
    expired_at: datetime = None
    expiration_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.expired_at is None:
            self.expired_at = datetime.utcnow()


@dataclass
class OrderSuspendedEvent(Event):
    """Event when an order is suspended"""
    order_id: str
    suspension_reason: str
    suspension_duration: Optional[timedelta] = None
    suspended_at: datetime = None
    suspension_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.suspended_at is None:
            self.suspended_at = datetime.utcnow()


@dataclass
class OrderResumedEvent(Event):
    """Event when an order is resumed"""
    order_id: str
    resume_reason: str
    resumed_at: datetime = None
    resume_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.resumed_at is None:
            self.resumed_at = datetime.utcnow()


@dataclass
class OrderStatusChangedEvent(Event):
    """Event when order status changes"""
    order_id: str
    old_status: OrderStatus
    new_status: OrderStatus
    status_reason: str
    changed_at: datetime = None
    status_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.changed_at is None:
            self.changed_at = datetime.utcnow()


@dataclass
class OrderNoteAddedEvent(Event):
    """Event when a note is added to an order"""
    order_id: str
    note: str
    note_type: str
    added_at: datetime = None
    note_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.added_at is None:
            self.added_at = datetime.utcnow()


@dataclass
class OrderTagsUpdatedEvent(Event):
    """Event when order tags are updated"""
    order_id: str
    old_tags: List[str]
    new_tags: List[str]
    operation: str
    updated_at: datetime = None
    tag_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrdersLinkedEvent(Event):
    """Event when orders are linked"""
    primary_order_id: str
    linked_order_ids: List[str]
    link_type: str
    linked_at: datetime = None
    link_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.linked_at is None:
            self.linked_at = datetime.utcnow()


@dataclass
class OrderRiskUpdatedEvent(Event):
    """Event when order risk parameters are updated"""
    order_id: str
    old_risk_params: Dict[str, Any]
    new_risk_params: Dict[str, Any]
    updated_at: datetime = None
    risk_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderValidatedEvent(Event):
    """Event when an order is validated"""
    order_id: str
    validation_rules: List[str]
    validation_result: bool
    validation_details: Dict[str, Any]
    validated_at: datetime = None
    validation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.validated_at is None:
            self.validated_at = datetime.utcnow()


@dataclass
class OrderPreflightCompletedEvent(Event):
    """Event when order preflight checks are completed"""
    order_id: str
    preflight_checks: List[str]
    preflight_result: bool
    preflight_details: Dict[str, Any]
    completed_at: datetime = None
    preflight_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()


@dataclass
class OrderScheduledEvent(Event):
    """Event when an order is scheduled for future execution"""
    order_id: str
    scheduled_time: datetime
    schedule_type: str
    scheduled_at: datetime = None
    schedule_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.scheduled_at is None:
            self.scheduled_at = datetime.utcnow()


@dataclass
class ScheduledOrderCancelledEvent(Event):
    """Event when a scheduled order is cancelled"""
    order_id: str
    cancellation_reason: str
    cancelled_at: datetime = None
    cancellation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.cancelled_at is None:
            self.cancelled_at = datetime.utcnow()


@dataclass
class OrderExecutionUpdatedEvent(Event):
    """Event when order execution parameters are updated"""
    order_id: str
    execution_strategy: str
    execution_venue: str
    updated_at: datetime = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderHeartbeatEvent(Event):
    """Event for order heartbeat monitoring"""
    order_id: str
    heartbeat_time: datetime = None
    heartbeat_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.heartbeat_time is None:
            self.heartbeat_time = datetime.utcnow()


@dataclass
class OrderComplianceUpdatedEvent(Event):
    """Event when order compliance status is updated"""
    order_id: str
    compliance_status: str
    compliance_checks: List[str]
    updated_at: datetime = None
    compliance_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderAuditedEvent(Event):
    """Event when an order is audited"""
    order_id: str
    audit_type: str
    audit_result: Dict[str, Any]
    audited_at: datetime = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.audited_at is None:
            self.audited_at = datetime.utcnow()


@dataclass
class OrderAnalyticsUpdatedEvent(Event):
    """Event when order analytics are updated"""
    order_id: str
    analytics_type: str
    analytics_data: Dict[str, Any]
    updated_at: datetime = None
    analytics_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderSignalLinkedEvent(Event):
    """Event when an order is linked to a trading signal"""
    order_id: str
    signal_id: str
    linked_at: datetime = None
    link_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.linked_at is None:
            self.linked_at = datetime.utcnow()


@dataclass
class OrderStrategyUpdatedEvent(Event):
    """Event when order strategy information is updated"""
    order_id: str
    strategy_id: str
    strategy_parameters: Dict[str, Any]
    updated_at: datetime = None
    strategy_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderReconciledEvent(Event):
    """Event when an order is reconciled with external system"""
    order_id: str
    external_system: str
    reconciliation_result: Dict[str, Any]
    reconciled_at: datetime = None
    reconciliation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.reconciled_at is None:
            self.reconciled_at = datetime.utcnow()


@dataclass
class OrderCostsUpdatedEvent(Event):
    """Event when order costs are updated"""
    order_id: str
    commission: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    updated_at: datetime = None
    cost_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderPerformanceUpdatedEvent(Event):
    """Event when order performance metrics are updated"""
    order_id: str
    performance_type: str
    performance_metrics: Dict[str, Any]
    updated_at: datetime = None
    performance_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderRoutingUpdatedEvent(Event):
    """Event when order routing information is updated"""
    order_id: str
    routing_strategy: str
    routing_venues: List[str]
    updated_at: datetime = None
    routing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderLifecycleEvent(Event):
    """Event for order lifecycle management"""
    order_id: str
    lifecycle_event: str
    lifecycle_data: Dict[str, Any]
    occurred_at: datetime = None
    lifecycle_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow()


@dataclass
class OrderPriorityUpdatedEvent(Event):
    """Event when order priority is updated"""
    order_id: str
    old_priority: int
    new_priority: int
    priority_reason: str
    updated_at: datetime = None
    priority_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderEscalatedEvent(Event):
    """Event when an order is escalated"""
    order_id: str
    escalation_level: str
    escalation_reason: str
    escalated_at: datetime = None
    escalation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.escalated_at is None:
            self.escalated_at = datetime.utcnow()


@dataclass
class OrderAlertCreatedEvent(Event):
    """Event when an order alert is created"""
    order_id: str
    alert_type: str
    alert_message: str
    alert_severity: str
    created_at: datetime = None
    alert_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class OrderSnapshotCreatedEvent(Event):
    """Event when an order snapshot is created"""
    order_id: str
    snapshot_type: str
    snapshot_data: Dict[str, Any]
    created_at: datetime = None
    snapshot_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class OrderWorkflowUpdatedEvent(Event):
    """Event when order workflow is updated"""
    order_id: str
    workflow_step: str
    workflow_data: Dict[str, Any]
    updated_at: datetime = None
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderIntegrationEvent(Event):
    """Event for order integration with external systems"""
    order_id: str
    integration_system: str
    integration_action: str
    integration_data: Dict[str, Any]
    integrated_at: datetime = None
    integration_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.integrated_at is None:
            self.integrated_at = datetime.utcnow()


@dataclass
class OrderBookUpdatedEvent(Event):
    """Event when order book is updated"""
    symbol: str
    venue: str
    order_book_data: Dict[str, Any]
    updated_at: datetime = None
    book_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class OrderExecutionQualityEvent(Event):
    """Event for order execution quality metrics"""
    order_id: str
    execution_quality_metrics: Dict[str, Any]
    benchmark_price: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    impact: Optional[Decimal] = None
    measured_at: datetime = None
    quality_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.measured_at is None:
            self.measured_at = datetime.utcnow()


@dataclass
class OrderMarketImpactEvent(Event):
    """Event for order market impact analysis"""
    order_id: str
    market_impact_analysis: Dict[str, Any]
    impact_score: Optional[Decimal] = None
    impact_category: str = None
    analyzed_at: datetime = None
    impact_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.analyzed_at is None:
            self.analyzed_at = datetime.utcnow()


@dataclass
class OrderVenueAnalysisEvent(Event):
    """Event for order venue analysis"""
    order_id: str
    venue_analysis: Dict[str, Any]
    best_venue: str = None
    venue_rankings: List[Dict[str, Any]] = field(default_factory=list)
    analyzed_at: datetime = None
    venue_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.analyzed_at is None:
            self.analyzed_at = datetime.utcnow()


@dataclass
class OrderTimingAnalysisEvent(Event):
    """Event for order timing analysis"""
    order_id: str
    timing_analysis: Dict[str, Any]
    optimal_timing: Optional[datetime] = None
    timing_score: Optional[Decimal] = None
    analyzed_at: datetime = None
    timing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.analyzed_at is None:
            self.analyzed_at = datetime.utcnow() 