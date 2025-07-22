# 🤖 AI Analysis System Guide

## Overview

The AI Analysis System provides automated buy/sell recommendations for stocks using your existing LLM proxy service. It combines market data, technical analysis, and sentiment analysis to generate confidence-scored recommendations.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Market Data    │───▶│  AI Analysis    │───▶│  LLM Proxy      │
│  Service        │    │  Service        │    │  Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  News Worker    │───▶│  Technical      │───▶│  AI Analysis    │
│  (Sentiment)    │    │  Indicators     │    │  Results        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Deploy AI Analysis Service

```bash
# Build and deploy the AI analysis service
make ai-analysis-deploy

# Check service status
kubectl get pods -n trading-system | grep ai-analysis-service
```

### 2. Test the Service

```bash
# Test single stock analysis
make ai-analysis-test

# Get daily recommendations
make ai-analysis-daily
```

### 3. Generate AI Recommendations Report

```bash
# Generate report for default stock list
python scripts/generate_ai_recommendations.py

# Generate report for specific symbols
python scripts/generate_ai_recommendations.py --symbols AAPL MSFT GOOGL

# Use daily recommendations
python scripts/generate_ai_recommendations.py --daily
```

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:11085/health
```

### Single Stock Analysis
```bash
curl -X POST http://localhost:11085/api/analyze/symbol/AAPL \
  -H "Content-Type: application/json" \
  -d '{"include_news": true, "include_technical": true}'
```

### Batch Analysis
```bash
curl -X POST http://localhost:11085/api/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "include_news": true,
    "include_technical": true
  }'
```

### Get Analysis Results
```bash
curl http://localhost:11085/api/analysis/{analysis_id}
```

### Daily Recommendations
```bash
curl http://localhost:11085/api/recommendations/daily
```

## 📈 Report Generation

### Command Line Interface

```bash
# Basic usage
python scripts/generate_ai_recommendations.py

# With custom symbols
python scripts/generate_ai_recommendations.py --symbols AAPL MSFT GOOGL TSLA

# Use daily recommendations
python scripts/generate_ai_recommendations.py --daily

# Custom output filename
python scripts/generate_ai_recommendations.py --output my_recommendations.html

# Exclude news sentiment
python scripts/generate_ai_recommendations.py --no-include-news

# Exclude technical analysis
python scripts/generate_ai_recommendations.py --no-include-technical
```

### Report Features

- **Interactive Charts**: Plotly-powered visualization
- **Confidence Scoring**: 0-100% confidence levels
- **Technical Indicators**: RSI, MACD, Bollinger Bands, SMAs
- **Sentiment Analysis**: News sentiment integration
- **Risk Assessment**: Position sizing and stop-loss levels
- **Professional Design**: MetaTrader-style interface

## 🎯 Recommendation Types

### Confidence Levels
- **High (80-100%)**: Strong technical + sentiment alignment
- **Medium (60-79%)**: Mixed signals with positive bias
- **Low (40-59%)**: Weak signals, monitor only
- **Very Low (<40%)**: Avoid or close positions

### Action Types
- **BUY**: Strong bullish signals
- **SELL**: Strong bearish signals
- **HOLD**: Neutral or mixed signals

## 🔧 Configuration

### Environment Variables

```bash
# AI Analysis Service
AI_ANALYSIS_URL=http://localhost:11085

# LLM Proxy Service
LLM_PROXY_URL=http://localhost:12001

# Market Data Service
MARKET_DATA_URL=http://localhost:8002

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading
```

### Default Stock List

The system analyzes these stocks by default:
```
AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, 
AMD, INTC, CRM, ORCL, ADBE, PYPL, NKE, DIS,
JPM, BAC, WFC, GS, JNJ, PFE, UNH, HD, PG
```

## 📊 Integration with Existing Services

### Gateway Integration

The AI analysis is integrated into the main gateway at:
- **Reports Dashboard**: `http://localhost:8000/reports`
- **API Endpoints**: `http://localhost:8000/api/ai-analysis/*`

### Central Hub Integration

Access AI analysis from the central hub:
- **Central Hub**: `http://localhost:11080`
- **AI Analysis Section**: Available in the main dashboard

## 🔍 Monitoring & Debugging

### Service Logs
```bash
# View AI analysis service logs
make ai-analysis-logs

# Or directly
kubectl logs -f deployment/ai-analysis-service -n trading-system
```

