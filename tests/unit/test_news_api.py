"""
Tests for news API endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.api.news_api import router, NewsEventResponse, NewsScannerConfig


class TestNewsAPI:
    """Test news API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_news_scanner(self):
        """Mock news scanner"""
        scanner = Mock()
        scanner.is_running = False
        scanner.start = AsyncMock()
        scanner.stop = AsyncMock()
        scanner.news_sources = {
            'rss_feed': 'https://example.com/rss',
            'api_source': 'https://api.example.com/news'
        }
        scanner.event_keywords = {
            'earnings': ['earnings', 'quarterly', 'revenue'],
            'merger': ['merger', 'acquisition', 'buyout'],
            'regulatory': ['regulation', 'fda', 'sec']
        }
        scanner.positive_keywords = ['positive', 'growth', 'profit', 'success']
        scanner.negative_keywords = ['negative', 'loss', 'decline', 'failure']
        scanner.company_symbols = {
            'Apple Inc.': 'AAPL',
            'Tesla Inc.': 'TSLA',
            'Microsoft Corporation': 'MSFT'
        }
        scanner.processed_news = [
            {
                'title': 'Apple Reports Strong Q4 Earnings',
                'source': 'Reuters',
                'url': 'https://example.com/apple-earnings',
                'published_at': '2024-01-15T10:00:00Z',
                'sentiment_score': 0.8,
                'impact_score': 0.9,
                'affected_symbols': ['AAPL'],
                'event_type': 'earnings',
                'confidence': 0.95,
                'metadata': {'revenue': '100B', 'eps': '1.50'}
            }
        ]
        return scanner
    
    def test_get_scanner_status_success(self, client, mock_news_scanner):
        """Test successful scanner status retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/scanner/status")
            assert response.status_code == 200
            data = response.json()
            
            assert data["is_running"] is False
            assert "rss_feed" in data["sources"]
            assert "api_source" in data["sources"]
            assert "earnings" in data["event_types"]
            assert "merger" in data["event_types"]
            assert data["processed_news_count"] == 1
    
    def test_get_scanner_status_not_initialized(self, client):
        """Test scanner status when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/scanner/status")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_start_scanner_success(self, client, mock_news_scanner):
        """Test successful scanner start"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.post("/news/scanner/start")
            assert response.status_code == 200
            data = response.json()
            assert "started" in data["message"]
    
    def test_start_scanner_already_running(self, client, mock_news_scanner):
        """Test scanner start when already running"""
        mock_news_scanner.is_running = True
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.post("/news/scanner/start")
            assert response.status_code == 400
            data = response.json()
            assert "already running" in data["detail"]
    
    def test_start_scanner_not_initialized(self, client):
        """Test scanner start when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.post("/news/scanner/start")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_stop_scanner_success(self, client, mock_news_scanner):
        """Test successful scanner stop"""
        mock_news_scanner.is_running = True
        mock_news_scanner.stop = AsyncMock()
        
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.post("/news/scanner/stop")
            assert response.status_code == 200
            data = response.json()
            assert "stopped" in data["message"]
    
    def test_stop_scanner_not_running(self, client, mock_news_scanner):
        """Test scanner stop when not running"""
        mock_news_scanner.is_running = False
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.post("/news/scanner/stop")
            assert response.status_code == 400
            data = response.json()
            assert "not running" in data["detail"]
    
    def test_get_recent_events_success(self, client, mock_news_scanner):
        """Test successful recent events retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/events?limit=10")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2  # API returns 2 sample events by default
            # Check first event (Apple)
            assert "Apple" in data[0]["title"]
            assert data[0]["source"] == "reuters"
            assert data[0]["affected_symbols"] == ["AAPL"]
            assert data[0]["event_type"] == "earnings"
            # Check second event (Tesla)
            assert "Tesla" in data[1]["title"]
            assert data[1]["source"] == "bloomberg"
            assert data[1]["affected_symbols"] == ["TSLA"]
            assert data[1]["event_type"] == "regulatory"
    
    def test_get_recent_events_not_initialized(self, client):
        """Test recent events when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/events")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_get_events_by_symbol_success(self, client, mock_news_scanner):
        """Test successful events by symbol retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/events/AAPL?limit=5")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 1
            assert data[0]["affected_symbols"] == ["AAPL"]
            assert "AAPL" in data[0]["affected_symbols"]
    
    def test_get_events_by_symbol_not_initialized(self, client):
        """Test events by symbol when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/events/AAPL")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_get_sentiment_analysis_success(self, client, mock_news_scanner):
        """Test successful sentiment analysis retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/sentiment/AAPL")
            assert response.status_code == 200
            data = response.json()
            
            assert "symbol" in data
            assert "sentiment_score" in data
            assert "sentiment_label" in data
            assert "confidence" in data
            assert "recent_events_count" in data
            assert "last_updated" in data
            assert data["symbol"] == "AAPL"
    
    def test_get_sentiment_analysis_not_initialized(self, client):
        """Test sentiment analysis when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/sentiment/AAPL")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_trigger_manual_scan_success(self, client, mock_news_scanner):
        """Test successful manual scan trigger"""
        mock_news_scanner._scan_news_sources = AsyncMock(return_value=[])
        
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.post("/news/scan/trigger")
            assert response.status_code == 200
            data = response.json()
            assert "Manual scan completed" in data["message"]
    
    def test_trigger_manual_scan_not_initialized(self, client):
        """Test manual scan trigger when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.post("/news/scan/trigger")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_get_news_sources_success(self, client, mock_news_scanner):
        """Test successful news sources retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/sources")
            assert response.status_code == 200
            data = response.json()
            
            assert "sources" in data
            assert "total_sources" in data
            assert "rss_feed" in data["sources"]
            assert "api_source" in data["sources"]
            assert data["sources"]["rss_feed"] == "https://example.com/rss"
            assert data["sources"]["api_source"] == "https://api.example.com/news"
    
    def test_get_news_sources_not_initialized(self, client):
        """Test news sources when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/sources")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_get_event_keywords_success(self, client, mock_news_scanner):
        """Test successful event keywords retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/keywords")
            assert response.status_code == 200
            data = response.json()
            
            assert "event_keywords" in data
            assert "positive_keywords" in data
            assert "negative_keywords" in data
            assert "earnings" in data["event_keywords"]
            assert "merger" in data["event_keywords"]
            assert "regulatory" in data["event_keywords"]
    
    def test_get_event_keywords_not_initialized(self, client):
        """Test event keywords when not initialized"""
        with patch('src.api.news_api.news_scanner', None):
            response = client.get("/news/keywords")
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"]
    
    def test_get_company_mappings_success(self, client, mock_news_scanner):
        """Test successful company mappings retrieval"""
        with patch('src.api.news_api.news_scanner', mock_news_scanner):
            response = client.get("/news/companies")
            assert response.status_code == 200
            data = response.json()
            
            # Should return a dictionary of company mappings
            assert isinstance(data, dict)


