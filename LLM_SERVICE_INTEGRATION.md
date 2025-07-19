# 🤖 LLM Service Integration

## Overview

The **LLM Service Integration** provides AI-powered intelligence for the Ultimate Trading Platform by connecting to a remotely hosted Ollama LLM proxy service. This service enables advanced trading decisions through sentiment analysis, signal generation, risk assessment, and market analysis.

## 🏗️ Architecture

### LLM Service Components

1. **LLM Client** (`src/services/llm_service/llm_client.py`)
   - HTTP client for remote Ollama service communication
   - Rate limiting and caching
   - Error handling and retries
   - Health monitoring

2. **LLM Service** (`src/services/llm_service/service.py`)
   - FastAPI service for LLM operations
   - RESTful API endpoints
   - Request/response handling
   - Integration with trading platform

3. **LLM Worker** (`services/llm-worker/main.py`)
   - Background processing of LLM tasks
   - RabbitMQ integration
   - Asynchronous task processing
   - Error handling and retries

## 🔧 Configuration

### Environment Variables

```bash
# LLM Service Configuration
LLM_BASE_URL=http://localhost:8081
LLM_API_KEY=your_api_key_here
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
LLM_RATE_LIMIT=100
LLM_RATE_LIMIT_WINDOW=60
LLM_CACHE_TTL=300
LLM_HEALTH_CHECK_INTERVAL=60

# Database and Message Queue
DATABASE_URL=postgresql://user:pass@host:port/db
RABBITMQ_URL=amqp://user:pass@host:port
```

### Configuration File

The LLM service configuration is centralized in `src/utils/trading_config.py`:

```python
LLM_SERVICE_CONFIG = {
    'base_url': 'http://localhost:8081',
    'api_key': '',
    'timeout': 30,
    'max_retries': 3,
    'rate_limit_requests': 100,
    'rate_limit_window': 60,
    'cache_ttl': 300,
    'health_check_interval': 60
}
```

## 🚀 Quick Start

### 1. Build LLM Service

```bash
# Build LLM service and worker
make build-llm-service
make build-llm-worker
```

### 2. Deploy to Kubernetes

```bash
# Deploy LLM service
kubectl apply -f k8s/llm-service.yaml
```

### 3. Start Services

```bash
# Start LLM service and worker
make start-llm-service
make start-llm-worker
```

### 4. Verify Deployment

```bash
# Check service status
kubectl get pods -n trading-system -l app=llm-service
kubectl get pods -n trading-system -l app=llm-worker

# Check service health
curl http://localhost:8008/health
```

## 📊 API Endpoints

### Health and Monitoring

```http
GET /health
GET /metrics
GET /history?limit=100
DELETE /history
```

### Centralized API

The LLM service provides a centralized API endpoint that handles all operations with callback support:

```http
POST /api/v1/llm
Content-Type: application/json

{
  "operation": "sentiment|signal|risk|market|custom",
  "data": {
    // Operation-specific data
  },
  "model": "gpt-4",
  "callback_config": {
    "callback_type": "http_webhook|rabbitmq_queue|database_update|trading_action|notification|logging",
    "url": "http://localhost:8080/webhook/callback",
    "queue_name": "llm.results",
    "method": "POST",
    "headers": {"Authorization": "Bearer token"},
    "timeout": 30,
    "retries": 3,
    "retry_delay": 1.0,
    "metadata": {"source": "trading_platform"}
  },
  "priority": 1,
  "use_cache": true
}
```

### Individual Endpoints

#### Sentiment Analysis
```http
POST /sentiment
Content-Type: application/json

{
  "text": "Apple reported strong Q4 earnings with 15% revenue growth",
  "context": "Technology sector earnings season",
  "model": "gpt-3.5-turbo",
  "callback_config": {
    "callback_type": "http_webhook",
    "url": "http://localhost:8080/webhook/sentiment"
  }
}
```

#### Trading Signal Generation
```http
POST /signal
Content-Type: application/json

{
  "symbol": "AAPL",
  "market_data": {
    "price": 150.25,
    "volume": 50000000,
    "change_24h": 2.5,
    "market_cap": 2500000000000
  },
  "news_data": [
    {
      "title": "Apple beats earnings expectations",
      "sentiment": "positive"
    }
  ],
  "technical_indicators": {
    "rsi": 65,
    "macd": "bullish",
    "sma_20": 148.50
  },
  "model": "gpt-4",
  "callback_config": {
    "callback_type": "trading_action",
    "metadata": {"auto_execute": true}
  }
}
```

