# Historical Options Data Backfill Guide

## Why You Need This

Options backtests require historical options data (strikes, prices, Greeks, etc.). Instead of hitting the Polygon API for every backtest, we cache this data in the database for faster execution.

## Quick Start

### Step 1: Check if you have data
```bash
make -f makefiles/Makefile.demo check-options-data
```

### Step 2: Backfill data (if needed)
```bash
# Full backfill (1 year of data for 9 symbols)
make -f makefiles/Makefile.demo backfill-options-data

# Quick test (7 days only)
make -f makefiles/Makefile.demo backfill-options-quick

# Dry run (test without saving)
make -f makefiles/Makefile.demo backfill-options-dry-run
```

### Step 3: Run demos
```bash
make -f makefiles/Makefile.demo options-demo
```

## What Gets Backfilled

### Default Configuration
- **Symbols**: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, SPY, QQQ (9 symbols)
- **Time Range**: 365 days (1 year)
- **Data**: Full options chains (all strikes, expirations)
- **Storage**: `historical_options_snapshots` table in TimescaleDB

### Estimated Time & Data
- **7 days**: ~5-10 minutes, ~few hundred snapshots
- **30 days**: ~15-20 minutes, ~few thousand snapshots
- **365 days**: ~30-60 minutes, ~3,000-5,000 snapshots

### API Usage
- **Free Tier**: Polygon allows 5 requests/minute
- **Script Rate Limit**: 2 requests/second (well within limits)
- **Total API Calls**: ~days × symbols = 365 × 9 = ~3,285 calls

## Advanced Usage

### Custom Symbols
```bash
python3 scripts/backfill_historical_options_data.py --symbols AAPL TSLA NVDA
```

### Custom Date Range
```bash
# 2 years of data
python3 scripts/backfill_historical_options_data.py --days 730

# Just last month
python3 scripts/backfill_historical_options_data.py --days 30
```

### Skip Existing Data (Faster)
```bash
# Only fetch missing dates
python3 scripts/backfill_historical_options_data.py --skip-existing
```

### Combination
```bash
# 2 years of FAANG stocks, skip existing
python3 scripts/backfill_historical_options_data.py \
  --symbols AAPL MSFT GOOGL AMZN META \
  --days 730 \
  --skip-existing
```

## Checking Data

### Quick Check
```bash
make -f makefiles/Makefile.demo check-options-data
```

### Detailed Check
```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d trading_bot -c "
SELECT 
    symbol,
    COUNT(*) as snapshot_count,
    MIN(snapshot_date) as first_date,
    MAX(snapshot_date) as last_date
FROM historical_options_snapshots
GROUP BY symbol
ORDER BY snapshot_count DESC;
"
```

### Sample Data
```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d trading_bot -c "
SELECT 
    snapshot_date,
    symbol,
    json_array_length(contracts::json) as num_contracts
FROM historical_options_snapshots
ORDER BY snapshot_date DESC
LIMIT 10;
"
```

## Troubleshooting

### "POLYGON_API_KEY not found"
```bash
# Check environment
make -f makefiles/Makefile.demo env-info

# Reload API key
kubectl get secret trading-secrets -n trading-system -o jsonpath='{.data.POLYGON_API_KEY}' | base64 -d
```

### "Cannot connect to database"
```bash
# Start port forward
make -f makefiles/Makefile.database db-port-forward

# Verify connection
make -f makefiles/Makefile.database db-port-check
```

### "No data returned"
Possible causes:
1. **Weekend/Market Closed**: Options data only available on trading days
2. **Symbol doesn't exist**: Check symbol is valid
3. **Date too old**: Polygon historical data has limits
4. **API limit**: Wait a moment and retry

### "Slow backfill"
```bash
# Use skip-existing to only fetch missing data
python3 scripts/backfill_historical_options_data.py --skip-existing

# Or backfill fewer symbols
python3 scripts/backfill_historical_options_data.py --symbols AAPL MSFT
```

## How It Works

1. **Fetch**: Script calls Polygon API for each day
2. **Parse**: Extracts options contracts (strikes, prices, Greeks)
3. **Store**: Saves to `historical_options_snapshots` table
4. **Cache**: MarketDataService reads from this table during backtests

### Database Schema
```sql
CREATE TABLE historical_options_snapshots (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    snapshot_date DATE NOT NULL,
    contracts JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, snapshot_date)
);

CREATE INDEX idx_snapshots_symbol_date 
ON historical_options_snapshots(symbol, snapshot_date);
```

### Backtest Flow
```
Backtest Request
    ↓
MarketDataService.get_historical_options_data()
    ↓
Query historical_options_snapshots table
    ↓
If exists: Return cached data
    ↓
If missing: Try Polygon API (slower)
```

## Best Practices

### For Development
```bash
# Quick test with minimal data
make -f makefiles/Makefile.demo backfill-options-quick
```

### For Testing Strategies
```bash
# 30 days is usually enough
python3 scripts/backfill_historical_options_data.py --days 30
```

### For Production Backtests
```bash
# Full year or more
python3 scripts/backfill_historical_options_data.py --days 730
```

### Maintenance
```bash
# Weekly: Fill gaps for new data
python3 scripts/backfill_historical_options_data.py --days 7 --skip-existing

# Monthly: Refresh all symbols
python3 scripts/backfill_historical_options_data.py --days 30
```

## Integration with Demos

The demo scripts will automatically check for historical data:

```bash
# Will check and prompt if data missing
make -f makefiles/Makefile.demo options-demo
```

If data is missing, you'll see:
```
❌ WARNING: No historical options data found!

This backtest requires historical options data to run efficiently.

💡 To backfill data, run:
   make -f makefiles/Makefile.demo backfill-options-data

Or to continue anyway (will be MUCH slower):
   Press Ctrl+C to cancel, or wait 10 seconds to continue...
```

## Costs & Limits

### Polygon API
- **Free Tier**: 5 requests/minute = 300/hour = 7,200/day
- **Script Uses**: ~2 requests/second when running
- **1 Year Backfill**: ~3,285 requests = fits in free tier

### Database Storage
- **Per Snapshot**: ~10-50 KB (depends on # of contracts)
- **365 days × 9 symbols**: ~150-500 MB
- **2 years × 9 symbols**: ~300MB-1GB

### Time Investment
- **Initial Backfill**: 30-60 minutes (one-time)
- **Weekly Updates**: 5-10 minutes
- **Backtest Speedup**: 10-100x faster than live API calls!

## Related Commands

```bash
# Database
make -f makefiles/Makefile.database db-port-forward
make -f makefiles/Makefile.database db-shell-timescale

# Environment  
make -f makefiles/Makefile.demo env-info
make -f makefiles/Makefile.demo test-api

# Data Check
make -f makefiles/Makefile.demo check-options-data

# Backfill
make -f makefiles/Makefile.demo backfill-options-data
make -f makefiles/Makefile.demo backfill-options-quick
make -f makefiles/Makefile.demo backfill-options-dry-run

# Run Demos
make -f makefiles/Makefile.demo options-demo
make -f makefiles/Makefile.demo comprehensive-demo
```

## Next Steps

1. ✅ Start database port-forward
2. ✅ Check current data status
3. ✅ Run quick backfill test (7 days)
4. ✅ Run full backfill if needed
5. ✅ Run options demos with cached data!

Happy backtesting! 🚀












