"""
Unit tests for trading commands
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.services.trading.commands import (
    PlaceOrderCommand,
    CancelOrderCommand,
    UpdateOrderCommand,
    ExecuteStrategyCommand,
    UpdateStrategyCommand,
    CreateStrategyCommand
)


class TestPlaceOrderCommand:
    """Test PlaceOrderCommand"""
    
    def test_place_order_command_creation(self):
        """Test creating a place order command"""
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            user_id="user123"
        )
        
        assert cmd.symbol == "AAPL"
        assert cmd.side == "BUY"
        assert cmd.quantity == 100
        assert cmd.order_type == "market"
        assert cmd.user_id == "user123"
        assert cmd.limit_price is None
        assert cmd.stop_price is None
        assert cmd.time_in_force == "day"
    
    def test_place_order_command_with_limit_price(self):
        """Test creating a place order command with limit price"""
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="SELL",
            quantity=50,
            order_type="limit",
            limit_price=Decimal("150.00"),
            user_id="user123"
        )
        
        assert cmd.order_type == "limit"
        assert cmd.limit_price == Decimal("150.00")
        assert cmd.side == "SELL"
    
    def test_place_order_command_with_stop_price(self):
        """Test creating a place order command with stop price"""
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="SELL",
            quantity=50,
            order_type="stop",
            stop_price=Decimal("140.00"),
            user_id="user123"
        )
        
        assert cmd.order_type == "stop"
        assert cmd.stop_price == Decimal("140.00")
    
    def test_place_order_command_with_strategy(self):
        """Test creating a place order command with strategy"""
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=100,
            strategy_id="strategy-123",
            metadata={"reason": "SMA crossover signal"}
        )
        
        assert cmd.strategy_id == "strategy-123"
        assert cmd.metadata["reason"] == "SMA crossover signal"
    
    def test_place_order_command_validation(self):
        """Test place order command validation"""
        # Valid command
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=100
        )
        assert cmd.symbol is not None
        assert cmd.quantity > 0
        
        # Test invalid side
        with pytest.raises(ValueError):
            PlaceOrderCommand(
                symbol="AAPL",
                side="INVALID",
                quantity=100
            )


class TestCancelOrderCommand:
    """Test CancelOrderCommand"""
    
    def test_cancel_order_command_creation(self):
        """Test creating a cancel order command"""
        cmd = CancelOrderCommand(
            order_id="order-123",
            reason="User request",
            user_id="user123"
        )
        
        assert cmd.order_id == "order-123"
        assert cmd.reason == "User request"
        assert cmd.user_id == "user123"
    
    def test_cancel_order_command_without_reason(self):
        """Test creating a cancel order command without reason"""
        cmd = CancelOrderCommand(order_id="order-123")
        
        assert cmd.order_id == "order-123"
        assert cmd.reason is None


class TestUpdateOrderCommand:
    """Test UpdateOrderCommand"""
    
    def test_update_order_command_creation(self):
        """Test creating an update order command"""
        cmd = UpdateOrderCommand(
            order_id="order-123",
            quantity=75,
            limit_price=Decimal("145.00"),
            time_in_force="gtc"
        )
        
        assert cmd.order_id == "order-123"
        assert cmd.quantity == 75
        assert cmd.limit_price == Decimal("145.00")
        assert cmd.time_in_force == "gtc"
        assert cmd.stop_price is None
    
    def test_update_order_command_partial_update(self):
        """Test creating an update order command with partial updates"""
        cmd = UpdateOrderCommand(
            order_id="order-123",
            quantity=50  # Only update quantity
        )
        
        assert cmd.order_id == "order-123"
        assert cmd.quantity == 50
        assert cmd.limit_price is None
        assert cmd.stop_price is None
        assert cmd.time_in_force is None


class TestExecuteStrategyCommand:
    """Test ExecuteStrategyCommand"""
    
    def test_execute_strategy_command_creation(self):
        """Test creating an execute strategy command"""
        cmd = ExecuteStrategyCommand(
            strategy_id="strategy-123",
            symbols=["AAPL", "GOOGL", "MSFT"],
            parameters={"lookback_period": 20, "threshold": 0.02}
        )
        
        assert cmd.strategy_id == "strategy-123"
        assert cmd.symbols == ["AAPL", "GOOGL", "MSFT"]
        assert cmd.parameters["lookback_period"] == 20
        assert cmd.parameters["threshold"] == 0.02
    
    def test_execute_strategy_command_without_parameters(self):
        """Test creating an execute strategy command without parameters"""
        cmd = ExecuteStrategyCommand(
            strategy_id="strategy-123",
            symbols=["AAPL"]
        )
        
        assert cmd.strategy_id == "strategy-123"
        assert cmd.symbols == ["AAPL"]
        assert cmd.parameters is None


class TestUpdateStrategyCommand:
    """Test UpdateStrategyCommand"""
    
    def test_update_strategy_command_creation(self):
        """Test creating an update strategy command"""
        cmd = UpdateStrategyCommand(
            strategy_id="strategy-123",
            name="Updated SMA Strategy",
            parameters={"lookback_period": 30},
            is_active=False
        )
        
        assert cmd.strategy_id == "strategy-123"
        assert cmd.name == "Updated SMA Strategy"
        assert cmd.parameters["lookback_period"] == 30
        assert cmd.is_active is False
    
    def test_update_strategy_command_partial_update(self):
        """Test creating an update strategy command with partial updates"""
        cmd = UpdateStrategyCommand(
            strategy_id="strategy-123",
            is_active=True  # Only update active status
        )
        
        assert cmd.strategy_id == "strategy-123"
        assert cmd.is_active is True
        assert cmd.name is None
        assert cmd.parameters is None


class TestCreateStrategyCommand:
    """Test CreateStrategyCommand"""
    
    def test_create_strategy_command_creation(self):
        """Test creating a create strategy command"""
        cmd = CreateStrategyCommand(
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
        
        assert cmd.name == "SMA Crossover Strategy"
        assert cmd.strategy_type == "SMA_CROSSOVER"
        assert cmd.symbols == ["AAPL", "GOOGL"]
        assert cmd.parameters["short_period"] == 10
        assert cmd.parameters["long_period"] == 30
        assert cmd.initial_capital == Decimal("10000.00")
        assert cmd.risk_limits["max_position_size"] == 0.1
    
    def test_create_strategy_command_without_risk_limits(self):
        """Test creating a create strategy command without risk limits"""
        cmd = CreateStrategyCommand(
            name="Simple Strategy",
            strategy_type="SIMPLE",
            symbols=["AAPL"],
            parameters={},
            initial_capital=Decimal("5000.00")
        )
        
        assert cmd.name == "Simple Strategy"
        assert cmd.strategy_type == "SIMPLE"
        assert cmd.risk_limits is None


class TestCommandValidation:
    """Test command validation scenarios"""
    
    def test_place_order_invalid_quantity(self):
        """Test place order with invalid quantity"""
        with pytest.raises(ValueError):
            PlaceOrderCommand(
                symbol="AAPL",
                side="BUY",
                quantity=0  # Invalid quantity
            )
    
    def test_place_order_invalid_order_type(self):
        """Test place order with invalid order type"""
        with pytest.raises(ValueError):
            PlaceOrderCommand(
                symbol="AAPL",
                side="BUY",
                quantity=100,
                order_type="invalid_type"
            )
    
    def test_place_order_limit_without_price(self):
        """Test limit order without limit price"""
        with pytest.raises(ValueError):
            PlaceOrderCommand(
                symbol="AAPL",
                side="BUY",
                quantity=100,
                order_type="limit"  # Limit order without price
            )
    
    def test_place_order_stop_without_price(self):
        """Test stop order without stop price"""
        with pytest.raises(ValueError):
            PlaceOrderCommand(
                symbol="AAPL",
                side="SELL",
                quantity=100,
                order_type="stop"  # Stop order without price
            )


class TestCommandSerialization:
    """Test command serialization"""
    
    def test_place_order_command_serialization(self):
        """Test place order command serialization"""
        cmd = PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=100,
            limit_price=Decimal("150.00"),
            user_id="user123"
        )
        
        cmd_dict = cmd.dict()
        
        assert cmd_dict["symbol"] == "AAPL"
        assert cmd_dict["side"] == "BUY"
        assert cmd_dict["quantity"] == 100
        assert cmd_dict["limit_price"] == "150.00"  # Decimal serialized as string
        assert cmd_dict["user_id"] == "user123"
        assert "command_id" in cmd_dict
        assert "timestamp" in cmd_dict
    
    def test_execute_strategy_command_serialization(self):
        """Test execute strategy command serialization"""
        cmd = ExecuteStrategyCommand(
            strategy_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            parameters={"param1": "value1"}
        )
        
        cmd_dict = cmd.dict()
        
        assert cmd_dict["strategy_id"] == "strategy-123"
        assert cmd_dict["symbols"] == ["AAPL", "GOOGL"]
        assert cmd_dict["parameters"]["param1"] == "value1" 