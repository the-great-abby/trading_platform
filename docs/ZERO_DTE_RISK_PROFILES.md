# 0-DTE Risk Profiles: Covered vs. Naked vs. Spreads

## Overview

The 0-DTE screener can be used for different strategies with vastly different risk profiles. **Understanding these risks is critical before trading.**

## Strategy Comparison

| Strategy | Stock Requirement | Risk | Margin Required | Options Level | Recommended For |
|----------|------------------|------|-----------------|---------------|-----------------|
| **Covered Call** | ✅ Own 100 shares | Limited | None (beyond stock) | Level 2 | Most traders |
| **Naked Call** | ❌ None | ⚠️ Unlimited | Very High | Level 4-5 | **NOT RECOMMENDED** |
| **Credit Spread** | ❌ None | ✅ Defined | Moderate | Level 3 | **BEST ALTERNATIVE** |
| **Cash-Secured Put** | ❌ None | Limited | High (cash for shares) | Level 2 | Bullish traders |

---

## 1. Covered Call (Current Default)

### Description
- **Own 100 shares** of the underlying
- **Sell 1 call** against those shares
- Collect premium as income

### Risk Profile
```
Max Loss: Stock goes to zero
Max Profit: Premium + (Strike - Purchase Price)
Breakeven: Purchase Price - Premium

Example:
- Own 100 SPY @ $444
- Sell 1x $445 call @ $0.25
- Max Profit: $125 ($25 premium + $100 stock gain)
- Max Loss: $44,400 (if SPY → $0)
- Breakeven: $443.75
```

### Pros
✅ You already own the stock  
✅ Generates additional income on holdings  
✅ No margin requirement  
✅ Lower options approval needed  
✅ Defined risk (same as owning stock)  

### Cons
❌ Caps upside at strike price  
❌ Stock can be called away  
❌ Requires significant capital ($44,400 for SPY)  
❌ Still exposed to stock downside  

### When to Use
- You own the stock and want income
- Neutral to slightly bullish outlook
- Willing to sell stock at strike
- Long-term holder monetizing holdings

---

## 2. Naked/Uncovered Call ⚠️

### Description
- **DO NOT own stock**
- **Sell call** without any hedge
- Theoretically unlimited risk

### Risk Profile
```
Max Loss: UNLIMITED (if stock goes to infinity)
Max Profit: Premium collected
Breakeven: Strike + Premium

Example:
- Sell 1x SPY $445 call @ $0.25
- Max Profit: $25
- Max Loss: UNLIMITED
- Margin Required: ~$9,000+ (varies by broker)
```

### Why This is EXTREMELY DANGEROUS for 0-DTE

#### 1. **Fast Price Movements**
0-DTE options can move 100-500% in minutes. A $0.25 option can become $5.00 instantly.

#### 2. **No Time to React**
- Market opens: Sell call for $0.25 credit
- 10:00 AM: Stock jumps 2% on news
- 10:01 AM: Call now worth $2.50
- 10:02 AM: Margin call + forced liquidation
- Loss: $225+ per contract (9x the premium)

#### 3. **Gap Risk**
Stocks can gap up overnight or intraday:
- Earnings surprise
- FDA approval
- Takeover announcement
- Market crash (short covering)

#### 4. **Margin Requirements**
Most brokers require 20-50% of the notional value as margin:
- Sell SPY $445 call
- Margin: $8,900 - $22,250
- For $25 of premium!
- Return on margin: 0.11% - 0.28%

#### 5. **Assignment Risk**
You can be assigned and forced to deliver shares:
- Assignment: Deliver 100 shares @ $445
- Stock price: $450
- Loss: $500 - $25 premium = $475 loss
- For a $25 credit!

### ⛔ **STRONG WARNING**

**DO NOT TRADE NAKED CALLS ON 0-DTE UNLESS:**
- You have $100,000+ trading capital
- You understand unlimited risk
- You have professional-level risk management
- Your broker allows it (Level 4-5 approval)
- You can monitor positions full-time

**For 99% of traders: DON'T DO THIS.**

---

## 3. Credit Spread ✅ (RECOMMENDED ALTERNATIVE)

### Description
- **Sell call** at lower strike (collect premium)
- **Buy call** at higher strike (define max loss)
- Defined risk, no stock required

### Risk Profile
```
Max Loss: (Strike Width - Credit) × 100
Max Profit: Credit × 100
Breakeven: Short Strike + Credit

Example:
- Sell 1x SPY $445 call @ $0.25
- Buy 1x SPY $447 call @ $0.10
- Net Credit: $0.15 × 100 = $15
- Max Loss: ($2 - $0.15) × 100 = $185
- Max Profit: $15
- Risk/Reward: $185 / $15 = 12.3:1
```

### Pros
✅ **Defined maximum loss**  
✅ No stock ownership required  
✅ Lower margin ($185 vs $9,000+)  
✅ Better capital efficiency  
✅ Can't be blown out by gap  
✅ Level 3 options (more accessible)  

### Cons
❌ Lower profit potential  
❌ Wider spreads = higher risk  
❌ Both legs need liquidity  

### When to Use
- Want income without owning stock
- Need defined risk
- Limited capital
- Can't get Level 4-5 approval
- Want better risk/reward

