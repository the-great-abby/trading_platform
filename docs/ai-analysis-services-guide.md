# 🏴‍☠️ AI Analysis Services Guide 🏴‍☠️

## Overview

The Space Pirate Trading System requires a comprehensive fleet of services to provide accurate AI analysis functionality. This guide explains all the required services and their roles in the AI analysis pipeline.

## 🚀 Quick Start

```bash
# Power up the entire fleet!
./scripts/power-up-ship.sh

# Check fleet status
./scripts/power-up-ship.sh status

# Just start port forwarding
./scripts/power-up-ship.sh ports
```

## 🏗️ Service Architecture

### **Core Infrastructure Services**

#### **1. TimescaleDB** (`timescaledb`)
- **Purpose**: Primary time-series database
- **Role**: Stores all trading data, historical prices, trades, backtest results
- **Data**: Market data, trades, positions, backtest runs, news articles
- **Dependencies**: None (foundation service)

#### **2. Redis** (`redis`)
- **Purpose**: Caching and session management
- **Role**: Fast data caching, session storage, real-time data
- **Data**: User sessions, cached market data, temporary calculations
- **Dependencies**: None

#### **3. RabbitMQ** (`rabbitmq`)
- **Purpose**: Message queue for async processing
- **Role**: Handles background tasks, data processing, notifications
- **Data**: Job queues, event streams, worker coordination
- **Dependencies**: None

### **Data Services**

#### **4. Market Data Service** (`market-data-service`)
- **Purpose**: Real-time stock and options data
- **Role**: Provides current prices, historical data, options chains
- **Data**: Stock prices, volume, options data, Greeks
- **Dependencies**: TimescaleDB
- **API**: `/market-data/current/{symbol}`, `/market-data/historical`

#### **5. Market Data Worker** (`market-data-worker`)
- **Purpose**: Background data processing
- **Role**: Fetches and processes market data, updates cache
- **Data**: Real-time price updates, data aggregation
- **Dependencies**: Market Data Service, RabbitMQ

#### **6. RSS Feed Service** (`rss-feed-service`)
- **Purpose**: News feed aggregation and sentiment analysis
- **Role**: Collects news articles, analyzes sentiment, classifies events
- **Data**: News articles, sentiment scores, event types
- **Dependencies**: TimescaleDB
- **API**: `/api/news/{symbol}`, `/api/sentiment/{symbol}`

### **AI & Analysis Services**

#### **7. LLM Proxy** (`llm-proxy`)
- **Purpose**: AI language model service
- **Role**: Provides AI analysis, recommendations, reasoning
- **Data**: AI-generated analysis, recommendations, confidence scores
- **Dependencies**: None
- **API**: `/api/chat`, `/api/embed`

#### **8. AI Analysis Service** (`ai-analysis-service`)
- **Purpose**: Centralized AI recommendations
- **Role**: Combines all data sources for comprehensive analysis
- **Data**: Stock recommendations, confidence scores, target prices
- **Dependencies**: Market Data Service, LLM Proxy
- **API**: `/api/analyze/symbol/{symbol}`, `/api/recommendations/daily`

#### **9. Data Analysis Service** (`data-analysis-service`)
- **Purpose**: Comprehensive data analysis
- **Role**: Technical analysis, pattern recognition, correlation analysis
- **Data**: Technical indicators, analysis results, insights
- **Dependencies**: TimescaleDB, Data Transformation Pipeline
- **API**: `/api/technical/{symbol}`, `/api/analysis/portfolio`

#### **10. Data Transformation Pipeline** (`data-transformation-pipeline`)
- **Purpose**: Data transformation and preprocessing
- **Role**: Transforms raw data into analysis-ready format
- **Data**: Cleaned and normalized data for analysis
- **Dependencies**: TimescaleDB
- **API**: `/transform/stocks`, `/transform/options`, `/transform/news`

