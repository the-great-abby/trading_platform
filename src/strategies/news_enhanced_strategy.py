"""
News-Enhanced Trading Strategy - Combines technical indicators with news sentiment
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .base import BaseStrategy
from ..core.types import TradeSignal
from ..services.ai.ollama_service import OllamaService, AIAnalysis


@dataclass
class NewsSentimentData:
    """News sentiment data structure"""
    symbol: str
    sentiment_score: float
    impact_score: float
    event_count: int
    recent_events: List[Dict[str, Any]]
    ai_enhanced_sentiment: Optional[float] = None


class NewsEnhancedStrategy(BaseStrategy):
    """Strategy that combines technical indicators with news sentiment analysis"""
    
    def __init__(self, 
                 technical_weight: float = 0.6,
                 news_weight: float = 0.4,
                 sentiment_threshold: float = 0.3,
                 **kwargs):
        super().__init__("News_Enhanced_Strategy", kwargs)
        self.technical_weight = technical_weight
        self.news_weight = news_weight
        self.sentiment_threshold = sentiment_threshold
        self.ollama_service = None
        self.news_cache = {}  # Cache news sentiment data
        
    async def initialize(self, ollama_url: str = "http://ollama:11434"):
        """Initialize the strategy with Ollama service"""
        self.ollama_service = OllamaService(base_url=ollama_url)
        
    async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:
        """Generate trading signal combining technical and news analysis"""
        
        if data.empty or len(data) < 50:
            return None
        
        # Get technical signals from multiple indicators
        technical_signals = await self._get_technical_signals(symbol, data)
        
        # Get news sentiment data
        news_sentiment = await self._get_news_sentiment(symbol)
        
        # Combine signals using AI if available
        if self.ollama_service:
            return await self._generate_ai_enhanced_signal(
                symbol, technical_signals, news_sentiment, data
            )
        else:
            return await self._generate_weighted_signal(
                symbol, technical_signals, news_sentiment, data
            )
    
    async def _get_technical_signals(self, symbol: str, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get technical signals from multiple indicators"""
        signals = []
        
        # RSI Signal
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            rsi_signal = {
                'indicator': 'RSI',
                'value': rsi,
                'signal': 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD',
                'strength': abs(50 - rsi) / 50,  # 0-1 strength
                'confidence': 0.7 if abs(50 - rsi) > 20 else 0.3
            }
            signals.append(rsi_signal)
        
        # SMA Crossover Signal
        if len(data) >= 50:
            short_sma = data['Close'].rolling(window=20).mean().iloc[-1]
            long_sma = data['Close'].rolling(window=50).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            sma_signal = {
                'indicator': 'SMA_CROSSOVER',
                'short_sma': short_sma,
                'long_sma': long_sma,
                'signal': 'BUY' if short_sma > long_sma else 'SELL',
                'strength': abs(short_sma - long_sma) / current_price,
                'confidence': 0.6
            }
            signals.append(sma_signal)
        
        # MACD Signal
        if len(data) >= 26:
            exp1 = data['Close'].ewm(span=12).mean()
            exp2 = data['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            macd_signal = {
                'indicator': 'MACD',
                'macd': current_macd,
                'signal_line': current_signal,
                'signal': 'BUY' if current_macd > current_signal else 'SELL',
                'strength': abs(current_macd - current_signal) / abs(current_signal) if current_signal != 0 else 0,
                'confidence': 0.65
            }
            signals.append(macd_signal)
        
        # Bollinger Bands Signal
        if len(data) >= 20:
            sma = data['Close'].rolling(window=20).mean().iloc[-1]
            std = data['Close'].rolling(window=20).std().iloc[-1]
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            current_price = data['Close'].iloc[-1]
            
            bb_signal = {
                'indicator': 'BOLLINGER_BANDS',
                'upper': upper_band,
                'lower': lower_band,
                'middle': sma,
                'signal': 'BUY' if current_price <= lower_band else 'SELL' if current_price >= upper_band else 'HOLD',
                'strength': abs(current_price - sma) / (upper_band - lower_band) if upper_band != lower_band else 0,
                'confidence': 0.7
            }
            signals.append(bb_signal)
        
        return signals
    
    async def _get_news_sentiment(self, symbol: str) -> NewsSentimentData:
        """Get news sentiment data for symbol"""
        # This would typically come from the news scanner service
        # For now, we'll simulate some sentiment data
        
        # Check cache first
        if symbol in self.news_cache:
            cached_data = self.news_cache[symbol]
            # Return cached data if it's recent (within last hour)
            if datetime.now() - cached_data.get('timestamp', datetime.now()) < timedelta(hours=1):
                return cached_data['data']
        
        # Simulate news sentiment data
        sentiment_data = NewsSentimentData(
            symbol=symbol,
            sentiment_score=0.1,  # Slightly positive
            impact_score=0.3,     # Medium impact
            event_count=2,        # 2 recent events
            recent_events=[
                {
                    'title': f'Positive news for {symbol}',
                    'sentiment': 0.2,
                    'impact': 0.4,
                    'timestamp': datetime.now() - timedelta(hours=2)
                }
            ]
        )
        
        # Cache the data
        self.news_cache[symbol] = {
            'data': sentiment_data,
            'timestamp': datetime.now()
        }
        
        return sentiment_data
    
    async def _generate_ai_enhanced_signal(self, 
                                         symbol: str,
                                         technical_signals: List[Dict[str, Any]],
                                         news_sentiment: NewsSentimentData,
                                         data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate AI-enhanced trading signal"""
        
        try:
            # Prepare market context
            market_context = {
                'current_price': data['Close'].iloc[-1],
                'volume': data['Volume'].iloc[-1] if 'Volume' in data.columns else 1000000,
                'price_change_24h': (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] if len(data) > 1 else 0,
                'volatility': data['Close'].rolling(window=20).std().iloc[-1] / data['Close'].iloc[-1] if len(data) >= 20 else 0
            }
            
            # Convert news sentiment to dict format
            news_dict = {
                'sentiment_score': news_sentiment.sentiment_score,
                'impact_score': news_sentiment.impact_score,
                'event_count': news_sentiment.event_count,
                'recent_events': news_sentiment.recent_events
            }
            
            # Generate AI signal
            signal = await self.ollama_service.generate_multi_factor_signal(
                symbol, technical_signals, news_dict, market_context
            )
            
            return signal
            
        except Exception as e:
            print(f"Error generating AI signal for {symbol}: {e}")
            # Fallback to weighted signal
            return await self._generate_weighted_signal(symbol, technical_signals, news_sentiment, data)
    
    async def _generate_weighted_signal(self, 
                                      symbol: str,
                                      technical_signals: List[Dict[str, Any]],
                                      news_sentiment: NewsSentimentData,
                                      data: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate weighted signal without AI enhancement"""
        
        # Calculate technical score
        technical_score = 0.0
        technical_confidence = 0.0
        
        for signal in technical_signals:
            if signal['signal'] == 'BUY':
                technical_score += signal['strength'] * signal['confidence']
            elif signal['signal'] == 'SELL':
                technical_score -= signal['strength'] * signal['confidence']
            technical_confidence += signal['confidence']
        
        if technical_signals:
            technical_score /= len(technical_signals)
            technical_confidence /= len(technical_signals)
        
        # Calculate news score
        news_score = news_sentiment.sentiment_score * news_sentiment.impact_score
        news_confidence = min(news_sentiment.impact_score, 0.8)
        
        # Combine scores
        combined_score = (technical_score * self.technical_weight + 
                         news_score * self.news_weight)
        
        combined_confidence = (technical_confidence * self.technical_weight + 
                              news_confidence * self.news_weight)
        
        # Generate signal
        if abs(combined_score) > self.sentiment_threshold:
            action = "BUY" if combined_score > 0 else "SELL"
            current_price = data['Close'].iloc[-1]
            
            return TradeSignal(
                symbol=symbol,
                action=action,
                quantity=self._calculate_quantity(current_price, combined_confidence),
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name,
                confidence=combined_confidence,
                metadata={
                    'technical_score': technical_score,
                    'news_score': news_score,
                    'combined_score': combined_score,
                    'technical_signals': technical_signals,
                    'news_sentiment': {
                        'sentiment_score': news_sentiment.sentiment_score,
                        'impact_score': news_sentiment.impact_score,
                        'event_count': news_sentiment.event_count
                    }
                }
            )
        
        return None
    
    def _calculate_quantity(self, price: float, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_quantity = 1000 / price  # $1000 base position
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1x based on confidence
        return base_quantity * confidence_multiplier 