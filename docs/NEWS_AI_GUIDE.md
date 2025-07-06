# News + AI Enhanced Trading System Guide

## Overview

This enhanced trading system combines **news sentiment analysis** with **AI-powered market analysis** using Ollama to create sophisticated multi-factor trading signals. The system integrates technical indicators, news sentiment, and AI reasoning to generate more informed trading decisions.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News Scanner  │    │  Ollama AI      │    │  Trading        │
│                 │    │  Service        │    │  Strategies     │
│ • Reuters       │───▶│                 │───▶│                 │
│ • Bloomberg     │    │ • Sentiment     │    │ • RSI           │
│ • CNBC          │    │   Enhancement   │    │ • MACD          │
│ • Yahoo Finance │    │ • Market        │    │ • Bollinger     │
│ • MarketWatch   │    │   Analysis      │    │ • News Enhanced │
└─────────────────┘    │ • Signal Gen    │    └─────────────────┘
                       └─────────────────┘
```

## 🚀 Key Features

### 1. **News Sentiment Analysis**
- **Real-time monitoring** of 5 major financial news sources
- **Event classification** (earnings, M&A, regulatory, macroeconomic, etc.)
- **Sentiment scoring** (-1.0 to 1.0) with impact assessment
- **Company symbol mapping** for 100+ major companies

### 2. **AI Enhancement with Ollama**
- **Sentiment enhancement** using AI analysis
- **Market context analysis** combining technical and fundamental factors
- **Multi-factor signal generation** with reasoning
- **Risk assessment** and position sizing recommendations

### 3. **News-Enhanced Trading Strategy**
- **Combines technical indicators** (RSI, MACD, SMA, Bollinger Bands)
- **Integrates news sentiment** with configurable weights
- **AI-powered decision making** when Ollama is available
- **Fallback to weighted analysis** when AI is unavailable

## 📦 Components

### 1. **Ollama Service** (`src/services/ai/ollama_service.py`)
```python
class OllamaService:
    async def enhance_news_sentiment(self, news_event: Dict) -> Dict
    async def analyze_market_sentiment(self, news_events, technical_signals, market_data) -> AIAnalysis
    async def generate_multi_factor_signal(self, symbol, technical_signals, news_sentiment, market_context) -> TradeSignal
```

### 2. **News-Enhanced Strategy** (`src/strategies/news_enhanced_strategy.py`)
```python
class NewsEnhancedStrategy(BaseStrategy):
    async def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[TradeSignal]
    async def _get_technical_signals(self, symbol: str, data: pd.DataFrame) -> List[Dict]
    async def _get_news_sentiment(self, symbol: str) -> NewsSentimentData
```

### 3. **Demo Application** (`news_ai_demo.py`)
- Complete demonstration of the integrated system
- Simulated news events and market data
- AI enhancement showcase
- Multi-factor signal generation

## 🛠️ Setup Instructions

### 1. **Start the Enhanced System**
```bash
# Start all services including Ollama
make docker-up

# Check Ollama status
make docker-ollama-status

# Setup Ollama models (first time only)
make docker-ollama-setup
```

### 2. **Run the Demo**
```bash
# Run the complete news + AI demo
make docker-news-ai-demo
```

### 3. **Backtest with News-Enhanced Strategy**
```bash
# Add the news-enhanced strategy to your backtest
# Edit run_backtest.py to include "news_enhanced" in strategies list
make docker-backtest
```

## 📊 How It Works

### 1. **News Scanning Process**
```
News Sources → Event Detection → Sentiment Analysis → AI Enhancement → Trading Signals
```

### 2. **AI Enhancement Flow**
```
Raw News Event → AI Analysis → Enhanced Sentiment → Market Context → Multi-Factor Signal
```

### 3. **Signal Generation Process**
```
Technical Indicators + News Sentiment + Market Data → AI Analysis → Trading Decision
```

## 🎯 Example Usage

### **Scenario: Apple Earnings Report**

1. **News Detection**
   ```
   Title: "Apple Reports Strong Q4 Earnings, Beats Expectations"
   Sentiment: 0.8 (Positive)
   Impact: 0.9 (High)
   Symbols: ["AAPL"]
   ```

2. **AI Enhancement**
   ```
   Enhanced Sentiment: 0.85
   Market Impact: "bullish"
   Risk Level: "medium"
   Reasoning: "Strong earnings beat with positive guidance"
   ```

3. **Multi-Factor Analysis**
   ```
   Technical Score: 0.6 (RSI oversold, MACD bullish)
   News Score: 0.77 (0.85 * 0.9)
   Combined Score: 0.67
   AI Recommendation: "BUY with 75% confidence"
   ```

4. **Trading Signal**
   ```
   Action: BUY
   Symbol: AAPL
   Quantity: 6.75 shares
   Confidence: 0.75
   Stop Loss: 2%
   Take Profit: 10%
   ```

## 🔧 Configuration

### **Strategy Parameters**
```python
NewsEnhancedStrategy(
    technical_weight=0.6,      # Weight for technical indicators
    news_weight=0.4,           # Weight for news sentiment
    sentiment_threshold=0.3    # Minimum signal strength
)
```

### **Ollama Configuration**
```python
OllamaService(
    base_url="http://ollama:11434",  # Ollama service URL
    model="llama2"                   # AI model to use
)
```

### **News Sources**
- Reuters: `https://www.reuters.com/markets/`
- Bloomberg: `https://www.bloomberg.com/markets`
- CNBC: `https://www.cnbc.com/markets/`
- Yahoo Finance: `https://finance.yahoo.com/news/`
- MarketWatch: `https://www.marketwatch.com/newsview`

