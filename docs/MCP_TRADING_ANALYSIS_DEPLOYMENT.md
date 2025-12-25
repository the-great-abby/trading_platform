# MCP Trading Strategy Analysis - Deployment Guide

## 📋 What Was Built

A comprehensive Trading Strategy Analysis Tool that integrates with your existing trading system APIs to provide real-time strategy analysis and performance monitoring through the MCP (Model Context Protocol) service.

### Key Features

✅ **Active Strategy Monitoring** - View currently enabled strategies from configuration  
✅ **Backtest Performance Analysis** - Historical strategy performance from backtest API  
✅ **Live Trading Performance** - Real P&L and metrics from database  
✅ **Strategy Comparison** - Side-by-side comparison of multiple strategies  
✅ **Position Tracking** - Current open positions by strategy  
✅ **Portfolio Analytics** - Risk metrics and portfolio-level analytics  
✅ **Top Performers** - Identify best strategies by various metrics  

### Integration Points

The tool seamlessly integrates with:
- **Backtest API** (port 10001) - Strategy backtest results
- **Portfolio Service** (port 8000) - Portfolio management
- **Analytics Service** (port 8000) - Risk and performance metrics
- **TimescaleDB** - Direct database queries for trade history
- **Configuration Files** - Live trading strategy configuration

## 🏗️ Architecture

```
MCP Service (Port 8000)
├── Trading Strategy Analysis Tool
│   ├── Active Strategy Reader (YAML config)
│   ├── Backtest API Client (HTTP)
│   ├── Portfolio API Client (HTTP)
│   ├── Analytics API Client (HTTP)
│   └── Database Client (PostgreSQL)
│
└── 8 New REST Endpoints
    ├── GET /api/mcp/trading/strategies
    ├── GET /api/mcp/trading/strategies/active
    ├── GET /api/mcp/trading/strategies/performance/backtest
    ├── GET /api/mcp/trading/strategies/performance/live
    ├── GET /api/mcp/trading/strategies/comparison
    ├── GET /api/mcp/trading/strategies/top
    ├── GET /api/mcp/trading/positions
    └── GET /api/mcp/trading/analytics
```

## 📦 Files Created/Modified

### New Files
1. `services/mcp-service/mcp_tools/trading_strategy_analysis_tool.py` (700+ lines)
   - Core trading strategy analysis logic
   - API integration with existing services
   - Database queries for trade data

2. `services/mcp-service/TRADING_STRATEGY_ANALYSIS_GUIDE.md`
   - Comprehensive documentation
   - API reference
   - Usage examples

3. `docs/MCP_TRADING_ANALYSIS_QUICK_REF.md`
   - Quick reference card
   - Common queries
   - Pro tips and shortcuts

4. `docs/MCP_TRADING_ANALYSIS_DEPLOYMENT.md` (this file)
   - Deployment instructions
   - Testing guide

### Modified Files
1. `services/mcp-service/main.py`
   - Added import for TradingStrategyAnalysisTool
   - Initialized trading_strategy_tool instance
   - Added 8 new API endpoint handlers
   - Updated tools list in /api/mcp/tools

## 🚀 Deployment Steps

### Prerequisites

```bash
# Ensure you're in the project root
cd /Users/abby/code/trading

# Verify you have access to the Kubernetes cluster
kubectl get pods -n trading-system
```

### Option 1: Local Testing (Development)

```bash
# 1. Install dependencies (if not already installed)
cd services/mcp-service
pip install -r requirements.txt

# 2. Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trading_db
export DB_USER=postgres
export DB_PASSWORD=password
export BACKTEST_API_URL=http://localhost:10001
export PORTFOLIO_API_URL=http://localhost:8000
export ANALYTICS_API_URL=http://localhost:8000

# 3. Port forward required services (in separate terminals)
kubectl port-forward -n trading-system svc/timescaledb-service 5432:5432
kubectl port-forward -n trading-system svc/backtest-api 10001:10001
kubectl port-forward -n trading-system svc/analytics-service 8000:8000

# 4. Run MCP service locally
python main.py
```

### Option 2: Kubernetes Deployment (Production)

```bash
# 1. Build new Docker image
cd /Users/abby/code/trading
docker build -t localhost:32000/mcp-service:latest -f services/mcp-service/Dockerfile services/mcp-service/

# 2. Push to local registry
docker push localhost:32000/mcp-service:latest

# 3. Restart MCP service deployment
kubectl rollout restart deployment/mcp-service -n trading-system

# 4. Wait for rollout to complete
kubectl rollout status deployment/mcp-service -n trading-system

# 5. Verify pod is running
kubectl get pods -n trading-system | grep mcp-service

# 6. Check logs for errors
kubectl logs -n trading-system deployment/mcp-service --tail=50
```

