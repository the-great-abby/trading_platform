# 📰 Historical News for Backtesting Guide

This guide shows you how to fetch historical news from Polygon.io and integrate it into your backtesting system.

## 🎯 Overview

The historical news system allows you to:
- **Fetch historical news** from Polygon.io for any stock symbols
- **Store news data** in your PostgreSQL database
- **Play back news events** during backtesting in chronological order
- **Integrate news sentiment** into your trading strategies

## 🚀 Quick Start

### 1. Set Up Your Polygon API Key

```bash
export POLYGON_API_KEY='your_polygon_api_key_here'
```

### 2. Fetch Historical News

```bash
# Fetch news for major stocks (2023-2024)
python fetch_polygon_news.py

# Show news database statistics
python fetch_polygon_news.py --stats
```

### 3. Run the Demo

```bash
# Run the complete demo
python demo_news_backtest.py
```

## 📊 System Components

### 1. **Polygon News Service** (`src/services/news/polygon_news_service.py`)
- Fetches historical news from Polygon.io API
- Handles rate limiting and error recovery
- Parses news articles into structured data

### 2. **News Database Service** (`src/services/database/news_data_service.py`)
- Stores news articles in PostgreSQL
- Provides query methods for backtesting
- Manages news cache metadata

### 3. **News Playback Service** (`src/services/backtest/news_playback_service.py`)
- Provides news events during backtesting
- Maintains chronological order
- Calculates sentiment and impact scores

## 🔧 Usage Examples

### Fetching News for Specific Symbols

```python
from src.services.news.polygon_news_service import PolygonNewsService
from src.services.database.news_data_service import NewsDataService

# Initialize services
news_service = PolygonNewsService()
db_service = NewsDataService()

# Fetch news for AAPL and TSLA
symbols = ['AAPL', 'TSLA']
start_date = "2024-01-01"
end_date = "2024-01-31"

for symbol in symbols:
    articles = news_service.get_historical_news(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=1000
    )
    
    if articles:
        # Store in database
        results = db_service.store_news_batch(articles)
        print(f"Stored {results['stored']} articles for {symbol}")
```

### Using News in Backtesting

```python
from src.services.database.news_data_service import NewsDataService
from datetime import datetime, timedelta

db_service = NewsDataService()

# Get news for backtest period
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31)
symbols = ['AAPL', 'TSLA']

# Get all news articles for the period
news_articles = list(db_service.get_news_for_backtest(symbols, start_date, end_date))

# Sort by publication date
news_articles.sort(key=lambda x: x.published_at)

# Use in backtest loop
current_date = start_date
while current_date <= end_date:
    # Get news for current date
    day_news = [
        article for article in news_articles 
        if article.published_at.date() == current_date.date()
    ]
    
    # Process news events
    for article in day_news:
        print(f"News: {article.title}")
        print(f"Sentiment: {article.sentiment_score}")
        print(f"Impact: {article.impact_score}")
        
        # Make trading decisions based on news
        if article.sentiment_score and article.sentiment_score > 0.5:
            print("Positive news - consider BUY signal")
        elif article.sentiment_score and article.sentiment_score < -0.5:
            print("Negative news - consider SELL signal")
    
    current_date += timedelta(days=1)
```

### News Sentiment Analysis

```python
# Get sentiment analysis for a symbol
symbol = 'AAPL'
current_date = datetime(2024, 1, 15)
start_date = current_date - timedelta(days=7)

# Get recent news
recent_news = db_service.get_news_by_date_range(
    start_date, 
    current_date, 
    [symbol]
)

# Calculate average sentiment
sentiments = [
    article.sentiment_score 
    for article in recent_news 
    if article.sentiment_score is not None
]

if sentiments:
    avg_sentiment = sum(sentiments) / len(sentiments)
    print(f"Average sentiment for {symbol}: {avg_sentiment:.2f}")
    
    # Trading decision based on sentiment
    if avg_sentiment > 0.3:
        print("BUY signal - positive sentiment")
    elif avg_sentiment < -0.3:
        print("SELL signal - negative sentiment")
    else:
        print("HOLD signal - neutral sentiment")
```

## 📈 News Event Types

The system classifies news events into different types:

- **Earnings**: Quarterly results, profit/loss reports
- **Mergers & Acquisitions**: Deals, buyouts, takeovers
- **Regulatory**: FDA approvals, SEC investigations
- **Macro Economic**: Fed decisions, interest rates
- **Sector Specific**: Industry-specific news
- **Geopolitical**: Trade wars, sanctions, political events

## 🎯 Sentiment Analysis

News articles are analyzed for sentiment:

- **Positive keywords**: "beat", "surge", "growth", "approval"
- **Negative keywords**: "miss", "fall", "investigation", "recall"
- **Sentiment score**: -1.0 (very negative) to +1.0 (very positive)

## 💾 Database Schema

### Historical News Table
```sql
CREATE TABLE historical_news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    url TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    sentiment_score FLOAT,
    impact_score FLOAT,
    confidence_score FLOAT,
    event_type VARCHAR(50),
    affected_symbols JSON,
    metadata JSON,
    provider_id VARCHAR(100),
    ticker VARCHAR(10)
);
```

### News Cache Table
```sql
CREATE TABLE news_cache (
    symbol VARCHAR(10) NOT NULL,
    source VARCHAR(100) NOT NULL,
    earliest_date TIMESTAMP,
    latest_date TIMESTAMP,
    total_articles INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, source)
);
```

## 🔍 Monitoring and Statistics

### Check News Coverage
```python
# Get statistics for a symbol
stats = db_service.get_news_statistics('AAPL', start_date, end_date)
print(f"Total articles: {stats['total_articles']}")
print(f"Average sentiment: {stats['avg_sentiment']:.2f}")
print(f"Sources: {', '.join(stats['sources'])}")
```

### Cache Status
```python
# Check cache status
cache_status = db_service.get_cache_status()
for entry in cache_status:
    print(f"{entry['symbol']}: {entry['total_articles']} articles")
```

## 🚨 Best Practices

### 1. **Rate Limiting**
- Polygon.io has rate limits (varies by plan)
- The service includes automatic rate limiting
- Wait between requests to avoid hitting limits

### 2. **Data Freshness**
- News data is historical and doesn't change
- Cache metadata helps track what you have
- Re-run fetches to get new articles

### 3. **Memory Management**
- Use streaming for large date ranges
- Process news in batches
- Clean up old news periodically

### 4. **Backtesting Integration**
- Only use news available at each timestamp
- Avoid lookahead bias
- Consider news delay/latency

## 🛠️ Troubleshooting

### Common Issues

1. **No news found**
   - Check if symbols are valid
   - Verify date range
   - Ensure Polygon API key is valid

2. **Rate limiting**
   - Wait longer between requests
   - Check your Polygon plan limits
   - Use smaller date ranges

3. **Database errors**
   - Check database connection
   - Verify table schema
   - Check for duplicate articles

### Debug Commands

```bash
# Check news statistics
python fetch_polygon_news.py --stats

# Test Polygon API connection
python -c "
from src.services.news.polygon_news_service import PolygonNewsService
service = PolygonNewsService()
articles = service.get_historical_news('AAPL', '2024-01-01', '2024-01-02', limit=5)
print(f'Found {len(articles)} articles')
"
```

## 📚 Next Steps

1. **Integrate with your backtest engine**
2. **Add news-based trading strategies**
3. **Implement sentiment analysis**
4. **Add news impact scoring**
5. **Create news-driven alerts**

## 🎉 Success!

You now have a complete historical news system for backtesting! The news data will help you create more realistic and comprehensive backtests that include the impact of real-world events on stock prices. 