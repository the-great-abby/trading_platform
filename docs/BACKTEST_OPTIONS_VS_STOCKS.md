# Backtest Comparison: Options vs Stocks

## Overview

Your trading system has **two separate recommendation engines**:

### 1. Stock Recommendations
- **Endpoints:**
  - `/api/trading/recommendations` - Original (Elliott Wave only)
  - `/api/trading/recommendations/enhanced` - Enhanced (Multi-indicator)
- **What it does:** Returns BUY/SELL signals for stocks
- **Assets:** Equities like AAPL, MSFT, TSLA, SPY, QQQ, etc.
- **Strategies:** Technical analysis, Elliott Wave patterns, RSI, MACD, etc.

### 2. Options Recommendations
- **Endpoint:** `/api/options/scan`
- **What it does:** Returns options trading opportunities
- **Assets:** Options contracts on underlying stocks
- **Strategies:** 
  - Iron Condor
  - Calendar Spread
  - Butterfly Spread
  - Straddle/Strangle
  - Covered Call
  - Cash Secured Put

## Available Backtests

### 1. `compare_recommendations_backtest.py` - Stocks Only ✅ UPDATED
**What it tests:**
- Original recommendations (Elliott Wave) vs Enhanced recommendations (Multi-indicator)
- Only stock trading
- No options

**Use when:**
- You want to compare stock recommendation algorithms
- Testing technical indicator performance
- Evaluating Elliott Wave vs Multi-indicator strategies

**Run:**
```bash
python backtests/compare_recommendations_backtest.py
```

**Output:**
```
🔵 ORIGINAL RECOMMENDATIONS (Elliott Wave Only)
   💰 Final Portfolio:    $4,003.50
      💵 Cash:            $1,096.85
      📦 Positions:       $2,906.65
   📈 Total Return:       $3.50 (0.09%)
      ✅ Realized:        $0.00
      📊 Unrealized:      $3.50
   📊 Total Trades:       9 (9 buys, 0 sells)

🟢 ENHANCED RECOMMENDATIONS (Multi-Indicator)
   💰 Final Portfolio:    $4,050.00
   ...
```

---

### 2. `comprehensive_comparison_backtest.py` - Stocks + Options ✅ NEW
**What it tests:**
- Original stock recommendations vs Enhanced stock recommendations vs Options scanner
- Three separate portfolios running in parallel
- Mix of stock and options trading

**Use when:**
- You want to compare stocks vs options performance
- Testing if options strategies outperform stock strategies
- Evaluating the full capability of your trading system

**Run:**
```bash
python backtests/comprehensive_comparison_backtest.py
```

**Output:**
```
🔵 ORIGINAL (ELLIOTT WAVE)
   💰 Final Portfolio:    $4,003.50
      📈 Stocks:          $2,906.65
      📊 Options:         $0.00
   📈 Total Return:       $3.50 (0.09%)

🟢 ENHANCED (MULTI-INDICATOR)
   💰 Final Portfolio:    $4,050.00
      📈 Stocks:          $2,980.00
      📊 Options:         $0.00
   📈 Total Return:       $50.00 (1.25%)

🟡 OPTIONS (AUTOMATED SCANNER)
   💰 Final Portfolio:    $4,200.00
      📈 Stocks:          $0.00
      📊 Options:         $3,150.00
   📈 Total Return:       $200.00 (5.00%)

🏆 WINNER: Options
```

---

## Key Differences

### Stock Trading
- **Execution:** Buy shares at market price
- **Position Size:** Based on available cash (20% max per position)
- **P&L Calculation:** (Exit Price - Entry Price) × Quantity
- **Holding Period:** Indefinite until SELL signal
- **Risk:** Full value of shares

**Example:**
```
BUY 10 AAPL @ $180.00 = $1,800 cost
SELL 10 AAPL @ $185.00 = $1,850 proceeds
P&L = $50 profit
```

### Options Trading
- **Execution:** Pay premium for options contract
- **Position Size:** Based on strategy cost (Iron Condor ~$100, Straddle ~$500)
- **P&L Calculation:** Complex (depends on Greeks, time decay, volatility)
- **Holding Period:** Limited by expiration date
- **Risk:** Premium paid (defined risk strategies)

**Example:**
```
OPEN Iron Condor TSLA = $150 premium paid
Strategy expires profitable = $300 max profit
P&L = $150 profit (100% return on premium)
```

## Understanding the Results

### When Options Outperform
Options typically show better results when:
- **Market is range-bound** (Iron Condors excel)
- **High implied volatility** (Premium selling strategies)
- **Limited capital** (Options provide leverage)
- **Defined risk preferred** (Know max loss upfront)

### When Stocks Outperform
Stocks typically show better results when:
- **Strong trending markets** (Directional bets)
- **Low volatility** (Options premiums too cheap)
- **Long-term holds** (No expiration pressure)
- **Simple execution preferred** (No Greeks to manage)

## Portfolio Metrics Explained

### Cash
- **Liquid capital** available for new trades
- Decreases when opening positions
- Increases when closing positions

### Positions Value
- **Stocks:** Current market value of shares held
- **Options:** Current value of option contracts (estimated)

### Realized P&L
- Profit/loss from **closed positions**
- Only counts completed trades (buy + sell)
- This is "locked in" money

### Unrealized P&L
- Profit/loss from **open positions**
- Paper gains/losses
- Not locked in until you close the position

### Total Return
- **Realized P&L + Unrealized P&L**
- Complete picture of portfolio performance
- What matters for comparing strategies

## Important Notes

### ⚠️ These Are API Integration Tests
Both backtests are **NOT historical backtests**. They:
- ✅ Test if API endpoints work
- ✅ Validate recommendation retrieval
- ✅ Simulate trade execution logic
- ❌ Do NOT test historical performance (use same current data repeatedly)

### For True Historical Backtesting
Use these instead:
```bash
# Historical stock backtests
python backtests/comprehensive_two_year_backtest.py
python backtests/enhanced_market_regime_backtest.py

# Historical options backtests
python demo/demo_comprehensive_options_backtest.py
```

### Options Limitations in Current Backtest
The comprehensive backtest simplifies options trading:
- **No Greeks calculation** (Delta, Gamma, Theta, Vega)
- **No expiration handling** (positions don't expire)
- **Simplified P&L** (assumes 5% return on open positions)
- **No multi-leg execution** (treats strategies as single orders)

For accurate options backtesting with historical data and Greeks, use the full options backtesting suite in `demo/` or `services/strategy-service/`.

## Quick Command Reference

```bash
# Stock recommendations only
python backtests/compare_recommendations_backtest.py

# Stocks + Options comparison
python backtests/comprehensive_comparison_backtest.py

# Historical stock backtest (real data)
python backtests/comprehensive_two_year_backtest.py

# Historical options backtest (real data + Greeks)
python demo/demo_comprehensive_options_backtest.py
```

## Next Steps

1. **Run both backtests** to see the difference
2. **Check the results/** directory for detailed JSON output
3. **Compare performance** - which system generates better signals?
4. **Consider a hybrid approach** - use stocks for trends, options for income

The goal is to find the right mix of stock and options strategies that fits your:
- Risk tolerance
- Capital constraints
- Time commitment
- Market outlook














