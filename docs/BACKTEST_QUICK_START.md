# 🚀 Quick Start: Testing Live Trading API Endpoints

## ⚠️ Important Note

The comparison backtest is an **API integration test**, not a true historical backtest. It:
- ✅ Tests that API endpoints work correctly
- ✅ Validates recommendations can be retrieved
- ✅ Compares which endpoint generates more signals
- ❌ Does NOT test historical performance (uses current data repeatedly)

For **true historical backtesting** with actual historical data:
```bash
python backtests/comprehensive_two_year_backtest.py
python backtests/enhanced_market_regime_backtest.py
```

## Overview

You can test your live trading API endpoints to ensure they work before deploying changes.

## Quick Commands

### 1. Test Enhanced Recommendations
```bash
make -f makefiles/Makefile.backtesting enhanced
```
**What it does**: Tests the enhanced multi-indicator recommendations (same as live trading uses)

### 2. Compare Original vs Enhanced
```bash
make -f makefiles/Makefile.backtesting compare
```
**What it does**: Runs both strategies side-by-side and shows which performs better

### 3. Full Strategy Test
```bash
make -f makefiles/Makefile.backtesting test-strategies
```
**What it does**: Runs the comparison backtest (alias for `compare`)

## Before You Start

### 1. Ensure Strategy Service is Running
```bash
curl http://localhost:11001/health
```
**Expected**: `{"status": "healthy"}`

### 2. Check Port Forward
```bash
ps aux | grep port-forward | grep 11001
```
**Expected**: Should show an active port-forward

If not running:
```bash
kubectl port-forward -n trading-system svc/strategy-service 11001:8001 &
```

### 3. Activate Virtual Environment
```bash
source .venv/bin/activate
```

## What Gets Tested

### 🔵 Original (Elliott Wave Only)
- Endpoint: `/api/trading/recommendations`
- Single indicator analysis
- Based on Elliott Wave patterns

### 🟢 Enhanced (Multi-Indicator)
- Endpoint: `/api/trading/recommendations/enhanced`
- **RSI** - Relative Strength Index
- **MACD** - Moving Average Convergence Divergence
- **MA** - Moving Averages
- **Volume** - Volume analysis
- **Bollinger Bands** - Volatility bands
- Weighted voting system
- Minimum 60% confidence threshold

## Understanding Results

### During Backtest
You'll see output like:
```
📅 Day 1/30 - Check 1/24
💰 Portfolio Value: $4,000.00
📊 Got 5 enhanced recommendations
   AMZN   | BUY  | Score:  50.00 | Conf:  70.0%
   MSFT   | HOLD | Score:  28.93 | Conf:  57.0%
✅ BUY 10 AMZN @ $180.50 (confidence: 70.0%, score: 50.00)
```

### Final Results
```
📊 BACKTEST RESULTS
═══════════════════════════════════════════════
💰 Initial Capital:     $4,000.00
💰 Final Capital:       $4,600.00
📈 Total Return:        $600.00 (15.00%)
📊 Total Trades:        45
🎯 Win Rate:            62.0%
📊 Profit Factor:       1.80
⚠️  Max Drawdown:        8.50%
```

### Comparison Results
```
🏆 FINAL COMPARISON RESULTS
═══════════════════════════════════════════════

🔵 ORIGINAL RECOMMENDATIONS (Elliott Wave Only)
   💰 Final Capital:      $4,320.00
   📈 Total Return:       $320.00 (8.00%)
   🎯 Win Rate:           55.0%
   📊 Profit Factor:      1.45

🟢 ENHANCED RECOMMENDATIONS (Multi-Indicator)
   💰 Final Capital:      $4,600.00
   📈 Total Return:       $600.00 (15.00%)
   🎯 Win Rate:           62.0%
   📊 Profit Factor:      1.80

🏆 WINNER: Enhanced
   📊 Margin: $280.00 (8.75%)
```

## Where Results Are Saved

```bash
# Enhanced backtest results
results/enhanced_recommendations_backtest_YYYYMMDD_HHMMSS.json

# Comparison results
results/comparison_backtest_YYYYMMDD_HHMMSS.json
```

View latest results:
```bash
make -f makefiles/Makefile.backtesting results
```

## How It Mimics Live Trading

