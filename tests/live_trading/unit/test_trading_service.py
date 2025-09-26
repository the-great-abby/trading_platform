"""
Unit tests for trading service.

Tests trade execution, order management, and position tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from src.services.live_trading.trading_service import (
    TradingService, TradingError, OrderExecutionError, PositionNotFoundError
)
from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus
)
from src.services.live_trading.public_api_client import PublicAPIClient


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_public_api_client():
    """Create mock Public.com API client."""
    return AsyncMock(spec=PublicAPIClient)


@pytest.fixture
def mock_risk_service():
    """Create mock risk service."""
    return AsyncMock()


@pytest.fixture
def mock_market_hours_service():
    """Create mock market hours service."""
    return AsyncMock()


@pytest.fixture
def sample_account():
    """Create sample trading account."""
    return LiveTradingAccount(
        account_id="test-account-123",
        public_account_id="public-123",
        account_name="Test Account",
        account_type="CASH",
        buying_power=10000.0,
        cash_balance=5000.0,
        equity=15000.0,
        is_active=True
    )


@pytest.fixture
def sample_position():
    """Create sample position."""
    return LivePosition(
        account_id="test-account-123",
        symbol="SPY",
        strategy=StrategyType.IRON_CONDOR,
        quantity=10,
        average_price=Decimal("400.00"),
        current_price=Decimal("405.00"),
        unrealized_pnl=Decimal("50.00"),
        realized_pnl=Decimal("0.00"),
        status=PositionStatus.OPEN
    )


@pytest.fixture
def trading_service(mock_db_session, mock_public_api_client, mock_risk_service, mock_market_hours_service):
    """Create trading service instance."""
    return TradingService(
        db_session=mock_db_session,
        public_api_client=mock_public_api_client,
        risk_service=mock_risk_service,
        market_hours_service=mock_market_hours_service
    )


class TestTradeExecution:
    """Test trade execution methods."""
    
    @pytest.mark.asyncio
    async def test_execute_trade_success(self, trading_service, mock_db_session, mock_public_api_client, 
                                       mock_risk_service, mock_market_hours_service, sample_account):
        """Test successful trade execution."""
        # Mock market hours check
        mock_market_hours_service.is_market_open.return_value = True
        
        # Mock risk check
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        
        # Mock Public.com API response
        mock_public_api_client.execute_order.return_value = {
            "order_id": "public_order_123",
            "status": "FILLED",
            "filled_quantity": 100,
            "average_price": 400.25
        }
        
        # Mock database queries
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await trading_service.execute_trade("test-account-123", trade_details)
        
        assert result["success"] is True
        assert result["order_id"] == "public_order_123"
        assert result["status"] == "FILLED"
        assert result["filled_quantity"] == 100
        
        # Verify API client was called
        mock_public_api_client.execute_order.assert_called_once()
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_trade_market_closed(self, trading_service, mock_market_hours_service):
        """Test trade execution when market is closed."""
        mock_market_hours_service.is_market_open.return_value = False
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        with pytest.raises(TradingError, match="Market is closed"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_execute_trade_risk_check_failed(self, trading_service, mock_market_hours_service, 
                                                 mock_risk_service):
        """Test trade execution when risk check fails."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {
            "passed": False, 
            "message": "Position size exceeds limit"
        }
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100000,  # Very large quantity
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        with pytest.raises(TradingError, match="Risk check failed"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_execute_trade_api_error(self, trading_service, mock_market_hours_service, 
                                         mock_risk_service, mock_public_api_client):
        """Test trade execution when API returns error."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        mock_public_api_client.execute_order.side_effect = Exception("API Error")
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        with pytest.raises(OrderExecutionError, match="API Error"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_execute_trade_partial_fill(self, trading_service, mock_db_session, mock_public_api_client,
                                            mock_risk_service, mock_market_hours_service, sample_account):
        """Test trade execution with partial fill."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        
        # Mock partial fill response
        mock_public_api_client.execute_order.return_value = {
            "order_id": "public_order_123",
            "status": "PARTIAL_FILL",
            "filled_quantity": 50,
            "remaining_quantity": 50,
            "average_price": 400.25
        }
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        result = await trading_service.execute_trade("test-account-123", trade_details)
        
        assert result["success"] is True
        assert result["status"] == "PARTIAL_FILL"
        assert result["filled_quantity"] == 50
        assert result["remaining_quantity"] == 50
    
    @pytest.mark.asyncio
    async def test_execute_trade_limit_order(self, trading_service, mock_db_session, mock_public_api_client,
                                           mock_risk_service, mock_market_hours_service, sample_account):
        """Test limit order execution."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        
        mock_public_api_client.execute_order.return_value = {
            "order_id": "public_order_123",
            "status": "PENDING",
            "filled_quantity": 0,
            "remaining_quantity": 100
        }
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("395.00"),  # Limit price
            "order_type": "LIMIT"
        }
        
        result = await trading_service.execute_trade("test-account-123", trade_details)
        
        assert result["success"] is True
        assert result["status"] == "PENDING"
        assert result["filled_quantity"] == 0
        assert result["remaining_quantity"] == 100


class TestOrderManagement:
    """Test order management methods."""
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, trading_service, mock_public_api_client, mock_db_session):
        """Test successful order cancellation."""
        mock_public_api_client.cancel_order.return_value = {
            "order_id": "public_order_123",
            "status": "CANCELLED"
        }
        
        # Mock existing order status
        existing_order = OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="test-account-123",
            order_id="public_order_123",
            status="PENDING",
            symbol="SPY",
            order_type="MARKET",
            side="BUY",
            quantity=100,
            filled_quantity=0,
            remaining_quantity=100
        )
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_order
        
        result = await trading_service.cancel_order("test-account-123", "public_order_123")
        
        assert result["success"] is True
        assert result["status"] == "CANCELLED"
        
        # Verify API client was called
        mock_public_api_client.cancel_order.assert_called_once_with("public_order_123")
        
        # Verify database was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, trading_service, mock_db_session):
        """Test order cancellation when order not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(TradingError, match="Order not found"):
            await trading_service.cancel_order("test-account-123", "nonexistent_order")
    
    @pytest.mark.asyncio
    async def test_cancel_order_already_filled(self, trading_service, mock_db_session):
        """Test order cancellation when order is already filled."""
        existing_order = OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="test-account-123",
            order_id="public_order_123",
            status="FILLED",
            symbol="SPY",
            order_type="MARKET",
            side="BUY",
            quantity=100,
            filled_quantity=100,
            remaining_quantity=0
        )
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_order
        
        with pytest.raises(TradingError, match="Cannot cancel filled order"):
            await trading_service.cancel_order("test-account-123", "public_order_123")
    
    @pytest.mark.asyncio
    async def test_get_order_status(self, trading_service, mock_db_session):
        """Test getting order status."""
        existing_order = OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="test-account-123",
            order_id="public_order_123",
            status="FILLED",
            symbol="SPY",
            order_type="MARKET",
            side="BUY",
            quantity=100,
            filled_quantity=100,
            remaining_quantity=0,
            average_price=Decimal("400.25")
        )
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_order
        
        result = await trading_service.get_order_status("test-account-123", "public_order_123")
        
        assert result["order_id"] == "public_order_123"
        assert result["status"] == "FILLED"
        assert result["filled_quantity"] == 100
        assert result["remaining_quantity"] == 0
        assert result["average_price"] == Decimal("400.25")
    
    @pytest.mark.asyncio
    async def test_get_order_status_not_found(self, trading_service, mock_db_session):
        """Test getting order status when order not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(TradingError, match="Order not found"):
            await trading_service.get_order_status("test-account-123", "nonexistent_order")
    
    @pytest.mark.asyncio
    async def test_get_order_history(self, trading_service, mock_db_session):
        """Test getting order history for an account."""
        orders = [
            OrderStatus(
                order_status_id=str(uuid.uuid4()),
                account_id="test-account-123",
                order_id="order_1",
                status="FILLED",
                symbol="SPY",
                order_type="MARKET",
                side="BUY",
                quantity=100,
                filled_quantity=100,
                remaining_quantity=0
            ),
            OrderStatus(
                order_status_id=str(uuid.uuid4()),
                account_id="test-account-123",
                order_id="order_2",
                status="PENDING",
                symbol="QQQ",
                order_type="LIMIT",
                side="SELL",
                quantity=50,
                filled_quantity=0,
                remaining_quantity=50
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = orders
        
        result = await trading_service.get_order_history("test-account-123")
        
        assert len(result) == 2
        assert result[0]["order_id"] == "order_1"
        assert result[1]["order_id"] == "order_2"


class TestPositionManagement:
    """Test position management methods."""
    
    @pytest.mark.asyncio
    async def test_update_position_new_position(self, trading_service, mock_db_session, sample_account):
        """Test updating position for new position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing position
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await trading_service.update_position("test-account-123", trade_details)
        
        assert result["symbol"] == "SPY"
        assert result["quantity"] == 100
        assert result["average_price"] == Decimal("400.00")
        assert result["strategy"] == StrategyType.IRON_CONDOR
        
        # Verify new position was created
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_existing_position(self, trading_service, mock_db_session, sample_position):
        """Test updating position for existing position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 50,  # Adding to existing 10
            "price": Decimal("410.00"),
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await trading_service.update_position("test-account-123", trade_details)
        
        # New quantity: 10 + 50 = 60
        # New average price: ((10 * 400) + (50 * 410)) / 60 = (4000 + 20500) / 60 = 408.33
        assert result["quantity"] == 60
        assert result["average_price"] == Decimal("408.33")
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_reducing_position(self, trading_service, mock_db_session, sample_position):
        """Test updating position when reducing position size."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.SELL,
            "quantity": 5,  # Selling 5 from existing 10
            "price": Decimal("410.00"),
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await trading_service.update_position("test-account-123", trade_details)
        
        # New quantity: 10 - 5 = 5
        # Average price remains the same for remaining position
        assert result["quantity"] == 5
        assert result["average_price"] == Decimal("400.00")
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_closing_position(self, trading_service, mock_db_session, sample_position):
        """Test updating position when closing entire position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.SELL,
            "quantity": 10,  # Selling all 10
            "price": Decimal("410.00"),
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await trading_service.update_position("test-account-123", trade_details)
        
        # Position should be closed (quantity = 0)
        assert result["quantity"] == 0
        assert result["status"] == PositionStatus.CLOSED
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_position(self, trading_service, mock_db_session, sample_position):
        """Test getting position by symbol."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        result = await trading_service.get_position("test-account-123", "SPY")
        
        assert result["symbol"] == "SPY"
        assert result["quantity"] == 10
        assert result["average_price"] == Decimal("400.00")
        assert result["current_price"] == Decimal("405.00")
        assert result["unrealized_pnl"] == Decimal("50.00")
    
    @pytest.mark.asyncio
    async def test_get_position_not_found(self, trading_service, mock_db_session):
        """Test getting position when not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(PositionNotFoundError, match="Position not found"):
            await trading_service.get_position("test-account-123", "NONEXISTENT")
    
    @pytest.mark.asyncio
    async def test_get_all_positions(self, trading_service, mock_db_session):
        """Test getting all positions for an account."""
        positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("50.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN
            ),
            LivePosition(
                account_id="test-account-123",
                symbol="QQQ",
                strategy=StrategyType.BUTTERFLY_SPREAD,
                quantity=5,
                average_price=Decimal("300.00"),
                current_price=Decimal("295.00"),
                unrealized_pnl=Decimal("-25.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        
        result = await trading_service.get_all_positions("test-account-123")
        
        assert len(result) == 2
        assert result[0]["symbol"] == "SPY"
        assert result[1]["symbol"] == "QQQ"


class TestTradeHistory:
    """Test trade history methods."""
    
    @pytest.mark.asyncio
    async def test_get_trade_history(self, trading_service, mock_db_session):
        """Test getting trade history for an account."""
        trades = [
            LiveTrade(
                trade_id=str(uuid.uuid4()),
                account_id="test-account-123",
                public_order_id="order_1",
                symbol="SPY",
                action=TradeAction.BUY,
                quantity=100,
                price=Decimal("400.00"),
                total_amount=Decimal("40000.00"),
                filled_quantity=100,
                remaining_quantity=0,
                status=TradeStatus.FILLED,
                strategy=StrategyType.IRON_CONDOR,
                filled_at=datetime.now(timezone.utc)
            ),
            LiveTrade(
                trade_id=str(uuid.uuid4()),
                account_id="test-account-123",
                public_order_id="order_2",
                symbol="QQQ",
                action=TradeAction.SELL,
                quantity=50,
                price=Decimal("300.00"),
                total_amount=Decimal("15000.00"),
                filled_quantity=50,
                remaining_quantity=0,
                status=TradeStatus.FILLED,
                strategy=StrategyType.BUTTERFLY_SPREAD,
                filled_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = trades
        
        result = await trading_service.get_trade_history("test-account-123")
        
        assert len(result) == 2
        assert result[0]["symbol"] == "SPY"
        assert result[1]["symbol"] == "QQQ"
    
    @pytest.mark.asyncio
    async def test_get_trade_history_with_filters(self, trading_service, mock_db_session):
        """Test getting trade history with filters."""
        trades = [
            LiveTrade(
                trade_id=str(uuid.uuid4()),
                account_id="test-account-123",
                public_order_id="order_1",
                symbol="SPY",
                action=TradeAction.BUY,
                quantity=100,
                price=Decimal("400.00"),
                total_amount=Decimal("40000.00"),
                filled_quantity=100,
                remaining_quantity=0,
                status=TradeStatus.FILLED,
                strategy=StrategyType.IRON_CONDOR,
                filled_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = trades
        
        filters = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "start_date": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2024, 12, 31, tzinfo=timezone.utc)
        }
        
        result = await trading_service.get_trade_history("test-account-123", filters=filters)
        
        assert len(result) == 1
        assert result[0]["symbol"] == "SPY"
        assert result[0]["strategy"] == StrategyType.IRON_CONDOR


class TestPricingUpdates:
    """Test pricing and P&L update methods."""
    
    @pytest.mark.asyncio
    async def test_update_position_prices(self, trading_service, mock_db_session, mock_public_api_client):
        """Test updating position prices from market data."""
        positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("50.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        
        # Mock market data response
        mock_public_api_client.get_market_data.return_value = {
            "symbol": "SPY",
            "price": 410.00,
            "bid": 409.95,
            "ask": 410.05
        }
        
        result = await trading_service.update_position_prices("test-account-123")
        
        assert len(result) == 1
        assert result[0]["symbol"] == "SPY"
        assert result[0]["current_price"] == Decimal("410.00")
        assert result[0]["unrealized_pnl"] == Decimal("100.00")  # (410 - 400) * 10
        
        # Verify API was called
        mock_public_api_client.get_market_data.assert_called_with("SPY")
        
        # Verify database was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_pnl(self, trading_service, mock_db_session):
        """Test calculating portfolio P&L."""
        positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("410.00"),
                unrealized_pnl=Decimal("100.00"),
                realized_pnl=Decimal("50.00"),
                status=PositionStatus.OPEN
            ),
            LivePosition(
                account_id="test-account-123",
                symbol="QQQ",
                strategy=StrategyType.BUTTERFLY_SPREAD,
                quantity=5,
                average_price=Decimal("300.00"),
                current_price=Decimal("295.00"),
                unrealized_pnl=Decimal("-25.00"),
                realized_pnl=Decimal("75.00"),
                status=PositionStatus.OPEN
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        
        result = await trading_service.calculate_portfolio_pnl("test-account-123")
        
        assert result["total_unrealized_pnl"] == Decimal("75.00")  # 100 + (-25)
        assert result["total_realized_pnl"] == Decimal("125.00")   # 50 + 75
        assert result["total_pnl"] == Decimal("200.00")           # 75 + 125
        assert result["position_count"] == 2


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_execute_trade_invalid_trade_data(self, trading_service):
        """Test trade execution with invalid trade data."""
        trade_details = {
            "symbol": "SPY",
            # Missing required fields
        }
        
        with pytest.raises(TradingError, match="Invalid trade data"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_execute_trade_account_not_found(self, trading_service, mock_db_session, 
                                                 mock_market_hours_service, mock_risk_service):
        """Test trade execution when account not found."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        with pytest.raises(TradingError, match="Account not found"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_execute_trade_database_error(self, trading_service, mock_db_session, 
                                              mock_market_hours_service, mock_risk_service):
        """Test trade execution with database error."""
        mock_market_hours_service.is_market_open.return_value = True
        mock_risk_service.comprehensive_risk_check.return_value = {"passed": True, "message": "All checks passed"}
        mock_db_session.execute.side_effect = Exception("Database error")
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        with pytest.raises(TradingError, match="Database error"):
            await trading_service.execute_trade("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_update_position_insufficient_quantity(self, trading_service, mock_db_session, sample_position):
        """Test updating position when trying to sell more than owned."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.SELL,
            "quantity": 20,  # Trying to sell 20 when only 10 owned
            "price": Decimal("410.00"),
            "strategy": StrategyType.IRON_CONDOR
        }
        
        with pytest.raises(TradingError, match="Insufficient quantity"):
            await trading_service.update_position("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_update_position_price_update_error(self, trading_service, mock_db_session, 
                                                    mock_public_api_client):
        """Test position price update with API error."""
        positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("50.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        mock_public_api_client.get_market_data.side_effect = Exception("API Error")
        
        with pytest.raises(TradingError, match="Failed to update prices"):
            await trading_service.update_position_prices("test-account-123")


class TestTradeValidation:
    """Test trade validation methods."""
    
    def test_validate_trade_data_valid(self, trading_service):
        """Test trade data validation with valid data."""
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        result = trading_service._validate_trade_data(trade_details)
        
        assert result is True
    
    def test_validate_trade_data_missing_symbol(self, trading_service):
        """Test trade data validation with missing symbol."""
        trade_details = {
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        result = trading_service._validate_trade_data(trade_details)
        
        assert result is False
    
    def test_validate_trade_data_invalid_quantity(self, trading_service):
        """Test trade data validation with invalid quantity."""
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": -100,  # Negative quantity
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        result = trading_service._validate_trade_data(trade_details)
        
        assert result is False
    
    def test_validate_trade_data_invalid_price(self, trading_service):
        """Test trade data validation with invalid price."""
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("-400.00"),  # Negative price
            "order_type": "MARKET"
        }
        
        result = trading_service._validate_trade_data(trade_details)
        
        assert result is False
    
    def test_validate_trade_data_invalid_action(self, trading_service):
        """Test trade data validation with invalid action."""
        trade_details = {
            "symbol": "SPY",
            "action": "INVALID",  # Invalid action
            "quantity": 100,
            "price": Decimal("400.00"),
            "order_type": "MARKET"
        }
        
        result = trading_service._validate_trade_data(trade_details)
        
        assert result is False
