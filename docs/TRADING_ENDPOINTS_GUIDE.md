# 📊 Trading Endpoints Guide - Orders, Trades & Metrics

## Overview

This guide shows you how to access orders, trades, and metrics from your trading system after deprecating the trading-engine service.

**Good News**: All endpoints are available in your existing services! No functionality was lost.

## 🎯 Available Endpoints

### 1. **Paper Trading Service** (Port 8080 or 11190)

#### Get Orders
```bash
# Get all orders for an account
curl "http://localhost:8080/api/v1/trading/orders?account_id=paper_account"

# Filter by status
curl "http://localhost:8080/api/v1/trading/orders?account_id=paper_account&status_filter=filled&limit=50"
```

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "order_id": "paper_order_1728345678",
      "symbol": "AAPL",
      "strategy": "IRON_CONDOR",
      "status": "filled",
      "total_quantity": 4,
      "average_price": 2.50,
      "estimated_premium": 250.00,
      "created_at": "2025-10-07T12:00:00Z"
    }
  ],
  "total_count": 1
}
```

#### Submit Orders
```bash
curl -X POST "http://localhost:8080/api/v1/trading/orders?account_id=paper_account" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SPY",
    "strategy": "IRON_CONDOR",
    "order_type": "LIMIT",
    "legs": [
      {"action": "SELL", "option_type": "CALL", "strike_price": 450, "quantity": 1, "premium": 2.50}
    ],
    "estimated_premium": 250.00,
    "estimated_risk": 1000.00
  }'
```

#### Metrics
```bash
curl "http://localhost:8080/metrics"
```

### 2. **Unified Trading Dashboard** (Port 11115)

#### Get Recent Trades
```bash
# Get recent trades from database
curl "http://localhost:11115/api/trades/recent"
```

**Response:**
```json
{
  "trades": [
    {
      "id": 123,
      "symbol": "AAPL",
      "action": "BUY",
      "quantity": 10,
      "price": 180.50,
      "strategy": "IronCondor",
      "pnl": 125.00,
      "timestamp": "2025-10-07T12:00:00Z"
    }
  ],
  "count": 1
}
```

#### Get Orders
```bash
curl "http://localhost:11115/api/orders"
```

#### Get Paper Trading Trades
```bash
curl "http://localhost:11115/api/paper-trading/trades"
```

### 3. **Strategy Service** (Port 11001)

#### Metrics for Prometheus/Grafana
```bash
curl "http://localhost:11001/metrics"
```

**Returns Prometheus format:**
```
# HELP strategy_requests_total Total number of strategy requests
# TYPE strategy_requests_total counter
strategy_requests_total 42.0

# HELP strategy_request_duration_seconds Time spent on strategy requests
# TYPE strategy_request_duration_seconds histogram
strategy_request_duration_seconds_bucket{le="0.1"} 10.0
strategy_request_duration_seconds_bucket{le="0.5"} 35.0
```

#### Health Check
```bash
curl "http://localhost:11001/health"
```

### 4. **Market Data Service** (Port 11084)

#### Metrics
```bash
curl "http://localhost:11084/metrics"
```

### 5. **Risk Management Service** (Port 11182)

#### Metrics
```bash
# First set up port forward
kubectl port-forward svc/risk-management-service 11182:80 -n trading-system &

# Then get metrics
curl "http://localhost:11182/metrics"
```

## 📈 Grafana Integration

### Step 1: Set Up Prometheus to Scrape Your Services

Create a Prometheus config or add to existing `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'paper-trading'
    static_configs:
      - targets: ['paper-trading-k8s-service.trading-system.svc.cluster.local:9090']
    
  - job_name: 'strategy-service'
    static_configs:
      - targets: ['strategy-service.trading-system.svc.cluster.local:80']
    metrics_path: '/metrics'
    
  - job_name: 'market-data'
    static_configs:
      - targets: ['market-data-service.trading-system.svc.cluster.local:11084']
    metrics_path: '/metrics'
    
  - job_name: 'risk-management'
    static_configs:
      - targets: ['risk-management-service.trading-system.svc.cluster.local:9090']
