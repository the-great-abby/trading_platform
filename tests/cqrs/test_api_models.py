"""
Tests for Phase 4: API Models and Schemas
Tests Pydantic models, request/response schemas, and validation
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import ValidationError

from src.api.models.cqrs_models import (
    # Request Models
    PlaceOrderRequest, CancelOrderRequest, CreateStrategyRequest,
    UpdatePortfolioRequest, UpdatePositionRequest,
    GetPortfolioRequest, GetPositionsRequest, GetMarketDataRequest,
    GetPerformanceRequest, GetBacktestResultsRequest,
    
    # Response Models
    OrderResponse, PortfolioResponse, PositionResponse, MarketDataResponse,
    PerformanceResponse, BacktestResultsResponse, StrategyResponse,
    
    # WebSocket Models
    WebSocketMessage, EventSubscription, EventBroadcast,
    
    # Error Models
    APIError, ValidationErrorResponse, ErrorDetail
)


class TestRequestModels:
    """Test request model validation and serialization"""
    
    def test_place_order_request_valid(self):
        """Test valid place order request"""
        request = PlaceOrderRequest(
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        assert request.symbol == "AAPL"
        assert request.side == "buy"
        assert request.quantity == 100
        assert request.order_type == "market"
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
        assert request.price is None  # Optional field
    
    def test_place_order_request_with_price(self):
        """Test place order request with price"""
        request = PlaceOrderRequest(
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="limit",
            price=Decimal("150.50"),
            user_id="user1",
            account_id="acc1"
        )
        
        assert request.price == Decimal("150.50")
        assert request.order_type == "limit"
    
    def test_place_order_request_validation_errors(self):
        """Test place order request validation errors"""
        # Invalid side
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="AAPL",
                side="invalid_side",
                quantity=100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
        
        # Invalid order type
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="invalid_type",
                user_id="user1",
                account_id="acc1"
            )
        
        # Negative quantity
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=-100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
        
        # Empty symbol
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="",
                side="buy",
                quantity=100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
    
    def test_cancel_order_request_valid(self):
        """Test valid cancel order request"""
        request = CancelOrderRequest(
            order_id="order_123",
            reason="user_request"
        )
        
        assert request.order_id == "order_123"
        assert request.reason == "user_request"
    
    def test_cancel_order_request_validation_errors(self):
        """Test cancel order request validation errors"""
        # Empty order_id
        with pytest.raises(ValidationError):
            CancelOrderRequest(
                order_id="",
                reason="user_request"
            )
        
        # Empty reason
        with pytest.raises(ValidationError):
            CancelOrderRequest(
                order_id="order_123",
                reason=""
            )
    
    def test_create_strategy_request_valid(self):
        """Test valid create strategy request"""
        request = CreateStrategyRequest(
            name="Test Strategy",
            description="A test trading strategy",
            parameters={"risk_level": "medium", "max_position_size": 1000},
            user_id="user1",
            account_id="acc1"
        )
        
        assert request.name == "Test Strategy"
        assert request.description == "A test trading strategy"
        assert request.parameters == {"risk_level": "medium", "max_position_size": 1000}
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
    
    def test_create_strategy_request_validation_errors(self):
        """Test create strategy request validation errors"""
        # Empty name
        with pytest.raises(ValidationError):
            CreateStrategyRequest(
                name="",
                description="A test trading strategy",
                parameters={},
                user_id="user1",
                account_id="acc1"
            )
        
        # Invalid parameters type
        with pytest.raises(ValidationError):
            CreateStrategyRequest(
                name="Test Strategy",
                description="A test trading strategy",
                parameters="invalid_parameters",
                user_id="user1",
                account_id="acc1"
            )
    
    def test_update_portfolio_request_valid(self):
        """Test valid update portfolio request"""
        request = UpdatePortfolioRequest(
            portfolio_id="portfolio_123",
            name="Updated Portfolio",
            cash_balance=Decimal("6000.00"),
            user_id="user1",
            account_id="acc1"
        )
        
        assert request.portfolio_id == "portfolio_123"
        assert request.name == "Updated Portfolio"
        assert request.cash_balance == Decimal("6000.00")
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
    
    def test_update_portfolio_request_validation_errors(self):
        """Test update portfolio request validation errors"""
        # Negative cash balance
        with pytest.raises(ValidationError):
            UpdatePortfolioRequest(
                portfolio_id="portfolio_123",
                name="Updated Portfolio",
                cash_balance=Decimal("-1000.00"),
                user_id="user1",
                account_id="acc1"
            )
        
        # Empty portfolio_id
        with pytest.raises(ValidationError):
            UpdatePortfolioRequest(
                portfolio_id="",
                name="Updated Portfolio",
                cash_balance=Decimal("6000.00"),
                user_id="user1",
                account_id="acc1"
            )
    
    def test_get_portfolio_request_valid(self):
        """Test valid get portfolio request"""
        request = GetPortfolioRequest(
            user_id="user1",
            account_id="acc1",
            include_positions=True,
            include_performance=True
        )
        
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
        assert request.include_positions == True
        assert request.include_performance == True
    
    def test_get_portfolio_request_defaults(self):
        """Test get portfolio request with defaults"""
        request = GetPortfolioRequest(
            user_id="user1",
            account_id="acc1"
        )
        
        assert request.include_positions == False
        assert request.include_performance == False
    
    def test_get_positions_request_valid(self):
        """Test valid get positions request"""
        request = GetPositionsRequest(
            user_id="user1",
            account_id="acc1",
            symbol="AAPL",
            status="open"
        )
        
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
        assert request.symbol == "AAPL"
        assert request.status == "open"
    
    def test_get_market_data_request_valid(self):
        """Test valid get market data request"""
        request = GetMarketDataRequest(
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            interval="1d"
        )
        
        assert request.symbol == "AAPL"
        assert request.start_date == date(2024, 1, 1)
        assert request.end_date == date(2024, 1, 31)
        assert request.interval == "1d"
    
    def test_get_market_data_request_defaults(self):
        """Test get market data request with defaults"""
        request = GetMarketDataRequest(symbol="AAPL")
        
        assert request.start_date is None
        assert request.end_date is None
        assert request.interval == "1d"
    
    def test_get_performance_request_valid(self):
        """Test valid get performance request"""
        request = GetPerformanceRequest(
            user_id="user1",
            account_id="acc1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            metrics=["total_return", "sharpe_ratio", "max_drawdown"]
        )
        
        assert request.user_id == "user1"
        assert request.account_id == "acc1"
        assert request.start_date == date(2024, 1, 1)
        assert request.end_date == date(2024, 1, 31)
        assert request.metrics == ["total_return", "sharpe_ratio", "max_drawdown"]
    
    def test_get_performance_request_defaults(self):
        """Test get performance request with defaults"""
        request = GetPerformanceRequest(
            user_id="user1",
            account_id="acc1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert request.metrics == ["total_return", "sharpe_ratio", "max_drawdown"]
    
    def test_get_backtest_results_request_valid(self):
        """Test valid get backtest results request"""
        request = GetBacktestResultsRequest(
            strategy_id="strategy_123",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert request.strategy_id == "strategy_123"
        assert request.start_date == date(2024, 1, 1)
        assert request.end_date == date(2024, 1, 31)


class TestResponseModels:
    """Test response model validation and serialization"""
    
    def test_order_response_valid(self):
        """Test valid order response"""
        response = OrderResponse(
            order_id="order_123",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            status="pending",
            user_id="user1",
            account_id="acc1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert response.order_id == "order_123"
        assert response.symbol == "AAPL"
        assert response.side == "buy"
        assert response.quantity == 100
        assert response.order_type == "market"
        assert response.status == "pending"
        assert response.user_id == "user1"
        assert response.account_id == "acc1"
    
    def test_order_response_with_price(self):
        """Test order response with price"""
        response = OrderResponse(
            order_id="order_123",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="limit",
            price=Decimal("150.50"),
            status="pending",
            user_id="user1",
            account_id="acc1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert response.price == Decimal("150.50")
        assert response.order_type == "limit"
    
    def test_portfolio_response_valid(self):
        """Test valid portfolio response"""
        response = PortfolioResponse(
            user_id="user1",
            account_id="acc1",
            total_value=Decimal("10000.00"),
            cash_balance=Decimal("5000.00"),
            positions=[
                PositionResponse(
                    symbol="AAPL",
                    quantity=100,
                    average_price=Decimal("150.00"),
                    current_price=Decimal("155.00"),
                    unrealized_pnl=Decimal("500.00")
                )
            ],
            performance_metrics={
                "total_return": Decimal("0.05"),
                "sharpe_ratio": Decimal("1.2"),
                "max_drawdown": Decimal("0.02")
            },
            last_updated=datetime.now()
        )
        
        assert response.user_id == "user1"
        assert response.account_id == "acc1"
        assert response.total_value == Decimal("10000.00")
        assert response.cash_balance == Decimal("5000.00")
        assert len(response.positions) == 1
        assert response.positions[0].symbol == "AAPL"
    
    def test_position_response_valid(self):
        """Test valid position response"""
        response = PositionResponse(
            symbol="AAPL",
            quantity=100,
            average_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            unrealized_pnl=Decimal("500.00"),
            realized_pnl=Decimal("0.00")
        )
        
        assert response.symbol == "AAPL"
        assert response.quantity == 100
        assert response.average_price == Decimal("150.00")
        assert response.current_price == Decimal("155.00")
        assert response.unrealized_pnl == Decimal("500.00")
        assert response.realized_pnl == Decimal("0.00")
    
    def test_market_data_response_valid(self):
        """Test valid market data response"""
        response = MarketDataResponse(
            symbol="AAPL",
            current_price=Decimal("155.00"),
            price_change=Decimal("5.00"),
            price_change_pct=Decimal("0.032"),
            volume=1000000,
            last_updated=datetime.now(),
            historical_data=[
                {"date": "2024-01-01", "price": Decimal("150.00")},
                {"date": "2024-01-02", "price": Decimal("155.00")}
            ]
        )
        
        assert response.symbol == "AAPL"
        assert response.current_price == Decimal("155.00")
        assert response.price_change == Decimal("5.00")
        assert response.price_change_pct == Decimal("0.032")
        assert response.volume == 1000000
        assert len(response.historical_data) == 2
    
    def test_performance_response_valid(self):
        """Test valid performance response"""
        response = PerformanceResponse(
            user_id="user1",
            account_id="acc1",
            total_return=Decimal("0.05"),
            sharpe_ratio=Decimal("1.2"),
            max_drawdown=Decimal("0.02"),
            win_rate=Decimal("0.65"),
            avg_trade_duration=timedelta(days=5),
            last_updated=datetime.now()
        )
        
        assert response.user_id == "user1"
        assert response.account_id == "acc1"
        assert response.total_return == Decimal("0.05")
        assert response.sharpe_ratio == Decimal("1.2")
        assert response.max_drawdown == Decimal("0.02")
        assert response.win_rate == Decimal("0.65")
        assert response.avg_trade_duration == timedelta(days=5)
    
    def test_backtest_results_response_valid(self):
        """Test valid backtest results response"""
        response = BacktestResultsResponse(
            strategy_id="strategy_123",
            total_return=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.05"),
            win_rate=Decimal("0.70"),
            total_trades=100,
            trades=[
                {
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 100,
                    "price": Decimal("150.00"),
                    "timestamp": datetime.now()
                }
            ],
            last_updated=datetime.now()
        )
        
        assert response.strategy_id == "strategy_123"
        assert response.total_return == Decimal("0.15")
        assert response.sharpe_ratio == Decimal("1.5")
        assert response.max_drawdown == Decimal("0.05")
        assert response.win_rate == Decimal("0.70")
        assert response.total_trades == 100
        assert len(response.trades) == 1
    
    def test_strategy_response_valid(self):
        """Test valid strategy response"""
        response = StrategyResponse(
            strategy_id="strategy_123",
            name="Test Strategy",
            description="A test trading strategy",
            parameters={"risk_level": "medium", "max_position_size": 1000},
            status="active",
            user_id="user1",
            account_id="acc1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert response.strategy_id == "strategy_123"
        assert response.name == "Test Strategy"
        assert response.description == "A test trading strategy"
        assert response.parameters == {"risk_level": "medium", "max_position_size": 1000}
        assert response.status == "active"
        assert response.user_id == "user1"
        assert response.account_id == "acc1"


class TestWebSocketModels:
    """Test WebSocket message models"""
    
    def test_websocket_message_valid(self):
        """Test valid WebSocket message"""
        message = WebSocketMessage(
            type="event",
            data={
                "event_type": "OrderCreated",
                "order_id": "order_123",
                "symbol": "AAPL"
            }
        )
        
        assert message.type == "event"
        assert message.data["event_type"] == "OrderCreated"
        assert message.data["order_id"] == "order_123"
        assert message.data["symbol"] == "AAPL"
    
    def test_event_subscription_valid(self):
        """Test valid event subscription"""
        subscription = EventSubscription(
            type="subscribe",
            event_types=["OrderCreated", "OrderFilled"],
            user_id="user1",
            account_id="acc1"
        )
        
        assert subscription.type == "subscribe"
        assert subscription.event_types == ["OrderCreated", "OrderFilled"]
        assert subscription.user_id == "user1"
        assert subscription.account_id == "acc1"
    
    def test_event_broadcast_valid(self):
        """Test valid event broadcast"""
        broadcast = EventBroadcast(
            type="event",
            event_type="OrderCreated",
            data={
                "order_id": "order_123",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100
            },
            timestamp=datetime.now()
        )
        
        assert broadcast.type == "event"
        assert broadcast.event_type == "OrderCreated"
        assert broadcast.data["order_id"] == "order_123"
        assert broadcast.data["symbol"] == "AAPL"
        assert broadcast.timestamp is not None


class TestErrorModels:
    """Test error response models"""
    
    def test_api_error_valid(self):
        """Test valid API error"""
        error = APIError(
            error="validation_error",
            message="Invalid input data",
            details={"field": "symbol", "issue": "required"}
        )
        
        assert error.error == "validation_error"
        assert error.message == "Invalid input data"
        assert error.details["field"] == "symbol"
        assert error.details["issue"] == "required"
    
    def test_validation_error_response_valid(self):
        """Test valid validation error response"""
        error_response = ValidationErrorResponse(
            error="validation_error",
            message="Input validation failed",
            details=[
                ErrorDetail(
                    field="symbol",
                    message="Field is required",
                    value=None
                ),
                ErrorDetail(
                    field="quantity",
                    message="Must be positive",
                    value=-100
                )
            ]
        )
        
        assert error_response.error == "validation_error"
        assert error_response.message == "Input validation failed"
        assert len(error_response.details) == 2
        assert error_response.details[0].field == "symbol"
        assert error_response.details[0].message == "Field is required"
        assert error_response.details[0].value is None
        assert error_response.details[1].field == "quantity"
        assert error_response.details[1].message == "Must be positive"
        assert error_response.details[1].value == -100
    
    def test_error_detail_valid(self):
        """Test valid error detail"""
        error_detail = ErrorDetail(
            field="symbol",
            message="Field is required",
            value=None
        )
        
        assert error_detail.field == "symbol"
        assert error_detail.message == "Field is required"
        assert error_detail.value is None


class TestModelSerialization:
    """Test model serialization and deserialization"""
    
    def test_place_order_request_serialization(self):
        """Test place order request serialization"""
        request = PlaceOrderRequest(
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        # Test to dict
        data = request.model_dump()
        assert data["symbol"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == 100
        assert data["order_type"] == "market"
        assert data["user_id"] == "user1"
        assert data["account_id"] == "acc1"
        
        # Test from dict
        new_request = PlaceOrderRequest(**data)
        assert new_request.symbol == "AAPL"
        assert new_request.side == "buy"
        assert new_request.quantity == 100
        assert new_request.order_type == "market"
        assert new_request.user_id == "user1"
        assert new_request.account_id == "acc1"
    
    def test_order_response_serialization(self):
        """Test order response serialization"""
        now = datetime.now()
        response = OrderResponse(
            order_id="order_123",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            status="pending",
            user_id="user1",
            account_id="acc1",
            created_at=now,
            updated_at=now
        )
        
        # Test to dict
        data = response.model_dump()
        assert data["order_id"] == "order_123"
        assert data["symbol"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == 100
        assert data["order_type"] == "market"
        assert data["status"] == "pending"
        assert data["user_id"] == "user1"
        assert data["account_id"] == "acc1"
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        
        # Test from dict
        new_response = OrderResponse(**data)
        assert new_response.order_id == "order_123"
        assert new_response.symbol == "AAPL"
        assert new_response.side == "buy"
        assert new_response.quantity == 100
        assert new_response.order_type == "market"
        assert new_response.status == "pending"
        assert new_response.user_id == "user1"
        assert new_response.account_id == "acc1"
        assert new_response.created_at == now
        assert new_response.updated_at == now
    
    def test_decimal_serialization(self):
        """Test decimal field serialization"""
        response = OrderResponse(
            order_id="order_123",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="limit",
            price=Decimal("150.50"),
            status="pending",
            user_id="user1",
            account_id="acc1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test to dict
        data = response.model_dump()
        assert data["price"] == "150.50"  # Decimal serialized as string
        
        # Test from dict
        new_response = OrderResponse(**data)
        assert new_response.price == Decimal("150.50")
    
    def test_datetime_serialization(self):
        """Test datetime field serialization"""
        now = datetime.now()
        response = OrderResponse(
            order_id="order_123",
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            status="pending",
            user_id="user1",
            account_id="acc1",
            created_at=now,
            updated_at=now
        )
        
        # Test to dict
        data = response.model_dump()
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        
        # Test from dict
        new_response = OrderResponse(**data)
        assert new_response.created_at == now
        assert new_response.updated_at == now
    
    def test_optional_field_serialization(self):
        """Test optional field serialization"""
        request = PlaceOrderRequest(
            symbol="AAPL",
            side="buy",
            quantity=100,
            order_type="market",
            user_id="user1",
            account_id="acc1"
        )
        
        # Test to dict
        data = request.model_dump()
        assert "price" not in data or data["price"] is None
        
        # Test from dict
        new_request = PlaceOrderRequest(**data)
        assert new_request.price is None


class TestModelValidation:
    """Test model validation rules"""
    
    def test_enum_validation(self):
        """Test enum field validation"""
        # Valid enum values
        valid_sides = ["buy", "sell"]
        for side in valid_sides:
            request = PlaceOrderRequest(
                symbol="AAPL",
                side=side,
                quantity=100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
            assert request.side == side
        
        # Invalid enum values
        invalid_sides = ["BUY", "SELL", "invalid", ""]
        for side in invalid_sides:
            with pytest.raises(ValidationError):
                PlaceOrderRequest(
                    symbol="AAPL",
                    side=side,
                    quantity=100,
                    order_type="market",
                    user_id="user1",
                    account_id="acc1"
                )
    
    def test_string_validation(self):
        """Test string field validation"""
        # Valid strings
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        for symbol in valid_symbols:
            request = PlaceOrderRequest(
                symbol=symbol,
                side="buy",
                quantity=100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
            assert request.symbol == symbol
        
        # Invalid strings (empty)
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="",
                side="buy",
                quantity=100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
    
    def test_integer_validation(self):
        """Test integer field validation"""
        # Valid integers
        valid_quantities = [1, 100, 1000, 10000]
        for quantity in valid_quantities:
            request = PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=quantity,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
            assert request.quantity == quantity
        
        # Invalid integers (negative)
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=-100,
                order_type="market",
                user_id="user1",
                account_id="acc1"
            )
    
    def test_decimal_validation(self):
        """Test decimal field validation"""
        # Valid decimals
        valid_prices = [Decimal("0.01"), Decimal("150.50"), Decimal("1000.00")]
        for price in valid_prices:
            request = PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="limit",
                price=price,
                user_id="user1",
                account_id="acc1"
            )
            assert request.price == price
        
        # Invalid decimals (negative)
        with pytest.raises(ValidationError):
            PlaceOrderRequest(
                symbol="AAPL",
                side="buy",
                quantity=100,
                order_type="limit",
                price=Decimal("-150.50"),
                user_id="user1",
                account_id="acc1"
            )
    
    def test_date_validation(self):
        """Test date field validation"""
        # Valid dates
        valid_dates = [
            date(2024, 1, 1),
            date(2024, 12, 31),
            date.today()
        ]
        for start_date in valid_dates:
            request = GetMarketDataRequest(
                symbol="AAPL",
                start_date=start_date
            )
            assert request.start_date == start_date
        
        # Invalid dates (future dates)
        future_date = date.today().replace(year=date.today().year + 1)
        with pytest.raises(ValidationError):
            GetMarketDataRequest(
                symbol="AAPL",
                start_date=future_date
            )
    
    def test_list_validation(self):
        """Test list field validation"""
        # Valid lists
        valid_metrics = [
            ["total_return"],
            ["total_return", "sharpe_ratio"],
            ["total_return", "sharpe_ratio", "max_drawdown"]
        ]
        for metrics in valid_metrics:
            request = GetPerformanceRequest(
                user_id="user1",
                account_id="acc1",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                metrics=metrics
            )
            assert request.metrics == metrics
        
        # Invalid lists (empty)
        with pytest.raises(ValidationError):
            GetPerformanceRequest(
                user_id="user1",
                account_id="acc1",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                metrics=[]
            )
    
    def test_dict_validation(self):
        """Test dictionary field validation"""
        # Valid dictionaries
        valid_parameters = [
            {},
            {"risk_level": "medium"},
            {"risk_level": "medium", "max_position_size": 1000}
        ]
        for parameters in valid_parameters:
            request = CreateStrategyRequest(
                name="Test Strategy",
                description="A test trading strategy",
                parameters=parameters,
                user_id="user1",
                account_id="acc1"
            )
            assert request.parameters == parameters
        
        # Invalid dictionaries (not dict type)
        with pytest.raises(ValidationError):
            CreateStrategyRequest(
                name="Test Strategy",
                description="A test trading strategy",
                parameters="invalid_parameters",
                user_id="user1",
                account_id="acc1"
            )
