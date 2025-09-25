# Strategy Service API Documentation

## Overview

The Strategy Service provides a FastAPI-based interface for running backtests and managing trading strategies. It supports both traditional stock strategies and advanced options strategies with comprehensive error handling and fallback mechanisms.

## Quick Start

### Running the Service

```bash
# Start the service
python main.py

# Service will be available at http://localhost:8000
```

### Health Check

```bash
curl http://localhost:8000/health
```

## API Endpoints

### Core Endpoints

#### `GET /`
**Description**: Service root endpoint  
**Response**: Service status message

```json
{
  "message": "Strategy Service is running"
}
```

#### `GET /health`
**Description**: Health check endpoint  
**Response**: Service health status

```json
{
  "status": "healthy"
}
```

#### `GET /ready`
**Description**: Readiness check endpoint  
**Response**: Service readiness status

```json
{
  "status": "ready"
}
```

#### `GET /metrics`
**Description**: Prometheus metrics endpoint  
**Response**: Metrics in Prometheus format

### Strategy Management

#### `POST /api/v1/strategies`
**Description**: Create a new strategy  
**Request Body**:
```json
{
  "name": "MyStrategy",
  "type": "momentum",
  "parameters": {
    "lookback_period": 14,
    "threshold": 70
  }
}
```

**Response**:
```json
{
  "message": "Strategy created",
  "strategy": {
    "name": "MyStrategy",
    "type": "momentum",
    "parameters": {
      "lookback_period": 14,
      "threshold": 70
    }
  }
}
```

### Backtesting

#### `POST /api/backtest/run`
**Description**: Run a comprehensive backtest  
**Request Body**:
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "strategies": ["IronCondor", "RSI", "MACD"]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Backtest completed successfully",
  "results": [
    {
      "name": "IronCondor",
      "total_return": 0.15,
      "sharpe_ratio": 1.8,
      "max_drawdown": 0.08,
      "win_rate": 0.65,
      "total_trades": 45,
      "profit_factor": 1.4
    },
    {
      "name": "RSI",
      "total_return": 0.12,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.12,
      "win_rate": 0.58,
      "total_trades": 32,
      "profit_factor": 1.1
    }
  ]
}
```

#### `POST /api/strategies/compare`
**Description**: Run comprehensive strategy comparison  
**Response**:
```json
{
  "success": true,
  "message": "Strategy comparison completed successfully. Check logs for detailed results."
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_ONLY` | `false` | Use only database data (no external APIs) |
| `USE_MOCK_DATA` | `false` | Use mock data for testing |
| `ENABLE_OPTIONS_STRATEGIES` | `true` | Enable options strategies |
| `ENABLE_LLM_EVALUATION` | `true` | Enable LLM trade evaluation |

### Container Configuration

The service automatically configures itself based on environment variables:

```python
# Containerized environment configuration
DATABASE_ONLY = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() in ('true', '1', 'yes')
ENABLE_OPTIONS_STRATEGIES = os.getenv('ENABLE_OPTIONS_STRATEGIES', 'true').lower() in ('true', '1', 'yes')
```

## Supported Strategies

### Traditional Strategies

- **RSI**: Relative Strength Index momentum strategy
- **MACD**: Moving Average Convergence Divergence strategy
- **SMA Crossover**: Simple Moving Average crossover strategy
- **Bollinger Bands**: Mean reversion strategy
- **Momentum**: Price momentum strategy
- **Mean Reversion**: Statistical mean reversion strategy
- **Volatility Breakout**: Volatility-based breakout strategy

### Options Strategies

- **Iron Condor**: Range-bound options strategy
- **Butterfly Spread**: Limited risk/reward options strategy
- **Calendar Spread**: Time decay options strategy
- **Covered Call**: Income generation strategy
- **Cash Secured Put**: Income generation strategy

### Advanced Strategies

- **Regime Switching**: Market regime adaptive strategy
- **Neural Network**: AI-based strategy
- **Quantum Momentum**: Advanced momentum strategy
- **Adaptive Momentum**: Self-adjusting momentum strategy

## Error Handling

### Graceful Degradation

The service implements multiple levels of fallback:

1. **Real Options Service**: Primary options data source
2. **Mock Options Service**: Fallback for testing/development
3. **Strategy Fallback**: Automatic fallback to stock-based strategies
4. **Minimal Service**: Last resort with empty data

### Error Response Format

```json
{
  "success": false,
  "error": "Strategy execution failed",
  "details": {
    "strategy": "IronCondor",
    "symbol": "AAPL",
    "error_type": "OptionsDataError",
    "recovery_suggestions": [
      "Use mock options data for backtesting",
      "Check options data service availability",
      "Verify symbol has options contracts available"
    ]
  }
}
```

### Common Error Codes

- `BACKTEST_ERROR`: Backtest execution failed
- `OPTIONS_DATA_ERROR`: Options data unavailable
- `STRATEGY_ERROR`: Strategy execution failed
- `VALIDATION_ERROR`: Request validation failed

## Performance

### Metrics

The service exposes Prometheus metrics:

- `strategy_requests_total`: Total strategy requests
- `strategy_request_duration_seconds`: Request duration histogram
- `backtest_executions_total`: Total backtest executions
- `options_data_requests_total`: Total options data requests

### Performance Targets

- **Single Strategy Backtest**: < 10 seconds
- **Batch Backtest** (5 symbols × 3 strategies): < 30 seconds
- **Memory Usage**: < 1GB for typical operations
- **API Response Time**: < 5 seconds for most requests

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **Contract Tests**: API contract validation
- **Performance Tests**: Load and stress testing

## Development

### Adding New Strategies

1. **Create Strategy Class**:
```python
from src.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, config=None):
        super().__init__("MyStrategy", config)
    
    async def generate_signal(self, symbol, data, historical_date=None):
        # Implementation
        pass
