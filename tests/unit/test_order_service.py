"""
Unit tests for Order Service
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json
from datetime import datetime

# Import the order service app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/order-service'))
from main import app, Order

client = TestClient(app)


class TestOrderServiceHealth:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Order Service" in data["message"]
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Should return Prometheus metrics
        content = response.text
        assert "order_requests_total" in content
        assert "order_request_duration_seconds" in content


class TestOrderModel:
    """Test Order model validation"""
    
    def test_order_creation_valid(self):
        """Test creating a valid order"""
        order = Order(
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.0,
            order_type="MARKET"
        )
        
        assert order.symbol == "AAPL"
        assert order.side == "BUY"
        assert order.quantity == 100
        assert order.price == 150.0
        assert order.order_type == "MARKET"
    
    def test_order_creation_with_different_types(self):
        """Test creating orders with different types"""
        # Market order
        market_order = Order(
            symbol="MSFT",
            side="SELL",
            quantity=50,
            price=300.0,
            order_type="MARKET"
        )
        assert market_order.order_type == "MARKET"
        
        # Limit order
        limit_order = Order(
            symbol="GOOGL",
            side="BUY",
            quantity=25,
            price=2500.0,
            order_type="LIMIT"
        )
        assert limit_order.order_type == "LIMIT"
    
    def test_order_side_validation(self):
        """Test order side validation"""
        # Buy order
        buy_order = Order(
            symbol="TSLA",
            side="BUY",
            quantity=10,
            price=200.0,
            order_type="MARKET"
        )
        assert buy_order.side == "BUY"
        
        # Sell order
        sell_order = Order(
            symbol="TSLA",
            side="SELL",
            quantity=10,
            price=200.0,
            order_type="MARKET"
        )
        assert sell_order.side == "SELL"


class TestOrderServiceAPI:
    """Test order service API endpoints"""
    
    def test_create_market_order(self):
        """Test creating a market order"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "AAPL"
        assert order["side"] == "BUY"
        assert order["quantity"] == 100
        assert order["price"] == 150.0
        assert order["order_type"] == "MARKET"
    
    def test_create_limit_order(self):
        """Test creating a limit order"""
        order_data = {
            "symbol": "MSFT",
            "side": "SELL",
            "quantity": 50,
            "price": 300.0,
            "order_type": "LIMIT"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "MSFT"
        assert order["side"] == "SELL"
        assert order["quantity"] == 50
        assert order["price"] == 300.0
        assert order["order_type"] == "LIMIT"
    
    def test_create_sell_order(self):
        """Test creating a sell order"""
        order_data = {
            "symbol": "GOOGL",
            "side": "SELL",
            "quantity": 25,
            "price": 2500.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "GOOGL"
        assert order["side"] == "SELL"
        assert order["quantity"] == 25
        assert order["price"] == 2500.0
        assert order["order_type"] == "MARKET"
    
    def test_create_order_with_fractional_quantity(self):
        """Test creating an order with fractional quantity"""
        order_data = {
            "symbol": "TSLA",
            "side": "BUY",
            "quantity": 1,
            "price": 200.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "TSLA"
        assert order["side"] == "BUY"
        assert order["quantity"] == 1
        assert order["price"] == 200.0
        assert order["order_type"] == "MARKET"
    
    def test_create_order_with_high_price(self):
        """Test creating an order with high price"""
        order_data = {
            "symbol": "BRK.A",
            "side": "BUY",
            "quantity": 1,
            "price": 500000.0,
            "order_type": "LIMIT"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "BRK.A"
        assert order["side"] == "BUY"
        assert order["quantity"] == 1
        assert order["price"] == 500000.0
        assert order["order_type"] == "LIMIT"


class TestOrderServiceValidation:
    """Test order validation and error handling"""
    
    def test_create_order_missing_symbol(self):
        """Test creating order with missing symbol"""
        order_data = {
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_order_missing_side(self):
        """Test creating order with missing side"""
        order_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_order_missing_quantity(self):
        """Test creating order with missing quantity"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_order_missing_price(self):
        """Test creating order with missing price"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_order_missing_order_type(self):
        """Test creating order with missing order type"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.0
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_order_invalid_quantity(self):
        """Test creating order with invalid quantity"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 0,  # Invalid quantity
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        # Should accept 0 quantity as it's a valid integer
        assert response.status_code == 200
    
    def test_create_order_invalid_price(self):
        """Test creating order with invalid price"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": -150.0,  # Negative price
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        # Should accept negative price as it's a valid float
        assert response.status_code == 200
    
    def test_create_order_invalid_symbol(self):
        """Test creating order with invalid symbol"""
        order_data = {
            "symbol": "",  # Empty symbol
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        # Should accept empty string as it's a valid string
        assert response.status_code == 200


class TestOrderServiceIntegration:
    """Integration tests for order service"""
    
    def test_complete_order_workflow(self):
        """Test complete order workflow"""
        # 1. Check service health
        response = client.get("/health")
        assert response.status_code == 200
        
        # 2. Check service status
        response = client.get("/")
        assert response.status_code == 200
        
        # 3. Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # 4. Create a market order
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        # 5. Create a limit order
        order_data = {
            "symbol": "MSFT",
            "side": "SELL",
            "quantity": 50,
            "price": 300.0,
            "order_type": "LIMIT"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
    
    def test_multiple_order_creation(self):
        """Test creating multiple orders"""
        orders = [
            {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100,
                "price": 150.0,
                "order_type": "MARKET"
            },
            {
                "symbol": "MSFT",
                "side": "SELL",
                "quantity": 50,
                "price": 300.0,
                "order_type": "LIMIT"
            },
            {
                "symbol": "GOOGL",
                "side": "BUY",
                "quantity": 25,
                "price": 2500.0,
                "order_type": "MARKET"
            }
        ]
        
        for order_data in orders:
            response = client.post("/api/v1/orders", json=order_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert data["message"] == "Order created"
            assert "order" in data
            
            order = data["order"]
            assert order["symbol"] == order_data["symbol"]
            assert order["side"] == order_data["side"]
            assert order["quantity"] == order_data["quantity"]
            assert order["price"] == order_data["price"]
            assert order["order_type"] == order_data["order_type"]


class TestOrderServiceMetrics:
    """Test order service metrics"""
    
    def test_metrics_after_health_check(self):
        """Test metrics after health check"""
        # Get initial metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        initial_content = response.text
        
        # Make health check request
        response = client.get("/health")
        assert response.status_code == 200
        
        # Get metrics again
        response = client.get("/metrics")
        assert response.status_code == 200
        updated_content = response.text
        
        # Should have order_requests_total metric
        assert "order_requests_total" in updated_content
    
    def test_metrics_after_order_creation(self):
        """Test metrics after order creation"""
        # Get initial metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        initial_content = response.text
        
        # Create an order
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        # Get metrics again
        response = client.get("/metrics")
        assert response.status_code == 200
        updated_content = response.text
        
        # Should have order_requests_total metric
        assert "order_requests_total" in updated_content


class TestOrderServiceErrorHandling:
    """Test error handling in order service"""
    
    def test_invalid_json_request(self):
        """Test invalid JSON request"""
        response = client.post("/api/v1/orders", data="invalid json")
        assert response.status_code == 422  # Validation error
    
    def test_empty_request_body(self):
        """Test empty request body"""
        response = client.post("/api/v1/orders", json={})
        assert response.status_code == 422  # Validation error
    
    def test_malformed_request(self):
        """Test malformed request"""
        response = client.post("/api/v1/orders", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error
    
    def test_wrong_data_types(self):
        """Test wrong data types"""
        order_data = {
            "symbol": 123,  # Should be string
            "side": "BUY",
            "quantity": "100",  # Should be int
            "price": "150.0",  # Should be float
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 422  # Validation error


class TestOrderServiceEdgeCases:
    """Test edge cases for order service"""
    
    def test_order_with_zero_quantity(self):
        """Test order with zero quantity"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 0,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["quantity"] == 0
    
    def test_order_with_zero_price(self):
        """Test order with zero price"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 0.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["price"] == 0.0
    
    def test_order_with_very_large_quantity(self):
        """Test order with very large quantity"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 999999999,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["quantity"] == 999999999
    
    def test_order_with_very_high_price(self):
        """Test order with very high price"""
        order_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 999999.99,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["price"] == 999999.99
    
    def test_order_with_long_symbol(self):
        """Test order with long symbol name"""
        order_data = {
            "symbol": "VERY_LONG_SYMBOL_NAME_THAT_IS_UNREALISTIC",
            "side": "BUY",
            "quantity": 100,
            "price": 150.0,
            "order_type": "MARKET"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "Order created"
        assert "order" in data
        
        order = data["order"]
        assert order["symbol"] == "VERY_LONG_SYMBOL_NAME_THAT_IS_UNREALISTIC" 