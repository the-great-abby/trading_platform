# Live Trading Monitor Guide
**Updated:** October 14, 2025

## Quick Start

```bash
# Run single status check
python scripts/live_trading_monitor_api.py

# Run continuous monitoring (every 5 minutes)
# Answer 'y' when prompted
python scripts/live_trading_monitor_api.py
```

---

## What You'll See

### Portfolio Overview
```
💰 Account Balance (Equity): $25,319.72
💵 Cash Balance: $15,319.72
💼 Position Cost Basis: $9,674.22
📈 Position Market Value: $10,655.70
💵 Buying Power: $15,319.72
📊 Total P&L: $981.48 (3.87%)
```

### Active Positions
```
💼 Current Positions (2):
  QQQ: 4 shares @ $604.52 (Current: $615.01, P&L: $42.00)
    🎯 Exit Strategy:
       • Max Hold: 30 days
       • Profit Target: 15.0%
       • Stop Loss: 8.0%
```

### Recent Trades with Status

#### Stock Trades:
```
✅ 13:43:27 MDT | 📈 QQQ | MULTI_STRATEGY_ENSEMBLE | 4 @ $604.52 | Status: FILLED
⏳ 14:15:30 MDT | 📈 AAPL | GREEKS_ENHANCED | 10 @ $247.50 | Status: PENDING
🚫 14:45:05 MDT | 📈 NVDA | MULTI_STRATEGY_ENSEMBLE | 1 @ $892.70 | FAILED: No match found
```

#### Options Trades (when available):
```
✅ 10:30:15 MDT | 📊 AAPL $250 CALL 11/15/25 | GREEKS_ENHANCED | 5 @ $3.50 | Status: FILLED
⏳ 11:45:22 MDT | 📊 TSLA $900 PUT 12/20/25 | GREEKS_ENHANCED | 3 @ $12.35 | Status: PENDING
🚫 14:20:10 MDT | 📊 NVDA $200 CALL 11/30/25 | GREEKS_ENHANCED | 2 @ $8.25 | FAILED: Insufficient buying power
```

---

## Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| ✅ | FILLED | Successfully executed on Public.com |
| ⏳ | PENDING/SUBMITTED | Waiting for exchange confirmation |
| 🚫 | FAILED | Rejected by Public.com (reason shown) |
| ❌ | CANCELLED | Cancelled by user or system |

## Asset Type Indicators

| Icon | Type | Example |
|------|------|---------|
| 📈 | Stock | `NVDA` |
| 📊 | Option | `NVDA $200 CALL 11/15/25` |

---

## Timestamp Format

All timestamps are displayed in **Mountain Time (MST/MDT)**:
- **MDT** = Mountain Daylight Time (spring/summer)
- **MST** = Mountain Standard Time (fall/winter)

Examples:
- `13:43:27 MDT` = 1:43 PM Mountain Daylight Time
- `09:15:30 MST` = 9:15 AM Mountain Standard Time

Database stores in UTC, automatically converted for display.

---

## Understanding Trade Failures

### Common Rejection Reasons:

1. **"No match found for this Symbol"**
   - Symbol not recognized by Public.com
   - Often means options order missing strike/expiration
   - **Fixed:** Now properly formats stock orders

2. **"Insufficient buying power"**
   - Account doesn't have enough cash
   - Check buying power in portfolio overview

3. **"Market is closed"**
   - Trading outside market hours (9:30 AM - 4:00 PM ET)
   - System should prevent this, but may still occur

4. **"Account not approved for options trading"**
   - Account doesn't have options approval
   - Contact Public.com to enable options

---

## Options Order Format

### Valid Options Order (Future):
```python
{
    "symbol": "AAPL",
    "option_type": "CALL",       # Required
    "strike_price": 250.0,       # Required
    "expiration_date": "2025-11-15",  # Required
    "quantity": 5,
    "premium": 3.50
}
```

Display: `📊 AAPL $250 CALL 11/15/25 | 5 @ $3.50`

### Valid Stock Order:
```python
{
    "symbol": "AAPL",
    "option_type": None,         # Must be None
    "strike_price": None,        # Not applicable
    "expiration_date": None,     # Not applicable
    "quantity": 10,
    "price": 247.50
}
```

Display: `📈 AAPL | 10 @ $247.50`

### ❌ Invalid (What Was Happening):
```python
{
    "symbol": "NVDA",
    "option_type": "CALL",       # Set to CALL
    "strike_price": None,        # But missing strike!
    "expiration_date": None      # And missing expiration!
}
```

This creates a hybrid order that Public.com rejects.

---

## Testing

### Run Unit Tests:
```bash
python tests/services/live_trading/test_options_order_validation.py
```

### Expected Output:
```
✅ ALL TESTS COMPLETED
❌ PROBLEM DETECTED: (for bug detection test)
   Has option_type: True (CALL)
   Has strike_price: False (None)
   This is the bug! Order has option_type but no strike/expiration
```

---

## Troubleshooting

### Monitor Shows Old Trades
**Solution:** Check if live-trading-service is running
```bash
kubectl get pods -n default | grep live-trading
```

### Prices Not Updating
**Solution:** Restart market-data-service
```bash
kubectl rollout restart deployment/market-data-service -n trading-system
```

### Port-Forward Issues
**Solution:** Restart port-forwards
```bash
# Live trading service
pkill -f "port-forward.*11120"
kubectl port-forward -n default svc/live-trading-service 11120:8080 &

# Market data service  
pkill -f "port-forward.*11084"
kubectl port-forward -n trading-system svc/market-data-service 11084:11084 &
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Live Trading Monitor                        │
│                 (Mountain Time Display)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Live Trading Service API (Port 11120)              │
│  • Fetches orders from database (UTC timestamps)            │
│  • Returns option fields (type, strike, expiration)         │
│  • Sorts by filled_at for FILLED orders                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (UTC)                       │
│  • live_trades table                                         │
│  • Stores: option_type, strike_price, expiration_date       │
│  • Stores: rejection_reason for failed orders               │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Files

- **Monitor Script:** `scripts/live_trading_monitor_api.py`
- **API Routes:** `services/live-trading-service/routes/trading.py`
- **Strategy Execution:** `services/live-trading-service/src/services/live_trading/strategy_execution_service.py`
- **Unit Tests:** `tests/services/live_trading/test_options_order_validation.py`
- **Summary:** `OPTIONS_ORDER_FIX_SUMMARY.md`