| Feature | Live Trading | Backtest |
|---------|--------------|----------|
| API Endpoint | `/api/trading/recommendations/enhanced` | ✅ Same |
| Risk Management | 20% max position, 5 max positions | ✅ Same |
| Trading Costs | Public.com (no commission, slippage) | ✅ Same |
| Database | postgres-infra | ✅ Same |
| Confidence Threshold | 60% minimum | ✅ Same |
| Position Sizing | Based on confidence | ✅ Same |

## Typical Workflow

1. **Make changes to live trading strategy**
   ```bash
   # Example: Update indicator weights in strategy-service
   ```

2. **Test in backtest mode FIRST**
   ```bash
   make -f makefiles/Makefile.backtesting compare
   ```

3. **Review results**
   - Check if enhanced performs better
   - Verify win rate improves
   - Look at drawdown

4. **Deploy to live trading** (if backtest is successful)
   ```bash
   # Your changes are already deployed
   # Backtest just validates they work
   ```

5. **Monitor live trading**
   - Watch first few trades
   - Compare to backtest expectations
   - Be ready to rollback if needed

## Troubleshooting

### "Failed to get recommendations: HTTP 500"
- Check strategy-service logs: `kubectl logs -n trading-system deployment/strategy-service`
- Verify database connection
- Check if market-data-worker is running

### "No recommendations available"
- Database might not have current data
- Check market-data-worker: `kubectl get pods -n trading-system | grep market-data-worker`
- Verify symbols are configured

### "Connection refused" or "Timeout"
- Strategy service not running: `kubectl get pods -n trading-system | grep strategy-service`
- Port-forward not active: `kubectl port-forward -n trading-system svc/strategy-service 11001:8001 &`

### Import Errors (httpx, pandas)
```bash
source .venv/bin/activate
pip install httpx pandas
```

## Advanced Usage

### Custom Parameters

Edit the backtest scripts to customize:

**Duration**:
```python
results = await backtest.run_backtest(days=60, check_interval_hours=4)
```

**Initial Capital**:
```python
backtest = EnhancedRecommendationsBacktest(initial_capital=5000.0)
```

**Risk Limits**:
```python
self.max_position_size = 0.15  # 15% instead of 20%
self.max_concurrent_positions = 3  # 3 instead of 5
```

### Using in Kubernetes

The backtests detect Kubernetes environment automatically:
```python
if os.getenv('KUBERNETES_SERVICE_HOST'):
    self.strategy_service_url = "http://strategy-service.trading-system.svc.cluster.local:8001"
```

To run in K8s, create a Job:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: backtest-enhanced
spec:
  template:
    spec:
      containers:
      - name: backtest
        image: localhost:32000/trading-system:latest
        command: ["python", "backtests/enhanced_recommendations_backtest.py"]
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:postgres@postgres-timescale-external.postgres-infra:5432/trading_bot"
```

## Help Commands

```bash
# Main help
make -f makefiles/Makefile.backtesting help

# Detailed backtest help
make -f makefiles/Makefile.backtesting backtest-help

# Check status
make -f makefiles/Makefile.backtesting status

# View results
make -f makefiles/Makefile.backtesting results

# Clean old results
make -f makefiles/Makefile.backtesting clean
```

## What's Different from Old Backtests?

### Old Backtests
- ❌ Used simulated/random signals
- ❌ Didn't call real strategy service
- ❌ Couldn't validate live trading strategies
- ❌ Mock data only

### New Backtests  
- ✅ Call actual strategy-service API
- ✅ Use same endpoints as live trading
- ✅ Test real recommendations
- ✅ Validate before deployment
- ✅ Use current market data

## Summary

The new backtesting system lets you:

✅ **Test before deploy** - Validate strategies work  
✅ **Compare approaches** - See which performs better  
✅ **Use real data** - Same as live trading  
✅ **Get metrics** - Win rate, profit factor, drawdown  
✅ **Save results** - JSON output for analysis  

This creates a complete testing pipeline:
1. Make strategy changes
2. Test in backtest mode
3. Validate improvement
4. Deploy to live trading with confidence

---

**Quick Start Command**:
```bash
make -f makefiles/Makefile.backtesting compare
```

This will run both strategies and tell you which performs better! 🚀

