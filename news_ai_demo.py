#!/usr/bin/env python3
"""
News + AI Enhanced Trading Demo
Demonstrates the integration of news sentiment analysis with AI-powered trading signals
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.services.news.news_scanner import NewsScanner, NewsEvent
from src.services.ai.ollama_service import OllamaService, AIAnalysis
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.utils.config import Config


class NewsAIDemo:
    """Demo class for news + AI enhanced trading"""
    
    def __init__(self):
        self.config = Config()
        self.news_scanner = NewsScanner(self.config)
        self.ollama_service = None
        self.news_strategy = NewsEnhancedStrategy()
        
    async def setup(self):
        """Setup the demo environment"""
        print("🚀 Setting up News + AI Enhanced Trading Demo")
        print("=" * 60)
        
        # Initialize Ollama service
        try:
            self.ollama_service = OllamaService()
            await self.ollama_service.__aenter__()
            print("✅ Ollama AI service initialized")
        except Exception as e:
            print(f"⚠️  Ollama service unavailable: {e}")
            print("   Continuing with simulated AI responses")
        
        # Initialize news strategy
        if self.ollama_service:
            await self.news_strategy.initialize()
            print("✅ News-enhanced strategy initialized with AI")
        else:
            print("✅ News-enhanced strategy initialized (AI disabled)")
        
        print()
    
    async def demo_news_scanning(self):
        """Demo news scanning and sentiment analysis"""
        print("📰 Demo: News Scanning and Sentiment Analysis")
        print("-" * 50)
        
        # Simulate news events
        simulated_news = [
            {
                "title": "Apple Reports Strong Q4 Earnings, Beats Expectations",
                "content": "Apple Inc. reported quarterly earnings that exceeded analyst expectations...",
                "source": "Reuters",
                "url": "https://reuters.com/apple-earnings",
                "published_at": datetime.now() - timedelta(hours=2),
                "sentiment_score": 0.8,
                "impact_score": 0.9,
                "affected_symbols": ["AAPL"],
                "event_type": "earnings",
                "confidence": 0.9,
                "metadata": {}
            },
            {
                "title": "Federal Reserve Signals Potential Rate Hike",
                "content": "The Federal Reserve indicated it may raise interest rates...",
                "source": "Bloomberg",
                "url": "https://bloomberg.com/fed-rate-hike",
                "published_at": datetime.now() - timedelta(hours=1),
                "sentiment_score": -0.3,
                "impact_score": 0.8,
                "affected_symbols": ["JPM", "BAC", "WFC"],
                "event_type": "macro_economic",
                "confidence": 0.8,
                "metadata": {}
            },
            {
                "title": "Tesla Announces New Battery Technology Breakthrough",
                "content": "Tesla revealed a new battery technology that could...",
                "source": "CNBC",
                "url": "https://cnbc.com/tesla-battery",
                "published_at": datetime.now() - timedelta(minutes=30),
                "sentiment_score": 0.7,
                "impact_score": 0.7,
                "affected_symbols": ["TSLA"],
                "event_type": "sector_specific",
                "confidence": 0.7,
                "metadata": {}
            }
        ]
        
        print(f"📊 Found {len(simulated_news)} news events")
        
        # Enhance news with AI if available
        if self.ollama_service:
            print("\n🤖 Enhancing news sentiment with AI...")
            enhanced_news = []
            
            for news in simulated_news:
                try:
                    enhanced = await self.ollama_service.enhance_news_sentiment(news)
                    enhanced_news.append(enhanced)
                    print(f"   📈 {news['title'][:50]}...")
                    print(f"      Original sentiment: {news['sentiment_score']:.2f}")
                    print(f"      Enhanced sentiment: {enhanced.get('enhanced_sentiment', 'N/A')}")
                except Exception as e:
                    print(f"   ⚠️  AI enhancement failed: {e}")
                    enhanced_news.append(news)
            
            simulated_news = enhanced_news
        
        # Display news summary
        print("\n📋 News Summary:")
        for i, news in enumerate(simulated_news, 1):
            print(f"   {i}. {news['title']}")
            print(f"      Sentiment: {news.get('enhanced_sentiment', news['sentiment_score']):.2f}")
            print(f"      Impact: {news['impact_score']:.2f}")
            print(f"      Symbols: {', '.join(news['affected_symbols'])}")
            print()
        
        return simulated_news
    
    async def demo_market_analysis(self, news_events: List[Dict[str, Any]]):
        """Demo AI-powered market analysis"""
        print("🧠 Demo: AI-Powered Market Analysis")
        print("-" * 50)
        
        if not self.ollama_service:
            print("⚠️  Ollama service unavailable, using simulated analysis")
            return self._simulate_market_analysis()
        
        # Simulate technical signals
        technical_signals = [
            {
                "indicator": "RSI",
                "value": 65.2,
                "signal": "HOLD",
                "strength": 0.3,
                "confidence": 0.7
            },
            {
                "indicator": "MACD",
                "macd": 0.15,
                "signal_line": 0.12,
                "signal": "BUY",
                "strength": 0.6,
                "confidence": 0.65
            },
            {
                "indicator": "BOLLINGER_BANDS",
                "upper": 150.5,
                "lower": 145.2,
                "middle": 147.8,
                "signal": "HOLD",
                "strength": 0.2,
                "confidence": 0.7
            }
        ]
        
        # Simulate market data
        market_data = {
            "current_price": 148.25,
            "volume": 2500000,
            "price_change_24h": 0.025,
            "volatility": 0.018,
            "market_cap": 2350000000000,
            "pe_ratio": 28.5
        }
        
        print("📊 Analyzing market conditions...")
        print(f"   Technical signals: {len(technical_signals)}")
        print(f"   News events: {len(news_events)}")
        print(f"   Current market data: ${market_data['current_price']:.2f}")
        
        try:
            analysis = await self.ollama_service.analyze_market_sentiment(
                news_events, technical_signals, market_data
            )
            
            print("\n🤖 AI Market Analysis Results:")
            print(f"   Overall Sentiment: {analysis.sentiment_score:.2f}")
            print(f"   Confidence: {analysis.confidence:.2f}")
            print(f"   Risk Assessment: {analysis.risk_assessment}")
            print(f"   Market Impact: {analysis.market_impact}")
            print(f"   Recommended Action: {analysis.recommended_action}")
            print(f"   Key Factors: {', '.join(analysis.metadata.get('key_factors', []))}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return self._simulate_market_analysis()
    
    def _simulate_market_analysis(self) -> AIAnalysis:
        """Simulate market analysis when AI is unavailable"""
        return AIAnalysis(
            sentiment_score=0.2,
            confidence=0.6,
            reasoning="Simulated analysis based on technical indicators and news sentiment",
            risk_assessment="medium",
            market_impact="slightly_bullish",
            recommended_action="Consider selective buying with proper risk management",
            metadata={
                'key_factors': ['positive earnings', 'technical momentum', 'moderate volatility'],
                'market_volatility': 'medium'
            }
        )
    
    async def demo_trading_signals(self, symbols: List[str] = ["AAPL", "TSLA", "JPM"]):
        """Demo multi-factor trading signal generation"""
        print("\n📈 Demo: Multi-Factor Trading Signal Generation")
        print("-" * 50)
        
        for symbol in symbols:
            print(f"\n🎯 Generating signal for {symbol}...")
            
            # Simulate market data for the symbol
            import pandas as pd
            import numpy as np
            
            # Create mock price data
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            np.random.seed(hash(symbol) % 1000)
            
            start_price = np.random.uniform(50, 200)
            prices = [start_price]
            
            for i in range(1, len(dates)):
                daily_return = np.random.normal(0.0005, 0.02)
                new_price = prices[-1] * (1 + daily_return)
                prices.append(max(new_price, 1.0))
            
            # Create DataFrame with technical indicators
            df = pd.DataFrame({
                'Close': prices,
                'Open': prices,
                'High': prices,
                'Low': prices,
                'Volume': np.random.uniform(1000000, 5000000, len(prices))
            })
            
            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Generate signal
            try:
                signal = await self.news_strategy.generate_signal(symbol, df)
                
                if signal:
                    print(f"   ✅ Signal Generated: {signal.action}")
                    print(f"      Confidence: {signal.confidence:.2f}")
                    print(f"      Quantity: {signal.quantity:.2f}")
                    print(f"      Price: ${signal.price:.2f}")
                    
                    if 'reasoning' in signal.metadata:
                        print(f"      Reasoning: {signal.metadata['reasoning']}")
                    
                    if 'technical_score' in signal.metadata:
                        print(f"      Technical Score: {signal.metadata['technical_score']:.2f}")
                        print(f"      News Score: {signal.metadata['news_score']:.2f}")
                        print(f"      Combined Score: {signal.metadata['combined_score']:.2f}")
                else:
                    print(f"   ⏸️  No signal generated (insufficient confidence)")
                    
            except Exception as e:
                print(f"   ❌ Error generating signal: {e}")
    
    async def run_full_demo(self):
        """Run the complete demo"""
        await self.setup()
        
        # Demo 1: News scanning
        news_events = await self.demo_news_scanning()
        
        # Demo 2: Market analysis
        market_analysis = await self.demo_market_analysis(news_events)
        
        # Demo 3: Trading signals
        await self.demo_trading_signals()
        
        print("\n🎉 Demo Complete!")
        print("=" * 60)
        print("📋 Summary:")
        print("   • News sentiment analysis with AI enhancement")
        print("   • Multi-factor market analysis")
        print("   • AI-powered trading signal generation")
        print("   • Integration of technical and fundamental analysis")
        
        if self.ollama_service:
            await self.ollama_service.__aexit__(None, None, None)


async def main():
    """Main demo function"""
    demo = NewsAIDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main()) 