# 📊 Backtesting Guide

## Quick Start

Run backtests easily with the new **Makefile.backtesting**:

```bash
# Show all available commands
make -f Makefile.backtesting help

# Quick 30-day test
make -f Makefile.backtesting quick

# Full 2-year backtest
make -f Makefile.backtesting 2year

# Multi-strategy ensemble backtest
make -f Makefile.backtesting multi

# Regime-switching backtest
make -f Makefile.backtesting regime

# Open web interface
make -f Makefile.backtesting dashboard
```

---

## 🌟 **NEW FEATURES**

### 1. Multi-Strategy Support ✅

Test multiple strategies simultaneously and see how they perform together!

**Command**:
```bash
make -f Makefile.backtesting multi
```

**What it does**:
- Tests 7+ strategies in parallel
- Shows individual performance
- Calculates ensemble performance
- Ranks strategies by Sharpe ratio
- Shows top performers

**Strategies tested**:
- RSI, MACD, Bollinger Bands
- SMA Crossover, Momentum
- Mean Reversion
- Iron Condor (options)

**Results**:
```
📊 INDIVIDUAL STRATEGY RESULTS:
  RSIStrategy: +15.3% return (65% win rate)
  MACDStrategy: +22.1% return (58% win rate)
  ...

🏆 ENSEMBLE PERFORMANCE:
  Average Return: +18.5%
  Total Trades: 142
  
🌟 TOP PERFORMERS:
  1. MACDStrategy: +22.1%
  2. MomentumStrategy: +19.8%
  3. RSIStrategy: +15.3%
```

---

### 2. Regime Switching ✅

**Automatically switches strategies based on market conditions!**

**Command**:
```bash
make -f Makefile.backtesting regime
```

**What it does**:
- Detects market regime (Bull/Bear/Sideways)
- Uses different strategies for each regime
- Optimizes performance based on market conditions

**Strategy Assignment**:

| Regime | Strategies | Why? |
|--------|-----------|------|
| **Bull Market** 📈 | Momentum, SMA Crossover, Breakout | Trend-following works best |
| **Bear Market** 📉 | Mean Reversion, Iron Condor | Range-bound strategies |
| **Sideways** ↔️ | Iron Condor, Butterfly Spread | Profit from low volatility |

**How it detects regimes**:
- **Trend**: Average return over 20 days
- **Volatility**: Standard deviation of returns
- **Bull**: Positive trend + low volatility
- **Bear**: Negative trend + high volatility
- **Sideways**: Everything else

**Results**:
```
🎯 REGIME-SWITCHING BACKTEST

BULL Market Strategies:
  MomentumStrategy: +25.3% return (Sharpe: 2.1)
  ⭐ Best for bull: MomentumStrategy

BEAR Market Strategies:
  IronCondorStrategy: +8.5% return (Sharpe: 1.8)
  ⭐ Best for bear: IronCondorStrategy

SIDEWAYS Market Strategies:
  ButterflySpreadStrategy: +12.1% return (Sharpe: 1.5)
  ⭐ Best for sideways: ButterflySpreadStrategy
```

---

## 🌐 Web Interface

Access the backtesting dashboard through your browser!

### Open Dashboard

```bash
make -f Makefile.backtesting dashboard
```

Then navigate to: **http://localhost:11115/#backtesting**

### Features:
- ✅ Select multiple strategies
- ✅ Choose date range
- ✅ Set initial capital
- ✅ Configure risk profile
- ✅ Enable/disable AI analysis
- ✅ View results in real-time
- ✅ Compare strategies side-by-side

---

## 📋 All Commands

### Quick Actions

```bash
# Quick 30-day test (3 strategies, 3 symbols)
make -f Makefile.backtesting quick

# Full 2-year backtest (historical data)
make -f Makefile.backtesting 2year

# Multi-strategy ensemble
make -f Makefile.backtesting multi

# Regime-switching
make -f Makefile.backtesting regime

# Web interface
make -f Makefile.backtesting web
```

### Dashboard & Results

```bash
# Open dashboard
make -f Makefile.backtesting dashboard

# View latest results
make -f Makefile.backtesting results

# Check job status
make -f Makefile.backtesting status

# Follow logs
make -f Makefile.backtesting logs
```

### Cleanup