### 0-DTE Credit Spread Strategy

For 0-DTE, use **narrow spreads** (1-2 points wide):

```bash
# SPY Example (tight spread)
Sell: $445 call @ $0.25
Buy:  $446 call @ $0.15
Credit: $0.10
Max Loss: $90
Max Profit: $10
Return: 11.1% in one day

# Wider spread (more risk)
Sell: $445 call @ $0.25
Buy:  $448 call @ $0.05
Credit: $0.20
Max Loss: $280
Max Profit: $20
Return: 7.1% in one day
```

---

## 4. Cash-Secured Put

### Description
- **Sell put** with cash to buy 100 shares if assigned
- Bullish strategy
- Generate income while waiting to buy stock

### Risk Profile
```
Max Loss: (Strike - Premium) × 100
Max Profit: Premium × 100
Breakeven: Strike - Premium

Example:
- Sell 1x SPY $443 put @ $0.30
- Max Profit: $30
- Max Loss: $44,270 (if SPY → $0)
- Breakeven: $442.70
- Cash Required: $44,300
```

### When to Use
- Want to buy stock at lower price
- Bullish on underlying
- Have cash ready
- Don't mind owning stock

---

## Screener Adaptations

### Current Screener (Covered Calls)
```bash
make -f makefiles/Makefile.zero-dte screen
# Assumes you own 100 shares per contract
```

### For Credit Spreads (Coming Soon)
```bash
make -f makefiles/Makefile.zero-dte screen-spreads \
  SPREAD_WIDTH=2 \
  MIN_CREDIT=0.10
```

### For Cash-Secured Puts
```bash
make -f makefiles/Makefile.zero-dte screen-puts \
  MAX_STRIKE=443 \
  MIN_PREMIUM=0.20
```

---

## Risk Management Rules

### For All 0-DTE Strategies

1. **Size Appropriately**
   - Never risk >1% of portfolio per trade
   - Start with 1 contract
   - Scale up slowly

2. **Use Stop Losses**
   - Close at 2x premium loss
   - Don't let winners become losers
   - Take profits at 50-70% of max

3. **Monitor Actively**
   - 0-DTE requires active management
   - Check every 15-30 minutes
   - Be ready to exit

4. **Know Assignment Risk**
   - Calls: assigned if ITM at expiration
   - Puts: assigned if ITM at expiration
   - Can happen early (rare but possible)

5. **Have an Exit Plan**
   - Before entry: know your exit
   - Time-based: close by 3:30 PM
   - Profit-based: close at 50-70%
   - Loss-based: close at 2x credit

---

## Recommended Approach for Most Traders

### Beginner/Intermediate
1. **Start with covered calls** if you own stock
2. **Or use credit spreads** for defined risk
3. Paper trade for 2-4 weeks first
4. Start with 1 contract
5. Use SPY/QQQ (most liquid)

### Advanced
1. Credit spreads (2-5 point wide)
2. Iron condors (defined risk both sides)
3. Multiple contracts across strikes
4. Active management throughout day

### Professional
1. Portfolio margining
2. Sophisticated hedging
3. High-frequency adjustments
4. Potentially naked options (if approved)

---

## Capital Requirements

### Covered Call
- **Capital**: 100 shares × price
- SPY: ~$44,000
- QQQ: ~$37,000
- IWM: ~$19,000

### Credit Spread
- **Capital**: (Width - Credit) × 100
- 2-point spread: $150-185
- 5-point spread: $450-475

### Naked Call
- **Capital**: 20-50% of notional
- SPY: $8,900 - $22,250
- **NOT RECOMMENDED**

---

## Bottom Line

### ✅ SAFE OPTIONS
1. **Covered Call** - If you own the stock
2. **Credit Spread** - Best risk/reward for most traders
3. **Cash-Secured Put** - If you want to own stock

### ⚠️ DANGEROUS OPTIONS
1. **Naked Call** - Unlimited risk, tiny premium
2. **Naked Put** - Can blow up account

### 🎯 RECOMMENDATION

**For 0-DTE income generation without owning stock:**

Use **CREDIT SPREADS** (2-3 point wide)
- Defined risk
- Better capital efficiency
- More accessible
- Can't get blown out
- Still profitable

---

## Questions to Ask Yourself

Before trading 0-DTE options, answer these:

1. ❓ Do I understand the risks?
2. ❓ Can I monitor positions during market hours?
3. ❓ Do I have appropriate capital?
4. ❓ Am I using defined-risk strategies?
5. ❓ Have I paper traded this?
6. ❓ Do I have a written trading plan?
7. ❓ Can I afford to lose this money?

If ANY answer is "no," reconsider trading 0-DTE options.

---

## Additional Resources

- [Options Strategies Guide](./OPTIONS_STRATEGIES_GUIDE.md)
- [0-DTE Screener Guide](./ZERO_DTE_SCREENER_GUIDE.md)
- [Risk Management Guide](./RISK_MANAGEMENT_GUIDE.md)

## Disclaimer

This is educational information only, not financial advice. Options involve significant risk and are not suitable for all investors. Consult a financial advisor before trading. Paper trade before using real capital.

---

**Last Updated:** October 21, 2025  
**Author:** Orion (Trading System AI)

