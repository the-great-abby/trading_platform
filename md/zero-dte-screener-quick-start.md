# 0-DTE Covered Call Screener - Quick Start

## What is it?

A specialized screener for **Zero Days to Expiration (0-DTE)** covered call opportunities. Scans for same-day expiration options that can generate daily income with defined risk.

## Quick Commands

### Basic Screening
```bash
# Screen SPY (most liquid)
make -f makefiles/Makefile.zero-dte screen

# Screen multiple tickers
make -f makefiles/Makefile.zero-dte screen-multi

# Quick ticker-specific
make -f makefiles/Makefile.zero-dte spy
make -f makefiles/Makefile.zero-dte qqq
make -f makefiles/Makefile.zero-dte iwm
```

### Strategy Presets
```bash
# Conservative (high probability)
make -f makefiles/Makefile.zero-dte screen-conservative

# Aggressive (high premium)
make -f makefiles/Makefile.zero-dte screen-aggressive

# Tight (30-delta sweet spot)
make -f makefiles/Makefile.zero-dte screen-tight
```

### Custom Parameters
```bash
# Custom delta band
make -f makefiles/Makefile.zero-dte screen-custom \
  SYMBOL=TSLA \
  DELTA_LO=0.20 \
  DELTA_HI=0.40

# Custom OTM range
make -f makefiles/Makefile.zero-dte screen-custom \
  SYMBOL=SPY \
  MIN_OTM_PCT=0.01 \
  MAX_OTM_PCT=0.05
```

### P&L Tracking
```bash
# After market close, mark realized P&L
make -f makefiles/Makefile.zero-dte mark \
  CSV_PATH=./data/0dte_covered_calls_2025-10-21.csv \
  CLOSE_PRICE=445.32
```

## Key Features

✅ **Real-time screening** - Polygon.io snapshot API  
✅ **Delta-based filtering** - Target 15-35 delta range  
✅ **OTM band screening** - Focus on 0-3% above spot  
✅ **Spread quality checks** - Reject wide spreads  
✅ **Liquidity filtering** - Minimum open interest  
✅ **POP estimation** - Probability of profit calculation  
✅ **Multiple ranking metrics** - Premium yield, max profit, POP  
✅ **P&L tracking** - Mark realized results after close

## Requirements

- **Polygon.io API key** (Options Advanced plan)
- **Python 3.10+**
- **100 shares** of underlying per contract

## Setup

```bash
# Set API key
export POLYGON_API_KEY=your_key_here

# Test the screener
make -f makefiles/Makefile.zero-dte info
```

## Daily Workflow

### Morning (9:45 AM ET)
```bash
make -f makefiles/Makefile.zero-dte cron-morning
# Review results, enter best 1-3 opportunities
```

### Midday (12:00 PM ET)
```bash
make -f makefiles/Makefile.zero-dte cron-noon
# Re-scan, check existing positions
```

### Close (3:30 PM ET)
```bash
make -f makefiles/Makefile.zero-dte cron-close
# Final scan, close positions if needed
```

### After Close (4:00+ PM ET)
```bash
make -f makefiles/Makefile.zero-dte mark \
  CSV_PATH=./data/0dte_covered_calls_$(date +%Y-%m-%d).csv \
  CLOSE_PRICE=<closing_price>
```

## Example Output

```
================================================================================
📊 0-DTE COVERED CALL CANDIDATES
================================================================================
ticker    strike    mid      premium_yield  delta   max_profit  breakeven  pop_est  open_interest  score
SPY       $445.00   $0.25    0.06%         0.28    $0.28      $443.75    72.3%    1250           0.543
SPY       $446.00   $0.18    0.04%         0.22    $0.21      $443.82    78.1%    980            0.498
QQQ       $375.00   $0.32    0.09%         0.31    $0.35      $373.68    71.5%    2150           0.587
================================================================================

🎯 TOP 3 RECOMMENDATIONS:

1. QQQ $375.00 strike
   Premium: $0.32 (0.09% yield)
   Max Profit: $0.35 | Breakeven: $373.68
   Delta: 0.310 | POP: 71.5%
   Open Interest: 2150 | Score: 0.587

2. SPY $445.00 strike
   Premium: $0.25 (0.06% yield)
   Max Profit: $0.28 | Breakeven: $443.75
   Delta: 0.280 | POP: 72.3%
   Open Interest: 1250 | Score: 0.543

3. SPY $446.00 strike
   Premium: $0.18 (0.04% yield)
   Max Profit: $0.21 | Breakeven: $443.82
   Delta: 0.220 | POP: 78.1%
   Open Interest: 980 | Score: 0.498
```

## Understanding the Metrics

| Metric | Description | Good Values |
|--------|-------------|-------------|
| **Premium Yield** | Return on stock capital | 0.1-0.3% daily |
| **Delta** | Probability of assignment | 0.15-0.35 (70-85% POP) |
| **OTM %** | Distance above spot | 0-3% |
| **Max Profit** | If expires OTM | $0.10-$0.50 per share |
| **Breakeven** | Protection level | 0.1-0.3% below spot |
| **POP** | Probability of profit | 70-85% |
| **Open Interest** | Liquidity indicator | >100 for SPY/QQQ |

## Best Practices

### ✅ Do's
- Screen early (best at market open)
- Verify stock ownership (100 shares per contract)
- Check spreads (tight = good execution)
- Start small (1-2 contracts)
- Use liquid names (SPY, QQQ, IWM)

### ❌ Don'ts
- Don't chase (wait for next day)
- Don't overtrade (quality over quantity)
- Don't ignore Greeks (delta = probability)
- Don't hold too long (exit by 3:30 PM if profitable)
- Don't trade illiquid options

## Target Performance

- **Win Rate**: 70-85%
- **Average Premium**: 0.1-0.3% of stock price
- **Daily Return**: 0.1-0.3% on deployed capital
- **Annualized**: 25-75% (if done daily)

## Full Documentation

For complete details, see:
- [Full Guide](../docs/ZERO_DTE_SCREENER_GUIDE.md)
- [Options Strategies](../docs/OPTIONS_STRATEGIES_GUIDE.md)
- [Polygon.io Blog Post](https://polygon.io/blog/build-a-0-dte-covered-call-screener-for-spy-with-polygon-io)

## Get Help

```bash
# Show all commands
make -f makefiles/Makefile.zero-dte help

# Show strategy info
make -f makefiles/Makefile.zero-dte info

# Run interactive demo
python demo/demo_zero_dte_screener.py
```

---

**Ready to start?**
```bash
make -f makefiles/Makefile.zero-dte screen
```