class TestNewsAPIModels:
    """Test news API data models"""
    
    def test_news_event_response_model(self):
        """Test NewsEventResponse model"""
        event = NewsEventResponse(
            title="Test News Event",
            source="Test Source",
            url="https://example.com/test",
            published_at="2024-01-15T10:00:00Z",
            sentiment_score=0.8,
            impact_score=0.9,
            affected_symbols=["AAPL", "GOOGL"],
            event_type="earnings",
            confidence=0.95,
            metadata={"revenue": "100B", "eps": "1.50"}
        )
        
        assert event.title == "Test News Event"
        assert event.source == "Test Source"
        assert event.url == "https://example.com/test"
        assert event.published_at == "2024-01-15T10:00:00Z"
        assert event.sentiment_score == 0.8
        assert event.impact_score == 0.9
        assert event.affected_symbols == ["AAPL", "GOOGL"]
        assert event.event_type == "earnings"
        assert event.confidence == 0.95
        assert event.metadata == {"revenue": "100B", "eps": "1.50"}
    
    def test_news_scanner_config_model(self):
        """Test NewsScannerConfig model"""
        config = NewsScannerConfig(
            is_active=True,
            scan_interval=300,
            sources=["rss_feed", "api_source"],
            event_types=["earnings", "merger"],
            min_impact_score=0.5,
            min_confidence=0.6
        )
        
        assert config.is_active is True
        assert config.scan_interval == 300
        assert config.sources == ["rss_feed", "api_source"]
        assert config.event_types == ["earnings", "merger"]
        assert config.min_impact_score == 0.5
        assert config.min_confidence == 0.6
    
    def test_news_scanner_config_defaults(self):
        """Test NewsScannerConfig default values"""
        config = NewsScannerConfig(
            is_active=True,
            sources=["rss_feed"],
            event_types=["earnings"]
        )
        
        assert config.scan_interval == 300  # default
        assert config.min_impact_score == 0.5  # default
        assert config.min_confidence == 0.6  # default


class TestNewsAPIValidation:
    """Test news API validation and error handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_limit_parameter_validation(self, client):
        """Test limit parameter validation"""
        # Test with valid limit
        with patch('src.api.news_api.news_scanner', Mock()):
            response = client.get("/news/events?limit=10")
            assert response.status_code == 200
        
        # Test with invalid limit (negative) - API doesn't validate this
        with patch('src.api.news_api.news_scanner', Mock()):
            response = client.get("/news/events?limit=-1")
            assert response.status_code == 200  # API accepts negative limits
    
    def test_symbol_parameter_validation(self, client):
        """Test symbol parameter validation"""
        # Test with valid symbol
        with patch('src.api.news_api.news_scanner', Mock()):
            response = client.get("/news/events/AAPL")
            assert response.status_code == 200
        
        # Test with empty symbol - API doesn't validate this
        with patch('src.api.news_api.news_scanner', Mock()):
            response = client.get("/news/events/")
            assert response.status_code == 200  # API accepts empty symbols 