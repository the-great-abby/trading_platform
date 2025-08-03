"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from decimal import Decimal
from datetime import datetime

from src.cqrs.base import CommandBus, QueryBus, EventBus
from src.core.trading_engine import TradingEngine
from src.strategies.base import BaseStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.risk.risk_manager import RiskManager
from src.utils.config import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def config():
    """Test configuration"""
    return Config(
        public_api_key="test_key",
        public_api_secret="test_secret",
        public_base_url="https://api.test.com",
        log_level="DEBUG",
        database_url="sqlite:///test.db"
    )


@pytest.fixture
def command_bus():
    """Command bus fixture"""
    return CommandBus()


@pytest.fixture
def query_bus():
    """Query bus fixture"""
    return QueryBus()


@pytest.fixture
def event_bus():
    """Event bus fixture"""
    return EventBus()


@pytest.fixture
def mock_market_data_provider():
    """Mock market data provider"""
    mock = AsyncMock()
    
    # Mock historical data
    mock.get_historical_data.return_value = {
        "AAPL": [
            {"timestamp": "2024-01-01T09:30:00Z", "open": 150.0, "high": 152.0, "low": 149.0, "close": 151.0, "volume": 1000000},
            {"timestamp": "2024-01-01T10:30:00Z", "open": 151.0, "high": 153.0, "low": 150.0, "close": 152.0, "volume": 1200000},
            {"timestamp": "2024-01-01T11:30:00Z", "open": 152.0, "high": 154.0, "low": 151.0, "close": 153.0, "volume": 1100000},
            {"timestamp": "2024-01-01T12:30:00Z", "open": 153.0, "high": 155.0, "low": 152.0, "close": 154.0, "volume": 1300000},
            {"timestamp": "2024-01-01T13:30:00Z", "open": 154.0, "high": 156.0, "low": 153.0, "close": 155.0, "volume": 1400000},
        ],
        "GOOGL": [
            {"timestamp": "2024-01-01T09:30:00Z", "open": 2800.0, "high": 2820.0, "low": 2790.0, "close": 2810.0, "volume": 500000},
            {"timestamp": "2024-01-01T10:30:00Z", "open": 2810.0, "high": 2830.0, "low": 2800.0, "close": 2820.0, "volume": 600000},
            {"timestamp": "2024-01-01T11:30:00Z", "open": 2820.0, "high": 2840.0, "low": 2810.0, "close": 2830.0, "volume": 550000},
            {"timestamp": "2024-01-01T12:30:00Z", "open": 2830.0, "high": 2850.0, "low": 2820.0, "close": 2840.0, "volume": 650000},
            {"timestamp": "2024-01-01T13:30:00Z", "open": 2840.0, "high": 2860.0, "low": 2830.0, "close": 2850.0, "volume": 700000},
        ]
    }
    
    # Mock real-time data
    mock.get_real_time_data.return_value = {
        "AAPL": {"price": 155.0, "volume": 1000000, "timestamp": datetime.now()},
        "GOOGL": {"price": 2850.0, "volume": 500000, "timestamp": datetime.now()}
    }
    
    # Mock order placement
    mock.place_order.return_value = {
        "order_id": "test-order-123",
        "status": "pending",
        "filled_quantity": 0,
        "remaining_quantity": 100
    }
    
    return mock


@pytest.fixture
def mock_risk_manager():
    """Mock risk manager"""
    mock = AsyncMock()
    
    # Mock risk checks
    mock.check_risk_limits.return_value = True
    mock.calculate_position_size.return_value = 100
    mock.check_portfolio_risk.return_value = True
    mock.validate_order.return_value = True
    
    return mock


@pytest.fixture
def mock_portfolio_manager():
    """Mock portfolio manager"""
    mock = AsyncMock()
    
    # Mock portfolio operations
    mock.get_positions.return_value = {
        "AAPL": {"quantity": 100, "avg_price": 150.0, "market_value": 15500.0},
        "GOOGL": {"quantity": 10, "avg_price": 2800.0, "market_value": 28500.0}
    }
    
    mock.get_cash_balance.return_value = Decimal("50000.00")
    mock.update_position.return_value = True
    
    return mock


@pytest.fixture
def trading_engine(config, command_bus, query_bus, event_bus, mock_market_data_provider, mock_risk_manager):
    """Trading engine fixture"""
    return TradingEngine(
        config=config,
        command_bus=command_bus,
        query_bus=query_bus,
        event_bus=event_bus,
        market_data_provider=mock_market_data_provider,
        risk_manager=mock_risk_manager
    )





