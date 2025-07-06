# 📰 News Bot Guide

The News Bot is a sophisticated system that monitors financial news sources in real-time, analyzes headlines for market-moving events, and generates trading signals based on sentiment analysis and impact assessment.

## 🚀 Features

### **Real-time News Monitoring**
- Monitors multiple financial news sources simultaneously
- Extracts and analyzes headlines for market relevance
- Tracks company mentions and event types
- Avoids duplicate processing

### **Intelligent Event Classification**
- **Earnings Events**: Quarterly results, profit/loss reports, guidance
- **Mergers & Acquisitions**: Deals, buyouts, takeovers, IPOs
- **Regulatory Events**: FDA approvals, SEC investigations, lawsuits
- **Macro Economic**: Fed decisions, interest rates, economic data
- **Sector Specific**: Industry-specific news and trends
- **Geopolitical**: Trade wars, sanctions, political events

### **Sentiment Analysis**
- Positive keywords: "beat", "surge", "growth", "approval"
- Negative keywords: "miss", "fall", "investigation", "recall"
- Sentiment scoring from -1.0 (very negative) to +1.0 (very positive)

### **Impact Assessment**
- Event type weighting (earnings = high impact, general = low impact)
- Company size consideration (major companies = higher impact)
- Urgency detection ("breaking", "urgent", "alert")

### **Trading Signal Generation**
- Automatic signal generation for high-impact events
- Position sizing based on impact and confidence scores
- Integration with existing trading strategies

## 🛠️ Setup & Configuration

### **1. Install Dependencies**
```bash
# Install required packages
pip install aiohttp loguru

# Or use the Makefile
make install
```

### **2. Configure News Sources**
The news bot monitors these sources by default:
- **Reuters**: https://www.reuters.com/markets/
- **Bloomberg**: https://www.bloomberg.com/markets
- **CNBC**: https://www.cnbc.com/markets/
- **Yahoo Finance**: https://finance.yahoo.com/news/
- **MarketWatch**: https://www.marketwatch.com/newsview

### **3. Start the News Bot**
```bash
# Start the API server (includes news bot)
make run-api

# Or start in Docker
make docker-run-api
```

## 📊 API Endpoints

### **News Scanner Control**
```bash
# Check scanner status
curl http://localhost:8000/news/scanner/status

# Start the news scanner
curl -X POST http://localhost:8000/news/scanner/start

# Stop the news scanner
curl -X POST http://localhost:8000/news/scanner/stop

# Trigger manual scan
curl -X POST http://localhost:8000/news/scan/trigger
```

### **News Data Access**
```bash
# Get recent news events
curl http://localhost:8000/news/events?limit=10

# Get events for specific symbol
curl http://localhost:8000/news/events/AAPL

# Get sentiment analysis
curl http://localhost:8000/news/sentiment/AAPL

# Get configured news sources
curl http://localhost:8000/news/sources

# Get event keywords
curl http://localhost:8000/news/keywords

# Get company mappings
curl http://localhost:8000/news/companies
```

## 🎯 Usage Examples

### **1. Run the News Bot Demo**
```bash
make run-news-bot
```

This will:
- Start the news scanner
- Show configured sources and keywords
- Display recent news events
- Show sentiment analysis for major stocks
- Demonstrate signal generation

### **2. Monitor Specific Companies**
```bash
# Get news for Apple
curl http://localhost:8000/news/events/AAPL

# Get sentiment for Tesla
curl http://localhost:8000/news/sentiment/TSLA
```

### **3. Custom News Scanning**
```python
import asyncio
from src.services.news.news_scanner import NewsScanner
from src.utils.config import Config

async def custom_news_scan():
    config = Config()
    scanner = NewsScanner(config)
    
    # Start scanner
    await scanner.start()
    
    # Wait for some events
    await asyncio.sleep(60)
    
    # Stop scanner
    await scanner.stop()

# Run custom scan
asyncio.run(custom_news_scan())
```

## 🔧 Configuration Options

### **News Scanner Settings**
```python
# In your config file
NEWS_SCAN_INTERVAL = 300  # Scan every 5 minutes
MIN_IMPACT_SCORE = 0.5    # Minimum impact to generate signal
MIN_CONFIDENCE = 0.6      # Minimum confidence to generate signal
```

### **Custom News Sources**
```python
# Add custom news sources
scanner.news_sources.update({
    "custom_source": "https://your-news-source.com",
    "financial_times": "https://www.ft.com/markets"
})
```

### **Custom Event Keywords**
```python
# Add custom event types
scanner.event_keywords["crypto"] = [
    "bitcoin", "ethereum", "blockchain", "cryptocurrency",
    "defi", "nft", "mining", "wallet"
]
```

### **Custom Company Mappings**
```python
# Add custom company mappings
scanner.company_symbols.update({
    "spacex": "SPACEX",  # If SpaceX goes public
    "starlink": "STARLINK"
})
```

## 📈 Signal Generation Logic

### **Event Filtering**
1. **Market Relevance**: Must contain event keywords or company names
2. **Impact Threshold**: Impact score must be ≥ 0.5
3. **Confidence Threshold**: Confidence score must be ≥ 0.6
4. **Symbol Presence**: Must affect at least one stock symbol

### **Signal Generation**
```python
# Positive sentiment (> 0.3) → BUY signal
# Negative sentiment (< -0.3) → SELL signal
# Neutral sentiment → No signal

# Position sizing
base_quantity = 1000  # $1000 base position
quantity = base_quantity * impact_score * confidence
```