```

2. **Register Strategy**:
```python
# Add to strategy mapping in backtest engine
STRATEGY_MAPPING = {
    'MyStrategy': 'src.strategies.my_strategy.MyStrategy',
    # ... existing strategies
}
```

3. **Add Tests**:
```python
# Create test file
tests/unit/test_my_strategy.py
tests/integration/test_my_strategy_backtest.py
```

### Adding New Endpoints

1. **Define Request/Response Models**:
```python
class MyRequest(BaseModel):
    param1: str
    param2: int

class MyResponse(BaseModel):
    result: str
    success: bool
```

2. **Implement Endpoint**:
```python
@app.post("/api/my-endpoint")
async def my_endpoint(request: MyRequest):
    # Implementation
    return MyResponse(result="success", success=True)
```

3. **Add Documentation**:
Update this README with endpoint documentation.

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check with metrics
curl http://localhost:8000/metrics
```

### Logging

The service uses structured logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Metrics Collection

Prometheus metrics are automatically collected and exposed at `/metrics`.

## Troubleshooting

### Common Issues

1. **"No options data available"**
   - Check `ENABLE_OPTIONS_STRATEGIES` environment variable
   - Verify options service initialization
   - Review error logs for service failures

2. **"Backtest execution failed"**
   - Check market data availability
   - Verify strategy configuration
   - Review error logs for specific failures

3. **"Memory usage high"**
   - Reduce batch size for backtests
   - Check for memory leaks in strategies
   - Monitor container resource limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

```python
import cProfile
cProfile.run('await engine.run_backtest(...)')
```

## Security

### API Security

- Input validation on all endpoints
- Rate limiting (implemented via Prometheus metrics)
- Error message sanitization
- Structured logging for audit trails

### Data Security

- No sensitive data in logs
- Environment variable configuration
- Secure error handling
- Input sanitization

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strategy-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: strategy-service
  template:
    metadata:
      labels:
        app: strategy-service
    spec:
      containers:
      - name: strategy-service
        image: strategy-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_ONLY
          value: "true"
        - name: USE_MOCK_DATA
          value: "false"
```

## Changelog

### Version 1.1.0 (Current)

- Added comprehensive options strategy support
- Implemented mock options data generation
- Enhanced error handling and fallback mechanisms
- Added structured logging and metrics
- Improved containerized environment support
- Added strategy comparison endpoint

### Version 1.0.0

- Initial service implementation
- Basic backtesting functionality
- Traditional strategy support
- Prometheus metrics integration

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review service logs
3. Check Prometheus metrics
4. Verify environment configuration

---

*Last updated: 2025-09-20*


