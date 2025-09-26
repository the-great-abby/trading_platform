"""
Unit tests for position service.

Tests position tracking, P&L calculations, and position management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from src.services.live_trading.position_service import (
    PositionService, PositionNotFoundError, PositionCalculationError
)
from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade,
    StrategyType, TradeAction, TradeStatus, PositionStatus
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
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
        status=PositionStatus.OPEN,
        opened_at=datetime.now(timezone.utc),
        expiration_date=datetime.now(timezone.utc).replace(day=30),
        legs_data='[{"strike": 400, "type": "CALL", "action": "SELL"}]',
        greeks_data='{"delta": 0.5, "gamma": 0.1}'
    )


@pytest.fixture
def sample_trades():
    """Create sample trades."""
    return [
        LiveTrade(
            trade_id=str(uuid.uuid4()),
            account_id="test-account-123",
            public_order_id="order_1",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=10,
            price=Decimal("400.00"),
            total_amount=Decimal("4000.00"),
            filled_quantity=10,
            remaining_quantity=0,
            status=TradeStatus.FILLED,
            strategy=StrategyType.IRON_CONDOR,
            filled_at=datetime.now(timezone.utc)
        ),
        LiveTrade(
            trade_id=str(uuid.uuid4()),
            account_id="test-account-123",
            public_order_id="order_2",
            symbol="SPY",
            action=TradeAction.SELL,
            quantity=5,
            price=Decimal("410.00"),
            total_amount=Decimal("2050.00"),
            filled_quantity=5,
            remaining_quantity=0,
            status=TradeStatus.FILLED,
            strategy=StrategyType.IRON_CONDOR,
            filled_at=datetime.now(timezone.utc)
        )
    ]


@pytest.fixture
def position_service(mock_db_session):
    """Create position service instance."""
    return PositionService(mock_db_session)


class TestPositionRetrieval:
    """Test position retrieval methods."""
    
    @pytest.mark.asyncio
    async def test_get_position_success(self, position_service, mock_db_session, sample_position):
        """Test successful position retrieval."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        result = await position_service.get_position("test-account-123", "SPY")
        
        assert result["symbol"] == "SPY"
        assert result["quantity"] == 10
        assert result["average_price"] == Decimal("400.00")
        assert result["current_price"] == Decimal("405.00")
        assert result["unrealized_pnl"] == Decimal("50.00")
        assert result["strategy"] == StrategyType.IRON_CONDOR
    
    @pytest.mark.asyncio
    async def test_get_position_not_found(self, position_service, mock_db_session):
        """Test position retrieval when not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(PositionNotFoundError, match="Position not found"):
            await position_service.get_position("test-account-123", "NONEXISTENT")
    
    @pytest.mark.asyncio
    async def test_get_all_positions(self, position_service, mock_db_session):
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
        
        result = await position_service.get_all_positions("test-account-123")
        
        assert len(result) == 2
        assert result[0]["symbol"] == "SPY"
        assert result[1]["symbol"] == "QQQ"
    
    @pytest.mark.asyncio
    async def test_get_positions_by_strategy(self, position_service, mock_db_session):
        """Test getting positions by strategy."""
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
        
        result = await position_service.get_positions_by_strategy("test-account-123", StrategyType.IRON_CONDOR)
        
        assert len(result) == 1
        assert result[0]["symbol"] == "SPY"
        assert result[0]["strategy"] == StrategyType.IRON_CONDOR
    
    @pytest.mark.asyncio
    async def test_get_open_positions(self, position_service, mock_db_session):
        """Test getting only open positions."""
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
                quantity=0,
                average_price=Decimal("300.00"),
                current_price=Decimal("295.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("100.00"),
                status=PositionStatus.CLOSED
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        
        result = await position_service.get_open_positions("test-account-123")
        
        assert len(result) == 1
        assert result[0]["symbol"] == "SPY"
        assert result[0]["status"] == PositionStatus.OPEN


class TestPositionCreation:
    """Test position creation methods."""
    
    @pytest.mark.asyncio
    async def test_create_position_new(self, position_service, mock_db_session, sample_account):
        """Test creating a new position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing position
        
        position_data = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": 100,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("400.00"),
            "legs_data": '[{"strike": 400, "type": "CALL", "action": "SELL"}]',
            "greeks_data": '{"delta": 0.5, "gamma": 0.1}'
        }
        
        result = await position_service.create_position("test-account-123", position_data)
        
        assert result["symbol"] == "SPY"
        assert result["quantity"] == 100
        assert result["average_price"] == Decimal("400.00")
        assert result["strategy"] == StrategyType.IRON_CONDOR
        assert result["status"] == PositionStatus.OPEN
        
        # Verify position was created
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_position_existing(self, position_service, mock_db_session, sample_position):
        """Test creating position when one already exists."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        position_data = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": 50,
            "average_price": Decimal("410.00"),
            "current_price": Decimal("410.00")
        }
        
        with pytest.raises(PositionCalculationError, match="Position already exists"):
            await position_service.create_position("test-account-123", position_data)


class TestPositionUpdates:
    """Test position update methods."""
    
    @pytest.mark.asyncio
    async def test_update_position_quantity_increase(self, position_service, mock_db_session, sample_position):
        """Test updating position quantity (increase)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        update_data = {
            "quantity": 50,  # Adding 40 to existing 10
            "price": Decimal("410.00")
        }
        
        result = await position_service.update_position_quantity("test-account-123", "SPY", update_data)
        
        # New quantity: 10 + 40 = 50
        # New average price: ((10 * 400) + (40 * 410)) / 50 = (4000 + 16400) / 50 = 408.00
        assert result["quantity"] == 50
        assert result["average_price"] == Decimal("408.00")
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_quantity_decrease(self, position_service, mock_db_session, sample_position):
        """Test updating position quantity (decrease)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        update_data = {
            "quantity": 5,  # Reducing from 10 to 5
            "price": Decimal("410.00")
        }
        
        result = await position_service.update_position_quantity("test-account-123", "SPY", update_data)
        
        assert result["quantity"] == 5
        assert result["average_price"] == Decimal("400.00")  # Average price remains the same
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_quantity_close(self, position_service, mock_db_session, sample_position):
        """Test updating position quantity to close position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        update_data = {
            "quantity": 0,  # Closing position
            "price": Decimal("410.00")
        }
        
        result = await position_service.update_position_quantity("test-account-123", "SPY", update_data)
        
        assert result["quantity"] == 0
        assert result["status"] == PositionStatus.CLOSED
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_prices(self, position_service, mock_db_session, sample_position):
        """Test updating position prices."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        price_data = {
            "current_price": Decimal("415.00"),
            "bid": Decimal("414.95"),
            "ask": Decimal("415.05")
        }
        
        result = await position_service.update_position_prices("test-account-123", "SPY", price_data)
        
        assert result["current_price"] == Decimal("415.00")
        assert result["unrealized_pnl"] == Decimal("150.00")  # (415 - 400) * 10
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_greeks(self, position_service, mock_db_session, sample_position):
        """Test updating position Greeks."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position
        
        greeks_data = {
            "delta": 0.6,
            "gamma": 0.15,
            "theta": -0.05,
            "vega": 0.3
        }
        
        result = await position_service.update_position_greeks("test-account-123", "SPY", greeks_data)
        
        assert result["greeks_data"] == '{"delta": 0.6, "gamma": 0.15, "theta": -0.05, "vega": 0.3}'
        
        # Verify position was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_position_not_found(self, position_service, mock_db_session):
        """Test updating position when not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        update_data = {
            "quantity": 50,
            "price": Decimal("410.00")
        }
        
        with pytest.raises(PositionNotFoundError, match="Position not found"):
            await position_service.update_position_quantity("test-account-123", "NONEXISTENT", update_data)


class TestPositionCalculations:
    """Test position calculation methods."""
    
    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl(self, position_service):
        """Test calculating unrealized P&L."""
        position_data = {
            "quantity": 10,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        unrealized_pnl = await position_service.calculate_unrealized_pnl(position_data)
        
        assert unrealized_pnl == Decimal("50.00")  # (405 - 400) * 10
    
    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl_negative(self, position_service):
        """Test calculating unrealized P&L (negative)."""
        position_data = {
            "quantity": 10,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("395.00")
        }
        
        unrealized_pnl = await position_service.calculate_unrealized_pnl(position_data)
        
        assert unrealized_pnl == Decimal("-50.00")  # (395 - 400) * 10
    
    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl_zero_quantity(self, position_service):
        """Test calculating unrealized P&L with zero quantity."""
        position_data = {
            "quantity": 0,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        unrealized_pnl = await position_service.calculate_unrealized_pnl(position_data)
        
        assert unrealized_pnl == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_calculate_average_price(self, position_service):
        """Test calculating average price for position updates."""
        existing_position = {
            "quantity": 10,
            "average_price": Decimal("400.00")
        }
        
        new_trade = {
            "quantity": 20,
            "price": Decimal("410.00")
        }
        
        new_average_price = await position_service.calculate_average_price(existing_position, new_trade)
        
        # (10 * 400 + 20 * 410) / (10 + 20) = (4000 + 8200) / 30 = 406.67
        assert new_average_price == Decimal("406.67")
    
    @pytest.mark.asyncio
    async def test_calculate_average_price_first_trade(self, position_service):
        """Test calculating average price for first trade."""
        existing_position = {
            "quantity": 0,
            "average_price": Decimal("0.00")
        }
        
        new_trade = {
            "quantity": 100,
            "price": Decimal("400.00")
        }
        
        new_average_price = await position_service.calculate_average_price(existing_position, new_trade)
        
        assert new_average_price == Decimal("400.00")
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(self, position_service, mock_db_session):
        """Test calculating total portfolio value."""
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
        
        portfolio_value = await position_service.calculate_portfolio_value("test-account-123")
        
        # SPY: 10 * 405.00 = 4050.00
        # QQQ: 5 * 295.00 = 1475.00
        # Total: 5525.00
        assert portfolio_value == Decimal("5525.00")
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_pnl(self, position_service, mock_db_session):
        """Test calculating total portfolio P&L."""
        positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("50.00"),
                realized_pnl=Decimal("100.00"),
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
        
        portfolio_pnl = await position_service.calculate_portfolio_pnl("test-account-123")
        
        assert portfolio_pnl["total_unrealized_pnl"] == Decimal("25.00")  # 50 + (-25)
        assert portfolio_pnl["total_realized_pnl"] == Decimal("175.00")   # 100 + 75
        assert portfolio_pnl["total_pnl"] == Decimal("200.00")           # 25 + 175
        assert portfolio_pnl["position_count"] == 2


class TestPositionHistory:
    """Test position history methods."""
    
    @pytest.mark.asyncio
    async def test_get_position_history(self, position_service, mock_db_session):
        """Test getting position history."""
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
                status=PositionStatus.OPEN,
                created_at=datetime.now(timezone.utc)
            ),
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=0,
                average_price=Decimal("400.00"),
                current_price=Decimal("410.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("100.00"),
                status=PositionStatus.CLOSED,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = positions
        
        result = await position_service.get_position_history("test-account-123", "SPY")
        
        assert len(result) == 2
        assert result[0]["status"] == PositionStatus.OPEN
        assert result[1]["status"] == PositionStatus.CLOSED
    
    @pytest.mark.asyncio
    async def test_get_position_trades(self, position_service, mock_db_session, sample_trades):
        """Test getting trades for a position."""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_trades
        
        result = await position_service.get_position_trades("test-account-123", "SPY")
        
        assert len(result) == 2
        assert result[0]["action"] == TradeAction.BUY
        assert result[1]["action"] == TradeAction.SELL


class TestPositionValidation:
    """Test position validation methods."""
    
    def test_validate_position_data_valid(self, position_service):
        """Test position data validation with valid data."""
        position_data = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": 100,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        result = position_service._validate_position_data(position_data)
        
        assert result is True
    
    def test_validate_position_data_missing_symbol(self, position_service):
        """Test position data validation with missing symbol."""
        position_data = {
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": 100,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        result = position_service._validate_position_data(position_data)
        
        assert result is False
    
    def test_validate_position_data_invalid_quantity(self, position_service):
        """Test position data validation with invalid quantity."""
        position_data = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": -100,  # Negative quantity
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        result = position_service._validate_position_data(position_data)
        
        assert result is False
    
    def test_validate_position_data_invalid_price(self, position_service):
        """Test position data validation with invalid price."""
        position_data = {
            "symbol": "SPY",
            "strategy": StrategyType.IRON_CONDOR,
            "quantity": 100,
            "average_price": Decimal("-400.00"),  # Negative price
            "current_price": Decimal("405.00")
        }
        
        result = position_service._validate_position_data(position_data)
        
        assert result is False
    
    def test_validate_position_data_invalid_strategy(self, position_service):
        """Test position data validation with invalid strategy."""
        position_data = {
            "symbol": "SPY",
            "strategy": "INVALID_STRATEGY",
            "quantity": 100,
            "average_price": Decimal("400.00"),
            "current_price": Decimal("405.00")
        }
        
        result = position_service._validate_position_data(position_data)
        
        assert result is False


class TestPositionCleanup:
    """Test position cleanup methods."""
    
    @pytest.mark.asyncio
    async def test_close_expired_positions(self, position_service, mock_db_session):
        """Test closing expired positions."""
        expired_positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=10,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("50.00"),
                realized_pnl=Decimal("0.00"),
                status=PositionStatus.OPEN,
                expiration_date=datetime.now(timezone.utc).replace(day=1)  # Expired
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = expired_positions
        
        result = await position_service.close_expired_positions()
        
        assert len(result) == 1
        assert result[0]["status"] == PositionStatus.CLOSED
        
        # Verify positions were updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_zero_quantity_positions(self, position_service, mock_db_session):
        """Test cleaning up zero quantity positions."""
        zero_positions = [
            LivePosition(
                account_id="test-account-123",
                symbol="SPY",
                strategy=StrategyType.IRON_CONDOR,
                quantity=0,
                average_price=Decimal("400.00"),
                current_price=Decimal("405.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("100.00"),
                status=PositionStatus.OPEN
            )
        ]
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = zero_positions
        
        result = await position_service.cleanup_zero_quantity_positions()
        
        assert len(result) == 1
        assert result[0]["status"] == PositionStatus.CLOSED
        
        # Verify positions were updated
        mock_db_session.commit.assert_called()


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_create_position_invalid_data(self, position_service):
        """Test creating position with invalid data."""
        position_data = {
            "symbol": "SPY",
            # Missing required fields
        }
        
        with pytest.raises(PositionCalculationError, match="Invalid position data"):
            await position_service.create_position("test-account-123", position_data)
    
    @pytest.mark.asyncio
    async def test_update_position_database_error(self, position_service, mock_db_session):
        """Test updating position with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        
        update_data = {
            "quantity": 50,
            "price": Decimal("410.00")
        }
        
        with pytest.raises(PositionCalculationError, match="Database error"):
            await position_service.update_position_quantity("test-account-123", "SPY", update_data)
    
    @pytest.mark.asyncio
    async def test_calculate_pnl_invalid_data(self, position_service):
        """Test calculating P&L with invalid data."""
        position_data = {
            "quantity": 10,
            "average_price": Decimal("400.00"),
            # Missing current_price
        }
        
        with pytest.raises(PositionCalculationError, match="Invalid position data"):
            await position_service.calculate_unrealized_pnl(position_data)
    
    @pytest.mark.asyncio
    async def test_calculate_average_price_invalid_data(self, position_service):
        """Test calculating average price with invalid data."""
        existing_position = {
            "quantity": 10,
            "average_price": Decimal("400.00")
        }
        
        new_trade = {
            "quantity": -20,  # Invalid negative quantity
            "price": Decimal("410.00")
        }
        
        with pytest.raises(PositionCalculationError, match="Invalid trade data"):
            await position_service.calculate_average_price(existing_position, new_trade)