```

### Step 2: Deploy Prometheus

```bash
# Apply Prometheus configuration
kubectl apply -f monitoring/prometheus.yml

# Port forward Prometheus
kubectl port-forward svc/prometheus 11190:9090 -n trading-system &
```

### Step 3: Configure Grafana Data Source

```bash
# Port forward Grafana (if not already running)
kubectl port-forward svc/grafana 11102:3000 -n trading-system &

# Open Grafana
open http://localhost:11102
```

**Add Prometheus Data Source:**
1. Go to Configuration → Data Sources
2. Add Prometheus
3. URL: `http://prometheus.trading-system.svc.cluster.local:9090`
4. Save & Test

### Step 4: Create Dashboards

**Trading Metrics Dashboard:**
- Total trades: `sum(strategy_requests_total)`
- Request duration: `strategy_request_duration_seconds`
- Active orders: Query from paper-trading service
- P&L: Query from unified-trading-dashboard

## 🔧 Quick Port Forward Setup

Create a script to start all necessary port forwards:

```bash
#!/bin/bash
# start-trading-ports.sh

# Kill existing port forwards
pkill -f "kubectl port-forward"

# Paper Trading Service
kubectl port-forward svc/paper-trading-k8s-service 11190:8080 -n trading-system &

# Strategy Service  
kubectl port-forward svc/strategy-service 11001:80 -n trading-system &

# Market Data Service
kubectl port-forward svc/market-data-service 11084:11084 -n trading-system &

# Unified Trading Dashboard
kubectl port-forward svc/unified-trading-dashboard 11115:80 -n trading-system &

# Prometheus
kubectl port-forward svc/prometheus 11190:9090 -n trading-system &

# Grafana
kubectl port-forward svc/grafana 11102:3000 -n trading-system &

echo "✅ All trading ports forwarded!"
```

## 📊 Database Queries for Historical Data

If you need historical trades/orders, query TimescaleDB directly:

```sql
-- Get recent trades
SELECT * FROM trades 
ORDER BY timestamp DESC 
LIMIT 100;

-- Get recent orders
SELECT * FROM paper_trading_orders 
ORDER BY created_at DESC 
LIMIT 100;

-- Get P&L summary
SELECT 
  symbol,
  strategy,
  SUM(pnl) as total_pnl,
  COUNT(*) as trade_count
FROM trades
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY symbol, strategy
ORDER BY total_pnl DESC;
```

**Connect to database:**
```bash
# Port forward database
kubectl port-forward svc/timescaledb 5432:5432 -n trading-system &

# Connect with psql
psql -h localhost -U trading_user -d trading_bot
```

## 🎯 Summary: What Replaced Trading-Engine

| Trading-Engine Feature | Replacement Service | Endpoint |
|----------------------|-------------------|----------|
| `/trades` | Unified Trading Dashboard | `http://localhost:11115/api/trades/recent` |
| `/orders` | Paper Trading Service | `http://localhost:8080/api/v1/trading/orders` |
| `/metrics` | Multiple Services | Strategy: `http://localhost:11001/metrics`<br>Paper Trading: `http://localhost:8080/metrics`<br>Market Data: `http://localhost:11084/metrics` |
| `/stats` | Unified Trading Dashboard | `http://localhost:11115/api/paper-trading/status` |
| Order Management | Paper Trading Service | POST `http://localhost:8080/api/v1/trading/orders` |
| Risk Management | Risk Management Service | `http://localhost:11182/api/risk/*` |

## ✅ Result

**You have MORE endpoints available now** than the trading-engine provided:
- ✅ Multiple services with `/metrics` for Grafana
- ✅ Database-backed orders and trades with persistence
- ✅ Comprehensive trading dashboard
- ✅ Better separation of concerns
- ✅ No crash-looping pods wasting resources!

---

*Last Updated: 2025-10-07*

