"""
Social Media Sentiment Strategy
==============================
A strategy that analyzes Twitter, Reddit, and news sentiment to predict short-term price movements.
Uses NLP to extract trading signals from social media data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import re
from textblob import TextBlob
import asyncio

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class SocialMediaSentimentStrategy(BaseStrategy):
    """
    Social Media Sentiment Strategy
    
    Features:
    - Analyzes Twitter, Reddit, and news sentiment
    - Uses NLP to extract trading signals
    - Predicts short-term price movements
    - Real-time sentiment tracking
    - Multi-platform sentiment aggregation
    """
    
    def __init__(self, 
                 name: str = "SocialMediaSentiment",
                 sentiment_threshold: float = 0.2,
                 volume_threshold: int = 100,
                 confidence_threshold: float = 0.6,
                 sentiment_window: int = 24,  # hours
                 min_mentions: int = 10):
        super().__init__(name)
        self.sentiment_threshold = sentiment_threshold
        self.volume_threshold = volume_threshold
        self.confidence_threshold = confidence_threshold
        self.sentiment_window = sentiment_window
        self.min_mentions = min_mentions
        
        # Sentiment cache
        self.sentiment_cache = {}
        self.mention_counts = {}
        
        # Keywords for different sentiment types
        self.bullish_keywords = [
            'bullish', 'moon', 'rocket', 'pump', 'buy', 'long', 'strong', 'breakout',
            'earnings beat', 'upgrade', 'positive', 'growth', 'revenue', 'profit'
        ]
        
        self.bearish_keywords = [
            'bearish', 'dump', 'crash', 'sell', 'short', 'weak', 'breakdown',
            'earnings miss', 'downgrade', 'negative', 'decline', 'loss', 'debt'
        ]
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using multiple methods"""
        
        # Clean text
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Method 1: TextBlob sentiment
        blob = TextBlob(text)
        textblob_sentiment = blob.sentiment.polarity
        
        # Method 2: Keyword-based sentiment
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in clean_text)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in clean_text)
        
        keyword_sentiment = 0.0
        if bullish_count > 0 or bearish_count > 0:
            keyword_sentiment = (bullish_count - bearish_count) / max(bullish_count + bearish_count, 1)
        
        # Method 3: Volume and engagement indicators
        engagement_score = 0.0
        if '🚀' in text or 'moon' in clean_text:
            engagement_score = 0.3
        elif '📉' in text or 'crash' in clean_text:
            engagement_score = -0.3
        
        # Combine sentiment scores
        combined_sentiment = (textblob_sentiment * 0.4 + 
                            keyword_sentiment * 0.4 + 
                            engagement_score * 0.2)
        
        return {
            'textblob_sentiment': textblob_sentiment,
            'keyword_sentiment': keyword_sentiment,
            'engagement_score': engagement_score,
            'combined_sentiment': combined_sentiment
        }
    
    def aggregate_sentiment(self, sentiment_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate sentiment from multiple sources"""
        
        if not sentiment_data:
            return {'overall_sentiment': 0.0, 'confidence': 0.0, 'volume': 0}
        
        # Extract sentiment scores
        sentiments = [item.get('sentiment', 0.0) for item in sentiment_data]
        volumes = [item.get('volume', 1) for item in sentiment_data]
        
        # Weight by volume
        total_volume = sum(volumes)
        if total_volume == 0:
            return {'overall_sentiment': 0.0, 'confidence': 0.0, 'volume': 0}
        
        weighted_sentiment = sum(s * v for s, v in zip(sentiments, volumes)) / total_volume
        
        # Calculate confidence based on volume and consistency
        volume_confidence = min(total_volume / self.volume_threshold, 1.0)
        
        # Consistency confidence (lower std = higher confidence)
        sentiment_std = np.std(sentiments) if len(sentiments) > 1 else 0
        consistency_confidence = max(0, 1 - sentiment_std)
        
        overall_confidence = (volume_confidence * 0.6 + consistency_confidence * 0.4)
        
        return {
            'overall_sentiment': weighted_sentiment,
            'confidence': overall_confidence,
            'volume': total_volume
        }
    
    def get_social_media_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get social media data for symbol (mock implementation)"""
        
        # Mock data - in real implementation, this would fetch from APIs
        mock_data = [
            {
                'platform': 'twitter',
                'text': f'$AAPL looking bullish today! Strong earnings report 📈',
                'timestamp': datetime.now() - timedelta(hours=2),
                'volume': 150,
                'sentiment': 0.7
            },
            {
                'platform': 'reddit',
                'text': f'AAPL stock discussion - anyone else seeing this breakout?',
                'timestamp': datetime.now() - timedelta(hours=1),
                'volume': 80,
                'sentiment': 0.5
            },
            {
                'platform': 'twitter',
                'text': f'$AAPL earnings miss - stock might be in trouble 📉',
                'timestamp': datetime.now() - timedelta(hours=3),
                'volume': 200,
                'sentiment': -0.6
            }
        ]
        
        # Filter by time window
        cutoff_time = datetime.now() - timedelta(hours=self.sentiment_window)
        recent_data = [item for item in mock_data if item['timestamp'] > cutoff_time]
        
        return recent_data
    
    def calculate_sentiment_score(self, symbol: str) -> Dict[str, float]:
        """Calculate sentiment score for a symbol"""
        
        # Get social media data
        social_data = self.get_social_media_data(symbol)
        
        if not social_data:
            return {'sentiment': 0.0, 'confidence': 0.0, 'volume': 0}
        
        # Analyze sentiment for each post
        sentiment_analysis = []
        for post in social_data:
            analysis = self.analyze_text_sentiment(post['text'])
            sentiment_analysis.append({
                'sentiment': analysis['combined_sentiment'],
                'volume': post['volume'],
                'platform': post['platform']
            })
        
        # Aggregate sentiment
        aggregated = self.aggregate_sentiment(sentiment_analysis)
        
        return aggregated
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate social media sentiment-based trading signal"""
        
        if len(data) < 10:
            return None
        
        # Calculate sentiment score
        sentiment_data = self.calculate_sentiment_score(symbol)
        
        sentiment = sentiment_data['sentiment']
        confidence = sentiment_data['confidence']
        volume = sentiment_data['volume']
        
        # Check if we have enough data
        if volume < self.min_mentions:
            return None
        
        # Generate signal based on sentiment
        action = None
        
        if sentiment > self.sentiment_threshold and confidence > self.confidence_threshold:
            action = "BUY"
        elif sentiment < -self.sentiment_threshold and confidence > self.confidence_threshold:
            action = "SELL"
        
        if not action:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Calculate position size based on sentiment strength
        sentiment_strength = abs(sentiment)
        position_size = self._calculate_quantity(current_price, confidence, sentiment_strength)
        
        signal = TradeSignal(
            symbol=symbol,
            action=action,
            quantity=position_size,
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'sentiment_score': sentiment,
                'sentiment_volume': volume,
                'sentiment_strength': sentiment_strength,
                'sentiment_threshold': self.sentiment_threshold,
                'signal_type': 'social_media_sentiment',
                'platforms_analyzed': ['twitter', 'reddit', 'news'],
                'sentiment_window_hours': self.sentiment_window
            }
        )
        
        logger.info(f"Social Media Sentiment signal: {symbol} {action} "
                   f"(sentiment: {sentiment:.3f}, confidence: {confidence:.3f}, "
                   f"volume: {volume})")
        
        return signal
    
    def _calculate_quantity(self, price: float, confidence: float, sentiment_strength: float) -> float:
        """Calculate position size based on confidence and sentiment strength"""
        base_size = 1000  # Base position size
        sentiment_multiplier = 1 + sentiment_strength  # Stronger sentiment = larger position
        return (base_size * confidence * sentiment_multiplier) / price
    
    def get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment summary for a symbol"""
        sentiment_data = self.calculate_sentiment_score(symbol)
        social_data = self.get_social_media_data(symbol)
        
        return {
            'symbol': symbol,
            'sentiment_score': sentiment_data['sentiment'],
            'confidence': sentiment_data['confidence'],
            'volume': sentiment_data['volume'],
            'recent_posts': len(social_data),
            'sentiment_window_hours': self.sentiment_window,
            'threshold': self.sentiment_threshold
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "sentiment_threshold": self.sentiment_threshold,
            "volume_threshold": self.volume_threshold,
            "confidence_threshold": self.confidence_threshold,
            "sentiment_window_hours": self.sentiment_window,
            "min_mentions": self.min_mentions,
            "bullish_keywords_count": len(self.bullish_keywords),
            "bearish_keywords_count": len(self.bearish_keywords)
        } 