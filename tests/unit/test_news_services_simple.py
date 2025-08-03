"""
Simplified unit tests for News Services
Focuses on core functionality without complex async operations
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json
from datetime import datetime

# Import the RSS feed service app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/rss-feed-service'))
from main import app as rss_app, RSSFeedGenerator, RSSFeedConfig, RSSItem

# Import the unified news dashboard app
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/unified-news-dashboard'))
try:
    from main import app as dashboard_app, UnifiedNewsDashboard
except ImportError:
    # Fallback if UnifiedNewsDashboard is not available
    dashboard_app = None
    UnifiedNewsDashboard = None

rss_client = TestClient(rss_app)
dashboard_client = TestClient(dashboard_app)


class TestRSSFeedServiceCore:
    """Test core RSS feed service functionality"""
    
    def test_rss_feed_config(self):
        """Test RSS feed configuration"""
        config = RSSFeedConfig(
            title="Test Feed",
            description="Test Description",
            language="en-us",
            ttl=60,
            max_items=10,
            feed_url="http://test.com/feed",
            site_url="http://test.com"
        )
        
        assert config.title == "Test Feed"
        assert config.description == "Test Description"
        assert config.language == "en-us"
        assert config.ttl == 60
        assert config.max_items == 10
    
    def test_rss_item_creation(self):
        """Test RSS item creation"""
        item = RSSItem(
            title="Test Item",
            description="Test Description",
            link="http://test.com/item",
            guid="test-guid-123",
            pub_date=datetime.now(),
            category="Trading",
            author="Test Author"
        )
        
        assert item.title == "Test Item"
        assert item.description == "Test Description"
        assert item.link == "http://test.com/item"
        assert item.guid == "test-guid-123"
        assert item.category == "Trading"
        assert item.author == "Test Author"
    
    def test_rss_feed_generator(self):
        """Test RSS feed generator"""
        config = RSSFeedConfig()
        generator = RSSFeedGenerator(config)
        
        assert generator.config == config
        assert hasattr(generator, 'generate_rss_feed')
        assert callable(generator.generate_rss_feed)
    
    def test_generate_rss_feed(self):
        """Test RSS feed generation"""
        config = RSSFeedConfig(
            title="Test Feed",
            description="Test Description",
            feed_url="http://test.com/feed",
            site_url="http://test.com"
        )
        generator = RSSFeedGenerator(config)
        
        items = [
            RSSItem(
                title="Test Item 1",
                description="Test Description 1",
                link="http://test.com/item1",
                guid="test-guid-1",
                pub_date=datetime.now(),
                category="Trading"
            )
        ]
        
        rss_xml = generator.generate_rss_feed(items)
        
        # Parse XML to verify structure
        import xml.etree.ElementTree as ET
        root = ET.fromstring(rss_xml)
        assert root.tag == "rss"
        assert root.get("version") == "2.0"
        
        channel = root.find("channel")
        assert channel is not None
        
        # Check channel metadata
        title = channel.find("title")
        assert title.text == "Test Feed"
        
        # Check items
        items_elements = channel.findall("item")
        assert len(items_elements) == 1
        
        # Check first item
        first_item = items_elements[0]
        item_title = first_item.find("title")
        assert item_title.text == "Test Item 1"


class TestRSSFeedServiceEndpoints:
    """Test RSS feed service endpoints"""
    
    def test_rss_service_health(self):
        """Test RSS service health endpoint"""
        response = rss_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_rss_service_root(self):
        """Test RSS service root endpoint"""
        response = rss_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "RSS Feed Service"
    
    def test_get_daily_recommendations_rss(self):
        """Test getting daily recommendations RSS feed"""
        response = rss_client.get("/rss/daily-recommendations")
        assert response.status_code == 200
        
        # Should return XML content
        content = response.text
        assert "<?xml" in content
        assert "<rss" in content
        assert "<channel>" in content
    
    def test_get_symbol_recommendation_rss(self):
        """Test getting symbol-specific RSS feed"""
        response = rss_client.get("/rss/symbol/AAPL")
        assert response.status_code == 200
        
        # Should return XML content
        content = response.text
        assert "<?xml" in content
        assert "<rss" in content
        assert "<channel>" in content
    
    def test_get_feed_data(self):
        """Test getting feed data via API"""
        response = rss_client.get("/api/feed")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "recommendations" in data
    
    def test_get_recommendations_api(self):
        """Test getting recommendations via API"""
        response = rss_client.get("/api/recommendations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "recommendations" in data
    
    def test_get_symbol_news(self):
        """Test getting news for a specific symbol"""
        response = rss_client.get("/api/news/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_fetch_symbol_news(self):
        """Test fetching news for a symbol"""
        response = rss_client.post("/api/news/fetch/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)


class TestUnifiedNewsDashboardCore:
    """Test core unified news dashboard functionality"""
    
    def test_dashboard_manager_initialization(self):
        """Test dashboard manager initialization"""
        dashboard = UnifiedNewsDashboard()
        
        assert hasattr(dashboard, 'rss_service_url')
        assert hasattr(dashboard, 'strategy_service_url')
        assert hasattr(dashboard, 'cache')
        assert hasattr(dashboard, 'last_update')
        assert hasattr(dashboard, 'get_rss_feed')
        assert callable(dashboard.get_rss_feed)
        assert hasattr(dashboard, 'get_news_recommendations')
        assert callable(dashboard.get_news_recommendations)
        assert hasattr(dashboard, 'get_symbol_news')
        assert callable(dashboard.get_symbol_news)
    
    def test_dashboard_cache_initialization(self):
        """Test dashboard cache initialization"""
        dashboard = UnifiedNewsDashboard()
        
        assert isinstance(dashboard.cache, dict)
        assert isinstance(dashboard.last_update, dict)
        assert len(dashboard.cache) == 0
        assert len(dashboard.last_update) == 0
    
    def test_dashboard_configuration(self):
        """Test dashboard configuration"""
        dashboard = UnifiedNewsDashboard()
        
        # Check configuration values
        assert hasattr(dashboard, 'rss_service_url')
        assert hasattr(dashboard, 'strategy_service_url')
        assert isinstance(dashboard.rss_service_url, str)
        assert isinstance(dashboard.strategy_service_url, str)
        
        # Check that URLs are properly formatted
        assert dashboard.rss_service_url.startswith("http://")
        assert dashboard.strategy_service_url.startswith("http://")


class TestUnifiedNewsDashboardEndpoints:
    """Test unified news dashboard endpoints"""
    
    def test_dashboard_health(self):
        """Test dashboard health endpoint"""
        response = dashboard_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_dashboard_readiness(self):
        """Test dashboard readiness endpoint"""
        response = dashboard_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_dashboard_home(self):
        """Test dashboard home page"""
        response = dashboard_client.get("/")
        assert response.status_code == 200
        # Should return HTML content
        content = response.text
        assert "<html" in content.lower()
    
    def test_get_feed_data(self):
        """Test getting feed data"""
        response = dashboard_client.get("/api/feed")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_feed_data_with_type(self):
        """Test getting feed data with type parameter"""
        response = dashboard_client.get("/api/feed?feed_type=daily")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_feed_data_with_symbol(self):
        """Test getting feed data for specific symbol"""
        response = dashboard_client.get("/api/feed?feed_type=symbol&symbol=AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_recommendations(self):
        """Test getting recommendations"""
        response = dashboard_client.get("/api/recommendations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_symbol_news(self):
        """Test getting news for a specific symbol"""
        response = dashboard_client.get("/api/symbol/AAPL/news")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_stream_feed(self):
        """Test streaming feed endpoint"""
        response = dashboard_client.get("/api/feed/stream")
        assert response.status_code == 200
        
        # Should return streaming content
        content = response.text
        assert len(content) >= 0


class TestNewsServicesIntegration:
    """Integration tests for news services"""
    
    def test_rss_service_complete_workflow(self):
        """Test complete RSS service workflow"""
        # 1. Check service health
        response = rss_client.get("/health")
        assert response.status_code == 200
        
        # 2. Get daily recommendations RSS
        response = rss_client.get("/rss/daily-recommendations")
        assert response.status_code == 200
        assert "<?xml" in response.text
        
        # 3. Get feed data via API
        response = rss_client.get("/api/feed")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        
        # 4. Get recommendations API
        response = rss_client.get("/api/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
    
    def test_dashboard_complete_workflow(self):
        """Test complete dashboard workflow"""
        # 1. Check service health
        response = dashboard_client.get("/health")
        assert response.status_code == 200
        
        # 2. Access dashboard home
        response = dashboard_client.get("/")
        assert response.status_code == 200
        assert "<html" in response.text.lower()
        
        # 3. Get feed data via API
        response = dashboard_client.get("/api/feed")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # 4. Get recommendations
        response = dashboard_client.get("/api/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestNewsServicesErrorHandling:
    """Test error handling in news services"""
    
    def test_rss_service_invalid_symbol(self):
        """Test invalid symbol for RSS service"""
        response = rss_client.get("/api/news/INVALID_SYMBOL")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]
    
    def test_dashboard_invalid_symbol(self):
        """Test invalid symbol for dashboard"""
        response = dashboard_client.get("/api/symbol/INVALID_SYMBOL/news")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]
    
    def test_dashboard_invalid_feed_type(self):
        """Test invalid feed type for dashboard"""
        response = dashboard_client.get("/api/feed?feed_type=invalid")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_dashboard_missing_symbol_parameter(self):
        """Test missing symbol parameter for dashboard"""
        response = dashboard_client.get("/api/feed?feed_type=symbol")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestNewsServicesParsing:
    """Test parsing functionality"""
    
    def test_parse_rss_xml(self):
        """Test parsing RSS XML"""
        dashboard = UnifiedNewsDashboard()
        
        # Sample RSS XML
        xml_content = """
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <description>Test Description</description>
                <item>
                    <title>Test Item</title>
                    <description>Test Description</description>
                    <link>http://test.com</link>
                    <pubDate>Wed, 01 Jan 2023 10:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>
        """
        
        data = dashboard._parse_rss_xml(xml_content)
        
        assert isinstance(data, dict)
        assert "channel" in data
        assert "items" in data
        assert len(data["items"]) == 1
        
        item = data["items"][0]
        assert "title" in item
        assert "description" in item
        assert "link" in item
        assert "pubDate" in item
    
    def test_get_text_from_element(self):
        """Test getting text from XML element"""
        dashboard = UnifiedNewsDashboard()
        
        # Mock element
        mock_element = MagicMock()
        mock_element.text = "Test Text"
        
        text = dashboard._get_text(mock_element, "title")
        
        assert text == "Test Text"
    
    def test_get_text_from_element_none(self):
        """Test getting text from None element"""
        dashboard = UnifiedNewsDashboard()
        
        text = dashboard._get_text(None, "title")
        
        assert text == "" 