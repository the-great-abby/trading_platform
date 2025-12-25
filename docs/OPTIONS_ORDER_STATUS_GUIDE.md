# Options Order Status Monitoring Guide

## Overview

New tools to monitor options orders across their lifecycle: submitted → filled → positions.

---

## Quick Commands

### Check Options Order Status

```bash
# Complete options order status
make -f makefiles/Makefile.live-trading live-trading-options-status
```

**Output**:
```
📊 Options Orders Status
============================================================

📈 SUBMITTED Orders (Pending Execution):
  🕒 DIS CALL - Strike: $95 - Qty: 1 - 2025-10-21
  🕒 QCOM CALL - Strike: $180 - Qty: 1 - 2025-10-21
  🕒 CSCO CALL - Strike: $60 - Qty: 1 - 2025-10-21

✅ FILLED Orders (Executed):
  None

❌ REJECTED Orders (Failed):
  None

📊 Summary:
  Total Submitted: 3
  Total Filled: 0
  Total Rejected: 0
```

---

## Enhanced Live Trading Monitor

The live trading monitor now shows:
1. ✅ **Stock Positions** (existing)
2. ✅ **Options Positions** (when filled)
3. ✅ **Pending Options Orders** (submitted but not filled)
4. ✅ **Rejected Options Orders** (failed with reasons)

### Run Monitor

```bash
# Standard monitor with options status
make -f makefiles/Makefile.live-trading live-trading-monitor
```

**Enhanced Output**:
```
📊 Live Trading Status - 2025-10-21 18:09:32
============================================================
💰 Account Balance (Equity): $4,027.67
💵 Cash Balance: $1,319.72
💼 Position Cost Basis: $2,674.22
📈 Position Market Value: $2,708.29

💼 Current Positions (2):

  📈 STOCK POSITIONS:
  QQQ: 4 shares @ $604.52 (Current: $611.38, P&L: $27.44)
    🎯 Exit Strategy:
       • Max Hold: 30 days
       • Profit Target: 15.0%
       • Stop Loss: 8.0%
       • Min Holding: 4 hours
  
  AAPL: 1 shares @ $256.14 (Current: $262.77, P&L: $6.63)
    🎯 Exit Strategy:
       • Max Hold: 30 days
       • Profit Target: 15.0%
       • Stop Loss: 8.0%
       • Min Holding: 4 hours

🕒 PENDING OPTIONS ORDERS (9):
   🕒 DIS CALL Strike $95 x1 - Submitted 2025-10-21
      Status: Awaiting market open / execution
   🕒 QCOM CALL Strike $180 x1 - Submitted 2025-10-21
      Status: Awaiting market open / execution
   🕒 CSCO CALL Strike $60 x1 - Submitted 2025-10-21
      Status: Awaiting market open / execution
   ... (6 more)

❌ REJECTED OPTIONS ORDERS (0):
   None
```

---

## Order Status Lifecycle

### 1. SUBMITTED → Pending Execution

**Status**: `SUBMITTED`
**Meaning**: Order sent to broker, awaiting execution
**What to do**: Wait for market open or order to fill

**Display**:
```
🕒 PENDING: SPY CALL $580 x2 - Awaiting execution
```

---

### 2. FILLED → Position Created

**Status**: `FILLED`
**Meaning**: Order executed, position created
**What to do**: Monitor position P&L

**Display**:
```
📊 POSITION: SPY CREDIT SPREAD
  SELL 2 CALL $583 @ $1.50
  BUY 2 CALL $588 @ $0.30
  Credit: $1.20, P&L: +$0.60
```

---

### 3. REJECTED → Failed

**Status**: `REJECTED`, `CANCELLED`, `FAILED`
**Meaning**: Order failed to execute
**What to do**: Review reason and adjust strategy

**Display**:
```
❌ REJECTED: SPY CALL $580 - REJECTED: Insufficient buying power
```

**Common Rejection Reasons**:
- `Insufficient buying power`
- `Invalid option contract`
- `Market closed`
- `Position limit exceeded`
- `Contract not available`
- `Price out of range`

---

## Monitoring Workflow

### Morning (Before Market Open)

**Check pending orders**:
```bash
make -f makefiles/Makefile.live-trading live-trading-options-status
```

**Expected**:
- Orders submitted previous day/evening
- Status: SUBMITTED
- Will fill when market opens (9:30 AM ET)

---

### During Market Hours (9:30 AM - 4:00 PM ET)

**Monitor fills**:
```bash
# Every 5 minutes
watch -n 300 'make -f makefiles/Makefile.live-trading live-trading-monitor'
```

**Watch for**:
- SUBMITTED → FILLED transitions
- Positions appearing in portfolio
- Any rejections

---

### After Market Close

**Review day's activity**:
```bash
make -f makefiles/Makefile.live-trading live-trading-options-status
```

**Check**:
- All filled orders
- Any rejected orders
- Positions still open

---

## Troubleshooting

### Issue: Orders Stuck in SUBMITTED

**Possible Causes**:
1. Market closed (options only trade 9:30 AM - 4:00 PM ET)
2. Low liquidity (no buyers/sellers at your price)
3. Invalid contract (expired, delisted)
4. Broker processing delay

