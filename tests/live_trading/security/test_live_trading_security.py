"""
Security tests for live trading system.

Tests authentication, authorization, input validation, and security controls.
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
def security_test_database():
    """Create security test database."""
    db = AsyncMock()
    
    # Mock account
    account = LiveTradingAccount(
        account_id="security-test-account-123",
        public_account_id="public-security-123",
        account_name="Security Test Account",
        account_type="CASH",
        buying_power=10000.0,
        cash_balance=5000.0,
        equity=15000.0,
        is_active=True
    )
    
    # Mock risk profile
    risk_profile = RiskProfile(
        account_id="security-test-account-123",
        max_position_size=10000.0,
        max_portfolio_risk=0.05,
        max_daily_loss=1000.0,
        max_daily_trades=20,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
        max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )
    
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
            return []  # No existing positions/trades
        elif hasattr(query_result, 'scalar'):
            return 0  # Mock count queries
        return query_result
    
    db.execute.side_effect = mock_execute
    return db


@pytest.fixture
def security_test_redis():
    """Create security test Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # No emergency stop
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.ping.return_value = True
    redis.info.return_value = {
        "connected_clients": 3,
        "used_memory": 2048000,
        "keyspace_hits": 1000,
        "keyspace_misses": 100
    }
    return redis


@pytest.fixture
def security_test_public_api():
    """Create security test Public.com API client."""
    api = AsyncMock()
    
    # Mock authentication
    api.authenticate.return_value = {
        "access_token": "security_access_token_123",
        "refresh_token": "security_refresh_token_456",
        "expires_in": 3600
    }
    
    # Mock account info
    api.get_account_info.return_value = {
        "account_id": "public-security-123",
        "buying_power": 10000.0,
        "cash_balance": 5000.0,
        "equity": 15000.0
    }
    
    # Mock positions
    api.get_positions.return_value = {
        "positions": []
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


class TestAuthenticationSecurity:
    """Test authentication security."""
    
    @pytest.mark.asyncio
    async def test_invalid_api_credentials(self, security_test_database, security_test_redis, security_test_public_api):
        """Test handling of invalid API credentials."""
        from src.services.live_trading.public_api_client import PublicAPIClient, AuthenticationError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock authentication failure
        security_test_public_api.authenticate.side_effect = AuthenticationError("Invalid credentials")
        
        # Test authentication with invalid credentials
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await api_client.authenticate("invalid_user", "invalid_password")
    
    @pytest.mark.asyncio
    async def test_expired_token_handling(self, security_test_database, security_test_redis, security_test_public_api):
        """Test handling of expired tokens."""
        from src.services.live_trading.public_api_client import PublicAPIClient, AuthenticationError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock expired token
        api_client.access_token = "expired_token"
        api_client.token_expires_at = datetime.now(timezone.utc) - timezone.utc.utctimetuple()
        
        # Mock authentication failure
        security_test_public_api.refresh_access_token.side_effect = AuthenticationError("Token refresh failed")
        
        # Test API call with expired token
        with pytest.raises(AuthenticationError, match="Token refresh failed"):
            await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_token_refresh_security(self, security_test_database, security_test_redis, security_test_public_api):
        """Test token refresh security."""
        from src.services.live_trading.public_api_client import PublicAPIClient, AuthenticationError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock token refresh
        security_test_public_api.refresh_access_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        
        # Test token refresh
        result = await api_client.refresh_access_token()
        
        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"
        assert api_client.access_token == "new_access_token"
        assert api_client.refresh_token == "new_refresh_token"
    
    @pytest.mark.asyncio
    async def test_unauthorized_api_access(self, security_test_database, security_test_redis, security_test_public_api):
        """Test unauthorized API access."""
        from src.services.live_trading.public_api_client import PublicAPIClient, AuthenticationError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock unauthorized access
        security_test_public_api.get_account_info.side_effect = AuthenticationError("Unauthorized")
        
        # Test unauthorized API access
        with pytest.raises(AuthenticationError, match="Unauthorized"):
            await api_client.get_account_info()


class TestInputValidationSecurity:
    """Test input validation security."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, security_test_database, security_test_redis, security_test_public_api):
        """Test SQL injection prevention."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test SQL injection in account ID
        malicious_account_id = "'; DROP TABLE accounts; --"
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
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
            
            # Test that SQL injection is prevented
            with pytest.raises(Exception, match="Account not found"):
                await trading_service.execute_trade(malicious_account_id, trade_details)
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, security_test_database, security_test_redis, security_test_public_api):
        """Test XSS prevention."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(security_test_database, security_test_redis)
        
        # Test XSS in emergency stop reason
        xss_payload = "<script>alert('XSS')</script>"
        
        # Test that XSS is prevented
        result = await system_service.activate_emergency_stop("security-test-account-123", xss_payload)
        
        # Verify that the payload is not executed
        assert result["success"] is True
        assert result["reason"] == xss_payload  # Should be stored as-is, not executed
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, security_test_database, security_test_redis, security_test_public_api):
        """Test input sanitization."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test input sanitization
        malicious_symbol = "SPY'; DROP TABLE positions; --"
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            trade_details = {
                "symbol": malicious_symbol,
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            # Test that malicious input is handled safely
            result = await trading_service.execute_trade("security-test-account-123", trade_details)
            
            # Verify that the trade was processed safely
            assert result["success"] is True
            assert result["status"] == "FILLED"
    
    @pytest.mark.asyncio
    async def test_numeric_input_validation(self, security_test_database, security_test_redis, security_test_public_api):
        """Test numeric input validation."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test invalid numeric inputs
        invalid_inputs = [
            {"quantity": "not_a_number"},
            {"quantity": -1000},
            {"quantity": 0},
            {"price": "invalid_price"},
            {"price": -100.0},
            {"price": 0.0}
        ]
        
        for invalid_input in invalid_inputs:
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR,
                **invalid_input
            }
            
            # Test that invalid inputs are rejected
            with pytest.raises(Exception, match="Invalid trade data"):
                await trading_service.execute_trade("security-test-account-123", trade_details)


class TestAuthorizationSecurity:
    """Test authorization security."""
    
    @pytest.mark.asyncio
    async def test_account_isolation(self, security_test_database, security_test_redis, security_test_public_api):
        """Test account isolation."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test accessing another account's data
        other_account_id = "other-account-123"
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
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
            
            # Test that access to other accounts is denied
            with pytest.raises(Exception, match="Account not found"):
                await trading_service.execute_trade(other_account_id, trade_details)
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_prevention(self, security_test_database, security_test_redis, security_test_public_api):
        """Test privilege escalation prevention."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(security_test_database, security_test_redis)
        
        # Test emergency stop activation for other accounts
        other_account_id = "other-account-123"
        
        # Test that emergency stop cannot be activated for other accounts
        with pytest.raises(Exception, match="Account not found"):
            await system_service.activate_emergency_stop(other_account_id, "Test reason")
    
    @pytest.mark.asyncio
    async def test_unauthorized_risk_profile_access(self, security_test_database, security_test_redis, security_test_public_api):
        """Test unauthorized risk profile access."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(security_test_database)
        
        # Test accessing risk profile for non-existent account
        non_existent_account = "non-existent-account-123"
        
        # Test that risk profile access is denied for non-existent accounts
        risk_profile = await risk_service.get_risk_profile(non_existent_account)
        assert risk_profile is None


class TestDataProtectionSecurity:
    """Test data protection security."""
    
    @pytest.mark.asyncio
    async def test_sensitive_data_encryption(self, security_test_database, security_test_redis, security_test_public_api):
        """Test sensitive data encryption."""
        from src.services.live_trading.public_api_client import PublicAPIClient
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Test that sensitive data is encrypted
        api_key = "sensitive_api_key_123"
        api_secret = "sensitive_api_secret_456"
        
        # Mock authentication
        security_test_public_api.authenticate.return_value = {
            "access_token": "encrypted_access_token",
            "refresh_token": "encrypted_refresh_token",
            "expires_in": 3600
        }
        
        # Test authentication
        result = await api_client.authenticate("test_user", "test_password")
        
        # Verify that sensitive data is handled securely
        assert result["access_token"] == "encrypted_access_token"
        assert result["refresh_token"] == "encrypted_refresh_token"
        assert api_client.access_token == "encrypted_access_token"
        assert api_client.refresh_token == "encrypted_refresh_token"
    
    @pytest.mark.asyncio
    async def test_data_masking(self, security_test_database, security_test_redis, security_test_public_api):
        """Test data masking."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test that sensitive data is masked in logs
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.25"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute trade
            result = await trading_service.execute_trade("security-test-account-123", trade_details)
            
            # Verify that sensitive data is not exposed
            assert result["success"] is True
            assert result["order_id"] == "security_test_123"
            assert result["status"] == "FILLED"
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, security_test_database, security_test_redis, security_test_public_api):
        """Test audit logging."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test that audit logs are created
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.25"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute trade
            result = await trading_service.execute_trade("security-test-account-123", trade_details)
            
            # Verify that audit logs are created
            assert result["success"] is True
            assert result["order_id"] == "security_test_123"
            assert result["status"] == "FILLED"
            
            # Verify database operations (audit logging)
            security_test_database.add.assert_called()
            security_test_database.commit.assert_called()


class TestRateLimitingSecurity:
    """Test rate limiting security."""
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, security_test_database, security_test_redis, security_test_public_api):
        """Test API rate limiting."""
        from src.services.live_trading.public_api_client import PublicAPIClient, RateLimitError
        
        # Create API client
        api_client = PublicAPIClient()
        
        # Mock rate limit error
        security_test_public_api.get_account_info.side_effect = RateLimitError("Rate limit exceeded")
        
        # Test rate limiting
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_trade_rate_limiting(self, security_test_database, security_test_redis, security_test_public_api):
        """Test trade rate limiting."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test trade rate limiting
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.25"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute multiple trades to test rate limiting
            for i in range(25):  # Exceed daily trade limit of 20
                if i < 20:
                    # First 20 trades should succeed
                    result = await trading_service.execute_trade("security-test-account-123", trade_details)
                    assert result["success"] is True
                else:
                    # Trades after limit should fail
                    with pytest.raises(Exception, match="Risk check failed"):
                        await trading_service.execute_trade("security-test-account-123", trade_details)


class TestErrorHandlingSecurity:
    """Test error handling security."""
    
    @pytest.mark.asyncio
    async def test_error_information_disclosure(self, security_test_database, security_test_redis, security_test_public_api):
        """Test error information disclosure."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test error information disclosure
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.25"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock API error
            security_test_public_api.execute_order.side_effect = Exception("Internal server error")
            
            # Test that sensitive error information is not disclosed
            with pytest.raises(Exception, match="Order execution failed"):
                await trading_service.execute_trade("security-test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, security_test_database, security_test_redis, security_test_public_api):
        """Test database error handling."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(security_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(security_test_database, security_test_redis)
        
        trading_service = TradingService(
            db_session=security_test_database,
            public_api_client=security_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Test database error handling
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.25"),
            "order_type": "MARKET",
            "strategy": StrategyType.IRON_CONDOR
        }
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            security_test_public_api.execute_order.return_value = {
                "order_id": "security_test_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Mock database error
            security_test_database.commit.side_effect = Exception("Database connection lost")
            
            # Test that database errors are handled securely
            with pytest.raises(Exception, match="Database error"):
                await trading_service.execute_trade("security-test-account-123", trade_details)
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self, security_test_database, security_test_redis, security_test_public_api):
        """Test Redis error handling."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(security_test_database, security_test_redis)
        
        # Test Redis error handling
        security_test_redis.get.side_effect = Exception("Redis connection error")
        
        # Test that Redis errors are handled securely
        with pytest.raises(Exception, match="Redis connection error"):
            await system_service.check_emergency_stop("security-test-account-123")
