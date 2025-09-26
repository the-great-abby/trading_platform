# Elliott Wave Analysis Service - Quick Start Guide

## Overview

The Elliott Wave Analysis Service provides advanced Elliott Wave pattern detection with options trading integration. This guide will help you deploy, configure, and use the service.

## Prerequisites

- Kubernetes cluster (Docker Desktop Kubernetes recommended)
- kubectl configured
- Docker (for building images)

## Deployment

### 1. Build Docker Image

```bash
cd /Users/abby/code/trading/services/elliott-wave-service
docker build -t elliott-wave-service:latest .
```

### 2. Deploy to Kubernetes

```bash
cd /Users/abby/code/trading
kubectl apply -f k8s/elliott-wave-service.yaml
```

### 3. Verify Deployment

```bash
kubectl get pods -n trading-system -l app=elliott-wave-service
kubectl get svc -n trading-system elliott-wave-service
```

### 4. Port Forward for Local Access

```bash
kubectl port-forward -n trading-system service/elliott-wave-service 11085:8000
```

## Configuration

### Environment Variables

The service can be configured using environment variables:

```yaml
env:
- name: ELLIOTT_WAVE_TIMEOUT
  value: "30"
- name: ELLIOTT_WAVE_MIN_CONFIDENCE
  value: "0.6"
- name: ELLIOTT_WAVE_TIMEFRAME
  value: "15m"
- name: MARKET_DATA_SERVICE_URL
  value: "http://market-data-service.trading-system.svc.cluster.local:8000"
```

### Tracked Symbols

Default tracked symbols: `["SPY", "QQQ", "AAPL"]`

To modify tracked symbols, update the `TRACKED_SYMBOLS` list in `main.py`.

## Usage

### 1. Health Check

```bash
curl -X GET "http://localhost:11085/elliott-wave/health"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Elliott Wave Analysis",
  "timestamp": "2024-01-01T12:00:00",
  "market_data_available": true,
  "options_integration": true
}
```

### 2. Analyze Single Symbol

```bash
curl -X GET "http://localhost:11085/elliott-wave/analyze/SPY"
```

### 3. Analyze All Symbols

```bash
curl -X GET "http://localhost:11085/elliott-wave/analyze-all"
```

### 4. Get Options Analysis

```bash
curl -X GET "http://localhost:11085/elliott-wave/options-analysis/SPY"
```

### 5. Get Options Analysis for All Symbols

```bash
curl -X GET "http://localhost:11085/elliott-wave/options-analysis-all"
```

## API Documentation

Once the service is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:11085/docs
- **ReDoc**: http://localhost:11085/redoc

## Testing

### Run Unit Tests

```bash
cd /Users/abby/code/trading
python -m pytest tests/unit/test_pattern_detection.py -v
python -m pytest tests/unit/test_fibonacci_calculations.py -v
python -m pytest tests/unit/test_options_integration.py -v
```

### Run Integration Tests

```bash
python -m pytest tests/integration/test_pattern_detection.py -v
python -m pytest tests/integration/test_options_integration.py -v
```

### Run Contract Tests

```bash
python -m pytest tests/contract/test_elliott_wave_contracts.py -v
```

### Run Performance Tests

```bash
python -m pytest tests/performance/test_analysis_timing.py -v
```

## Monitoring

### Health Checks

The service provides health check endpoints:

- **Liveness Probe**: `/elliott-wave/health`
- **Readiness Probe**: `/elliott-wave/health`

### Logs

View service logs:

```bash
kubectl logs -f deployment/elliott-wave-service -n trading-system
```

### Metrics

The service logs structured metrics including:

- Analysis timing
- Pattern detection rates
- Signal generation counts
- Error rates

## Troubleshooting

### Common Issues

1. **Service not starting**
   - Check Kubernetes logs: `kubectl logs deployment/elliott-wave-service -n trading-system`
   - Verify image exists: `docker images | grep elliott-wave-service`

2. **Port forwarding issues**
   - Ensure port 11085 is not in use: `lsof -i :11085`
   - Check service status: `kubectl get svc elliott-wave-service -n trading-system`

3. **Analysis errors**
   - Check market data service connectivity
   - Verify symbol data availability
   - Review confidence thresholds

### Debug Mode

Enable debug logging:

```yaml
env:
- name: LOG_LEVEL
  value: "DEBUG"
```

## Performance Optimization

### Resource Limits

The service is configured with resource limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Scaling

To scale the service:

```bash
kubectl scale deployment elliott-wave-service -n trading-system --replicas=3
```

## Integration with Trading System

### Market Data Service

The service integrates with the existing market data service:

```python
MARKET_DATA_SERVICE_URL = "http://market-data-service.trading-system.svc.cluster.local:8000"
```

### Options Trading

The service generates signals for 12 options strategies:

- StraddleStrategy
- IronCondorStrategy
- CalendarSpreadStrategy
- ButterflySpreadStrategy
- VolatilityStrategy
- LongStrangleStrategy
- DiagonalSpreadStrategy
- CoveredCallStrategy

### Risk Management

Risk levels are automatically determined based on pattern confidence:

- **High Risk**: Confidence ≥0.8, Max position size 10%
- **Medium Risk**: Confidence ≥0.6, Max position size 5%
- **Low Risk**: Confidence ≥0.4, Max position size 2%

## Security

### CORS Configuration

The service is configured with permissive CORS for development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict CORS origins to specific domains.

### Error Handling

All errors are handled gracefully with appropriate HTTP status codes and error messages.

## Support

For issues or questions:

1. Check the logs: `kubectl logs deployment/elliott-wave-service -n trading-system`
2. Review the API documentation: http://localhost:11085/docs
3. Run the test suite to verify functionality
4. Check the health endpoint: http://localhost:11085/elliott-wave/health

## Next Steps

1. **Deploy the service** using the steps above
2. **Test the API endpoints** with the provided examples
3. **Integrate with your trading system** using the generated signals
4. **Monitor performance** and adjust configuration as needed
5. **Scale the service** based on your requirements

The Elliott Wave Analysis Service is now ready for production use! 🏴‍☠️
