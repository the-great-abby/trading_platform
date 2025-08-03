# Trading System Metrics Implementation Plan

## Overview
Comprehensive plan to add Prometheus metrics to all trading system services for Grafana dashboards.

## Current Status
- ✅ Infrastructure metrics (CPU, Memory, Disk)
- ✅ Basic service health checks
- ❌ Trading-specific metrics
- ❌ Worker/job metrics
- ❌ Strategy performance metrics

## Implementation Priority

### Phase 1: Core Trading Metrics (High Priority)
**Services to instrument:**
1. **trading-service** - Order processing, P&L, positions
2. **strategy-service** - Strategy performance, signals
3. **portfolio-service** - Portfolio metrics, allocation
4. **risk-service** - Risk exposure, limits

**Key metrics:**
```python
# Trading metrics
trading_orders_total{service="trading-service", status="success|failed"}
trading_order_latency_seconds{service="trading-service"}
trading_pnl_total{service="trading-service"}
trading_positions_active{service="trading-service"}

# Strategy metrics
strategy_signals_generated{strategy="rsi|macd|bollinger"}
strategy_win_rate{strategy="rsi|macd|bollinger"}
strategy_sharpe_ratio{strategy="rsi|macd|bollinger"}
```

### Phase 2: Data Pipeline Metrics (Medium Priority)
**Services to instrument:**
1. **market-data-service** - Data requests, latency, cache
2. **data-processing-service** - Processing jobs, errors
3. **market-data-worker** - Worker metrics, queue status

**Key metrics:**
```python
# Market data metrics
market_data_requests_total{service="market-data-service"}
market_data_latency_seconds{service="market-data-service"}
market_data_cache_hit_ratio{service="market-data-service"}

# Processing metrics
data_processing_jobs_total{service="data-processing-service"}
data_processing_latency_seconds{service="data-processing-service"}
```

### Phase 3: Worker & Job Metrics (Medium Priority)
**Services to instrument:**
1. **backtest-api** - Backtest jobs, completion rates
2. **llm-worker** - LLM requests, response times
3. **end-of-day-backtest-cronjob** - Scheduled job metrics

**Key metrics:**
```python
# Job metrics
backtest_jobs_total{service="backtest-api"}
backtest_jobs_completed{service="backtest-api"}
backtest_duration_seconds{service="backtest-api"}

# Worker metrics
worker_jobs_processed_total{worker="llm-worker"}
worker_processing_time_seconds{worker="llm-worker"}
```

### Phase 4: AI/LLM Metrics (Low Priority)
**Services to instrument:**
1. **llm-service** - LLM requests, tokens, errors
2. **ai-analysis-service** - AI decisions, confidence scores

**Key metrics:**
```python
# LLM metrics
llm_requests_total{service="llm-service"}
llm_response_time_seconds{service="llm-service"}
llm_tokens_processed_total{service="llm-service"}

# AI decision metrics
ai_decisions_total{service="ai-analysis-service"}
ai_decisions_approved{service="ai-analysis-service"}
ai_confidence_scores{service="ai-analysis-service"}
```

## Implementation Steps

### Step 1: Add Prometheus Client to Services
```python
# Add to requirements.txt
prometheus-client==0.19.0

# Add to each service
from prometheus_client import Counter, Gauge, Histogram, generate_latest
```

### Step 2: Create Metrics Classes
```python
# Example: trading_metrics.py
class TradingMetrics:
    def __init__(self):
        self.orders_total = Counter('trading_orders_total', 'Total orders processed', ['status'])
        self.order_latency = Histogram('trading_order_latency_seconds', 'Order processing latency')
        self.pnl_total = Gauge('trading_pnl_total', 'Total P&L')
        self.positions_active = Gauge('trading_positions_active', 'Active positions')
```

### Step 3: Instrument Key Functions
```python
# Example: Instrument order processing
@trading_metrics.order_latency.time()
def process_order(order):
    try:
        # Process order
        trading_metrics.orders_total.labels(status='success').inc()
        return result
    except Exception as e:
        trading_metrics.orders_total.labels(status='failed').inc()
        raise
```

### Step 4: Add Metrics Endpoints
```python
# Add to each service
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Step 5: Update Prometheus Configuration
```yaml
# Add to prometheus.yml
scrape_configs:
  - job_name: 'trading-services'
    static_configs:
      - targets: ['trading-service:80', 'strategy-service:80', 'portfolio-service:80']
```

## Grafana Dashboard Templates

### Dashboard 1: Trading Overview
- **Panels:**
  - Orders per minute (Counter)
  - P&L over time (Gauge)
  - Active positions (Gauge)
  - Order latency (Histogram)
  - Win rate by strategy (Gauge)

### Dashboard 2: System Health
- **Panels:**
  - Service health status (Gauge)
  - Response times (Histogram)
  - Error rates (Counter)
  - CPU/Memory usage (Gauge)

### Dashboard 3: Data Pipeline
- **Panels:**
  - Market data requests (Counter)
  - Processing jobs (Counter)
  - Cache hit ratio (Gauge)
  - Worker queue depth (Gauge)

### Dashboard 4: Strategy Performance
- **Panels:**
  - Strategy signals (Counter)
  - Win rates by strategy (Gauge)
  - Sharpe ratios (Gauge)
  - Maximum drawdown (Gauge)

## Next Steps

1. **Start with Phase 1** - Implement core trading metrics
2. **Create metrics classes** for each service type
3. **Add instrumentation** to key functions
4. **Test metrics endpoints** for each service
5. **Update Prometheus config** to scrape new endpoints
6. **Create Grafana dashboards** for visualization

## Success Criteria

- [ ] All core services expose `/metrics` endpoints
- [ ] Prometheus scrapes all trading service metrics
- [ ] Grafana dashboards show real-time trading data
- [ ] Alerts configured for critical metrics
- [ ] Historical data available for analysis 