"""
News Data Service for RSS Feed Service
Handles fetching, storing, and analyzing news events
"""

import os
import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import create_engine, text, Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

Base = declarative_base()

class HistoricalNews(Base):
    """Historical news events storage model"""
    
    __tablename__ = 'news_historical'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # News content
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Source information
    source = Column(String(100), nullable=False)
    url = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    
    # Timing
    published_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Analysis results
    sentiment_score = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Event classification
    event_type = Column(String(50), nullable=True)
    
    # Affected symbols (stored as JSON array)
    affected_symbols = Column(JSON, nullable=True)
    
    # Additional metadata
    news_metadata = Column(JSON, nullable=True)
    
    # Provider-specific fields
    provider_id = Column(String(100), nullable=True)
    ticker = Column(String(10), nullable=True)

@dataclass
class NewsEvent:
    """News event data structure"""
    title: str
    content: Optional[str]
    source: str
    url: Optional[str]
    author: Optional[str]
    published_at: datetime
    sentiment_score: Optional[float]
    impact_score: Optional[float]
    confidence_score: Optional[float]
    event_type: Optional[str]
    affected_symbols: List[str]
    news_metadata: Dict[str, Any]
    provider_id: Optional[str]
    ticker: Optional[str]

class NewsDataService:
    """Service for managing news data"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database connection initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        return self.SessionLocal()
    
    async def fetch_news_from_polygon(self, symbol: str, days_back: int = 7) -> List[NewsEvent]:
        """Fetch news from Polygon API"""
        if not self.polygon_api_key:
            logger.warning("⚠️ POLYGON_API_KEY not set - cannot fetch news")
            return []
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for Polygon API
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            logger.info(f"📰 Fetching news for {symbol} from {start_str} to {end_str}")
            
            # Polygon API endpoint for news
            url = f"https://api.polygon.io/v2/reference/news"
            params = {
                "ticker": symbol,
                "published_utc.gte": start_str,
                "published_utc.lte": end_str,
                "limit": 50,
                "apiKey": self.polygon_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        news_events = []
                        for article in results:
                            # Extract affected symbols
                            affected_symbols = []
                            if "tickers" in article:
                                affected_symbols = [ticker for ticker in article["tickers"]]
                            
                            # Create news event
                            news_event = NewsEvent(
                                title=article.get("title", ""),
                                content=article.get("description", ""),
                                source=article.get("publisher", {}).get("name", "polygon"),
                                url=article.get("article_url"),
                                author=article.get("author"),
                                published_at=datetime.fromisoformat(article.get("published_utc", "").replace("Z", "+00:00")),
                                sentiment_score=None,  # Will be calculated by LLM
                                impact_score=None,     # Will be calculated by LLM
                                confidence_score=None, # Will be calculated by LLM
                                event_type=None,      # Will be classified by LLM
                                affected_symbols=affected_symbols,
                                news_metadata={
                                    "polygon_id": article.get("id"),
                                    "keywords": article.get("keywords", []),
                                    "image_url": article.get("image_url"),
                                    "amp_url": article.get("amp_url")
                                },
                                provider_id=article.get("id"),
                                ticker=symbol
                            )
                            news_events.append(news_event)
                        
                        logger.info(f"✅ Fetched {len(news_events)} news articles for {symbol}")
                        return news_events
                    else:
                        logger.warning(f"⚠️ Polygon API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Error fetching news for {symbol}: {e}")
            return []
    
    async def analyze_news_with_llm(self, news_events: List[NewsEvent]) -> List[NewsEvent]:
        """Analyze news events with LLM for sentiment, impact, and classification"""
        if not news_events:
            return []
        
        logger.info(f"🤖 Analyzing {len(news_events)} news events with LLM")
        
        # For now, implement simple analysis
        # In production, this would call the AI analysis service
        for event in news_events:
            # Simple sentiment analysis based on keywords
            event.sentiment_score = self._calculate_sentiment(event.title, event.content or "")
            event.impact_score = self._calculate_impact(event.title, event.content or "")
            event.confidence_score = 0.7  # Default confidence
            event.event_type = self._classify_event_type(event.title, event.content or "")
        
        logger.info(f"✅ Analyzed {len(news_events)} news events")
        return news_events
    
    def _calculate_sentiment(self, title: str, content: str) -> float:
        """Calculate sentiment score (-1.0 to 1.0)"""
        text = (title + " " + content).lower()
        
        positive_words = [
            "beat", "surge", "rise", "gain", "up", "positive", "strong", "growth",
            "profit", "revenue", "approval", "success", "win", "positive", "bullish"
        ]
        
        negative_words = [
            "miss", "fall", "drop", "decline", "down", "negative", "weak", "loss",
            "investigation", "lawsuit", "recall", "bankruptcy", "layoff", "bearish"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_impact(self, title: str, content: str) -> float:
        """Calculate impact score (0.0 to 1.0)"""
        text = (title + " " + content).lower()
        
        high_impact_words = [
            "earnings", "merger", "acquisition", "fda", "sec", "investigation",
            "bankruptcy", "ipo", "ceo", "cfo", "resignation", "recall"
        ]
        
        medium_impact_words = [
            "guidance", "outlook", "analyst", "upgrade", "downgrade", "target",
            "price", "volume", "trading", "market"
        ]
        
        high_count = sum(1 for word in high_impact_words if word in text)
        medium_count = sum(1 for word in medium_impact_words if word in text)
        
        # Calculate impact score
        impact = (high_count * 0.8 + medium_count * 0.4) / max(1, len(text.split()))
        return min(1.0, impact)
    
    def _classify_event_type(self, title: str, content: str) -> str:
        """Classify event type"""
        text = (title + " " + content).lower()
        
        if any(word in text for word in ["earnings", "profit", "revenue", "eps", "ebitda"]):
            return "earnings"
        elif any(word in text for word in ["merger", "acquisition", "buyout", "deal"]):
            return "mergers_acquisitions"
        elif any(word in text for word in ["fda", "sec", "investigation", "lawsuit", "regulatory"]):
            return "regulatory"
        elif any(word in text for word in ["fed", "interest", "inflation", "gdp", "economic"]):
            return "macro_economic"
        else:
            return "general"
    
    def store_news_batch(self, news_events: List[NewsEvent]) -> Dict[str, int]:
        """Store news events in database"""
        if not self.engine:
            logger.error("❌ Database not initialized")
            return {"stored": 0, "errors": len(news_events)}
        
        session = self.get_session()
        stored_count = 0
        error_count = 0
        
        try:
            for event in news_events:
                try:
                    # Check if article already exists
                    existing = session.query(HistoricalNews).filter(
                        HistoricalNews.provider_id == event.provider_id,
                        HistoricalNews.source == event.source
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.title = event.title
                        existing.content = event.content
                        existing.sentiment_score = event.sentiment_score
                        existing.impact_score = event.impact_score
                        existing.confidence_score = event.confidence_score
                        existing.event_type = event.event_type
                        existing.affected_symbols = event.affected_symbols
                        existing.news_metadata = event.news_metadata
                        existing.fetched_at = datetime.utcnow()
                    else:
                        # Create new
                        db_event = HistoricalNews(
                            title=event.title,
                            content=event.content,
                            source=event.source,
                            url=event.url,
                            author=event.author,
                            published_at=event.published_at,
                            sentiment_score=event.sentiment_score,
                            impact_score=event.impact_score,
                            confidence_score=event.confidence_score,
                            event_type=event.event_type,
                            affected_symbols=event.affected_symbols,
                            news_metadata=event.news_metadata,
                            provider_id=event.provider_id,
                            ticker=event.ticker
                        )
                        session.add(db_event)
                    
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error storing news event: {e}")
                    error_count += 1
            
            session.commit()
            logger.info(f"✅ Stored {stored_count} news events, {error_count} errors")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database error: {e}")
            error_count += len(news_events)
        finally:
            session.close()
        
        return {"stored": stored_count, "errors": error_count}
    
    def get_recent_news_for_symbol(self, symbol: str, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get recent news for a symbol"""
        if not self.engine:
            return []
        
        session = self.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            news_articles = session.query(HistoricalNews).filter(
                HistoricalNews.ticker == symbol,
                HistoricalNews.published_at >= cutoff_time
            ).order_by(HistoricalNews.published_at.desc()).limit(20).all()
            
            return [
                {
                    "title": article.title,
                    "content": article.content,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at.isoformat(),
                    "sentiment_score": article.sentiment_score,
                    "impact_score": article.impact_score,
                    "event_type": article.event_type,
                    "affected_symbols": article.affected_symbols or []
                }
                for article in news_articles
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting recent news for {symbol}: {e}")
            return []
        finally:
            session.close()
    
    def get_news_statistics(self, symbol: str, days_back: int = 7) -> Dict[str, Any]:
        """Get news statistics for a symbol"""
        if not self.engine:
            return {"total_articles": 0, "avg_sentiment": 0.0, "sources": []}
        
        session = self.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            articles = session.query(HistoricalNews).filter(
                HistoricalNews.ticker == symbol,
                HistoricalNews.published_at >= cutoff_time
            ).all()
            
            if not articles:
                return {"total_articles": 0, "avg_sentiment": 0.0, "sources": []}
            
            # Calculate statistics
            total_articles = len(articles)
            sentiments = [a.sentiment_score for a in articles if a.sentiment_score is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            sources = list(set(a.source for a in articles))
            
            return {
                "total_articles": total_articles,
                "avg_sentiment": avg_sentiment,
                "sources": sources,
                "event_types": list(set(a.event_type for a in articles if a.event_type))
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting news statistics for {symbol}: {e}")
            return {"total_articles": 0, "avg_sentiment": 0.0, "sources": []}
        finally:
            session.close() 