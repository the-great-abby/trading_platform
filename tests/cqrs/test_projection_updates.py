"""
Tests for Projection Update System
"""

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from src.services.cqrs.projection_update_service import ProjectionUpdateService
from src.services.cqrs.event_subscription_service import EventSubscriptionService
from src.services.cqrs.cqrs_service import CQRSService
from src.services.cqrs.events import (
    OrderCreatedEvent, OrderFilledEvent, OrderCancelledEvent,
    PortfolioUpdatedEvent, PositionOpenedEvent, PositionClosedEvent
)


@pytest.mark.asyncio
class TestProjectionUpdateService:
    """Test projection update service functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.db_conn = AsyncMock()
        self.event_store = AsyncMock()
        self.read_model_repository = AsyncMock()
        self.service = ProjectionUpdateService(self.event_store, self.read_model_repository)
    
    async def test_handle_order_created(self):
        """Test handling order created event"""
        await self.setup_test_environment()
        
        event = OrderCreatedEvent(
            order_id="test_order_1",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            price=None,
            user_id="user1",
            account_id="acc1"
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        self.read_model_repository.upsert_order.assert_called_once()
        
        # Check the order read model that was created
        call_args = self.read_model_repository.upsert_order.call_args[0][0]
        assert call_args.order_id == "test_order_1"
        assert call_args.symbol == "AAPL"
        assert call_args.side == "buy"
        assert call_args.quantity == 100
        assert call_args.status == "pending"
    
    async def test_handle_order_filled(self):
        """Test handling order filled event"""
        await self.setup_test_environment()
        
        # Mock existing order
        existing_order = Mock()
        existing_order.filled_quantity = 0
        existing_order.average_fill_price = None
        existing_order.quantity = 100
        existing_order.status = "pending"
        existing_order.filled_at = None
        
        self.read_model_repository.get_order.return_value = existing_order
        
        event = OrderFilledEvent(
            order_id="test_order_1",
            filled_quantity=50,
            fill_price=Decimal("150.0"),
            remaining_quantity=50
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        assert existing_order.filled_quantity == 50
        assert existing_order.average_fill_price == Decimal("150.0")
        assert existing_order.status == "partially_filled"
        self.read_model_repository.upsert_order.assert_called_once_with(existing_order)
    
    async def test_handle_order_cancelled(self):
        """Test handling order cancelled event"""
        await self.setup_test_environment()
        
        # Mock existing order
        existing_order = Mock()
        existing_order.status = "pending"
        existing_order.cancelled_at = None
        
        self.read_model_repository.get_order.return_value = existing_order
        
        event = OrderCancelledEvent(
            order_id="test_order_1",
            reason="User requested",
            cancelled_quantity=100
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        assert existing_order.status == "cancelled"
        assert existing_order.cancelled_at == event.timestamp
        self.read_model_repository.upsert_order.assert_called_once_with(existing_order)
    
    async def test_handle_portfolio_updated(self):
        """Test handling portfolio updated event"""
        await self.setup_test_environment()
        
        event = PortfolioUpdatedEvent(
            portfolio_id="test_portfolio_1",
            user_id="user1",
            account_id="acc1",
            name="Test Portfolio",
            cash_balance=Decimal("10000.0"),
            total_value=Decimal("10000.0")
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        self.read_model_repository.upsert_portfolio.assert_called_once()
        
        # Check the portfolio read model that was created
        call_args = self.read_model_repository.upsert_portfolio.call_args[0][0]
        assert call_args.portfolio_id == "test_portfolio_1"
        assert call_args.user_id == "user1"
        assert call_args.account_id == "acc1"
        assert call_args.name == "Test Portfolio"
        assert call_args.cash_balance == Decimal("10000.0")
    
    async def test_handle_position_opened(self):
        """Test handling position opened event"""
        await self.setup_test_environment()
        
        # Mock no existing position
        self.read_model_repository.get_position.return_value = None
        
        event = PositionOpenedEvent(
            portfolio_id="test_portfolio_1",
            symbol="AAPL",
            quantity=100,
            price=Decimal("150.0"),
            market_value=Decimal("15000.0")
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        self.read_model_repository.upsert_position.assert_called_once()
        
        # Check the position read model that was created
        call_args = self.read_model_repository.upsert_position.call_args[0][0]
        assert call_args.portfolio_id == "test_portfolio_1"
        assert call_args.symbol == "AAPL"
        assert call_args.quantity == 100
        assert call_args.average_price == Decimal("150.0")
    
    async def test_handle_position_closed(self):
        """Test handling position closed event"""
        await self.setup_test_environment()
        
        # Mock existing position
        existing_position = Mock()
        existing_position.quantity = 100
        existing_position.cost_basis = Decimal("15000.0")
        existing_position.average_price = Decimal("150.0")
        
        self.read_model_repository.get_position.return_value = existing_position
        
        event = PositionClosedEvent(
            portfolio_id="test_portfolio_1",
            symbol="AAPL",
            quantity=50,
            price=Decimal("160.0"),
            market_value=Decimal("8000.0")
        )
        
        result = await self.service.process_event(event)
        
        assert result == True
        assert existing_position.quantity == 50
        self.read_model_repository.upsert_position.assert_called_once_with(existing_position)
    
    async def test_process_events_batch(self):
        """Test processing a batch of events"""
        await self.setup_test_environment()
        
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
            PortfolioUpdatedEvent(
                portfolio_id="test_portfolio_1",
                user_id="user1",
                account_id="acc1",
                name="Test Portfolio",
                cash_balance=Decimal("10000.0"),
                total_value=Decimal("10000.0")
            )
        ]
        
        results = await self.service.process_events_batch(events)
        
        assert results["processed"] == 2
        assert results["failed"] == 0
        assert results["skipped"] == 0
        assert self.read_model_repository.upsert_order.call_count == 1
        assert self.read_model_repository.upsert_portfolio.call_count == 1


@pytest.mark.asyncio
class TestEventSubscriptionService:
    """Test event subscription service functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.db_conn = AsyncMock()
        self.event_store = AsyncMock()
        self.read_model_repository = AsyncMock()
        self.projection_update_service = ProjectionUpdateService(self.event_store, self.read_model_repository)
        self.service = EventSubscriptionService(self.event_store, self.projection_update_service)
    
    async def test_subscribe_to_event_type(self):
        """Test subscribing to an event type"""
        await self.setup_test_environment()
        
        handler = Mock()
        self.service.subscribe_to_event_type("OrderCreatedEvent", handler)
        
        assert "OrderCreatedEvent" in self.service._subscriptions
        assert handler in self.service._subscriptions["OrderCreatedEvent"]
    
    async def test_unsubscribe_from_event_type(self):
        """Test unsubscribing from an event type"""
        await self.setup_test_environment()
        
        handler = Mock()
        self.service.subscribe_to_event_type("OrderCreatedEvent", handler)
        self.service.unsubscribe_from_event_type("OrderCreatedEvent", handler)
        
        assert "OrderCreatedEvent" not in self.service._subscriptions or handler not in self.service._subscriptions["OrderCreatedEvent"]
    
    async def test_process_event_immediately(self):
        """Test processing an event immediately"""
        await self.setup_test_environment()
        
        # Mock projection update service
        self.projection_update_service.process_event = AsyncMock(return_value=True)
        
        event = OrderCreatedEvent(
            order_id="test_order_1",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            price=None,
            user_id="user1",
            account_id="acc1"
        )
        
        result = await self.service.process_event_immediately(event)
        
        assert result == True
        self.projection_update_service.process_event.assert_called_once_with(event)
    
    async def test_get_subscription_status(self):
        """Test getting subscription status"""
        await self.setup_test_environment()
        
        status = await self.service.get_subscription_status()
        
        assert "is_running" in status
        assert "last_processed_timestamp" in status
        assert "subscription_count" in status
        assert "subscribed_event_types" in status


