#!/usr/bin/env python3
"""
Tests for Market Data Provider System
Comprehensive test suite for market data providers and manager
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import time

from src.services.market_data.market_data_provider import (
    MarketDataProvider,
    AlphaVantageProvider,
    IEXCloudProvider,
    PolygonProvider,
    MarketDataManager,
    get_market_data_manager,
    get_historical_data,
    get_live_prices
)


class TestMarketDataProvider:
    """Test abstract MarketDataProvider base class"""
    
    def test_market_data_provider_abstract(self):
        """Test that MarketDataProvider is abstract and cannot be instantiated"""
        with pytest.raises(TypeError):
            MarketDataProvider()


@pytest.mark.skip(reason="AlphaVantage provider not used in this project")
class TestAlphaVantageProvider:
    """Test AlphaVantageProvider implementation"""
    
    @pytest.fixture
    def provider(self):
        """Create AlphaVantageProvider instance"""
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            return AlphaVantageProvider()
    
    @pytest.fixture
    def provider_no_key(self):
        """Create AlphaVantageProvider without API key"""
        with patch.dict(os.environ, {}, clear=True):
            return AlphaVantageProvider()
    
    def test_alpha_vantage_initialization_with_key(self, provider):
        """Test AlphaVantageProvider initialization with API key"""
        assert provider.api_key == 'test_key'
        assert provider.base_url == "https://www.alphavantage.co/query"
        assert provider.min_delay_between_requests == 15.0
        assert provider.max_requests_per_minute == 5
        assert provider.request_count == 0
        assert provider.rate_limit_hits == 0
    
    def test_alpha_vantage_initialization_without_key(self, provider_no_key):
        """Test AlphaVantageProvider initialization without API key"""
        assert provider_no_key.api_key is None
        assert provider_no_key.base_url == "https://www.alphavantage.co/query"
    
    def test_alpha_vantage_initialization_custom_key(self):
        """Test AlphaVantageProvider initialization with custom API key"""
        provider = AlphaVantageProvider(api_key="custom_key")
        assert provider.api_key == "custom_key"
    
    @patch('requests.Session')
    def test_create_session(self, mock_session_class, provider):
        """Test session creation with retry logic"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        session = provider._create_session()
        
        assert session == mock_session
        mock_session.mount.assert_called()
    
    @patch('time.time')
    @patch('time.sleep')
    def test_enforce_rate_limit_first_request(self, mock_sleep, mock_time, provider):
        """Test rate limiting on first request"""
        mock_time.return_value = 1000.0
        
        provider._enforce_rate_limit()
        
        assert provider.last_request_time == 1000.0
        assert provider.request_count == 1
        mock_sleep.assert_not_called()
    
    @patch('time.time')
    @patch('time.sleep')
    def test_enforce_rate_limit_with_delay(self, mock_sleep, mock_time, provider):
        """Test rate limiting with required delay"""
        provider.last_request_time = 1000.0
        mock_time.return_value = 1005.0  # 5 seconds later, need 10 more
        
        provider._enforce_rate_limit()
        
        mock_sleep.assert_called_once_with(10.0)
        assert provider.request_count == 1
    
    @patch('time.time')
    @patch('time.sleep')
    def test_enforce_rate_limit_with_rate_limit_hits(self, mock_sleep, mock_time, provider):
        """Test rate limiting with previous rate limit hits"""
        provider.last_request_time = 1000.0
        provider.rate_limit_hits = 2
        mock_time.return_value = 1005.0
        
        provider._enforce_rate_limit()
        
        # Should wait 15 + (2 * 45) = 105 seconds
        mock_sleep.assert_called_once_with(100.0)  # 105 - 5 = 100
    
    @patch('requests.Session.get')
    def test_get_historical_data_no_api_key(self, mock_get, provider_no_key):
        """Test historical data request without API key"""
        result = provider_no_key.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
        mock_get.assert_not_called()
    
    @patch('requests.Session.get')
    def test_get_historical_data_success(self, mock_get, provider):
        """Test successful historical data request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2023-01-30": {
                    "1. open": "150.00",
                    "2. high": "152.00",
                    "3. low": "149.00",
                    "4. close": "151.00",
                    "5. volume": "1000000"
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
    
    @patch('requests.Session.get')
    def test_get_historical_data_api_error(self, mock_get, provider):
        """Test historical data request with API error"""
        mock_response = Mock()
        mock_response.json.return_value = {"Error Message": "Invalid API call"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_get_live_price_success(self, mock_get, provider):
        """Test successful live price request"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "151.25"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = provider.get_live_price("AAPL")
        
        assert result == 151.25
    
    @patch('requests.Session.get')
    def test_get_live_price_no_data(self, mock_get, provider):
        """Test live price request with no data"""
        mock_response = Mock()
        mock_response.json.return_value = {"Global Quote": {}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = provider.get_live_price("AAPL")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_get_multiple_symbols_success(self, mock_get, provider):
        """Test successful multiple symbols request"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2023-01-30": {
                    "1. open": "150.00",
                    "2. high": "152.00",
                    "3. low": "149.00",
                    "4. close": "151.00",
                    "5. volume": "1000000"
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = provider.get_multiple_symbols(["AAPL", "MSFT"], "2023-01-01", "2023-01-31")
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        assert isinstance(result["AAPL"], pd.DataFrame)
        assert isinstance(result["MSFT"], pd.DataFrame)


@pytest.mark.skip(reason="IEX Cloud provider not used in this project")
class TestIEXCloudProvider:
    """Test IEXCloudProvider implementation"""
    
    @pytest.fixture
    def provider(self):
        """Create IEXCloudProvider instance"""
        with patch.dict(os.environ, {'IEX_CLOUD_API_KEY': 'test_key'}):
            return IEXCloudProvider()
    
    def test_iex_cloud_initialization(self, provider):
        """Test IEXCloudProvider initialization"""
        assert provider.api_key == 'test_key'
        assert provider.base_url == "https://cloud.iexapis.com/stable"
    
    @patch('requests.Session.get')
    def test_get_historical_data_success(self, mock_get, provider):
        """Test successful historical data request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "date": "2023-01-30",
                "open": 150.00,
                "high": 152.00,
                "low": 149.00,
                "close": 151.00,
                "volume": 1000000
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
    
    @patch('requests.Session.get')
    def test_get_live_price_success(self, mock_get, provider):
        """Test successful live price request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"latestPrice": 151.25}
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_live_price("AAPL")
        
        assert result == 151.25
    
    @patch('requests.Session.get')
    def test_get_multiple_symbols_success(self, mock_get, provider):
        """Test successful multiple symbols request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "date": "2023-01-30",
                "open": 150.00,
                "high": 152.00,
                "low": 149.00,
                "close": 151.00,
                "volume": 1000000
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_multiple_symbols(["AAPL", "MSFT"], "2023-01-01", "2023-01-31")
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result


class TestPolygonProvider:
    """Test PolygonProvider implementation"""
    
    @pytest.fixture
    def provider(self):
        """Create PolygonProvider instance"""
        with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_key'}):
            return PolygonProvider()
    
    def test_polygon_initialization(self, provider):
        """Test PolygonProvider initialization"""
        assert provider.api_key == 'test_key'
        assert provider.base_url == "https://api.polygon.io"
        assert provider.min_delay_between_requests == 1.0
    
    @patch('time.time')
    @patch('time.sleep')
    def test_enforce_rate_limit(self, mock_sleep, mock_time, provider):
        """Test rate limiting"""
        provider.last_request_time = 1000.0
        mock_time.return_value = 1000.5  # 0.5 seconds later, need 0.5 more
        
        provider._enforce_rate_limit()
        
        mock_sleep.assert_called_once_with(0.5)
        assert provider.last_request_time == 1000.5
    
    @patch('requests.Session.get')
    def test_get_historical_data_success(self, mock_get, provider):
        """Test successful historical data request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "t": 1675123200000,  # Unix timestamp
                    "o": 150.00,
                    "h": 152.00,
                    "l": 149.00,
                    "c": 151.00,
                    "v": 1000000
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
    
    @patch('requests.Session.get')
    def test_get_live_price_success(self, mock_get, provider):
        """Test successful live price request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "lastTrade": {
                    "p": 151.25  # Current price
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_live_price("AAPL")
        
        assert result == 151.25
    
    @patch('requests.Session.get')
    def test_get_multiple_symbols_success(self, mock_get, provider):
        """Test successful multiple symbols request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "t": 1675123200000,
                    "o": 150.00,
                    "h": 152.00,
                    "l": 149.00,
                    "c": 151.00,
                    "v": 1000000
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_response.text = "mock response text"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        result = provider.get_multiple_symbols(["AAPL", "MSFT"], "2023-01-01", "2023-01-31")
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result


class TestMarketDataManager:
    """Test MarketDataManager implementation"""
    
    @pytest.fixture
    def manager(self):
        """Create MarketDataManager instance"""
        return MarketDataManager()
    
    @pytest.fixture
    def manager_with_providers(self):
        """Create MarketDataManager with custom providers"""
        mock_provider = Mock(spec=MarketDataProvider)
        return MarketDataManager(providers=[mock_provider])
    
    def test_manager_initialization_default(self, manager):
        """Test MarketDataManager initialization with default providers"""
        assert isinstance(manager.providers, list)
        assert len(manager.providers) > 0
    
    def test_manager_initialization_custom_providers(self, manager_with_providers):
        """Test MarketDataManager initialization with custom providers"""
        assert len(manager_with_providers.providers) == 1
        assert isinstance(manager_with_providers.providers[0], Mock)
    
    @patch('src.services.market_data.market_data_provider.AlphaVantageProvider')
    @patch('src.services.market_data.market_data_provider.IEXCloudProvider')
    @patch('src.services.market_data.market_data_provider.PolygonProvider')
    def test_add_default_providers(self, mock_polygon, mock_iex, mock_alpha, manager):
        """Test adding default providers"""
        # Clear existing providers
        manager.providers = []
        
        # Call the method that adds default providers
        manager._add_default_providers()
        
        # Should have added at least one provider
        assert len(manager.providers) > 0
    
    def test_get_historical_data_success(self, manager_with_providers):
        """Test successful historical data request through manager"""
        mock_provider = manager_with_providers.providers[0]
        mock_df = pd.DataFrame({
            'open': [150.0],
            'high': [152.0],
            'low': [149.0],
            'close': [151.0],
            'volume': [1000000]
        })
        mock_provider.get_historical_data.return_value = mock_df
        
        result = manager_with_providers.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        mock_provider.get_historical_data.assert_called_once_with(
            "AAPL", "2023-01-01", "2023-01-31", "1d"
        )
    
    def test_get_historical_data_all_providers_fail(self, manager_with_providers):
        """Test historical data request when all providers fail"""
        mock_provider = manager_with_providers.providers[0]
        mock_provider.get_historical_data.return_value = None
        
        result = manager_with_providers.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
    
    def test_get_live_price_success(self, manager_with_providers):
        """Test successful live price request through manager"""
        mock_provider = manager_with_providers.providers[0]
        mock_provider.get_live_price.return_value = 151.25
        
        result = manager_with_providers.get_live_price("AAPL")
        
        assert result == 151.25
        mock_provider.get_live_price.assert_called_once_with("AAPL")
    
    def test_get_live_price_all_providers_fail(self, manager_with_providers):
        """Test live price request when all providers fail"""
        mock_provider = manager_with_providers.providers[0]
        mock_provider.get_live_price.return_value = None
        
        result = manager_with_providers.get_live_price("AAPL")
        
        assert result is None
    
    def test_get_multiple_symbols_success(self, manager_with_providers):
        """Test successful multiple symbols request through manager"""
        mock_provider = manager_with_providers.providers[0]
        mock_df = pd.DataFrame({
            'open': [150.0],
            'high': [152.0],
            'low': [149.0],
            'close': [151.0],
            'volume': [1000000]
        })
        mock_provider.get_historical_data.return_value = mock_df
        
        result = manager_with_providers.get_multiple_symbols(
            ["AAPL", "MSFT"], "2023-01-01", "2023-01-31"
        )
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        # Should be called twice, once for each symbol
        assert mock_provider.get_historical_data.call_count == 2
    
    def test_get_provider_status(self, manager_with_providers):
        """Test getting provider status"""
        status = manager_with_providers.get_provider_status()
        
        assert isinstance(status, dict)
        # Should have status for each provider
        assert len(status) == len(manager_with_providers.providers)


class TestGlobalFunctions:
    """Test global functions"""
    
    @patch('src.services.market_data.market_data_provider.MarketDataManager')
    def test_get_market_data_manager(self, mock_manager_class):
        """Test get_market_data_manager function"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        result = get_market_data_manager()
        
        assert result == mock_manager
        mock_manager_class.assert_called_once()
    
    @patch('src.services.market_data.market_data_provider.get_market_data_manager')
    def test_get_historical_data_global(self, mock_get_manager):
        """Test get_historical_data global function"""
        mock_manager = Mock()
        mock_df = pd.DataFrame({'close': [151.0]})
        mock_manager.get_multiple_symbols.return_value = {"AAPL": mock_df}
        mock_get_manager.return_value = mock_manager
        
        result = get_historical_data(["AAPL"], "2023-01-01", "2023-01-31")
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        mock_manager.get_multiple_symbols.assert_called_once_with(
            ["AAPL"], "2023-01-01", "2023-01-31", "1d"
        )
    
    @patch('src.services.market_data.market_data_provider.get_market_data_manager')
    def test_get_live_prices_global(self, mock_get_manager):
        """Test get_live_prices global function"""
        mock_manager = Mock()
        mock_manager.get_live_price.return_value = 151.25
        mock_get_manager.return_value = mock_manager
        
        result = get_live_prices(["AAPL"])
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert result["AAPL"] == 151.25
        mock_manager.get_live_price.assert_called_once_with("AAPL")


class TestMarketDataProviderEdgeCases:
    """Test edge cases for market data providers"""
    
    @pytest.fixture
    def alpha_provider(self):
        """Create AlphaVantageProvider instance"""
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            return AlphaVantageProvider()
    
    @patch('requests.Session.get')
    def test_get_historical_data_empty_response(self, mock_get, alpha_provider):
        """Test historical data request with empty response"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = alpha_provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_get_historical_data_malformed_response(self, mock_get, alpha_provider):
        """Test historical data request with malformed response"""
        mock_response = Mock()
        mock_response.json.return_value = {"Invalid": "Data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = alpha_provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_get_historical_data_http_error(self, mock_get, alpha_provider):
        """Test historical data request with HTTP error"""
        mock_get.side_effect = Exception("HTTP Error")
        
        result = alpha_provider.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is None
    
    def test_get_historical_data_invalid_dates(self, alpha_provider):
        """Test historical data request with invalid dates"""
        result = alpha_provider.get_historical_data("AAPL", "invalid-date", "also-invalid")
        
        assert result is None


class TestMarketDataProviderIntegration:
    """Integration tests for market data providers"""
    
    @pytest.fixture
    def manager(self):
        """Create MarketDataManager with mocked providers"""
        mock_provider = Mock(spec=MarketDataProvider)
        return MarketDataManager(providers=[mock_provider])
    
    def test_full_workflow_historical_data(self, manager):
        """Test complete workflow for historical data"""
        mock_provider = manager.providers[0]
        mock_df = pd.DataFrame({
            'open': [150.0, 151.0],
            'high': [152.0, 153.0],
            'low': [149.0, 150.0],
            'close': [151.0, 152.0],
            'volume': [1000000, 1100000]
        })
        mock_provider.get_historical_data.return_value = mock_df
        
        # Test through manager
        result = manager.get_historical_data("AAPL", "2023-01-01", "2023-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "open" in result.columns
        assert "close" in result.columns
    
    def test_full_workflow_live_price(self, manager):
        """Test complete workflow for live price"""
        mock_provider = manager.providers[0]
        mock_provider.get_live_price.return_value = 151.25
        
        # Test through manager
        result = manager.get_live_price("AAPL")
        
        assert result == 151.25
        mock_provider.get_live_price.assert_called_once_with("AAPL")
    
    def test_full_workflow_multiple_symbols(self, manager):
        """Test complete workflow for multiple symbols"""
        mock_provider = manager.providers[0]
        mock_df = pd.DataFrame({
            'open': [150.0],
            'high': [152.0],
            'low': [149.0],
            'close': [151.0],
            'volume': [1000000]
        })
        mock_provider.get_historical_data.return_value = mock_df
        
        # Test through manager
        result = manager.get_multiple_symbols(
            ["AAPL", "MSFT"], "2023-01-01", "2023-01-31"
        )
        
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        assert isinstance(result["AAPL"], pd.DataFrame)
        assert isinstance(result["MSFT"], pd.DataFrame) 