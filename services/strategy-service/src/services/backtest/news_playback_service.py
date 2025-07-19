"""
News Playback Service for Backtesting
Provides historical news events during backtest execution
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Generator, Iterator
from dataclasses import dataclass

from ...models.news_data import HistoricalNews
from ...services.database.news_data_service import NewsDataService

logger = logging.getLogger(__name__)


@dataclass
class BacktestNewsEvent:
    """News event for backtesting"""
    timestamp: datetime
    title: str
    content: Optional[str]
    source: str
    url: Optional[str]
    sentiment_score: Optional[float]
    impact_score: Optional[float]
    event_type: Optional[str]
    affected_symbols: List[str]
    metadata: Dict[str, Any]


class NewsPlaybackService:
    """Service for providing historical news during backtesting"""
    
    def __init__(self, db_service: Optional[NewsDataService] = None):
        self.db_service = db_service or NewsDataService()
        self.news_events: List[BacktestNewsEvent] = []
        self.current_index = 0
        self.is_initialized = False
    
    def initialize_for_backtest(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> bool:
        """
        Initialize news playback for a backtest period
        
        Args:
            symbols: List of symbols to include
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Initializing news playback for {len(symbols)} symbols from {start_date} to {end_date}")
            
            # Get news articles from database
            news_articles = list(self.db_service.get_news_for_backtest(symbols, start_date, end_date))
            
            if not news_articles:
                logger.warning("No news articles found for backtest period")
                self.news_events = []
                self.current_index = 0
                self.is_initialized = True
                return True
            
            # Convert to backtest events
            self.news_events = []
            for article in news_articles:
                event = BacktestNewsEvent(
                    timestamp=article.published_at,
                    title=article.title,
                    content=article.content,
                    source=article.source,
                    url=article.url,
                    sentiment_score=article.sentiment_score,
                    impact_score=article.impact_score,
                    event_type=article.event_type,
                    affected_symbols=article.affected_symbols or [],
                    metadata=article.metadata or {}
                )
                self.news_events.append(event)
            
            # Sort by timestamp (chronological order)
            self.news_events.sort(key=lambda x: x.timestamp)
            
            self.current_index = 0
            self.is_initialized = True
            
            logger.info(f"Initialized news playback with {len(self.news_events)} events")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing news playback: {e}")
            return False
    
    def get_news_at_timestamp(self, timestamp: datetime) -> List[BacktestNewsEvent]:
        """
        Get news events that occurred at or before the given timestamp
        
        Args:
            timestamp: Current backtest timestamp
        
        Returns:
            List of news events up to the timestamp
        """
        if not self.is_initialized:
            logger.warning("News playback not initialized")
            return []
        
        events = []
        
        # Find events that occurred at or before the timestamp
        while (self.current_index < len(self.news_events) and 
               self.news_events[self.current_index].timestamp <= timestamp):
            events.append(self.news_events[self.current_index])
            self.current_index += 1
        
        return events
    
    def get_news_for_symbol(self, symbol: str, timestamp: datetime) -> List[BacktestNewsEvent]:
        """
        Get news events for a specific symbol at or before the given timestamp
        
        Args:
            symbol: Stock symbol
            timestamp: Current backtest timestamp
        
        Returns:
            List of news events for the symbol
        """
        all_events = self.get_news_at_timestamp(timestamp)
        return [event for event in all_events if symbol in event.affected_symbols]
    
    def get_recent_news(
        self, 
        symbol: str, 
        timestamp: datetime, 
        hours_back: int = 24
    ) -> List[BacktestNewsEvent]:
        """
        Get recent news events for a symbol within a time window
        
        Args:
            symbol: Stock symbol
            timestamp: Current backtest timestamp
            hours_back: Hours to look back for news
        
        Returns:
            List of recent news events
        """
        cutoff_time = timestamp - timedelta(hours=hours_back)
        
        # Get all events up to current timestamp
        all_events = self.get_news_at_timestamp(timestamp)
        
        # Filter for symbol and time window
        recent_events = [
            event for event in all_events 
            if (symbol in event.affected_symbols and 
                event.timestamp >= cutoff_time)
        ]
        
        return recent_events
    
    def get_news_sentiment(
        self, 
        symbol: str, 
        timestamp: datetime, 
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Calculate news sentiment for a symbol based on recent news
        
        Args:
            symbol: Stock symbol
            timestamp: Current backtest timestamp
            hours_back: Hours to look back for news
        
        Returns:
            Dictionary with sentiment analysis
        """
        recent_news = self.get_recent_news(symbol, timestamp, hours_back)
        
        if not recent_news:
            return {
                'symbol': symbol,
                'sentiment_score': 0.0,
                'impact_score': 0.0,
                'event_count': 0,
                'recent_events': []
            }
        
        # Calculate average sentiment and impact
        sentiments = [event.sentiment_score for event in recent_news if event.sentiment_score is not None]
        impacts = [event.impact_score for event in recent_news if event.impact_score is not None]
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        avg_impact = sum(impacts) / len(impacts) if impacts else 0.0
        
        # Prepare recent events summary
        recent_events_summary = [
            {
                'title': event.title,
                'timestamp': event.timestamp.isoformat(),
                'sentiment': event.sentiment_score or 0.0,
                'impact': event.impact_score or 0.0,
                'event_type': event.event_type or 'general'
            }
            for event in recent_news[-5:]  # Last 5 events
        ]
        
        return {
            'symbol': symbol,
            'sentiment_score': avg_sentiment,
            'impact_score': avg_impact,
            'event_count': len(recent_news),
            'recent_events': recent_events_summary
        }
    
    def get_market_news(
        self, 
        timestamp: datetime, 
        hours_back: int = 24
    ) -> List[BacktestNewsEvent]:
        """
        Get general market news (not specific to individual symbols)
        
        Args:
            timestamp: Current backtest timestamp
            hours_back: Hours to look back for news
        
        Returns:
            List of market news events
        """
        cutoff_time = timestamp - timedelta(hours=hours_back)
        
        # Get all events up to current timestamp
        all_events = self.get_news_at_timestamp(timestamp)
        
        # Filter for market-wide news (no specific symbols or macro events)
        market_events = [
            event for event in all_events 
            if (event.timestamp >= cutoff_time and
                (not event.affected_symbols or 
                 event.event_type in ['macro_economic', 'geopolitical', 'sector_specific']))
        ]
        
        return market_events
    
    def reset(self):
        """Reset the news playback to the beginning"""
        self.current_index = 0
        logger.info("News playback reset to beginning")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded news data"""
        if not self.is_initialized:
            return {'error': 'News playback not initialized'}
        
        if not self.news_events:
            return {
                'total_events': 0,
                'date_range': None,
                'symbols': [],
                'sources': []
            }
        
        # Calculate statistics
        dates = [event.timestamp for event in self.news_events]
        all_symbols = set()
        sources = set()
        
        for event in self.news_events:
            all_symbols.update(event.affected_symbols)
            sources.add(event.source)
        
        return {
            'total_events': len(self.news_events),
            'date_range': {
                'start': min(dates).isoformat(),
                'end': max(dates).isoformat()
            },
            'symbols': list(all_symbols),
            'sources': list(sources),
            'current_index': self.current_index,
            'events_processed': self.current_index,
            'events_remaining': len(self.news_events) - self.current_index
        }
    
    def preview_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Preview upcoming news events
        
        Args:
            count: Number of events to preview
        
        Returns:
            List of event previews
        """
        if not self.is_initialized:
            return []
        
        preview_events = []
        start_index = self.current_index
        
        for i in range(min(count, len(self.news_events) - start_index)):
            event = self.news_events[start_index + i]
            preview_events.append({
                'timestamp': event.timestamp.isoformat(),
                'title': event.title,
                'symbols': event.affected_symbols,
                'event_type': event.event_type,
                'sentiment': event.sentiment_score,
                'impact': event.impact_score
            })
        
        return preview_events 