# Live Trading Setup - Corrected Configuration

**Last Updated**: 2025-10-07 19:56:00 EST

## 🎯 Correct Live Trading Service

### ✅ **Production Live Trading Service**
- **Deployment**: `live-trading-service` in `default` namespace
- **Status**: ✅ Running (2/2 pods)
- **Configuration**: Real Public.com API integration
- **Port**: 8080
- **Data Source**: `live_trades` and `live_positions` tables

```bash
# Port forward to live trading service
kubectl port-forward -n default deployment/live-trading-service 11120:8080

# Health check
curl http://localhost:11120/health
```

### ❌ **Deprecated Paper Trading Service**
- **Deployment**: `paper-trading-k8s` in `trading-system` namespace
- **Status**: ❌ Scaled to 0 (was in CrashLoopBackOff)
- **Reason**: Misconfigured - had TRADING_MODE=paper but was calling real Public.com API
- **Data Source**: `paper_trading_orders` table (OPTIONS trades, not stocks)

## 📊 Your Live Trading Portfolio

### Current Positions (REAL Stock Trades)
```
AAPL:  1 share  @ $256.14 entry → $256.48 current (+$0.34 / +0.13%)
GOOGL: 1 share  @ $246.70 entry → $245.76 current (-$0.94 / -0.38%)
MSFT:  2 shares @ $522.96 entry → $523.98 current (+$2.04 / +0.20%)
QQQ:   4 shares @ $604.52 entry → $604.51 current (-$0.03 / -0.00%)

Total Portfolio: $4,001.41
Live P&L: +$1.41 since entry
```

### Account Details
- **Account ID**: `19c25392-8b61-4b71-a344-0eb04d275528`
- **Account Type**: CASH
- **Initial Capital**: $4,000.00
- **Cash Remaining**: $33.17
- **Equity**: $3,966.83
- **Total Value**: $4,000.00

## 🔧 Monitoring Setup

### Live Trading Monitor (Recommended)
```bash
# Single check with real-time prices
python3 live_trading_monitor.py single

# Continuous monitoring (every 5 minutes)
python3 live_trading_monitor.py continuous 5

# Or use Makefile
make live-trading-monitor
```

**Features**:
- ✅ Queries `live_trades` table (real stock trades)
- ✅ Shows both stored AND real-time market prices
- ✅ Displays position-by-position P&L
- ✅ Tracks strategy performance
- ✅ Shows exit strategies and risk management

### API-Based Monitor (Fixed)
```bash
# Quick status
make live-trading-monitor-api
```

**Note**: This was previously showing paper trading OPTIONS orders. Now fixed to query `live_trades` table.

## 🗄️ Database Tables Explained

### Live Trading Tables (STOCKS)
- **`live_trades`**: All stock order attempts (FILLED, REJECTED, PENDING, CANCELLED)
- **`live_positions`**: Current open stock positions
- **`live_trading_accounts`**: Account configuration and balances

### Paper Trading Tables (OPTIONS - NOT USED)
- **`paper_trading_orders`**: Options contracts (premiums, spreads, etc.)
- **`paper_trading_order_legs`**: Multi-leg options strategies

## 🚀 Live Trading Execution

### Automated Trading (CronJob)
```bash
# Check cronjob status
kubectl get cronjobs -n default | grep live-trading-executor

# View recent executions
kubectl get jobs -n default | grep live-trading-executor | tail -5

# View logs from latest execution
kubectl logs -n default $(kubectl get pods -n default --sort-by=.metadata.creationTimestamp | grep live-trading-executor | tail -1 | awk '{print $1}')
```

**Schedule**: Every 15 minutes during market hours
**Strategy**: MULTI_STRATEGY_ENSEMBLE
**Max Daily Trades**: 10
**Max Position Size**: 15%

## 📈 Recent Trading Activity (Last 24 Hours)

