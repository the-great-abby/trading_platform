"""
Order Aggregate for CQRS Trading Platform
Comprehensive order lifecycle management with event sourcing
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from decimal import Decimal
from uuid import UUID, uuid4

from ...cqrs.base import Aggregate
from .commands import (
    CreateOrderCommand, UpdateOrderCommand, CancelOrderCommand, ReplaceOrderCommand,
    RouteOrderCommand, ExecuteOrderCommand, PartialFillCommand, CompleteFillCommand,
    RejectOrderCommand, ExpireOrderCommand, SuspendOrderCommand, ResumeOrderCommand,
    UpdateOrderStatusCommand, AddOrderNoteCommand, UpdateOrderTagsCommand,
    LinkOrdersCommand, UpdateOrderRiskCommand, ValidateOrderCommand,
    PreflightOrderCommand, ScheduleOrderCommand, CancelScheduledOrderCommand,
    UpdateOrderExecutionCommand, OrderHeartbeatCommand, UpdateOrderComplianceCommand,
    OrderAuditCommand, UpdateOrderAnalyticsCommand, LinkOrderToSignalCommand,
    UpdateOrderStrategyCommand, OrderReconciliationCommand, UpdateOrderCostsCommand,
    OrderPerformanceCommand, UpdateOrderRoutingCommand, OrderLifecycleCommand,
    UpdateOrderPriorityCommand, OrderEscalationCommand, UpdateOrderAlertsCommand,
    OrderSnapshotCommand, UpdateOrderWorkflowCommand, OrderIntegrationCommand,
    OrderType, OrderSide, TimeInForce, OrderStatus, OrderSource
)
from .events import (
    OrderCreatedEvent, OrderSubmittedEvent, OrderUpdatedEvent, OrderCancelledEvent,
    OrderReplacedEvent, OrderRoutedEvent, OrderExecutedEvent, OrderPartiallyFilledEvent,
    OrderFilledEvent, OrderRejectedEvent, OrderExpiredEvent, OrderSuspendedEvent,
    OrderResumedEvent, OrderStatusChangedEvent, OrderNoteAddedEvent,
    OrderTagsUpdatedEvent, OrdersLinkedEvent, OrderRiskUpdatedEvent,
    OrderValidatedEvent, OrderPreflightCompletedEvent, OrderScheduledEvent,
    ScheduledOrderCancelledEvent, OrderExecutionUpdatedEvent, OrderHeartbeatEvent,
    OrderComplianceUpdatedEvent, OrderAuditedEvent, OrderAnalyticsUpdatedEvent,
    OrderSignalLinkedEvent, OrderStrategyUpdatedEvent, OrderReconciledEvent,
    OrderCostsUpdatedEvent, OrderPerformanceUpdatedEvent, OrderRoutingUpdatedEvent,
    OrderLifecycleEvent, OrderPriorityUpdatedEvent, OrderEscalatedEvent,
    OrderAlertCreatedEvent, OrderSnapshotCreatedEvent, OrderWorkflowUpdatedEvent,
    OrderIntegrationEvent
)


@dataclass
class OrderFill:
    """Represents a fill of an order"""
    fill_id: str
    quantity: int
    price: Decimal
    timestamp: datetime
    venue: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderNote:
    """Represents a note attached to an order"""
    note_id: str
    note: str
    note_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderAlert:
    """Represents an alert for an order"""
    alert_id: str
    alert_type: str
    alert_message: str
    alert_severity: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderSnapshot:
    """Represents a snapshot of order state"""
    snapshot_id: str
    snapshot_type: str
    snapshot_data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderAggregate(Aggregate):
    """Order aggregate for comprehensive order management"""
    
    # Core order information
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    filled_quantity: int = 0
    remaining_quantity: int = 0
    
    # Pricing
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    trailing_stop_pct: Optional[Decimal] = None
    average_fill_price: Optional[Decimal] = None
    
    # Time and execution
    time_in_force: TimeInForce = TimeInForce.DAY
    good_till_date: Optional[datetime] = None
    created_at: datetime = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    
    # Status and state
    status: OrderStatus = OrderStatus.PENDING
    source: OrderSource = OrderSource.MANUAL
    
    # Strategy and metadata
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    linked_order_ids: Set[str] = field(default_factory=set)
    
    # Advanced order types
    iceberg_visible_quantity: Optional[int] = None
    twap_duration: Optional[timedelta] = None
    vwap_volume_target: Optional[Decimal] = None
    
    # Risk and compliance
    max_slippage: Optional[Decimal] = None
    max_impact: Optional[Decimal] = None
    compliance_status: str = "pending"
    compliance_checks: List[str] = field(default_factory=list)
    
    # User and account
    user_id: str = None
    account_id: str = None
    
    # Execution
    execution_strategy: str = "best_execution"
    execution_venue: Optional[str] = None
    routing_strategy: str = "best_execution"
    routing_venues: List[str] = field(default_factory=list)
    
    # Costs and performance
    commission: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Collections
    fills: List[OrderFill] = field(default_factory=list)
    notes: List[OrderNote] = field(default_factory=list)
    alerts: List[OrderAlert] = field(default_factory=list)
    snapshots: List[OrderSnapshot] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow and lifecycle
    priority: int = 0
    escalation_level: str = "normal"
    workflow_step: str = "created"
    lifecycle_events: List[str] = field(default_factory=list)
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    schedule_type: str = "immediate"
    
    # Monitoring
    last_heartbeat: Optional[datetime] = None
    validation_result: Optional[bool] = None
    preflight_result: Optional[bool] = None
    
    # Analytics
    analytics_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
    
    def create_order(self, command: CreateOrderCommand) -> List[OrderCreatedEvent]:
        """Create a new order"""
        event = OrderCreatedEvent(
            order_id=command.order_id,
            symbol=command.symbol,
            side=command.side,
            order_type=command.order_type,
            quantity=command.quantity,
            limit_price=command.limit_price,
            stop_price=command.stop_price,
            time_in_force=command.time_in_force,
            strategy_id=command.strategy_id,
            signal_id=command.signal_id,
            user_id=command.user_id,
            account_id=command.account_id,
            metadata=command.metadata
        )
        return [event]
    
    def update_order(self, command: UpdateOrderCommand) -> List[OrderUpdatedEvent]:
        """Update an existing order"""
        updated_fields = {}
        
        if command.quantity is not None:
            updated_fields['quantity'] = command.quantity
            self.quantity = command.quantity
            self.remaining_quantity = command.quantity - self.filled_quantity
            
        if command.limit_price is not None:
            updated_fields['limit_price'] = command.limit_price
            self.limit_price = command.limit_price
            
        if command.stop_price is not None:
            updated_fields['stop_price'] = command.stop_price
            self.stop_price = command.stop_price
            
        if command.time_in_force is not None:
            updated_fields['time_in_force'] = command.time_in_force
            self.time_in_force = command.time_in_force
            
        if command.good_till_date is not None:
            updated_fields['good_till_date'] = command.good_till_date
            self.good_till_date = command.good_till_date
            
        if command.tags is not None:
            updated_fields['tags'] = command.tags
            self.tags = command.tags
            
        if command.metadata is not None:
            updated_fields['metadata'] = command.metadata
            self.metadata.update(command.metadata)
        
        event = OrderUpdatedEvent(
            order_id=command.order_id,
            updated_fields=updated_fields,
            update_reason=command.update_reason,
            update_metadata=command.metadata or {}
        )
        return [event]
    
    def cancel_order(self, command: CancelOrderCommand) -> List[OrderCancelledEvent]:
        """Cancel an order"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            raise ValueError(f"Cannot cancel order in status: {self.status}")
        
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        
        event = OrderCancelledEvent(
            order_id=command.order_id,
            cancel_reason=command.cancel_reason,
            cancel_source=command.cancel_source,
            cancel_metadata={}
        )
        return [event]
    
    def execute_order(self, command: ExecuteOrderCommand) -> List[OrderExecutedEvent]:
        """Execute an order"""
        if self.status not in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
            raise ValueError(f"Cannot execute order in status: {self.status}")
        
        # Create fill record
        fill = OrderFill(
            fill_id=str(uuid4()),
            quantity=command.execution_quantity,
            price=command.execution_price,
            timestamp=command.execution_time,
            venue=command.execution_venue,
            metadata=command.execution_metadata
        )
        self.fills.append(fill)
        
        # Update order state
        self.filled_quantity += command.execution_quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        
        # Calculate average fill price
        total_value = sum(fill.quantity * fill.price for fill in self.fills)
        self.average_fill_price = total_value / self.filled_quantity
        
        # Update status
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
            self.filled_at = command.execution_time
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
        
        event = OrderExecutedEvent(
            order_id=command.order_id,
            execution_venue=command.execution_venue,
            execution_price=command.execution_price,
            execution_quantity=command.execution_quantity,
            execution_time=command.execution_time,
            execution_metadata=command.execution_metadata
        )
        return [event]
    
    def reject_order(self, command: RejectOrderCommand) -> List[OrderRejectedEvent]:
        """Reject an order"""
        self.status = OrderStatus.REJECTED
        
        event = OrderRejectedEvent(
            order_id=command.order_id,
            rejection_reason=command.rejection_reason,
            rejection_code=command.rejection_code,
            rejection_details=command.rejection_details
        )
        return [event]
    
    def expire_order(self, command: ExpireOrderCommand) -> List[OrderExpiredEvent]:
        """Expire an order"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            raise ValueError(f"Cannot expire order in status: {self.status}")
        
        self.status = OrderStatus.EXPIRED
        self.expired_at = command.expiration_time
        
        event = OrderExpiredEvent(
            order_id=command.order_id,
            expiration_reason=command.expiration_reason,
            expiration_metadata={}
        )
        return [event]
    
    def submit_order(self, venue: str = None) -> List[OrderSubmittedEvent]:
        """Submit order to market"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot submit order in status: {self.status}")
        
        self.status = OrderStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()
        self.execution_venue = venue
        
        event = OrderSubmittedEvent(
            order_id=self.order_id,
            submission_venue=venue,
            submission_metadata={}
        )
        return [event]
    
    def add_note(self, command: AddOrderNoteCommand) -> List[OrderNoteAddedEvent]:
        """Add a note to the order"""
        note = OrderNote(
            note_id=str(uuid4()),
            note=command.note,
            note_type=command.note_type,
            timestamp=datetime.utcnow(),
            metadata=command.note_metadata
        )
        self.notes.append(note)
        
        event = OrderNoteAddedEvent(
            order_id=command.order_id,
            note=command.note,
            note_type=command.note_type,
            note_metadata=command.note_metadata
        )
        return [event]
    
    def update_tags(self, command: UpdateOrderTagsCommand) -> List[OrderTagsUpdatedEvent]:
        """Update order tags"""
        old_tags = self.tags.copy()
        
        if command.operation == "replace":
            self.tags = command.tags
        elif command.operation == "add":
            self.tags.extend(command.tags)
        elif command.operation == "remove":
            self.tags = [tag for tag in self.tags if tag not in command.tags]
        
        event = OrderTagsUpdatedEvent(
            order_id=command.order_id,
            old_tags=old_tags,
            new_tags=self.tags,
            operation=command.operation,
            tag_metadata={}
        )
        return [event]
    
    def link_orders(self, command: LinkOrdersCommand) -> List[OrdersLinkedEvent]:
        """Link orders together"""
        self.linked_order_ids.update(command.linked_order_ids)
        
        event = OrdersLinkedEvent(
            primary_order_id=command.primary_order_id,
            linked_order_ids=command.linked_order_ids,
            link_type=command.link_type,
            link_metadata=command.link_metadata
        )
        return [event]
    
    def update_risk(self, command: UpdateOrderRiskCommand) -> List[OrderRiskUpdatedEvent]:
        """Update order risk parameters"""
        old_risk_params = {
            'max_slippage': self.max_slippage,
            'max_impact': self.max_impact
        }
        
        if command.max_slippage is not None:
            self.max_slippage = command.max_slippage
        if command.max_impact is not None:
            self.max_impact = command.max_impact
            
        new_risk_params = {
            'max_slippage': self.max_slippage,
            'max_impact': self.max_impact
        }
        
        event = OrderRiskUpdatedEvent(
            order_id=command.order_id,
            old_risk_params=old_risk_params,
            new_risk_params=new_risk_params,
            risk_metadata=command.risk_metadata
        )
        return [event]
    
    def validate_order(self, command: ValidateOrderCommand) -> List[OrderValidatedEvent]:
        """Validate order"""
        # Basic validation logic
        validation_result = True
        validation_details = {}
        
        # Check if order is in valid state for validation
        if self.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            validation_result = False
            validation_details['status'] = f"Invalid status: {self.status}"
        
        # Check quantity
        if self.quantity <= 0:
            validation_result = False
            validation_details['quantity'] = "Quantity must be positive"
        
        # Check prices
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            validation_result = False
            validation_details['limit_price'] = "Limit price required for limit orders"
        
        if self.order_type == OrderType.STOP and self.stop_price is None:
            validation_result = False
            validation_details['stop_price'] = "Stop price required for stop orders"
        
        self.validation_result = validation_result
        
        event = OrderValidatedEvent(
            order_id=command.order_id,
            validation_rules=command.validation_rules,
            validation_result=validation_result,
            validation_details=validation_details,
            validation_metadata=command.validation_metadata
        )
        return [event]
    
    def schedule_order(self, command: ScheduleOrderCommand) -> List[OrderScheduledEvent]:
        """Schedule order for future execution"""
        self.scheduled_time = command.scheduled_time
        self.schedule_type = command.schedule_type
        
        event = OrderScheduledEvent(
            order_id=command.order_id,
            scheduled_time=command.scheduled_time,
            schedule_type=command.schedule_type,
            schedule_metadata=command.schedule_metadata
        )
        return [event]
    
    def update_execution(self, command: UpdateOrderExecutionCommand) -> List[OrderExecutionUpdatedEvent]:
        """Update order execution parameters"""
        if command.execution_strategy is not None:
            self.execution_strategy = command.execution_strategy
        if command.execution_venue is not None:
            self.execution_venue = command.execution_venue
            
        event = OrderExecutionUpdatedEvent(
            order_id=command.order_id,
            execution_strategy=self.execution_strategy,
            execution_venue=self.execution_venue,
            execution_metadata=command.execution_metadata
        )
        return [event]
    
    def heartbeat(self, command: OrderHeartbeatCommand) -> List[OrderHeartbeatEvent]:
        """Update order heartbeat"""
        self.last_heartbeat = command.heartbeat_time
        
        event = OrderHeartbeatEvent(
            order_id=command.order_id,
            heartbeat_time=command.heartbeat_time,
            heartbeat_metadata=command.heartbeat_metadata
        )
        return [event]
    
    def update_compliance(self, command: UpdateOrderComplianceCommand) -> List[OrderComplianceUpdatedEvent]:
        """Update order compliance status"""
        self.compliance_status = command.compliance_status
        self.compliance_checks = command.compliance_checks
        
        event = OrderComplianceUpdatedEvent(
            order_id=command.order_id,
            compliance_status=command.compliance_status,
            compliance_checks=command.compliance_checks,
            compliance_metadata=command.compliance_metadata
        )
        return [event]
    
    def update_analytics(self, command: UpdateOrderAnalyticsCommand) -> List[OrderAnalyticsUpdatedEvent]:
        """Update order analytics"""
        self.analytics_data.update(command.analytics_data)
        
        event = OrderAnalyticsUpdatedEvent(
            order_id=command.order_id,
            analytics_type=command.analytics_type,
            analytics_data=command.analytics_data,
            analytics_metadata={}
        )
        return [event]
    
    def link_signal(self, command: LinkOrderToSignalCommand) -> List[OrderSignalLinkedEvent]:
        """Link order to trading signal"""
        self.signal_id = command.signal_id
        
        event = OrderSignalLinkedEvent(
            order_id=command.order_id,
            signal_id=command.signal_id,
            link_metadata=command.link_metadata
        )
        return [event]
    
    def update_strategy(self, command: UpdateOrderStrategyCommand) -> List[OrderStrategyUpdatedEvent]:
        """Update order strategy information"""
        self.strategy_id = command.strategy_id
        self.metadata.update(command.strategy_parameters)
        
        event = OrderStrategyUpdatedEvent(
            order_id=command.order_id,
            strategy_id=command.strategy_id,
            strategy_parameters=command.strategy_parameters,
            strategy_metadata=command.strategy_metadata
        )
        return [event]
    
    def update_costs(self, command: UpdateOrderCostsCommand) -> List[OrderCostsUpdatedEvent]:
        """Update order costs"""
        if command.commission is not None:
            self.commission = command.commission
        if command.fees is not None:
            self.fees = command.fees
        if command.taxes is not None:
            self.taxes = command.taxes
        if command.slippage is not None:
            self.slippage = command.slippage
        if command.total_cost is not None:
            self.total_cost = command.total_cost
            
        event = OrderCostsUpdatedEvent(
            order_id=command.order_id,
            commission=self.commission,
            fees=self.fees,
            taxes=self.taxes,
            slippage=self.slippage,
            total_cost=self.total_cost,
            cost_metadata=command.cost_metadata
        )
        return [event]
    
    def update_performance(self, command: OrderPerformanceCommand) -> List[OrderPerformanceUpdatedEvent]:
        """Update order performance metrics"""
        self.performance_metrics.update(command.performance_metrics)
        
        event = OrderPerformanceUpdatedEvent(
            order_id=command.order_id,
            performance_type=command.performance_type,
            performance_metrics=command.performance_metrics,
            performance_metadata={}
        )
        return [event]
    
    def update_routing(self, command: UpdateOrderRoutingCommand) -> List[OrderRoutingUpdatedEvent]:
        """Update order routing information"""
        self.routing_strategy = command.routing_strategy
        self.routing_venues = command.routing_venues
        
        event = OrderRoutingUpdatedEvent(
            order_id=command.order_id,
            routing_strategy=command.routing_strategy,
            routing_venues=command.routing_venues,
            routing_metadata=command.routing_metadata
        )
        return [event]
    
    def update_priority(self, command: UpdateOrderPriorityCommand) -> List[OrderPriorityUpdatedEvent]:
        """Update order priority"""
        old_priority = self.priority
        self.priority = command.priority
        
        event = OrderPriorityUpdatedEvent(
            order_id=command.order_id,
            old_priority=old_priority,
            new_priority=command.priority,
            priority_reason=command.priority_reason,
            priority_metadata=command.priority_metadata
        )
        return [event]
    
    def escalate_order(self, command: OrderEscalationCommand) -> List[OrderEscalatedEvent]:
        """Escalate order"""
        self.escalation_level = command.escalation_level
        
        event = OrderEscalatedEvent(
            order_id=command.order_id,
            escalation_level=command.escalation_level,
            escalation_reason=command.escalation_reason,
            escalation_metadata=command.escalation_metadata
        )
        return [event]
    
    def add_alert(self, command: UpdateOrderAlertsCommand) -> List[OrderAlertCreatedEvent]:
        """Add alert to order"""
        alert = OrderAlert(
            alert_id=str(uuid4()),
            alert_type=command.alert_type,
            alert_message=command.alert_message,
            alert_severity=command.alert_severity,
            timestamp=datetime.utcnow(),
            metadata=command.alert_metadata
        )
        self.alerts.append(alert)
        
        event = OrderAlertCreatedEvent(
            order_id=command.order_id,
            alert_type=command.alert_type,
            alert_message=command.alert_message,
            alert_severity=command.alert_severity,
            alert_metadata=command.alert_metadata
        )
        return [event]
    
    def create_snapshot(self, command: OrderSnapshotCommand) -> List[OrderSnapshotCreatedEvent]:
        """Create order snapshot"""
        snapshot = OrderSnapshot(
            snapshot_id=str(uuid4()),
            snapshot_type=command.snapshot_type,
            snapshot_data=command.snapshot_data,
            timestamp=datetime.utcnow(),
            metadata=command.snapshot_metadata
        )
        self.snapshots.append(snapshot)
        
        event = OrderSnapshotCreatedEvent(
            order_id=command.order_id,
            snapshot_type=command.snapshot_type,
            snapshot_data=command.snapshot_data,
            snapshot_metadata=command.snapshot_metadata
        )
        return [event]
    
    def update_workflow(self, command: UpdateOrderWorkflowCommand) -> List[OrderWorkflowUpdatedEvent]:
        """Update order workflow"""
        self.workflow_step = command.workflow_step
        self.metadata.update(command.workflow_data)
        
        event = OrderWorkflowUpdatedEvent(
            order_id=command.order_id,
            workflow_step=command.workflow_step,
            workflow_data=command.workflow_data,
            workflow_metadata=command.workflow_metadata
        )
        return [event]
    
    def integrate_order(self, command: OrderIntegrationCommand) -> List[OrderIntegrationEvent]:
        """Integrate order with external system"""
        event = OrderIntegrationEvent(
            order_id=command.order_id,
            integration_system=command.integration_system,
            integration_action="update",
            integration_data=command.integration_data,
            integration_metadata=command.integration_metadata
        )
        return [event]
    
    def apply_event(self, event) -> None:
        """Apply event to aggregate"""
        if isinstance(event, OrderCreatedEvent):
            self.order_id = event.order_id
            self.symbol = event.symbol
            self.side = event.side
            self.order_type = event.order_type
            self.quantity = event.quantity
            self.remaining_quantity = event.quantity
            self.limit_price = event.limit_price
            self.stop_price = event.stop_price
            self.time_in_force = event.time_in_force
            self.strategy_id = event.strategy_id
            self.signal_id = event.signal_id
            self.user_id = event.user_id
            self.account_id = event.account_id
            self.created_at = event.created_at
            self.metadata = event.metadata
            
        elif isinstance(event, OrderSubmittedEvent):
            self.status = OrderStatus.SUBMITTED
            self.submitted_at = event.submitted_at
            self.execution_venue = event.submission_venue
            
        elif isinstance(event, OrderCancelledEvent):
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = event.cancelled_at
            
        elif isinstance(event, OrderExecutedEvent):
            # Add fill
            fill = OrderFill(
                fill_id=str(uuid4()),
                quantity=event.execution_quantity,
                price=event.execution_price,
                timestamp=event.execution_time,
                venue=event.execution_venue,
                metadata=event.execution_metadata
            )
            self.fills.append(fill)
            
            # Update quantities
            self.filled_quantity += event.execution_quantity
            self.remaining_quantity = self.quantity - self.filled_quantity
            
            # Update average price
            total_value = sum(fill.quantity * fill.price for fill in self.fills)
            self.average_fill_price = total_value / self.filled_quantity
            
            # Update status
            if self.remaining_quantity == 0:
                self.status = OrderStatus.FILLED
                self.filled_at = event.execution_time
            else:
                self.status = OrderStatus.PARTIALLY_FILLED
                
        elif isinstance(event, OrderRejectedEvent):
            self.status = OrderStatus.REJECTED
            
        elif isinstance(event, OrderExpiredEvent):
            self.status = OrderStatus.EXPIRED
            self.expired_at = event.expired_at
            
        elif isinstance(event, OrderStatusChangedEvent):
            self.status = event.new_status
            
        elif isinstance(event, OrderTagsUpdatedEvent):
            self.tags = event.new_tags
            
        elif isinstance(event, OrdersLinkedEvent):
            self.linked_order_ids.update(event.linked_order_ids)
            
        elif isinstance(event, OrderScheduledEvent):
            self.scheduled_time = event.scheduled_time
            self.schedule_type = event.schedule_type
            
        elif isinstance(event, OrderExecutionUpdatedEvent):
            self.execution_strategy = event.execution_strategy
            self.execution_venue = event.execution_venue
            
        elif isinstance(event, OrderHeartbeatEvent):
            self.last_heartbeat = event.heartbeat_time
            
        elif isinstance(event, OrderComplianceUpdatedEvent):
            self.compliance_status = event.compliance_status
            self.compliance_checks = event.compliance_checks
            
        elif isinstance(event, OrderAnalyticsUpdatedEvent):
            self.analytics_data.update(event.analytics_data)
            
        elif isinstance(event, OrderSignalLinkedEvent):
            self.signal_id = event.signal_id
            
        elif isinstance(event, OrderStrategyUpdatedEvent):
            self.strategy_id = event.strategy_id
            self.metadata.update(event.strategy_parameters)
            
        elif isinstance(event, OrderCostsUpdatedEvent):
            self.commission = event.commission
            self.fees = event.fees
            self.taxes = event.taxes
            self.slippage = event.slippage
            self.total_cost = event.total_cost
            
        elif isinstance(event, OrderPerformanceUpdatedEvent):
            self.performance_metrics.update(event.performance_metrics)
            
        elif isinstance(event, OrderRoutingUpdatedEvent):
            self.routing_strategy = event.routing_strategy
            self.routing_venues = event.routing_venues
            
        elif isinstance(event, OrderPriorityUpdatedEvent):
            self.priority = event.new_priority
            
        elif isinstance(event, OrderEscalatedEvent):
            self.escalation_level = event.escalation_level
            
        elif isinstance(event, OrderWorkflowUpdatedEvent):
            self.workflow_step = event.workflow_step
            self.metadata.update(event.workflow_data)
    
    def get_total_value(self) -> Decimal:
        """Get total value of the order"""
        if self.average_fill_price:
            return self.filled_quantity * self.average_fill_price
        elif self.limit_price:
            return self.quantity * self.limit_price
        return Decimal('0')
    
    def get_fill_rate(self) -> float:
        """Get fill rate as percentage"""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100
    
    def is_complete(self) -> bool:
        """Check if order is complete"""
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    def can_modify(self) -> bool:
        """Check if order can be modified"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def get_latest_fill(self) -> Optional[OrderFill]:
        """Get the most recent fill"""
        return self.fills[-1] if self.fills else None
    
    def get_total_cost(self) -> Decimal:
        """Calculate total cost including fees"""
        base_cost = self.get_total_value()
        fees = self.commission or Decimal('0')
        fees += self.fees or Decimal('0')
        fees += self.taxes or Decimal('0')
        return base_cost + fees 