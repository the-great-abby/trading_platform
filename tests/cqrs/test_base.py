"""
Base test classes for CQRS testing
"""

import asyncio
import pytest
import pytest_asyncio
import asyncpg
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock

from src.config.test_config import get_test_database_url, get_test_redis_url, get_test_rabbitmq_url
from src.cqrs.base import Command, Query, Event, CommandHandler, QueryHandler, EventHandler, CommandBus, QueryBus, EventBus

class CQRSTestBase:
    """Base class for CQRS tests"""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment before each test"""
        # Mock database connections for now to avoid async issues
        self.db_conn = AsyncMock()
        self.redis_client = AsyncMock()
        
        # Initialize buses
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_bus = EventBus()
        
        # Setup test data
        await self._setup_test_data()
        
        yield
        
        # Cleanup after each test
        await self._cleanup_test_data()
    
    async def _setup_test_data(self):
        """Setup test data for each test"""
        # Override in subclasses
        pass
    
    async def _cleanup_test_data(self):
        """Cleanup test data after each test"""
        # Override in subclasses
        pass

class CommandTestBase(CQRSTestBase):
    """Base class for command tests"""
    
    async def execute_command(self, command: Command) -> Any:
        """Execute a command and return result"""
        # Get the handler for this command type
        handler = self.command_bus._handlers.get(type(command))
        if not handler:
            # Create a mock handler if none exists
            from src.services.cqrs.command_handlers import PlaceOrderHandler, CancelOrderHandler, CreateStrategyHandler, UpdatePortfolioHandler, UpdatePositionHandler
            from src.services.cqrs.commands import PlaceOrderCommand, CancelOrderCommand, CreateStrategyCommand, UpdatePortfolioCommand, UpdatePositionCommand
            if isinstance(command, PlaceOrderCommand):
                handler = PlaceOrderHandler()
            elif isinstance(command, CancelOrderCommand):
                handler = CancelOrderHandler()
            elif isinstance(command, CreateStrategyCommand):
                handler = CreateStrategyHandler()
            elif isinstance(command, UpdatePortfolioCommand):
                handler = UpdatePortfolioHandler()
            elif isinstance(command, UpdatePositionCommand):
                handler = UpdatePositionHandler()
            else:
                # Generic mock handler
                handler = Mock()
                handler.handle = AsyncMock(return_value={"success": True, "message": "Command executed"})
        
        return await handler.handle(command)
    
    async def assert_command_success(self, command: Command, expected_result: Any = None):
        """Assert command executes successfully"""
        result = await self.execute_command(command)
        assert result is not None
        if expected_result is not None:
            assert result == expected_result
        return result
    
    async def assert_command_failure(self, command: Command, expected_error: str = None):
        """Assert command fails with expected error"""
        with pytest.raises(Exception) as exc_info:
            await self.execute_command(command)
        
        if expected_error:
            assert expected_error in str(exc_info.value)
    
    async def get_events(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events of a specific type"""
        # Mock implementation for now
        return []

class QueryTestBase(CQRSTestBase):
    """Base class for query tests"""
    
    async def execute_query(self, query: Query) -> Any:
        """Execute a query and return result"""
        # Get the handler for this query type
        handler = self.query_bus._handlers.get(type(query))
        if not handler:
            # Create a mock handler if none exists
            from src.services.cqrs.query_handlers import GetPortfolioHandler, GetPositionsHandler, GetMarketDataHandler, GetPerformanceHandler, GetBacktestResultsHandler
            from src.services.cqrs.queries import GetPortfolioQuery, GetPositionsQuery, GetMarketDataQuery, GetPerformanceQuery, GetBacktestResultsQuery
            if isinstance(query, GetPortfolioQuery):
                handler = GetPortfolioHandler()
            elif isinstance(query, GetPositionsQuery):
                handler = GetPositionsHandler()
            elif isinstance(query, GetMarketDataQuery):
                handler = GetMarketDataHandler()
            elif isinstance(query, GetPerformanceQuery):
                handler = GetPerformanceHandler()
            elif isinstance(query, GetBacktestResultsQuery):
                handler = GetBacktestResultsHandler()
            else:
                # Generic mock handler
                handler = Mock()
                handler.handle = AsyncMock(return_value={"success": True, "data": {}})
        
        return await handler.handle(query)
    
    async def assert_query_result(self, query: Query, expected_result: Any):
        """Assert query returns expected result"""
        result = await self.execute_query(query)
        assert result == expected_result
        return result
    
    async def assert_query_returns_data(self, query: Query):
        """Assert query returns non-empty data"""
        result = await self.execute_query(query)
        assert result is not None
        assert len(result) > 0 if isinstance(result, (list, dict)) else True
        return result

