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
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            user_id="user123"
        )
        
        assert event.aggregate_id == "order-123"
        assert event.symbol == "AAPL"
        assert event.side == "BUY"
        assert event.quantity == 100
        assert event.order_type == "market"
        assert event.user_id == "user123"
        assert event.status == "pending"
    
    def test_order_placed_event_with_limit_price(self):
        """Test creating an order placed event with limit price"""
        event = OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="SELL",
            quantity=50,
            order_type="limit",
            limit_price=Decimal("150.00")
        )
        
        assert event.order_type == "limit"
        assert event.limit_price == Decimal("150.00")
        assert event.side == "SELL"
    
    def test_order_placed_event_with_strategy(self):
        """Test creating an order placed event with strategy"""
        event = OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            strategy_id="strategy-123",
            metadata={"signal": "SMA crossover"}
        )
        
        assert event.strategy_id == "strategy-123"
        assert event.metadata["signal"] == "SMA crossover"


class TestOrderCancelledEvent:
    """Test OrderCancelledEvent"""
    
    def test_order_cancelled_event_creation(self):
        """Test creating an order cancelled event"""
        event = OrderCancelledEvent(
            aggregate_id="order-123",
            reason="User request",
            user_id="user123"
        )
        
        assert event.aggregate_id == "order-123"
        assert event.reason == "User request"
        assert event.user_id == "user123"
        assert event.status == "cancelled"
    
    def test_order_cancelled_event_without_reason(self):
        """Test creating an order cancelled event without reason"""
        event = OrderCancelledEvent(aggregate_id="order-123")
        
        assert event.aggregate_id == "order-123"
        assert event.reason is None


class TestOrderUpdatedEvent:
    """Test OrderUpdatedEvent"""
    
    def test_order_updated_event_creation(self):
        """Test creating an order updated event"""
        event = OrderUpdatedEvent(
            aggregate_id="order-123",
            quantity=75,
            limit_price=Decimal("145.00"),
            time_in_force="gtc"
        )
        
        assert event.aggregate_id == "order-123"
        assert event.quantity == 75
        assert event.limit_price == Decimal("145.00")
        assert event.time_in_force == "gtc"
        assert event.status == "updated"
    
    def test_order_updated_event_partial_update(self):
        """Test creating an order updated event with partial updates"""
        event = OrderUpdatedEvent(
            aggregate_id="order-123",
            quantity=50  # Only update quantity
        )
        
        assert event.aggregate_id == "order-123"
        assert event.quantity == 50
        assert event.limit_price is None
        assert event.stop_price is None
        assert event.time_in_force is None


class TestOrderFilledEvent:
    """Test OrderFilledEvent"""
    
    def test_order_filled_event_creation(self):
        """Test creating an order filled event"""
        event = OrderFilledEvent(
            aggregate_id="order-123",
            filled_quantity=100,
            fill_price=Decimal("148.50"),
            commission=Decimal("1.00"),
            timestamp=datetime.now()
        )
        
        assert event.aggregate_id == "order-123"
        assert event.filled_quantity == 100
        assert event.fill_price == Decimal("148.50")
        assert event.commission == Decimal("1.00")
        assert event.status == "filled"
        assert isinstance(event.timestamp, datetime)
    
    def test_order_filled_event_partial_fill(self):
        """Test creating an order filled event for partial fill"""
        event = OrderFilledEvent(
            aggregate_id="order-123",
            filled_quantity=50,
            fill_price=Decimal("148.50"),
            commission=Decimal("0.50")
        )
        
        assert event.filled_quantity == 50
        assert event.commission == Decimal("0.50")


class TestOrderRejectedEvent:
    """Test OrderRejectedEvent"""
    
    def test_order_rejected_event_creation(self):
        """Test creating an order rejected event"""
        event = OrderRejectedEvent(
            aggregate_id="order-123",
            reason="Insufficient funds",
            error_code="INSUFFICIENT_FUNDS"
        )
        
        assert event.aggregate_id == "order-123"
        assert event.reason == "Insufficient funds"
        assert event.error_code == "INSUFFICIENT_FUNDS"
        assert event.status == "rejected"
    
    def test_order_rejected_event_without_error_code(self):
        """Test creating an order rejected event without error code"""
        event = OrderRejectedEvent(
            aggregate_id="order-123",
            reason="Invalid order"
        )
        
        assert event.aggregate_id == "order-123"
        assert event.reason == "Invalid order"
        assert event.error_code is None


