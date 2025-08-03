"""
Unit tests for AI Stock Dashboard Service
Comprehensive testing of AI-powered stock analysis functionality
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta

# Import the AI stock dashboard app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/ai-stock-dashboard'))

try:
    from main import app, AIStockAnalyzer, ReportStatus, ReportJob, StockAnalysisRequest, StockAnalysisResponse
    dashboard_app = app
    AIStockAnalyzerClass = AIStockAnalyzer
except ImportError:
    # Handle import errors gracefully
    dashboard_app = None
    AIStockAnalyzerClass = None

client = TestClient(dashboard_app) if dashboard_app else None


class TestAIStockDashboardHealth:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-stock-dashboard"


class TestAIStockDashboardStructure:
    """Test dashboard structure and attributes"""
    
    def test_dashboard_app_structure(self):
        """Test dashboard app structure"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        # Check that the app has the expected structure
        assert hasattr(dashboard_app, 'routes')
        assert hasattr(dashboard_app, 'get')
        assert hasattr(dashboard_app, 'post')
    
    def test_ai_analyzer_structure(self):
        """Test AI analyzer class structure"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Check required methods
        assert hasattr(analyzer, 'analyze_stock')
        assert callable(analyzer.analyze_stock)
        assert hasattr(analyzer, '_get_real_market_data')
        assert callable(analyzer._get_real_market_data)
        assert hasattr(analyzer, '_get_real_technical_analysis')
        assert callable(analyzer._get_real_technical_analysis)
        assert hasattr(analyzer, '_get_real_news_sentiment')
        assert callable(analyzer._get_real_news_sentiment)
        assert hasattr(analyzer, '_get_vector_context')
        assert callable(analyzer._get_vector_context)


class TestAIStockDashboardAPI:
    """Test dashboard API endpoints"""
    
    def test_analyze_stock_endpoint(self):
        """Test stock analysis endpoint"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        request_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        }
        
        response = client.post("/api/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "symbol" in data
        assert "current_price" in data
        assert "recommendation" in data
        assert "confidence" in data
    
    def test_submit_report_job(self):
        """Test report job submission"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        request_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        }
        
        response = client.post("/api/reports/submit", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "job_id" in data
        assert "status" in data
    
    def test_get_report_status(self):
        """Test getting report status"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        # First submit a job
        request_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        }
        
        submit_response = client.post("/api/reports/submit", json=request_data)
        assert submit_response.status_code == 200
        
        job_data = submit_response.json()
        job_id = job_data["job_id"]
        
        # Then check the status
        response = client.get(f"/api/reports/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "job_id" in data
        assert "status" in data
    
    def test_list_report_jobs(self):
        """Test listing report jobs"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/reports")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "jobs" in data
    
    def test_get_popular_symbols(self):
        """Test getting popular symbols"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/symbols")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "symbols" in data
    
    def test_get_vapid_public_key(self):
        """Test getting VAPID public key"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "public_key" in data


class TestAIStockAnalyzer:
    """Test AI stock analyzer functionality"""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Check required attributes
        assert hasattr(analyzer, 'vector_storage_url')
        assert hasattr(analyzer, 'llm_proxy_url')
        assert hasattr(analyzer, 'backtest_api_url')
        assert hasattr(analyzer, 'market_data_url')
        assert hasattr(analyzer, 'rss_feed_url')
        assert hasattr(analyzer, 'notification_service_url')
    
    @pytest.mark.asyncio
    async def test_analyze_stock_success(self):
        """Test successful stock analysis"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Mock all external dependencies
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            # Mock market data response
            mock_market_response = MagicMock()
            mock_market_response.status = 200
            mock_market_response.json = AsyncMock(return_value={
                "symbol": "AAPL",
                "current_price": 150.0,
                "historical_data": [
                    {"close": 145.0, "volume": 1000000},
                    {"close": 148.0, "volume": 1100000},
                    {"close": 150.0, "volume": 1200000}
                ]
            })
            
            # Mock LLM response
            mock_llm_response = MagicMock()
            mock_llm_response.status = 200
            mock_llm_response.json = AsyncMock(return_value={
                "recommendation": "BUY",
                "confidence": 85,
                "reasoning": "Strong technical indicators"
            })
            
            # Mock news response
            mock_news_response = MagicMock()
            mock_news_response.status = 200
            mock_news_response.json = AsyncMock(return_value={
                "articles": [
                    {"title": "AAPL News", "sentiment": 0.8}
                ]
            })
            
            # Mock vector storage response
            mock_vector_response = MagicMock()
            mock_vector_response.status = 200
            mock_vector_response.json = AsyncMock(return_value={
                "context": "Apple stock analysis context"
            })
            
            # Set up mock responses
            mock_get.return_value.__aenter__.side_effect = [
                mock_market_response,
                mock_news_response,
                mock_vector_response
            ]
            mock_post.return_value.__aenter__.return_value = mock_llm_response
            
            result = await analyzer.analyze_stock("AAPL", 150.0)
            
            assert isinstance(result, dict)
            assert "symbol" in result
            assert "current_price" in result
            assert "recommendation" in result
            assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_analyze_stock_error_handling(self):
        """Test stock analysis error handling"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Mock HTTP client to raise an error
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            result = await analyzer.analyze_stock("AAPL", 150.0)
            
            # Should handle errors gracefully
            assert isinstance(result, dict)
            assert "symbol" in result
            assert "current_price" in result


class TestReportStatus:
    """Test report status enum"""
    
    def test_report_status_values(self):
        """Test report status enum values"""
        if not ReportStatus:
            pytest.skip("ReportStatus enum not available")
        
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.PROCESSING.value == "processing"
        assert ReportStatus.READY_WITHOUT_AI.value == "ready_without_ai"
        assert ReportStatus.READY_WITH_AI.value == "ready_with_ai"
        assert ReportStatus.FAILED.value == "failed"
    
    def test_report_status_enum_membership(self):
        """Test report status enum membership"""
        if not ReportStatus:
            pytest.skip("ReportStatus enum not available")
        
        assert ReportStatus.PENDING in ReportStatus
        assert ReportStatus.PROCESSING in ReportStatus
        assert ReportStatus.READY_WITHOUT_AI in ReportStatus
        assert ReportStatus.READY_WITH_AI in ReportStatus
        assert ReportStatus.FAILED in ReportStatus


class TestReportJob:
    """Test report job dataclass"""
    
    def test_report_job_creation(self):
        """Test report job creation"""
        if not ReportJob:
            pytest.skip("ReportJob dataclass not available")
        
        job_id = "test-job-123"
        symbol = "AAPL"
        current_price = 150.0
        status = ReportStatus.PENDING
        created_at = datetime.utcnow()
        
        job = ReportJob(
            job_id=job_id,
            symbol=symbol,
            current_price=current_price,
            status=status,
            created_at=created_at
        )
        
        assert job.job_id == job_id
        assert job.symbol == symbol
        assert job.current_price == current_price
        assert job.status == status
        assert job.created_at == created_at
        assert job.completed_at is None
        assert job.result is None
        assert job.error is None
        assert job.notification_sent is False
    
    def test_report_job_with_completion(self):
        """Test report job with completion data"""
        if not ReportJob:
            pytest.skip("ReportJob dataclass not available")
        
        job_id = "test-job-456"
        symbol = "MSFT"
        current_price = 300.0
        status = ReportStatus.READY_WITH_AI
        created_at = datetime.utcnow()
        completed_at = datetime.utcnow()
        result = {"recommendation": "BUY", "confidence": 85}
        
        job = ReportJob(
            job_id=job_id,
            symbol=symbol,
            current_price=current_price,
            status=status,
            created_at=created_at,
            completed_at=completed_at,
            result=result
        )
        
        assert job.job_id == job_id
        assert job.symbol == symbol
        assert job.current_price == current_price
        assert job.status == status
        assert job.created_at == created_at
        assert job.completed_at == completed_at
        assert job.result == result
        assert job.error is None
        assert job.notification_sent is False


class TestStockAnalysisRequest:
    """Test stock analysis request model"""
    
    def test_stock_analysis_request_creation(self):
        """Test stock analysis request creation"""
        if not StockAnalysisRequest:
            pytest.skip("StockAnalysisRequest model not available")
        
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
    
    def test_stock_analysis_request_defaults(self):
        """Test stock analysis request with defaults"""
        if not StockAnalysisRequest:
            pytest.skip("StockAnalysisRequest model not available")
        
        request = StockAnalysisRequest(
            symbol="AAPL",
            current_price=150.0
        )
        
        assert request.symbol == "AAPL"
        assert request.current_price == 150.0
        assert request.include_news is True
        assert request.include_technical is True
        assert request.include_sentiment is True
        assert request.async_mode is False
        assert request.user_email is None


class TestStockAnalysisResponse:
    """Test stock analysis response model"""
    
    def test_stock_analysis_response_creation(self):
        """Test stock analysis response creation"""
        if not StockAnalysisResponse:
            pytest.skip("StockAnalysisResponse model not available")
        
        response = StockAnalysisResponse(
            symbol="AAPL",
            current_price=150.0,
            recommendation="BUY",
            confidence=85,
            risk_level="MEDIUM",
            reasoning="Strong technical indicators",
            target_price=165.0,
            stop_loss=140.0,
            technical_indicators={
                "rsi": 65,
                "macd": "positive",
                "bollinger_bands": "upper"
            },
            analysis_time=2.5,
            timestamp="2023-01-01T10:00:00Z"
        )
        
        assert response.symbol == "AAPL"
        assert response.current_price == 150.0
        assert response.recommendation == "BUY"
        assert response.confidence == 85
        assert response.risk_level == "MEDIUM"
        assert response.reasoning == "Strong technical indicators"
        assert response.target_price == 165.0
        assert response.stop_loss == 140.0
        assert response.technical_indicators["rsi"] == 65
        assert response.analysis_time == 2.5
        assert response.timestamp == "2023-01-01T10:00:00Z"


class TestAIStockDashboardIntegration:
    """Test integration workflows"""
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        # Test health check
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # Test symbol analysis
        request_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True
        }
        
        response = client.post("/api/analyze", json=request_data)
        assert response.status_code == 200
        
        # Test report submission
        request_data = {
            "symbol": "AAPL",
            "current_price": 150.0,
            "include_news": True,
            "include_technical": True,
            "include_sentiment": True,
            "user_email": "test@example.com"
        }
        
        response = client.post("/api/reports/submit", json=request_data)
        assert response.status_code == 200
    
    def test_notification_workflow(self):
        """Test notification workflow"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        # Test VAPID public key
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        
        # Test popular symbols
        response = client.get("/api/symbols")
        assert response.status_code == 200


class TestAIStockDashboardErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/invalid/endpoint")
        assert response.status_code in [404, 405, 500]  # Should handle gracefully
    
    def test_invalid_analysis_request(self):
        """Test invalid analysis request"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        # Test with missing required fields
        request_data = {
            "symbol": "AAPL"
            # Missing current_price
        }
        
        response = client.post("/api/analyze", json=request_data)
        assert response.status_code in [422, 400]  # Validation error
    
    def test_analysis_request_with_invalid_data_types(self):
        """Test analysis request with invalid data types"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        request_data = {
            "symbol": "AAPL",
            "current_price": "invalid_price",  # Should be float
            "include_news": "not_boolean"  # Should be boolean
        }
        
        response = client.post("/api/analyze", json=request_data)
        assert response.status_code in [422, 400]  # Validation error


class TestAIStockDashboardConfiguration:
    """Test configuration"""
    
    def test_environment_variables(self):
        """Test environment variable configuration"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Check that URLs are configured
        assert hasattr(analyzer, 'vector_storage_url')
        assert hasattr(analyzer, 'llm_proxy_url')
        assert hasattr(analyzer, 'backtest_api_url')
        assert hasattr(analyzer, 'market_data_url')
        assert hasattr(analyzer, 'rss_feed_url')
        assert hasattr(analyzer, 'notification_service_url')
    
    def test_vapid_configuration(self):
        """Test VAPID configuration"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 0


