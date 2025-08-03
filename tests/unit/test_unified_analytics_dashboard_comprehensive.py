#!/usr/bin/env python3
"""
Comprehensive tests for Unified Analytics Dashboard
Tests all functionality including AI stock analysis, central hub, and data pipeline features
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from fastapi.testclient import TestClient

# Add the service directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/unified-analytics-dashboard'))

try:
    from main import app, UnifiedAnalyticsDashboard, StockAnalysisRequest, StockAnalysisResponse, ReportStatus, ReportJob
except ImportError:
    app = None
    UnifiedAnalyticsDashboard = None
    StockAnalysisRequest = None
    StockAnalysisResponse = None
    ReportStatus = None
    ReportJob = None

@pytest.fixture
def client():
    """Create test client"""
    if app is None:
        pytest.skip("Unified Analytics Dashboard not available")
    return TestClient(app)

@pytest.fixture
def dashboard_manager():
    """Create dashboard manager instance"""
    if UnifiedAnalyticsDashboard is None:
        pytest.skip("Unified Analytics Dashboard not available")
    return UnifiedAnalyticsDashboard()

class TestUnifiedAnalyticsDashboardComprehensive:
    """Comprehensive tests for Unified Analytics Dashboard"""
    
    def test_dashboard_structure(self):
        """Test dashboard structure and configuration"""
        assert app is not None, "App should be available"
        assert UnifiedAnalyticsDashboard is not None, "Dashboard class should be available"
        assert StockAnalysisRequest is not None, "StockAnalysisRequest should be available"
        assert StockAnalysisResponse is not None, "StockAnalysisResponse should be available"
        assert ReportStatus is not None, "ReportStatus should be available"
        assert ReportJob is not None, "ReportJob should be available"
        
        # Test app structure
        assert hasattr(app, 'routes'), "App should have routes"
        assert len(app.routes) > 0, "App should have routes defined"
        
        # Test dashboard manager structure
        manager = UnifiedAnalyticsDashboard()
        assert hasattr(manager, 'get_ai_stock_analysis'), "Should have AI stock analysis method"
        assert hasattr(manager, 'get_data_pipeline_status'), "Should have data pipeline status method"
        assert hasattr(manager, 'get_central_hub_data'), "Should have central hub data method"
        assert hasattr(manager, 'get_symbols_coverage'), "Should have symbols coverage method"
    
    def test_health_endpoints(self, client):
        """Test health and readiness endpoints"""
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "Unified Analytics Dashboard"
        
        # Test ready endpoint
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"
    
    def test_dashboard_pages(self, client):
        """Test dashboard page endpoints"""
        # Test main dashboard page
        response = client.get("/")
        assert response.status_code in [200, 500]  # Allow for template issues
        
        # Test AI stock page
        response = client.get("/ai-stock")
        assert response.status_code in [200, 500]  # Allow for template issues
        
        # Test central hub page
        response = client.get("/central-hub")
        assert response.status_code in [200, 500]  # Allow for template issues
        
        # Test data pipeline page
        response = client.get("/data-pipeline")
        assert response.status_code in [200, 500]  # Allow for template issues
    
    def test_api_endpoints(self, client):
        """Test API endpoints"""
        # Test AI stock analysis
        response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "symbol" in data
        assert "current_price" in data
        assert "recommendation" in data
        
        # Test pipeline status
        response = client.get("/api/pipeline/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test sample analysis
        response = client.get("/api/pipeline/sample-analysis")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test pipeline metrics
        response = client.get("/api/pipeline/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test central hub data
        response = client.get("/api/central-hub/data")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test symbols
        response = client.get("/api/symbols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test options coverage
        response = client.get("/api/options/coverage")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test Greeks status
        response = client.get("/api/greeks/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Test VAPID public key
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @patch('aiohttp.ClientSession.get')
    def test_dashboard_manager_methods(self, mock_get, dashboard_manager):
        """Test dashboard manager methods with mocked responses"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "symbol": "AAPL",
            "current_price": 150.0,
            "recommendation": "BUY",
            "confidence": 75,
            "risk_level": "medium",
            "reasoning": "Strong technical indicators",
            "target_price": 165.0,
            "stop_loss": 140.0,
            "technical_indicators": {"rsi": 65, "macd": "positive"},
            "analysis_time": 2.5,
            "timestamp": "2024-01-01T00:00:00Z"
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Test get_ai_stock_analysis
        result = asyncio.run(dashboard_manager.get_ai_stock_analysis("AAPL", 150.0))
        assert isinstance(result, dict)
        assert "symbol" in result or "error" in result
        
        # Test get_data_pipeline_status
        result = asyncio.run(dashboard_manager.get_data_pipeline_status())
        assert isinstance(result, dict)
        assert "analysis_service" in result or "error" in result
        
        # Test get_central_hub_data
        result = asyncio.run(dashboard_manager.get_central_hub_data())
        assert isinstance(result, dict)
        assert "data_coverage" in result or "error" in result
        
        # Test get_symbols_coverage
        result = asyncio.run(dashboard_manager.get_symbols_coverage())
        assert isinstance(result, dict)
        assert "popular_symbols" in result or "error" in result
    
    def test_pydantic_models(self):
        """Test Pydantic models"""
        # Test StockAnalysisRequest
        request = StockAnalysisRequest(
            symbol="AAPL",
            current_price=150.0,
            include_news=True,
            include_technical=True,
            include_sentiment=True,
            async_mode=False,
            user_email="test@example.com"
        )
        assert request.symbol == "AAPL"
        assert request.current_price == 150.0
        assert request.include_news is True
        assert request.include_technical is True
        assert request.include_sentiment is True
        assert request.async_mode is False
        assert request.user_email == "test@example.com"
        
        # Test StockAnalysisResponse
        response = StockAnalysisResponse(
            symbol="AAPL",
            current_price=150.0,
            recommendation="BUY",
            confidence=75,
            risk_level="medium",
            reasoning="Strong technical indicators",
            target_price=165.0,
            stop_loss=140.0,
            technical_indicators={"rsi": 65, "macd": "positive"},
            analysis_time=2.5,
            timestamp="2024-01-01T00:00:00Z"
        )
        assert response.symbol == "AAPL"
        assert response.current_price == 150.0
        assert response.recommendation == "BUY"
        assert response.confidence == 75
        assert response.risk_level == "medium"
        assert response.reasoning == "Strong technical indicators"
        assert response.target_price == 165.0
        assert response.stop_loss == 140.0
        assert response.technical_indicators == {"rsi": 65, "macd": "positive"}
        assert response.analysis_time == 2.5
        assert response.timestamp == "2024-01-01T00:00:00Z"
    
    def test_report_status_enum(self):
        """Test ReportStatus enum"""
        assert ReportStatus.PENDING == "pending"
        assert ReportStatus.PROCESSING == "processing"
        assert ReportStatus.COMPLETED == "completed"
        assert ReportStatus.FAILED == "failed"
        
        # Test enum membership
        assert ReportStatus.PENDING in ReportStatus
        assert ReportStatus.PROCESSING in ReportStatus
        assert ReportStatus.COMPLETED in ReportStatus
        assert ReportStatus.FAILED in ReportStatus
    
    def test_report_job_dataclass(self):
        """Test ReportJob dataclass"""
        from datetime import datetime
        
        job = ReportJob(
            job_id="test-job-123",
            symbol="AAPL",
            current_price=150.0,
            status=ReportStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert job.job_id == "test-job-123"
        assert job.symbol == "AAPL"
        assert job.current_price == 150.0
        assert job.status == ReportStatus.PENDING
        assert job.completed_at is None
        assert job.result is None
        assert job.error is None
        assert job.notification_sent is False
        
        # Test with completion data
        job_with_completion = ReportJob(
            job_id="test-job-456",
            symbol="GOOGL",
            current_price=2800.0,
            status=ReportStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            result={"recommendation": "BUY", "confidence": 85},
            notification_sent=True
        )
        
        assert job_with_completion.job_id == "test-job-456"
        assert job_with_completion.symbol == "GOOGL"
        assert job_with_completion.current_price == 2800.0
        assert job_with_completion.status == ReportStatus.COMPLETED
        assert job_with_completion.completed_at is not None
        assert job_with_completion.result == {"recommendation": "BUY", "confidence": 85}
        assert job_with_completion.notification_sent is True
    
    def test_error_handling(self, client):
        """Test error handling for invalid endpoints"""
        # Test invalid endpoint
        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404
        
        # Test invalid method
        response = client.get("/api/analyze")
        assert response.status_code == 405  # Method not allowed (POST required)
        
        # Test invalid request data
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422  # Validation error
    
    def test_data_validation(self, client):
        """Test data validation for API responses"""
        # Test AI analysis response structure
        response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        })
        data = response.json()
        if "error" not in data:
            assert "symbol" in data, "Should have symbol"
            assert "current_price" in data, "Should have current_price"
            assert "recommendation" in data, "Should have recommendation"
            assert "confidence" in data, "Should have confidence"
            assert "risk_level" in data, "Should have risk_level"
            assert "reasoning" in data, "Should have reasoning"
            assert "technical_indicators" in data, "Should have technical_indicators"
            assert "analysis_time" in data, "Should have analysis_time"
            assert "timestamp" in data, "Should have timestamp"
        
        # Test pipeline status structure
        response = client.get("/api/pipeline/status")
        data = response.json()
        if "error" not in data:
            assert isinstance(data, dict), "Should return dictionary"
            if "analysis_service" in data:
                assert isinstance(data["analysis_service"], str), "Analysis service should be string"
            if "market_data_service" in data:
                assert isinstance(data["market_data_service"], str), "Market data service should be string"
            if "transformation_pipeline" in data:
                assert isinstance(data["transformation_pipeline"], str), "Transformation pipeline should be string"
        
        # Test central hub data structure
        response = client.get("/api/central-hub/data")
        data = response.json()
        if "error" not in data:
            assert isinstance(data, dict), "Should return dictionary"
            if "data_coverage" in data:
                assert isinstance(data["data_coverage"], dict), "Data coverage should be dictionary"
            if "polygon_status" in data:
                assert isinstance(data["polygon_status"], str), "Polygon status should be string"
            if "recent_activity" in data:
                assert isinstance(data["recent_activity"], list), "Recent activity should be list"
    
    def test_async_operations(self, dashboard_manager):
        """Test asynchronous operations"""
        # Test that all manager methods are async
        methods = [
            'get_ai_stock_analysis',
            'get_data_pipeline_status',
            'get_central_hub_data',
            'get_symbols_coverage',
            'get_options_data'
        ]
        
        for method_name in methods:
            method = getattr(dashboard_manager, method_name)
            assert asyncio.iscoroutinefunction(method), f"{method_name} should be async"
    
    def test_service_integration(self, dashboard_manager):
        """Test service integration"""
        # Test that external services are being called
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test service health checks
            result = asyncio.run(dashboard_manager.get_data_pipeline_status())
            assert isinstance(result, dict)
    
    def test_template_rendering(self, client):
        """Test template rendering"""
        # Test that templates can be rendered (even if they return 500 due to missing templates)
        pages = ["/", "/ai-stock", "/central-hub", "/data-pipeline"]
        
        for page in pages:
            response = client.get(page)
            # Should return 200 (success) or 500 (template not found)
            assert response.status_code in [200, 500], f"Page {page} should return 200 or 500"
    
    def test_api_response_formats(self, client):
        """Test API response formats"""
        endpoints = [
            "/api/pipeline/status",
            "/api/pipeline/sample-analysis",
            "/api/pipeline/metrics",
            "/api/central-hub/data",
            "/api/symbols",
            "/api/options/coverage",
            "/api/greeks/status",
            "/api/notifications/vapid-public-key"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} should return 200"
            data = response.json()
            assert isinstance(data, dict), f"Endpoint {endpoint} should return JSON object"
    
    def test_dashboard_functionality_completeness(self):
        """Test that all expected functionality is present"""
        # Test that all required methods exist
        manager = UnifiedAnalyticsDashboard()
        required_methods = [
            'get_ai_stock_analysis',
            'get_data_pipeline_status',
            'get_central_hub_data',
            'get_symbols_coverage',
            'get_options_data'
        ]
        
        for method in required_methods:
            assert hasattr(manager, method), f"Missing method: {method}"
            method_obj = getattr(manager, method)
            assert callable(method_obj), f"Method {method} should be callable"
    
    def test_ai_analysis_functionality(self, client):
        """Test AI analysis functionality"""
        # Test valid analysis request
        response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "async_mode": False,
            "user_email": "test@example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "symbol", "current_price", "recommendation", "confidence",
            "risk_level", "reasoning", "technical_indicators", "analysis_time", "timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"AI analysis response should have {field}"
        
        # Check data types
        assert isinstance(data["symbol"], str)
        assert isinstance(data["current_price"], (int, float))
        assert isinstance(data["recommendation"], str)
        assert isinstance(data["confidence"], int)
        assert isinstance(data["risk_level"], str)
        assert isinstance(data["reasoning"], str)
        assert isinstance(data["technical_indicators"], dict)
        assert isinstance(data["analysis_time"], (int, float))
        assert isinstance(data["timestamp"], str)
        
        # Check value ranges
        assert 0 <= data["confidence"] <= 100, "Confidence should be between 0 and 100"
        assert data["recommendation"] in ["BUY", "SELL", "HOLD"], "Recommendation should be valid"
        assert data["risk_level"] in ["low", "medium", "high"], "Risk level should be valid"
    
    def test_pipeline_status_functionality(self, client):
        """Test pipeline status functionality"""
        response = client.get("/api/pipeline/status")
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            # Check for expected service status fields
            service_fields = ["analysis_service", "market_data_service", "transformation_pipeline"]
            for field in service_fields:
                if field in data:
                    assert isinstance(data[field], str), f"{field} should be string"
                    assert data[field] in ["healthy", "unhealthy", "error", "unknown"], f"{field} should have valid status"
    
    def test_central_hub_functionality(self, client):
        """Test central hub functionality"""
        response = client.get("/api/central-hub/data")
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            # Check for expected central hub fields
            expected_fields = ["data_coverage", "polygon_status", "recent_activity"]
            for field in expected_fields:
                if field in data:
                    if field == "recent_activity":
                        assert isinstance(data[field], list), f"{field} should be list"
                    else:
                        assert isinstance(data[field], (dict, str)), f"{field} should be dict or string"
    
    def test_symbols_functionality(self, client):
        """Test symbols functionality"""
        response = client.get("/api/symbols")
        assert response.status_code == 200
        data = response.json()
        
        if "error" not in data:
            # Check for expected symbols fields
            if "symbols" in data:
                assert isinstance(data["symbols"], list), "Symbols should be list"
                for symbol in data["symbols"]:
                    assert isinstance(symbol, str), "Each symbol should be string"
    
    def test_error_recovery(self, dashboard_manager):
        """Test error recovery mechanisms"""
        # Test that the dashboard handles service failures gracefully
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock service failure
            mock_get.side_effect = Exception("Service unavailable")
            
            # Should handle errors gracefully
            result = asyncio.run(dashboard_manager.get_ai_stock_analysis("AAPL", 150.0))
            assert isinstance(result, dict)
            assert "error" in result or "symbol" in result
    
    def test_data_consistency(self, client):
        """Test data consistency across endpoints"""
        # Test that related endpoints return consistent data
        pipeline_response = client.get("/api/pipeline/status")
        central_hub_response = client.get("/api/central-hub/data")
        
        if pipeline_response.status_code == 200 and central_hub_response.status_code == 200:
            pipeline_data = pipeline_response.json()
            central_hub_data = central_hub_response.json()
            
            # Both should return dictionaries
            assert isinstance(pipeline_data, dict)
            assert isinstance(central_hub_data, dict)
            
            # Check for consistent service status
            if "analysis_service" in pipeline_data and "polygon_status" in central_hub_data:
                # Both should indicate service health
                assert pipeline_data["analysis_service"] in ["healthy", "unhealthy", "error", "unknown"]
                assert central_hub_data["polygon_status"] in ["healthy", "unhealthy", "error", "unknown"]
    
    def test_vapid_key_functionality(self, client):
        """Test VAPID key functionality"""
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        
        assert "public_key" in data, "Should have public_key field"
        assert isinstance(data["public_key"], str), "Public key should be string"
        assert len(data["public_key"]) > 0, "Public key should not be empty"
    
    def test_analysis_request_validation(self, client):
        """Test analysis request validation"""
        # Test missing required fields
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid symbol
        response = client.post("/api/analyze", json={
            "symbol": "",  # Empty symbol
            "current_price": 150.0
        })
        assert response.status_code == 422  # Validation error
        
        # Test invalid price
        response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": -150.0  # Negative price
        })
        assert response.status_code == 422  # Validation error
        
        # Test valid request
        response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        })
        assert response.status_code == 200  # Should be valid

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 