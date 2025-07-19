# 🚀 Centralized API Gateway Guide

## Overview

The **Space Trading Station Centralized API Gateway** provides a single entry point for all external systems to interact with the trading platform. This gateway consolidates all trading system functionality into a unified, secure, and well-documented API.

## 🎯 Key Features

- **Single Entry Point**: All trading operations through one API
- **Unified Authentication**: Bearer token-based security
- **Rate Limiting**: Configurable request limits per user
- **Comprehensive Monitoring**: Prometheus metrics and health checks
- **Real-time Data**: WebSocket support for live market data
- **Standardized Responses**: Consistent JSON response format
- **Full Documentation**: Auto-generated Swagger/OpenAPI docs

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Mobile    │  │   Web App   │  │   Desktop   │        │
│  │    App      │  │             │  │    App      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                API Gateway (Port 8000)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Authentication & Rate Limiting                    │   │
│  │  Request Routing & Load Balancing                  │   │
│  │  Error Handling & Logging                          │   │
│  │  Metrics Collection                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Trading    │ │  Market     │ │  Portfolio  │
│  Service    │ │  Data       │ │  Service    │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Strategy   │ │  Analytics  │ │  Risk       │
│  Service    │ │  Service    │ │  Service    │
└─────────────┘ └─────────────┘ └─────────────┘
```

## 🚀 Quick Start

### 1. Authentication

All API requests require a Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer your-api-key-here" \
     http://localhost:8000/health
```

### 2. Check System Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "trading": "healthy",
    "market_data": "healthy",
    "portfolio": "healthy",
    "analytics": "healthy",
    "strategy": "healthy",
    "order": "healthy",
    "risk": "healthy",
    "user": "healthy",
    "backtest": "healthy",
    "redis": "healthy"
  }
}
```

### 3. Get System Information

```bash
curl http://localhost:8000/
```

## 📊 API Endpoints

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.tradingstation.com`

### Authentication
All endpoints require authentication via Bearer token:
```
Authorization: Bearer your-api-key-here
```

### Response Format
All responses follow this standard format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456"
}
```

## 🎯 Core Endpoints

### Trading Operations

#### Create Order
```bash
POST /api/v1/trading/orders
```

Request:
```json
{
  "symbol": "AAPL",
  "action": "buy",
  "quantity": 100,
  "order_type": "market",
  "price": null,
  "strategy": "rsi_strategy"
}
```

#### Get Orders
```bash
GET /api/v1/trading/orders
```

Parameters:
- `status` (optional): Filter by order status
- `symbol` (optional): Filter by symbol

### Market Data

#### Get Market Quotes
```bash
POST /api/v1/market-data/quotes
```

Request:
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "interval": "1d",
  "period": "1y"
}
```

### Portfolio Management

#### Get Portfolio
```bash
GET /api/v1/portfolio
```

Parameters:
- `account_id` (optional): Specific account
- `include_positions` (default: true): Include current positions
- `include_history` (default: false): Include historical data

### Strategy Management

#### Get Available Strategies
```bash
GET /api/v1/strategies
```

#### Get Strategy Recommendations
```bash
POST /api/v1/strategies/recommendations
```

Request:
```json
{
  "symbol": "AAPL",
  "strategies": ["rsi_strategy", "macd_strategy"],
  "include_ai_analysis": true,
  "include_news_sentiment": true
}
```

### Backtesting

#### Run Backtest
```bash
POST /api/v1/backtest/run
```

Request:
```json
{
  "strategy": "rsi_strategy",
  "symbols": ["AAPL"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 100000,
  "commission": 0.001
}
```

#### Get Backtest Results
```bash
GET /api/v1/backtest/results
```

### Analytics

#### Get Performance Analytics
```bash
GET /api/v1/analytics/performance
```

Parameters:
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis
- `metrics` (optional): Comma-separated list of metrics

### Risk Management

#### Get Risk Positions
```bash
GET /api/v1/risk/positions
```

### User Management

#### Get User Profile
```bash
GET /api/v1/users/profile
```

## 🔌 WebSocket Support

### Real-time Market Data
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-data');

ws.onopen = function() {
    console.log('Connected to market data stream');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Market data:', data);
};

ws.onclose = function() {
    console.log('Disconnected from market data stream');
};
```

## 📱 Client Libraries

### Python Client
```python
from src.utils.trading_api_client import TradingAPIClient, TradingOrder, OrderSide

# Initialize client
async with TradingAPIClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
) as client:
    
    # Create order
    order = TradingOrder(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=100
    )
    result = await client.create_order(order)
    
    # Get market data
    quotes = await client.get_market_quotes(["AAPL", "MSFT"])
    
    # Get recommendations
    recommendations = await client.get_strategy_recommendations("AAPL")
