# Options Backtest: Real Data Only Policy

## 🎯 Overview

The Greeks-Enhanced Strategy now uses **ONLY real historical options data** for backtesting. When real data is not available, the strategy **skips that day** instead of using mock data.

## ✅ What Changed

### Before
- Used mock/synthetic Greeks data when historical data was unavailable
- Generated fake delta, gamma, theta, vega values
- Produced misleading backtest results

### After
- Returns `None` when no real historical Greeks data is found
- Skips the day entirely in backtesting (HOLD with confidence=0.0)
- Only uses actual historical options data from the database
- Produces accurate, realistic backtest results

## 📊 Implementation Details

### Files Updated
1. `src/strategies/options/greeks_enhanced_strategy.py`
2. `services/strategy-service/src/strategies/options/greeks_enhanced_strategy.py`

### Key Changes

#### 1. `get_greeks_data()` Method
```python
# OLD: Generated mock data
if not liquid_contracts:
    logger.warning(f"Using mock data")
    mock_greeks = GreeksData(delta=0.6, gamma=0.08, ...)
    return mock_greeks

# NEW: Returns None to skip
if not liquid_contracts:
    logger.info(f"Skipping this day")
    return None
```

#### 2. `generate_signal()` Method
```python
greeks = self.get_greeks_data(symbol, current_price, historical_date)

# Skip if no real data available for backtesting
if greeks is None and historical_date:
    logger.info(f"Skipping {symbol} on {historical_date} - no real Greeks data")
    return TradeSignal(
        action="HOLD",
        quantity=0,
        confidence=0.0,
        metadata={"skipped": True, "reason": "no_greeks_data"}
    )
```

## 🔍 Behavior by Context

### During Backtesting (`historical_date` provided)
- ✅ Uses real historical options data when available
- ⏭️  Skips day when no real data exists
- ❌ Never uses mock/synthetic data

### During Live Trading (`historical_date` is None)
- ✅ Uses real current options data when available
- ⚠️  Returns None when no data available (strategy doesn't trade)

## 📈 Impact on Backtests

### Data Availability
- Strategy will only generate signals on days where:
  1. Real historical options data exists in database
  2. Options contracts are liquid (volume >= 1)
  3. Greeks values are properly calculated

### Backtest Accuracy
- **More Realistic**: Results reflect actual market conditions
- **Fewer Trades**: Only trades when real data supports it
- **True Performance**: No artificial inflation from mock data

## 🚀 Usage

### 1. Backfill Historical Options Data (2 years)
```bash
make -f makefiles/Makefile.demo backfill-options-2year
```

### 2. Verify Data Availability
```bash
make -f makefiles/Makefile.demo check-options-data
```

### 3. Run Options Backtest
```bash
make -f makefiles/Makefile.demo options-demo
```

## 📝 Log Messages

### What to Expect

#### Real Data Found ✅
```
[GreeksStrategy] ✅ Found REAL historical Greeks data for AAPL on 2024-06-26
[GreeksStrategy] ✅ Using REAL Greeks data: delta=0.654, gamma=0.082, theta=-0.031, vega=0.178
```

#### No Data - Skipping Day ⏭️
```
[GreeksStrategy] ⏭️ No historical options data found for AAPL on 2024-06-26, skipping this day
[GreeksStrategy] ⏭️ Skipping AAPL on 2024-06-26 - no real Greeks data available
```

#### Error - Skipping Day ❌
```
[GreeksStrategy] ❌ Error getting Greeks data for AAPL on 2024-06-26: <error message>
[GreeksStrategy] ⏭️ Skipping AAPL on 2024-06-26 due to error
```

## 🎯 Benefits

1. **Accuracy**: Backtest results reflect real market conditions
2. **Transparency**: Clear logging of when/why days are skipped
3. **Integrity**: No artificial performance inflation
4. **Reliability**: Results you can trust for strategy validation

## ⚠️ Important Notes

- **Coverage Depends on Data**: Backtest coverage depends on historical data availability
- **Backfill First**: Always backfill historical options data before backtesting
- **Check Coverage**: Use `check-options-data` to verify data availability
- **Expected Gaps**: Some days may be skipped due to data gaps (weekends, holidays, low liquidity)

## 🔧 Troubleshooting

### Issue: Too Many Skipped Days
**Solution**: Backfill more historical options data
```bash
make -f makefiles/Makefile.demo backfill-options-2year
```

### Issue: No Trades in Backtest
**Check**: 
1. Historical options data exists: `make -f makefiles/Makefile.demo check-options-data`
2. Date range matches backfilled data
3. Database port-forward is active: `make -f makefiles/Makefile.database db-port-check`

### Issue: Strategy Not Running
**Verify**:
1. Database connection: `nc -z localhost 5432`
2. Polygon API key loaded: `make -f makefiles/Makefile.demo env-info`
3. Data availability: `make -f makefiles/Makefile.demo check-options-data`

---

**Last Updated**: October 12, 2025
**Strategy**: GreeksEnhancedStrategy
**Policy**: Real Data Only - No Mock Data in Backtests












