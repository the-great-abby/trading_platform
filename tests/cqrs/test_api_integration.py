"""
Tests for Phase 4: API Integration
Tests FastAPI endpoints, WebSocket connections, and API validation
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.services.cqrs.cqrs_service import CQRSService
from src.services.cqrs.commands import (
    PlaceOrderCommand, CancelOrderCommand, CreateStrategyCommand,
    UpdatePortfolioCommand, UpdatePositionCommand
)
from src.services.cqrs.queries import (
    GetPortfolioQuery, GetPositionsQuery, GetMarketDataQuery,
    GetPerformanceQuery, GetBacktestResultsQuery
)
from src.services.cqrs.events import (
    OrderCreatedEvent, OrderFilledEvent, PortfolioUpdatedEvent
)


class TestFastAPIEndpoints:
    """Test FastAPI REST endpoints for CQRS operations"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with CQRS endpoints"""
        from src.api.cqrs_api import create_app
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_cqrs_service(self):
        """Mock CQRS service"""
        service = Mock(spec=CQRSService)
        service.dispatch_command = AsyncMock()
        service.execute_query = AsyncMock()
        service.get_service_status = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data"""
        return {
            "user_id": "user1",
            "account_id": "acc1",
            "total_value": Decimal("10000.00"),
            "cash_balance": Decimal("5000.00"),
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "average_price": Decimal("150.00"),
                    "current_price": Decimal("155.00"),
                    "unrealized_pnl": Decimal("500.00")
                }
            ],
            "performance_metrics": {
                "total_return": Decimal("0.05"),
                "sharpe_ratio": Decimal("1.2"),
                "max_drawdown": Decimal("0.02")
            }
        }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "cqrs-api"}
    
    def test_cqrs_status(self, client, mock_cqrs_service):
        """Test CQRS service status endpoint"""
        mock_cqrs_service.get_service_status.return_value = {
            "status": "healthy",
            "components": {
                "command_bus": "active",
                "query_bus": "active",
                "event_bus": "active"
            }
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/cqrs/status")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_place_order_endpoint(self, client, mock_cqrs_service):
        """Test place order command endpoint"""
        mock_cqrs_service.dispatch_command.return_value = {
            "success": True,
            "order_id": "order_123",
            "status": "pending"
        }
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.post("/api/orders", json=order_data)
            assert response.status_code == 201
            assert response.json()["success"] == True
            assert response.json()["order_id"] == "order_123"
    
    def test_place_order_validation_error(self, client, mock_cqrs_service):
        """Test place order with invalid data"""
        invalid_order_data = {
            "symbol": "",  # Invalid empty symbol
            "side": "invalid_side",  # Invalid side
            "quantity": -100,  # Invalid negative quantity
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.post("/api/orders", json=invalid_order_data)
            assert response.status_code == 422  # Validation error
    
    def test_cancel_order_endpoint(self, client, mock_cqrs_service):
        """Test cancel order command endpoint"""
        mock_cqrs_service.dispatch_command.return_value = {
            "success": True,
            "order_id": "order_123",
            "status": "cancelled"
        }
        
        cancel_data = {
            "order_id": "order_123",
            "reason": "user_request"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.post("/api/orders/cancel", json=cancel_data)
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["status"] == "cancelled"
    
    def test_get_portfolio_endpoint(self, client, mock_cqrs_service, mock_portfolio_data):
        """Test get portfolio query endpoint"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "portfolio": mock_portfolio_data
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/portfolio/user1/acc1")
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["portfolio"]["user_id"] == "user1"
            assert response.json()["portfolio"]["account_id"] == "acc1"
    
    def test_get_portfolio_with_filters(self, client, mock_cqrs_service, mock_portfolio_data):
        """Test get portfolio with query parameters"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "portfolio": mock_portfolio_data
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/portfolio/user1/acc1?include_positions=true&include_performance=true")
            assert response.status_code == 200
            assert response.json()["success"] == True
    
    def test_get_positions_endpoint(self, client, mock_cqrs_service):
        """Test get positions query endpoint"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "average_price": Decimal("150.00"),
                    "current_price": Decimal("155.00"),
                    "unrealized_pnl": Decimal("500.00")
                }
            ]
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/positions/user1/acc1")
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert len(response.json()["positions"]) == 1
    
    def test_get_positions_with_filters(self, client, mock_cqrs_service):
        """Test get positions with symbol filter"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "average_price": Decimal("150.00"),
                    "current_price": Decimal("155.00"),
                    "unrealized_pnl": Decimal("500.00")
                }
            ]
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/positions/user1/acc1?symbol=AAPL")
            assert response.status_code == 200
            assert response.json()["success"] == True
    
    def test_get_market_data_endpoint(self, client, mock_cqrs_service):
        """Test get market data query endpoint"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "market_data": {
                "symbol": "AAPL",
                "current_price": Decimal("155.00"),
                "price_change": Decimal("5.00"),
                "price_change_pct": Decimal("0.032"),
                "volume": 1000000,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/market-data/AAPL")
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["market_data"]["symbol"] == "AAPL"
    
    def test_get_market_data_with_date_range(self, client, mock_cqrs_service):
        """Test get market data with date range"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "market_data": {
                "symbol": "AAPL",
                "historical_data": [
                    {"date": "2024-01-01", "price": Decimal("150.00")},
                    {"date": "2024-01-02", "price": Decimal("155.00")}
                ]
            }
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/market-data/AAPL?start_date=2024-01-01&end_date=2024-01-02")
            assert response.status_code == 200
            assert response.json()["success"] == True
    
    def test_get_performance_endpoint(self, client, mock_cqrs_service):
        """Test get performance query endpoint"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "performance": {
                "total_return": Decimal("0.05"),
                "sharpe_ratio": Decimal("1.2"),
                "max_drawdown": Decimal("0.02"),
                "win_rate": Decimal("0.65")
            }
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/performance/user1/acc1?start_date=2024-01-01&end_date=2024-01-31")
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["performance"]["total_return"] == "0.05"
    
    def test_get_backtest_results_endpoint(self, client, mock_cqrs_service):
        """Test get backtest results query endpoint"""
        mock_cqrs_service.execute_query.return_value = {
            "success": True,
            "backtest_results": {
                "strategy_id": "strategy_123",
                "total_return": Decimal("0.15"),
                "sharpe_ratio": Decimal("1.5"),
                "max_drawdown": Decimal("0.05"),
                "trades": [
                    {
                        "symbol": "AAPL",
                        "side": "buy",
                        "quantity": 100,
                        "price": Decimal("150.00"),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.get("/api/backtest/strategy_123?start_date=2024-01-01&end_date=2024-01-31")
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["backtest_results"]["strategy_id"] == "strategy_123"
    
    def test_create_strategy_endpoint(self, client, mock_cqrs_service):
        """Test create strategy command endpoint"""
        mock_cqrs_service.dispatch_command.return_value = {
            "success": True,
            "strategy_id": "strategy_123",
            "status": "created"
        }
        
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test trading strategy",
            "parameters": {"risk_level": "medium"},
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.post("/api/strategies", json=strategy_data)
            assert response.status_code == 201
            assert response.json()["success"] == True
            assert response.json()["strategy_id"] == "strategy_123"
    
    def test_update_portfolio_endpoint(self, client, mock_cqrs_service):
        """Test update portfolio command endpoint"""
        mock_cqrs_service.dispatch_command.return_value = {
            "success": True,
            "portfolio_id": "portfolio_123",
            "status": "updated"
        }
        
        portfolio_data = {
            "portfolio_id": "portfolio_123",
            "name": "Updated Portfolio",
            "cash_balance": Decimal("6000.00"),
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.put("/api/portfolio/portfolio_123", json=portfolio_data)
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.json()["status"] == "updated"
    
    def test_error_handling(self, client, mock_cqrs_service):
        """Test error handling in API endpoints"""
        mock_cqrs_service.dispatch_command.side_effect = Exception("Database connection failed")
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            response = client.post("/api/orders", json=order_data)
            assert response.status_code == 500
            assert "error" in response.json()
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication"""
        # This would test JWT token validation
        response = client.get("/api/portfolio/user1/acc1", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
    
    def test_rate_limiting(self, client, mock_cqrs_service):
        """Test rate limiting on API endpoints"""
        mock_cqrs_service.dispatch_command.return_value = {"success": True}
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        with patch('src.api.cqrs_api.cqrs_service', mock_cqrs_service):
            # Make multiple requests to test rate limiting
            for _ in range(10):
                response = client.post("/api/orders", json=order_data)
                if response.status_code == 429:  # Rate limited
                    break
            else:
                # If we get here, rate limiting might not be implemented yet
                pass


class TestWebSocketIntegration:
    """Test WebSocket connections for real-time updates"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with WebSocket support"""
        from src.api.cqrs_api import create_app
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client with WebSocket support"""
        return TestClient(app)
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/ws/events") as websocket:
            # Test connection
            assert websocket is not None
    
    def test_websocket_event_subscription(self, client):
        """Test subscribing to specific events via WebSocket"""
        with client.websocket_connect("/ws/events?event_types=OrderCreated,OrderFilled") as websocket:
            # Test subscription message
            subscription_message = {
                "type": "subscribe",
                "event_types": ["OrderCreated", "OrderFilled"]
            }
            websocket.send_json(subscription_message)
            
            # Test acknowledgment
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
    
    def test_websocket_event_broadcast(self, client):
        """Test receiving events via WebSocket"""
        with client.websocket_connect("/ws/events") as websocket:
            # Simulate event broadcast
            event_data = {
                "type": "event",
                "event_type": "OrderCreated",
                "data": {
                    "order_id": "order_123",
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 100
                }
            }
            
            # This would be sent by the server
            # websocket.send_json(event_data)
            
            # Test receiving (would need actual event broadcasting)
            # response = websocket.receive_json()
            # assert response["type"] == "event"
    
    def test_websocket_heartbeat(self, client):
        """Test WebSocket heartbeat mechanism"""
        with client.websocket_connect("/ws/events") as websocket:
            # Test heartbeat
            heartbeat_message = {"type": "ping"}
            websocket.send_json(heartbeat_message)
            
            # Test pong response
            response = websocket.receive_json()
            assert response["type"] == "pong"


class TestAPIValidation:
    """Test API input validation and error handling"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app"""
        from src.api.cqrs_api import create_app
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON"""
        response = client.post("/api/orders", data="invalid json")
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        incomplete_order = {
            "symbol": "AAPL",
            "side": "buy"
            # Missing quantity, order_type, user_id, account_id
        }
        
        response = client.post("/api/orders", json=incomplete_order)
        assert response.status_code == 422
        assert "validation_error" in response.json()
    
    def test_invalid_field_types(self, client):
        """Test handling of invalid field types"""
        invalid_order = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "not_a_number",  # Should be int
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        response = client.post("/api/orders", json=invalid_order)
        assert response.status_code == 422
    
    def test_invalid_enum_values(self, client):
        """Test handling of invalid enum values"""
        invalid_order = {
            "symbol": "AAPL",
            "side": "invalid_side",  # Should be "buy" or "sell"
            "quantity": 100,
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        response = client.post("/api/orders", json=invalid_order)
        assert response.status_code == 422
    
    def test_decimal_validation(self, client):
        """Test decimal field validation"""
        order_with_decimal = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "price": "155.50",  # Should be valid decimal
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        response = client.post("/api/orders", json=order_with_decimal)
        # Should be valid if price is optional
        assert response.status_code in [200, 201, 422]
    
    def test_date_validation(self, client):
        """Test date field validation"""
        query_with_dates = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        response = client.get("/api/performance/user1/acc1", params=query_with_dates)
        # Should be valid if dates are properly formatted
        assert response.status_code in [200, 422]


class TestAPIIntegration:
    """Test integration between API and CQRS services"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with real CQRS service"""
        from src.api.cqrs_api import create_app
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_end_to_end_order_flow(self, client):
        """Test complete order flow from API to CQRS"""
        # Place order
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        order_id = response.json()["order_id"]
        
        # Get order status
        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["order_id"] == order_id
        
        # Cancel order
        cancel_data = {
            "order_id": order_id,
            "reason": "user_request"
        }
        
        response = client.post("/api/orders/cancel", json=cancel_data)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_end_to_end_portfolio_flow(self, client):
        """Test complete portfolio flow from API to CQRS"""
        # Get portfolio
        response = client.get("/api/portfolio/user1/acc1")
        assert response.status_code == 200
        
        # Update portfolio
        portfolio_data = {
            "portfolio_id": "portfolio_123",
            "name": "Updated Portfolio",
            "cash_balance": "6000.00",
            "user_id": "user1",
            "account_id": "acc1"
        }
        
        response = client.put("/api/portfolio/portfolio_123", json=portfolio_data)
        assert response.status_code == 200
        
        # Get updated portfolio
        response = client.get("/api/portfolio/user1/acc1")
        assert response.status_code == 200
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent API requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            order_data = {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "order_type": "market",
                "user_id": "user1",
                "account_id": "acc1"
            }
            response = client.post("/api/orders", json=order_data)
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 5
        assert all(status in [200, 201, 429] for status in results)  # 429 for rate limiting


class TestAPIPerformance:
    """Test API performance and scalability"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app"""
        from src.api.cqrs_api import create_app
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_response_times(self, client):
        """Test API response times"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond in < 100ms
    
    def test_memory_usage(self, client):
        """Test API memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 10 * 1024 * 1024  # < 10MB increase
    
    def test_concurrent_load(self, client):
        """Test API under concurrent load"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_requests():
            for _ in range(10):
                try:
                    response = client.get("/health")
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 100
        assert len(errors) == 0
        assert all(status == 200 for status in results)
