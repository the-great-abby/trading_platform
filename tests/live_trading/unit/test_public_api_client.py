"""
Unit tests for Public.com API client.

Tests authentication, API communication, error handling, and retry logic.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import json

from src.services.live_trading.public_api_client import (
    PublicAPIClient, PublicAPIConfig, AuthenticationError, 
    APIError, RateLimitError, NetworkError
)


@pytest.fixture
def api_config():
    """Create API configuration for testing."""
    return PublicAPIConfig(
        base_url="https://api.test.com",
        api_version="v1",
        timeout=5,
        max_retries=2,
        retry_delay=0.1
    )


@pytest.fixture
def api_client(api_config):
    """Create API client for testing."""
    return PublicAPIClient(config=api_config)


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True, "data": "test"}
    response.headers = {"Content-Type": "application/json"}
    return response


class TestPublicAPIConfig:
    """Test PublicAPIConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PublicAPIConfig()
        
        assert config.base_url == "https://public.com/api"
        assert config.api_version == "v1"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PublicAPIConfig(
            base_url="https://custom.api.com",
            api_version="v2",
            timeout=10,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.base_url == "https://custom.api.com"
        assert config.api_version == "v2"
        assert config.timeout == 10
        assert config.max_retries == 5
        assert config.retry_delay == 2.0


class TestPublicAPIClient:
    """Test PublicAPIClient class."""
    
    def test_client_initialization(self, api_client):
        """Test client initialization."""
        assert api_client.config is not None
        assert api_client.access_token is None
        assert api_client.refresh_token is None
        assert api_client.token_expires_at is None
        assert api_client.is_authenticated is False
        assert api_client.client is not None
    
    def test_client_headers(self, api_client):
        """Test client headers."""
        expected_headers = {
            "Content-Type": "application/json",
            "User-Agent": "LiveTradingService/1.0.0"
        }
        
        assert api_client.client.headers == expected_headers


class TestAuthentication:
    """Test authentication methods."""
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, api_client, mock_response):
        """Test successful authentication."""
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            result = await api_client.authenticate("test_user", "test_pass")
            
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert api_client.access_token == "test_access_token"
            assert api_client.refresh_token == "test_refresh_token"
            assert api_client.is_authenticated is True
            assert api_client.token_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, api_client, mock_response):
        """Test authentication failure."""
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Invalid credentials",
            "message": "Authentication failed"
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                await api_client.authenticate("wrong_user", "wrong_pass")
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, api_client, mock_response):
        """Test successful token refresh."""
        api_client.refresh_token = "test_refresh_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            result = await api_client.refresh_access_token()
            
            assert result["access_token"] == "new_access_token"
            assert api_client.access_token == "new_access_token"
            assert api_client.refresh_token == "new_refresh_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, api_client, mock_response):
        """Test token refresh failure."""
        api_client.refresh_token = "invalid_refresh_token"
        
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Invalid refresh token"
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            with pytest.raises(AuthenticationError, match="Token refresh failed"):
                await api_client.refresh_access_token()
    
    @pytest.mark.asyncio
    async def test_logout(self, api_client):
        """Test logout functionality."""
        api_client.access_token = "test_token"
        api_client.refresh_token = "test_refresh"
        api_client.is_authenticated = True
        
        await api_client.logout()
        
        assert api_client.access_token is None
        assert api_client.refresh_token is None
        assert api_client.is_authenticated is False
        assert api_client.token_expires_at is None


class TestAccountMethods:
    """Test account-related API methods."""
    
    @pytest.mark.asyncio
    async def test_get_account_info_success(self, api_client, mock_response):
        """Test successful account info retrieval."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "account_id": "test_account",
            "buying_power": 10000.0,
            "cash_balance": 5000.0,
            "equity": 15000.0
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            result = await api_client.get_account_info()
            
            assert result["account_id"] == "test_account"
            assert result["buying_power"] == 10000.0
            assert result["cash_balance"] == 5000.0
            assert result["equity"] == 15000.0
    
    @pytest.mark.asyncio
    async def test_get_account_info_unauthorized(self, api_client, mock_response):
        """Test account info retrieval with invalid token."""
        api_client.access_token = "invalid_token"
        
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Unauthorized"
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            with pytest.raises(AuthenticationError, match="Unauthorized"):
                await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_get_positions_success(self, api_client, mock_response):
        """Test successful positions retrieval."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "positions": [
                {
                    "symbol": "SPY",
                    "quantity": 100,
                    "average_price": 400.0,
                    "current_price": 405.0
                }
            ]
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            result = await api_client.get_positions()
            
            assert len(result["positions"]) == 1
            assert result["positions"][0]["symbol"] == "SPY"
            assert result["positions"][0]["quantity"] == 100