### Option 3: Using Makefile (Recommended)

If you have semantic versioning Makefile targets:

```bash
# Build and deploy MCP service
make deploy-mcp

# Or build only
make build-mcp
```

## ✅ Testing

### 1. Basic Health Check

```bash
# Port forward MCP service
kubectl port-forward -n trading-system svc/mcp-service 8000:8000

# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "mcp-service",
#   "timestamp": "2025-10-23T12:00:00Z",
#   "version": "1.0.0",
#   "automation": {...}
# }
```

### 2. Verify New Tool is Registered

```bash
curl http://localhost:8000/api/mcp/tools | jq '.tools[] | select(.name == "trading_strategy")'

# Expected output:
# {
#   "name": "trading_strategy",
#   "description": "Trading strategy analysis and performance monitoring",
#   "endpoints": [...]
# }
```

### 3. Test Active Strategies Endpoint

```bash
curl http://localhost:8000/api/mcp/trading/strategies/active | jq

# Expected: JSON with active_strategies object
```

### 4. Test Comprehensive Analysis

```bash
curl http://localhost:8000/api/mcp/trading/strategies | jq '.summary'

# Expected: Summary with total_strategies, active_strategies, etc.
```

### 5. Test Live Performance

```bash
curl "http://localhost:8000/api/mcp/trading/strategies/performance/live?days=7" | jq

# Expected: Strategy performance data from database
```

### 6. Test Current Positions

```bash
curl http://localhost:8000/api/mcp/trading/positions | jq

# Expected: Open positions grouped by strategy
```

### 7. Test Strategy Comparison

```bash
curl http://localhost:8000/api/mcp/trading/strategies/comparison | jq '.comparison[0]'

# Expected: Comparison data for strategies
```

### 8. Test Top Performers

```bash
# By P&L
curl "http://localhost:8000/api/mcp/trading/strategies/top?metric=pnl&limit=3" | jq

# By Win Rate
curl "http://localhost:8000/api/mcp/trading/strategies/top?metric=win_rate&limit=3" | jq

# Expected: Top strategies sorted by metric
```

## 🧪 Integration Tests

Create a test script:

```bash
#!/bin/bash
# test_mcp_trading_analysis.sh

BASE_URL="http://localhost:8000"
PASS=0
FAIL=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_key=$3
    
    echo "Testing: $name"
    response=$(curl -s "$url")
    
    if echo "$response" | jq -e ".$expected_key" > /dev/null 2>&1; then
        echo "✅ PASS: $name"
        ((PASS++))
    else
        echo "❌ FAIL: $name"
        echo "Response: $response"
        ((FAIL++))
    fi
    echo ""
}

echo "=== MCP Trading Strategy Analysis Tests ==="
echo ""

test_endpoint "Health Check" "$BASE_URL/health" "status"
test_endpoint "Active Strategies" "$BASE_URL/api/mcp/trading/strategies/active" "success"
test_endpoint "Comprehensive Analysis" "$BASE_URL/api/mcp/trading/strategies" "summary"
test_endpoint "Backtest Performance" "$BASE_URL/api/mcp/trading/strategies/performance/backtest" "success"
test_endpoint "Live Performance" "$BASE_URL/api/mcp/trading/strategies/performance/live" "success"
test_endpoint "Current Positions" "$BASE_URL/api/mcp/trading/positions" "success"
test_endpoint "Strategy Comparison" "$BASE_URL/api/mcp/trading/strategies/comparison" "success"
test_endpoint "Top Performers" "$BASE_URL/api/mcp/trading/strategies/top" "success"
test_endpoint "Portfolio Analytics" "$BASE_URL/api/mcp/trading/analytics" "success"

echo "=== Test Summary ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [ $FAIL -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed"
    exit 1
fi
```

Run the test script:

```bash
chmod +x test_mcp_trading_analysis.sh
./test_mcp_trading_analysis.sh
```

## 🔍 Monitoring

### Check Service Logs

```bash
# Real-time logs
kubectl logs -f -n trading-system deployment/mcp-service

# Recent errors
kubectl logs -n trading-system deployment/mcp-service --tail=100 | grep -i error

# Trading analysis specific logs
kubectl logs -n trading-system deployment/mcp-service --tail=100 | grep -i "trading"
```

