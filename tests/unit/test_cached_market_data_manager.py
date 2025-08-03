#!/usr/bin/env python3
"""
Tests for Cached Market Data Manager
Comprehensive test suite for market data processing and caching
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from src.services.market_data.cached_market_data_manager import (
    CacheStats,
    CachedMarketDataManager,
    get_cached_market_data_manager
)


class TestCacheStats:
    """Test CacheStats dataclass"""
    
    def test_cache_stats_initialization(self):
        """Test CacheStats initialization with default values"""
        stats = CacheStats()
        
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.api_calls == 0
        assert stats.cache_hit_rate == 0.0
    
    def test_cache_stats_update_hit(self):
        """Test updating stats for cache hit"""
        stats = CacheStats()
        
        # Update for cache hit
        stats.update_hit()
        
        assert stats.total_requests == 1
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.api_calls == 0
        assert stats.cache_hit_rate == 100.0
    
    def test_cache_stats_update_miss(self):
        """Test updating stats for cache miss"""
        stats = CacheStats()
        
        # Update for cache miss with API calls
        stats.update_miss(api_calls=2)
        
        assert stats.total_requests == 1
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1
        assert stats.api_calls == 2
        assert stats.cache_hit_rate == 0.0
    
    def test_cache_stats_multiple_updates(self):
        """Test multiple stat updates"""
        stats = CacheStats()
        
        # Multiple hits and misses
        stats.update_hit()   # 1/1 = 100%
        stats.update_miss(1) # 1/2 = 50%
        stats.update_hit()   # 2/3 = 66.67%
        stats.update_miss(0) # 2/4 = 50%
        
        assert stats.total_requests == 4
        assert stats.cache_hits == 2
        assert stats.cache_misses == 2
        assert stats.api_calls == 1
        assert stats.cache_hit_rate == 50.0
    
    def test_cache_stats_edge_cases(self):
        """Test edge cases for cache stats"""
        stats = CacheStats()
        
        # Test with zero total requests (should not cause division by zero)
        assert stats.cache_hit_rate == 0.0
        
        # Test with only misses
        stats.update_miss(1)
        assert stats.cache_hit_rate == 0.0
        
        # Test with only hits
        stats = CacheStats()
        stats.update_hit()
        assert stats.cache_hit_rate == 100.0


class TestCachedMarketDataManagerInitialization:
    """Test CachedMarketDataManager initialization"""
    
    @patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService')
    @patch('src.services.market_data.cached_market_data_manager.get_market_data_manager')
    def test_manager_initialization_default(self, mock_get_manager, mock_db_service):
        """Test manager initialization with default settings"""
        mock_db_service.return_value = Mock()
        mock_get_manager.return_value = Mock()
        
        manager = CachedMarketDataManager()
        
        assert manager.db_service is not None
        assert manager.api_manager is not None
        assert isinstance(manager.stats, CacheStats)
        assert manager._cache_enabled is True
        assert manager.database_only is False
    
    @patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService')
    @patch('src.services.market_data.cached_market_data_manager.get_market_data_manager')
    def test_manager_initialization_database_only(self, mock_get_manager, mock_db_service):
        """Test manager initialization with database-only mode"""
        mock_db_service.return_value = Mock()
        mock_get_manager.return_value = Mock()
        
        manager = CachedMarketDataManager(database_only=True)
        
        assert manager.database_only is True
    
    @patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService')
    @patch('src.services.market_data.cached_market_data_manager.get_market_data_manager')
    def test_manager_initialization_custom_database_url(self, mock_get_manager, mock_db_service):
        """Test manager initialization with custom database URL"""
        mock_db_service.return_value = Mock()
        mock_get_manager.return_value = Mock()
        
        custom_url = "sqlite:///custom.db"
        manager = CachedMarketDataManager(database_url=custom_url)
        
        mock_db_service.assert_called_once_with(custom_url)
    
    def test_enable_cache(self):
        """Test cache enable/disable functionality"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            
            # Test disabling cache
            manager.enable_cache(False)
            assert manager._cache_enabled is False
            
            # Test enabling cache
            manager.enable_cache(True)
            assert manager._cache_enabled is True