@pytest.mark.asyncio
class TestCQRSService:
    """Test main CQRS service functionality"""
    
    async def setup_test_environment(self):
        """Setup test environment"""
        self.db_conn = AsyncMock()
        self.redis_client = AsyncMock()
        self.service = CQRSService(self.db_conn, self.redis_client)
    
    async def test_initialize(self):
        """Test CQRS service initialization"""
        await self.setup_test_environment()
        
        # Mock the initialization methods
        self.service.event_store.create_tables = AsyncMock()
        self.service.read_model_repository.create_tables = AsyncMock()
        self.service.start_event_subscription = AsyncMock()
        
        result = await self.service.initialize()
        
        assert result == True
        self.service.event_store.create_tables.assert_called_once()
        self.service.read_model_repository.create_tables.assert_called_once()
        self.service.start_event_subscription.assert_called_once()
    
    async def test_place_order(self):
        """Test placing an order through CQRS service"""
        await self.setup_test_environment()
        
        # Mock the event sourcing service
        self.service.event_sourcing_service.place_order = AsyncMock(return_value=True)
        
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
        self.service.event_sourcing_service.place_order.assert_called_once()
    
    async def test_get_portfolio(self):
        """Test getting portfolio through CQRS service"""
        await self.setup_test_environment()
        
        # Mock the query execution
        self.service.execute_query = AsyncMock(return_value={
            "success": True,
            "data": {"portfolio_id": "test_portfolio_1", "name": "Test Portfolio"}
        })
        
        result = await self.service.get_portfolio(portfolio_id="test_portfolio_1")
        
        assert result["success"] == True
        assert "data" in result
        self.service.execute_query.assert_called_once()
    
    async def test_get_service_status(self):
        """Test getting service status"""
        await self.setup_test_environment()
        
        # Mock the subscription service status
        self.service.event_subscription_service.get_subscription_status = AsyncMock(return_value={
            "is_running": True,
            "last_processed_timestamp": datetime.utcnow(),
            "subscription_count": 0,
            "subscribed_event_types": []
        })
        
        status = await self.service.get_service_status()
        
        assert "service_status" in status
        assert "event_subscription" in status
        assert "command_handlers" in status
        assert "query_handlers" in status
        assert status["command_handlers"] > 0
        assert status["query_handlers"] > 0
