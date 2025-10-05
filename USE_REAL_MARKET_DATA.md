# Using Real Market Data in Backtests

## The Problem

The BacktestEngine falls back to mock data when `DATABASE_URL` is not set. This happens when running backtests locally.

## Current Behavior

### In Kubernetes ✅
- DATABASE_URL is set from `trading-secrets`
- Uses real historical market data from TimescaleDB
- Can fetch from Polygon API if database is empty

### Locally ❌  
- DATABASE_URL not set
- Falls back to mock data
- Unrealistic price movements

## Solution 1: Port-Forward to TimescaleDB (Recommended)

```bash
# 1. Port-forward to TimescaleDB
kubectl port-forward -n trading-system svc/timescaledb 5432:5432

# 2. Get the database credentials
kubectl get secret -n trading-system trading-secrets -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d

# 3. Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/trading"

# 4. Run backtest with real data
python3 run/run_2year_automated_backtest.py
```

## Solution 2: Use Polygon API Directly

```bash
# 1. Set Polygon API key
export POLYGON_API_KEY="your_polygon_api_key"

# 2. Run backtest (will fetch from API)
python3 run/run_2year_automated_backtest.py
```

## Solution 3: Run Backtest in Kubernetes

```bash
# Run backtest as a Kubernetes job (has DATABASE_URL automatically)
kubectl apply -f k8s/backtest-2year-comprehensive.yaml

# Check logs
kubectl logs -n trading-system job/backtest-2year-comprehensive -f
```

## What's Wrong with Mock Data?

The current mock data (before my improvements):
```python
# OLD: Overly optimistic
daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean = always going up!
```

**My improvements** (now includes):
- ✅ Bull/bear/sideways market regimes
- ✅ Market shocks (5% chance of volatility spike)
- ✅ Realistic volatility patterns
- ✅ No upward bias

But even with improvements, **real data is always better** for backtesting!

## Recommended Approach

**For realistic backtests, always use real data:**

1. **In development** (local):
   - Port-forward to TimescaleDB
   - Set DATABASE_URL
   - Use cached real data

2. **In production** (Kubernetes):
   - DATABASE_URL automatically set
   - Uses real historical data
   - Falls back to Polygon API if needed

## Verifying Real Data Usage

When backtest runs, check the logs:

```
✅ Using real data:
📥 Fetching market data for 3 symbols...
✅ Successfully fetched data for 3/3 symbols

❌ Using mock data:
📊 Using mock data for testing...
📊 Generated mock data for 3 symbols
```

## Current Status

**Mock data improvements applied** (realistic market regimes, shocks, no bias)
- But you should still use real data when possible!

**To switch to real data:**
```bash
# Quick command to set up
kubectl port-forward -n trading-system svc/timescaledb 5432:5432 &
export DATABASE_URL="postgresql://postgres:$(kubectl get secret -n trading-system trading-secrets -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)@localhost:5432/trading"
python3 run/run_2year_automated_backtest.py
```







