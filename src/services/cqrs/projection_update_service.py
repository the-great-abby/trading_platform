"""
Projection Update Service for CQRS
Handles automatic updates of read models when events occur
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.read_model_repository import ReadModelRepository
from src.services.cqrs.events import BaseEvent
from src.services.cqrs.read_models import (
    PortfolioReadModel, PositionReadModel, OrderReadModel, 
    MarketDataReadModel, PerformanceReadModel, StrategyReadModel,
    SignalReadModel, TradingHistoryReadModel
)

logger = logging.getLogger(__name__)


class ProjectionUpdateService:
    """Service for updating read model projections from events"""
    
    def __init__(self, event_store: EventStore, read_model_repository: ReadModelRepository):
        self.event_store = event_store
        self.read_model_repository = read_model_repository
        self._projection_handlers: Dict[str, callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register projection update handlers for each event type"""
        self._projection_handlers.update({
            # Order events
            'OrderCreatedEvent': self._handle_order_created,
            'OrderFilledEvent': self._handle_order_filled,
            'OrderCancelledEvent': self._handle_order_cancelled,
            'OrderUpdatedEvent': self._handle_order_updated,
            
            # Portfolio events
            'PortfolioUpdatedEvent': self._handle_portfolio_updated,
            'PositionOpenedEvent': self._handle_position_opened,
            'PositionClosedEvent': self._handle_position_closed,
            'PositionUpdatedEvent': self._handle_position_updated,
            
            # Strategy events
            'StrategyCreatedEvent': self._handle_strategy_created,
            'StrategyUpdatedEvent': self._handle_strategy_updated,
            'StrategyDeletedEvent': self._handle_strategy_deleted,
            'StrategyStartedEvent': self._handle_strategy_started,
            'StrategyStoppedEvent': self._handle_strategy_stopped,
            
            # Signal events
            'SignalCreatedEvent': self._handle_signal_created,
            'SignalUpdatedEvent': self._handle_signal_updated,
            'SignalDeletedEvent': self._handle_signal_deleted,
            'SignalExecutedEvent': self._handle_signal_executed,
            
            # Market data events
            'MarketDataUpdatedEvent': self._handle_market_data_updated,
            'MarketDataErrorEvent': self._handle_market_data_error,
            
            # Performance events
            'PerformanceCalculatedEvent': self._handle_performance_calculated,
            'PerformanceAlertEvent': self._handle_performance_alert,
            
            # Backtest events
            'BacktestStartedEvent': self._handle_backtest_started,
            'BacktestCompletedEvent': self._handle_backtest_completed,
            'BacktestFailedEvent': self._handle_backtest_failed,
            
            # Risk events
            'RiskLimitExceededEvent': self._handle_risk_limit_exceeded,
            'RiskAlertTriggeredEvent': self._handle_risk_alert_triggered,
            'RiskAlertResolvedEvent': self._handle_risk_alert_resolved,
        })
    
    async def process_event(self, event: BaseEvent) -> bool:
        """Process a single event and update relevant projections"""
        try:
            event_type = event.__class__.__name__
            handler = self._projection_handlers.get(event_type)
            
            if handler:
                await handler(event)
                logger.info(f"Updated projections for event: {event_type}")
                return True
            else:
                logger.warning(f"No projection handler for event type: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to process event {event.__class__.__name__}: {e}")
            return False
    
    async def process_events_batch(self, events: List[BaseEvent]) -> Dict[str, int]:
        """Process a batch of events and update projections"""
        results = {"processed": 0, "failed": 0, "skipped": 0}
        
        for event in events:
            try:
                success = await self.process_event(event)
                if success:
                    results["processed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(f"Failed to process event {event.__class__.__name__}: {e}")
                results["failed"] += 1
        
        logger.info(f"Processed batch: {results}")
        return results
    
    # Order event handlers
    async def _handle_order_created(self, event):
        """Handle order created event"""
        order_read_model = OrderReadModel(
            order_id=event.order_id,
            symbol=event.symbol,
            side=event.side,
            quantity=event.quantity,
            filled_quantity=0,
            remaining_quantity=event.quantity,
            order_type=event.order_type,
            price=event.price,
            stop_price=event.stop_price,
            average_fill_price=None,
            status="pending",
            time_in_force="GTC",
            strategy_id=event.strategy_id,
            signal_id=event.signal_id,
            created_at=event.timestamp,
            updated_at=event.timestamp,
            filled_at=None,
            cancelled_at=None,
            metadata={}
        )
        
        await self.read_model_repository.upsert_order(order_read_model)
    
    async def _handle_order_filled(self, event):
        """Handle order filled event"""
        # Get existing order
        existing_order = await self.read_model_repository.get_order(event.order_id)
        if not existing_order:
            logger.warning(f"Order {event.order_id} not found for fill event")
            return
        
        # Update order with fill information
        existing_order.filled_quantity += event.filled_quantity
        existing_order.remaining_quantity = existing_order.quantity - existing_order.filled_quantity
        
        # Calculate new average fill price
        if existing_order.filled_quantity > 0:
            if existing_order.average_fill_price is None:
                existing_order.average_fill_price = event.fill_price
            else:
                # Weighted average
                total_value = (existing_order.average_fill_price * (existing_order.filled_quantity - event.filled_quantity) + 
                             event.fill_price * event.filled_quantity)
                existing_order.average_fill_price = total_value / existing_order.filled_quantity
        
        # Update status
        if existing_order.filled_quantity >= existing_order.quantity:
            existing_order.status = "filled"
            existing_order.filled_at = event.timestamp
        else:
            existing_order.status = "partially_filled"
        
        existing_order.updated_at = event.timestamp
        
        await self.read_model_repository.upsert_order(existing_order)
    
    async def _handle_order_cancelled(self, event):
        """Handle order cancelled event"""
        existing_order = await self.read_model_repository.get_order(event.order_id)
        if not existing_order:
            logger.warning(f"Order {event.order_id} not found for cancel event")
            return
        
        existing_order.status = "cancelled"
        existing_order.cancelled_at = event.timestamp
        existing_order.updated_at = event.timestamp
        
        await self.read_model_repository.upsert_order(existing_order)
    
    async def _handle_order_updated(self, event):
        """Handle order updated event"""
        existing_order = await self.read_model_repository.get_order(event.order_id)
        if not existing_order:
            logger.warning(f"Order {event.order_id} not found for update event")
            return
        
        # Update fields if provided
        if event.quantity is not None:
            existing_order.quantity = event.quantity
        if event.price is not None:
            existing_order.price = event.price
        if event.stop_price is not None:
            existing_order.stop_price = event.stop_price
        if event.time_in_force is not None:
            existing_order.time_in_force = event.time_in_force
        
        existing_order.updated_at = event.timestamp
        
        await self.read_model_repository.upsert_order(existing_order)
    
    # Portfolio event handlers
    async def _handle_portfolio_updated(self, event):
        """Handle portfolio updated event"""
        portfolio_read_model = PortfolioReadModel(
            portfolio_id=event.portfolio_id,
            user_id=event.user_id,
            account_id=event.account_id,
            name=event.name,
            cash_balance=event.cash_balance,
            total_value=event.total_value,
            total_cost=event.total_value,  # Simplified for now
            unrealized_pnl=event.total_value - event.cash_balance,
            realized_pnl=0,  # Would need to track separately
            total_return=0,
            total_return_percentage=0,
            position_count=0,  # Will be updated by position events
            last_updated=event.timestamp,
            metadata={}
        )
        
        await self.read_model_repository.upsert_portfolio(portfolio_read_model)
    
    async def _handle_position_opened(self, event):
        """Handle position opened event"""
        # Get existing position or create new one
        existing_position = await self.read_model_repository.get_position(
            event.portfolio_id, event.symbol
        )
        
        if existing_position:
            # Update existing position
            total_quantity = existing_position.quantity + event.quantity
            total_cost = existing_position.cost_basis + (event.quantity * event.price)
            
            existing_position.quantity = total_quantity
            existing_position.cost_basis = total_cost
            existing_position.average_price = total_cost / total_quantity
            existing_position.current_price = event.price
            existing_position.market_value = total_quantity * event.price
            existing_position.unrealized_pnl = existing_position.market_value - existing_position.cost_basis
        else:
            # Create new position
            position_read_model = PositionReadModel(
                portfolio_id=event.portfolio_id,
                symbol=event.symbol,
                quantity=event.quantity,
                cost_basis=event.quantity * event.price,
                average_price=event.price,
                current_price=event.price,
                market_value=event.market_value,
                unrealized_pnl=0,
                realized_pnl=0,
                return_percentage=0,
                opened_at=event.timestamp,
                last_updated=event.timestamp,
                metadata={}
            )
            existing_position = position_read_model
        
        await self.read_model_repository.upsert_position(existing_position)
        
        # Update portfolio position count
        await self._update_portfolio_position_count(event.portfolio_id)
    
    async def _handle_position_closed(self, event):
        """Handle position closed event"""
        existing_position = await self.read_model_repository.get_position(
            event.portfolio_id, event.symbol
        )
        
        if not existing_position:
            logger.warning(f"Position {event.symbol} not found for close event")
            return
        
        # Update position
        existing_position.quantity -= event.quantity
        
        if existing_position.quantity <= 0:
            # Delete position if fully closed
            await self.read_model_repository.delete_position(
                event.portfolio_id, event.symbol
            )
        else:
            # Update cost basis proportionally
            from decimal import Decimal
            remaining_ratio = Decimal(existing_position.quantity) / Decimal(existing_position.quantity + event.quantity)
            existing_position.cost_basis = existing_position.cost_basis * remaining_ratio
            existing_position.average_price = existing_position.cost_basis / Decimal(existing_position.quantity)
            existing_position.current_price = event.price
            existing_position.market_value = existing_position.quantity * event.price
            existing_position.unrealized_pnl = existing_position.market_value - existing_position.cost_basis
            existing_position.last_updated = event.timestamp
            
            await self.read_model_repository.upsert_position(existing_position)
        
        # Update portfolio position count
        await self._update_portfolio_position_count(event.portfolio_id)
    
    async def _handle_position_updated(self, event):
        """Handle position updated event"""
        existing_position = await self.read_model_repository.get_position(
            event.portfolio_id, event.symbol
        )
        
        if not existing_position:
            logger.warning(f"Position {event.symbol} not found for update event")
            return
        
        # Update fields
        if event.quantity is not None:
            existing_position.quantity = event.quantity
        if event.average_price is not None:
            existing_position.average_price = event.average_price
        if event.current_price is not None:
            existing_position.current_price = event.current_price
        if event.unrealized_pnl is not None:
            existing_position.unrealized_pnl = event.unrealized_pnl
        if event.realized_pnl is not None:
            existing_position.realized_pnl = event.realized_pnl
        
        existing_position.last_updated = event.timestamp
        
        await self.read_model_repository.upsert_position(existing_position)
    
    # Strategy event handlers
    async def _handle_strategy_created(self, event):
        """Handle strategy created event"""
        strategy_read_model = StrategyReadModel(
            strategy_id=event.strategy_id,
            name=event.name,
            strategy_type=event.strategy_type,
            parameters=event.parameters,
            is_active=True,
            created_at=event.timestamp,
            updated_at=event.timestamp,
            last_run_at=None,
            next_run_at=None,
            metadata={}
        )
        
        await self.read_model_repository.upsert_strategy(strategy_read_model)
    
    async def _handle_strategy_updated(self, event):
        """Handle strategy updated event"""
        existing_strategy = await self.read_model_repository.get_strategy(event.strategy_id)
        if not existing_strategy:
            logger.warning(f"Strategy {event.strategy_id} not found for update event")
            return
        
        # Update fields
        if event.name is not None:
            existing_strategy.name = event.name
        if event.parameters is not None:
            existing_strategy.parameters = event.parameters
        if event.is_active is not None:
            existing_strategy.is_active = event.is_active
        
        existing_strategy.updated_at = event.timestamp
        
        await self.read_model_repository.upsert_strategy(existing_strategy)
    
    async def _handle_strategy_deleted(self, event):
        """Handle strategy deleted event"""
        await self.read_model_repository.delete_strategy(event.strategy_id)
    
    async def _handle_strategy_started(self, event):
        """Handle strategy started event"""
        existing_strategy = await self.read_model_repository.get_strategy(event.strategy_id)
        if existing_strategy:
            existing_strategy.is_active = True
            existing_strategy.last_run_at = event.started_at
            existing_strategy.updated_at = event.started_at
            await self.read_model_repository.upsert_strategy(existing_strategy)
    
    async def _handle_strategy_stopped(self, event):
        """Handle strategy stopped event"""
        existing_strategy = await self.read_model_repository.get_strategy(event.strategy_id)
        if existing_strategy:
            existing_strategy.is_active = False
            existing_strategy.updated_at = event.stopped_at
            await self.read_model_repository.upsert_strategy(existing_strategy)
    
    # Signal event handlers
    async def _handle_signal_created(self, event):
        """Handle signal created event"""
        signal_read_model = SignalReadModel(
            signal_id=event.signal_id,
            symbol=event.symbol,
            signal_type=event.signal_type,
            strength=event.strength,
            price=event.price,
            quantity=event.quantity,
            strategy_id=event.strategy_id,
            is_active=True,
            created_at=event.timestamp,
            updated_at=event.timestamp,
            executed_at=None,
            expired_at=None,
            metadata={}
        )
        
        await self.read_model_repository.upsert_signal(signal_read_model)
    
    async def _handle_signal_updated(self, event):
        """Handle signal updated event"""
        existing_signal = await self.read_model_repository.get_signal(event.signal_id)
        if not existing_signal:
            logger.warning(f"Signal {event.signal_id} not found for update event")
            return
        
        # Update fields
        if event.signal_type is not None:
            existing_signal.signal_type = event.signal_type
        if event.strength is not None:
            existing_signal.strength = event.strength
        if event.price is not None:
            existing_signal.price = event.price
        if event.quantity is not None:
            existing_signal.quantity = event.quantity
        
        existing_signal.updated_at = event.timestamp
        
        await self.read_model_repository.upsert_signal(existing_signal)
    
    async def _handle_signal_deleted(self, event):
        """Handle signal deleted event"""
        await self.read_model_repository.delete_signal(event.signal_id)
    
    async def _handle_signal_executed(self, event):
        """Handle signal executed event"""
        existing_signal = await self.read_model_repository.get_signal(event.signal_id)
        if existing_signal:
            existing_signal.is_active = False
            existing_signal.executed_at = event.timestamp
            existing_signal.updated_at = event.timestamp
            await self.read_model_repository.upsert_signal(existing_signal)
    
    # Market data event handlers
    async def _handle_market_data_updated(self, event):
        """Handle market data updated event"""
        market_data_read_model = MarketDataReadModel(
            symbol=event.symbol,
            price=event.price,
            volume=event.volume,
            timestamp=event.timestamp,
            indicators=event.indicators or {},
            metadata={}
        )
        
        await self.read_model_repository.upsert_market_data(market_data_read_model)
    
    async def _handle_market_data_error(self, event):
        """Handle market data error event"""
        # Log the error but don't update read models
        logger.error(f"Market data error for {event.symbol}: {event.error}")
    
    # Performance event handlers
    async def _handle_performance_calculated(self, event):
        """Handle performance calculated event"""
        performance_read_model = PerformanceReadModel(
            portfolio_id=event.portfolio_id,
            period_start=event.period_start,
            period_end=event.period_end,
            total_return=event.total_return,
            total_return_percentage=event.total_return_percentage,
            calculated_at=event.calculated_at,
            metadata={}
        )
        
        await self.read_model_repository.upsert_performance(performance_read_model)
    
    async def _handle_performance_alert(self, event):
        """Handle performance alert event"""
        # Log the alert but don't update read models
        logger.warning(f"Performance alert for {event.portfolio_id}: {event.message}")
    
    # Backtest event handlers
    async def _handle_backtest_started(self, event):
        """Handle backtest started event"""
        # Could create a backtest read model if needed
        logger.info(f"Backtest started: {event.backtest_id}")
    
    async def _handle_backtest_completed(self, event):
        """Handle backtest completed event"""
        # Could create a backtest results read model if needed
        logger.info(f"Backtest completed: {event.backtest_id}")
    
    async def _handle_backtest_failed(self, event):
        """Handle backtest failed event"""
        logger.error(f"Backtest failed: {event.backtest_id} - {event.error}")
    
    # Risk event handlers
    async def _handle_risk_limit_exceeded(self, event):
        """Handle risk limit exceeded event"""
        logger.warning(f"Risk limit exceeded for {event.portfolio_id}: {event.limit_type}")
    
    async def _handle_risk_alert_triggered(self, event):
        """Handle risk alert triggered event"""
        logger.warning(f"Risk alert triggered for {event.portfolio_id}: {event.alert_type}")
    
    async def _handle_risk_alert_resolved(self, event):
        """Handle risk alert resolved event"""
        logger.info(f"Risk alert resolved for {event.portfolio_id}: {event.alert_id}")
    
    # Helper methods
    async def _update_portfolio_position_count(self, portfolio_id: str):
        """Update the position count for a portfolio"""
        try:
            positions = await self.read_model_repository.get_positions(portfolio_id)
            position_count = len(positions)
            
            # Update portfolio with new position count
            portfolio = await self.read_model_repository.get_portfolio(portfolio_id)
            if portfolio:
                portfolio.position_count = position_count
                portfolio.last_updated = datetime.utcnow()
                await self.read_model_repository.upsert_portfolio(portfolio)
        except Exception as e:
            logger.error(f"Failed to update portfolio position count for {portfolio_id}: {e}")