class TestCachedMarketDataManagerHistoricalData:
    """Test historical data retrieval functionality"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.db_service = Mock()
            manager.api_manager = Mock()
            return manager
    
    def test_get_historical_data_complete_cache_hit(self, mock_manager):
        """Test complete cache hit scenario"""
        # Mock cached data
        cached_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_manager.db_service.get_historical_data.return_value = cached_data
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        assert result is not None
        assert len(result) == 3
        assert mock_manager.stats.cache_hits == 1
        assert mock_manager.stats.cache_misses == 0
    
    def test_get_historical_data_cache_miss(self, mock_manager):
        """Test cache miss scenario"""
        # Mock no cached data
        mock_manager.db_service.get_historical_data.return_value = None
        
        # Mock API data
        api_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_manager._fetch_from_api = Mock(return_value=api_data)
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        assert result is not None
        assert len(result) == 3
        assert mock_manager.stats.cache_misses == 1
        assert mock_manager.stats.api_calls == 1
    
    def test_get_historical_data_partial_cache_hit(self, mock_manager):
        """Test partial cache hit scenario"""
        # Mock cached data with missing dates
        cached_data = pd.DataFrame({
            'open': [100, 102],
            'high': [105, 107],
            'low': [95, 97],
            'close': [103, 105],
            'volume': [1000, 1200]
        }, index=pd.date_range('2023-01-01', periods=2, freq='2D'))
        
        mock_manager.db_service.get_historical_data.return_value = cached_data
        
        # Mock missing data from API
        missing_data = pd.DataFrame({
            'open': [101],
            'high': [106],
            'low': [96],
            'close': [104],
            'volume': [1100]
        }, index=pd.date_range('2023-01-02', periods=1))
        
        mock_manager._fetch_missing_dates = Mock(return_value=missing_data)
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        assert result is not None
        assert len(result) == 3
        assert mock_manager.stats.cache_misses == 1
    
    def test_get_historical_data_database_only_mode(self, mock_manager):
        """Test database-only mode"""
        mock_manager.database_only = True
        
        # Mock no cached data
        mock_manager.db_service.get_historical_data.return_value = None
        
        # Mock the _fetch_from_api method to track if it's called
        mock_manager._fetch_from_api = Mock()
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        assert result is None
        # Should not call API in database-only mode
        mock_manager._fetch_from_api.assert_not_called()
    
    def test_get_historical_data_force_refresh(self, mock_manager):
        """Test force refresh functionality"""
        # Mock cached data
        cached_data = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [103],
            'volume': [1000]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        mock_manager.db_service.get_historical_data.return_value = cached_data
        
        # Mock API data
        api_data = pd.DataFrame({
            'open': [101],
            'high': [106],
            'low': [96],
            'close': [104],
            'volume': [1100]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        mock_manager._fetch_from_api = Mock(return_value=api_data)
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-01', force_refresh=True)
        
        assert result is not None
        # Should use API data instead of cached data
        assert result.iloc[0]['open'] == 101
    
    def test_get_historical_data_large_date_range(self, mock_manager):
        """Test large date range handling"""
        # Mock API data for large range
        api_data = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [103],
            'volume': [1000]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        mock_manager._fetch_from_api = Mock(return_value=api_data)
        
        # Large date range (more than 180 days)
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-12-31')
        
        assert result is not None
        # Should force API fetch for large ranges
        mock_manager._fetch_from_api.assert_called_once()
    
    def test_get_historical_data_error_handling(self, mock_manager):
        """Test error handling in historical data retrieval"""
        # Mock exception
        mock_manager.db_service.get_historical_data.side_effect = Exception("Database error")
        
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        assert result is None


class TestCachedMarketDataManagerMultipleSymbols:
    """Test multiple symbols processing"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.get_historical_data = Mock()
            return manager
    
    def test_get_multiple_symbols_success(self, mock_manager):
        """Test successful multiple symbols retrieval"""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        # Mock successful data for each symbol
        mock_manager.get_historical_data.side_effect = [
            pd.DataFrame({'close': [100, 101]}, index=pd.date_range('2023-01-01', periods=2)),
            pd.DataFrame({'close': [200, 201]}, index=pd.date_range('2023-01-01', periods=2)),
            pd.DataFrame({'close': [300, 301]}, index=pd.date_range('2023-01-01', periods=2))
        ]
        
        results = mock_manager.get_multiple_symbols(symbols, '2023-01-01', '2023-01-02')
        
        assert len(results) == 3
        assert 'AAPL' in results
        assert 'GOOGL' in results
        assert 'MSFT' in results
        assert len(results['AAPL']) == 2
        assert len(results['GOOGL']) == 2
        assert len(results['MSFT']) == 2
    
    def test_get_multiple_symbols_partial_failure(self, mock_manager):
        """Test multiple symbols with partial failures"""
        symbols = ['AAPL', 'INVALID', 'MSFT']
        
        # Mock mixed results
        mock_manager.get_historical_data.side_effect = [
            pd.DataFrame({'close': [100, 101]}, index=pd.date_range('2023-01-01', periods=2)),
            None,  # Invalid symbol returns None
            pd.DataFrame({'close': [300, 301]}, index=pd.date_range('2023-01-01', periods=2))
        ]
        
        results = mock_manager.get_multiple_symbols(symbols, '2023-01-01', '2023-01-02')
        
        assert len(results) == 2
        assert 'AAPL' in results
        assert 'MSFT' in results
        assert 'INVALID' not in results
    
    def test_get_multiple_symbols_all_failures(self, mock_manager):
        """Test multiple symbols with all failures"""
        symbols = ['INVALID1', 'INVALID2', 'INVALID3']
        
        # Mock all failures
        mock_manager.get_historical_data.return_value = None
        
        results = mock_manager.get_multiple_symbols(symbols, '2023-01-01', '2023-01-02')
        
        assert len(results) == 0