#### Risk Assessment
```http
POST /risk
Content-Type: application/json

{
  "portfolio_data": {
    "total_value": 100000,
    "positions": [
      {"symbol": "AAPL", "value": 25000, "weight": 0.25}
    ],
    "drawdown": 2.5
  },
  "market_conditions": {
    "volatility": "high",
    "trend": "bullish",
    "economic_indicators": ["inflation_rising", "fed_hawkish"]
  },
  "model": "gpt-4",
  "callback_config": {
    "callback_type": "notification",
    "metadata": {"priority": "high"}
  }
}
```

#### Market Analysis
```http
POST /market
Content-Type: application/json

{
  "market_data": {
    "market": "S&P 500",
    "price_action": {"trend": "bullish", "support": 4200, "resistance": 4500},
    "volume_analysis": {"above_average": true, "distribution": "normal"},
    "support_resistance": {"support": [4200, 4150], "resistance": [4500, 4550]}
  },
  "timeframe": "1d",
  "model": "gpt-4",
  "callback_config": {
    "callback_type": "rabbitmq_queue",
    "queue_name": "market.analysis.results"
  }
}
```

#### Custom LLM Request
```http
POST /custom
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a trading expert."},
    {"role": "user", "content": "Analyze the current market conditions."}
  ],
  "task_type": "market_analysis",
  "temperature": 0.3,
  "max_tokens": 500,
  "use_cache": true,
  "callback_config": {
    "callback_type": "database_update",
    "metadata": {"store_result": true}
  },
  "priority": 3
}
```

## 🔄 RabbitMQ Integration

### Queues

The LLM worker processes tasks from the following queues:

- `llm.sentiment` - Sentiment analysis tasks
- `llm.signal` - Trading signal generation tasks
- `llm.risk` - Risk assessment tasks
- `llm.market` - Market analysis tasks
- `llm.custom` - Custom LLM tasks

### Callback Queues

The LLM service also publishes callback results to:

- `llm.results` - Successful LLM responses
- `llm.errors` - Failed LLM requests
- `llm.callbacks` - General callback results

### Publishing Tasks

```python
import json
import aio_pika

# Connect to RabbitMQ
connection = await aio_pika.connect_robust("amqp://localhost")
channel = await connection.channel()

# Publish sentiment analysis task
task_data = {
    "task_id": "sentiment_001",
    "text": "Apple reported strong earnings",
    "model": "gpt-3.5-turbo",
    "metadata": {"source": "news_analysis"}
}

await channel.default_exchange.publish(
    aio_pika.Message(body=json.dumps(task_data).encode()),
    routing_key="llm.sentiment"
)
```

### Consuming Results

```python
# Consume LLM results
async def process_llm_results(message):
    data = json.loads(message.body.decode())
    
    if data['success']:
        print(f"Task {data['task_id']} completed successfully")
        print(f"Result: {data['result']}")
    else:
        print(f"Task {data['task_id']} failed: {data['result']}")
    
    await message.ack()

await channel.declare_queue("llm.results")
await channel.set_qos(prefetch_count=1)
await channel.consume("llm.results", process_llm_results)
```

## 🧠 LLM Models and Tasks

### Supported Models

- **GPT-4** - Advanced reasoning and analysis
- **GPT-3.5-turbo** - Fast and cost-effective
- **Claude-3** - Strong analytical capabilities
- **Mistral** - Open-source alternative
- **Llama2** - Local deployment option
- **CodeLlama** - Code and data analysis

### Callback Types

The LLM service supports multiple callback types for taking actions after responses:

1. **HTTP Webhook** (`http_webhook`) - Send results to external HTTP endpoints
2. **RabbitMQ Queue** (`rabbitmq_queue`) - Publish results to message queues
3. **Database Update** (`database_update`) - Store results in database
4. **Trading Action** (`trading_action`) - Execute trading commands automatically
5. **Notification** (`notification`) - Send notifications to users
6. **Logging** (`logging`) - Log results for monitoring and debugging

### Task Types