class TestTradingMethods:
    """Test trading-related API methods."""
    
    @pytest.mark.asyncio
    async def test_execute_order_success(self, api_client, mock_response):
        """Test successful order execution."""
        api_client.access_token = "test_token"
        
        order_data = {
            "symbol": "SPY",
            "side": "BUY",
            "quantity": 100,
            "order_type": "MARKET"
        }
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "order_id": "order_123",
            "status": "FILLED",
            "filled_quantity": 100,
            "average_price": 400.25
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            result = await api_client.execute_order(order_data)
            
            assert result["order_id"] == "order_123"
            assert result["status"] == "FILLED"
            assert result["filled_quantity"] == 100
    
    @pytest.mark.asyncio
    async def test_execute_order_insufficient_funds(self, api_client, mock_response):
        """Test order execution with insufficient funds."""
        api_client.access_token = "test_token"
        
        order_data = {
            "symbol": "SPY",
            "side": "BUY",
            "quantity": 1000000,  # Very large quantity
            "order_type": "MARKET"
        }
        
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "Insufficient funds",
            "message": "Not enough buying power for this order"
        }
        
        with patch.object(api_client.client, 'post', return_value=mock_response):
            with pytest.raises(APIError, match="Insufficient funds"):
                await api_client.execute_order(order_data)
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, api_client, mock_response):
        """Test successful order cancellation."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "order_id": "order_123",
            "status": "CANCELLED"
        }
        
        with patch.object(api_client.client, 'delete', return_value=mock_response):
            result = await api_client.cancel_order("order_123")
            
            assert result["order_id"] == "order_123"
            assert result["status"] == "CANCELLED"
    
    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, api_client, mock_response):
        """Test order cancellation for non-existent order."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": "Order not found"
        }
        
        with patch.object(api_client.client, 'delete', return_value=mock_response):
            with pytest.raises(APIError, match="Order not found"):
                await api_client.cancel_order("nonexistent_order")


class TestMarketDataMethods:
    """Test market data API methods."""
    
    @pytest.mark.asyncio
    async def test_get_market_data_success(self, api_client, mock_response):
        """Test successful market data retrieval."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "SPY",
            "price": 405.50,
            "bid": 405.45,
            "ask": 405.55,
            "volume": 1000000
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            result = await api_client.get_market_data("SPY")
            
            assert result["symbol"] == "SPY"
            assert result["price"] == 405.50
            assert result["bid"] == 405.45
            assert result["ask"] == 405.55
    
    @pytest.mark.asyncio
    async def test_get_market_data_invalid_symbol(self, api_client, mock_response):
        """Test market data retrieval for invalid symbol."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "Invalid symbol"
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            with pytest.raises(APIError, match="Invalid symbol"):
                await api_client.get_market_data("INVALID")
    
    @pytest.mark.asyncio
    async def test_get_options_chain_success(self, api_client, mock_response):
        """Test successful options chain retrieval."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 200
        mock_response.json.return_value = {
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
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            result = await api_client.get_options_chain("SPY")
            
            assert result["symbol"] == "SPY"
            assert len(result["expiration_dates"]) == 2
            assert len(result["strikes"]) == 3
            assert len(result["options"]) == 1


class TestErrorHandling:
    """Test error handling and exceptions."""
    
    @pytest.mark.asyncio
    async def test_network_error(self, api_client):
        """Test network error handling."""
        with patch.object(api_client.client, 'get', side_effect=Exception("Network error")):
            with pytest.raises(NetworkError, match="Network error"):
                await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, api_client, mock_response):
        """Test rate limit error handling."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {
            "error": "Rate limit exceeded",
            "message": "Too many requests"
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_server_error(self, api_client, mock_response):
        """Test server error handling."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": "Internal server error"
        }
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            with pytest.raises(APIError, match="Internal server error"):
                await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, api_client):
        """Test timeout error handling."""
        with patch.object(api_client.client, 'get', side_effect=asyncio.TimeoutError):
            with pytest.raises(NetworkError, match="Request timeout"):
                await api_client.get_account_info()


class TestRetryLogic:
    """Test retry logic and resilience."""
    
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, api_client, mock_response):
        """Test retry logic on server errors."""
        api_client.access_token = "test_token"
        
        # First call fails, second succeeds
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}
        
        with patch.object(api_client.client, 'get', side_effect=[mock_response, success_response]):
            result = await api_client.get_account_info()
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, api_client, mock_response):
        """Test behavior when max retries are exceeded."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        
        with patch.object(api_client.client, 'get', return_value=mock_response):
            with pytest.raises(APIError, match="Server error"):
                await api_client.get_account_info()
    
    @pytest.mark.asyncio
    async def test_retry_delay(self, api_client, mock_response):
        """Test retry delay implementation."""
        api_client.access_token = "test_token"
        
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}
        
        with patch.object(api_client.client, 'get', side_effect=[mock_response, success_response]):
            with patch('asyncio.sleep') as mock_sleep:
                await api_client.get_account_info()
                
                # Verify retry delay was called
                mock_sleep.assert_called_once_with(api_client.config.retry_delay)


