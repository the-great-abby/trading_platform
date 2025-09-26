"""
Integration tests for live trading system.

Tests end-to-end workflows, service interactions, and system integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from src.services.live_trading.trading_service import TradingService
from src.services.live_trading.risk_service import RiskService
from src.services.live_trading.position_service import PositionService
from src.services.live_trading.system_service import SystemService
from src.services.live_trading.market_hours_service import MarketHoursService
from src.services.live_trading.public_api_client import PublicAPIClient
from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    return AsyncMock()


@pytest.fixture
def mock_public_api_client():
    """Create mock Public.com API client."""
    return AsyncMock(spec=PublicAPIClient)


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
def trading_service(mock_db_session, mock_public_api_client, mock_redis_client):
    """Create trading service with all dependencies."""
    risk_service = RiskService(mock_db_session)
    market_hours_service = MarketHoursService()
    system_service = SystemService(mock_db_session, mock_redis_client)
    
    return TradingService(
        db_session=mock_db_session,
        public_api_client=mock_public_api_client,
        risk_service=risk_service,
        market_hours_service=market_hours_service,
        system_service=system_service
    )


class TestEndToEndTradingWorkflow:
    """Test complete trading workflows from start to finish."""
    
    @pytest.mark.asyncio
    async def test_complete_iron_condor_workflow(self, trading_service, mock_db_session, 
                                               mock_public_api_client, mock_redis_client, 
                                               sample_account, sample_risk_profile):
        """Test complete Iron Condor trading workflow."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []  # No existing positions
        mock_db_session.execute.return_value.scalar.return_value = 0  # No trades today
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response
            mock_public_api_client.execute_order.return_value = {
                "order_id": "iron_condor_123",
                "status": "FILLED",
                "filled_quantity": 10,
                "average_price": 2.50
            }
            
            # Mock Redis for emergency stop check
            mock_redis_client.get.return_value = None  # No emergency stop
            
            # Execute Iron Condor trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 10,
                "price": Decimal("2.50"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR,
                "legs_data": '[{"strike": 400, "type": "CALL", "action": "SELL"}]',
                "greeks_data": '{"delta": 0.5, "gamma": 0.1}'
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["order_id"] == "iron_condor_123"
            assert result["status"] == "FILLED"
            
            # Verify position was created
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_butterfly_spread_workflow(self, trading_service, mock_db_session, 
                                                    mock_public_api_client, mock_redis_client,
                                                    sample_account, sample_risk_profile):
        """Test complete Butterfly Spread trading workflow."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response
            mock_public_api_client.execute_order.return_value = {
                "order_id": "butterfly_456",
                "status": "FILLED",
                "filled_quantity": 5,
                "average_price": 1.75
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute Butterfly Spread trade
            trade_details = {
                "symbol": "QQQ",
                "action": TradeAction.BUY,
                "quantity": 5,
                "price": Decimal("1.75"),
                "order_type": "MARKET",
                "strategy": StrategyType.BUTTERFLY_SPREAD,
                "legs_data": '[{"strike": 300, "type": "CALL", "action": "BUY"}]',
                "greeks_data": '{"delta": 0.3, "gamma": 0.05}'
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["order_id"] == "butterfly_456"
            assert result["status"] == "FILLED"
    
    @pytest.mark.asyncio
    async def test_complete_calendar_spread_workflow(self, trading_service, mock_db_session, 
                                                   mock_public_api_client, mock_redis_client,
                                                   sample_account, sample_risk_profile):
        """Test complete Calendar Spread trading workflow."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response
            mock_public_api_client.execute_order.return_value = {
                "order_id": "calendar_789",
                "status": "FILLED",
                "filled_quantity": 3,
                "average_price": 3.25
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute Calendar Spread trade
            trade_details = {
                "symbol": "AAPL",
                "action": TradeAction.BUY,
                "quantity": 3,
                "price": Decimal("3.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.CALENDAR_SPREAD,
                "legs_data": '[{"strike": 150, "type": "CALL", "action": "BUY"}]',
                "greeks_data": '{"delta": 0.4, "gamma": 0.08}'
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["order_id"] == "calendar_789"
            assert result["status"] == "FILLED"


class TestRiskManagementIntegration:
    """Test risk management integration across services."""
    
    @pytest.mark.asyncio
    async def test_risk_check_failure_prevents_trade(self, trading_service, mock_db_session, 
                                                   mock_public_api_client, mock_redis_client,
                                                   sample_account, sample_risk_profile):
        """Test that risk check failures prevent trade execution."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            mock_redis_client.get.return_value = None
            
            # Try to execute a trade that exceeds risk limits
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 15000,  # Exceeds max_position_size of 10000
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Risk check failed"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api_client.execute_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_emergency_stop_prevents_trade(self, trading_service, mock_db_session, 
                                               mock_public_api_client, mock_redis_client,
                                               sample_account, sample_risk_profile):
        """Test that emergency stop prevents trade execution."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock emergency stop active
            mock_redis_client.get.return_value = "true"
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Emergency stop active"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api_client.execute_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_market_hours_prevents_trade(self, trading_service, mock_db_session, 
                                             mock_public_api_client, mock_redis_client,
                                             sample_account, sample_risk_profile):
        """Test that market hours prevent trade execution."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market closed
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=False):
            mock_redis_client.get.return_value = None
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Market is closed"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api_client.execute_order.assert_not_called()


class TestPositionManagementIntegration:
    """Test position management integration."""
    
    @pytest.mark.asyncio
    async def test_position_creation_and_update(self, trading_service, mock_db_session, 
                                              mock_public_api_client, mock_redis_client,
                                              sample_account, sample_risk_profile):
        """Test position creation and updates through trading workflow."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []  # No existing positions
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response
            mock_public_api_client.execute_order.return_value = {
                "order_id": "position_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute first trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 100
            
            # Verify position was created
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_position_reduction_and_closure(self, trading_service, mock_db_session, 
                                                mock_public_api_client, mock_redis_client,
                                                sample_account, sample_risk_profile):
        """Test position reduction and closure through trading workflow."""
        # Create existing position
        existing_position = LivePosition(
            account_id="test-account-123",
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=100,
            average_price=Decimal("400.00"),
            current_price=Decimal("405.00"),
            unrealized_pnl=Decimal("500.00"),
            realized_pnl=Decimal("0.00"),
            status=PositionStatus.OPEN
        )
        
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [existing_position]
        mock_db_session.execute.return_value.scalar.return_value = 1
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response for partial close
            mock_public_api_client.execute_order.return_value = {
                "order_id": "partial_close_123",
                "status": "FILLED",
                "filled_quantity": 50,
                "average_price": 410.00
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute partial close trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.SELL,
                "quantity": 50,
                "price": Decimal("410.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 50
            
            # Verify position was updated
            mock_db_session.commit.assert_called()


class TestOrderManagementIntegration:
    """Test order management integration."""
    
    @pytest.mark.asyncio
    async def test_order_cancellation_workflow(self, trading_service, mock_db_session, 
                                             mock_public_api_client, mock_redis_client):
        """Test complete order cancellation workflow."""
        # Create existing order
        existing_order = OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="test-account-123",
            order_id="cancel_test_123",
            status="PENDING",
            symbol="SPY",
            order_type="LIMIT",
            side="BUY",
            quantity=100,
            filled_quantity=0,
            remaining_quantity=100,
            price=Decimal("395.00")
        )
        
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_order
        
        # Mock Public.com API response
        mock_public_api_client.cancel_order.return_value = {
            "order_id": "cancel_test_123",
            "status": "CANCELLED"
        }
        
        # Execute order cancellation
        result = await trading_service.cancel_order("test-account-123", "cancel_test_123")
        
        assert result["success"] is True
        assert result["status"] == "CANCELLED"
        
        # Verify API was called
        mock_public_api_client.cancel_order.assert_called_once_with("cancel_test_123")
        
        # Verify database was updated
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_order_status_tracking(self, trading_service, mock_db_session):
        """Test order status tracking and updates."""
        # Create existing order
        existing_order = OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="test-account-123",
            order_id="status_test_123",
            status="FILLED",
            symbol="SPY",
            order_type="MARKET",
            side="BUY",
            quantity=100,
            filled_quantity=100,
            remaining_quantity=0,
            average_price=Decimal("400.25")
        )
        
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_order
        
        # Get order status
        result = await trading_service.get_order_status("test-account-123", "status_test_123")
        
        assert result["order_id"] == "status_test_123"
        assert result["status"] == "FILLED"
        assert result["filled_quantity"] == 100
        assert result["remaining_quantity"] == 0
        assert result["average_price"] == Decimal("400.25")


class TestSystemIntegration:
    """Test system-level integration."""
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, trading_service, mock_db_session, 
                                          mock_public_api_client, mock_redis_client):
        """Test system health monitoring across all services."""
        # Setup mocks for health check
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = None  # No emergency stop
        
        # Perform health check
        result = await trading_service.system_service.perform_health_check()
        
        assert result["overall_status"] == "healthy"
        assert result["checks"]["database"] == "healthy"
        assert result["checks"]["redis"] == "healthy"
        assert result["checks"]["emergency_stop"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_emergency_stop_workflow(self, trading_service, mock_db_session, 
                                         mock_public_api_client, mock_redis_client,
                                         sample_risk_profile):
        """Test complete emergency stop workflow."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        # Activate emergency stop
        result = await trading_service.system_service.activate_emergency_stop("test-account-123", "Test emergency")
        
        assert result["success"] is True
        assert result["status"] == "activated"
        assert result["reason"] == "Test emergency"
        
        # Verify Redis was updated
        mock_redis_client.set.assert_called_with(
            "emergency_stop:test-account-123",
            "true",
            ex=None
        )
        
        # Verify database was updated
        assert sample_risk_profile.emergency_stop_active is True
        mock_db_session.commit.assert_called()
        
        # Check emergency stop status
        mock_redis_client.get.return_value = "true"
        is_active = await trading_service.system_service.check_emergency_stop("test-account-123")
        assert is_active is True
        
        # Deactivate emergency stop
        result = await trading_service.system_service.deactivate_emergency_stop("test-account-123")
        
        assert result["success"] is True
        assert result["status"] == "deactivated"
        
        # Verify Redis was updated
        mock_redis_client.delete.assert_called_with("emergency_stop:test-account-123")
        
        # Verify database was updated
        assert sample_risk_profile.emergency_stop_active is False
        mock_db_session.commit.assert_called()


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_api_failure_recovery(self, trading_service, mock_db_session, 
                                      mock_public_api_client, mock_redis_client,
                                      sample_account, sample_risk_profile):
        """Test recovery from API failures."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            mock_redis_client.get.return_value = None
            
            # Mock API failure
            mock_public_api_client.execute_order.side_effect = Exception("API connection error")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="API connection error"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify database rollback occurred
            mock_db_session.rollback.assert_called()
    
    @pytest.mark.asyncio
    async def test_database_failure_recovery(self, trading_service, mock_db_session, 
                                           mock_public_api_client, mock_redis_client,
                                           sample_account, sample_risk_profile):
        """Test recovery from database failures."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            mock_redis_client.get.return_value = None
            
            # Mock Public.com API success
            mock_public_api_client.execute_order.return_value = {
                "order_id": "db_failure_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Mock database failure on commit
            mock_db_session.commit.side_effect = Exception("Database connection lost")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Database connection lost"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify rollback occurred
            mock_db_session.rollback.assert_called()
    
    @pytest.mark.asyncio
    async def test_redis_failure_recovery(self, trading_service, mock_db_session, 
                                        mock_public_api_client, mock_redis_client,
                                        sample_account, sample_risk_profile):
        """Test recovery from Redis failures."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Redis failure
            mock_redis_client.get.side_effect = Exception("Redis connection error")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Redis connection error"):
                await trading_service.execute_trade("test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api_client.execute_order.assert_not_called()


class TestPerformanceIntegration:
    """Test performance and scalability."""
    
    @pytest.mark.asyncio
    async def test_concurrent_trade_execution(self, trading_service, mock_db_session, 
                                            mock_public_api_client, mock_redis_client,
                                            sample_account, sample_risk_profile):
        """Test concurrent trade execution handling."""
        import asyncio
        
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API responses
            mock_public_api_client.execute_order.return_value = {
                "order_id": "concurrent_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute multiple trades concurrently
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            # Create multiple concurrent tasks
            tasks = [
                trading_service.execute_trade("test-account-123", trade_details)
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all trades were processed
            assert len(results) == 5
            for result in results:
                if isinstance(result, Exception):
                    # Some trades might fail due to risk limits or other constraints
                    assert "Risk check failed" in str(result) or "Position size" in str(result)
                else:
                    assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_large_volume_trade_handling(self, trading_service, mock_db_session, 
                                             mock_public_api_client, mock_redis_client,
                                             sample_account, sample_risk_profile):
        """Test handling of large volume trades."""
        # Setup mocks
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value.scalar.return_value = 0
        
        # Mock market hours
        with patch.object(trading_service.market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response for large trade
            mock_public_api_client.execute_order.return_value = {
                "order_id": "large_volume_test_123",
                "status": "FILLED",
                "filled_quantity": 1000,
                "average_price": 400.25
            }
            
            mock_redis_client.get.return_value = None
            
            # Execute large volume trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 1000,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 1000
            
            # Verify position was created with correct quantity
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called()