1. **Sentiment Analysis** (`SENTIMENT_ANALYSIS`)
   - News sentiment analysis
   - Social media sentiment
   - Earnings call sentiment
   - Market sentiment

2. **Signal Generation** (`SIGNAL_GENERATION`)
   - Trading signal generation
   - Entry/exit recommendations
   - Position sizing suggestions
   - Risk-reward analysis

3. **Risk Assessment** (`RISK_ASSESSMENT`)
   - Portfolio risk analysis
   - Position concentration
   - Correlation analysis
   - Stress testing

4. **Market Analysis** (`MARKET_ANALYSIS`)
   - Market trend analysis
   - Technical analysis
   - Fundamental analysis
   - Market regime detection

5. **News Analysis** (`NEWS_ANALYSIS`)
   - News impact assessment
   - Event-driven analysis
   - Market reaction prediction
   - Volatility forecasting

6. **Strategy Optimization** (`STRATEGY_OPTIMIZATION`)
   - Parameter optimization
   - Strategy backtesting
   - Performance analysis
   - Risk-adjusted returns

## 📈 Performance and Monitoring

### Metrics

The LLM service provides comprehensive metrics including callback performance:

```json
{
  "llm_metrics": {
    "total_requests": 1250,
    "successful_requests": 1180,
    "failed_requests": 70,
    "average_response_time": 2.45,
    "cache_hits": 320,
    "cache_misses": 930,
    "callbacks_executed": 1150,
    "callback_failures": 15,
    "average_callback_time": 0.85,
    "callback_queue_size": 5,
    "callback_workers_active": 5,
    "is_healthy": true,
    "rate_limit_remaining": 85
  },
  "service_metrics": {
    "total_requests": 1250,
    "successful_requests": 1180,
    "failed_requests": 70,
    "average_response_time": 2.45,
    "callbacks_executed": 1150
  },
  "callback_support": true
}
```

### Health Monitoring

```bash
# Check service health
curl http://localhost:8008/health

# Response:
{
  "status": "healthy",
  "llm_service_healthy": true,
  "base_url": "http://localhost:8081",
  "metrics": {...},
  "request_history_size": 1250,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Logging

The service provides structured logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Example log messages
logger.info("LLM request completed", extra={
    "request_id": "req_123",
    "model": "gpt-4",
    "response_time": 2.45,
    "task_type": "sentiment_analysis"
})
```

## 🔒 Security and Rate Limiting

### Rate Limiting

- **Requests per minute**: 100 (configurable)
- **Rate limit window**: 60 seconds
- **Retry logic**: Exponential backoff
- **Circuit breaker**: Automatic service protection

### Authentication

```python
# API key authentication
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}
```

### Caching

- **Cache TTL**: 5 minutes (configurable)
- **Cache key**: MD5 hash of request parameters
- **Cache invalidation**: Automatic cleanup

## 🚀 Integration with Trading Platform

### Centralized API Integration

```python
import aiohttp
import json

async def centralized_llm_request():
    """Example of using the centralized LLM API with callbacks"""
    
    # Centralized request with trading action callback
    payload = {
        "operation": "signal",
        "data": {
            "symbol": "AAPL",
            "market_data": {
                "price": 150.25,
                "volume": 50000000,
                "change_24h": 2.5
            },
            "news_data": [
                {"title": "Apple beats earnings", "sentiment": "positive"}
            ],
            "technical_indicators": {
                "rsi": 65,
                "macd": "bullish"
            }
        },
        "model": "gpt-4",
        "callback_config": {
            "callback_type": "trading_action",
            "metadata": {"auto_execute": True}
        },
        "priority": 5,
        "use_cache": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8008/api/v1/llm", json=payload) as response:
            result = await response.json()
            
            print(f"Request ID: {result['request_id']}")
            print(f"Success: {result['success']}")
            print(f"Callback Queued: {result['callback_queued']}")
            
            if result['success']:
                print(f"Signal: {result['data']}")

### Direct Client Integration

```python
from src.services.llm_service.llm_client import LLMClient, CallbackConfig, CallbackType

# Initialize LLM client with callback support
llm_client = LLMClient(
    base_url="http://localhost:8081",
    enable_callbacks=True
)

