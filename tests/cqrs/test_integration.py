"""
Integration tests for CQRS system
Tests the complete flow from commands to queries
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any

from tests.cqrs.test_base import IntegrationTestBase
from src.services.cqrs.commands import PlaceOrderCommand, UpdatePortfolioCommand
from src.services.cqrs.queries import GetPortfolioQuery, GetMarketDataQuery
from src.services.cqrs.command_handlers import PlaceOrderHandler, UpdatePortfolioHandler
from src.services.cqrs.query_handlers import GetPortfolioHandler, GetMarketDataHandler
from src.services.cqrs.events import OrderCreatedEvent, OrderFilledEvent, PortfolioUpdatedEvent

@pytest.mark.asyncio
class TestCQRSIntegration(IntegrationTestBase):
    """Test complete CQRS flow integration"""
    
    async def _setup_test_data(self):
        """Setup test data for integration tests"""
        # Setup initial portfolio
        await self.setup_test_portfolio("user1", "acc1", {"AAPL": 100, "MSFT": 50})
        
        # Setup market data
        await self.setup_test_market_data("AAPL", 150.00, 1000000)
        await self.setup_test_market_data("MSFT", 300.00, 500000)
        
        # Register handlers
        self.command_bus.register_handler(PlaceOrderCommand, PlaceOrderHandler(self.db_conn, self.event_bus))
        self.command_bus.register_handler(UpdatePortfolioCommand, UpdatePortfolioHandler(self.db_conn, self.event_bus))
        self.query_bus.register_handler(GetPortfolioQuery, GetPortfolioHandler(self.db_conn))
        self.query_bus.register_handler(GetMarketDataQuery, GetMarketDataHandler(self.db_conn))
    
    async def test_complete_trading_flow(self):
        """Test complete trading flow from order to portfolio update"""
        # 1. Place an order
        place_command = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=50,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        order_result = await self.execute_command(place_command)
        assert order_result is not None
        assert order_result.status == "placed"
        
        # 2. Verify order event was published
        order_events = await self.get_events("OrderPlacedEvent")
        assert len(order_events) == 1
        assert order_events[0]['event_data']['symbol'] == "AAPL"
        
        # 3. Simulate order fill
        fill_command = UpdatePortfolioCommand(
            user_id="user1",
            account_id="acc1",
            symbol="AAPL",
            quantity_change=50,
            price=150.25  # Slightly higher than market price
        )
        
        fill_result = await self.execute_command(fill_command)
        assert fill_result is not None
        assert fill_result.success is True
        
        # 4. Verify portfolio was updated
        portfolio_query = GetPortfolioQuery(user_id="user1", account_id="acc1")
        portfolio_result = await self.execute_query(portfolio_query)
        
        assert portfolio_result is not None
        aapl_position = next((p for p in portfolio_result.positions if p.symbol == "AAPL"), None)
        assert aapl_position is not None
        assert aapl_position.quantity == 150  # 100 + 50
        
        # 5. Verify events were published
        fill_events = await self.get_events("OrderFilledEvent")
        assert len(fill_events) == 1
        
        portfolio_events = await self.get_events("PortfolioUpdatedEvent")
        assert len(portfolio_events) == 1
    
    async def test_multiple_orders_flow(self):
        """Test multiple orders affecting the same portfolio"""
        # Place multiple orders
        orders = [
            PlaceOrderCommand(symbol="AAPL", side="BUY", quantity=25, order_type="market", user_id="user1", account_id="acc1"),
            PlaceOrderCommand(symbol="MSFT", side="SELL", quantity=10, order_type="market", user_id="user1", account_id="acc1"),
            PlaceOrderCommand(symbol="AAPL", side="BUY", quantity=15, order_type="market", user_id="user1", account_id="acc1")
        ]
        
        for command in orders:
            result = await self.execute_command(command)
            assert result is not None
        
        # Verify all order events were published
        order_events = await self.get_events("OrderPlacedEvent")
        assert len(order_events) == 3
        
        # Simulate all orders being filled
        fills = [
            UpdatePortfolioCommand(user_id="user1", account_id="acc1", symbol="AAPL", quantity_change=25, price=150.00),
            UpdatePortfolioCommand(user_id="user1", account_id="acc1", symbol="MSFT", quantity_change=-10, price=300.00),
            UpdatePortfolioCommand(user_id="user1", account_id="acc1", symbol="AAPL", quantity_change=15, price=150.50)
        ]
        
        for command in fills:
            result = await self.execute_command(command)
            assert result is not None
        
        # Verify final portfolio state
        portfolio_query = GetPortfolioQuery(user_id="user1", account_id="acc1")
        portfolio_result = await self.execute_query(portfolio_query)
        
        assert portfolio_result is not None
        
        # Check AAPL position (100 + 25 + 15 = 140)
        aapl_position = next((p for p in portfolio_result.positions if p.symbol == "AAPL"), None)
        assert aapl_position is not None
        assert aapl_position.quantity == 140
        
        # Check MSFT position (50 - 10 = 40)
        msft_position = next((p for p in portfolio_result.positions if p.symbol == "MSFT"), None)
        assert msft_position is not None
        assert msft_position.quantity == 40
    
    async def test_event_ordering(self):
        """Test that events are published in correct order"""
        # Place an order
        place_command = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=50,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        await self.execute_command(place_command)
        
        # Fill the order
        fill_command = UpdatePortfolioCommand(
            user_id="user1",
            account_id="acc1",
            symbol="AAPL",
            quantity_change=50,
            price=150.00
        )
        
        await self.execute_command(fill_command)
        
        # Get all events and verify ordering
        all_events = await self.get_events()
        
        # Find order and fill events
        order_event = next((e for e in all_events if e['event_type'] == "OrderPlacedEvent"), None)
        fill_event = next((e for e in all_events if e['event_type'] == "OrderFilledEvent"), None)
        portfolio_event = next((e for e in all_events if e['event_type'] == "PortfolioUpdatedEvent"), None)
        
        assert order_event is not None
        assert fill_event is not None
        assert portfolio_event is not None
        
        # Verify event ordering
        assert order_event['timestamp'] <= fill_event['timestamp']
        assert fill_event['timestamp'] <= portfolio_event['timestamp']
    
    async def test_concurrent_operations(self):
        """Test concurrent command and query operations"""
        import asyncio
        
        # Define concurrent operations
        async def place_order(symbol: str, quantity: int):
            command = PlaceOrderCommand(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
            return await self.execute_command(command)
        
        async def query_portfolio():
            query = GetPortfolioQuery(user_id="user1", account_id="acc1")
            return await self.execute_query(query)
        
        # Execute concurrent operations
        tasks = [
            place_order("AAPL", 25),
            place_order("MSFT", 30),
            query_portfolio(),
            place_order("GOOGL", 10),
            query_portfolio()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
        
        # Verify events were published
        order_events = await self.get_events("OrderPlacedEvent")
        assert len(order_events) == 3  # 3 orders placed
    
    async def test_error_recovery(self):
        """Test system recovery from errors"""
        # Place an order
        place_command = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=50,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        order_result = await self.execute_command(place_command)
        assert order_result is not None
        
        # Simulate a failed fill (insufficient quantity)
        with pytest.raises(ValueError):
            fill_command = UpdatePortfolioCommand(
                user_id="user1",
                account_id="acc1",
                symbol="AAPL",
                quantity_change=200,  # More than available
                price=150.00
            )
            await self.execute_command(fill_command)
        
        # Verify portfolio state is unchanged
        portfolio_query = GetPortfolioQuery(user_id="user1", account_id="acc1")
        portfolio_result = await self.execute_query(portfolio_query)
        
        aapl_position = next((p for p in portfolio_result.positions if p.symbol == "AAPL"), None)
        assert aapl_position is not None
        assert aapl_position.quantity == 100  # Original quantity unchanged
        
        # Verify no fill events were published
        fill_events = await self.get_events("OrderFilledEvent")
        assert len(fill_events) == 0
    
    async def test_data_consistency(self):
        """Test data consistency across commands and queries"""
        # Initial portfolio state
        initial_portfolio = await self.execute_query(GetPortfolioQuery(user_id="user1", account_id="acc1"))
        initial_aapl_quantity = next((p.quantity for p in initial_portfolio.positions if p.symbol == "AAPL"), 0)
        
        # Place and fill order
        place_command = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=50,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        order_result = await self.execute_command(place_command)
        
        fill_command = UpdatePortfolioCommand(
            user_id="user1",
            account_id="acc1",
            symbol="AAPL",
            quantity_change=50,
            price=150.00
        )
        
        fill_result = await self.execute_command(fill_command)
        
        # Verify final portfolio state
        final_portfolio = await self.execute_query(GetPortfolioQuery(user_id="user1", account_id="acc1"))
        final_aapl_quantity = next((p.quantity for p in final_portfolio.positions if p.symbol == "AAPL"), 0)
        
        # Quantity should have increased by 50
        assert final_aapl_quantity == initial_aapl_quantity + 50
        
        # Verify total value calculation
        assert final_portfolio.total_value > initial_portfolio.total_value
        
        # Verify events contain consistent data
        order_events = await self.get_events("OrderPlacedEvent")
        fill_events = await self.get_events("OrderFilledEvent")
        
        assert len(order_events) == 1
        assert len(fill_events) == 1
        
        assert order_events[0]['event_data']['symbol'] == "AAPL"
        assert order_events[0]['event_data']['quantity'] == 50
        assert fill_events[0]['event_data']['symbol'] == "AAPL"
        assert fill_events[0]['event_data']['quantity'] == 50