### Health Checks
```bash
# Check all services health
curl http://localhost:8000/api/services/health

# Check AI analysis specifically
curl http://localhost:11085/health
```

### Troubleshooting

#### Service Not Starting
```bash
# Check pod status
kubectl get pods -n trading-system | grep ai-analysis

# Check pod events
kubectl describe pod -l app=ai-analysis-service -n trading-system

# Check logs
kubectl logs deployment/ai-analysis-service -n trading-system
```

#### LLM Service Issues
```bash
# Check LLM proxy health
curl http://localhost:12001/health

# Check LLM service logs
kubectl logs -f deployment/llm-service -n trading-system
```

#### Analysis Failures
```bash
# Check analysis service logs
kubectl logs -f deployment/ai-analysis-service -n trading-system

# Test LLM connection
curl -X POST http://localhost:12001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 10}'
```

## 🚀 Advanced Usage

### Custom Stock Lists

Create custom stock lists for analysis:

```python
# In your script
custom_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
python scripts/generate_ai_recommendations.py --symbols AAPL MSFT GOOGL TSLA NVDA
```

### Batch Processing

Run analysis on multiple stock lists:

```bash
# Technology stocks
python scripts/generate_ai_recommendations.py --symbols AAPL MSFT GOOGL NVDA AMD

# Financial stocks
python scripts/generate_ai_recommendations.py --symbols JPM BAC WFC GS

# Healthcare stocks
python scripts/generate_ai_recommendations.py --symbols JNJ PFE UNH
```

### Automated Reports

Set up automated daily reports:

```bash
# Add to crontab for daily reports
0 9 * * * cd /path/to/project && python scripts/generate_ai_recommendations.py --daily
```

## 📈 Performance Optimization

### Resource Allocation

The AI analysis service is configured with:
- **Memory**: 128Mi request, 256Mi limit
- **CPU**: 100m request, 200m limit
- **Replicas**: 1 (can be scaled as needed)

### Scaling

```bash
# Scale up for high load
kubectl scale deployment ai-analysis-service --replicas=3 -n trading-system

# Scale down to save resources
kubectl scale deployment ai-analysis-service --replicas=1 -n trading-system
```

## 🔐 Security Considerations

### API Access
- All endpoints are internal (ClusterIP)
- Access via gateway proxy
- No direct external access

### Data Privacy
- Analysis data stored in memory only
- No persistent storage of recommendations
- LLM prompts don't contain sensitive data

## 💰 Cost Optimization

### LLM API Usage
- **Estimated cost**: $50-200/month
- **Optimization**: Batch processing reduces API calls
- **Caching**: Results cached in memory

### Infrastructure Costs
- **Memory**: ~128Mi per service
- **CPU**: ~100m per service
- **Storage**: Minimal (in-memory only)

## 🎯 Success Metrics

### Performance KPIs
- **Response Time**: < 5 seconds per stock
- **Accuracy**: 60-70% (industry standard)
- **Coverage**: 100+ stocks
- **Uptime**: 99.9%

### Quality Metrics
- **Confidence Distribution**: Target 60%+ high confidence
- **Recommendation Diversity**: Balanced buy/sell/hold
- **Technical Signal Quality**: Valid indicator readings

## 🔮 Future Enhancements

### Planned Features
1. **Machine Learning Models**: Custom trained models
2. **Portfolio Optimization**: Multi-asset recommendations
3. **Real-time Alerts**: Webhook notifications
4. **Backtesting Integration**: Strategy validation
5. **Advanced Analytics**: Risk-adjusted returns

### Migration to Larger System
The architecture is designed for easy migration:
- **Stateless Design**: No persistent storage dependencies
- **Containerized**: Easy to move between systems
- **API-First**: Standard REST interfaces
- **Modular**: Independent service components

## 📞 Support

### Common Issues
1. **Service not starting**: Check resource limits
2. **LLM connection failed**: Verify LLM proxy service
3. **Analysis timeout**: Increase timeout parameter
4. **Report generation failed**: Check file permissions

### Getting Help
- Check service logs: `make ai-analysis-logs`
- Verify health: `curl http://localhost:11085/health`
- Test LLM: `curl http://localhost:12001/health`
- Review this guide for troubleshooting steps

---

**🎉 You now have a complete AI-powered trading recommendation system integrated with your existing infrastructure!** 