@pytest.fixture
def rsi_strategy():
    """RSI strategy fixture"""
    return RSIStrategy(
        period=14,
        oversold_threshold=30,
        overbought_threshold=70
    )


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "AAPL": [
            {"timestamp": "2024-01-01T09:30:00Z", "open": 150.0, "high": 152.0, "low": 149.0, "close": 151.0, "volume": 1000000},
            {"timestamp": "2024-01-01T10:30:00Z", "open": 151.0, "high": 153.0, "low": 150.0, "close": 152.0, "volume": 1200000},
            {"timestamp": "2024-01-01T11:30:00Z", "open": 152.0, "high": 154.0, "low": 151.0, "close": 153.0, "volume": 1100000},
            {"timestamp": "2024-01-01T12:30:00Z", "open": 153.0, "high": 155.0, "low": 152.0, "close": 154.0, "volume": 1300000},
            {"timestamp": "2024-01-01T13:30:00Z", "open": 154.0, "high": 156.0, "low": 153.0, "close": 155.0, "volume": 1400000},
            {"timestamp": "2024-01-01T14:30:00Z", "open": 155.0, "high": 157.0, "low": 154.0, "close": 156.0, "volume": 1500000},
            {"timestamp": "2024-01-01T15:30:00Z", "open": 156.0, "high": 158.0, "low": 155.0, "close": 157.0, "volume": 1600000},
            {"timestamp": "2024-01-01T16:30:00Z", "open": 157.0, "high": 159.0, "low": 156.0, "close": 158.0, "volume": 1700000},
            {"timestamp": "2024-01-02T09:30:00Z", "open": 158.0, "high": 160.0, "low": 157.0, "close": 159.0, "volume": 1800000},
            {"timestamp": "2024-01-02T10:30:00Z", "open": 159.0, "high": 161.0, "low": 158.0, "close": 160.0, "volume": 1900000},
        ]
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "order_id": "test-order-123",
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 100,
        "order_type": "limit",
        "limit_price": Decimal("150.00"),
        "time_in_force": "day",
        "user_id": "user123",
        "strategy_id": "strategy-123",
        "status": "pending"
    }


@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for testing"""
    return {
        "strategy_id": "sma-crossover-1",
        "name": "SMA Crossover Strategy",
        "strategy_type": "SMA_CROSSOVER",
        "symbols": ["AAPL", "GOOGL"],
        "parameters": {
            "short_period": 10,
            "long_period": 30,
            "threshold": 0.01
        },
        "initial_capital": Decimal("10000.00"),
        "risk_limits": {
            "max_position_size": 0.1,
            "max_daily_loss": 0.05
        },
        "is_active": True
    }


@pytest.fixture
def mock_event_store():
    """Mock event store"""
    mock = AsyncMock()
    
    # Mock event storage
    mock.save_events.return_value = True
    mock.get_events.return_value = []
    mock.get_events_by_type.return_value = []
    mock.get_events_by_aggregate.return_value = []
    
    return mock


@pytest.fixture
def mock_snapshot_store():
    """Mock snapshot store"""
    mock = AsyncMock()
    
    # Mock snapshot operations
    mock.save_snapshot.return_value = True
    mock.get_snapshot.return_value = None
    mock.get_latest_snapshot.return_value = None
    
    return mock


@pytest.fixture
def mock_aggregate_repository():
    """Mock aggregate repository"""
    mock = AsyncMock()
    
    # Mock aggregate operations
    mock.save.return_value = True
    mock.get_by_id.return_value = None
    mock.get_all.return_value = []
    
    return mock


@pytest.fixture
def sample_events():
    """Sample events for testing"""
    from src.services.trading.events import OrderPlacedEvent, OrderFilledEvent, OrderCancelledEvent
    
    return [
        OrderPlacedEvent(
            aggregate_id="order-123",
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="limit",
            limit_price=Decimal("150.00"),
            user_id="user123"
        ),
        OrderFilledEvent(
            aggregate_id="order-123",
            filled_quantity=100,
            fill_price=Decimal("150.00"),
            commission=Decimal("1.00")
        ),
        OrderCancelledEvent(
            aggregate_id="order-124",
            reason="User request",
            user_id="user123"
        )
    ]


@pytest.fixture
def sample_commands():
    """Sample commands for testing"""
    from src.services.trading.commands import PlaceOrderCommand, CancelOrderCommand, ExecuteStrategyCommand
    
    return [
        PlaceOrderCommand(
            symbol="AAPL",
            side="BUY",
            quantity=100,
            order_type="market",
            user_id="user123"
        ),
        CancelOrderCommand(
            order_id="order-123",
            reason="User request",
            user_id="user123"
        ),
        ExecuteStrategyCommand(
            strategy_id="strategy-123",
            symbols=["AAPL", "GOOGL"],
            parameters={"param1": "value1"}
        )
    ]


@pytest.fixture
def mock_logger():
    """Mock logger"""
    mock = Mock()
    mock.debug = Mock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.critical = Mock()
    return mock


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "async: mark test as async"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # Mark integration tests based on file path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# Test reporting
def pytest_html_report_title(report):
    """Set HTML report title"""
    report.title = "Trading Bot Test Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add description to test report"""
    outcome = yield
    report = outcome.get_result()
    
    # Add test description
    if hasattr(item.function, "__doc__") and item.function.__doc__:
        report.description = str(item.function.__doc__).strip()
    else:
        report.description = item.function.__name__.replace("_", " ").title() 