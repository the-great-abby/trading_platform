# Quick Start: Options Backtesting

## 🚀 3-Step Setup (One-Time)

### Step 1: Start Database Port Forward
```bash
make -f makefiles/Makefile.database db-port-forward
```

### Step 2: Verify Environment
```bash
make -f Makefile.demo env-info
```

Expected output:
```
✅ Polygon API Key loaded
✅ Database connected
```

### Step 3: Backfill Historical Options Data
```bash
# Quick test (7 days, ~5 minutes)
make -f Makefile.demo backfill-options-quick

# Or full year (~30 minutes)
make -f Makefile.demo backfill-options-data
```

---

## ✅ You're Ready! Run Demos

```bash
# Options backtest (14 strategies)
make -f Makefile.demo options-demo

# Stock comparison
make -f Makefile.demo comparison-demo

# Comprehensive (Stocks + Options)
make -f Makefile.demo comprehensive-demo
```

---

## 📊 Check Your Data

```bash
# See what data you have
make -f Makefile.demo check-options-data
```

Example output:
```
 total_snapshots | unique_symbols | earliest_date | latest_date
-----------------+----------------+---------------+-------------
           12000 |              3 | 2025-10-03    | 2025-10-09
```

---

## 🔧 Troubleshooting

### "POLYGON_API_KEY not found"
```bash
kubectl get secret trading-secrets -n trading-system
```

### "Cannot connect to database"
```bash
make -f makefiles/Makefile.database db-port-forward
make -f makefiles/Makefile.database db-port-check
```

### "No historical options data found"
```bash
make -f Makefile.demo backfill-options-quick
```

---

## 📚 All Available Commands

### Demo Execution
- `make -f Makefile.demo options-demo` - Options backtest
- `make -f Makefile.demo comparison-demo` - Stock comparison
- `make -f Makefile.demo comprehensive-demo` - Stocks + Options
- `make -f Makefile.demo stock-demo` - Stock recommendations

### Environment
- `make -f Makefile.demo env-info` - Check environment status
- `make -f Makefile.demo test-api` - Test Polygon API

### Data Management
- `make -f Makefile.demo check-options-data` - Check data availability
- `make -f Makefile.demo backfill-options-data` - Full backfill (1 year)
- `make -f Makefile.demo backfill-options-quick` - Quick backfill (7 days)
- `make -f Makefile.demo backfill-options-dry-run` - Test mode

### Database
- `make -f makefiles/Makefile.database db-port-forward` - Start port forward
- `make -f makefiles/Makefile.database db-port-check` - Verify connection
- `make -f makefiles/Makefile.database db-port-stop` - Stop port forward
- `make -f makefiles/Makefile.database db-shell-timescale` - Open SQL shell

---

## ⚡ Super Quick Start (If Already Set Up)

```bash
# Start database (if not already running)
make -f makefiles/Makefile.database db-port-check || \
make -f makefiles/Makefile.database db-port-forward

# Run any demo
make -f Makefile.demo options-demo
```

---

## 📈 What You Get

### Stock Comparison Backtest
- Tests Elliott Wave vs Multi-Indicator
- Shows realized vs unrealized P&L
- Breaks down cash vs position values
- ~10-15 minutes runtime

### Options Backtest
- Tests 14 different options strategies
- Uses cached historical data
- Shows performance in different market conditions
- ~5-10 minutes runtime (with cached data)

### Comprehensive Comparison
- Tests 3 portfolios simultaneously
- Stocks (Original) vs Stocks (Enhanced) vs Options
- Side-by-side performance comparison
- ~15-20 minutes runtime

---

## 🎯 Pro Tips

1. **Backfill once, test forever**: Historical data is cached
2. **Use dry-run first**: Test API access before full backfill
3. **Start with quick**: 7 days is enough to test strategies
4. **Expand gradually**: Add more symbols/days as needed
5. **Check data first**: Always run `check-options-data` before demos

---

## 📖 Complete Documentation

- **This Guide**: `QUICK_START_OPTIONS_BACKTESTING.md`
- **Environment Setup**: `docs/ENVIRONMENT_SETUP.md`
- **Database Guide**: `docs/DATABASE_PORT_FORWARD_GUIDE.md`
- **Backfill Guide**: `docs/OPTIONS_DATA_BACKFILL_GUIDE.md`
- **Options vs Stocks**: `docs/BACKTEST_OPTIONS_VS_STOCKS.md`
- **Session Summary**: `SESSION_SUMMARY_OCT10_2025.md`

---

**You're all set! Happy backtesting! 🚀**




