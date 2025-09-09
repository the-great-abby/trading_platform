"""
Event Replay Service for CQRS Event Sourcing
Handles rebuilding projections from event history
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.read_model_repository import ReadModelRepository
from src.services.cqrs.aggregate_root import AggregateRoot, OrderAggregate, PortfolioAggregate

logger = logging.getLogger(__name__)


class EventReplayService:
    """Service for replaying events and rebuilding projections"""
    
    def __init__(self, event_store: EventStore, read_model_repository: ReadModelRepository):
        self.event_store = event_store
        self.read_model_repository = read_model_repository
        self._projection_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default projection handlers"""
        self._projection_handlers.update({
            'OrderCreatedEvent': self._handle_order_created,
            'OrderFilledEvent': self._handle_order_filled,
            'OrderCancelledEvent': self._handle_order_cancelled,
            'PortfolioUpdatedEvent': self._handle_portfolio_updated,
            'PositionOpenedEvent': self._handle_position_opened,
            'PositionClosedEvent': self._handle_position_closed,
            'StrategyCreatedEvent': self._handle_strategy_created,
            'StrategyUpdatedEvent': self._handle_strategy_updated,
            'StrategyDeletedEvent': self._handle_strategy_deleted,
            'SignalGeneratedEvent': self._handle_signal_generated,
            'SignalExecutedEvent': self._handle_signal_executed,
            'BacktestCompletedEvent': self._handle_backtest_completed,
            'RiskLimitExceededEvent': self._handle_risk_limit_exceeded,
        })
    
    async def rebuild_all_projections(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """Rebuild all projections from event history"""
        logger.info("Starting full projection rebuild")
        
        # Clear existing read models
        await self._clear_read_models()
        
        # Get all events in batches
        total_processed = 0
        offset = 0
        
        while True:
            events = await self.event_store.replay_events(
                from_date=from_date,
                to_date=to_date,
                limit=batch_size
            )
            
            if not events:
                break
            
            # Process events in batch
            processed = await self._process_event_batch(events)
            total_processed += processed
            
            logger.info(f"Processed {total_processed} events so far...")
            
            # If we got fewer events than batch size, we're done
            if len(events) < batch_size:
                break
            
            offset += batch_size
        
        logger.info(f"Completed projection rebuild. Processed {total_processed} events")
        return {"total_processed": total_processed}
    
    async def rebuild_aggregate_projection(
        self,
        aggregate_id: str,
        aggregate_type: str
    ) -> bool:
        """Rebuild projection for a specific aggregate"""
        try:
            # Get all events for the aggregate
            events = await self.event_store.get_events(aggregate_id, aggregate_type)
            
            if not events:
                logger.warning(f"No events found for {aggregate_type}:{aggregate_id}")
                return False
            
            # Create aggregate and replay events
            aggregate = self._create_aggregate(aggregate_type, aggregate_id)
            aggregate.load_from_history(events)
            
            # Update read models based on aggregate state
            await self._update_read_models_from_aggregate(aggregate)
            
            logger.info(f"Rebuilt projection for {aggregate_type}:{aggregate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rebuild projection for {aggregate_id}: {e}")
            return False
    
    async def process_new_events(
        self,
        from_date: Optional[datetime] = None,
        batch_size: int = 100
    ) -> int:
        """Process new events since last run"""
        if not from_date:
            from_date = datetime.utcnow() - timedelta(hours=1)
        
        events = await self.event_store.replay_events(
            from_date=from_date,
            limit=batch_size
        )
        
        if not events:
            return 0
        
        processed = await self._process_event_batch(events)
        logger.info(f"Processed {processed} new events")
        return processed
    
    async def _process_event_batch(self, events: List[Any]) -> int:
        """Process a batch of events"""
        processed = 0
        
        for event in events:
            try:
                await self._process_single_event(event)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process event {event.__class__.__name__}: {e}")
        
        return processed
    
    async def _process_single_event(self, event: Any):
        """Process a single event"""
        event_type = event.__class__.__name__
        handler = self._projection_handlers.get(event_type)
        
        if handler:
            await handler(event)
        else:
            logger.warning(f"No projection handler for event type: {event_type}")
    
    def _create_aggregate(self, aggregate_type: str, aggregate_id: str) -> AggregateRoot:
        """Create an aggregate instance"""
        if aggregate_type == "Order":
            return OrderAggregate(aggregate_id)
        elif aggregate_type == "Portfolio":
            return PortfolioAggregate(aggregate_id)
        else:
            raise ValueError(f"Unknown aggregate type: {aggregate_type}")
    
    async def _update_read_models_from_aggregate(self, aggregate: AggregateRoot):
        """Update read models based on aggregate state"""
        if isinstance(aggregate, OrderAggregate):
            await self._update_order_read_model(aggregate)
        elif isinstance(aggregate, PortfolioAggregate):
            await self._update_portfolio_read_model(aggregate)
    
    async def _update_order_read_model(self, order: OrderAggregate):
        """Update order read model from aggregate"""
        from src.services.cqrs.read_models import OrderReadModel
        
        order_read_model = OrderReadModel(
            order_id=order.aggregate_id,
            portfolio_id=order.account_id,  # Using account_id as portfolio_id for now
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            price=order.price,
            stop_price=None,
            status=order.status,
            filled_quantity=order.filled_quantity,
            average_fill_price=order.average_fill_price,
            time_in_force="GTC",
            strategy_id=None,
            signal_id=None,
            created_at=order.created_at or datetime.utcnow(),
            updated_at=order.updated_at or datetime.utcnow(),
            filled_at=order.updated_at if order.status == "filled" else None,
            cancelled_at=order.updated_at if order.status == "cancelled" else None,
            metadata={}
        )
        
        await self.read_model_repository.upsert_order(order_read_model)
    
    async def _update_portfolio_read_model(self, portfolio: PortfolioAggregate):
        """Update portfolio read model from aggregate"""
        from src.services.cqrs.read_models import PortfolioReadModel
        from decimal import Decimal
        
        # Calculate total value from positions
        total_value = portfolio.cash_balance
        for symbol, position in portfolio.positions.items():
            total_value += position.get("market_value", 0)
        
        portfolio_read_model = PortfolioReadModel(
            portfolio_id=portfolio.aggregate_id,
            user_id=portfolio.user_id,
            account_id=portfolio.account_id,
            name=portfolio.name,
            cash_balance=Decimal(str(portfolio.cash_balance)),
            total_value=Decimal(str(total_value)),
            total_cost=Decimal(str(sum(pos.get("cost_basis", 0) for pos in portfolio.positions.values()))),
            unrealized_pnl=Decimal(str(total_value - sum(pos.get("cost_basis", 0) for pos in portfolio.positions.values()))),
            realized_pnl=Decimal("0.00"),  # Would need to track this separately
            total_return=Decimal("0.00"),  # Would need to calculate this
            total_return_percentage=Decimal("0.00"),
            position_count=len(portfolio.positions),
            last_updated=portfolio.updated_at or datetime.utcnow(),
            metadata={"version": portfolio.version}
        )
        
        await self.read_model_repository.upsert_portfolio(portfolio_read_model)
    
    async def _clear_read_models(self):
        """Clear all read models (for full rebuild)"""
        # This would clear all read model tables
        # Implementation depends on your specific needs
        logger.info("Clearing read models for rebuild")
    
    # Event handlers for specific event types
    async def _handle_order_created(self, event):
        """Handle order created event"""
        # This would update order read models
        pass
    
    async def _handle_order_filled(self, event):
        """Handle order filled event"""
        # This would update order and position read models
        pass
    
    async def _handle_order_cancelled(self, event):
        """Handle order cancelled event"""
        # This would update order read models
        pass
    
    async def _handle_portfolio_updated(self, event):
        """Handle portfolio updated event"""
        # This would update portfolio read models
        pass
    
    async def _handle_position_opened(self, event):
        """Handle position opened event"""
        # This would update position read models
        pass
    
    async def _handle_position_closed(self, event):
        """Handle position closed event"""
        # This would update position read models
        pass
    
    async def _handle_strategy_created(self, event):
        """Handle strategy created event"""
        # This would update strategy read models
        pass
    
    async def _handle_strategy_updated(self, event):
        """Handle strategy updated event"""
        # This would update strategy read models
        pass
    
    async def _handle_strategy_deleted(self, event):
        """Handle strategy deleted event"""
        # This would update strategy read models
        pass
    
    async def _handle_signal_generated(self, event):
        """Handle signal generated event"""
        # This would update signal read models
        pass
    
    async def _handle_signal_executed(self, event):
        """Handle signal executed event"""
        # This would update signal read models
        pass
    
    async def _handle_backtest_completed(self, event):
        """Handle backtest completed event"""
        # This would update backtest read models
        pass
    
    async def _handle_risk_limit_exceeded(self, event):
        """Handle risk limit exceeded event"""
        # This would update risk read models
        pass
