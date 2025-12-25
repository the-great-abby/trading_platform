# 0-DTE Covered Call Screener Guide

## Overview

The **0-DTE Covered Call Screener** is a specialized strategy for screening and trading zero-days-to-expiration (0-DTE) covered call opportunities. It leverages Polygon.io's real-time options snapshot API to find high-probability, income-generating trades that expire the same day.

## What is 0-DTE?

**0-DTE** (Zero Days to Expiration) refers to options that expire on the same trading day. These options have unique characteristics:

- ✅ **Rapid time decay** - theta works in your favor fast
- ✅ **Lower premium** - but can be collected daily for consistent income
- ✅ **High probability** - less time for stock to move against you
- ✅ **Defined risk** - known maximum profit and loss
- ⚠️ **Requires active management** - positions expire same day
- ⚠️ **Liquidity matters** - need tight spreads for entry/exit

## Key Features

### 🎯 Smart Screening
- **Delta-based filtering** - Target 15-35 delta for optimal risk/reward
- **OTM band screening** - Focus on 0-3% out-of-the-money calls
- **Spread quality checks** - Reject quotes with >75% spread-to-mid
- **Liquidity filtering** - Minimum open interest and volume requirements

### 📊 Advanced Analytics
- **Probability of profit** - Black-Scholes based POP estimation
- **Premium yield** - Return on capital per contract
- **Max profit calculation** - Cap if assigned at strike
- **Breakeven analysis** - Downside protection level

### 🔄 Complete Workflow
- **Morning scan** - Identify opportunities at market open
- **Midday re-scan** - Adjust for market movement
- **Close scan** - Last-minute opportunities
- **P&L marking** - Track actual vs expected results

## Installation & Requirements

### Prerequisites
1. **Polygon.io API Key** with Options Advanced plan
2. **Python 3.10+** with trading environment
3. **Capital for your chosen strategy**:
   - **Covered Call**: 100 shares per contract (~$44k for SPY)
   - **Credit Spread**: Width × 100 (~$185 for 2-point spread) ← **RECOMMENDED**
   - **Naked Call**: ⚠️ **NOT RECOMMENDED** (unlimited risk)

> 💡 **Don't own stock?** Use **credit spreads** instead! See [Risk Profiles Guide](./ZERO_DTE_RISK_PROFILES.md) for safer alternatives.

### Setup
```bash
# Set API key
export POLYGON_API_KEY=your_key_here

# Test the screener
make -f makefiles/Makefile.zero-dte info
```

## Usage

### Quick Start

#### 1. Basic Screening (SPY)
```bash
# Screen SPY with default parameters
make -f makefiles/Makefile.zero-dte screen

# Screen SPY with custom parameters  
make -f makefiles/Makefile.zero-dte screen-custom SYMBOL=SPY DELTA_LO=0.20 DELTA_HI=0.40
```

#### 2. Multi-Ticker Screening
```bash
# Screen SPY, QQQ, IWM
make -f makefiles/Makefile.zero-dte screen-multi

# Screen custom tickers
make -f makefiles/Makefile.zero-dte screen-custom SYMBOLS="AAPL,TSLA,NVDA"
```

#### 3. Preset Strategies

##### Conservative (High POP)
```bash
make -f makefiles/Makefile.zero-dte screen-conservative
# • Lower delta (10-25)
# • Wider OTM (2-5%)
# • Ranks by probability of profit
```

##### Aggressive (High Premium)
```bash
make -f makefiles/Makefile.zero-dte screen-aggressive
# • Higher delta (35-55)
# • Wider OTM (0-5%)
# • Ranks by max profit
```

##### Tight (Standard 30-Delta)
```bash
make -f makefiles/Makefile.zero-dte screen-tight
# • Tight delta band (25-35)
# • Standard OTM (0-3%)
# • Best risk/reward balance
```

### Advanced Usage

#### Custom Parameters via Python Script
```bash
python scripts/zero_dte_screener.py screen \
  --symbol SPY \
  --delta-lo 0.20 \
  --delta-hi 0.35 \
  --min-otm-pct 0.01 \
  --max-otm-pct 0.04 \
  --min-bid 0.08 \
  --rank-metric premium_yield \
  --outdir ./data
```

#### Parameter Reference
| Parameter | Description | Default | Good Range |
|-----------|-------------|---------|------------|
| `symbol` | Single ticker to screen | SPY | Any liquid stock |
| `symbols` | Multiple tickers (comma-separated) | - | SPY,QQQ,IWM |
| `delta-lo` | Minimum delta | 0.15 | 0.10-0.25 |
| `delta-hi` | Maximum delta | 0.35 | 0.30-0.50 |
| `min-otm-pct` | Min OTM % above spot | 0.00 | 0.00-0.02 |
| `max-otm-pct` | Max OTM % above spot | 0.03 | 0.03-0.08 |
| `min-bid` | Minimum bid price | $0.05 | $0.03-$0.15 |
| `min-open-interest` | Min open interest | 1 | 1-100 |
| `max-spread-to-mid` | Max spread % of mid | 0.75 | 0.50-1.00 |
| `rank-metric` | Ranking method | premium_yield | See below |