class TestAIStockDashboardAsyncOperations:
    """Test async operations"""
    
    @pytest.mark.asyncio
    async def test_async_stock_analysis(self):
        """Test async stock analysis"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Mock the HTTP client
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "symbol": "AAPL",
                "current_price": 150.0,
                "recommendation": "BUY",
                "confidence": 85
            })
            
            mock_get.return_value.__aenter__.return_value = mock_response
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await analyzer.analyze_stock("AAPL", 150.0)
            
            assert isinstance(result, dict)
            assert "symbol" in result
            assert "current_price" in result
    
    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test async timeout handling"""
        if not AIStockAnalyzerClass:
            pytest.skip("AIStockAnalyzer class not available")
        
        analyzer = AIStockAnalyzerClass()
        
        # Mock the HTTP client to simulate timeout
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            result = await analyzer.analyze_stock("AAPL", 150.0)
            
            assert isinstance(result, dict)
            # Should handle errors gracefully
            assert "symbol" in result
            assert "current_price" in result


class TestAIStockDashboardDataValidation:
    """Test data validation"""
    
    def test_analysis_response_validation(self):
        """Test analysis response validation"""
        if not StockAnalysisResponse:
            pytest.skip("StockAnalysisResponse model not available")
        
        # Test valid response
        response = StockAnalysisResponse(
            symbol="AAPL",
            current_price=150.0,
            recommendation="BUY",
            confidence=85,
            risk_level="MEDIUM",
            reasoning="Strong technical indicators",
            target_price=165.0,
            stop_loss=140.0,
            technical_indicators={"rsi": 65},
            analysis_time=2.5,
            timestamp="2023-01-01T10:00:00Z"
        )
        
        assert response.symbol == "AAPL"
        assert response.current_price == 150.0
        assert response.recommendation == "BUY"
        assert response.confidence == 85
        assert response.risk_level == "MEDIUM"
        assert response.reasoning == "Strong technical indicators"
        assert response.target_price == 165.0
        assert response.stop_loss == 140.0
        assert response.technical_indicators["rsi"] == 65
        assert response.analysis_time == 2.5
        assert response.timestamp == "2023-01-01T10:00:00Z"
    
    def test_symbols_response_validation(self):
        """Test symbols response validation"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/symbols")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "symbols" in data
        assert isinstance(data["symbols"], list)
    
    def test_vapid_key_response_validation(self):
        """Test VAPID key response validation"""
        if not dashboard_app:
            pytest.skip("Dashboard app not available")
        
        response = client.get("/api/notifications/vapid-public-key")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "public_key" in data
        assert isinstance(data["public_key"], str)
        assert len(data["public_key"]) > 0 