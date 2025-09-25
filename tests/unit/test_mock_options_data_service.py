"""
Unit Tests: MockOptionsDataService
=================================
Unit tests for the MockOptionsDataService functionality.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/strategy-service/src'))

def test_mock_options_data_service_initialization():
    """Test MockOptionsDataService initialization"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    # Test default initialization
    service = MockOptionsDataService()
    assert service is not None
    assert hasattr(service, 'generator')
    assert hasattr(service, 'error_handler')
    assert hasattr(service, 'cache')
    
    # Test with custom parameters
    service_custom = MockOptionsDataService(base_iv=0.3, volume_range=(50, 5000))
    assert service_custom.generator.base_iv == 0.3
    assert service_custom.generator.volume_range == (50, 5000)

def test_get_liquid_options():
    """Test get_liquid_options method"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # Test with valid symbol
    options = service.get_liquid_options("AAPL", min_volume=10)
    
    assert isinstance(options, list)
    assert len(options) > 0
    
    # Check option structure
    if options:
        option = options[0]
        required_fields = [
            'symbol', 'option_type', 'strike', 'expiration', 'price',
            'volume', 'delta', 'gamma', 'theta', 'vega',
            'implied_volatility', 'bid', 'ask', 'open_interest'
        ]
        
        for field in required_fields:
            assert field in option, f"Missing field: {field}"
        
        assert option['symbol'] == "AAPL"
        assert option['option_type'] in ['call', 'put']
        assert option['volume'] >= 10
        assert option['price'] > 0
        assert -1 <= option['delta'] <= 1

def test_get_liquid_options_with_historical_support():
    """Test get_liquid_options_with_historical_support method"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # Test with historical date
    historical_date = "2023-06-15"
    options = service.get_liquid_options_with_historical_support(
        "AAPL", min_volume=10, historical_date=historical_date
    )
    
    assert isinstance(options, list)
    assert len(options) > 0
    
    # Check that options have historical_date field
    if options:
        option = options[0]
        assert 'historical_date' in option
        assert option['historical_date'] == historical_date

def test_generate_mock_options_chain():
    """Test generate_mock_options_chain method"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # Test with default parameters
    options_chain = service.generate_mock_options_chain("AAPL")
    
    assert isinstance(options_chain, list)
    assert len(options_chain) > 0
    
    # Test with custom parameters
    current_price = 200.0
    options_chain_custom = service.generate_mock_options_chain("AAPL", current_price)
    
    assert isinstance(options_chain_custom, list)
    assert len(options_chain_custom) > 0

def test_can_execute_with_options_data():
    """Test can_execute_with_options_data method"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # Mock service should always be able to execute
    assert service.can_execute_with_options_data() == True

def test_get_service_status():
    """Test get_service_status method"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    status = service.get_service_status()
    
    assert isinstance(status, dict)
    assert 'service_type' in status
    assert 'status' in status
    assert 'cache_size' in status
    assert 'generator_config' in status
    
    assert status['service_type'] == "mock_options_data"
    assert status['status'] == "active"

def test_cache_functionality():
    """Test caching functionality"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # First call - should populate cache
    options1 = service.get_liquid_options("AAPL", min_volume=10)
    cache_size_1 = len(service.cache)
    
    # Second call with same parameters - should use cache
    options2 = service.get_liquid_options("AAPL", min_volume=10)
    cache_size_2 = len(service.cache)
    
    # Cache size should be the same
    assert cache_size_1 == cache_size_2
    
    # Results should be the same (deterministic mock data)
    assert len(options1) == len(options2)

def test_error_handling():
    """Test error handling in MockOptionsDataService"""
    
    from src.services.mock_options_data_service import MockOptionsDataService, OptionsDataError
    
    service = MockOptionsDataService()
    
    # Test with invalid symbol (should not raise exception)
    try:
        options = service.get_liquid_options("", min_volume=10)
        assert isinstance(options, list)  # Should return empty list or handle gracefully
    except OptionsDataError:
        # This is also acceptable - error handling is working
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception type: {type(e)}")

def test_volume_filtering():
    """Test volume filtering functionality"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    # Test with different volume requirements
    options_low_volume = service.get_liquid_options("AAPL", min_volume=100)
    options_high_volume = service.get_liquid_options("AAPL", min_volume=1000)
    
    # High volume requirement should return fewer or equal options
    assert len(options_high_volume) <= len(options_low_volume)
    
    # All returned options should meet volume requirement
    for option in options_high_volume:
        assert option['volume'] >= 1000

def test_options_pricing_realism():
    """Test that mock options pricing is realistic"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    options = service.get_liquid_options("AAPL", min_volume=10)
    
    if options:
        for option in options:
            # Price should be positive
            assert option['price'] > 0
            
            # Bid should be less than or equal to ask
            assert option['bid'] <= option['ask']
            
            # Spread should be reasonable (not too wide)
            if option['price'] > 0:
                spread_pct = (option['ask'] - option['bid']) / option['price']
                assert spread_pct < 0.5  # Spread should be less than 50%
            
            # Greeks should be reasonable
            assert -1 <= option['delta'] <= 1
            assert option['gamma'] >= 0
            assert option['theta'] <= 0  # Theta should be negative (time decay)
            assert option['vega'] >= 0

def test_multiple_symbols():
    """Test service with multiple symbols"""
    
    from src.services.mock_options_data_service import MockOptionsDataService
    
    service = MockOptionsDataService()
    
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    
    for symbol in symbols:
        options = service.get_liquid_options(symbol, min_volume=10)
        assert isinstance(options, list)
        assert len(options) > 0
        
        # All options should have the correct symbol
        for option in options:
            assert option['symbol'] == symbol

if __name__ == "__main__":
    pytest.main([__file__])