#### Ranking Metrics
- **`premium_yield`** - Income per dollar of stock (default)
- **`max_profit`** - Maximum profit in dollars
- **`pop_est`** - Probability of profit estimate
- **`score`** - Composite score (weighted combination)

### P&L Tracking

#### Mark Realized P&L After Close
```bash
# After market close, mark your results
make -f makefiles/Makefile.zero-dte mark \
  CSV_PATH=./data/0dte_covered_calls_2025-10-21.csv \
  CLOSE_PRICE=445.32

# Output shows:
# • Total P&L
# • Win rate
# • Assignment rate
# • Return on capital
```

## Strategy Patterns

### Daily Income Pattern
**Objective**: Consistent daily premium collection

```bash
# Morning scan (9:45 AM ET)
make -f makefiles/Makefile.zero-dte cron-morning

# Enter positions: 10:00-10:30 AM
# Monitor: Let time decay work for you
# Exit: 3:00-3:30 PM or let expire
```

### High-Probability Pattern
**Objective**: Maximum success rate

```bash
# Use conservative settings
make -f makefiles/Makefile.zero-dte screen-conservative

# Characteristics:
# • 10-25 delta (far OTM)
# • 2-5% above spot
# • Lower premium but higher POP
# • Best for sideways/down markets
```

### High-Premium Pattern
**Objective**: Maximum income per contract

```bash
# Use aggressive settings
make -f makefiles/Makefile.zero-dte screen-aggressive

# Characteristics:
# • 35-55 delta (closer to ATM)
# • 0-5% OTM range
# • Higher premium, lower POP
# • Best for low volatility markets
```

## Integration with Existing System

### As a Strategy
```python
from src.strategies.options import ZeroDTECoveredCallStrategy

# Create strategy instance
strategy = ZeroDTECoveredCallStrategy(
    delta_lo=0.20,
    delta_hi=0.35,
    max_otm_pct=0.03,
    rank_metric="premium_yield"
)

# Run scan
results = strategy.scan_multiple_tickers(["SPY", "QQQ"])

# Get top candidate
if not results.empty:
    top = results.iloc[0]
    print(f"Best: {top['ticker']} ${top['strike']} for ${top['mid']}")
```

### Automated Scanning
```python
import pandas as pd
from src.strategies.options import ZeroDTECoveredCallStrategy

def morning_scan():
    """Run morning 0-DTE scan"""
    strategy = ZeroDTECoveredCallStrategy(
        target_tickers=["SPY", "QQQ", "IWM"]
    )
    
    results = strategy.scan_multiple_tickers()
    
    # Save to database or send alert
    if not results.empty:
        filepath = strategy.save_scan_results(results)
        send_alert(f"Found {len(results)} 0-DTE opportunities")
        
    return results
```

## Best Practices

### ✅ Do's
1. **Screen early** - Best opportunities found at market open
2. **Verify ownership** - Need 100 shares per contract
3. **Check spreads** - Wide spreads = poor execution
4. **Monitor open interest** - Higher is better for fills
5. **Track your results** - Use P&L marking feature
6. **Start small** - 1-2 contracts max initially
7. **Use liquid names** - SPY, QQQ, IWM work best

### ❌ Don'ts
1. **Don't chase** - If you miss entry, wait for next day
2. **Don't overtrade** - Quality over quantity
3. **Don't ignore Greeks** - Delta tells probability
4. **Don't hold too long** - Exit by 3:30 PM if profitable
5. **Don't trade illiquid options** - Stuck with bad fills
6. **Don't go naked** - Must own stock (covered call)
7. **Don't forget assignment** - Stock may be called away

## Example Workflow

### Morning (9:30-10:30 AM ET)
```bash
# 1. Run morning scan
make -f makefiles/Makefile.zero-dte cron-morning

# 2. Review results
# Look for:
# • Premium yield > 0.1% (0.1% daily = 25% annually)
# • Delta 25-35 (70-75% POP)
# • Tight spreads (< 50% of mid)
# • OI > 100

# 3. Execute best 1-3 opportunities
# Enter via broker or API
```

### Midday (12:00-1:00 PM ET)
```bash
# Re-scan for new opportunities
make -f makefiles/Makefile.zero-dte cron-noon

# Check existing positions
# Consider early exit if 50-70% of max profit reached
```

### Close (3:00-4:00 PM ET)
```bash
# Final scan for last-minute premium
make -f makefiles/Makefile.zero-dte cron-close

# Close existing positions if:
# • Profitable and want to lock in
# • At risk of assignment and don't want to sell stock
```