class TestCachedMarketDataManagerAPIFetching:
    """Test API fetching functionality"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.api_manager = Mock()
            return manager
    
    def test_fetch_from_api_success(self, mock_manager):
        """Test successful API fetch"""
        # Mock API data
        api_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.get_historical_data.return_value = api_data
        mock_manager.api_manager.providers = [mock_provider]
        
        result = mock_manager._fetch_from_api('AAPL', '2023-01-01', '2023-01-03', '1d')
        
        assert result is not None
        assert len(result) == 3
        mock_provider.get_historical_data.assert_called_once()
    
    def test_fetch_from_api_fallback(self, mock_manager):
        """Test API fetch with fallback to second provider"""
        # Mock first provider failure
        mock_provider1 = Mock()
        mock_provider1.get_historical_data.side_effect = Exception("Provider 1 failed")
        
        # Mock second provider success
        api_data = pd.DataFrame({
            'open': [100, 101],
            'high': [105, 106],
            'low': [95, 96],
            'close': [103, 104],
            'volume': [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        
        mock_provider2 = Mock()
        mock_provider2.get_historical_data.return_value = api_data
        
        mock_manager.api_manager.providers = [mock_provider1, mock_provider2]
        
        result = mock_manager._fetch_from_api('AAPL', '2023-01-01', '2023-01-02', '1d')
        
        assert result is not None
        assert len(result) == 2
        mock_provider1.get_historical_data.assert_called_once()
        mock_provider2.get_historical_data.assert_called_once()
    
    def test_fetch_from_api_all_providers_fail(self, mock_manager):
        """Test API fetch when all providers fail"""
        # Mock all providers failing
        mock_provider1 = Mock()
        mock_provider1.get_historical_data.side_effect = Exception("Provider 1 failed")
        
        mock_provider2 = Mock()
        mock_provider2.get_historical_data.side_effect = Exception("Provider 2 failed")
        
        mock_manager.api_manager.providers = [mock_provider1, mock_provider2]
        
        result = mock_manager._fetch_from_api('AAPL', '2023-01-01', '2023-01-02', '1d')
        
        assert result is None
    
    def test_fetch_missing_dates_success(self, mock_manager):
        """Test fetching missing dates successfully"""
        missing_dates = {date(2023, 1, 2), date(2023, 1, 3)}
        
        # Mock API data for missing dates
        api_data = pd.DataFrame({
            'open': [101, 102],
            'high': [106, 107],
            'low': [96, 97],
            'close': [104, 105],
            'volume': [1100, 1200]
        }, index=pd.date_range('2023-01-02', periods=2))
        
        mock_manager._fetch_from_api = Mock(return_value=api_data)
        
        result = mock_manager._fetch_missing_dates('AAPL', missing_dates, '1d')
        
        assert result is not None
        assert len(result) == 2
        mock_manager._fetch_from_api.assert_called_once()
    
    def test_fetch_missing_dates_empty(self, mock_manager):
        """Test fetching missing dates with empty set"""
        result = mock_manager._fetch_missing_dates('AAPL', set(), '1d')
        
        assert result is None
    
    def test_fetch_missing_dates_api_failure(self, mock_manager):
        """Test fetching missing dates when API fails"""
        missing_dates = {date(2023, 1, 2)}
        
        mock_manager._fetch_from_api = Mock(return_value=None)
        
        result = mock_manager._fetch_missing_dates('AAPL', missing_dates, '1d')
        
        assert result is None


class TestCachedMarketDataManagerDateHandling:
    """Test date handling functionality"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            return manager
    
    def test_generate_date_range_weekdays(self, mock_manager):
        """Test date range generation for weekdays"""
        start_date = date(2023, 1, 2)  # Monday
        end_date = date(2023, 1, 6)    # Friday
        
        dates = mock_manager._generate_date_range(start_date, end_date)
        
        assert len(dates) == 5  # Monday through Friday
        assert date(2023, 1, 2) in dates  # Monday
        assert date(2023, 1, 6) in dates  # Friday
        assert date(2023, 1, 7) not in dates  # Saturday
        assert date(2023, 1, 8) not in dates  # Sunday
    
    def test_generate_date_range_with_weekends(self, mock_manager):
        """Test date range generation including weekends"""
        start_date = date(2023, 1, 6)  # Friday
        end_date = date(2023, 1, 9)    # Monday
        
        dates = mock_manager._generate_date_range(start_date, end_date)
        
        assert len(dates) == 2  # Friday and Monday only
        assert date(2023, 1, 6) in dates  # Friday
        assert date(2023, 1, 9) in dates  # Monday
        assert date(2023, 1, 7) not in dates  # Saturday
        assert date(2023, 1, 8) not in dates  # Sunday
    
    def test_generate_date_range_single_day(self, mock_manager):
        """Test date range generation for single day"""
        start_date = date(2023, 1, 2)  # Monday
        end_date = date(2023, 1, 2)    # Same Monday
        
        dates = mock_manager._generate_date_range(start_date, end_date)
        
        assert len(dates) == 1
        assert date(2023, 1, 2) in dates


