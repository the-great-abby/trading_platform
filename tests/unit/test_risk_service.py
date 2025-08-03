"""
Unit tests for Risk Service
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import json

# Import the risk service app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/risk-service'))
from main import app

client = TestClient(app)


class TestRiskServiceHealth:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "risk-service"
    
    def test_status_endpoint(self):
        """Test status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "risk-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"


class TestPortfolioRiskAssessment:
    """Test portfolio risk assessment functionality"""
    
    def test_assess_portfolio_risk_basic(self):
        """Test basic portfolio risk assessment"""
        request_data = {
            "portfolio_value": 100000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": 100, "value": 15000.0},
                {"symbol": "MSFT", "quantity": 50, "value": 10000.0}
            ],
            "cash": 75000.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_risk_score" in data
        assert "max_position_size" in data
        assert "recommended_cash_reserve" in data
        assert "risk_metrics" in data
        
        # Validate risk score is between 0-100
        assert 0 <= data["total_risk_score"] <= 100
        
        # Validate recommendations
        assert data["max_position_size"] == 5000.0  # 5% of portfolio
        assert data["recommended_cash_reserve"] == 10000.0  # 10% of portfolio
    
    def test_assess_portfolio_risk_high_concentration(self):
        """Test portfolio risk assessment with high concentration"""
        request_data = {
            "portfolio_value": 100000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": 1000, "value": 150000.0}  # 150% of portfolio
            ],
            "cash": -50000.0  # Negative cash due to leverage
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should have high risk score due to concentration and leverage
        assert data["total_risk_score"] > 50
    
    def test_assess_portfolio_risk_low_risk(self):
        """Test portfolio risk assessment with low risk profile"""
        request_data = {
            "portfolio_value": 100000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": 10, "value": 1500.0},
                {"symbol": "MSFT", "quantity": 5, "value": 1000.0}
            ],
            "cash": 97500.0  # High cash ratio
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should have low risk score due to diversification and high cash
        assert data["total_risk_score"] < 30
    
    def test_assess_portfolio_risk_empty_portfolio(self):
        """Test portfolio risk assessment with empty portfolio"""
        request_data = {
            "portfolio_value": 100000.0,
            "positions": [],
            "cash": 100000.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should have very low risk score
        assert data["total_risk_score"] < 10
    
    def test_assess_portfolio_risk_invalid_data(self):
        """Test portfolio risk assessment with invalid data"""
        request_data = {
            "portfolio_value": -1000.0,  # Negative portfolio value
            "positions": [],
            "cash": 100000.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        # Should handle gracefully
        assert response.status_code == 200


class TestPositionRiskChecking:
    """Test position risk checking functionality"""
    
    def test_check_position_risk_safe(self):
        """Test position risk check for safe position"""
        request_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
            "portfolio_value": 100000.0
        }
        
        response = client.post("/risk/check-position", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_acceptable" in data
        assert "max_allowed_ratio" in data
        assert "max_allowed_value" in data
        assert "position_ratio" in data
        
        # Position value is 15% of portfolio, should be unacceptable
        assert data["position_ratio"] == 0.15
        assert data["max_allowed_ratio"] == 0.05
    
    def test_check_position_risk_large(self):
        """Test position risk check for large position"""
        request_data = {
            "symbol": "AAPL",
            "quantity": 1000,
            "price": 150.0,
            "portfolio_value": 100000.0
        }
        
        response = client.post("/risk/check-position", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Position value is 150% of portfolio, should be unacceptable
        assert data["position_ratio"] == 1.5
        assert data["is_acceptable"] == False
    
    def test_check_position_risk_zero_portfolio(self):
        """Test position risk check with zero portfolio value"""
        request_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
            "portfolio_value": 0.0
        }
        
        response = client.post("/risk/check-position", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should handle gracefully
        assert "is_acceptable" in data
        assert data["max_allowed_value"] == 0.0


class TestRiskLimits:
    """Test risk limits functionality"""
    
    def test_get_risk_limits(self):
        """Test getting risk limits"""
        response = client.get("/risk/limits")
        assert response.status_code == 200
        
        data = response.json()
        assert "max_portfolio_leverage" in data
        assert "max_drawdown" in data
        assert "daily_loss_limit" in data
        assert "max_concentration_risk" in data
        
        # Validate limits are reasonable
        assert data["max_portfolio_leverage"] > 1
        assert 0 < data["max_drawdown"] <= 1
        assert 0 < data["daily_loss_limit"] <= 1
        assert 0 < data["max_concentration_risk"] <= 1


class TestRiskMetrics:
    """Test risk metrics functionality"""
    
    def test_get_risk_metrics(self):
        """Test getting risk metrics"""
        response = client.get("/risk/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_risk_score" in data
        assert "max_drawdown" in data
        assert "sharpe_ratio" in data
        assert "beta" in data
        
        # Metrics should be reasonable
        assert 0 <= data["current_risk_score"] <= 100
        assert 0 <= data["max_drawdown"] <= 1
        assert data["sharpe_ratio"] > 0
        assert data["beta"] > 0


class TestPrometheusMetrics:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Should return Prometheus format
        content = response.text
        assert "risk_assessments_total" in content
        assert "risk_assessment_duration_seconds" in content
        assert "portfolio_risk_score" in content
        assert "position_risk_checks_total" in content


class TestRiskServiceIntegration:
    """Integration tests for risk service"""
    
    def test_complete_risk_workflow(self):
        """Test complete risk assessment workflow"""
        # 1. Check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # 2. Assess portfolio risk
        portfolio_request = {
            "portfolio_value": 100000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": 100, "value": 15000.0}
            ],
            "cash": 85000.0
        }
        portfolio_response = client.post("/risk/assess-portfolio", json=portfolio_request)
        assert portfolio_response.status_code == 200
        
        # 3. Check position risk
        position_request = {
            "symbol": "MSFT",
            "quantity": 50,
            "price": 200.0,
            "portfolio_value": 100000.0
        }
        position_response = client.post("/risk/check-position", json=position_request)
        assert position_response.status_code == 200
        
        # 4. Get risk limits
        limits_response = client.get("/risk/limits")
        assert limits_response.status_code == 200
        
        # 5. Get metrics
        metrics_response = client.get("/risk/metrics")
        assert metrics_response.status_code == 200
        
        # All endpoints should work together
        assert all([
            health_response.status_code == 200,
            portfolio_response.status_code == 200,
            position_response.status_code == 200,
            limits_response.status_code == 200,
            metrics_response.status_code == 200
        ])
    
    def test_risk_service_error_handling(self):
        """Test error handling in risk service"""
        # Test with malformed JSON
        response = client.post("/risk/assess-portfolio", data="invalid json")
        assert response.status_code == 422  # Validation error
        
        # Test with missing required fields
        response = client.post("/risk/assess-portfolio", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid endpoint
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404


class TestRiskServiceEdgeCases:
    """Test edge cases for risk service"""
    
    def test_extreme_portfolio_values(self):
        """Test with extreme portfolio values"""
        # Very large portfolio
        request_data = {
            "portfolio_value": 1000000000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": 10000, "value": 1500000.0}
            ],
            "cash": 998500000.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 0 <= data["total_risk_score"] <= 100
    
    def test_zero_values(self):
        """Test with zero values"""
        request_data = {
            "portfolio_value": 0.0,
            "positions": [],
            "cash": 0.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_risk_score" in data
    
    def test_negative_values(self):
        """Test with negative values"""
        request_data = {
            "portfolio_value": -1000.0,
            "positions": [
                {"symbol": "AAPL", "quantity": -100, "value": -15000.0}
            ],
            "cash": -5000.0
        }
        
        response = client.post("/risk/assess-portfolio", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_risk_score" in data 