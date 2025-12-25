# Backtest Quick Reference

## Which Backtest Should I Run?

### 🔵 Stock Recommendations Comparison
**File:** `backtests/compare_recommendations_backtest.py`
```bash
python backtests/compare_recommendations_backtest.py
```
- **Tests:** Original (Elliott Wave) vs Enhanced (Multi-indicator)
- **Assets:** Stocks only (AAPL, MSFT, TSLA, etc.)
- **Duration:** ~2 hours for 30-day simulation
- **Use when:** Comparing stock recommendation algorithms

---

### 🟡 Stocks + Options Comparison
**File:** `backtests/comprehensive_comparison_backtest.py`
```bash
python backtests/comprehensive_comparison_backtest.py
```
- **Tests:** Original stocks vs Enhanced stocks vs Options scanner
- **Assets:** Stocks AND options strategies
- **Duration:** ~2 hours for 30-day simulation
- **Use when:** Comparing stocks vs options performance

---

### 📊 Historical Stock Backtest (Real Data)
**Files:** 
- `backtests/comprehensive_two_year_backtest.py`
- `backtests/enhanced_market_regime_backtest.py`
```bash
python backtests/comprehensive_two_year_backtest.py
```
- **Tests:** Multiple strategies with real historical data
- **Assets:** Stocks with 2+ years of market data
- **Duration:** Several hours
- **Use when:** Need accurate historical performance data

---

### 🎯 Historical Options Backtest (Real Data + Greeks)
**File:** `demo/demo_comprehensive_options_backtest.py`
```bash
python demo/demo_comprehensive_options_backtest.py
```
- **Tests:** Options strategies with Greeks calculations
- **Assets:** Options contracts with real pricing
- **Duration:** Several hours
- **Use when:** Need accurate options strategy performance

---

## Quick Decision Tree

```
Do you want to test options?
│
├─ NO → Do you need real historical data?
│        │
│        ├─ NO → Use: compare_recommendations_backtest.py
│        │         (Fast API integration test)
│        │
│        └─ YES → Use: comprehensive_two_year_backtest.py
│                  (Historical stock backtest)
│
└─ YES → Do you need accurate Greeks and real pricing?
         │
         ├─ NO → Use: comprehensive_comparison_backtest.py
         │         (Fast API integration test with options)
         │
         └─ YES → Use: demo_comprehensive_options_backtest.py
                   (Historical options backtest with Greeks)
```

## Results Location

All backtest results are saved to:
```
results/
├── comparison_backtest_20251009_153859.json
├── comprehensive_comparison_20251009_160000.json
├── comprehensive_backtest_20251009_170000.json
└── ...
```

## Understanding Output

### During Execution
```
📅 Day 15/30 - Check 12/24
📊 PORTFOLIO COMPARISON:
   🔵 Original:
      Total:     $4,003.50
      Cash:      $1,096.85
      Positions: $2,906.65 (1 open)
      Trades:    9
```

### Final Results
```
🏆 FINAL COMPARISON RESULTS
🔵 ORIGINAL RECOMMENDATIONS (Elliott Wave Only)
   💰 Final Portfolio:    $4,003.50
      💵 Cash:            $1,096.85
      📦 Positions:       $2,906.65
   📈 Total Return:       $3.50 (0.09%)
      ✅ Realized:        $0.00
      📊 Unrealized:      $3.50
   📊 Total Trades:       9 (9 buys, 0 sells)
   📦 Open Positions:     1
```

## Key Metrics

- **Final Portfolio** = Cash + Position Values (total account value)
- **Total Return** = Final Portfolio - Initial Capital
- **Realized P&L** = Locked-in profit from closed trades
- **Unrealized P&L** = Paper profit from open positions
- **Win Rate** = Winning Trades / Total Closed Trades

## Common Questions

### Why is my Total Return $0?
- You probably have no **closed positions** (only open positions)
- Check **Unrealized P&L** to see paper gains/losses
- See: `docs/BACKTEST_PORTFOLIO_TRACKING.md`

### Why don't I see any options trades?
- You're probably running `compare_recommendations_backtest.py` (stocks only)
- Switch to `comprehensive_comparison_backtest.py` for options
- See: `docs/BACKTEST_OPTIONS_VS_STOCKS.md`

### Are these real backtests?
- API integration tests (`compare_*`) use **current data repeatedly** (not historical)
- Historical backtests (`comprehensive_two_year_*`, `demo_comprehensive_*`) use **real historical data**
- Integration tests are faster but less accurate
- Historical backtests are slower but more realistic

### Which backtest is most realistic?
1. **Most realistic:** `demo/demo_comprehensive_options_backtest.py` (real data + Greeks)
2. **Very realistic:** `backtests/comprehensive_two_year_backtest.py` (real stock data)
3. **Less realistic:** `comprehensive_comparison_backtest.py` (current data, simplified options)
4. **Least realistic:** `compare_recommendations_backtest.py` (current data, stocks only)

## Documentation

- **Full comparison guide:** `docs/BACKTEST_OPTIONS_VS_STOCKS.md`
- **Portfolio tracking:** `docs/BACKTEST_PORTFOLIO_TRACKING.md`
- **Available strategies:** `docs/AVAILABLE_STRATEGIES.md`
- **Options strategies:** `docs/OPTIONS_STRATEGIES_GUIDE.md`

## Getting Started

**For quick testing (5 minutes):**
```bash
python backtests/compare_recommendations_backtest.py
```

**For comprehensive testing (30 minutes):**
```bash
python backtests/comprehensive_comparison_backtest.py
```

**For production-ready results (2+ hours):**
```bash
# Stocks
python backtests/comprehensive_two_year_backtest.py

# Options
python demo/demo_comprehensive_options_backtest.py
```






