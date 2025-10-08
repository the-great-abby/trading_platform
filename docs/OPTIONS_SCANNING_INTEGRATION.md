# Options Scanning Integration

## Overview

Your live trading system now includes **automated options scanning** using the existing `AutomatedOptionsScanner` from the strategy service, with **budget-friendly filtering** based on your available buying power.

## How It Works

### 1. Existing Scanner (Strategy Service)
The `AutomatedOptionsScanner` in the strategy service provides:
- ✅ IV Percentile Analysis (high IV = sell premium, low IV = buy premium)
- ✅ Earnings Event Scanning (pre/post earnings opportunities)
- ✅ Volatility Regime Detection (expanding/contracting)
- ✅ Greeks-Based Opportunities (high theta, vega opportunities)
- ✅ Technical Breakout Analysis (momentum + volatility)
- ✅ Calendar/Diagonal Spread identification

### 2. Budget-Friendly Filtering
The `AdaptiveSectorWaveStrategy` provides position sizing:
- Iron Condor: ~$100 (cheapest)
- Calendar Spread: ~$150
- Butterfly Spread: ~$200
- Strangle: ~$400
- Straddle: ~$500

**Filtering Logic:**
```python
available_cash = buying_power  # From your account
max_position_value = available_cash * 0.20  # 20% per position
# Only returns strategies you can afford
```

### 3. Integration Flow

```
┌─────────────────────────────────────────────────────┐
│  Options Scanning CronJob                           │
│  Runs: 10 AM & 2 PM ET daily                        │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│  Live Trading Service                                │
│  /api/v1/options/scan/{account_id}                  │
│  • Gets your buying power from database              │
│  • Calls strategy service with budget               │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│  Strategy Service                                    │
│  /api/options/scan                                   │
│  • Runs AutomatedOptionsScanner                      │
│  • Filters by available_cash                         │
│  • Returns only affordable opportunities             │
└─────────────────────────────────────────────────────┘
```

## Schedule

**Options Scanning:** Twice daily
- 10:00 AM ET (market open + 30min)
- 2:00 PM ET (afternoon check)

**Why not hourly?**
- Options opportunities are longer-term (days/weeks)
- IV and volatility don't change minute-by-minute
- Reduces API usage and costs
- Focuses on quality over quantity

## Data Sources

### Primary: Polygon.io
- ✅ Options chain data
- ✅ Implied volatility (IV)
- ✅ Greeks (delta, theta, vega, gamma)
- ✅ Open interest & volume
- ✅ Historical volatility

### Secondary: Public.com
- ✅ Account balance
- ✅ Buying power
- ✅ Current positions
- ✅ Risk profile

## What Gets Scanned

### Symbols (Default)
```python
symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
    'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
    'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'SLV'
]
```

### Opportunity Types
1. **IV Mean Reversion** - High IV returning to normal
2. **IV Expansion** - Low IV starting to rise
3. **Earnings Plays** - Pre/post earnings volatility
4. **Volatility Regime** - Trending volatility patterns
5. **Greeks Opportunities** - High theta/vega setups
6. **Technical Breakouts** - Price + volatility alignment
7. **Calendar Spreads** - Time decay advantages
8. **Diagonal Spreads** - Directional + time decay

### Filtering Criteria
- ✅ Minimum confidence: 60%
- ✅ Minimum volume: 10 contracts/day
- ✅ Minimum open interest: 50 contracts
- ✅ Risk/reward ratio: >0.3
- ✅ Budget: Must be affordable with your cash

## Management Commands

### Deploy Options Scanning
```bash
make -f Makefile.options-scan deploy-options-scan
```

### Manual Scan (Test Now)
```bash
make -f Makefile.options-scan manual-scan
```

### Check Status
```bash
make -f Makefile.options-scan status-options-scan
```

### View Logs
```bash
make -f Makefile.options-scan logs-options-scan
```

### Suspend/Resume
```bash
make -f Makefile.options-scan suspend-options-scan
make -f Makefile.options-scan resume-options-scan
```

## Example Output

```json
{
  "success": true,
  "account_id": "19c25392-8b61-4b71-a344-0eb04d275528",
  "available_cash": 33.17,
  "opportunities_found": 3,
  "total_scanned": 15,
  "filtered_by_budget": 12,
  "max_position_value": 6.63,
  "opportunities": [
    {
      "symbol": "AAPL",
      "opportunity_type": "iv_mean_reversion",
      "confidence": 0.75,
      "estimated_cost": 100,
      "suggested_strategy": "iron_condor",
      "entry_price": 175.50,
      "target_price": 180.00,
      "stop_loss": 172.00,
      "affordable": true,
      "metadata": {
        "iv_percentile": 0.78,
        "historical_volatility": 0.32,
        "earnings_date": "2025-11-01"
      }
    }
  ]
}
```

## Important Notes

### With $33.17 Buying Power
- ❌ **Most options will be too expensive**
- ✅ Max position size: $6.63 (20% of $33.17)
- ✅ Even cheapest strategy (Iron Condor ~$100) exceeds budget
- 💡 **Scanner will still run** but may return no affordable opportunities

### To Make Options Trading Viable
You would need:
1. **More capital**: ~$500+ for cheapest strategies
2. **Or fractional options** (not available)
3. **Or paper trade first** to test strategies

### Current Status
- ✅ Scanner integrated and ready
- ✅ Budget filtering active
- ⚠️  May not find affordable opportunities with current balance
- ✅ System will log why opportunities are filtered

## Next Steps

1. **Deploy the scanner:**
   ```bash
   make -f Makefile.options-scan deploy-options-scan
   ```

2. **Test manually:**
   ```bash
   make -f Makefile.options-scan manual-scan
   ```

3. **Monitor results:**
   ```bash
   make -f Makefile.options-scan logs-options-scan
   ```

4. **If no opportunities:**
   - Increase available cash, OR
   - Use for monitoring/learning, OR
   - Wait for extremely cheap opportunities

The scanner is ready and will work perfectly once you have sufficient capital for options trading!