### After Close (4:00+ PM ET)
```bash
# Mark realized P&L
make -f makefiles/Makefile.zero-dte mark \
  CSV_PATH=./data/0dte_covered_calls_$(date +%Y-%m-%d).csv \
  CLOSE_PRICE=445.32

# Review results
# • What worked?
# • What didn't?
# • Adjust parameters for tomorrow
```

## Performance Metrics

### Target Metrics
- **Win Rate**: 70-85% (based on delta selection)
- **Average Premium**: 0.1-0.3% of stock price
- **Daily Return**: 0.1-0.3% on deployed capital
- **Annualized**: 25-75% (if done daily)

### Risk Metrics
- **Max Loss**: Stock goes to zero (same as owning stock)
- **Assignment Risk**: ~30% with 30-delta calls
- **Opportunity Cost**: Miss upside above strike

## Troubleshooting

### No Candidates Found
**Causes:**
- Market closed or holiday
- No options expiring today
- Parameters too strict
- Low volatility (premiums too small)

**Solutions:**
```bash
# Widen parameters
make -f makefiles/Makefile.zero-dte screen-wide

# Lower minimum bid
make -f makefiles/Makefile.zero-dte screen MIN_BID=0.03

# Try different tickers
make -f makefiles/Makefile.zero-dte screen SYMBOL=QQQ
```

### API Rate Limits
**Cause:** Polygon.io rate limiting

**Solution:**
- Free tier: Very limited
- Starter plan: 5 requests/minute
- Advanced plan: Recommended for this tool

### Wide Spreads
**Cause:** Illiquid options

**Solutions:**
- Trade only SPY, QQQ, IWM
- Increase min_open_interest
- Use tighter OTM range

## Cron Automation

### Setup Cron Jobs
```cron
# Edit crontab
crontab -e

# Add these lines (adjust times for your timezone):

# Morning scan (9:45 AM ET)
45 9 * * 1-5 cd /path/to/trading && make -f makefiles/Makefile.zero-dte cron-morning >> logs/0dte_morning.log 2>&1

# Noon scan (12:00 PM ET)
0 12 * * 1-5 cd /path/to/trading && make -f makefiles/Makefile.zero-dte cron-noon >> logs/0dte_noon.log 2>&1

# Near-close scan (3:30 PM ET)
30 15 * * 1-5 cd /path/to/trading && make -f makefiles/Makefile.zero-dte cron-close >> logs/0dte_close.log 2>&1
```

## Additional Resources

### Related Documentation
- [Options Strategies Guide](./OPTIONS_STRATEGIES_GUIDE.md)
- [Covered Call Strategy](./COVERED_CALL_GUIDE.md)
- [Polygon.io API Docs](https://polygon.io/docs/options)

### Demo & Examples
```bash
# Run interactive demo
python demo/demo_zero_dte_screener.py

# View available commands
make -f makefiles/Makefile.zero-dte help
```

### Support
- Polygon.io blog post: [Build a 0-DTE Covered Call Screener](https://polygon.io/blog/build-a-0-dte-covered-call-screener-for-spy-with-polygon-io)
- GitHub Issues: Report bugs or request features

## Disclaimer

⚠️ **Important Risk Disclosure**

This screener is for educational and informational purposes only. It is not financial advice.

**Risks:**
- Options involve significant risk and are not suitable for all investors
- 0-DTE options have unique risks due to rapid time decay
- Assignment can occur at any time (especially near ex-dividend)
- Past performance does not guarantee future results
- You can lose your entire investment

**Requirements:**
- Must own 100 shares of underlying per contract (covered call)
- Understanding of options mechanics
- Appropriate risk capital only
- Paper trading recommended before live trading

**Always:**
- Understand what you're trading
- Start small and scale up
- Test thoroughly in paper trading
- Consult a financial advisor for personalized advice

---

## Quick Reference Card

```bash
# Daily Workflow
make -f makefiles/Makefile.zero-dte screen        # Basic SPY scan
make -f makefiles/Makefile.zero-dte screen-multi  # Multi-ticker
make -f makefiles/Makefile.zero-dte spy           # Quick SPY scan
make -f makefiles/Makefile.zero-dte qqq           # Quick QQQ scan

# Custom Screening
make -f makefiles/Makefile.zero-dte screen-conservative  # High POP
make -f makefiles/Makefile.zero-dte screen-aggressive    # High premium
make -f makefiles/Makefile.zero-dte screen-tight         # 30-delta

# P&L Tracking
make -f makefiles/Makefile.zero-dte mark \
  CSV_PATH=./data/0dte_covered_calls_2025-10-21.csv \
  CLOSE_PRICE=445.32

# Utilities
make -f makefiles/Makefile.zero-dte info           # Strategy info
make -f makefiles/Makefile.zero-dte list-results   # Show results
make -f makefiles/Makefile.zero-dte clean-results  # Clean old files
```

---

**Last Updated:** October 21, 2025  
**Version:** 1.0.0  
**Author:** Orion (Trading System AI)

