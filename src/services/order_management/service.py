"""
Order Management Service for CQRS Trading Platform
Comprehensive order lifecycle management service
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from decimal import Decimal
from uuid import uuid4

from ...cqrs.aggregate_repository import AggregateRepository
from ...services.queue.rabbitmq_service import RabbitMQService
from ...utils.trading_config import get_trading_config
from .aggregate import OrderAggregate
from .commands import *
from .events import *

logger = logging.getLogger(__name__)


class OrderManagementService:
    """Comprehensive order management service"""
    
    def __init__(self, 
                 repository: AggregateRepository,
                 rabbitmq: RabbitMQService,
                 config: Dict[str, Any] = None):
        self.repository = repository
        self.rabbitmq = rabbitmq
        self.config = config or get_trading_config()
        
        # Order tracking
        self.active_orders: Dict[str, OrderAggregate] = {}
        self.order_locks: Dict[str, asyncio.Lock] = {}
        
        # Performance tracking
        self.order_stats = {
            'total_orders': 0,
            'active_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'rejected_orders': 0
        }
        
        # Setup queues
        self.setup_queues()
    
    def setup_queues(self):
        """Setup RabbitMQ queues for order management"""
        # Order lifecycle queues
        self.rabbitmq.declare_queue('order.created')
        self.rabbitmq.declare_queue('order.submitted')
        self.rabbitmq.declare_queue('order.executed')
        self.rabbitmq.declare_queue('order.cancelled')
        self.rabbitmq.declare_queue('order.rejected')
        self.rabbitmq.declare_queue('order.expired')
        
        # Order management queues
        self.rabbitmq.declare_queue('order.validation')
        self.rabbitmq.declare_queue('order.routing')
        self.rabbitmq.declare_queue('order.risk_check')
        self.rabbitmq.declare_queue('order.compliance')
        self.rabbitmq.declare_queue('order.analytics')
        
        # Order monitoring queues
        self.rabbitmq.declare_queue('order.heartbeat')
        self.rabbitmq.declare_queue('order.alerts')
        self.rabbitmq.declare_queue('order.escalation')
        
        # Order integration queues
        self.rabbitmq.declare_queue('order.external_sync')
        self.rabbitmq.declare_queue('order.reconciliation')
        
        logger.info("Order management queues setup complete")
    
    async def create_order(self, command: CreateOrderCommand) -> str:
        """Create a new order"""
        try:
            # Generate order ID if not provided
            if not command.order_id:
                command.order_id = str(uuid4())
            
            # Create order aggregate
            order = OrderAggregate(
                order_id=command.order_id,
                symbol=command.symbol,
                side=command.side,
                order_type=command.order_type,
                quantity=command.quantity,
                limit_price=command.limit_price,
                stop_price=command.stop_price,
                trailing_stop_pct=command.trailing_stop_pct,
                time_in_force=command.time_in_force,
                good_till_date=command.good_till_date,
                strategy_id=command.strategy_id,
                signal_id=command.signal_id,
                parent_order_id=command.parent_order_id,
                iceberg_visible_quantity=command.iceberg_visible_quantity,
                twap_duration=command.twap_duration,
                vwap_volume_target=command.vwap_volume_target,
                max_slippage=command.max_slippage,
                max_impact=command.max_impact,
                user_id=command.user_id,
                account_id=command.account_id,
                tags=command.tags,
                metadata=command.metadata
            )
            
            # Generate events
            events = order.create_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Track active order
            self.active_orders[command.order_id] = order
            self.order_locks[command.order_id] = asyncio.Lock()
            
            # Update stats
            self.order_stats['total_orders'] += 1
            self.order_stats['active_orders'] += 1
            
            # Publish events
            await self.publish_order_events(events)
            
            # Trigger validation
            await self.validate_order(command.order_id)
            
            logger.info(f"Order created: {command.order_id} for {command.symbol}")
            return command.order_id
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise
    
    async def update_order(self, command: UpdateOrderCommand) -> bool:
        """Update an existing order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            if not order.can_modify():
                raise ValueError(f"Cannot modify order in status: {order.status}")
            
            # Generate events
            events = order.update_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Publish events
            await self.publish_order_events(events)
            
            logger.info(f"Order updated: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update order: {e}")
            raise
    
    async def cancel_order(self, command: CancelOrderCommand) -> bool:
        """Cancel an order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            if not order.can_cancel():
                raise ValueError(f"Cannot cancel order in status: {order.status}")
            
            # Generate events
            events = order.cancel_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Remove from active orders
            if command.order_id in self.active_orders:
                del self.active_orders[command.order_id]
                self.order_stats['active_orders'] -= 1
                self.order_stats['cancelled_orders'] += 1
            
            # Publish events
            await self.publish_order_events(events)
            
            logger.info(f"Order cancelled: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    async def execute_order(self, command: ExecuteOrderCommand) -> bool:
        """Execute an order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            # Generate events
            events = order.execute_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Check if order is complete
            if order.is_complete():
                if command.order_id in self.active_orders:
                    del self.active_orders[command.order_id]
                    self.order_stats['active_orders'] -= 1
                    self.order_stats['filled_orders'] += 1
            
            # Publish events
            await self.publish_order_events(events)
            
            # Trigger analytics update
            await self.update_order_analytics(command.order_id)
            
            logger.info(f"Order executed: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
            raise
    
    async def reject_order(self, command: RejectOrderCommand) -> bool:
        """Reject an order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            # Generate events
            events = order.reject_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Remove from active orders
            if command.order_id in self.active_orders:
                del self.active_orders[command.order_id]
                self.order_stats['active_orders'] -= 1
                self.order_stats['rejected_orders'] += 1
            
            # Publish events
            await self.publish_order_events(events)
            
            logger.info(f"Order rejected: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject order: {e}")
            raise
    
    async def submit_order(self, order_id: str, venue: str = None) -> bool:
        """Submit order to market"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Generate events
            events = order.submit_order(venue)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Publish events
            await self.publish_order_events(events)
            
            # Trigger routing
            await self.route_order(order_id, venue)
            
            logger.info(f"Order submitted: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise
    
    async def validate_order(self, order_id: str) -> bool:
        """Validate an order"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            command = ValidateOrderCommand(
                order_id=order_id,
                validation_rules=['basic', 'risk', 'compliance'],
                validation_metadata={}
            )
            
            # Generate events
            events = order.validate_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Publish events
            await self.publish_order_events(events)
            
            # Trigger risk check if validation passes
            if order.validation_result:
                await self.check_order_risk(order_id)
            
            logger.info(f"Order validated: {order_id}")
            return order.validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate order: {e}")
            raise
    
    async def check_order_risk(self, order_id: str) -> bool:
        """Check order risk parameters"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Basic risk checks
            risk_checks = []
            
            # Check position size
            if order.quantity > self.config.get('max_position_size', 10000):
                risk_checks.append('position_size_exceeded')
            
            # Check order value
            order_value = order.get_total_value()
            if order_value > self.config.get('max_order_value', 100000):
                risk_checks.append('order_value_exceeded')
            
            # Check daily limit
            daily_orders = await self.get_daily_orders(order.user_id)
            daily_value = sum(o.get_total_value() for o in daily_orders)
            if daily_value > self.config.get('max_daily_value', 1000000):
                risk_checks.append('daily_limit_exceeded')
            
            # Update compliance status
            command = UpdateOrderComplianceCommand(
                order_id=order_id,
                compliance_status='passed' if not risk_checks else 'failed',
                compliance_checks=risk_checks,
                compliance_metadata={'risk_score': len(risk_checks)}
            )
            
            events = order.update_compliance(command)
            await self.repository.save(order, events)
            await self.publish_order_events(events)
            
            logger.info(f"Order risk checked: {order_id}")
            return len(risk_checks) == 0
            
        except Exception as e:
            logger.error(f"Failed to check order risk: {e}")
            raise
    
    async def route_order(self, order_id: str, venue: str = None) -> bool:
        """Route order to execution venue"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Determine best venue if not specified
            if not venue:
                venue = await self.select_best_venue(order)
            
            command = RouteOrderCommand(
                order_id=order_id,
                venue=venue,
                routing_strategy='best_execution',
                routing_metadata={'selected_venue': venue}
            )
            
            # Generate events
            events = order.route_order(command)
            
            # Save to repository
            await self.repository.save(order, events)
            
            # Publish events
            await self.publish_order_events(events)
            
            logger.info(f"Order routed: {order_id} to {venue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to route order: {e}")
            raise
    
    async def select_best_venue(self, order: OrderAggregate) -> str:
        """Select best execution venue for order"""
        # Simple venue selection logic
        venues = self.config.get('execution_venues', ['NYSE', 'NASDAQ', 'ARCA'])
        
        # For now, return first venue
        # In production, this would use sophisticated venue analysis
        return venues[0] if venues else 'NYSE'
    
    async def update_order_analytics(self, order_id: str) -> bool:
        """Update order analytics"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            # Calculate analytics
            analytics_data = {
                'fill_rate': order.get_fill_rate(),
                'total_value': float(order.get_total_value()),
                'total_cost': float(order.get_total_cost()),
                'execution_quality': self.calculate_execution_quality(order),
                'market_impact': self.calculate_market_impact(order)
            }
            
            command = UpdateOrderAnalyticsCommand(
                order_id=order_id,
                analytics_data=analytics_data,
                analytics_type='execution_quality'
            )
            
            events = order.update_analytics(command)
            await self.repository.save(order, events)
            await self.publish_order_events(events)
            
            logger.info(f"Order analytics updated: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update order analytics: {e}")
            raise
    
    def calculate_execution_quality(self, order: OrderAggregate) -> float:
        """Calculate execution quality score"""
        if not order.fills:
            return 0.0
        
        # Simple quality calculation
        # In production, this would use sophisticated algorithms
        fill_rate = order.get_fill_rate()
        slippage = order.slippage or 0
        
        quality = fill_rate * (1 - abs(float(slippage)))
        return max(0.0, min(100.0, quality))
    
    def calculate_market_impact(self, order: OrderAggregate) -> float:
        """Calculate market impact score"""
        if not order.fills:
            return 0.0
        
        # Simple impact calculation
        # In production, this would use sophisticated market impact models
        order_size = order.quantity
        avg_price = order.average_fill_price or order.limit_price or 0
        
        if avg_price == 0:
            return 0.0
        
        # Impact based on order size relative to average daily volume
        # This is a simplified calculation
        impact = min(100.0, (order_size / 1000000) * 100)
        return impact
    
    async def get_order(self, order_id: str) -> Optional[OrderAggregate]:
        """Get order by ID"""
        try:
            # Check active orders first
            if order_id in self.active_orders:
                return self.active_orders[order_id]
            
            # Load from repository
            order = await self.repository.get(OrderAggregate, order_id)
            if order:
                # Cache in active orders
                self.active_orders[order_id] = order
                if order_id not in self.order_locks:
                    self.order_locks[order_id] = asyncio.Lock()
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            return None
    
    async def get_active_orders(self, user_id: str = None, account_id: str = None) -> List[OrderAggregate]:
        """Get active orders"""
        try:
            if user_id:
                return [o for o in self.active_orders.values() if o.user_id == user_id]
            elif account_id:
                return [o for o in self.active_orders.values() if o.account_id == account_id]
            else:
                return list(self.active_orders.values())
        except Exception as e:
            logger.error(f"Failed to get active orders: {e}")
            return []
    
    async def get_daily_orders(self, user_id: str) -> List[OrderAggregate]:
        """Get orders for today"""
        try:
            today = datetime.utcnow().date()
            orders = []
            
            for order in self.active_orders.values():
                if order.user_id == user_id and order.created_at.date() == today:
                    orders.append(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get daily orders: {e}")
            return []
    
    async def publish_order_events(self, events: List) -> None:
        """Publish order events to RabbitMQ"""
        try:
            for event in events:
                # Determine queue based on event type
                queue_name = self.get_event_queue(event)
                
                # Publish to queue
                await self.rabbitmq.publish(
                    queue_name,
                    {
                        'event_type': event.__class__.__name__,
                        'event_data': event.__dict__,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
            logger.debug(f"Published {len(events)} order events")
            
        except Exception as e:
            logger.error(f"Failed to publish order events: {e}")
    
    def get_event_queue(self, event) -> str:
        """Get queue name for event type"""
        event_type = event.__class__.__name__
        
        if 'Created' in event_type:
            return 'order.created'
        elif 'Submitted' in event_type:
            return 'order.submitted'
        elif 'Executed' in event_type or 'Filled' in event_type:
            return 'order.executed'
        elif 'Cancelled' in event_type:
            return 'order.cancelled'
        elif 'Rejected' in event_type:
            return 'order.rejected'
        elif 'Expired' in event_type:
            return 'order.expired'
        elif 'Validated' in event_type:
            return 'order.validation'
        elif 'Routed' in event_type:
            return 'order.routing'
        elif 'Compliance' in event_type:
            return 'order.compliance'
        elif 'Analytics' in event_type:
            return 'order.analytics'
        elif 'Heartbeat' in event_type:
            return 'order.heartbeat'
        elif 'Alert' in event_type:
            return 'order.alerts'
        elif 'Escalated' in event_type:
            return 'order.escalation'
        else:
            return 'order.general'
    
    async def cleanup_expired_orders(self) -> int:
        """Clean up expired orders"""
        try:
            expired_count = 0
            current_time = datetime.utcnow()
            
            for order_id, order in list(self.active_orders.items()):
                # Check for time-based expiration
                if order.good_till_date and current_time > order.good_till_date:
                    command = ExpireOrderCommand(
                        order_id=order_id,
                        expiration_reason='time_expired'
                    )
                    await self.expire_order(command)
                    expired_count += 1
                
                # Check for heartbeat timeout
                elif order.last_heartbeat:
                    timeout = timedelta(minutes=self.config.get('heartbeat_timeout_minutes', 5))
                    if current_time - order.last_heartbeat > timeout:
                        command = UpdateOrderAlertsCommand(
                            order_id=order_id,
                            alert_type='heartbeat_timeout',
                            alert_message='Order heartbeat timeout',
                            alert_severity='warning'
                        )
                        await self.add_order_alert(command)
            
            logger.info(f"Cleaned up {expired_count} expired orders")
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired orders: {e}")
            return 0
    
    async def expire_order(self, command: ExpireOrderCommand) -> bool:
        """Expire an order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            events = order.expire_order(command)
            await self.repository.save(order, events)
            
            # Remove from active orders
            if command.order_id in self.active_orders:
                del self.active_orders[command.order_id]
                self.order_stats['active_orders'] -= 1
            
            await self.publish_order_events(events)
            
            logger.info(f"Order expired: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to expire order: {e}")
            raise
    
    async def add_order_alert(self, command: UpdateOrderAlertsCommand) -> bool:
        """Add alert to order"""
        try:
            order = await self.get_order(command.order_id)
            if not order:
                raise ValueError(f"Order not found: {command.order_id}")
            
            events = order.add_alert(command)
            await self.repository.save(order, events)
            await self.publish_order_events(events)
            
            logger.info(f"Alert added to order: {command.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add order alert: {e}")
            raise
    
    def get_order_stats(self) -> Dict[str, Any]:
        """Get order management statistics"""
        return {
            **self.order_stats,
            'active_orders_count': len(self.active_orders),
            'order_locks_count': len(self.order_locks)
        }
    
    async def shutdown(self):
        """Shutdown order management service"""
        try:
            # Cleanup active orders
            await self.cleanup_expired_orders()
            
            # Clear caches
            self.active_orders.clear()
            self.order_locks.clear()
            
            logger.info("Order management service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}") 