class TestTokenManagement:
    """Test token management and expiration handling."""
    
    @pytest.mark.asyncio
    async def test_token_expiration_check(self, api_client):
        """Test token expiration checking."""
        # Set token to expire in the past
        api_client.token_expires_at = datetime.now() - timedelta(hours=1)
        api_client.access_token = "expired_token"
        
        assert api_client.is_token_expired() is True
    
    @pytest.mark.asyncio
    async def test_token_expiration_check_valid(self, api_client):
        """Test token expiration checking with valid token."""
        # Set token to expire in the future
        api_client.token_expires_at = datetime.now() + timedelta(hours=1)
        api_client.access_token = "valid_token"
        
        assert api_client.is_token_expired() is False
    
    @pytest.mark.asyncio
    async def test_auto_token_refresh(self, api_client, mock_response):
        """Test automatic token refresh on expiration."""
        # Set up expired token
        api_client.access_token = "expired_token"
        api_client.refresh_token = "valid_refresh_token"
        api_client.token_expires_at = datetime.now() - timedelta(hours=1)
        
        # Mock refresh token response
        refresh_response = MagicMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        
        # Mock account info response
        account_response = MagicMock()
        account_response.status_code = 200
        account_response.json.return_value = {"account_id": "test"}
        
        with patch.object(api_client.client, 'post', return_value=refresh_response):
            with patch.object(api_client.client, 'get', return_value=account_response):
                await api_client.get_account_info()
                
                # Verify token was refreshed
                assert api_client.access_token == "new_access_token"
                assert api_client.refresh_token == "new_refresh_token"


class TestRequestBuilding:
    """Test request building and formatting."""
    
    def test_build_headers(self, api_client):
        """Test header building."""
        api_client.access_token = "test_token"
        
        headers = api_client._build_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    def test_build_headers_no_token(self, api_client):
        """Test header building without token."""
        headers = api_client._build_headers()
        
        assert "Authorization" not in headers
        assert "Content-Type" in headers
    
    def test_build_url(self, api_client):
        """Test URL building."""
        url = api_client._build_url("/test/endpoint")
        
        assert url == "https://api.test.com/v1/test/endpoint"
    
    def test_build_url_with_params(self, api_client):
        """Test URL building with query parameters."""
        params = {"symbol": "SPY", "limit": 10}
        url = api_client._build_url("/test/endpoint", params=params)
        
        assert "symbol=SPY" in url
        assert "limit=10" in url
        assert url.startswith("https://api.test.com/v1/test/endpoint")


class TestDataValidation:
    """Test data validation and sanitization."""
    
    def test_validate_order_data(self, api_client):
        """Test order data validation."""
        valid_order = {
            "symbol": "SPY",
            "side": "BUY",
            "quantity": 100,
            "order_type": "MARKET"
        }
        
        assert api_client._validate_order_data(valid_order) is True
    
    def test_validate_order_data_missing_fields(self, api_client):
        """Test order data validation with missing fields."""
        invalid_order = {
            "symbol": "SPY",
            "side": "BUY"
            # Missing quantity and order_type
        }
        
        assert api_client._validate_order_data(invalid_order) is False
    
    def test_validate_order_data_invalid_values(self, api_client):
        """Test order data validation with invalid values."""
        invalid_order = {
            "symbol": "SPY",
            "side": "INVALID",  # Invalid side
            "quantity": -100,   # Negative quantity
            "order_type": "MARKET"
        }
        
        assert api_client._validate_order_data(invalid_order) is False
    
    def test_sanitize_symbol(self, api_client):
        """Test symbol sanitization."""
        assert api_client._sanitize_symbol("SPY") == "SPY"
        assert api_client._sanitize_symbol("spy") == "SPY"
        assert api_client._sanitize_symbol("SpY") == "SPY"
        assert api_client._sanitize_symbol("SPY ") == "SPY"  # Remove spaces
        assert api_client._sanitize_symbol("SPY123") == "SPY123"


class TestLogging:
    """Test logging and debugging functionality."""
    
    def test_log_request(self, api_client, caplog):
        """Test request logging."""
        api_client._log_request("GET", "/test", {"param": "value"})
        
        assert "GET /test" in caplog.text
        assert "param=value" in caplog.text
    
    def test_log_response(self, api_client, caplog):
        """Test response logging."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        
        api_client._log_response(mock_response)
        
        assert "200" in caplog.text
        assert "success" in caplog.text
    
    def test_log_error(self, api_client, caplog):
        """Test error logging."""
        api_client._log_error("Test error", {"details": "error details"})
        
        assert "Test error" in caplog.text
        assert "error details" in caplog.text