### **Example Signal**
```json
{
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 8.5,
  "price": 150.00,
  "strategy": "news_scanner",
  "confidence": 0.85,
  "metadata": {
    "news_event": {
      "title": "Apple Reports Strong Q4 Earnings, Beats Estimates",
      "source": "reuters",
      "event_type": "earnings",
      "sentiment_score": 0.8,
      "impact_score": 0.9
    },
    "signal_type": "news_driven"
  }
}
```

## 🔍 Event Types & Keywords

### **Earnings Events**
- Keywords: earnings, quarterly results, profit, revenue, beat, miss
- Impact: High (0.8)
- Examples: "Apple beats Q4 estimates", "Tesla misses revenue targets"

### **Mergers & Acquisitions**
- Keywords: merger, acquisition, buyout, takeover, deal, IPO
- Impact: Very High (0.9)
- Examples: "Microsoft acquires gaming studio", "Company announces IPO"

### **Regulatory Events**
- Keywords: regulation, FDA, SEC, investigation, lawsuit, approval
- Impact: High (0.7)
- Examples: "FDA approves new drug", "SEC investigates company"

### **Macro Economic**
- Keywords: Fed, interest rates, inflation, GDP, unemployment
- Impact: Medium (0.6)
- Examples: "Fed raises interest rates", "Inflation data released"

### **Sector Specific**
- Keywords: tech, healthcare, finance, oil, energy, biotech
- Impact: Medium (0.5)
- Examples: "Tech sector rally", "Oil prices surge"

### **Geopolitical**
- Keywords: trade war, tariffs, sanctions, election, conflict
- Impact: High (0.8)
- Examples: "Trade war escalates", "New sanctions announced"

## 🏢 Supported Companies

The news bot recognizes these major companies and their symbols:

### **Technology**
- Apple (AAPL), Microsoft (MSFT), Google (GOOGL)
- Amazon (AMZN), Tesla (TSLA), Nvidia (NVDA)
- Meta (META), Netflix (NFLX), Salesforce (CRM)

### **Healthcare**
- Johnson & Johnson (JNJ), Pfizer (PFE)
- Moderna (MRNA), BioNTech (BNTX)
- UnitedHealth (UNH), Anthem (ANTM)

### **Finance**
- JPMorgan (JPM), Bank of America (BAC)
- Wells Fargo (WFC), Goldman Sachs (GS)
- Morgan Stanley (MS), Berkshire Hathaway (BRK.A)

### **Energy**
- Exxon (XOM), Chevron (CVX), ConocoPhillips (COP)

### **Consumer**
- Coca-Cola (KO), Pepsi (PEP), Walmart (WMT)
- Target (TGT), Home Depot (HD), Disney (DIS)

## 🚨 Safety Features

### **Duplicate Prevention**
- Tracks processed headlines to avoid duplicate signals
- Uses hash-based deduplication

### **Rate Limiting**
- Configurable scan intervals (default: 5 minutes)
- Respects website rate limits

### **Error Handling**
- Graceful handling of network errors
- Automatic retry logic
- Detailed error logging

### **Signal Validation**
- Multiple thresholds for signal generation
- Confidence scoring prevents low-quality signals
- Impact assessment filters out irrelevant news

## 📊 Monitoring & Analytics

### **Scanner Status**
```bash
curl http://localhost:8000/news/scanner/status
```

Returns:
```json
{
  "is_running": true,
  "sources": ["reuters", "bloomberg", "cnbc", "yahoo_finance", "marketwatch"],
  "event_types": ["earnings", "mergers_acquisitions", "regulatory", "macro_economic"],
  "processed_news_count": 1250
}
```

### **Performance Metrics**
- Events processed per hour
- Signal generation rate
- Sentiment distribution
- Impact score distribution
- Error rates and retry counts

## 🔮 Future Enhancements

### **Planned Features**
1. **Machine Learning Sentiment**: Replace keyword-based with ML models
2. **Real-time Price Integration**: Use actual stock prices for position sizing
3. **News API Integration**: Use official APIs instead of web scraping
4. **Social Media Monitoring**: Include Twitter, Reddit sentiment
5. **Options Trading**: Generate options strategies based on news
6. **Multi-language Support**: Monitor international news sources
7. **Advanced Filtering**: Custom filters for specific event types
8. **Backtesting**: Historical news analysis and strategy testing

### **Advanced Configuration**
```python
# Future configuration options
NEWS_ML_MODEL_PATH = "models/sentiment_analyzer.pkl"
SOCIAL_MEDIA_SOURCES = ["twitter", "reddit", "stocktwits"]
INTERNATIONAL_SOURCES = ["ft", "wsj", "nikkei"]
OPTIONS_STRATEGY_ENABLED = True
BACKTESTING_MODE = False
```

## 🛠️ Troubleshooting

### **Common Issues**

1. **Scanner Not Starting**
   ```bash
   # Check if API server is running
   curl http://localhost:8000/health
   
   # Check scanner status
   curl http://localhost:8000/news/scanner/status
   ```

2. **No Events Found**
   - Verify news sources are accessible
   - Check network connectivity
   - Review event keywords configuration

3. **High Error Rate**
   - Check rate limiting settings
   - Verify website structure hasn't changed
   - Review error logs

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
python news_bot_demo.py --debug
```

## 📚 Additional Resources

- [News Bot API Documentation](http://localhost:8000/docs)
- [Strategy Manager Guide](./README.md#strategy-management)
- [Trading Engine Documentation](./README.md#trading-engine)
- [Event Replay Guide](./EVENT_REPLAY_GUIDE.md)

---

**Note**: The news bot is designed for educational and research purposes. Always test thoroughly in paper trading mode before using with real money. News-based trading can be risky due to market volatility and the speed at which news spreads. 