class TestCachedMarketDataManagerStatistics:
    """Test statistics and performance tracking"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.db_service = Mock()
            return manager
    
    def test_get_stats(self, mock_manager):
        """Test getting cache statistics"""
        # Simulate some cache activity
        mock_manager.stats.update_hit()
        mock_manager.stats.update_miss(2)
        mock_manager.stats.update_hit()
        
        stats = mock_manager.get_stats()
        
        assert stats['total_requests'] == 3
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['api_calls'] == 2
        assert stats['cache_hit_rate'] == pytest.approx(66.67, abs=0.01)
        assert stats['cache_enabled'] is True
    
    def test_get_cache_status(self, mock_manager):
        """Test getting cache status for a symbol"""
        mock_manager.db_service.get_cache_status.return_value = {
            'symbol': 'AAPL',
            'last_updated': '2023-01-01',
            'record_count': 100
        }
        
        status = mock_manager.get_cache_status('AAPL')
        
        assert status['symbol'] == 'AAPL'
        assert status['last_updated'] == '2023-01-01'
        assert status['record_count'] == 100
        mock_manager.db_service.get_cache_status.assert_called_once_with('AAPL')
    
    def test_cleanup_old_data(self, mock_manager):
        """Test cleanup of old data"""
        mock_manager.db_service.cleanup_old_data.return_value = 50
        
        result = mock_manager.cleanup_old_data(days_to_keep=365)
        
        assert result == 50
        mock_manager.db_service.cleanup_old_data.assert_called_once_with(365)


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    @patch('src.services.market_data.cached_market_data_manager.CachedMarketDataManager')
    def test_get_cached_market_data_manager(self, mock_manager_class):
        """Test global function to get cached market data manager"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        result = get_cached_market_data_manager()
        
        assert result == mock_manager
        mock_manager_class.assert_called_once()
    
    @patch('src.services.market_data.cached_market_data_manager.CachedMarketDataManager')
    def test_get_cached_market_data_manager_with_url(self, mock_manager_class):
        """Test global function with custom database URL"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        custom_url = "sqlite:///custom.db"
        result = get_cached_market_data_manager(database_url=custom_url)
        
        assert result == mock_manager
        mock_manager_class.assert_called_once()


class TestCachedMarketDataManagerEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.db_service = Mock()
            manager.api_manager = Mock()
            return manager
    
    def test_get_historical_data_invalid_date_format(self, mock_manager):
        """Test handling of invalid date format"""
        result = mock_manager.get_historical_data('AAPL', 'invalid-date', '2023-01-03')
        
        assert result is None
    
    def test_get_historical_data_reversed_dates(self, mock_manager):
        """Test handling of reversed start/end dates"""
        result = mock_manager.get_historical_data('AAPL', '2023-01-03', '2023-01-01')
        
        # Should handle gracefully
        assert result is None or isinstance(result, pd.DataFrame)
    
    def test_get_historical_data_empty_symbol(self, mock_manager):
        """Test handling of empty symbol"""
        result = mock_manager.get_historical_data('', '2023-01-01', '2023-01-03')
        
        assert result is None
    
    def test_get_historical_data_none_symbol(self, mock_manager):
        """Test handling of None symbol"""
        result = mock_manager.get_historical_data(None, '2023-01-01', '2023-01-03')
        
        assert result is None
    
    def test_get_multiple_symbols_empty_list(self, mock_manager):
        """Test handling of empty symbols list"""
        results = mock_manager.get_multiple_symbols([], '2023-01-01', '2023-01-03')
        
        assert len(results) == 0
    
    def test_get_multiple_symbols_none_list(self, mock_manager):
        """Test handling of None symbols list"""
        with pytest.raises(TypeError):
            mock_manager.get_multiple_symbols(None, '2023-01-01', '2023-01-03')


class TestCachedMarketDataManagerIntegration:
    """Integration tests for CachedMarketDataManager"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock CachedMarketDataManager"""
        with patch('src.services.market_data.cached_market_data_manager.MarketDataDatabaseService'), \
             patch('src.services.market_data.cached_market_data_manager.get_market_data_manager'):
            
            manager = CachedMarketDataManager()
            manager.db_service = Mock()
            manager.api_manager = Mock()
            return manager
    
    def test_full_workflow_cache_hit(self, mock_manager):
        """Test complete workflow with cache hit"""
        # Mock cached data
        cached_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_manager.db_service.get_historical_data.return_value = cached_data
        
        # Test the full workflow
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        # Verify results
        assert result is not None
        assert len(result) == 3
        assert mock_manager.stats.cache_hits == 1
        assert mock_manager.stats.cache_misses == 0
        
        # Verify database was queried
        mock_manager.db_service.get_historical_data.assert_called_once()
    
    def test_full_workflow_cache_miss_with_storage(self, mock_manager):
        """Test complete workflow with cache miss and data storage"""
        # Mock no cached data
        mock_manager.db_service.get_historical_data.return_value = None
        
        # Mock API data
        api_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_manager._fetch_from_api = Mock(return_value=api_data)
        
        # Test the full workflow
        result = mock_manager.get_historical_data('AAPL', '2023-01-01', '2023-01-03')
        
        # Verify results
        assert result is not None
        assert len(result) == 3
        assert mock_manager.stats.cache_misses == 1
        assert mock_manager.stats.api_calls == 1
        
        # Verify data was stored
        mock_manager.db_service.store_historical_data.assert_called_once()
    
    def test_full_workflow_multiple_symbols(self, mock_manager):
        """Test complete workflow with multiple symbols"""
        symbols = ['AAPL', 'GOOGL']
        
        # Mock data for each symbol
        mock_manager.get_historical_data = Mock(side_effect=[
            pd.DataFrame({'close': [100, 101]}, index=pd.date_range('2023-01-01', periods=2)),
            pd.DataFrame({'close': [200, 201]}, index=pd.date_range('2023-01-01', periods=2))
        ])
        
        # Test the full workflow
        results = mock_manager.get_multiple_symbols(symbols, '2023-01-01', '2023-01-02')
        
        # Verify results
        assert len(results) == 2
        assert 'AAPL' in results
        assert 'GOOGL' in results
        
        # Verify each symbol was processed
        assert mock_manager.get_historical_data.call_count == 2 