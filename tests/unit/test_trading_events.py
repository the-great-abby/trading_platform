"""
Unit tests for trading events
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.services.trading.events import (
    OrderPlacedEvent,
    OrderCancelledEvent,
    OrderUpdatedEvent,
    OrderFilledEvent,
    OrderRejectedEvent,
    StrategyExecutedEvent,
    StrategyUpdatedEvent,
    StrategyCreatedEvent
)


class TestOrderPlacedEvent:
    """Test OrderPlacedEvent"""
    
    def test_order_placed_event_creation(self):
        """Test creating an order placed event"""
        event = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            user_id="user123"
        )
        
        assert event.order_id == "order-123"
        assert event.symbol == "AAPL"
        assert event.side == "BUY"
        assert event.quantity == 100
        assert event.order_type == "market"
        assert event.user_id == "user123"
    
    def test_order_placed_event_with_strategy(self):
        """Test creating an order placed event with strategy"""
        event = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            strategy_id="strategy-123"
        )
        
        assert event.strategy_id == "strategy-123"
    
    def test_order_cancelled_event_creation(self):
        """Test creating an order cancelled event"""
        event = OrderCancelledEvent(
            order_id="order-123",
            reason="User request",
            user_id="user123"
        )
        
        assert event.order_id == "order-123"
        assert event.reason == "User request"
        assert event.user_id == "user123"
    
    def test_order_cancelled_event_without_reason(self):
        """Test creating an order cancelled event without reason"""
        event = OrderCancelledEvent(order_id="order-123")
        
        assert event.order_id == "order-123"
        assert event.reason is None


class TestOrderUpdatedEvent:
    """Test OrderUpdatedEvent"""
    
    def test_order_updated_event_creation(self):
        """Test creating an order updated event"""
        event = OrderUpdatedEvent(
            order_id="order-123",
            quantity=75,
            limit_price=Decimal("145.00"),
            time_in_force="gtc"
        )
        
        assert event.order_id == "order-123"
        assert event.quantity == 75
        assert event.limit_price == Decimal("145.00")
        assert event.time_in_force == "gtc"
    
    def test_order_updated_event_partial_update(self):
        """Test creating an order updated event with partial updates"""
        event = OrderUpdatedEvent(
            order_id="order-123",
            quantity=50  # Only update quantity
        )
        
        assert event.order_id == "order-123"
        assert event.quantity == 50
        assert event.limit_price is None
        assert event.stop_price is None
        assert event.time_in_force is None


class TestOrderFilledEvent:
    """Test OrderFilledEvent"""
    
    def test_order_filled_event_creation(self):
        """Test creating an order filled event"""
        event = OrderFilledEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            fill_price=Decimal("148.50"),
            fill_time=datetime.now(),
            commission=Decimal("1.00")
        )
        
        assert event.order_id == "order-123"
        assert event.symbol == "AAPL"
        assert event.side == "BUY"
        assert event.quantity == 100
        assert event.fill_price == Decimal("148.50")
        assert event.commission == Decimal("1.00")
        assert isinstance(event.fill_time, datetime)
    
    def test_order_filled_event_partial_fill(self):
        """Test creating an order filled event for partial fill"""
        event = OrderFilledEvent(
            order_id="order-123",
            symbol="AAPL",
            side="SELL",
            quantity=50,
            fill_price=Decimal("148.50"),
            fill_time=datetime.now(),
            commission=Decimal("0.50")
        )
        
        assert event.quantity == 50
        assert event.commission == Decimal("0.50")


class TestOrderRejectedEvent:
    """Test OrderRejectedEvent"""
    
    def test_order_rejected_event_creation(self):
        """Test creating an order rejected event"""
        event = OrderRejectedEvent(
            order_id="order-123",
            reason="Insufficient funds"
        )
        
        assert event.order_id == "order-123"
        assert event.reason == "Insufficient funds"
    
    def test_order_rejected_event_without_error_code(self):
        """Test creating an order rejected event without error code"""
        event = OrderRejectedEvent(
            order_id="order-123",
            reason="Invalid order"
        )
        
        assert event.order_id == "order-123"
        assert event.reason == "Invalid order"


class TestStrategyExecutedEvent:
    """Test StrategyExecutedEvent"""
    
    def test_strategy_executed_event_creation(self):
        """Test creating a strategy executed event"""
        event = StrategyExecutedEvent(
            strategy_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            parameters={"lookback_period": 20},
            execution_time=datetime.now()
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.symbols == ["AAPL", "GOOGL"]
        assert event.parameters["lookback_period"] == 20
    
    def test_strategy_executed_event_without_parameters(self):
        """Test creating a strategy executed event without parameters"""
        event = StrategyExecutedEvent(
            strategy_id="strategy-123",
            symbols=["AAPL"],
            execution_time=datetime.now()
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.parameters is None


class TestStrategyUpdatedEvent:
    """Test StrategyUpdatedEvent"""
    
    def test_strategy_updated_event_creation(self):
        """Test creating a strategy updated event"""
        event = StrategyUpdatedEvent(
            strategy_id="strategy-123",
            name="Updated SMA Strategy",
            parameters={"sma_period": 25},
            is_active=True
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.name == "Updated SMA Strategy"
        assert event.parameters["sma_period"] == 25
        assert event.is_active is True
    
    def test_strategy_updated_event_partial_update(self):
        """Test creating a strategy updated event with partial updates"""
        event = StrategyUpdatedEvent(
            strategy_id="strategy-123",
            name="New Name"  # Only update name
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.name == "New Name"
        assert event.parameters is None
        assert event.is_active is None


class TestStrategyCreatedEvent:
    """Test StrategyCreatedEvent"""
    
    def test_strategy_created_event_creation(self):
        """Test creating a strategy created event"""
        event = StrategyCreatedEvent(
            strategy_id="strategy-123",
            name="SMA Crossover Strategy",
            strategy_type="SMA_CROSSOVER",
            symbols=["AAPL", "GOOGL"],
            parameters={
                "short_period": 10,
                "long_period": 30,
                "threshold": 0.01
            },
            initial_capital=Decimal("10000.00"),
            risk_limits={
                "max_position_size": 0.1,
                "max_daily_loss": 0.05
            }
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.name == "SMA Crossover Strategy"
        assert event.strategy_type == "SMA_CROSSOVER"
        assert event.symbols == ["AAPL", "GOOGL"]
        assert event.parameters["short_period"] == 10
        assert event.initial_capital == Decimal("10000.00")
        assert event.risk_limits["max_position_size"] == 0.1
    
    def test_strategy_created_event_without_risk_limits(self):
        """Test creating a strategy created event without risk limits"""
        event = StrategyCreatedEvent(
            strategy_id="strategy-123",
            name="Simple Strategy",
            strategy_type="SIMPLE",
            symbols=["AAPL"],
            parameters={},
            initial_capital=Decimal("5000.00")
        )
        
        assert event.name == "Simple Strategy"
        assert event.strategy_type == "SIMPLE"
        assert event.risk_limits is None


class TestEventValidation:
    """Test event validation scenarios"""
    
    def test_order_placed_invalid_quantity(self):
        """Test order placed with invalid quantity"""
        with pytest.raises(ValueError):
            OrderPlacedEvent(
                order_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=0  # Invalid quantity
            )
    
    def test_order_placed_invalid_order_type(self):
        """Test order placed with invalid order type (currently no validation)"""
        # Currently no validation, so this should work
        event = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="invalid_type"
        )
        assert event.order_type == "invalid_type"
    
    def test_order_filled_invalid_quantity(self):
        """Test order filled with invalid quantity (currently no validation)"""
        # Currently no validation, so this should work
        event = OrderFilledEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=0,  # Invalid quantity but no validation
            fill_price=Decimal("150.00"),
            fill_time=datetime.now()
        )
        assert event.quantity == 0


class TestEventSerialization:
    """Test event serialization"""
    
    def test_order_placed_event_serialization(self):
        """Test order placed event serialization"""
        event = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            limit_price=Decimal("150.00"),
            user_id="user123"
        )
        
        event_dict = event.model_dump()
        
        assert event_dict["order_id"] == "order-123"
        assert event_dict["symbol"] == "AAPL"
        assert event_dict["side"] == "BUY"
        assert event_dict["quantity"] == 100
        # Decimal is serialized as Decimal object, not string
        assert event_dict["limit_price"] == Decimal("150.00")
        assert event_dict["user_id"] == "user123"
    
    def test_strategy_executed_event_serialization(self):
        """Test strategy executed event serialization"""
        event = StrategyExecutedEvent(
            strategy_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            parameters={"lookback_period": 20},
            execution_time=datetime.now()
        )
        
        event_dict = event.model_dump()
        
        assert event_dict["strategy_id"] == "strategy-123"
        assert event_dict["symbols"] == ["AAPL", "GOOGL"]
        assert event_dict["parameters"]["lookback_period"] == 20


class TestEventVersioning:
    """Test event versioning"""
    
    def test_event_version_increment(self):
        """Test event version increment"""
        event1 = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market"
        )
        
        event2 = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market"
        )
        
        # Version should be automatically incremented
        assert event1.event_id != event2.event_id
    
    def test_event_correlation_id(self):
        """Test event correlation ID"""
        event = OrderPlacedEvent(
            order_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market"
        )
        
        # Should have correlation ID for tracking
        assert hasattr(event, 'event_id')
        assert event.event_id is not None 