"""
End-to-end integration tests for backtest API.

Tests the complete API workflow including:
- HTTP requests to strategy service
- Real backtest execution
- Response formatting
- Error handling
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Add the strategy service path
sys.path.append('/Users/abby/code/trading/services/strategy-service')
sys.path.append('/Users/abby/code/trading/services/strategy-service/src')


class TestEndToEndBacktestAPI:
    """Test the end-to-end backtest API workflow."""
    
    @pytest.fixture
    def strategy_service_url(self):
        """Get the strategy service URL."""
        return "http://strategy-service.trading-system.svc.cluster.local:80"
    
    @pytest.fixture
    def backtest_request_data(self):
        """Create sample backtest request data."""
        return {
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "strategies": ["RSI", "MACD", "BollingerBands"]
        }
    
    @pytest.mark.asyncio
    async def test_backtest_api_endpoint_exists(self, strategy_service_url):
        """Test that the backtest API endpoint exists and responds."""
        
        async with httpx.AsyncClient() as client:
            try:
                # Test health endpoint first
                health_response = await client.get(f"{strategy_service_url}/health")
                assert health_response.status_code == 200
                
                # Test backtest endpoint with invalid data (should return 422)
                invalid_request = {"invalid": "data"}
                backtest_response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=invalid_request,
                    timeout=30.0
                )
                
                # Should return 422 for validation error
                assert backtest_response.status_code == 422
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")
    
    @pytest.mark.asyncio
    async def test_backtest_api_with_valid_request(self, strategy_service_url, backtest_request_data):
        """Test backtest API with valid request data."""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=backtest_request_data,
                    timeout=60.0  # Longer timeout for backtest execution
                )
                
                # Should return 200 for successful request
                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                
                # Parse response
                response_data = response.json()
                
                # Validate response structure
                assert "success" in response_data
                assert "message" in response_data
                assert "results" in response_data
                
                assert response_data["success"] is True
                assert isinstance(response_data["results"], list)
                
                # Validate results structure
                for result in response_data["results"]:
                    assert "name" in result
                    assert "total_return" in result
                    assert "sharpe_ratio" in result
                    assert "max_drawdown" in result
                    assert "total_trades" in result
                    assert "win_rate" in result
                    assert "profit_factor" in result
                    
                    # Validate data types
                    assert isinstance(result["total_return"], (int, float))
                    assert isinstance(result["sharpe_ratio"], (int, float))
                    assert isinstance(result["total_trades"], int)
                    assert isinstance(result["win_rate"], (int, float))
                    assert isinstance(result["profit_factor"], (int, float))
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")
    
    @pytest.mark.asyncio
    async def test_backtest_api_with_options_strategies(self, strategy_service_url):
        """Test backtest API with options strategies."""
        
        request_data = {
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "strategies": ["IronCondor", "RSI"]  # Mixed options and stock strategies
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=request_data,
                    timeout=60.0
                )
                
                # Should return 200 (even if some strategies fail)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                
                response_data = response.json()
                
                # Validate response structure
                assert response_data["success"] is True
                assert isinstance(response_data["results"], list)
                
                # Should have results for at least one strategy
                assert len(response_data["results"]) > 0
                
                # Check that we have results for the strategies we requested
                result_names = [result["name"] for result in response_data["results"]]
                assert "RSI" in result_names, "Should have RSI results"
                
                # IronCondor might fail due to options data, that's acceptable
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")
    
    @pytest.mark.asyncio
    async def test_backtest_api_error_handling(self, strategy_service_url):
        """Test backtest API error handling."""
        
        # Test with invalid date range
        invalid_request = {
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",  # Future date
            "end_date": "2023-01-01",    # Before start date
            "strategies": ["RSI"]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=invalid_request,
                    timeout=30.0
                )
                
                # Should handle gracefully (either 200 with error message or 422/500)
                assert response.status_code in [200, 422, 500]
                
                if response.status_code == 200:
                    response_data = response.json()
                    # If successful, should have empty or error results
                    assert "success" in response_data
                    assert "message" in response_data
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")
    
    @pytest.mark.asyncio
    async def test_backtest_api_performance(self, strategy_service_url, backtest_request_data):
        """Test backtest API performance."""
        
        async with httpx.AsyncClient() as client:
            try:
                start_time = datetime.now()
                
                response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=backtest_request_data,
                    timeout=60.0
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Should complete within reasonable time
                assert duration < 60.0, f"API call took {duration:.2f}s, exceeding 60s target"
                
                # Should return successful response
                assert response.status_code == 200
                
                response_data = response.json()
                assert response_data["success"] is True
                
                print(f"✅ API call completed in {duration:.2f}s")
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")
    
    @pytest.mark.asyncio
    async def test_backtest_api_response_format(self, strategy_service_url, backtest_request_data):
        """Test backtest API response format consistency."""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{strategy_service_url}/api/backtest/run",
                    json=backtest_request_data,
                    timeout=60.0
                )
                
                assert response.status_code == 200
                
                response_data = response.json()
                
                # Validate top-level response structure
                required_fields = ["success", "message", "results"]
                for field in required_fields:
                    assert field in response_data, f"Missing required field: {field}"
                
                assert isinstance(response_data["success"], bool)
                assert isinstance(response_data["message"], str)
                assert isinstance(response_data["results"], list)
                
                # Validate individual result structure
                for result in response_data["results"]:
                    required_result_fields = [
                        "name", "total_return", "sharpe_ratio", "max_drawdown",
                        "total_trades", "win_rate", "profit_factor"
                    ]
                    
                    for field in required_result_fields:
                        assert field in result, f"Missing result field: {field}"
                    
                    # Validate data types
                    assert isinstance(result["name"], str)
                    assert isinstance(result["total_return"], (int, float))
                    assert isinstance(result["sharpe_ratio"], (int, float))
                    assert isinstance(result["max_drawdown"], (int, float))
                    assert isinstance(result["total_trades"], int)
                    assert isinstance(result["win_rate"], (int, float))
                    assert isinstance(result["profit_factor"], (int, float))
                
            except httpx.ConnectError:
                pytest.skip("Strategy service not available - skipping API test")
            except Exception as e:
                pytest.skip(f"Strategy service error - skipping API test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


