#!/usr/bin/env python3
"""
Demo: Historical News for Backtesting
Shows how to fetch historical news from Polygon.io and use it in backtesting
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add src to path
sys.path.append('src')

from src.services.news.polygon_news_service import PolygonNewsService
from src.services.database.news_data_service import NewsDataService
from src.services.database.market_data_service import MarketDataService
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
from src.utils.config import get_config
from src.utils.trading_config import get_symbols

def demo_fetch_news():
    """Demo fetching news from Polygon.io"""
    
    print("📰 DEMO: Fetching Historical News from Polygon.io")
    print("=" * 60)
    
    # Configuration
    symbols = ['AAPL', 'TSLA', 'MSFT']  # Small set for demo
    start_date = "2024-01-01"
    end_date = "2024-01-31"  # One month for demo
    
    print(f"📊 Demo Configuration:")
    print(f"   📅 Date Range: {start_date} to {end_date}")
    print(f"   📈 Symbols: {', '.join(symbols)}")
    print(f"   🎯 Provider: Polygon.io News API")
    print()
    
    try:
        # Initialize services
        news_service = PolygonNewsService()
        db_service = NewsDataService()
        
        print("✅ Services initialized successfully")
        
        # Fetch news for each symbol
        total_articles = 0
        
        for symbol in symbols:
            print(f"\n📰 Fetching news for {symbol}...")
            
            articles = news_service.get_historical_news(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=100  # Limit for demo
            )
            
            if articles:
                print(f"   ✅ Found {len(articles)} articles")
                
                # Show sample articles
                for i, article in enumerate(articles[:3]):  # Show first 3
                    print(f"   📄 {i+1}. {article.title[:60]}...")
                    print(f"      📅 {article.published_at.strftime('%Y-%m-%d %H:%M')}")
                    print(f"      📰 {article.source}")
                    print(f"      🔗 {article.url}")
                    print()
                
                # Store in database
                store_results = db_service.store_news_batch(articles)
                total_articles += store_results['stored']
                
                print(f"   💾 Stored {store_results['stored']} articles in database")
                
            else:
                print(f"   ❌ No articles found for {symbol}")
        
        print(f"\n📊 Demo Results:")
        print(f"   📰 Total articles stored: {total_articles}")
        print(f"   🎯 Successfully processed {len(symbols)} symbols")
        
        # Show database statistics
        print(f"\n🔍 Database Statistics:")
        cache_status = db_service.get_cache_status()
        for entry in cache_status:
            print(f"   {entry['symbol']}: {entry['total_articles']} articles")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def demo_news_playback():
    """Demo news playback for backtesting"""
    
    print("\n🎬 DEMO: News Playback for Backtesting")
    print("=" * 60)
    
    try:
        db_service = NewsDataService()
        
        # Get news for a specific date range
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        symbols = ['AAPL', 'TSLA']
        
        print(f"📊 Playback Configuration:")
        print(f"   📅 Date Range: {start_date.date()} to {end_date.date()}")
        print(f"   📈 Symbols: {', '.join(symbols)}")
        print()
        
        # Get news articles from database
        news_articles = list(db_service.get_news_for_backtest(symbols, start_date, end_date))
        
        if not news_articles:
            print("❌ No news articles found for playback demo")
            return
        
        print(f"✅ Found {len(news_articles)} news articles for playback")
        
        # Simulate backtest timeline
        print(f"\n🎬 Simulating backtest timeline...")
        
        # Sort articles by date
        news_articles.sort(key=lambda x: x.published_at)
        
        # Simulate processing each day
        current_date = start_date
        while current_date <= end_date:
            # Get news for current date
            day_news = [
                article for article in news_articles 
                if article.published_at.date() == current_date.date()
            ]
            
            if day_news:
                print(f"\n📅 {current_date.strftime('%Y-%m-%d')}: {len(day_news)} news events")
                
                for article in day_news:
                    print(f"   📰 {article.title[:50]}...")
                    print(f"      🏷️  {', '.join(article.affected_symbols or [])}")
                    print(f"      📊 Sentiment: {article.sentiment_score or 'N/A'}")
                    print(f"      💥 Impact: {article.impact_score or 'N/A'}")
            
            current_date += timedelta(days=1)
        
        # Show sentiment analysis
        print(f"\n📊 Sentiment Analysis Demo:")
        for symbol in symbols:
            stats = db_service.get_news_statistics(symbol, start_date, end_date)
            print(f"   {symbol}: {stats['total_articles']} articles, avg sentiment: {stats['avg_sentiment']:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def demo_news_integration():
    """Demo how to integrate news into a trading strategy"""
    
    print("\n🤖 DEMO: News Integration in Trading Strategy")
    print("=" * 60)
    
    try:
        db_service = NewsDataService()
        
        # Simulate a trading strategy that uses news
        symbol = 'AAPL'
        current_date = datetime(2024, 1, 15)  # Mid-month
        
        print(f"📈 Simulating trading strategy for {symbol} on {current_date.strftime('%Y-%m-%d')}")
        print()
        
        # Get recent news (last 7 days)
        start_date = current_date - timedelta(days=7)
        end_date = current_date
        
        recent_news = db_service.get_news_by_date_range(start_date, end_date, [symbol])
        
        if recent_news:
            print(f"📰 Recent news analysis:")
            
            # Calculate sentiment
            sentiments = [article.sentiment_score for article in recent_news if article.sentiment_score is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            print(f"   📊 Average sentiment: {avg_sentiment:.2f}")
            print(f"   📰 Total articles: {len(recent_news)}")
            
            # Show key news events
            print(f"\n🔍 Key news events:")
            for article in recent_news[:3]:
                sentiment_label = "🟢 Positive" if (article.sentiment_score or 0) > 0 else "🔴 Negative" if (article.sentiment_score or 0) < 0 else "🟡 Neutral"
                print(f"   {sentiment_label} {article.title[:40]}...")
            
            # Simulate trading decision
            print(f"\n🤖 Trading Decision:")
            if avg_sentiment > 0.3:
                print(f"   🟢 BUY signal - Positive news sentiment ({avg_sentiment:.2f})")
            elif avg_sentiment < -0.3:
                print(f"   🔴 SELL signal - Negative news sentiment ({avg_sentiment:.2f})")
            else:
                print(f"   🟡 HOLD signal - Neutral news sentiment ({avg_sentiment:.2f})")
        
        else:
            print(f"   ❌ No recent news found for {symbol}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def demo_news_backtest():
    """Demo news-enhanced backtest with real market data"""
    config = get_config()
    
    # Initialize services
    market_data_service = MarketDataService(config.database_url)
    
    # Use centralized symbol list (small set for demo)
    symbols = get_symbols()[:3]  # Limit for demo
    
    # Calculate date range (6 months ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"📊 Running news-enhanced backtest demo for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # ... existing code ...


if __name__ == "__main__":
    print("🚀 Historical News Backtesting Demo")
    print("=" * 60)
    
    # Check if Polygon API key is available
    if not os.getenv('POLYGON_API_KEY'):
        print("❌ POLYGON_API_KEY environment variable not set")
        print("   Please set your Polygon.io API key to run this demo")
        print("   export POLYGON_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    # Run demos
    demo_fetch_news()
    demo_news_playback()
    demo_news_integration()
    
    print(f"\n✅ Demo completed!")
    print(f"🎉 You now have historical news data for backtesting!") 