class TestStrategyExecutedEvent:
    """Test StrategyExecutedEvent"""
    
    def test_strategy_executed_event_creation(self):
        """Test creating a strategy executed event"""
        event = StrategyExecutedEvent(
            aggregate_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            signals={
                "AAPL": {"action": "BUY", "confidence": 0.8},
                "GOOGL": {"action": "HOLD", "confidence": 0.6}
            },
            parameters={"lookback_period": 20}
        )
        
        assert event.aggregate_id == "strategy-123"
        assert event.symbols == ["AAPL", "GOOGL"]
        assert event.signals["AAPL"]["action"] == "BUY"
        assert event.signals["GOOGL"]["action"] == "HOLD"
        assert event.parameters["lookback_period"] == 20
    
    def test_strategy_executed_event_without_parameters(self):
        """Test creating a strategy executed event without parameters"""
        event = StrategyExecutedEvent(
            aggregate_id="strategy-123",
            symbols=["AAPL"],
            signals={"AAPL": {"action": "SELL", "confidence": 0.9}}
        )
        
        assert event.aggregate_id == "strategy-123"
        assert event.parameters is None


class TestStrategyUpdatedEvent:
    """Test StrategyUpdatedEvent"""
    
    def test_strategy_updated_event_creation(self):
        """Test creating a strategy updated event"""
        event = StrategyUpdatedEvent(
            aggregate_id="strategy-123",
            name="Updated SMA Strategy",
            parameters={"lookback_period": 30},
            is_active=False
        )
        
        assert event.aggregate_id == "strategy-123"
        assert event.name == "Updated SMA Strategy"
        assert event.parameters["lookback_period"] == 30
        assert event.is_active is False
    
    def test_strategy_updated_event_partial_update(self):
        """Test creating a strategy updated event with partial updates"""
        event = StrategyUpdatedEvent(
            aggregate_id="strategy-123",
            is_active=True  # Only update active status
        )
        
        assert event.aggregate_id == "strategy-123"
        assert event.is_active is True
        assert event.name is None
        assert event.parameters is None


class TestStrategyCreatedEvent:
    """Test StrategyCreatedEvent"""
    
    def test_strategy_created_event_creation(self):
        """Test creating a strategy created event"""
        event = StrategyCreatedEvent(
            aggregate_id="strategy-123",
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
        
        assert event.aggregate_id == "strategy-123"
        assert event.name == "SMA Crossover Strategy"
        assert event.strategy_type == "SMA_CROSSOVER"
        assert event.symbols == ["AAPL", "GOOGL"]
        assert event.parameters["short_period"] == 10
        assert event.initial_capital == Decimal("10000.00")
        assert event.risk_limits["max_position_size"] == 0.1
    
    def test_strategy_created_event_without_risk_limits(self):
        """Test creating a strategy created event without risk limits"""
        event = StrategyCreatedEvent(
            aggregate_id="strategy-123",
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
                aggregate_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=0  # Invalid quantity
            )
    
    def test_order_placed_invalid_order_type(self):
        """Test order placed with invalid order type"""
        with pytest.raises(ValueError):
            OrderPlacedEvent(
                aggregate_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=100,
                order_type="invalid_type"
            )
    
    def test_order_filled_invalid_quantity(self):
        """Test order filled with invalid quantity"""
        with pytest.raises(ValueError):
            OrderFilledEvent(
                aggregate_id="order-123",
                filled_quantity=0,  # Invalid quantity
                fill_price=Decimal("150.00")
            )


class TestEventSerialization:
    """Test event serialization"""
    
    def test_order_placed_event_serialization(self):
        """Test order placed event serialization"""
        event = OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            limit_price=Decimal("150.00"),
            user_id="user123"
        )
        
        event_dict = event.dict()
        
        assert event_dict["aggregate_id"] == "order-123"
        assert event_dict["symbol"] == "AAPL"
        assert event_dict["side"] == "BUY"
        assert event_dict["quantity"] == 100
        assert event_dict["limit_price"] == "150.00"  # Decimal serialized as string
        assert event_dict["user_id"] == "user123"
        assert "event_id" in event_dict
        assert "timestamp" in event_dict
        assert "version" in event_dict
    
    def test_strategy_executed_event_serialization(self):
        """Test strategy executed event serialization"""
        event = StrategyExecutedEvent(
            aggregate_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            signals={"AAPL": {"action": "BUY"}},
            parameters={"param1": "value1"}
        )
        
        event_dict = event.dict()
        
        assert event_dict["aggregate_id"] == "strategy-123"
        assert event_dict["symbols"] == ["AAPL", "GOOGL"]
        assert event_dict["signals"]["AAPL"]["action"] == "BUY"
        assert event_dict["parameters"]["param1"] == "value1"


class TestEventVersioning:
    """Test event versioning"""
    
    def test_event_version_increment(self):
        """Test that event version increments correctly"""
        event1 = OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100
        )
        
        event2 = OrderUpdatedEvent(
            aggregate_id="order-123",
            quantity=75,
            version=2
        )
        
        assert event1.version == 1
        assert event2.version == 2
    
    def test_event_correlation_id(self):
        """Test event correlation ID"""
        correlation_id = "corr-123"
        event = OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            correlation_id=correlation_id
        )
        
        assert event.correlation_id == correlation_id 