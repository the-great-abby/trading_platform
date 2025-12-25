# Demo Quick Start Guide

## 🚀 Running Demos

### For Stock Demos (2 Steps)
```bash
# Step 1: Start database
make -f makefiles/Makefile.database db-port-forward

# Step 2: Run demo
make -f Makefile.demo comparison-demo
```

### For Options Demos (3 Steps)
```bash
# Step 1: Start database
make -f makefiles/Makefile.database db-port-forward

# Step 2: Backfill historical options data (ONE TIME ONLY)
make -f Makefile.demo check-options-data  # Check if you need data
make -f Makefile.demo backfill-options-quick  # Quick test (7 days)
# OR
make -f Makefile.demo backfill-options-data  # Full backfill (1 year)

# Step 3: Run demo
make -f Makefile.demo options-demo
```

**Note:** Step 2 is a ONE-TIME setup! Once you have data, just run the demo.

## ✅ Environment is Auto-Loaded!

The Makefiles automatically:
- ✅ Load `POLYGON_API_KEY` from Kubernetes secrets
- ✅ Check database connectivity  
- ✅ Set environment variables
- ✅ Provide helpful error messages

## 📊 Check Environment Status

```bash
make -f Makefile.demo env-info
```

Example output:
```
🔧 Environment Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API Keys:
  POLYGON_API_KEY: ✅ PwSQb2yBh2aYqEs...

Database:
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/trading_bot
  Status: ✅ Connected

Backtest Settings:
  ENABLE_LLM_EVALUATION: false
  MARKET_DATA_CACHE_ENABLED: true
  BACKTEST_INITIAL_CAPITAL: 4000
```

## 🛑 When Done

```bash
# Stop database port forward
make -f makefiles/Makefile.database db-port-stop
```

## ❌ Troubleshooting

### "POLYGON_API_KEY not found"
```bash
# Check Kubernetes secret exists
kubectl get secret trading-secrets -n trading-system
```

### "Cannot connect to database"
```bash
# Start port forward
make -f makefiles/Makefile.database db-port-forward

# Verify it's working
make -f makefiles/Makefile.database db-port-check
```

### "Port 5432 already in use"
```bash
# Stop existing port forward
make -f makefiles/Makefile.database db-port-stop

# Then start fresh
make -f makefiles/Makefile.database db-port-forward
```

## 📚 More Documentation

- **Environment Setup:** `docs/ENVIRONMENT_SETUP.md`
- **Database Port Forward:** `docs/DATABASE_PORT_FORWARD_GUIDE.md`
- **Backtest Options vs Stocks:** `docs/BACKTEST_OPTIONS_VS_STOCKS.md`
- **Backtest Quick Reference:** `BACKTEST_QUICK_REFERENCE.md`