**Solutions**:
```bash
# Check order details
curl -s "http://localhost:11120/api/v1/trading/orders?account_id=19c25392-8b61-4b71-a344-0eb04d275528" | \
  jq '.orders[] | select(.status == "SUBMITTED") | {symbol, created_at, option_type, strike_price}'

# If stuck > 1 hour during market hours, may need to cancel
```

---

### Issue: Orders REJECTED

**Check rejection reason**:
```bash
make -f makefiles/Makefile.live-trading live-trading-options-status
```

**Common Fixes**:

1. **Insufficient Buying Power**:
   - Check available cash
   - Reduce position size
   - Close other positions

2. **Invalid Contract**:
   - Verify contract exists
   - Check expiration date
   - Confirm strike price valid

3. **Price Out of Range**:
   - Use limit orders instead of market
   - Adjust limit price closer to market

4. **Position Limit Exceeded**:
   - Check max contracts per trade (currently 2)
   - Close existing positions first

---

### Issue: Filled Orders But No Positions

**Possible Causes**:
1. Position sync delay from broker
2. Position already closed (same-day exit)
3. Database sync issue

**Solutions**:
```bash
# Trigger sync
curl -X POST "http://localhost:11120/api/v1/accounts/sync"

# Check positions
make -f makefiles/Makefile.live-trading live-trading-positions

# Check if closed
curl -s "http://localhost:11120/api/v1/trading/positions?account_id=19c25392-8b61-4b71-a344-0eb04d275528&status_filter=CLOSED" | \
  jq '.positions[] | select(.legs_data != null)'
```

---

## API Endpoints

### Get Options Orders

```bash
# All options orders
curl "http://localhost:11120/api/v1/trading/orders?account_id=19c25392-8b61-4b71-a344-0eb04d275528&limit=100" | \
  jq '.orders[] | select(.option_type != null)'

# Just pending
curl "http://localhost:11120/api/v1/trading/orders?account_id=19c25392-8b61-4b71-a344-0eb04d275528" | \
  jq '.orders[] | select(.option_type != null and .status == "SUBMITTED")'

# Just rejected
curl "http://localhost:11120/api/v1/trading/orders?account_id=19c25392-8b61-4b71-a344-0eb04d275528" | \
  jq '.orders[] | select(.option_type != null and .status == "REJECTED")'
```

---

### Get Options Positions

```bash
# All positions with legs (options)
curl "http://localhost:11120/api/v1/trading/positions?account_id=19c25392-8b61-4b71-a344-0eb04d275528" | \
  jq '.positions[] | select(.legs_data != null)'
```

---

## Integration with Multi-Strategy Ensemble

The 0-DTE strategy (15% weight) will:
1. **Screen** for credit spreads during market hours (9:45 AM - 3:45 PM ET)
2. **Submit** orders when candidates found
3. **Monitor** via this status system
4. **Track** fills and create positions
5. **Exit** based on P&L or time limits

---

## Example Scenarios

### Scenario 1: Normal Execution

**9:00 AM**: Strategy runs, finds SPY credit spread
```
🕒 SUBMITTED: SPY CALL $583/$588 x2 - Awaiting execution
```

**9:31 AM**: Market opens, order fills
```
✅ FILLED: SPY CALL $583/$588 x2 @ $1.20 credit
```

**9:32 AM**: Position appears
```
📊 SPY CREDIT SPREAD: Credit $1.20, Max Risk $3.80
```

**3:50 PM**: Position closes at profit
```
✅ CLOSED: SPY spread - P&L: +$0.80 (+66%)
```

---

### Scenario 2: Rejection

**10:00 AM**: Strategy submits order
```
🕒 SUBMITTED: QQQ CALL $500/$505 x3
```

**10:01 AM**: Order rejected
```
❌ REJECTED: QQQ CALL $500/$505 - Insufficient buying power
```

**Action**: System reduces size, resubmits
```
🕒 SUBMITTED: QQQ CALL $500/$505 x2 (reduced size)
```

**10:02 AM**: New order fills
```
✅ FILLED: QQQ CALL $500/$505 x2
```

---

### Scenario 3: After Hours Submission

**11:45 PM**: Strategy runs (testing/dev mode)
```
🕒 SUBMITTED: DIS CALL $95 x1
🕒 SUBMITTED: QCOM CALL $180 x1
🕒 SUBMITTED: CSCO CALL $60 x1
```

**Status**: All remain SUBMITTED until market opens

**Next Day 9:31 AM**: Orders fill or expire
```
✅ FILLED: DIS CALL $95 x1
✅ FILLED: QCOM CALL $180 x1
❌ REJECTED: CSCO CALL $60 - Contract expired
```

---

## Summary

**New Capabilities**:
- ✅ Monitor pending options orders
- ✅ Track order status (submitted/filled/rejected)
- ✅ See rejection reasons
- ✅ Separate stock vs options positions
- ✅ Integrated into live trading monitor

**Commands**:
- `make -f makefiles/Makefile.live-trading live-trading-options-status` - Options status
- `make -f makefiles/Makefile.live-trading live-trading-monitor` - Full monitor (enhanced)

**Monitor shows**:
1. Stock positions
2. Options positions (when filled)
3. Pending orders (awaiting fill)
4. Rejected orders (with reasons)









