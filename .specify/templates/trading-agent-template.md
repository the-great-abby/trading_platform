# Trading System Development Guidelines

## Project Context
This is a sophisticated algorithmic trading system with the following key components:

### Architecture
- **Microservices**: Strategy service, market data service, unified dashboards
- **Containerization**: Docker + Kubernetes deployment
- **Database**: PostgreSQL/TimescaleDB for time-series data, Redis for caching
- **Monitoring**: Prometheus metrics, Grafana dashboards

### Current Active Features
- **Paper Trading**: Running with Iron Condor, Regime Switching, Bollinger Bands strategies
- **Portfolio**: $2,000 initial capital, AMD/PYPL/INTC symbols
- **Risk Management**: 5% max risk per trade, 10% max position size
- **Port Management**: 11000-11999 range, tracked in PORT_MAP.md

## Development Rules

### Code Organization
- **Strategies**: `src/strategies/` following established patterns
- **Services**: `services/{service-name}/` for microservices
- **Configuration**: Centralized in `src/utils/trading_config.py`
- **Deployments**: `k8s/` for Kubernetes manifests
- **Testing**: Comprehensive tests in `tests/` directory

### Trading-Specific Requirements
- **Risk Management**: Every feature must include risk controls
- **Backtesting**: All strategies must be backtestable
- **Options Focus**: Support for Iron Condor, Covered Calls, Cash-Secured Puts
- **Real-time Data**: Integration with Polygon/Alpha Vantage APIs
- **Monitoring**: Structured logging and metrics collection

### Python Standards
- **Async**: Use `asyncio` for I/O-bound operations
- **Type Hints**: Required for all functions
- **Testing**: pytest with async support
- **Logging**: Structured logging with context
- **Error Handling**: Meaningful error messages with debugging info

### Infrastructure Standards
- **Kubernetes**: All services deployed via K8s
- **Health Checks**: Required for all services
- **Port Management**: Update PORT_MAP.md for new services
- **Security**: RBAC, network policies, secrets management
- **Monitoring**: Prometheus metrics, Grafana dashboards

### Trading Strategy Development
- **Base Classes**: Use established strategy base classes
- **Risk Controls**: Position sizing, stop-losses mandatory
- **Testing**: Mock data for backtesting, edge case testing
- **Documentation**: Clear strategy logic and parameters
- **Performance**: Transaction costs, realistic market conditions

### API Design
- **RESTful**: Follow REST principles for trading APIs
- **Versioning**: API versioning for backward compatibility
- **Documentation**: Comprehensive API docs with examples
- **Authentication**: Required for all trading endpoints
- **Error Handling**: Proper HTTP status codes

## Common Patterns

### Strategy Implementation
```python
from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal

class MyStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(name="MyStrategy", **kwargs)
        # Initialize strategy parameters
        
    def generate_signal(self, data: pd.DataFrame) -> TradeSignal:
        # Implement strategy logic
        pass
```

### Service Structure
```python
# services/{service-name}/main.py
from fastapi import FastAPI
import asyncio

app = FastAPI(title="Service Name")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/endpoint")
async def endpoint():
    # Implementation
    pass
```

### Kubernetes Deployment
```yaml
# k8s/{service-name}.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-name
  template:
    metadata:
      labels:
        app: service-name
    spec:
      containers:
      - name: service-name
        image: localhost:32000/service-name:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://..."
```

## Testing Requirements

### Unit Tests
- Test all public functions
- Mock external dependencies
- Use pytest with async support
- Aim for high coverage

### Integration Tests
- Test service interactions
- Test database operations
- Test API endpoints
- Test strategy execution

### Backtesting Tests
- Test strategy performance
- Test risk management
- Test edge cases
- Validate against historical data

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Docker image built and tagged
- [ ] Kubernetes manifests updated
- [ ] PORT_MAP.md updated
- [ ] Configuration validated

### Post-Deployment
- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Logs accessible
- [ ] Performance monitoring active
- [ ] Rollback plan ready

## Common Commands

### Development
```bash
# Run tests
pytest tests/

# Build Docker image
docker build -t localhost:32000/service-name:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/service-name.yaml

# Check logs
kubectl logs -n trading-system deployment/service-name

# Update port map
python scripts/update_paper_trading_status.py
```

### Trading Operations
```bash
# Check paper trading status
curl -s http://localhost:11115/api/paper-trading/status

# Start paper trading
curl -X POST http://localhost:11115/api/paper-trading/start -d '{...}'

# Check service health
curl -s http://localhost:{port}/health
```

## Error Handling

### Common Issues
- **Port Conflicts**: Use 11000-11999 range, update PORT_MAP.md
- **Memory Issues**: Check resource limits in K8s manifests
- **Database Connections**: Verify DATABASE_URL and network policies
- **API Failures**: Implement proper error handling and fallbacks
- **Strategy Failures**: Include comprehensive error logging

### Debugging
- Check Kubernetes logs: `kubectl logs -n trading-system deployment/{service}`
- Check port forwards: `ps aux | grep "kubectl port-forward"`
- Check service health: `curl -s http://localhost:{port}/health`
- Check paper trading: `curl -s http://localhost:11115/api/paper-trading/status`

This template should be used as a reference for all trading system development work.


