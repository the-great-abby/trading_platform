# 0-DTE Without Owning Stock: Your Options

## TL;DR

**❌ Don't use naked calls** (unlimited risk, tiny premium)  
**✅ Use credit spreads instead** (defined risk, better risk/reward)

---

## The Question

"Do I need to own 100 shares? Can I trade uncovered calls?"

## The Answer

### Option 1: Covered Call (Original Strategy)
**Requires**: 100 shares per contract

```
SPY @ $444 × 100 shares = $44,400 required
Sell $445 call @ $0.25 = $25 income
Return: 0.06% in one day
```

✅ **Pros**: Low risk (already own stock), no margin  
❌ **Cons**: Need $44k+ capital, caps upside

---

### Option 2: Naked Call ⚠️ **NOT RECOMMENDED**
**Requires**: $8,900-$22,250 margin

```
Sell SPY $445 call @ $0.25 = $25 income
Margin Required: $8,900-$22,250
Max Loss: UNLIMITED
Return on Margin: 0.11-0.28%
```

**Why this is DANGEROUS:**
- Stock gaps up 3% → You lose $300+
- Unlimited risk for $25 credit
- Margin call = forced liquidation
- 0-DTE moves FAST (no time to react)
- Risk/reward: 10:1 or worse

❌ **STRONG WARNING**: Don't do this unless you're a professional with $100k+ capital

---

### Option 3: Credit Spread ✅ **RECOMMENDED**
**Requires**: $185 per spread (for 2-point width)

```
Sell SPY $445 call @ $0.25
Buy SPY $447 call @ $0.10
Net Credit: $0.15 × 100 = $15
Max Loss: $185
Max Profit: $15
Return on Capital: 8.1% in one day
```

✅ **Pros**: Defined risk, lower capital, better ROI  
✅ **Safe**: Max loss is known upfront  
✅ **Accessible**: Level 3 options (easier to get)  
✅ **Flexible**: Can adjust width based on risk tolerance

---

## Comparison Table

| Strategy | Capital Needed | Max Loss | Max Profit | Risk Level | Options Level |
|----------|---------------|----------|------------|------------|---------------|
| **Covered Call** | $44,000 | Unlimited (stock) | $125 | Low | 2 |
| **Naked Call** | $8,900-22,250 | **UNLIMITED** | $25 | **EXTREME** | 4-5 |
| **Credit Spread** | **$185** | **$185** | $15 | **Low** | 3 |

---

## How to Use Credit Spreads with the Screener

### Step 1: Run the screener as normal
```bash
make -f makefiles/Makefile.zero-dte screen
```

### Step 2: From the results, pick your short strike
```
Example output:
SPY $445 strike | $0.25 premium | Delta: 0.28
```

### Step 3: Manually create the spread
In your broker:
1. **SELL** SPY $445 call (the screener's pick)
2. **BUY** SPY $447 call (2 points higher)
3. Net credit: ~$0.15

### Step 4: Calculate your risk
```
Max Loss = (Spread Width - Credit) × 100
         = ($2 - $0.15) × 100
         = $185

Risk/Reward = $185 / $15 = 12.3:1
```

---

## Credit Spread Guidelines for 0-DTE

### Spread Width
- **1 point**: Tightest risk, lowest profit
- **2 points**: Sweet spot (recommended)
- **3 points**: More risk, more profit
- **5 points**: Too wide for 0-DTE (high risk)

### Example Spreads

#### Conservative (2-point)
```
Sell $445 call @ $0.25
Buy  $447 call @ $0.10
Credit: $15
Risk: $185
ROI: 8.1%
```

#### Moderate (3-point)
```
Sell $445 call @ $0.25
Buy  $448 call @ $0.07
Credit: $18
Risk: $282
ROI: 6.4%
```

#### Aggressive (5-point)
```
Sell $445 call @ $0.25
Buy  $450 call @ $0.05
Credit: $20
Risk: $480
ROI: 4.2%
```

**Recommendation**: Start with 2-point spreads

---

## Other Defined-Risk Alternatives

### Iron Condor
Sell both call and put spreads:
```bash
# Already in your system!
src/strategies/options/iron_condor_strategy.py
```

### Cash-Secured Put
Sell puts with cash ready:
```
Sell SPY $443 put @ $0.30
Cash Required: $44,300
If assigned: Buy 100 SPY @ $443
```

---

## Action Items

### If You Own Stock
✅ Use the screener as-is for covered calls
```bash
make -f makefiles/Makefile.zero-dte screen
```

### If You DON'T Own Stock
✅ Use the screener to find strikes, then create credit spreads:
```bash
# 1. Run screener
make -f makefiles/Makefile.zero-dte screen

# 2. Take suggested strike (e.g., $445)
# 3. In broker: Sell $445 call, Buy $447 call
# 4. Collect $10-20 credit with $185 risk
```

### Automatic Credit Spread Screening ✅ **NOW AVAILABLE!**

```bash
# Screen SPY for 2-point credit spreads
make -f makefiles/Makefile.zero-dte spreads

# Screen multiple tickers
make -f makefiles/Makefile.zero-dte spreads-multi

# Different spread widths
make -f makefiles/Makefile.zero-dte spreads-tight  # 1-point
make -f makefiles/Makefile.zero-dte spreads-wide   # 3-point
make -f makefiles/Makefile.zero-dte spreads-5wide  # 5-point

# Conservative/Aggressive presets
make -f makefiles/Makefile.zero-dte spreads-conservative
make -f makefiles/Makefile.zero-dte spreads-aggressive

# Custom parameters
make -f makefiles/Makefile.zero-dte spreads-custom \
  SYMBOL=TSLA \
  SPREAD_WIDTH=3.0 \
  MIN_CREDIT=0.15
```

**Output includes:**
- Both strikes (SELL/BUY)
- Net credit collected
- Max loss and max profit
- Return on capital
- Risk/reward ratio
- Probability of profit
- Capital requirements

---

## Risk Management Rules

1. **Never risk >1% of portfolio per trade**
   - $10k account → Max $100 risk → 1 spread max
   - $50k account → Max $500 risk → 2-3 spreads

2. **Close at 2x loss**
   - Collected $15 → Close if loss reaches $30

3. **Take profits at 50-70%**
   - Max profit $15 → Close at $8-11

4. **Monitor actively**
   - 0-DTE moves fast
   - Check every 30 minutes minimum

5. **Have exit plan before entry**
   - Time-based: Close by 3:30 PM
   - Profit-based: Close at 50%
   - Loss-based: Close at 2x credit

---

## Bottom Line

### ✅ DO THIS
- **Credit spreads** (2-3 point width)
- Defined risk, accessible, profitable
- Capital: ~$185-285 per spread
- Return: 5-10% in one day

### ❌ DON'T DO THIS
- **Naked calls** on 0-DTE
- Unlimited risk, tiny premium
- Can blow up your account
- Professional traders only

### 📚 Learn More
- [Full Risk Profiles Guide](../docs/ZERO_DTE_RISK_PROFILES.md)
- [0-DTE Screener Guide](../docs/ZERO_DTE_SCREENER_GUIDE.md)
- [Options Strategies Guide](../docs/OPTIONS_STRATEGIES_GUIDE.md)

---

**Questions? Want credit spread screening added?** Let me know!