```

### JavaScript/TypeScript Client
```javascript
class TradingAPIClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async makeRequest(endpoint, options = {}) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        return response.json();
    }
    
    async createOrder(orderData) {
        return this.makeRequest('/api/v1/trading/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }
    
    async getMarketQuotes(symbols) {
        return this.makeRequest('/api/v1/market-data/quotes', {
            method: 'POST',
            body: JSON.stringify({ symbols })
        });
    }
}

// Usage
const client = new TradingAPIClient('http://localhost:8000', 'your-api-key');
const result = await client.createOrder({
    symbol: 'AAPL',
    action: 'buy',
    quantity: 100
});
```

## 🔒 Security

### Authentication
- **Bearer Token**: All requests require a valid Bearer token
- **Token Validation**: Tokens are validated on every request
- **User Context**: Each request is associated with a user account

### Rate Limiting
- **Default Limit**: 100 requests per minute per user
- **Configurable**: Limits can be adjusted per endpoint
- **Headers**: Rate limit information included in response headers

### CORS
- **Development**: All origins allowed
- **Production**: Configure specific allowed origins

## 📊 Monitoring

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Individual service health
curl http://localhost:8000/health?service=trading
```

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/metrics
```

Available metrics:
- `gateway_requests_total`: Total request count
- `gateway_request_duration_seconds`: Request latency
- Service-specific metrics for each microservice

### Logging
All requests are logged with:
- Request ID for tracing
- User ID for auditing
- Request/response details
- Performance metrics

## 🚨 Error Handling

### Standard Error Response
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "error": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456"
}
```

### Common Error Codes
- `401`: Unauthorized - Invalid or missing API key
- `429`: Too Many Requests - Rate limit exceeded
- `503`: Service Unavailable - Backend service down
- `500`: Internal Server Error - Unexpected error

## 🔧 Configuration

### Environment Variables
```bash
# Service URLs
TRADING_SERVICE_URL=http://trading-service:8000
MARKET_DATA_SERVICE_URL=http://market-data-service:8000
PORTFOLIO_SERVICE_URL=http://portfolio-service:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8000
STRATEGY_SERVICE_URL=http://strategy-service:8000
ORDER_SERVICE_URL=http://order-service:8000
RISK_SERVICE_URL=http://risk-service:8000
USER_SERVICE_URL=http://user-service:8000
BACKTEST_API_URL=http://backtest-api:8000

# Redis
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET=your-secret-key

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Caching
CACHE_TTL=300

# Timeouts
REQUEST_TIMEOUT=30
```

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t trading-gateway .

# Run container
docker run -p 8000:8000 trading-gateway
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/gateway.yaml

# Port forward for local access
kubectl port-forward svc/gateway 8000:80 -n trading-system
```

### Development
```bash
# Install dependencies
pip install -r services/gateway/requirements.txt

# Run locally
python services/gateway/main.py
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### OpenAPI Specification
```bash
# Download OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### API Test
```bash
# Test authentication
curl -H "Authorization: Bearer test-token" \
     http://localhost:8000/api/v1/trading/orders

# Test rate limiting
for i in {1..110}; do
    curl -H "Authorization: Bearer test-token" \
         http://localhost:8000/health
done
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer test-token" \
   http://localhost:8000/health
```

## 🔄 Integration Examples

### Trading Bot Integration
```python
import asyncio
from src.utils.trading_api_client import TradingAPIClient, TradingOrder, OrderSide

async def trading_bot():
    async with TradingAPIClient() as client:
        while True:
            # Get market data
            quotes = await client.get_market_quotes(["AAPL"])
            
            # Get recommendations
            rec = await client.get_strategy_recommendations("AAPL")
            
            if rec['data']['recommendation'] == 'buy':
                # Place order
                order = TradingOrder(
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    quantity=100
                )
                await client.create_order(order)
            
            await asyncio.sleep(60)  # Check every minute

# Run bot
asyncio.run(trading_bot())
```

### Dashboard Integration
```javascript
// Real-time dashboard
class TradingDashboard {
    constructor() {
        this.ws = new WebSocket('ws://localhost:8000/ws/market-data');
        this.setupWebSocket();
    }
    
    setupWebSocket() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateDashboard(data);
        };
    }
    
    updateDashboard(data) {
        // Update UI with real-time data
        document.getElementById('price').textContent = data.price;
        document.getElementById('change').textContent = data.change;
    }
}

const dashboard = new TradingDashboard();
```

## 🎯 Best Practices

### 1. Error Handling
Always check the `success` field in responses:
```python
response = await client.create_order(order)
if not response['success']:
    print(f"Error: {response['error']}")
    return
```

### 2. Rate Limiting
Implement exponential backoff for rate limit errors:
```python
async def make_request_with_retry(client, request_func):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await request_func()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
```

### 3. Connection Management
Use context managers for proper resource cleanup:
```python
async with TradingAPIClient() as client:
    # Make requests
    result = await client.get_portfolio()
```

### 4. Monitoring
Monitor your API usage:
```python
# Check system health before making requests
health = await client.health_check()
if health['status'] != 'healthy':
    print("System is not healthy")
    return
```

## 🆘 Support

### Getting Help
- **Documentation**: Check `/docs` for interactive API docs
- **Health Check**: Use `/health` to verify system status
- **Logs**: Check application logs for detailed error information
- **Metrics**: Monitor `/metrics` for performance data

### Common Issues

#### Authentication Errors
```bash
# Check if API key is valid
curl -H "Authorization: Bearer your-key" \
     http://localhost:8000/health
```

#### Rate Limiting
```bash
# Check rate limit headers
curl -I -H "Authorization: Bearer your-key" \
     http://localhost:8000/api/v1/trading/orders
```

#### Service Unavailable
```bash
# Check individual service health
curl http://localhost:8000/health | jq '.services'
```

This centralized API gateway provides a robust, secure, and scalable interface for all external systems to interact with your trading platform. The unified approach simplifies integration while maintaining security and performance. 