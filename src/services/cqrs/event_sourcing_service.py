"""
Event Sourcing Service for CQRS
Main service that coordinates event sourcing operations
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.aggregate_root import AggregateRoot, OrderAggregate, PortfolioAggregate
from src.services.cqrs.event_replay_service import EventReplayService
from src.services.cqrs.read_model_repository import ReadModelRepository

logger = logging.getLogger(__name__)


class EventSourcingService:
    """Main service for event sourcing operations"""
    
    def __init__(self, event_store: EventStore, read_model_repository: ReadModelRepository):
        self.event_store = event_store
        self.read_model_repository = read_model_repository
        self.replay_service = EventReplayService(event_store, read_model_repository)
    
    async def initialize(self):
        """Initialize the event sourcing service"""
        try:
            # Create event store tables
            await self.event_store.create_tables()
            
            # Create read model tables
            await self.read_model_repository.create_tables()
            
            logger.info("Event sourcing service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize event sourcing service: {e}")
            return False
    
    # Order operations
    async def place_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
        price: Optional[float],
        user_id: str,
        account_id: str,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Place a new order using event sourcing"""
        try:
            # Create order aggregate
            order = OrderAggregate(order_id)
            order.set_event_store(self.event_store)
            
            # Place the order (this creates events)
            order.place_order(symbol, side, quantity, order_type, price, user_id, account_id)
            
            # Save events to event store
            success = await order.save(
                correlation_id=correlation_id,
                user_id=user_id
            )
            
            if success:
                # Update read models
                await self.replay_service._update_order_read_model(order)
                logger.info(f"Order {order_id} placed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to place order {order_id}: {e}")
            return False
    
    async def fill_order(
        self,
        order_id: str,
        filled_quantity: int,
        fill_price: float,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Fill an order using event sourcing"""
        try:
            # Load order from event history
            order = await self._load_order(order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                return False
            
            # Fill the order
            order.fill_order(filled_quantity, fill_price)
            
            # Save events
            success = await order.save(correlation_id=correlation_id)
            
            if success:
                # Update read models
                await self.replay_service._update_order_read_model(order)
                logger.info(f"Order {order_id} filled successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to fill order {order_id}: {e}")
            return False
    
    async def cancel_order(
        self,
        order_id: str,
        reason: str = "User requested",
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Cancel an order using event sourcing"""
        try:
            # Load order from event history
            order = await self._load_order(order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                return False
            
            # Cancel the order
            order.cancel_order(reason)
            
            # Save events
            success = await order.save(correlation_id=correlation_id)
            
            if success:
                # Update read models
                await self.replay_service._update_order_read_model(order)
                logger.info(f"Order {order_id} cancelled successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    # Portfolio operations
    async def update_portfolio(
        self,
        portfolio_id: str,
        user_id: str,
        account_id: str,
        name: str,
        cash_balance: float,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Update portfolio using event sourcing"""
        try:
            # Load or create portfolio
            portfolio = await self._load_portfolio(portfolio_id)
            if not portfolio:
                portfolio = PortfolioAggregate(portfolio_id)
                portfolio.set_event_store(self.event_store)
            
            # Update portfolio
            portfolio.update_portfolio(user_id, account_id, name, cash_balance)
            
            # Save events
            success = await portfolio.save(
                correlation_id=correlation_id,
                user_id=user_id
            )
            
            if success:
                # Update read models
                await self.replay_service._update_portfolio_read_model(portfolio)
                logger.info(f"Portfolio {portfolio_id} updated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
            return False
    
    async def open_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: int,
        price: float,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Open a position using event sourcing"""
        try:
            # Load portfolio
            portfolio = await self._load_portfolio(portfolio_id)
            if not portfolio:
                logger.error(f"Portfolio {portfolio_id} not found")
                return False
            
            # Open position
            portfolio.open_position(symbol, quantity, price)
            
            # Save events
            success = await portfolio.save(correlation_id=correlation_id)
            
            if success:
                # Update read models
                await self.replay_service._update_portfolio_read_model(portfolio)
                logger.info(f"Position {symbol} opened in portfolio {portfolio_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to open position {symbol} in portfolio {portfolio_id}: {e}")
            return False
    
    async def close_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: int,
        price: float,
        correlation_id: Optional[UUID] = None
    ) -> bool:
        """Close a position using event sourcing"""
        try:
            # Load portfolio
            portfolio = await self._load_portfolio(portfolio_id)
            if not portfolio:
                logger.error(f"Portfolio {portfolio_id} not found")
                return False
            
            # Close position
            portfolio.close_position(symbol, quantity, price)
            
            # Save events
            success = await portfolio.save(correlation_id=correlation_id)
            
            if success:
                # Update read models
                await self.replay_service._update_portfolio_read_model(portfolio)
                logger.info(f"Position {symbol} closed in portfolio {portfolio_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to close position {symbol} in portfolio {portfolio_id}: {e}")
            return False
    
    # Aggregate loading methods
    async def _load_order(self, order_id: str) -> Optional[OrderAggregate]:
        """Load order aggregate from event history"""
        try:
            events = await self.event_store.get_events(order_id, "Order")
            if not events:
                return None
            
            order = OrderAggregate(order_id)
            order.set_event_store(self.event_store)
            order.load_from_history(events)
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to load order {order_id}: {e}")
            return None
    
    async def _load_portfolio(self, portfolio_id: str) -> Optional[PortfolioAggregate]:
        """Load portfolio aggregate from event history"""
        try:
            events = await self.event_store.get_events(portfolio_id, "Portfolio")
            if not events:
                return None
            
            portfolio = PortfolioAggregate(portfolio_id)
            portfolio.set_event_store(self.event_store)
            portfolio.load_from_history(events)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to load portfolio {portfolio_id}: {e}")
            return None
    
    # Event replay and projection methods
    async def rebuild_all_projections(self) -> Dict[str, int]:
        """Rebuild all projections from event history"""
        return await self.replay_service.rebuild_all_projections()
    
    async def rebuild_aggregate_projection(self, aggregate_id: str, aggregate_type: str) -> bool:
        """Rebuild projection for a specific aggregate"""
        return await self.replay_service.rebuild_aggregate_projection(aggregate_id, aggregate_type)
    
    async def process_new_events(self) -> int:
        """Process new events since last run"""
        return await self.replay_service.process_new_events()
    
    # Event query methods
    async def get_events_for_aggregate(
        self,
        aggregate_id: str,
        aggregate_type: str,
        from_version: int = 0
    ) -> List[Any]:
        """Get events for a specific aggregate"""
        return await self.event_store.get_events(aggregate_id, aggregate_type, from_version)
    
    async def get_events_by_type(
        self,
        event_type: str,
        from_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Any]:
        """Get events by type"""
        return await self.event_store.get_events_by_type(event_type, from_date, limit=limit)
    
    async def get_events_by_correlation(self, correlation_id: UUID) -> List[Any]:
        """Get all events for a correlation ID"""
        return await self.event_store.get_events_by_correlation(correlation_id)
    
    # Snapshot methods
    async def save_aggregate_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int
    ) -> bool:
        """Save a snapshot of an aggregate"""
        try:
            # Load aggregate
            if aggregate_type == "Order":
                aggregate = await self._load_order(aggregate_id)
            elif aggregate_type == "Portfolio":
                aggregate = await self._load_portfolio(aggregate_id)
            else:
                logger.error(f"Unknown aggregate type: {aggregate_type}")
                return False
            
            if not aggregate:
                logger.error(f"Aggregate {aggregate_id} not found")
                return False
            
            # Save snapshot
            snapshot_data = aggregate.to_snapshot()
            return await self.event_store.save_snapshot(aggregate_id, aggregate_type, version, snapshot_data)
            
        except Exception as e:
            logger.error(f"Failed to save snapshot for {aggregate_id}: {e}")
            return False
    
    async def get_aggregate_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a snapshot of an aggregate"""
        return await self.event_store.get_snapshot(aggregate_id, aggregate_type, version)
