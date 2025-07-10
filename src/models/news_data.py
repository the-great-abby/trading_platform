"""
News Data Models for PostgreSQL Storage
"""

from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Text, Index, PrimaryKeyConstraint, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional

Base = declarative_base()


class HistoricalNews(Base):
    """Historical news events storage model"""
    
    __tablename__ = 'historical_news'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # News content
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)  # Full article content if available
    summary = Column(Text, nullable=True)  # Article summary
    
    # Source information
    source = Column(String(100), nullable=False)  # 'polygon', 'reuters', 'bloomberg', etc.
    url = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    
    # Timing
    published_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=func.now())
    
    # Analysis results
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    impact_score = Column(Float, nullable=True)     # 0.0 to 1.0
    confidence_score = Column(Float, nullable=True) # 0.0 to 1.0
    
    # Event classification
    event_type = Column(String(50), nullable=True)  # 'earnings', 'mergers_acquisitions', 'regulatory', etc.
    
    # Affected symbols (stored as JSON array)
    affected_symbols = Column(JSON, nullable=True)  # ['AAPL', 'MSFT']
    
    # Additional metadata
    news_metadata = Column(JSON, nullable=True)  # Additional fields from Polygon API
    
    # Provider-specific fields
    provider_id = Column(String(100), nullable=True)  # Polygon article ID
    ticker = Column(String(10), nullable=True)        # Primary ticker from Polygon
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_news_published_at', 'published_at'),
        Index('idx_news_event_type', 'event_type'),
        Index('idx_news_source', 'source'),
        Index('idx_news_ticker', 'ticker'),
        Index('idx_news_sentiment', 'sentiment_score'),
        Index('idx_news_impact', 'impact_score'),
    )
    
    def __repr__(self):
        return f"<HistoricalNews(id={self.id}, title='{self.title[:50]}...', published_at='{self.published_at}')>"


class NewsCache(Base):
    """Cache metadata for tracking news data freshness"""
    
    __tablename__ = 'news_cache'
    
    # Primary key
    symbol = Column(String(10), nullable=False)
    source = Column(String(100), nullable=False)
    
    # Cache metadata
    earliest_date = Column(DateTime, nullable=True)
    latest_date = Column(DateTime, nullable=True)
    total_articles = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'source'),
        Index('idx_cache_symbol', 'symbol'),
        Index('idx_cache_source', 'source'),
    )
    
    def __repr__(self):
        return f"<NewsCache(symbol='{self.symbol}', source='{self.source}', articles={self.total_articles})>" 