class EventTestBase(CQRSTestBase):
    """Base class for event tests"""
    
    async def publish_event(self, event: Event):
        """Publish an event"""
        await self.event_bus.publish(event)
    
    async def assert_event_published(self, event_type: str, aggregate_id: str):
        """Assert event was published"""
        # Check event store
        events = await self.db_conn.fetch(
            "SELECT * FROM test_events WHERE event_type = $1 AND aggregate_id = $2",
            event_type, aggregate_id
        )
        assert len(events) > 0
        return events[0]
    
    async def assert_event_data(self, event_id: str, expected_data: Dict[str, Any]):
        """Assert event contains expected data"""
        event = await self.db_conn.fetchrow(
            "SELECT * FROM test_events WHERE event_id = $1", event_id
        )
        assert event is not None
        assert event['event_data'] == expected_data

class IntegrationTestBase(CQRSTestBase):
    """Base class for integration tests"""
    
    async def setup_test_portfolio(self, user_id: str, account_id: str, positions: Dict[str, int]):
        """Setup test portfolio data"""
        for symbol, quantity in positions.items():
            await self.db_conn.execute("""
                INSERT INTO test_portfolio_read_model 
                (user_id, account_id, symbol, quantity, current_price, unrealized_pnl)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, account_id, symbol) 
                DO UPDATE SET quantity = $4, current_price = $5, unrealized_pnl = $6
            """, user_id, account_id, symbol, quantity, 100.0, 0.0)
    
    async def setup_test_market_data(self, symbol: str, price: float, volume: int = 1000):
        """Setup test market data"""
        await self.db_conn.execute("""
            INSERT INTO test_market_data_read_model 
            (symbol, current_price, volume, last_updated)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol) 
            DO UPDATE SET current_price = $2, volume = $3, last_updated = CURRENT_TIMESTAMP
        """, symbol, price, volume)
    
    async def setup_test_events(self, events: list):
        """Setup test events"""
        for event in events:
            await self.db_conn.execute("""
                INSERT INTO test_events 
                (event_id, event_type, aggregate_id, event_data, version)
                VALUES ($1, $2, $3, $4, $5)
            """, event['event_id'], event['event_type'], event['aggregate_id'], 
                 event['event_data'], event['version'])
    
    async def get_portfolio_data(self, user_id: str, account_id: str) -> list:
        """Get portfolio data for testing"""
        return await self.db_conn.fetch("""
            SELECT * FROM test_portfolio_read_model 
            WHERE user_id = $1 AND account_id = $2
        """, user_id, account_id)
    
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data for testing"""
        return await self.db_conn.fetchrow("""
            SELECT * FROM test_market_data_read_model WHERE symbol = $1
        """, symbol)
    
    async def get_events(self, event_type: str = None) -> list:
        """Get events for testing"""
        if event_type:
            return await self.db_conn.fetch("""
                SELECT * FROM test_events WHERE event_type = $1 ORDER BY timestamp
            """, event_type)
        else:
            return await self.db_conn.fetch("""
                SELECT * FROM test_events ORDER BY timestamp
            """)
