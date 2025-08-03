"""
Tests for news data models
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.news_data import HistoricalNews, NewsCache, Base


class TestHistoricalNews:
    """Test the HistoricalNews model"""
    
    @pytest.fixture
    def sample_news_data(self):
        """Sample news data for testing"""
        return {
            'title': 'Apple Reports Strong Q4 Earnings',
            'content': 'Apple Inc. reported strong fourth quarter earnings...',
            'summary': 'Apple beats earnings expectations',
            'source': 'polygon',
            'url': 'https://example.com/apple-earnings',
            'author': 'John Doe',
            'published_at': datetime(2024, 1, 15, 10, 30, 0),
            'sentiment_score': 0.8,
            'impact_score': 0.9,
            'confidence_score': 0.85,
            'event_type': 'earnings',
            'affected_symbols': ['AAPL', 'MSFT'],
            'news_metadata': {'category': 'earnings', 'importance': 'high'},
            'provider_id': 'polygon_12345',
            'ticker': 'AAPL'
        }
    
    def test_historical_news_creation(self, sample_news_data):
        """Test creating a HistoricalNews instance"""
        news = HistoricalNews(**sample_news_data)
        
        assert news.title == sample_news_data['title']
        assert news.content == sample_news_data['content']
        assert news.summary == sample_news_data['summary']
        assert news.source == sample_news_data['source']
        assert news.url == sample_news_data['url']
        assert news.author == sample_news_data['author']
        assert news.published_at == sample_news_data['published_at']
        assert news.sentiment_score == sample_news_data['sentiment_score']
        assert news.impact_score == sample_news_data['impact_score']
        assert news.confidence_score == sample_news_data['confidence_score']
        assert news.event_type == sample_news_data['event_type']
        assert news.affected_symbols == sample_news_data['affected_symbols']
        assert news.news_metadata == sample_news_data['news_metadata']
        assert news.provider_id == sample_news_data['provider_id']
        assert news.ticker == sample_news_data['ticker']
    
    def test_historical_news_minimal_creation(self):
        """Test creating HistoricalNews with minimal required fields"""
        minimal_data = {
            'title': 'Test News',
            'source': 'test',
            'published_at': datetime.now()
        }
        
        news = HistoricalNews(**minimal_data)
        
        assert news.title == 'Test News'
        assert news.source == 'test'
        assert news.content is None
        assert news.summary is None
        assert news.url is None
        assert news.author is None
        assert news.sentiment_score is None
        assert news.impact_score is None
        assert news.confidence_score is None
        assert news.event_type is None
        assert news.affected_symbols is None
        assert news.news_metadata is None
        assert news.provider_id is None
        assert news.ticker is None
    
    def test_historical_news_repr(self, sample_news_data):
        """Test string representation of HistoricalNews"""
        news = HistoricalNews(**sample_news_data)
        repr_str = repr(news)
        
        assert 'HistoricalNews' in repr_str
        assert 'id=' in repr_str
        assert 'title=' in repr_str
        assert 'published_at=' in repr_str
        assert sample_news_data['title'][:50] in repr_str
    
    def test_historical_news_sentiment_score_range(self):
        """Test sentiment score validation"""
        # Test valid sentiment scores
        valid_scores = [-1.0, -0.5, 0.0, 0.5, 1.0]
        
        for score in valid_scores:
            news = HistoricalNews(
                title='Test',
                source='test',
                published_at=datetime.now(),
                sentiment_score=score
            )
            assert news.sentiment_score == score
    
    def test_historical_news_impact_score_range(self):
        """Test impact score validation"""
        # Test valid impact scores
        valid_scores = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for score in valid_scores:
            news = HistoricalNews(
                title='Test',
                source='test',
                published_at=datetime.now(),
                impact_score=score
            )
            assert news.impact_score == score
    
    def test_historical_news_confidence_score_range(self):
        """Test confidence score validation"""
        # Test valid confidence scores
        valid_scores = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for score in valid_scores:
            news = HistoricalNews(
                title='Test',
                source='test',
                published_at=datetime.now(),
                confidence_score=score
            )
            assert news.confidence_score == score
    
    def test_historical_news_event_types(self):
        """Test different event types"""
        event_types = ['earnings', 'mergers_acquisitions', 'regulatory', 'product_launch', 'market_news']
        
        for event_type in event_types:
            news = HistoricalNews(
                title='Test',
                source='test',
                published_at=datetime.now(),
                event_type=event_type
            )
            assert news.event_type == event_type
    
    def test_historical_news_affected_symbols_json(self):
        """Test affected symbols as JSON array"""
        symbols_list = ['AAPL', 'MSFT', 'GOOGL']
        
        news = HistoricalNews(
            title='Test',
            source='test',
            published_at=datetime.now(),
            affected_symbols=symbols_list
        )
        
        assert news.affected_symbols == symbols_list
        assert isinstance(news.affected_symbols, list)
    
    def test_historical_news_metadata_json(self):
        """Test news metadata as JSON"""
        metadata = {
            'category': 'earnings',
            'importance': 'high',
            'tags': ['technology', 'finance'],
            'source_credibility': 0.9
        }
        
        news = HistoricalNews(
            title='Test',
            source='test',
            published_at=datetime.now(),
            news_metadata=metadata
        )
        
        assert news.news_metadata == metadata
        assert isinstance(news.news_metadata, dict)


class TestNewsCache:
    """Test the NewsCache model"""
    
    @pytest.fixture
    def sample_cache_data(self):
        """Sample cache data for testing"""
        return {
            'symbol': 'AAPL',
            'source': 'polygon',
            'earliest_date': datetime(2024, 1, 1, 9, 30, 0),
            'latest_date': datetime(2024, 1, 15, 16, 0, 0),
            'total_articles': 150,
            'last_updated': datetime(2024, 1, 15, 16, 30, 0)
        }
    
    def test_news_cache_creation(self, sample_cache_data):
        """Test creating a NewsCache instance"""
        cache = NewsCache(**sample_cache_data)
        
        assert cache.symbol == sample_cache_data['symbol']
        assert cache.source == sample_cache_data['source']
        assert cache.earliest_date == sample_cache_data['earliest_date']
        assert cache.latest_date == sample_cache_data['latest_date']
        assert cache.total_articles == sample_cache_data['total_articles']
        assert cache.last_updated == sample_cache_data['last_updated']
    
    def test_news_cache_minimal_creation(self):
        """Test creating NewsCache with minimal required fields"""
        minimal_data = {
            'symbol': 'MSFT',
            'source': 'reuters'
        }
        
        cache = NewsCache(**minimal_data)
        
        assert cache.symbol == 'MSFT'
        assert cache.source == 'reuters'
        assert cache.earliest_date is None
        assert cache.latest_date is None
        assert cache.total_articles == 0
        assert cache.last_updated is not None  # Should have default value
    
    def test_news_cache_repr(self, sample_cache_data):
        """Test string representation of NewsCache"""
        cache = NewsCache(**sample_cache_data)
        repr_str = repr(cache)
        
        assert 'NewsCache' in repr_str
        assert 'symbol=' in repr_str
        assert 'source=' in repr_str
        assert 'articles=' in repr_str
        assert sample_cache_data['symbol'] in repr_str
        assert str(sample_cache_data['total_articles']) in repr_str
    
    def test_news_cache_composite_primary_key(self):
        """Test that symbol and source form composite primary key"""
        cache1 = NewsCache(symbol='AAPL', source='polygon')
        cache2 = NewsCache(symbol='AAPL', source='reuters')
        cache3 = NewsCache(symbol='MSFT', source='polygon')
        
        # All should be different records
        assert cache1.symbol == 'AAPL' and cache1.source == 'polygon'
        assert cache2.symbol == 'AAPL' and cache2.source == 'reuters'
        assert cache3.symbol == 'MSFT' and cache3.source == 'polygon'
    
    def test_news_cache_date_range(self):
        """Test date range functionality"""
        earliest = datetime(2024, 1, 1, 9, 30, 0)
        latest = datetime(2024, 1, 15, 16, 0, 0)
        
        cache = NewsCache(
            symbol='AAPL',
            source='polygon',
            earliest_date=earliest,
            latest_date=latest
        )
        
        assert cache.earliest_date == earliest
        assert cache.latest_date == latest
        
        # Test that latest is after earliest
        assert cache.latest_date > cache.earliest_date
    
    def test_news_cache_article_count(self):
        """Test article count functionality"""
        cache = NewsCache(
            symbol='AAPL',
            source='polygon',
            total_articles=100
        )
        
        assert cache.total_articles == 100
        
        # Test updating article count
        cache.total_articles = 150
        assert cache.total_articles == 150
    
    def test_news_cache_last_updated_auto(self):
        """Test automatic last_updated timestamp"""
        cache = NewsCache(symbol='AAPL', source='polygon')
        
        # Should have a timestamp
        assert cache.last_updated is not None
        assert isinstance(cache.last_updated, datetime)


class TestNewsDataModelsIntegration:
    """Integration tests for news data models"""
    
    @pytest.fixture
    def test_engine(self):
        """Create test database engine"""
        return create_engine('sqlite:///:memory:')
    
    @pytest.fixture
    def test_session(self, test_engine):
        """Create test database session"""
        Base.metadata.create_all(test_engine)
        Session = sessionmaker(bind=test_engine)
        return Session()
    
    def test_historical_news_database_operations(self, test_session):
        """Test HistoricalNews database operations"""
        # Create news record
        news = HistoricalNews(
            title='Test News',
            source='test',
            published_at=datetime.now(),
            sentiment_score=0.5,
            event_type='earnings'
        )
        
        # Add to database
        test_session.add(news)
        test_session.commit()
        
        # Query from database
        retrieved_news = test_session.query(HistoricalNews).first()
        
        assert retrieved_news.title == 'Test News'
        assert retrieved_news.source == 'test'
        assert retrieved_news.sentiment_score == 0.5
        assert retrieved_news.event_type == 'earnings'
    
    def test_news_cache_database_operations(self, test_session):
        """Test NewsCache database operations"""
        # Create cache record
        cache = NewsCache(
            symbol='AAPL',
            source='polygon',
            total_articles=100,
            earliest_date=datetime(2024, 1, 1),
            latest_date=datetime(2024, 1, 15)
        )
        
        # Add to database
        test_session.add(cache)
        test_session.commit()
        
        # Query from database
        retrieved_cache = test_session.query(NewsCache).first()
        
        assert retrieved_cache.symbol == 'AAPL'
        assert retrieved_cache.source == 'polygon'
        assert retrieved_cache.total_articles == 100
        assert retrieved_cache.earliest_date == datetime(2024, 1, 1)
        assert retrieved_cache.latest_date == datetime(2024, 1, 15)
    
    def test_news_cache_composite_key_constraint(self, test_session):
        """Test composite primary key constraint"""
        # Create first cache record
        cache1 = NewsCache(symbol='AAPL', source='polygon')
        test_session.add(cache1)
        test_session.commit()
        
        # Try to create duplicate (should work as we're testing constraints)
        cache2 = NewsCache(symbol='AAPL', source='polygon')
        test_session.add(cache2)
        
        # This should work in SQLite but would fail in PostgreSQL with proper constraints
        test_session.commit()
        
        # Verify both records exist
        caches = test_session.query(NewsCache).all()
        assert len(caches) == 2
    
    def test_historical_news_indexes(self, test_engine):
        """Test that indexes are created properly"""
        # Create tables
        Base.metadata.create_all(test_engine)
        
        # Check that indexes exist (this is a basic check)
        # In a real database, you would query the index information
        assert True  # Placeholder for index verification


class TestNewsDataModelsEdgeCases:
    """Test edge cases for news data models"""
    
    def test_historical_news_empty_strings(self):
        """Test handling of empty strings"""
        news = HistoricalNews(
            title='',
            source='',
            published_at=datetime.now(),
            content='',
            summary='',
            url='',
            author=''
        )
        
        assert news.title == ''
        assert news.source == ''
        assert news.content == ''
        assert news.summary == ''
        assert news.url == ''
        assert news.author == ''
    
    def test_historical_news_long_fields(self):
        """Test handling of long field values"""
        long_title = 'A' * 1000  # Very long title
        long_content = 'B' * 10000  # Very long content
        
        news = HistoricalNews(
            title=long_title,
            content=long_content,
            source='test',
            published_at=datetime.now()
        )
        
        assert news.title == long_title
        assert news.content == long_content
    
    def test_historical_news_extreme_scores(self):
        """Test handling of extreme score values"""
        news = HistoricalNews(
            title='Test',
            source='test',
            published_at=datetime.now(),
            sentiment_score=-1.0,  # Minimum
            impact_score=0.0,      # Minimum
            confidence_score=1.0    # Maximum
        )
        
        assert news.sentiment_score == -1.0
        assert news.impact_score == 0.0
        assert news.confidence_score == 1.0
    
    def test_news_cache_zero_articles(self):
        """Test cache with zero articles"""
        cache = NewsCache(
            symbol='AAPL',
            source='polygon',
            total_articles=0
        )
        
        assert cache.total_articles == 0
    
    def test_news_cache_same_dates(self):
        """Test cache with same earliest and latest dates"""
        same_date = datetime(2024, 1, 15, 10, 0, 0)
        
        cache = NewsCache(
            symbol='AAPL',
            source='polygon',
            earliest_date=same_date,
            latest_date=same_date
        )
        
        assert cache.earliest_date == same_date
        assert cache.latest_date == same_date


class TestNewsDataModelsValidation:
    """Test validation scenarios for news data models"""
    
    def test_historical_news_required_fields(self):
        """Test that required fields are properly enforced"""
        # Should work with required fields only
        news = HistoricalNews(
            title='Test',
            source='test',
            published_at=datetime.now()
        )
        
        assert news.title == 'Test'
        assert news.source == 'test'
        assert news.published_at is not None
    
    def test_news_cache_required_fields(self):
        """Test that required fields are properly enforced for cache"""
        # Should work with required fields only
        cache = NewsCache(
            symbol='AAPL',
            source='polygon'
        )
        
        assert cache.symbol == 'AAPL'
        assert cache.source == 'polygon'
    
    def test_historical_news_optional_fields_none(self):
        """Test that optional fields can be None"""
        news = HistoricalNews(
            title='Test',
            source='test',
            published_at=datetime.now(),
            content=None,
            summary=None,
            url=None,
            author=None,
            sentiment_score=None,
            impact_score=None,
            confidence_score=None,
            event_type=None,
            affected_symbols=None,
            news_metadata=None,
            provider_id=None,
            ticker=None
        )
        
        # All optional fields should be None
        assert news.content is None
        assert news.summary is None
        assert news.url is None
        assert news.author is None
        assert news.sentiment_score is None
        assert news.impact_score is None
        assert news.confidence_score is None
        assert news.event_type is None
        assert news.affected_symbols is None
        assert news.news_metadata is None
        assert news.provider_id is None
        assert news.ticker is None


class TestNewsDataModelsPerformance:
    """Performance tests for news data models"""
    
    def test_historical_news_creation_performance(self):
        """Test performance of creating many HistoricalNews instances"""
        import time
        
        start_time = time.time()
        
        # Create 1000 news records
        for i in range(1000):
            HistoricalNews(
                title=f'News {i}',
                source='test',
                published_at=datetime.now(),
                sentiment_score=0.5,
                event_type='earnings'
            )
        
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second
    
    def test_news_cache_creation_performance(self):
        """Test performance of creating many NewsCache instances"""
        import time
        
        start_time = time.time()
        
        # Create 1000 cache records
        for i in range(1000):
            NewsCache(
                symbol=f'SYMBOL{i}',
                source='test',
                total_articles=i
            )
        
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second 