### Check Service Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Service status
curl http://localhost:8000/api/mcp/services/status
```

## 🐛 Troubleshooting

### Issue: "Database connection failed"

**Solution:**
```bash
# Check database pod
kubectl get pods -n trading-system | grep timescale

# Test database connection
kubectl exec -it -n trading-system deployment/mcp-service -- \
  psql -h timescaledb-service -U postgres -d trading_db -c "SELECT 1;"

# Check environment variables
kubectl exec -it -n trading-system deployment/mcp-service -- env | grep DB_
```

### Issue: "API timeout" or "Service unavailable"

**Solution:**
```bash
# Check if services are running
kubectl get svc -n trading-system | grep -E "backtest-api|analytics-service|portfolio-service"

# Test service connectivity from MCP pod
kubectl exec -it -n trading-system deployment/mcp-service -- \
  curl http://backtest-api:10001/health
```

### Issue: "No strategies found"

**Solution:**
```bash
# Check if config file exists
kubectl exec -it -n trading-system deployment/mcp-service -- \
  ls -la /app/config/live_trading_strategies.yaml

# Verify config is valid YAML
kubectl exec -it -n trading-system deployment/mcp-service -- \
  cat /app/config/live_trading_strategies.yaml
```

### Issue: Import errors

**Solution:**
```bash
# Check if module exists
kubectl exec -it -n trading-system deployment/mcp-service -- \
  python -c "from mcp_tools.trading_strategy_analysis_tool import TradingStrategyAnalysisTool; print('OK')"

# Rebuild and redeploy
docker build -t localhost:32000/mcp-service:latest -f services/mcp-service/Dockerfile services/mcp-service/
docker push localhost:32000/mcp-service:latest
kubectl rollout restart deployment/mcp-service -n trading-system
```

## 📊 Performance Benchmarks

Expected response times (approximate):

| Endpoint | Response Time | Notes |
|----------|--------------|-------|
| `/strategies/active` | 50-100ms | Reads from config file |
| `/strategies/performance/backtest` | 200-500ms | Queries database + API call |
| `/strategies/performance/live` | 300-700ms | Complex database query |
| `/positions` | 100-300ms | Database query |
| `/strategies` (comprehensive) | 1-2s | Multiple parallel API calls |
| `/strategies/comparison` | 1-2s | Aggregates multiple data sources |

## 🔐 Security Considerations

1. **Internal Use Only** - Service is designed for internal cluster access
2. **No Authentication** - Currently no auth required (internal service)
3. **Database Access** - Uses read-only queries (no INSERT/UPDATE/DELETE)
4. **API Calls** - All calls are to internal services within cluster
5. **Configuration** - Sensitive data should be in Kubernetes secrets

## 🎯 Next Steps

1. **Monitor Usage** - Track which endpoints are most used
2. **Optimize Queries** - Add caching for frequently accessed data
3. **Add Alerts** - Set up alerts for strategy underperformance
4. **Dashboard Integration** - Create UI visualizations
5. **Natural Language** - Add LLM integration for conversational queries
6. **Automated Actions** - Enable strategy enable/disable via MCP
7. **Historical Trends** - Add time-series analysis

## 📚 Related Documentation

- [Trading Strategy Analysis Guide](../services/mcp-service/TRADING_STRATEGY_ANALYSIS_GUIDE.md) - Comprehensive API reference
- [Quick Reference Card](./MCP_TRADING_ANALYSIS_QUICK_REF.md) - Common queries and tips
- [MCP Service Documentation](../services/mcp-service/README.md) - MCP service overview
- [Port Mapping Guide](./PORT_MAPPING.md) - Service port allocations

## 🤝 Support

**Questions?** Ask Orion (that's me! 🤖)

**Issues?** Check the logs first:
```bash
kubectl logs -n trading-system deployment/mcp-service --tail=100
```

**Feature Requests?** Let's discuss and implement!

---

**Deployment Checklist:**

- [ ] Docker image built
- [ ] Image pushed to registry
- [ ] Deployment restarted
- [ ] Pod is running healthy
- [ ] Health endpoint returns 200
- [ ] All 8 new endpoints return data
- [ ] Integration tests pass
- [ ] Logs show no errors
- [ ] Documentation reviewed
- [ ] Team notified

**Congratulations! Your MCP Trading Strategy Analysis Tool is deployed! 🎉**

