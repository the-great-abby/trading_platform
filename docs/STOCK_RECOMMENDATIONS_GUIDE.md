# 🎯 Stock Recommendations Guide

## Overview

The Stock Recommendations API provides comprehensive buy/sell signals for individual stocks by combining multiple analysis approaches:

- **Multi-Strategy Analysis**: RSI, MACD, Bollinger Bands, SMA Crossover, etc.
- **AI-Powered Analysis**: Using Ollama for market sentiment and reasoning
- **News Sentiment Analysis**: Real-time news impact assessment
- **Risk Assessment**: Position sizing and risk management
- **Exit Strategies**: Stop-loss and take-profit recommendations

## 🚀 Quick Start

### 1. Start the Services

```bash
# Start the strategy service
make docker-run-api

# Or start individual services
docker-compose up strategy-service
```

### 2. Get a Stock Recommendation

```bash
# Using the CLI tool
python stock_recommendation_cli.py AAPL

# Using curl
curl -X POST http://localhost:8000/recommendations/stock \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

### 3. Run the Demo

```bash
# Run the comprehensive demo
python demo_stock_recommendations.py
```

## 📊 API Endpoints

### POST `/recommendations/stock`

Get comprehensive stock recommendation with all analysis types.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "include_ai_analysis": true,
  "include_news_sentiment": true,
  "include_risk_assessment": true,
  "strategies": ["rsi_strategy", "macd_strategy", "bollinger_bands"]
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "overall_recommendation": "BUY",
  "confidence": 0.75,
  "current_price": 150.0,
  "target_price": 172.5,
  "stop_loss": 138.0,
  "take_profit": 180.0,
  "reasoning": "3 strategies indicate BUY. AI analysis: positive momentum with strong technical indicators. News sentiment: positive",
  "risk_level": "medium",
  "position_size_recommendation": "3-5% of portfolio",
  "strategies_analysis": [
    {
      "strategy_name": "rsi_strategy",
      "signal": "BUY",
      "confidence": 0.8,
      "reasoning": "RSI indicates oversold condition",
      "metadata": {
        "technical_indicators": ["RSI"],
        "signal_strength": 0.8,
        "risk_level": "medium"
      }
    }
  ],
  "ai_analysis": {
    "sentiment_score": 0.65,
    "confidence": 0.8,
    "reasoning": "AI analysis indicates positive momentum with strong technical indicators",
    "risk_assessment": "medium",
    "market_impact": "bullish",
    "recommended_action": "BUY",
    "key_factors": ["technical_momentum", "volume_increase", "positive_sentiment"],
    "market_volatility": "medium"
  },
  "news_sentiment": {
    "sentiment_score": 0.7,
    "sentiment_label": "positive",
    "confidence": 0.75,
    "recent_events_count": 5,
    "impact_score": 0.6,
    "key_events": [
      {"type": "earnings", "sentiment": "positive", "impact": "high"},
      {"type": "product_launch", "sentiment": "positive", "impact": "medium"}
    ]
  },
  "risk_assessment": {
    "risk_level": "medium",
    "volatility_score": 0.4,
    "liquidity_score": 0.8,
    "correlation_risk": 0.3,
    "sector_risk": 0.5,
    "recommended_position_size": "3-5%",
    "max_position_size": "10%",
    "stop_loss_recommendation": "8%",
    "take_profit_recommendation": "15%"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🛠️ Usage Examples

### 1. Basic Recommendation

```python
import asyncio
import httpx

async def get_basic_recommendation(symbol: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/recommendations/stock",
            json={"symbol": symbol}
        )
        return response.json()

# Usage
recommendation = await get_basic_recommendation("AAPL")
print(f"Recommendation: {recommendation['overall_recommendation']}")
print(f"Confidence: {recommendation['confidence']:.1%}")
```

### 2. Strategy-Specific Analysis

```python
async def get_strategy_recommendation(symbol: str, strategies: list):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/recommendations/stock",
            json={
                "symbol": symbol,
                "strategies": strategies,
                "include_ai_analysis": False,
                "include_news_sentiment": False
            }
        )
        return response.json()

