"""
Main CQRS Service
Orchestrates all CQRS components: commands, queries, events, and projections
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.read_model_repository import ReadModelRepository
from src.services.cqrs.event_sourcing_service import EventSourcingService
from src.services.cqrs.projection_update_service import ProjectionUpdateService
from src.services.cqrs.event_subscription_service import EventSubscriptionService
from src.services.cqrs.command_handlers import (
    PlaceOrderHandler, CancelOrderHandler, UpdateOrderHandler,
    CreateStrategyHandler, UpdateStrategyHandler, DeleteStrategyHandler,
    CreateSignalHandler, UpdateSignalHandler, DeleteSignalHandler,
    UpdatePortfolioHandler, UpdatePositionHandler
)
from src.services.cqrs.query_handlers import (
    GetPortfolioHandler, GetPositionsHandler, GetMarketDataHandler,
    GetPerformanceHandler, GetBacktestResultsHandler, GetOrderHandler,
    GetStrategyHandler, GetSignalHandler, GetTradingHistoryHandler
)
from src.services.cqrs.commands import (
    PlaceOrderCommand, CancelOrderCommand, UpdateOrderCommand,
    CreateStrategyCommand, UpdateStrategyCommand, DeleteStrategyCommand,
    CreateSignalCommand, UpdateSignalCommand, DeleteSignalCommand,
    UpdatePortfolioCommand, UpdatePositionCommand
)
from src.services.cqrs.queries import (
    GetPortfolioQuery, GetPositionsQuery, GetMarketDataQuery,
    GetPerformanceQuery, GetBacktestResultsQuery, GetOrderQuery,
    GetStrategyQuery, GetSignalQuery, GetTradingHistoryQuery
)
from src.cqrs.base import CommandBus, QueryBus, EventBus

logger = logging.getLogger(__name__)


class CQRSService:
    """Main service that orchestrates all CQRS operations"""
    
    def __init__(self, db_conn, redis_client=None):
        self.db_conn = db_conn
        self.redis_client = redis_client
        
        # Initialize core services
        self.event_store = EventStore(db_conn)
        self.read_model_repository = ReadModelRepository(db_conn)
        self.event_sourcing_service = EventSourcingService(self.event_store, self.read_model_repository)
        self.projection_update_service = ProjectionUpdateService(self.event_store, self.read_model_repository)
        self.event_subscription_service = EventSubscriptionService(self.event_store, self.projection_update_service)
        
        # Initialize buses
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_bus = EventBus()
        
        # Initialize command and query handlers
        self._command_handlers = {}
        self._query_handlers = {}
        self._register_handlers()
        
        # Event subscription task
        self._subscription_task: Optional[asyncio.Task] = None
    
    def _register_handlers(self):
        """Register all command and query handlers"""
        # Command handlers
        self._command_handlers = {
            PlaceOrderCommand: PlaceOrderHandler(self.db_conn, self.event_sourcing_service),
            CancelOrderCommand: CancelOrderHandler(self.db_conn, self.event_sourcing_service),
            UpdateOrderCommand: UpdateOrderHandler(self.db_conn, self.event_sourcing_service),
            CreateStrategyCommand: CreateStrategyHandler(self.db_conn, self.event_sourcing_service),
            UpdateStrategyCommand: UpdateStrategyHandler(self.db_conn, self.event_sourcing_service),
            DeleteStrategyCommand: DeleteStrategyHandler(self.db_conn, self.event_sourcing_service),
            CreateSignalCommand: CreateSignalHandler(self.db_conn, self.event_sourcing_service),
            UpdateSignalCommand: UpdateSignalHandler(self.db_conn, self.event_sourcing_service),
            DeleteSignalCommand: DeleteSignalHandler(self.db_conn, self.event_sourcing_service),
            UpdatePortfolioCommand: UpdatePortfolioHandler(self.db_conn, self.event_sourcing_service),
            UpdatePositionCommand: UpdatePositionHandler(self.db_conn, self.event_sourcing_service),
        }
        
        # Query handlers
        self._query_handlers = {
            GetPortfolioQuery: GetPortfolioHandler(self.db_conn),
            GetPositionsQuery: GetPositionsHandler(self.db_conn),
            GetMarketDataQuery: GetMarketDataHandler(self.db_conn),
            GetPerformanceQuery: GetPerformanceHandler(self.db_conn),
            GetBacktestResultsQuery: GetBacktestResultsHandler(self.db_conn),
            GetOrderQuery: GetOrderHandler(self.db_conn),
            GetStrategyQuery: GetStrategyHandler(self.db_conn),
            GetSignalQuery: GetSignalHandler(self.db_conn),
            GetTradingHistoryQuery: GetTradingHistoryHandler(self.db_conn),
        }
        
        # Register handlers with buses
        for command_type, handler in self._command_handlers.items():
            self.command_bus.register_handler(command_type, handler)
        
        for query_type, handler in self._query_handlers.items():
            self.query_bus.register_handler(query_type, handler)
    
    async def initialize(self) -> bool:
        """Initialize the CQRS service"""
        try:
            # Initialize event store and read model repository
            await self.event_store.create_tables()
            await self.read_model_repository.create_tables()
            
            # Start event subscription service
            await self.start_event_subscription()
            
            logger.info("CQRS service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CQRS service: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the CQRS service"""
        try:
            # Stop event subscription service
            await self.event_subscription_service.stop()
            
            # Cancel subscription task
            if self._subscription_task and not self._subscription_task.done():
                self._subscription_task.cancel()
                try:
                    await self._subscription_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("CQRS service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during CQRS service shutdown: {e}")
    
    async def start_event_subscription(self, poll_interval: float = 1.0):
        """Start the event subscription service"""
        if self._subscription_task and not self._subscription_task.done():
            logger.warning("Event subscription is already running")
            return
        
        self._subscription_task = asyncio.create_task(
            self.event_subscription_service.start(poll_interval)
        )
        logger.info("Event subscription service started")
    
    async def stop_event_subscription(self):
        """Stop the event subscription service"""
        await self.event_subscription_service.stop()
        if self._subscription_task and not self._subscription_task.done():
            self._subscription_task.cancel()
        logger.info("Event subscription service stopped")
    
    # Command execution methods
    async def execute_command(self, command: Any, correlation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Execute a command"""
        try:
            command_type = type(command)
            handler = self._command_handlers.get(command_type)
            
            if not handler:
                return {
                    "success": False,
                    "error": f"No handler found for command type: {command_type.__name__}"
                }
            
            # Set correlation ID if not provided
            if correlation_id is None:
                correlation_id = uuid4()
            
            # Execute command
            result = await handler.handle(command)
            
            # Process any events that were generated
            if hasattr(handler, 'get_uncommitted_events'):
                events = handler.get_uncommitted_events()
                if events:
                    for event in events:
                        await self.event_subscription_service.process_event_immediately(event)
            
            return {
                "success": True,
                "result": result,
                "correlation_id": correlation_id
            }
            
        except Exception as e:
            logger.error(f"Failed to execute command {command.__class__.__name__}: {e}")
            return {
                "success": False,
                "error": str(e),
                "correlation_id": correlation_id
            }
    
    # Query execution methods
    async def execute_query(self, query: Any) -> Dict[str, Any]:
        """Execute a query"""
        try:
            query_type = type(query)
            handler = self._query_handlers.get(query_type)
            
            if not handler:
                return {
                    "success": False,
                    "error": f"No handler found for query type: {query_type.__name__}"
                }
            
            # Execute query
            result = await handler.handle(query)
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to execute query {query.__class__.__name__}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Event sourcing methods
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
    ) -> Dict[str, Any]:
        """Place an order using event sourcing"""
        return await self.event_sourcing_service.place_order(
            order_id, symbol, side, quantity, order_type, price,
            user_id, account_id, correlation_id
        )
    
    async def fill_order(
        self,
        order_id: str,
        filled_quantity: int,
        fill_price: float,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Fill an order using event sourcing"""
        return await self.event_sourcing_service.fill_order(
            order_id, filled_quantity, fill_price, correlation_id
        )
    
    async def cancel_order(
        self,
        order_id: str,
        reason: str = "User requested",
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Cancel an order using event sourcing"""
        return await self.event_sourcing_service.cancel_order(
            order_id, reason, correlation_id
        )
    
    async def update_portfolio(
        self,
        portfolio_id: str,
        user_id: str,
        account_id: str,
        name: str,
        cash_balance: float,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Update portfolio using event sourcing"""
        return await self.event_sourcing_service.update_portfolio(
            portfolio_id, user_id, account_id, name, cash_balance, correlation_id
        )
    
    async def open_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: int,
        price: float,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Open a position using event sourcing"""
        return await self.event_sourcing_service.open_position(
            portfolio_id, symbol, quantity, price, correlation_id
        )
    
    async def close_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: int,
        price: float,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Close a position using event sourcing"""
        return await self.event_sourcing_service.close_position(
            portfolio_id, symbol, quantity, price, correlation_id
        )
    
    # Query methods
    async def get_portfolio(
        self,
        portfolio_id: Optional[str] = None,
        user_id: Optional[str] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get portfolio information"""
        query = GetPortfolioQuery(
            portfolio_id=portfolio_id,
            user_id=user_id,
            account_id=account_id
        )
        return await self.execute_query(query)
    
    async def get_positions(
        self,
        portfolio_id: str,
        symbol: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get positions for a portfolio"""
        query = GetPositionsQuery(
            portfolio_id=portfolio_id,
            symbol=symbol,
            filters=filters or {}
        )
        return await self.execute_query(query)
    
    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get market data for a symbol"""
        query = GetMarketDataQuery(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return await self.execute_query(query)
    
    async def get_performance(
        self,
        portfolio_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance data for a portfolio"""
        query = GetPerformanceQuery(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date
        )
        return await self.execute_query(query)
    
    # Event replay methods
    async def rebuild_all_projections(self) -> Dict[str, int]:
        """Rebuild all projections from event history"""
        return await self.event_sourcing_service.rebuild_all_projections()
    
    async def replay_events_from_timestamp(self, from_timestamp: datetime) -> Dict[str, int]:
        """Replay events from a specific timestamp"""
        return await self.event_subscription_service.replay_events_from_timestamp(from_timestamp)
    
    # Event subscription methods
    async def subscribe_to_event_type(self, event_type: str, handler):
        """Subscribe to a specific event type"""
        self.event_subscription_service.subscribe_to_event_type(event_type, handler)
    
    async def unsubscribe_from_event_type(self, event_type: str, handler):
        """Unsubscribe from a specific event type"""
        self.event_subscription_service.unsubscribe_from_event_type(event_type, handler)
    
    # Status and monitoring methods
    async def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of the CQRS service"""
        subscription_status = await self.event_subscription_service.get_subscription_status()
        
        return {
            "service_status": "running",
            "event_subscription": subscription_status,
            "command_handlers": len(self._command_handlers),
            "query_handlers": len(self._query_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the CQRS service"""
        try:
            # Test database connection
            await self.db_conn.execute("SELECT 1")
            
            # Test event store
            await self.event_store.get_aggregate_version("health_check", "HealthCheck")
            
            # Test read model repository
            await self.read_model_repository.get_portfolio("health_check")
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "database": "connected",
                    "event_store": "operational",
                    "read_models": "operational",
                    "event_subscription": subscription_status["is_running"]
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
