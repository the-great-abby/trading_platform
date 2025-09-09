"""
Tests for Event Sourcing System
"""

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.aggregate_root import OrderAggregate, PortfolioAggregate
from src.services.cqrs.event_sourcing_service import EventSourcingService
from src.services.cqrs.read_model_repository import ReadModelRepository
from src.services.cqrs.events import OrderCreatedEvent, OrderFilledEvent, PortfolioUpdatedEvent


@pytest.mark.asyncio
class TestEventStore:
    """Test event store functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.db_conn = AsyncMock()
        self.event_store = EventStore(self.db_conn)
    
    async def test_create_tables(self):
        """Test event store table creation"""
        await self.setup_test_environment()
        
        # Mock the database operations
        self.db_conn.execute = AsyncMock()
        
        result = await self.event_store.create_tables()
        
        # Verify that execute was called multiple times for table creation
        assert self.db_conn.execute.call_count >= 3  # At least 3 table creation calls
    
    async def test_append_events(self):
        """Test appending events to the store"""
        await self.setup_test_environment()
        
        # Mock transaction and execute
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.db_conn.transaction.return_value = mock_transaction
        self.db_conn.execute = AsyncMock()
        
        # Create test events
        events = [
            OrderCreatedEvent(
                order_id="test_order_1",
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="market",
                price=None,
                user_id="user1",
                account_id="acc1"
            )
        ]
        
        result = await self.event_store.append_events(
            aggregate_id="test_order_1",
            aggregate_type="Order",
            events=events
        )
        
        assert result == True
        assert self.db_conn.execute.call_count >= 2  # At least 2 calls (insert + update stream)
    
    async def test_get_events(self):
        """Test retrieving events from the store"""
        await self.setup_test_environment()
        
        # Mock fetch results
        mock_row = {
            'event_type': 'OrderCreatedEvent',
            'event_data': {
                'order_id': 'test_order_1',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 100,
                'order_type': 'market',
                'price': None,
                'user_id': 'user1',
                'account_id': 'acc1',
                'occurred_at': datetime.utcnow().isoformat()
            },
            'metadata': {},
            'occurred_at': datetime.utcnow(),
            'event_version': 1
        }
        
        self.db_conn.fetch = AsyncMock(return_value=[mock_row])
        
        events = await self.event_store.get_events("test_order_1", "Order")
        
        assert len(events) == 1
        assert isinstance(events[0], OrderCreatedEvent)
        assert events[0].order_id == "test_order_1"
        assert events[0].symbol == "AAPL"


@pytest.mark.asyncio
class TestOrderAggregate:
    """Test order aggregate functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.event_store = AsyncMock()
        self.order = OrderAggregate("test_order_1")
        self.order.set_event_store(self.event_store)
    
    async def test_place_order(self):
        """Test placing an order"""
        await self.setup_test_environment()
        
        # Place order
        self.order.place_order(
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            price=None,
            user_id="user1",
            account_id="acc1"
        )
        
        # Check that event was created
        uncommitted_events = self.order.get_uncommitted_events()
        assert len(uncommitted_events) == 1
        assert isinstance(uncommitted_events[0], OrderCreatedEvent)
        assert uncommitted_events[0].symbol == "AAPL"
        assert uncommitted_events[0].quantity == 100
        
        # Check aggregate state
        assert self.order.symbol == "AAPL"
        assert self.order.side == "buy"
        assert self.order.quantity == 100
        assert self.order.user_id == "user1"
    
    async def test_fill_order(self):
        """Test filling an order"""
        await self.setup_test_environment()
        
        # First place the order
        self.order.place_order("AAPL", "buy", 100, "market", None, "user1", "acc1")
        
        # Then fill it
        self.order.fill_order(50, 150.0)
        
        # Check events
        uncommitted_events = self.order.get_uncommitted_events()
        assert len(uncommitted_events) == 2  # Created + Filled
        
        # Check aggregate state
        assert self.order.filled_quantity == 50
        assert self.order.average_fill_price == 150.0
        assert self.order.status == "partially_filled"
    
    async def test_cancel_order(self):
        """Test cancelling an order"""
        await self.setup_test_environment()
        
        # Place and then cancel order
        self.order.place_order("AAPL", "buy", 100, "market", None, "user1", "acc1")
        self.order.cancel_order("User requested")
        
        # Check events
        uncommitted_events = self.order.get_uncommitted_events()
        assert len(uncommitted_events) == 2  # Created + Cancelled
        
        # Check aggregate state
        assert self.order.status == "cancelled"
    
    async def test_load_from_history(self):
        """Test loading aggregate from event history"""
        await self.setup_test_environment()
        
        # Create events
        events = [
            OrderCreatedEvent(
                order_id="test_order_1",
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="market",
                price=None,
                user_id="user1",
                account_id="acc1"
            ),
            OrderFilledEvent(
                order_id="test_order_1",
                filled_quantity=50,
                fill_price=150.0,
                remaining_quantity=50
            )
        ]
        
        # Load from history
        self.order.load_from_history(events)
        
        # Check state
        assert self.order.symbol == "AAPL"
        assert self.order.quantity == 100
        assert self.order.filled_quantity == 50
        assert self.order.status == "partially_filled"
        assert len(self.order.get_uncommitted_events()) == 0  # No uncommitted events