# Usage
recommendation = await get_strategy_recommendation("GOOGL", ["rsi_strategy", "macd_strategy"])
```

### 3. Risk-Only Analysis

```python
async def get_risk_assessment(symbol: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/recommendations/stock",
            json={
                "symbol": symbol,
                "include_ai_analysis": False,
                "include_news_sentiment": False,
                "include_risk_assessment": True
            }
        )
        return response.json()

# Usage
risk_data = await get_risk_assessment("TSLA")
print(f"Risk Level: {risk_data['risk_assessment']['risk_level']}")
print(f"Position Size: {risk_data['risk_assessment']['recommended_position_size']}")
```

## 📈 Available Strategies

### Technical Analysis Strategies

1. **RSI Strategy** (`rsi_strategy`)
   - Relative Strength Index analysis
   - Oversold/overbought conditions
   - Divergence detection

2. **MACD Strategy** (`macd_strategy`)
   - Moving Average Convergence Divergence
   - Signal line crossovers
   - Histogram analysis

3. **Bollinger Bands Strategy** (`bollinger_bands`)
   - Mean reversion signals
   - Volatility analysis
   - Band squeeze detection

4. **SMA Crossover Strategy** (`sma_crossover`)
   - Simple Moving Average crossovers
   - Trend following signals
   - Multiple timeframe analysis

5. **Momentum Strategy** (`momentum_strategy`)
   - Price momentum analysis
   - Volume confirmation
   - Momentum ranking

6. **Mean Reversion Strategy** (`mean_reversion_strategy`)
   - Moving average mean reversion
   - Deviation analysis
   - Statistical arbitrage

7. **News Enhanced Strategy** (`news_enhanced`)
   - Technical + news sentiment
   - AI-powered analysis
   - Multi-factor signals

### Strategy Selection

```python
# Use specific strategies
strategies = ["rsi_strategy", "macd_strategy", "bollinger_bands"]

# Use all available strategies (default)
strategies = None

# Use only momentum strategies
momentum_strategies = ["momentum_strategy", "mean_reversion_strategy"]
```

## 🤖 AI Analysis Features

### AI-Powered Analysis

The system uses Ollama for AI-powered market analysis:

- **Sentiment Analysis**: Market sentiment scoring
- **Risk Assessment**: AI-driven risk evaluation
- **Market Impact**: Bullish/bearish/neutral assessment
- **Reasoning**: Detailed explanation of AI recommendations
- **Key Factors**: Identification of important market factors

### AI Analysis Response

```json
{
  "sentiment_score": 0.65,
  "confidence": 0.8,
  "reasoning": "AI analysis indicates positive momentum with strong technical indicators",
  "risk_assessment": "medium",
  "market_impact": "bullish",
  "recommended_action": "BUY",
  "key_factors": ["technical_momentum", "volume_increase", "positive_sentiment"],
  "market_volatility": "medium"
}
```

## 📰 News Sentiment Analysis

### News Features

- **Real-time Monitoring**: Multiple financial news sources
- **Event Classification**: Earnings, M&A, regulatory, macroeconomic
- **Sentiment Scoring**: -1.0 to 1.0 scale
- **Impact Assessment**: High/medium/low impact events
- **Company Mapping**: 100+ major companies

### News Response

```json
{
  "sentiment_score": 0.7,
  "sentiment_label": "positive",
  "confidence": 0.75,
  "recent_events_count": 5,
  "impact_score": 0.6,
  "key_events": [
    {"type": "earnings", "sentiment": "positive", "impact": "high"},
    {"type": "product_launch", "sentiment": "positive", "impact": "medium"}
  ]
}
```

## ⚠️ Risk Assessment

### Risk Metrics

- **Volatility Score**: Price volatility assessment
- **Liquidity Score**: Trading volume and market depth
- **Correlation Risk**: Market correlation analysis
- **Sector Risk**: Industry-specific risk factors
- **Position Sizing**: Recommended position sizes
- **Stop Loss**: Risk management levels
- **Take Profit**: Profit target recommendations

### Risk Response

```json
{
  "risk_level": "medium",
  "volatility_score": 0.4,
  "liquidity_score": 0.8,
  "correlation_risk": 0.3,
  "sector_risk": 0.5,
  "recommended_position_size": "3-5%",
  "max_position_size": "10%",
  "stop_loss_recommendation": "8%",
  "take_profit_recommendation": "15%"
}
```

## 🎯 Exit Strategies

### Automatic Exit Recommendations

The system provides automatic exit strategy recommendations:

**For BUY Signals:**
- **Target Price**: 15% upside target
- **Stop Loss**: 8% downside protection
- **Take Profit**: 20% upside target

**For SELL Signals:**
- **Target Price**: 15% downside target
- **Stop Loss**: 8% upside protection
- **Take Profit**: 20% downside target

### Exit Strategy Example

```python
recommendation = await get_stock_recommendation("AAPL")