#### **11. Postgres Vector Storage** (`postgres-vector-storage`)
- **Purpose**: Vector embeddings storage
- **Role**: Stores and searches vector embeddings for similarity
- **Data**: Market context, news embeddings, decision vectors
- **Dependencies**: TimescaleDB
- **API**: `/api/search/context`, `/api/embed`

### **Backtesting & Strategy Services**

#### **12. Backtest API** (`backtest-api`)
- **Purpose**: Strategy backtesting service
- **Role**: Runs strategy backtests, calculates performance metrics
- **Data**: Backtest results, performance metrics, equity curves
- **Dependencies**: TimescaleDB
- **API**: `/api/v1/runs`, `/api/v1/compare`

#### **13. Strategy Service** (`strategy-service`)
- **Purpose**: Strategy management
- **Role**: Manages trading strategies, configurations, parameters
- **Data**: Strategy definitions, parameters, configurations
- **Dependencies**: TimescaleDB
- **API**: `/api/strategies`, `/api/parameters`

#### **14. Trading Engine** (`trading-engine`)
- **Purpose**: Core trading logic
- **Role**: Executes trades, manages positions, risk management
- **Data**: Orders, positions, trade execution
- **Dependencies**: TimescaleDB, RabbitMQ
- **API**: `/api/orders`, `/api/positions`

### **Dashboard & UI Services**

#### **15. Unified Trading Dashboard** (`unified-trading-dashboard`)
- **Purpose**: Main trading interface
- **Role**: Trading interface, order management, position tracking
- **Data**: Trading interface, real-time data display
- **Dependencies**: Backtest API, Market Data Service
- **URL**: http://localhost:11115/

#### **16. Unified Analytics Dashboard** (`unified-analytics-dashboard`)
- **Purpose**: AI analysis interface
- **Role**: Displays AI recommendations, analysis results, insights
- **Data**: AI analysis results, charts, recommendations
- **Dependencies**: AI Analysis Service, Data Analysis Service, Vector Storage
- **URL**: http://localhost:11114/

#### **17. Unified News Dashboard** (`unified-news-dashboard`)
- **Purpose**: News and sentiment interface
- **Role**: Displays news articles, sentiment analysis, market events
- **Data**: News articles, sentiment scores, event classifications
- **Dependencies**: RSS Feed Service
- **URL**: http://localhost:11113/

#### **18. Grafana** (`grafana`)
- **Purpose**: Monitoring and visualization
- **Role**: System monitoring, performance metrics, alerts
- **Data**: System metrics, performance data, monitoring dashboards
- **Dependencies**: TimescaleDB
- **URL**: http://localhost:11044/

### **Support Services**

#### **19. Notification Service** (`notification-service`)
- **Purpose**: Alert and notification system
- **Role**: Sends alerts, notifications, trade confirmations
- **Data**: Notifications, alerts, user preferences
- **Dependencies**: TimescaleDB
- **API**: `/api/notifications/push`, `/api/alerts`

#### **20. Trading Monitor** (`trading-monitor`)
- **Purpose**: Real-time monitoring
- **Role**: Monitors trading activity, system health, performance
- **Data**: System health, trading metrics, alerts
- **Dependencies**: Trading Engine
- **API**: `/api/health`, `/api/metrics`

#### **21. Report Viewer Service** (`report-viewer-service`)
- **Purpose**: Report generation
- **Role**: Generates reports, exports data, creates summaries
- **Data**: Reports, exports, data summaries
- **Dependencies**: TimescaleDB
- **API**: `/api/reports`, `/api/exports`

## 🔄 Data Flow for AI Analysis

```
1. Market Data Service → Provides current prices and historical data
   ↓
2. RSS Feed Service → Provides news articles and sentiment
   ↓
3. Data Transformation Pipeline → Cleans and normalizes data
   ↓
4. Data Analysis Service → Performs technical analysis
   ↓
5. Vector Storage → Provides market context and embeddings
   ↓
6. LLM Proxy → Generates AI analysis and recommendations
   ↓
7. AI Analysis Service → Combines all data for final recommendations
   ↓
8. Analytics Dashboard → Displays results to user
```