## 📈 Performance Benefits

### **Traditional vs Enhanced**
| Aspect | Traditional | News + AI Enhanced |
|--------|-------------|-------------------|
| Signal Sources | Technical only | Technical + News + AI |
| Decision Making | Rule-based | AI-reasoned |
| Risk Assessment | Basic | AI-enhanced |
| Market Context | Limited | Comprehensive |
| Adaptability | Static | Dynamic |

### **Expected Improvements**
- **Higher accuracy** through multi-factor analysis
- **Better risk management** with AI assessment
- **Faster response** to market-moving news
- **Reduced false signals** through sentiment validation

## 🚨 Risk Considerations

### **AI Dependencies**
- **Ollama availability** affects AI enhancement
- **Model quality** impacts decision accuracy
- **Response time** may affect real-time trading

### **News Reliability**
- **Source credibility** varies
- **Sentiment accuracy** depends on analysis quality
- **Market reaction** may differ from sentiment

### **System Complexity**
- **More components** to maintain
- **Higher computational** requirements
- **Additional failure** points

## 🔍 Monitoring and Debugging

### **Check System Status**
```bash
# Check Ollama service
make docker-ollama-status

# Check news scanner logs
docker-compose -f docker-compose.dev.yml logs news-scanner

# Monitor trading signals
docker-compose -f docker-compose.dev.yml logs trading-bot-dev
```

### **Debug AI Responses**
```python
# Enable debug logging
import logging
logging.getLogger('src.services.ai.ollama_service').setLevel(logging.DEBUG)
```

### **Test Individual Components**
```python
# Test news enhancement
from src.services.ai.ollama_service import OllamaService
ollama = OllamaService()
enhanced = await ollama.enhance_news_sentiment(news_event)

# Test strategy signal generation
from src.strategies.news_enhanced_strategy import NewsEnhancedStrategy
strategy = NewsEnhancedStrategy()
signal = await strategy.generate_signal(symbol, data)
```

## 🎯 Best Practices

### **1. Model Selection**
- Use **llama2** for general analysis
- Use **codellama** for technical analysis
- Consider **fine-tuned models** for specific domains

### **2. Weight Configuration**
- **Adjust weights** based on market conditions
- **Higher news weight** during earnings season
- **Higher technical weight** in stable markets

### **3. Risk Management**
- **Set stop losses** based on AI recommendations
- **Monitor confidence** levels
- **Diversify** across multiple strategies

### **4. Performance Monitoring**
- **Track signal accuracy** over time
- **Monitor AI response** times
- **Validate news sentiment** accuracy

## 🔮 Future Enhancements

### **Planned Features**
- **Real-time news streaming** integration
- **Advanced sentiment models** (BERT, GPT)
- **Market regime detection** with AI
- **Automated strategy optimization**

### **Potential Integrations**
- **Alternative data sources** (social media, satellite)
- **ESG sentiment analysis**
- **Geopolitical risk assessment**
- **Sector rotation analysis**

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [News API Documentation](https://newsapi.org/docs)
- [Trading Strategy Development](https://www.investopedia.com/trading-strategies)
- [Sentiment Analysis in Finance](https://www.sciencedirect.com/science/article/pii/S0957417418304557)

---

**Note**: This enhanced system requires Ollama to be running for full functionality. The system gracefully degrades to traditional analysis when AI services are unavailable. 