if recommendation['overall_recommendation'] == "BUY":
    entry_price = recommendation['current_price']
    target_price = recommendation['target_price']
    stop_loss = recommendation['stop_loss']
    take_profit = recommendation['take_profit']
    
    print(f"Entry: ${entry_price:.2f}")
    print(f"Target: ${target_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Take Profit: ${take_profit:.2f}")
```

## 🔧 CLI Tool Usage

### Basic Usage

```bash
# Get recommendation for a stock
python stock_recommendation_cli.py AAPL

# Get recommendation without AI analysis
python stock_recommendation_cli.py GOOGL --no-ai

# Get risk-only analysis
python stock_recommendation_cli.py MSFT --risk-only

# Use specific strategies
python stock_recommendation_cli.py TSLA --strategies rsi_strategy,macd_strategy

# Get JSON output
python stock_recommendation_cli.py AAPL --format json

# Get summary output
python stock_recommendation_cli.py GOOGL --format summary
```

### CLI Options

- `--no-ai`: Exclude AI analysis
- `--no-news`: Exclude news sentiment analysis
- `--no-risk`: Exclude risk assessment
- `--risk-only`: Only include risk assessment
- `--strategies <list>`: Comma-separated list of strategies
- `--format <format>`: Output format (text, json, summary)
- `--api-url <url>`: API base URL

## 📊 Integration Examples

### 1. Portfolio Management

```python
async def analyze_portfolio(symbols: list):
    recommendations = []
    
    for symbol in symbols:
        rec = await get_stock_recommendation(symbol)
        if rec and rec['overall_recommendation'] == "BUY":
            recommendations.append({
                'symbol': symbol,
                'confidence': rec['confidence'],
                'target_price': rec['target_price'],
                'position_size': rec['position_size_recommendation']
            })
    
    # Sort by confidence
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    return recommendations

# Usage
portfolio = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
buy_signals = await analyze_portfolio(portfolio)
```

### 2. Risk Monitoring

```python
async def monitor_risk(symbols: list):
    risk_alerts = []
    
    for symbol in symbols:
        rec = await get_stock_recommendation(symbol, include_risk_assessment=True)
        if rec and rec['risk_assessment']['risk_level'] == "high":
            risk_alerts.append({
                'symbol': symbol,
                'risk_level': rec['risk_assessment']['risk_level'],
                'volatility': rec['risk_assessment']['volatility_score']
            })
    
    return risk_alerts

# Usage
alerts = await monitor_risk(["TSLA", "NVDA", "AMD"])
```

### 3. Strategy Performance Tracking

```python
async def track_strategy_performance(symbol: str, strategies: list):
    results = {}
    
    for strategy in strategies:
        rec = await get_stock_recommendation(
            symbol, 
            strategies=[strategy],
            include_ai_analysis=False,
            include_news_sentiment=False
        )
        
        if rec and rec['strategies_analysis']:
            strategy_result = rec['strategies_analysis'][0]
            results[strategy] = {
                'signal': strategy_result['signal'],
                'confidence': strategy_result['confidence']
            }
    
    return results