```bash
# Clean old results (>7 days)
make -f Makefile.backtesting clean

# Clean completed Kubernetes jobs
make -f Makefile.backtesting clean-jobs

# Stop all running backtests
make -f Makefile.backtesting stop
```

---

## 🎯 How It Works

### In Kubernetes ✅ (Recommended)

All backtest commands run as Kubernetes jobs:

```bash
make -f Makefile.backtesting multi
# Creates: kubectl apply -f k8s/backtest-multi-strategy.yaml
```

**Advantages**:
- ✅ Uses real market data from database
- ✅ No port-forwarding needed
- ✅ Proper resource limits
- ✅ Logs are preserved
- ✅ Can scale easily

### Architecture

```
┌─────────────────────────────────────────┐
│  Kubernetes Cluster                     │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │ Backtest     │───→│ TimescaleDB  │ │
│  │ Job          │    │ (Real Data)  │ │
│  └──────────────┘    └──────────────┘ │
│         │                              │
│         ↓ Results                      │
│  ┌──────────────┐                     │
│  │ Logs &       │                     │
│  │ Metrics      │                     │
│  └──────────────┘                     │
└─────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Environment Variables (in Kubernetes jobs)

**Multi-Strategy**:
```yaml
STRATEGIES: "RSIStrategy,MACDStrategy,BollingerBandsStrategy"
PORTFOLIO_MODE: "ensemble"  # ensemble, sequential, parallel
POSITION_ALLOCATION: "equal"  # equal, performance-weighted
```

**Regime Switching**:
```yaml
REGIME_LOOKBACK_DAYS: "20"
REGIME_VOLATILITY_THRESHOLD: "0.02"
BULL_STRATEGIES: "MomentumStrategy,SMACrossoverStrategy"
BEAR_STRATEGIES: "MeanReversionStrategy,IronCondorStrategy"
SIDEWAYS_STRATEGIES: "IronCondorStrategy,ButterflySpreadStrategy"
```

### Customization

Edit the YAML files in `k8s/backtest-*.yaml` to customize:
- Symbols to test
- Date ranges
- Strategies
- Resource limits
- Database settings

---

## 📊 Example Workflow

### 1. Quick Test

```bash
# Start with quick test to validate setup
make -f Makefile.backtesting quick

# Check logs
make -f Makefile.backtesting logs

# View results
make -f Makefile.backtesting results
```

### 2. Multi-Strategy Analysis

```bash
# Run multi-strategy backtest
make -f Makefile.backtesting multi

# Wait for completion (2-5 minutes)
make -f Makefile.backtesting status

# View results
make -f Makefile.backtesting logs
```

### 3. Regime Switching

```bash
# Test regime switching
make -f Makefile.backtesting regime

# Follow progress
make -f Makefile.backtesting logs

# Clean up when done
make -f Makefile.backtesting clean-jobs
```

### 4. Web Interface

```bash
# Open dashboard
make -f Makefile.backtesting dashboard

# Configure and run from browser
# View results in real-time
```

---

## 🚨 Troubleshooting

### "No database connection"

**Solution**: Make sure TimescaleDB is running in Kubernetes:
```bash
kubectl get pods -n trading-system | grep timescaledb
```

### "No results returned"

**Possible causes**:
1. Not enough historical data in database
2. Strategies not found
3. Date range too small

**Check logs**:
```bash
make -f Makefile.backtesting logs
```

### "Job failed"

**Check status**:
```bash
kubectl get jobs -n trading-system
kubectl describe job <job-name> -n trading-system
```

**View pod logs**:
```bash
kubectl logs -n trading-system <pod-name>
```

---

## ✅ Summary

| Feature | Command | Time | Strategies |
|---------|---------|------|------------|
| **Quick Test** | `make quick` | 1-2 min | 3 |
| **2-Year** | `make 2year` | 5-10 min | 8 |
| **Multi-Strategy** | `make multi` | 3-5 min | 7+ |
| **Regime Switch** | `make regime` | 5-8 min | 9+ |
| **Dashboard** | `make dashboard` | N/A | Any |

**Recommendation**: Start with `make quick` to validate setup, then use `make multi` or `make regime` for comprehensive analysis.

**Web Interface**: Use `make dashboard` for interactive testing and visual results!