@pytest.mark.asyncio
class TestPortfolioAggregate:
    """Test portfolio aggregate functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.event_store = AsyncMock()
        self.portfolio = PortfolioAggregate("test_portfolio_1")
        self.portfolio.set_event_store(self.event_store)
    
    async def test_update_portfolio(self):
        """Test updating portfolio"""
        await self.setup_test_environment()
        
        # Update portfolio
        self.portfolio.update_portfolio(
            user_id="user1",
            account_id="acc1",
            name="Test Portfolio",
            cash_balance=10000.0
        )
        
        # Check events
        uncommitted_events = self.portfolio.get_uncommitted_events()
        assert len(uncommitted_events) == 1
        assert isinstance(uncommitted_events[0], PortfolioUpdatedEvent)
        
        # Check state
        assert self.portfolio.user_id == "user1"
        assert self.portfolio.account_id == "acc1"
        assert self.portfolio.cash_balance == 10000.0
    
    async def test_open_position(self):
        """Test opening a position"""
        await self.setup_test_environment()
        
        # First update portfolio
        self.portfolio.update_portfolio("user1", "acc1", "Test Portfolio", 10000.0)
        
        # Then open position
        self.portfolio.open_position("AAPL", 100, 150.0)
        
        # Check state
        assert "AAPL" in self.portfolio.positions
        assert self.portfolio.positions["AAPL"]["quantity"] == 100
        assert self.portfolio.positions["AAPL"]["average_price"] == 150.0
    
    async def test_close_position(self):
        """Test closing a position"""
        await self.setup_test_environment()
        
        # Setup portfolio with position
        self.portfolio.update_portfolio("user1", "acc1", "Test Portfolio", 10000.0)
        self.portfolio.open_position("AAPL", 100, 150.0)
        
        # Close part of position
        self.portfolio.close_position("AAPL", 50, 160.0)
        
        # Check state
        assert self.portfolio.positions["AAPL"]["quantity"] == 50  # 100 - 50


@pytest.mark.asyncio
class TestEventSourcingService:
    """Test event sourcing service"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.db_conn = AsyncMock()
        self.event_store = EventStore(self.db_conn)
        self.read_model_repository = AsyncMock()
        self.service = EventSourcingService(self.event_store, self.read_model_repository)
        
        # Mock the replay service
        self.service.replay_service._update_order_read_model = AsyncMock()
        self.service.replay_service._update_portfolio_read_model = AsyncMock()
    
    async def test_place_order(self):
        """Test placing an order through the service"""
        await self.setup_test_environment()
        
        # Mock event store operations
        self.event_store.append_events = AsyncMock(return_value=True)
        
        result = await self.service.place_order(
            order_id="test_order_1",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            price=None,
            user_id="user1",
            account_id="acc1"
        )
        
        assert result == True
        self.event_store.append_events.assert_called_once()
    
    async def test_fill_order(self):
        """Test filling an order through the service"""
        await self.setup_test_environment()
        
        # Mock loading order
        mock_order = OrderAggregate("test_order_1")
        mock_order.place_order("AAPL", "buy", 100, "market", None, "user1", "acc1")
        self.service._load_order = AsyncMock(return_value=mock_order)
        
        # Mock event store operations
        self.event_store.append_events = AsyncMock(return_value=True)
        
        result = await self.service.fill_order("test_order_1", 50, 150.0)
        
        assert result == True
        assert mock_order.filled_quantity == 50
        assert mock_order.average_fill_price == 150.0
    
    async def test_update_portfolio(self):
        """Test updating portfolio through the service"""
        await self.setup_test_environment()
        
        # Mock event store operations
        self.event_store.append_events = AsyncMock(return_value=True)
        
        result = await self.service.update_portfolio(
            portfolio_id="test_portfolio_1",
            user_id="user1",
            account_id="acc1",
            name="Test Portfolio",
            cash_balance=10000.0
        )
        
        assert result == True
        self.event_store.append_events.assert_called_once()
    
    async def test_load_order(self):
        """Test loading order from event history"""
        await self.setup_test_environment()
        
        # Mock event store
        mock_events = [
            OrderCreatedEvent(
                order_id="test_order_1",
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="market",
                price=None,
                user_id="user1",
                account_id="acc1"
            )
        ]
        self.event_store.get_events = AsyncMock(return_value=mock_events)
        
        order = await self.service._load_order("test_order_1")
        
        assert order is not None
        assert order.aggregate_id == "test_order_1"
        assert order.symbol == "AAPL"
        assert order.quantity == 100
