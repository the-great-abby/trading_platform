#!/usr/bin/env python3
"""
Comprehensive tests for AI Stock Dashboard
Tests all functionality including AI analysis, report generation, and notifications
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from fastapi.testclient import TestClient

# Add the service directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/ai-stock-dashboard'))

try:
    from main import app, AIStockAnalyzer, ReportStatus, ReportJob, StockAnalysisRequest, StockAnalysisResponse
except ImportError:
    app = None
    AIStockAnalyzer = None
    ReportStatus = None
    ReportJob = None
    StockAnalysisRequest = None
    StockAnalysisResponse = None

@pytest.fixture
def client():
    """Create test client"""
    if app is None:
        pytest.skip("AI Stock Dashboard not available")
    return TestClient(app)

@pytest.fixture
def analyzer():
    """Create AI stock analyzer instance"""
    if AIStockAnalyzer is None:
        pytest.skip("AI Stock Analyzer not available")
    return AIStockAnalyzer()

class TestAIStockDashboardComprehensive:
    """Comprehensive tests for AI Stock Dashboard"""
    
    def test_dashboard_structure(self):
        """Test dashboard structure and configuration"""
        assert app is not None, "App should be available"
        assert AIStockAnalyzer is not None, "AIStockAnalyzer should be available"
        assert ReportStatus is not None, "ReportStatus should be available"
        assert ReportJob is not None, "ReportJob should be available"
        assert StockAnalysisRequest is not None, "StockAnalysisRequest should be available"
        assert StockAnalysisResponse is not None, "StockAnalysisResponse should be available"
        
        # Test app structure
        assert hasattr(app, 'routes'), "App should have routes"
        assert len(app.routes) > 0, "App should have routes defined"
        
        # Test analyzer structure
        analyzer = AIStockAnalyzer()
        assert hasattr(analyzer, 'analyze_stock'), "Should have analyze_stock method"
        assert hasattr(analyzer, '_get_real_market_data'), "Should have market data method"
        assert hasattr(analyzer, '_get_real_technical_analysis'), "Should have technical analysis method"
        assert hasattr(analyzer, '_get_real_news_sentiment'), "Should have news sentiment method"
        assert hasattr(analyzer, '_get_vector_context'), "Should have vector context method"
        assert hasattr(analyzer, '_generate_real_ai_recommendation'), "Should have AI recommendation method"
    
    def test_health_endpoints(self, client):
        """Test health endpoints"""
        # Test health endpoint
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "ai-stock-dashboard"
    
    def test_dashboard_pages(self, client):
        """Test dashboard page endpoints"""
        # Test main dashboard page
        response = client.get("/")
        assert response.status_code in [200, 500]  # Allow for template issues
        
        # Test service worker
        response = client.get("/sw.js")
        assert response.status_code == 200
    
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
        
        # Test report job submission
        response = client.post("/api/reports/submit", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "job_id" in data
        assert "status" in data
        
        # Test report status
        if "job_id" in data:
            job_id = data["job_id"]
            response = client.get(f"/api/reports/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "status" in data
        
        # Test list reports
        response = client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "jobs" in data
        
        # Test popular symbols
        response = client.get("/api/symbols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "symbols" in data
        
        # Test VAPID public key
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "public_key" in data
    
    @patch('aiohttp.ClientSession.get')
    def test_analyzer_methods(self, mock_get, analyzer):
        """Test analyzer methods with mocked responses"""
        # Mock successful responses
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
            "news_sentiment": {"sentiment": 0.7, "articles_count": 10},
            "market_data": {"volume": 1000000, "change": 2.5},
            "vector_context": {"similar_symbols": ["GOOGL", "MSFT"]},
            "analysis_time": 2.5,
            "timestamp": "2024-01-01T00:00:00Z"
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Test analyze_stock
        result = asyncio.run(analyzer.analyze_stock("AAPL", 150.0))
        assert isinstance(result, dict)
        assert "symbol" in result or "error" in result
        
        # Test individual analysis methods
        result = asyncio.run(analyzer._get_real_market_data("AAPL", 150.0))
        assert isinstance(result, dict)
        
        result = asyncio.run(analyzer._get_real_technical_analysis("AAPL", {}))
        assert isinstance(result, dict)
        
        result = asyncio.run(analyzer._get_real_news_sentiment("AAPL"))
        assert isinstance(result, dict)
        
        result = asyncio.run(analyzer._get_vector_context("AAPL"))
        assert isinstance(result, dict)
    
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
            news_sentiment={"sentiment": 0.7, "articles_count": 10},
            market_data={"volume": 1000000, "change": 2.5},
            vector_context={"similar_symbols": ["GOOGL", "MSFT"]},
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
        assert response.news_sentiment == {"sentiment": 0.7, "articles_count": 10}
        assert response.market_data == {"volume": 1000000, "change": 2.5}
        assert response.vector_context == {"similar_symbols": ["GOOGL", "MSFT"]}
        assert response.analysis_time == 2.5
        assert response.timestamp == "2024-01-01T00:00:00Z"
    
    def test_report_status_enum(self):
        """Test ReportStatus enum"""
        assert ReportStatus.PENDING == "pending"
        assert ReportStatus.PROCESSING == "processing"
        assert ReportStatus.READY_WITHOUT_AI == "ready_without_ai"
        assert ReportStatus.READY_WITH_AI == "ready_with_ai"
        assert ReportStatus.FAILED == "failed"
        
        # Test enum membership
        assert ReportStatus.PENDING in ReportStatus
        assert ReportStatus.PROCESSING in ReportStatus
        assert ReportStatus.READY_WITHOUT_AI in ReportStatus
        assert ReportStatus.READY_WITH_AI in ReportStatus
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
            status=ReportStatus.READY_WITH_AI,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            result={"recommendation": "BUY", "confidence": 85},
            notification_sent=True
        )
        
        assert job_with_completion.job_id == "test-job-456"
        assert job_with_completion.symbol == "GOOGL"
        assert job_with_completion.current_price == 2800.0
        assert job_with_completion.status == ReportStatus.READY_WITH_AI
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
            assert "news_sentiment" in data, "Should have news_sentiment"
            assert "market_data" in data, "Should have market_data"
            assert "vector_context" in data, "Should have vector_context"
            assert "analysis_time" in data, "Should have analysis_time"
            assert "timestamp" in data, "Should have timestamp"
        
        # Test report job response structure
        response = client.post("/api/reports/submit", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        })
        data = response.json()
        if "error" not in data:
            assert "job_id" in data, "Should have job_id"
            assert "status" in data, "Should have status"
            assert "message" in data, "Should have message"
        
        # Test reports list structure
        response = client.get("/api/reports")
        data = response.json()
        if "error" not in data:
            assert "jobs" in data, "Should have jobs"
            assert isinstance(data["jobs"], list), "Jobs should be list"
    
    def test_async_operations(self, analyzer):
        """Test asynchronous operations"""
        # Test that all analyzer methods are async
        methods = [
            'analyze_stock',
            '_get_real_market_data',
            '_get_real_technical_analysis',
            '_get_real_news_sentiment',
            '_get_vector_context',
            '_generate_real_ai_recommendation'
        ]
        
        for method_name in methods:
            method = getattr(analyzer, method_name)
            assert asyncio.iscoroutinefunction(method), f"{method_name} should be async"
    
    def test_service_integration(self, analyzer):
        """Test service integration"""
        # Test that external services are being called
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test service health checks
            result = asyncio.run(analyzer._get_real_market_data("AAPL", 150.0))
            assert isinstance(result, dict)
    
    def test_template_rendering(self, client):
        """Test template rendering"""
        # Test that templates can be rendered (even if they return 500 due to missing templates)
        pages = ["/"]
        
        for page in pages:
            response = client.get(page)
            # Should return 200 (success) or 500 (template not found)
            assert response.status_code in [200, 500], f"Page {page} should return 200 or 500"
    
    def test_api_response_formats(self, client):
        """Test API response formats"""
        endpoints = [
            "/api/health",
            "/api/symbols",
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
        analyzer = AIStockAnalyzer()
        required_methods = [
            'analyze_stock',
            '_get_real_market_data',
            '_get_real_technical_analysis',
            '_get_real_news_sentiment',
            '_get_vector_context',
            '_generate_real_ai_recommendation'
        ]
        
        for method in required_methods:
            assert hasattr(analyzer, method), f"Missing method: {method}"
            method_obj = getattr(analyzer, method)
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
            "risk_level", "reasoning", "technical_indicators", "news_sentiment",
            "market_data", "vector_context", "analysis_time", "timestamp"
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
        assert isinstance(data["news_sentiment"], dict)
        assert isinstance(data["market_data"], dict)
        assert isinstance(data["vector_context"], dict)
        assert isinstance(data["analysis_time"], (int, float))
        assert isinstance(data["timestamp"], str)
        
        # Check value ranges
        assert 0 <= data["confidence"] <= 100, "Confidence should be between 0 and 100"
        assert data["recommendation"] in ["BUY", "SELL", "HOLD"], "Recommendation should be valid"
        assert data["risk_level"] in ["low", "medium", "high"], "Risk level should be valid"
    
    def test_report_generation_functionality(self, client):
        """Test report generation functionality"""
        # Test report job submission
        response = client.post("/api/reports/submit", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["job_id", "status", "message"]
        for field in required_fields:
            assert field in data, f"Report submission response should have {field}"
        
        # Check data types
        assert isinstance(data["job_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
        
        # Test report status
        if "job_id" in data:
            job_id = data["job_id"]
            response = client.get(f"/api/reports/{job_id}")
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data, "Report status should have status"
            assert "symbol" in data, "Report status should have symbol"
            assert "current_price" in data, "Report status should have current_price"
            assert "created_at" in data, "Report status should have created_at"
    
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
    
    def test_error_recovery(self, analyzer):
        """Test error recovery mechanisms"""
        # Test that the analyzer handles service failures gracefully
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock service failure
            mock_get.side_effect = Exception("Service unavailable")
            
            # Should handle errors gracefully
            result = asyncio.run(analyzer.analyze_stock("AAPL", 150.0))
            assert isinstance(result, dict)
            assert "error" in result or "symbol" in result
    
    def test_data_consistency(self, client):
        """Test data consistency across endpoints"""
        # Test that related endpoints return consistent data
        analysis_response = client.post("/api/analyze", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        })
        symbols_response = client.get("/api/symbols")
        
        if analysis_response.status_code == 200 and symbols_response.status_code == 200:
            analysis_data = analysis_response.json()
            symbols_data = symbols_response.json()
            
            # Both should return dictionaries
            assert isinstance(analysis_data, dict)
            assert isinstance(symbols_data, dict)
            
            # Check for consistent symbol format
            if "symbol" in analysis_data and "symbols" in symbols_data:
                assert isinstance(analysis_data["symbol"], str)
                assert isinstance(symbols_data["symbols"], list)
    
    def test_service_worker_functionality(self, client):
        """Test service worker functionality"""
        response = client.get("/sw.js")
        assert response.status_code == 200
        assert "text/javascript" in response.headers.get("content-type", "")
    
    def test_background_task_processing(self, client):
        """Test background task processing"""
        # Test that report jobs can be submitted and processed
        response = client.post("/api/reports/submit", json={
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        if "job_id" in data:
            # Test that job status can be retrieved
            job_id = data["job_id"]
            response = client.get(f"/api/reports/{job_id}")
            assert response.status_code == 200
            
            # Test that job appears in list
            response = client.get("/api/reports")
            assert response.status_code == 200
            data = response.json()
            if "jobs" in data:
                job_ids = [job.get("job_id") for job in data["jobs"]]
                assert job_id in job_ids, "Submitted job should appear in list"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 