# Create callback configuration
callback_config = CallbackConfig(
    callback_type=CallbackType.TRADING_ACTION,
    metadata={"auto_execute": True}
)

# Generate trading signal with callback
signal_response = await llm_client.generate_trading_signal(
    market_data=market_data,
    news_data=news_data,
    technical_indicators=indicators,
    callback_config=callback_config
)

# Process signal
if isinstance(signal_response, LLMResponse):
    signal_data = json.loads(signal_response.content)
    print(f"Signal generated: {signal_data}")
    print(f"Callback executed: {signal_response.callback_executed}")
```

### Risk Integration

```python
# Assess portfolio risk
risk_response = await llm_client.assess_risk(
    portfolio_data=portfolio,
    market_conditions=market_conditions
)

# Apply risk controls
if isinstance(risk_response, LLMResponse):
    risk_data = json.loads(risk_response.content)
    if risk_data['risk_level'] == 'HIGH':
        await apply_risk_controls(portfolio)
```

### News Integration

```python
# Analyze news sentiment
sentiment_response = await llm_client.analyze_sentiment(
    text=news_article,
    context="Earnings season"
)

# Update trading decisions
if isinstance(sentiment_response, LLMResponse):
    sentiment_data = json.loads(sentiment_response.content)
    if sentiment_data['sentiment'] == 'positive':
        await adjust_position_sizing(symbol, 'increase')
```

## 🧪 Testing

### Unit Tests

```bash
# Run LLM service tests
pytest tests/unit/test_llm_service.py -v

# Run LLM client tests
pytest tests/unit/test_llm_client.py -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/test_llm_integration.py -v

# Test with real LLM service
pytest tests/integration/test_llm_end_to_end.py -v
```

### Load Testing

```bash
# Run load tests
locust -f tests/load/llm_load_test.py --host=http://localhost:8008
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Timeout**
   ```bash
   # Check LLM service connectivity
   curl -v http://localhost:8081/openapi.json
   
   # Check network connectivity
   ping localhost
   ```

2. **Rate Limiting**
   ```bash
   # Check rate limit status
   curl http://localhost:8008/metrics | jq '.llm_metrics.rate_limit_remaining'
   ```

3. **Service Health**
   ```bash
   # Check service health
   curl http://localhost:8008/health
   
   # Check logs
   kubectl logs -n trading-system deployment/llm-service
   ```

### Debug Commands

```bash
# Check LLM service logs
kubectl logs -n trading-system deployment/llm-service -f

# Check LLM worker logs
kubectl logs -n trading-system deployment/llm-worker -f

# Check RabbitMQ queues
kubectl exec -n trading-system deployment/rabbitmq -- rabbitmqctl list_queues

# Check service metrics
curl http://localhost:8008/metrics | jq '.'
```

## 📚 API Documentation

### OpenAPI Specification

The LLM service provides automatic API documentation:

- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc
- **OpenAPI JSON**: http://localhost:8008/openapi.json

### Example Requests

```python
import requests

# Sentiment analysis
response = requests.post("http://localhost:8008/sentiment", json={
    "text": "Apple reported strong earnings",
    "model": "gpt-3.5-turbo"
})

# Trading signal
response = requests.post("http://localhost:8008/signal", json={
    "symbol": "AAPL",
    "market_data": {...},
    "model": "gpt-4"
})

# Risk assessment
response = requests.post("http://localhost:8008/risk", json={
    "portfolio_data": {...},
    "market_conditions": {...},
    "model": "gpt-4"
})
```

## 🎯 Best Practices

### Performance Optimization

1. **Use Caching**: Enable caching for repeated requests
2. **Batch Requests**: Group similar requests together
3. **Model Selection**: Choose appropriate models for tasks
4. **Rate Limiting**: Respect rate limits and implement backoff

### Error Handling

1. **Retry Logic**: Implement exponential backoff
2. **Circuit Breaker**: Protect against service failures
3. **Fallback Strategies**: Provide alternative responses
4. **Monitoring**: Track error rates and response times

### Security

1. **API Keys**: Use secure API key management
2. **Input Validation**: Validate all inputs
3. **Rate Limiting**: Prevent abuse
4. **Logging**: Log security events

---

**The LLM Service Integration provides powerful AI capabilities to enhance trading decisions with real-time intelligence and analysis.** 🚀 