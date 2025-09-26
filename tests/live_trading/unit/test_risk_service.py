"""
Unit tests for risk management service.

Tests risk calculations, position sizing, and risk limit enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from src.services.live_trading.risk_service import (
    RiskService, RiskCalculationError, RiskLimitExceededError
)
from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, RiskProfile, LiveTrade,
    StrategyType, TradeAction, TradeStatus, RiskLevel
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
def sample_risk_profile():
    """Create sample risk profile."""
    return RiskProfile(
        account_id="test-account-123",
        max_position_size=10000.0,
        max_portfolio_risk=0.05,
        max_daily_loss=1000.0,
        max_daily_trades=20,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
        max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )


@pytest.fixture
def sample_positions():
    """Create sample positions."""
    return [
        LivePosition(
            account_id="test-account-123",
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=10,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            unrealized_pnl=Decimal("50.00"),
            realized_pnl=Decimal("0.00"),
            status="OPEN"
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
            status="OPEN"
        )
    ]


@pytest.fixture
def risk_service(mock_db_session):
    """Create risk service instance."""
    return RiskService(mock_db_session)


class TestRiskProfileManagement:
    """Test risk profile management methods."""
    
    @pytest.mark.asyncio
    async def test_get_risk_profile_success(self, risk_service, mock_db_session, sample_risk_profile):
        """Test successful risk profile retrieval."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await risk_service.get_risk_profile("test-account-123")
        
        assert result is not None
        assert result.account_id == "test-account-123"
        assert result.max_position_size == 10000.0
        assert result.max_portfolio_risk == 0.05
    
    @pytest.mark.asyncio
    async def test_get_risk_profile_not_found(self, risk_service, mock_db_session):
        """Test risk profile retrieval when not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await risk_service.get_risk_profile("nonexistent-account")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_risk_profile(self, risk_service, mock_db_session):
        """Test risk profile creation."""
        risk_data = {
            "account_id": "new-account-123",
            "max_position_size": 5000.0,
            "max_portfolio_risk": 0.03,
            "max_daily_loss": 500.0,
            "max_daily_trades": 10,
            "risk_level": RiskLevel.CONSERVATIVE
        }
        
        await risk_service.create_risk_profile(risk_data)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_risk_profile(self, risk_service, mock_db_session, sample_risk_profile):
        """Test risk profile updates."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        updates = {
            "max_position_size": 15000.0,
            "max_daily_loss": 1500.0
        }
        
        result = await risk_service.update_risk_profile("test-account-123", updates)
        
        assert result.max_position_size == 15000.0
        assert result.max_daily_loss == 1500.0
        mock_db_session.commit.assert_called_once()