### Successful Trades (FILLED)
```
19:43:27 - AAPL:  1 share @ $256.14 ✅ FILLED
19:43:27 - GOOGL: 1 share @ $246.70 ✅ FILLED  
19:43:27 - MSFT:  1 share @ $522.94 ✅ FILLED
19:43:27 - MSFT:  1 share @ $522.98 ✅ FILLED
19:43:27 - QQQ:   1 share @ $604.34 ✅ FILLED
19:43:27 - QQQ:   1 share @ $604.38 ✅ FILLED
19:43:27 - QQQ:   1 share @ $604.67 ✅ FILLED
19:43:27 - QQQ:   1 share @ $604.68 ✅ FILLED
```

### Rejected Orders
- **20:09+**: 2 GOOGL orders rejected (insufficient funds - $212.59 deposit required)
- **20:10+**: Multiple orders rejected due to pending orders
- **Reason**: Pending orders on GOOGL (20:10) and MSFT (21:10) blocking new trades

### Pending Orders (Need Action)
```
⏳ GOOGL: 1 share pending (created 20:10)
⏳ MSFT:  2 shares pending (created 21:10)
```

**Action Required**: Cancel or fill these pending orders to allow new trades.

## 🛡️ Risk Management Status

- ✅ **Max Daily Loss**: $200.00
- ✅ **Max Position Size**: 15.0%
- ✅ **Authentication**: Active with Public.com
- ❌ **Emergency Stop**: Inactive (optional)

## 🔗 API Endpoints

### Live Trading Service (http://localhost:11120)
```bash
# Health check
GET /health

# Get orders (FILLED stock trades)
GET /api/v1/trading/orders?account_id={account_id}&status_filter=FILLED

# Get positions
GET /api/v1/trading/positions?account_id={account_id}

# Get account info
GET /api/v1/accounts?account_id={account_id}

# Get strategies
GET /api/v1/strategies/{account_id}

# Risk profile
GET /api/v1/risk/profile/{account_id}

# Auth status
GET /api/v1/auth/status/{account_id}
```

## 📝 Key Findings from Debugging Session

1. **Two Services Confusion**:
   - `paper-trading-k8s` (trading-system namespace) was misconfigured
   - `live-trading-service` (default namespace) is the correct one
   
2. **Data Source Mismatch**:
   - API was returning `paper_trading_orders` (OPTIONS)
   - Should have been returning `live_trades` (STOCKS)
   
3. **Monitor Fix**:
   - Updated `live_trading_monitor.py` to show both stored AND real-time prices
   - Fixed API endpoint to query correct table
   
4. **Environment Variables**:
   - Paper trading had: `TRADING_MODE=paper`, `ENVIRONMENT=paper`
   - Live trading doesn't need these (defaults to live mode)

## 🎯 Best Practices

1. **Always use `live-trading-service` in default namespace**
2. **Monitor uses port 11120** for consistency
3. **Check pending orders** before troubleshooting rejections
4. **Real-time prices** show actual P&L vs stored entry prices
5. **CronJob runs every 15 minutes** - check logs if trades aren't executing

## 🆘 Troubleshooting

### Problem: Monitor shows $0 trades
**Solution**: Port forward isn't running
```bash
kubectl port-forward -n default deployment/live-trading-service 11120:8080
```

### Problem: Orders being rejected
**Check**: Pending orders blocking new trades
```bash
curl "http://localhost:11120/api/v1/trading/orders?account_id=19c25392-8b61-4b71-a344-0eb04d275528" | grep PENDING
```

### Problem: Prices not updating
**Check**: Polygon API key accessible
```bash
kubectl get secret polygon-api-key -n trading-system
```

### Problem: No new trades executing
**Check**: CronJob execution status
```bash
kubectl get cronjobs -n default
kubectl logs -n default $(kubectl get pods -n default | grep live-trading-executor | tail -1 | awk '{print $1}')
```

## 📚 Related Documentation
- [Trading Endpoints Guide](TRADING_ENDPOINTS_GUIDE.md)
- [Live Trading Monitor Fix](LIVE_TRADING_MONITOR_FIX.md)
- [Prometheus & Grafana Setup](PROMETHEUS_GRAFANA_SETUP.md)
- [Port Mapping](../PORT_MAP.md)
- [Deploy Map](../DEPLOY_MAP.md)