# Usage
performance = await track_strategy_performance("AAPL", ["rsi_strategy", "macd_strategy"])
```

## 🚀 Advanced Features

### 1. Custom Strategy Combinations

```python
# Momentum-focused analysis
momentum_strategies = ["momentum_strategy", "mean_reversion_strategy"]

# Technical analysis only
technical_strategies = ["rsi_strategy", "macd_strategy", "bollinger_bands", "sma_crossover"]

# News-enhanced analysis
news_strategies = ["news_enhanced"]
```

### 2. Batch Processing

```python
async def batch_recommendations(symbols: list, **kwargs):
    tasks = []
    for symbol in symbols:
        task = get_stock_recommendation(symbol, **kwargs)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA"]
recommendations = await batch_recommendations(symbols)
```

### 3. Real-time Monitoring

```python
async def monitor_stock(symbol: str, interval: int = 300):
    """Monitor a stock every 5 minutes"""
    while True:
        try:
            recommendation = await get_stock_recommendation(symbol)
            if recommendation['overall_recommendation'] != "HOLD":
                print(f"🚨 Signal for {symbol}: {recommendation['overall_recommendation']}")
                print(f"Confidence: {recommendation['confidence']:.1%}")
            
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"Error monitoring {symbol}: {e}")
            await asyncio.sleep(60)

# Usage
await monitor_stock("AAPL")
```

## 🔍 Troubleshooting

### Common Issues

1. **Service Not Available**
   ```bash
   # Check if service is running
   curl http://localhost:8000/health
   
   # Start the service
   make docker-run-api
   ```

2. **No Market Data**
   ```bash
   # Check market data service
   curl http://localhost:8000/api/v1/market-data/AAPL
   ```

3. **AI Analysis Failing**
   ```bash
   # Check Ollama service
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed error information
try:
    recommendation = await get_stock_recommendation("AAPL")
except Exception as e:
    print(f"Error details: {e}")
    import traceback
    traceback.print_exc()
```

## 📈 Performance Tips

1. **Use Specific Strategies**: Only request needed strategies
2. **Disable Unused Analysis**: Turn off AI/news/risk if not needed
3. **Batch Requests**: Use batch processing for multiple symbols
4. **Cache Results**: Cache recommendations for 5-15 minutes
5. **Monitor Errors**: Track failed requests and retry logic

## 🔮 Future Enhancements

### Planned Features

1. **Real-time Price Integration**: Live price feeds
2. **Options Analysis**: Options strategies and Greeks
3. **Portfolio Optimization**: Multi-asset recommendations
4. **Backtesting Integration**: Historical performance analysis
5. **Machine Learning**: Enhanced prediction models
6. **Social Sentiment**: Twitter, Reddit sentiment analysis
7. **International Markets**: Global stock support
8. **Custom Strategies**: User-defined strategy creation

### Advanced Configuration

```python
# Future configuration options
config = {
    "real_time_prices": True,
    "options_analysis": True,
    "portfolio_optimization": True,
    "backtesting_enabled": True,
    "ml_models": ["lstm", "transformer"],
    "social_sentiment": True,
    "international_markets": True,
    "custom_strategies": True
}
```

## 📚 Additional Resources

- [Trading Strategies Guide](docs/STRATEGIES_GUIDE.md)
- [AI Analysis Guide](docs/NEWS_AI_GUIDE.md)
- [Risk Management Guide](docs/RISK_MANAGEMENT_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Backtesting Guide](docs/BACKTESTING_GUIDE.md)

---

**🎯 Ready to get started?** Run `python demo_stock_recommendations.py` to see the system in action! 