class TestPositionRiskChecks:
    """Test position-level risk checks."""
    
    @pytest.mark.asyncio
    async def test_check_position_size_within_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test position size check within limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_position_size("test-account-123", trade_details)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_position_size_exceeds_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test position size check exceeding limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 15000,  # Exceeds max_position_size of 10000
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_position_size("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_position_size_with_existing_position(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test position size check with existing positions."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 5000,  # Would make total 15000 (10000 existing + 5000 new)
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_position_size("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_position_size_sell_reduces_position(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test position size check when selling reduces position."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 5,  # Selling 5 contracts (reduces from 10 to 5)
            "price": Decimal("400.00"),
            "side": "SELL"
        }
        
        result = await risk_service.check_position_size("test-account-123", trade_details)
        
        assert result is True


class TestPortfolioRiskChecks:
    """Test portfolio-level risk checks."""
    
    @pytest.mark.asyncio
    async def test_check_portfolio_risk_within_limit(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test portfolio risk check within limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        trade_details = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": Decimal("150.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_portfolio_risk("test-account-123", trade_details)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_portfolio_risk_exceeds_limit(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test portfolio risk check exceeding limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        # Create a large trade that would exceed portfolio risk
        trade_details = {
            "symbol": "AAPL",
            "quantity": 100000,  # Very large quantity
            "price": Decimal("150.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_portfolio_risk("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(self, risk_service, mock_db_session, sample_positions):
        """Test portfolio value calculation."""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        portfolio_value = await risk_service.calculate_portfolio_value("test-account-123")
        
        # SPY: 10 * 405.00 = 4050.00
        # QQQ: 5 * 295.00 = 1475.00
        # Total: 5525.00
        assert portfolio_value == Decimal("5525.00")
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_risk(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test portfolio risk calculation."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        risk_percentage = await risk_service.calculate_portfolio_risk("test-account-123")
        
        # Portfolio value: 5525.00
        # Max portfolio risk: 0.05 (5%)
        # Expected risk: 5525.00 * 0.05 = 276.25
        assert risk_percentage == Decimal("0.05")


class TestDailyRiskChecks:
    """Test daily risk limit checks."""
    
    @pytest.mark.asyncio
    async def test_check_daily_loss_limit_within_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test daily loss limit check within limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []  # No trades today
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        result = await risk_service.check_daily_loss_limit("test-account-123", trade_details)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_daily_loss_limit_exceeds_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test daily loss limit check exceeding limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        # Mock existing trades with large losses
        existing_trades = [
            LiveTrade(
                account_id="test-account-123",
                symbol="SPY",
                action=TradeAction.SELL,
                quantity=100,
                price=Decimal("390.00"),  # Sold at 390
                total_amount=Decimal("39000.00"),
                filled_quantity=100,
                remaining_quantity=0,
                status=TradeStatus.FILLED
            )
        ]
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = existing_trades
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("380.00"),  # Buying at 380 (losing 10 per share)
            "side": "BUY"
        }
        
        result = await risk_service.check_daily_loss_limit("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_daily_trade_limit_within_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test daily trade limit check within limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalar.return_value = 5  # 5 trades today
        
        result = await risk_service.check_daily_trade_limit("test-account-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_daily_trade_limit_exceeds_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test daily trade limit check exceeding limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalar.return_value = 25  # 25 trades today (exceeds limit of 20)
        
        result = await risk_service.check_daily_trade_limit("test-account-123")
        
        assert result is False


class TestGreeksRiskChecks:
    """Test Greeks-based risk checks."""
    
    @pytest.mark.asyncio
    async def test_check_greeks_exposure_within_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test Greeks exposure check within limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY",
            "greeks": {"delta": 50.0, "gamma": 5.0}
        }
        
        result = await risk_service.check_greeks_exposure("test-account-123", trade_details)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_greeks_exposure_exceeds_limit(self, risk_service, mock_db_session, sample_risk_profile):
        """Test Greeks exposure check exceeding limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY",
            "greeks": {"delta": 1500.0, "gamma": 150.0}  # Exceeds limits
        }
        
        result = await risk_service.check_greeks_exposure("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_greeks_exposure_with_existing_positions(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test Greeks exposure check with existing positions."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        # Mock existing positions with Greeks data
        sample_positions[0].greeks_data = '{"delta": 500.0, "gamma": 50.0}'
        sample_positions[1].greeks_data = '{"delta": 200.0, "gamma": 20.0}'
        
        trade_details = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": Decimal("150.00"),
            "side": "BUY",
            "greeks": {"delta": 400.0, "gamma": 40.0}  # Would exceed delta limit (500+200+400=1100 > 1000)
        }
        
        result = await risk_service.check_greeks_exposure("test-account-123", trade_details)
        
        assert result is False


class TestStrategyRiskChecks:
    """Test strategy-specific risk checks."""
    
    @pytest.mark.asyncio
    async def test_check_strategy_allowed(self, risk_service, mock_db_session, sample_risk_profile):
        """Test allowed strategy check."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await risk_service.check_strategy_allowed("test-account-123", trade_details)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_strategy_not_allowed(self, risk_service, mock_db_session, sample_risk_profile):
        """Test not allowed strategy check."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY",
            "strategy": StrategyType.CALENDAR_SPREAD  # Not in allowed_strategies
        }
        
        result = await risk_service.check_strategy_allowed("test-account-123", trade_details)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_strategy_concentration(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test strategy concentration limits."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        
        trade_details = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": Decimal("150.00"),
            "side": "BUY",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await risk_service.check_strategy_concentration("test-account-123", trade_details)
        
        assert result is True


class TestEmergencyStop:
    """Test emergency stop functionality."""
    
    @pytest.mark.asyncio
    async def test_check_emergency_stop_not_active(self, risk_service, mock_db_session, sample_risk_profile):
        """Test emergency stop check when not active."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await risk_service.check_emergency_stop("test-account-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_emergency_stop_active(self, risk_service, mock_db_session, sample_risk_profile):
        """Test emergency stop check when active."""
        sample_risk_profile.emergency_stop_active = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await risk_service.check_emergency_stop("test-account-123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_activate_emergency_stop(self, risk_service, mock_db_session, sample_risk_profile):
        """Test emergency stop activation."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        await risk_service.activate_emergency_stop("test-account-123", "Market volatility too high")
        
        assert sample_risk_profile.emergency_stop_active is True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_emergency_stop(self, risk_service, mock_db_session, sample_risk_profile):
        """Test emergency stop deactivation."""
        sample_risk_profile.emergency_stop_active = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        await risk_service.deactivate_emergency_stop("test-account-123")
        
        assert sample_risk_profile.emergency_stop_active is False
        mock_db_session.commit.assert_called_once()


class TestComprehensiveRiskCheck:
    """Test comprehensive risk checking."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_risk_check_pass(self, risk_service, mock_db_session, sample_risk_profile, sample_positions):
        """Test comprehensive risk check that passes all checks."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_positions
        mock_db_session.execute.return_value.scalar.return_value = 5  # 5 trades today
        
        trade_details = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": Decimal("150.00"),
            "side": "BUY",
            "strategy": StrategyType.IRON_CONDOR,
            "greeks": {"delta": 50.0, "gamma": 5.0}
        }
        
        result = await risk_service.comprehensive_risk_check("test-account-123", trade_details)
        
        assert result["passed"] is True
        assert "All risk checks passed" in result["message"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_risk_check_fail_position_size(self, risk_service, mock_db_session, sample_risk_profile):
        """Test comprehensive risk check that fails on position size."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 5
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 15000,  # Exceeds max_position_size
            "price": Decimal("400.00"),
            "side": "BUY",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        result = await risk_service.comprehensive_risk_check("test-account-123", trade_details)
        
        assert result["passed"] is False
        assert "position size" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_comprehensive_risk_check_fail_emergency_stop(self, risk_service, mock_db_session, sample_risk_profile):
        """Test comprehensive risk check that fails on emergency stop."""
        sample_risk_profile.emergency_stop_active = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        result = await risk_service.comprehensive_risk_check("test-account-123", trade_details)
        
        assert result["passed"] is False
        assert "emergency stop" in result["message"].lower()


class TestRiskCalculations:
    """Test risk calculation utilities."""
    
    @pytest.mark.asyncio
    async def test_calculate_var(self, risk_service):
        """Test Value at Risk calculation."""
        positions = [
            {"symbol": "SPY", "quantity": 100, "price": 400.0, "volatility": 0.20},
            {"symbol": "QQQ", "quantity": 50, "price": 300.0, "volatility": 0.25}
        ]
        
        var_95 = await risk_service.calculate_var(positions, confidence_level=0.95)
        
        assert var_95 > 0
        assert isinstance(var_95, Decimal)
    
    @pytest.mark.asyncio
    async def test_calculate_max_loss(self, risk_service):
        """Test maximum loss calculation."""
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        max_loss = await risk_service.calculate_max_loss(trade_details)
        
        # For a long position, max loss is the total cost
        assert max_loss == Decimal("40000.00")
    
    @pytest.mark.asyncio
    async def test_calculate_max_loss_short_position(self, risk_service):
        """Test maximum loss calculation for short position."""
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "SELL"
        }
        
        max_loss = await risk_service.calculate_max_loss(trade_details)
        
        # For a short position, max loss is theoretically unlimited
        # In practice, we might set a limit based on margin requirements
        assert max_loss > Decimal("40000.00")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_risk_check_no_risk_profile(self, risk_service, mock_db_session):
        """Test risk check when no risk profile exists."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        with pytest.raises(RiskCalculationError, match="No risk profile found"):
            await risk_service.comprehensive_risk_check("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_risk_check_invalid_trade_data(self, risk_service, mock_db_session, sample_risk_profile):
        """Test risk check with invalid trade data."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        trade_details = {
            "symbol": "SPY",
            # Missing required fields
        }
        
        with pytest.raises(RiskCalculationError, match="Invalid trade data"):
            await risk_service.comprehensive_risk_check("test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_risk_check_database_error(self, risk_service, mock_db_session):
        """Test risk check with database error."""
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        trade_details = {
            "symbol": "SPY",
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        with pytest.raises(RiskCalculationError, match="Database error"):
            await risk_service.comprehensive_risk_check("test-account-123", trade_details)