## 🎯 AI Analysis Capabilities

### **What Each Service Contributes:**

#### **Market Data Service**
- Real-time stock prices
- Historical price data
- Volume and market cap
- Options data and Greeks

#### **RSS Feed Service**
- News articles from major sources
- Sentiment analysis scores
- Event classification (earnings, M&A, etc.)
- Impact assessment

#### **LLM Proxy**
- AI-generated recommendations
- Confidence scoring
- Reasoning and analysis
- Target price calculations

#### **Data Analysis Service**
- Technical indicators (RSI, MACD, etc.)
- Pattern recognition
- Correlation analysis
- Risk assessment

#### **Vector Storage**
- Market context embeddings
- News sentiment vectors
- Decision context vectors
- Similarity search

#### **AI Analysis Service**
- Comprehensive recommendations
- Multi-factor analysis
- Risk-adjusted suggestions
- Position sizing advice

## 🚨 Critical Dependencies

### **For Basic AI Analysis:**
1. **TimescaleDB** - Database foundation
2. **Market Data Service** - Price data
3. **RSS Feed Service** - News data
4. **LLM Proxy** - AI analysis
5. **AI Analysis Service** - Recommendations
6. **Analytics Dashboard** - User interface

### **For Full Functionality:**
- All 21 services listed above

## 🔧 Troubleshooting

### **Common Issues:**

#### **"No market data available"**
- Check if `market-data-service` is running
- Verify `timescaledb` connection
- Check market data worker logs

#### **"AI analysis failed"**
- Check if `llm-proxy` is running
- Verify `ai-analysis-service` health
- Check LLM service logs

#### **"News sentiment unavailable"**
- Check if `rss-feed-service` is running
- Verify RSS feed connectivity
- Check news worker logs

#### **"Dashboard not loading"**
- Check port forwarding: `./scripts/power-up-ship.sh ports`
- Verify dashboard services are running
- Check service health endpoints

### **Health Check Commands:**

```bash
# Check all services
./scripts/power-up-ship.sh status

# Check specific service
kubectl get pods -n trading-system | grep service-name

# Check service logs
kubectl logs -n trading-system deployment/service-name

# Check service health
curl http://localhost:11114/health  # Analytics Dashboard
curl http://localhost:11115/health  # Trading Dashboard
curl http://localhost:11113/health  # News Dashboard
```

## 📊 Performance Monitoring

### **Key Metrics to Monitor:**

1. **Database Performance**
   - TimescaleDB query response times
   - Database connection pool usage
   - Storage utilization

2. **AI Service Performance**
   - LLM response times
   - Analysis generation speed
   - Recommendation accuracy

3. **Data Service Performance**
   - Market data freshness
   - News feed update frequency
   - Data transformation throughput

4. **Dashboard Performance**
   - Page load times
   - Real-time data updates
   - User interaction responsiveness

## 🎯 Success Criteria

### **AI Analysis is Working When:**

✅ **Market Data Available**
- Current prices display correctly
- Historical data loads without errors
- Options data is accessible

✅ **News Sentiment Working**
- News articles display in dashboard
- Sentiment scores are calculated
- Event classification is accurate

✅ **AI Recommendations Generated**
- Recommendations appear in dashboard
- Confidence scores are reasonable (0-100%)
- Reasoning is provided for each recommendation

✅ **Technical Analysis Available**
- Technical indicators calculate correctly
- Charts display properly
- Pattern recognition works

✅ **Dashboard Functionality**
- All dashboards load without errors
- Real-time updates work
- User interactions respond properly

## 🏴‍☠️ Space Pirate Commands

```bash
# Power up the entire fleet
./scripts/power-up-ship.sh

# Check fleet status
./scripts/power-up-ship.sh status

# Start port forwarding only
./scripts/power-up-ship.sh ports

# Get help
./scripts/power-up-ship.sh help
```

---

**Last Updated**: 2025-08-08  
**Version**: 1.0  
**Status**: ✅ ACTIVE



