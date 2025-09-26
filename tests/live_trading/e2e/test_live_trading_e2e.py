"""
End-to-end tests for live trading system.

Tests complete user workflows, API interactions, and system behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid
import json

from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def mock_database():
    """Create mock database with realistic data."""
    db = AsyncMock()
    
    # Mock account
    account = LiveTradingAccount(
        account_id="e2e-test-account-123",
        public_account_id="public-e2e-123",
        account_name="E2E Test Account",
        account_type="CASH",
        buying_power=50000.0,
        cash_balance=25000.0,
        equity=75000.0,
        is_active=True
    )
    
    # Mock risk profile
    risk_profile = RiskProfile(
        account_id="e2e-test-account-123",
        max_position_size=20000.0,
        max_portfolio_risk=0.08,
        max_daily_loss=2000.0,
        max_daily_trades=30,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD", "CALENDAR_SPREAD"]',
        max_greeks_exposure='{"delta": 2000.0, "gamma": 200.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )
    
    # Mock positions
    positions = [
        LivePosition(
            account_id="e2e-test-account-123",
            symbol="SPY",
            strategy=StrategyType.IRON_CONDOR,
            quantity=20,
            average_price=Decimal("2.50"),
            current_price=Decimal("2.75"),
            unrealized_pnl=Decimal("5.00"),
            realized_pnl=Decimal("25.00"),
            status=PositionStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
            expiration_date=datetime.now(timezone.utc).replace(day=30),
            legs_data='[{"strike": 400, "type": "CALL", "action": "SELL"}]',
            greeks_data='{"delta": 0.5, "gamma": 0.1}'
        )
    ]
    
    # Mock trades
    trades = [
        LiveTrade(
            trade_id=str(uuid.uuid4()),
            account_id="e2e-test-account-123",
            public_order_id="e2e-trade-001",
            symbol="SPY",
            action=TradeAction.BUY,
            quantity=20,
            price=Decimal("2.50"),
            total_amount=Decimal("50.00"),
            filled_quantity=20,
            remaining_quantity=0,
            status=TradeStatus.FILLED,
            strategy=StrategyType.IRON_CONDOR,
            filled_at=datetime.now(timezone.utc)
        )
    ]
    
    # Mock orders
    orders = [
        OrderStatus(
            order_status_id=str(uuid.uuid4()),
            account_id="e2e-test-account-123",
            order_id="e2e-order-001",
            status="FILLED",
            symbol="SPY",
            order_type="MARKET",
            side="BUY",
            quantity=20,
            filled_quantity=20,
            remaining_quantity=0,
            average_price=Decimal("2.50")
        )
    ]
    
    # Configure database responses
    def mock_execute(query_result):
        if hasattr(query_result, 'scalar_one_or_none'):
            if 'account' in str(query_result):
                return account
            elif 'risk_profile' in str(query_result):
                return risk_profile
            else:
                return None
        elif hasattr(query_result, 'scalars'):
            if 'position' in str(query_result):
                return positions
            elif 'trade' in str(query_result):
                return trades
            elif 'order' in str(query_result):
                return orders
            else:
                return []
        elif hasattr(query_result, 'scalar'):
            return 1  # Mock count queries
        return query_result
    
    db.execute.side_effect = mock_execute
    return db


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # No emergency stop by default
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.ping.return_value = True
    redis.info.return_value = {
        "connected_clients": 3,
        "used_memory": 2048000,
        "keyspace_hits": 5000,
        "keyspace_misses": 500
    }
    return redis


@pytest.fixture
def mock_public_api():
    """Create mock Public.com API client."""
    api = AsyncMock()
    
    # Mock authentication
    api.authenticate.return_value = {
        "access_token": "e2e_access_token_123",
        "refresh_token": "e2e_refresh_token_456",
        "expires_in": 3600
    }
    
    # Mock account info
    api.get_account_info.return_value = {
        "account_id": "public-e2e-123",
        "buying_power": 50000.0,
        "cash_balance": 25000.0,
        "equity": 75000.0
    }
    
    # Mock positions
    api.get_positions.return_value = {
        "positions": [
            {
                "symbol": "SPY",
                "quantity": 20,
                "average_price": 2.50,
                "current_price": 2.75
            }
        ]
    }
    
    # Mock market data
    api.get_market_data.return_value = {
        "symbol": "SPY",
        "price": 405.50,
        "bid": 405.45,
        "ask": 405.55,
        "volume": 1000000
    }
    
    # Mock options chain
    api.get_options_chain.return_value = {
        "symbol": "SPY",
        "expiration_dates": ["2024-01-19", "2024-01-26"],
        "strikes": [400, 405, 410],
        "options": [
            {
                "strike": 400,
                "expiration": "2024-01-19",
                "type": "CALL",
                "bid": 5.50,
                "ask": 5.75
            }
        ]
    }
    
    return api


class TestCompleteTradingWorkflow:
    """Test complete trading workflows from start to finish."""
    
    @pytest.mark.asyncio
    async def test_iron_condor_complete_workflow(self, mock_database, mock_redis, mock_public_api):
        """Test complete Iron Condor trading workflow."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_iron_condor_123",
                "status": "FILLED",
                "filled_quantity": 10,
                "average_price": 2.75
            }
            
            # Execute Iron Condor trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 10,
                "price": Decimal("2.75"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR,
                "legs_data": '[{"strike": 400, "type": "CALL", "action": "SELL"}]',
                "greeks_data": '{"delta": 0.5, "gamma": 0.1}'
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify trade execution
            assert result["success"] is True
            assert result["order_id"] == "e2e_iron_condor_123"
            assert result["status"] == "FILLED"
            assert result["filled_quantity"] == 10
            
            # Verify API was called
            mock_public_api.execute_order.assert_called_once()
            
            # Verify database operations
            mock_database.add.assert_called()
            mock_database.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_butterfly_spread_complete_workflow(self, mock_database, mock_redis, mock_public_api):
        """Test complete Butterfly Spread trading workflow."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_butterfly_456",
                "status": "FILLED",
                "filled_quantity": 5,
                "average_price": 1.85
            }
            
            # Execute Butterfly Spread trade
            trade_details = {
                "symbol": "QQQ",
                "action": TradeAction.BUY,
                "quantity": 5,
                "price": Decimal("1.85"),
                "order_type": "MARKET",
                "strategy": StrategyType.BUTTERFLY_SPREAD,
                "legs_data": '[{"strike": 300, "type": "CALL", "action": "BUY"}]',
                "greeks_data": '{"delta": 0.3, "gamma": 0.05}'
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify trade execution
            assert result["success"] is True
            assert result["order_id"] == "e2e_butterfly_456"
            assert result["status"] == "FILLED"
            assert result["filled_quantity"] == 5
            
            # Verify API was called
            mock_public_api.execute_order.assert_called_once()
            
            # Verify database operations
            mock_database.add.assert_called()
            mock_database.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_calendar_spread_complete_workflow(self, mock_database, mock_redis, mock_public_api):
        """Test complete Calendar Spread trading workflow."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_calendar_789",
                "status": "FILLED",
                "filled_quantity": 3,
                "average_price": 3.45
            }
            
            # Execute Calendar Spread trade
            trade_details = {
                "symbol": "AAPL",
                "action": TradeAction.BUY,
                "quantity": 3,
                "price": Decimal("3.45"),
                "order_type": "MARKET",
                "strategy": StrategyType.CALENDAR_SPREAD,
                "legs_data": '[{"strike": 150, "type": "CALL", "action": "BUY"}]',
                "greeks_data": '{"delta": 0.4, "gamma": 0.08}'
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify trade execution
            assert result["success"] is True
            assert result["order_id"] == "e2e_calendar_789"
            assert result["status"] == "FILLED"
            assert result["filled_quantity"] == 3
            
            # Verify API was called
            mock_public_api.execute_order.assert_called_once()
            
            # Verify database operations
            mock_database.add.assert_called()
            mock_database.commit.assert_called()


class TestRiskManagementE2E:
    """Test risk management in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_risk_limit_enforcement_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test risk limit enforcement in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Try to execute trade that exceeds risk limits
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 25000,  # Exceeds max_position_size of 20000
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Risk check failed"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api.execute_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_emergency_stop_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test emergency stop functionality in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Activate emergency stop
        result = await system_service.activate_emergency_stop("e2e-test-account-123", "E2E test emergency")
        
        assert result["success"] is True
        assert result["status"] == "activated"
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Try to execute trade with emergency stop active
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Emergency stop active"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api.execute_order.assert_not_called()
        
        # Deactivate emergency stop
        result = await system_service.deactivate_emergency_stop("e2e-test-account-123")
        
        assert result["success"] is True
        assert result["status"] == "deactivated"
    
    @pytest.mark.asyncio
    async def test_market_hours_enforcement_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test market hours enforcement in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market closed
        with patch.object(market_hours_service, 'is_market_open', return_value=False):
            # Try to execute trade when market is closed
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Market is closed"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api.execute_order.assert_not_called()


class TestPositionManagementE2E:
    """Test position management in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_position_creation_and_update_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test position creation and updates in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Execute first trade to create position
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_position_create_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 100
            
            # Execute second trade to update position
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_position_update_456",
                "status": "FILLED",
                "filled_quantity": 50,
                "average_price": 410.00
            }
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.SELL,
                "quantity": 50,
                "price": Decimal("410.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 50
            
            # Verify both trades were executed
            assert mock_public_api.execute_order.call_count == 2
            
            # Verify database operations
            assert mock_database.add.call_count >= 2
            assert mock_database.commit.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_position_closure_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test position closure in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Execute trade to close position
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_position_close_789",
                "status": "FILLED",
                "filled_quantity": 20,  # Close entire position
                "average_price": 2.85
            }
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.SELL,
                "quantity": 20,  # Close entire position
                "price": Decimal("2.85"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 20
            
            # Verify trade was executed
            mock_public_api.execute_order.assert_called_once()
            
            # Verify database operations
            mock_database.add.assert_called()
            mock_database.commit.assert_called()


class TestOrderManagementE2E:
    """Test order management in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_order_cancellation_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test order cancellation in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock successful order cancellation
        mock_public_api.cancel_order.return_value = {
            "order_id": "e2e_cancel_test_123",
            "status": "CANCELLED"
        }
        
        # Execute order cancellation
        result = await trading_service.cancel_order("e2e-test-account-123", "e2e_cancel_test_123")
        
        assert result["success"] is True
        assert result["status"] == "CANCELLED"
        
        # Verify API was called
        mock_public_api.cancel_order.assert_called_once_with("e2e_cancel_test_123")
        
        # Verify database was updated
        mock_database.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_order_status_tracking_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test order status tracking in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Get order status
        result = await trading_service.get_order_status("e2e-test-account-123", "e2e-order-001")
        
        assert result["order_id"] == "e2e-order-001"
        assert result["status"] == "FILLED"
        assert result["filled_quantity"] == 20
        assert result["remaining_quantity"] == 0
        assert result["average_price"] == Decimal("2.50")
    
    @pytest.mark.asyncio
    async def test_order_history_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test order history retrieval in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Get order history
        result = await trading_service.get_order_history("e2e-test-account-123")
        
        assert len(result) == 1
        assert result[0]["order_id"] == "e2e-order-001"
        assert result[0]["status"] == "FILLED"
        assert result[0]["symbol"] == "SPY"


class TestSystemHealthE2E:
    """Test system health monitoring in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_system_health_check_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test system health check in end-to-end scenario."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(mock_database, mock_redis)
        
        # Perform health check
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "healthy"
        assert result["checks"]["database"] == "healthy"
        assert result["checks"]["redis"] == "healthy"
        assert result["checks"]["emergency_stop"] == "inactive"
        assert result["timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_system_metrics_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test system metrics collection in end-to-end scenario."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(mock_database, mock_redis)
        
        # Get system metrics
        result = await system_service.get_system_metrics()
        
        assert "database" in result
        assert "redis" in result
        assert "timestamp" in result
        
        assert result["database"]["active_connections"] == 1
        assert result["redis"]["connected_clients"] == 3
        assert result["redis"]["used_memory"] == 2048000
    
    @pytest.mark.asyncio
    async def test_operational_status_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test operational status check in end-to-end scenario."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(mock_database, mock_redis)
        
        # Get operational status
        result = await system_service.get_operational_status()
        
        assert result["database"] == "connected"
        assert result["redis"] == "connected"
        assert result["emergency_stop"] == "inactive"
        assert result["overall_status"] == "operational"


class TestErrorRecoveryE2E:
    """Test error recovery and resilience in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_api_failure_recovery_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test API failure recovery in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock API failure
            mock_public_api.execute_order.side_effect = Exception("API connection error")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="API connection error"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify database rollback occurred
            mock_database.rollback.assert_called()
    
    @pytest.mark.asyncio
    async def test_database_failure_recovery_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test database failure recovery in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API success
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_db_failure_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Mock database failure on commit
            mock_database.commit.side_effect = Exception("Database connection lost")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Database connection lost"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify rollback occurred
            mock_database.rollback.assert_called()
    
    @pytest.mark.asyncio
    async def test_redis_failure_recovery_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test Redis failure recovery in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock Redis failure
            mock_redis.get.side_effect = Exception("Redis connection error")
            
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            with pytest.raises(Exception, match="Redis connection error"):
                await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            # Verify Public.com API was not called
            mock_public_api.execute_order.assert_not_called()


class TestPerformanceE2E:
    """Test performance and scalability in end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_trade_execution_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test concurrent trade execution in end-to-end scenario."""
        import asyncio
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API responses
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_concurrent_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
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
                trading_service.execute_trade("e2e-test-account-123", trade_details)
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
    async def test_large_volume_trade_e2e(self, mock_database, mock_redis, mock_public_api):
        """Test large volume trade handling in end-to-end scenario."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(mock_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(mock_database, mock_redis)
        
        trading_service = TradingService(
            db_session=mock_database,
            public_api_client=mock_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock Public.com API response for large trade
            mock_public_api.execute_order.return_value = {
                "order_id": "e2e_large_volume_test_123",
                "status": "FILLED",
                "filled_quantity": 1000,
                "average_price": 400.25
            }
            
            # Execute large volume trade
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 1000,
                "price": Decimal("400.00"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            result = await trading_service.execute_trade("e2e-test-account-123", trade_details)
            
            assert result["success"] is True
            assert result["filled_quantity"] == 1000
            
            # Verify position was created with correct quantity
            mock_database.add.assert_called()
            mock_database.commit.assert_called()
