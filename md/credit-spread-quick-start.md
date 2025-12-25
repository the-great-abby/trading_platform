# 0-DTE Credit Spreads - Quick Start

## What Are Credit Spreads?

A **credit spread** is:
- **SELL** a lower strike call (collect premium)
- **BUY** a higher strike call (cap your risk)
- **Net result**: Defined risk, no stock ownership needed

## Why Credit Spreads > Naked Calls?

| Naked Call | Credit Spread |
|------------|---------------|
| ⚠️ Unlimited risk | ✅ Defined risk |
| $9,000+ margin | ✅ $185 capital |
| $25 profit | ✅ $15 profit |
| 0.3% return | ✅ 8% return |
| **DON'T DO THIS** | **DO THIS** |

## Quick Commands

### Basic Screening
```bash
# Screen SPY for 2-point spreads (most common)
make -f makefiles/Makefile.zero-dte spreads

# Multiple tickers (SPY, QQQ, IWM)
make -f makefiles/Makefile.zero-dte spreads-multi

# Quick ticker shortcuts
make -f makefiles/Makefile.zero-dte spreads-spy
make -f makefiles/Makefile.zero-dte spreads-qqq
make -f makefiles/Makefile.zero-dte spreads-iwm
```

### Spread Width Options
```bash
# Tight 1-point spreads (lowest risk, lowest profit)
make -f makefiles/Makefile.zero-dte spreads-tight

# Standard 2-point spreads (recommended)
make -f makefiles/Makefile.zero-dte spreads

# Wide 3-point spreads
make -f makefiles/Makefile.zero-dte spreads-wide

# Very wide 5-point spreads (max risk/reward)
make -f makefiles/Makefile.zero-dte spreads-5wide
```

### Strategy Presets
```bash
# Conservative (high probability, low risk)
make -f makefiles/Makefile.zero-dte spreads-conservative
# • 2-point width
# • 10-25 delta
# • 2-5% OTM
# • High POP

# Aggressive (high premium, higher risk)
make -f makefiles/Makefile.zero-dte spreads-aggressive
# • 3-point width
# • 30-50 delta
# • 0-3% OTM
# • Higher return
```

### Custom Parameters
```bash
# Custom spread width and credit
make -f makefiles/Makefile.zero-dte spreads-custom \
  SYMBOL=TSLA \
  SPREAD_WIDTH=3.0 \
  MIN_CREDIT=0.15

# Very specific parameters
python scripts/zero_dte_screener.py screen-spreads \
  --symbol SPY \
  --spread-width 2.5 \
  --min-credit 0.12 \
  --delta-lo 0.20 \
  --delta-hi 0.35
```

## Example Output

```
================================================================================
💰 0-DTE CREDIT SPREAD CANDIDATES
================================================================================
ticker  short_strike  long_strike  spread_width  net_credit  max_loss  max_profit  return_on_capital  risk_reward_ratio
SPY     $445.00       $447.00      2.0           $0.15       $1.85     $0.15       8.1%               12.3:1
SPY     $446.00       $448.00      2.0           $0.13       $1.87     $0.13       7.0%               14.4:1
QQQ     $375.00       $377.00      2.0           $0.18       $1.82     $0.18       9.9%               10.1:1
================================================================================

🎯 TOP 3 CREDIT SPREAD RECOMMENDATIONS:

1. QQQ $375.00/$377.00 spread (2-wide)
   SELL  1x $375.00 call @ $0.32
   BUY   1x $377.00 call @ $0.14
   ───────────────────────────────────
   Net Credit: $0.18 × 100 = $18
   Max Loss: $1.82 × 100 = $182
   Max Profit: $0.18 × 100 = $18
   Return on Capital: 9.9%
   Risk/Reward: 10.1:1
   POP: 71.5%
   Score: 0.587

2. SPY $445.00/$447.00 spread (2-wide)
   SELL  1x $445.00 call @ $0.25
   BUY   1x $447.00 call @ $0.10
   ───────────────────────────────────
   Net Credit: $0.15 × 100 = $15
   Max Loss: $1.85 × 100 = $185
   Max Profit: $0.15 × 100 = $15
   Return on Capital: 8.1%
   Risk/Reward: 12.3:1
   POP: 72.3%
   Score: 0.543

💵 CAPITAL REQUIREMENTS:
   Per Spread: $185 (for 2-wide)
   For 5 Spreads: $925
   For 10 Spreads: $1,850
```

## How to Trade

### Step 1: Run the screener
```bash
make -f makefiles/Makefile.zero-dte spreads
```

### Step 2: Review top recommendations
Look for:
- ✅ Return on capital > 7%
- ✅ POP > 70%
- ✅ Risk/reward < 15:1
- ✅ Net credit > $0.10

### Step 3: Execute in your broker
Using the QQQ example above:

**In your broker's options chain:**
1. Find QQQ options expiring today
2. **SELL TO OPEN** 1 contract of $375 call
3. **BUY TO OPEN** 1 contract of $377 call
4. Order type: "Vertical Spread" or place as combo
5. Limit price: $0.18 credit (or better)

### Step 4: Monitor
- Check every 30 minutes
- Close at 50-70% of max profit ($9-13)
- Close at 2x loss ($36)
- Or let expire if OTM

## Spread Width Guide

### 1-Point Spreads
```
Capital: ~$85-95 per spread
Profit: ~$5-10
Return: 5-10%
Best for: Low capital, conservative
```

### 2-Point Spreads (Recommended)
```
Capital: ~$180-190 per spread
Profit: ~$10-20
Return: 7-12%
Best for: Most traders, balance of risk/reward
```

### 3-Point Spreads
```
Capital: ~$280-290 per spread
Profit: ~$10-20
Return: 4-7%
Best for: More risk tolerance
```

### 5-Point Spreads
```
Capital: ~$480-490 per spread
Profit: ~$10-20
Return: 2-4%
Best for: Advanced traders only
```

**Recommendation**: Start with 2-point spreads

## Capital Scaling

### $1,000 Account
```
1 spread = $185 (18.5% of capital)
Conservative: 1 spread max
```

### $5,000 Account
```
1 spread = $185 (3.7% of capital)
Conservative: 2-3 spreads
Moderate: 5 spreads
```

### $10,000 Account
```
1 spread = $185 (1.85% of capital)
Conservative: 5 spreads
Moderate: 10 spreads
Aggressive: 15 spreads
```

### $25,000+ Account
```
Scale proportionally
Never exceed 50% of capital in spreads
Leave room for adjustments
```

## Risk Management

### Position Sizing
- Never risk >1-2% per spread
- Leave capital for adjustments
- Start with 1-2 spreads

### Exit Rules
1. **Profit Target**: Close at 50-70% of max profit
2. **Stop Loss**: Close if loss reaches 2x credit
3. **Time-Based**: Close by 3:30 PM
4. **Let Expire**: If confidently OTM at 3:45 PM

### Don't Do This
❌ Hold losing spreads hoping for recovery  
❌ Add to losing positions  
❌ Use 100% of capital  
❌ Trade illiquid underlyings  
❌ Trade without stops  

## Daily Workflow

### Morning (9:45 AM ET)
```bash
# Run credit spread screener
make -f makefiles/Makefile.zero-dte spreads-multi

# Review recommendations
# Enter best 2-5 spreads
```

### Midday (12:00 PM ET)
```bash
# Check positions
# Take profits on 50-70% winners
# Close 2x losers
```

### Close (3:30 PM ET)
```bash
# Final P&L check
# Close any at-risk positions
# Let OTM expire
```

### After Market (4:00+ PM ET)
```bash
# Review performance
# Adjust strategy for tomorrow
```

## Comparison to Other Strategies

### vs. Covered Calls
| Covered Call | Credit Spread |
|-------------|---------------|
| Need $44k stock | Need $185 |
| $25 profit | $15 profit |
| 0.06% return | 8% return |
| Unlimited downside | Defined max loss |

**Winner**: Credit Spread (27x more capital efficient!)

### vs. Naked Calls
| Naked Call | Credit Spread |
|------------|---------------|
| Unlimited risk | Defined risk ($185) |
| $9,000 margin | $185 capital |
| $25 profit | $15 profit |
| 0.3% return | 8% return |

**Winner**: Credit Spread (MUCH safer!)

### vs. Iron Condor
| Iron Condor | Credit Spread |
|-------------|---------------|
| 4 legs | 2 legs |
| $370 capital | $185 capital |
| $30 profit | $15 profit |
| More complex | Simpler |

**Winner**: Depends on market conditions

## Troubleshooting

### "No candidates found"
- Market closed or no 0-DTE today
- Parameters too strict
- Try wider spread_width
- Try lower min_credit

### "Spreads too wide"
- Use `spreads-tight` instead
- Increase `--max-spread-to-mid 1.0`
- Trade only SPY/QQQ/IWM

### "Can't fill at credit price"
- Use limit orders
- Be patient
- Accept $0.01-0.02 less if needed
- Don't chase - wait for next opportunity

## Full Documentation

- [Risk Profiles Guide](../docs/ZERO_DTE_RISK_PROFILES.md)
- [Full Screener Guide](../docs/ZERO_DTE_SCREENER_GUIDE.md)
- [No-Stock Alternatives](./0dte-no-stock-alternatives.md)

## Help Commands

```bash
# Show all options
make -f makefiles/Makefile.zero-dte help

# Show strategy info
make -f makefiles/Makefile.zero-dte info

# Test installation
python scripts/zero_dte_screener.py screen-spreads --help
```

---

**Ready to start?**
```bash
make -f makefiles/Makefile.zero-dte spreads
```

**No stock ownership required. Defined risk. Better returns. This is the way.** 🚀

