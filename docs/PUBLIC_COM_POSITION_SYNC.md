# Public.com Position Sync - Complete Guide

## Overview

The live trading system now syncs positions directly from Public.com's portfolio API, including both stock and options positions.

---

## How It Works

### 1. Public.com Portfolio API

**Endpoint**: `GET /trading/{accountId}/portfolio/v2`

**Returns**:
```json
{
  "accountId": "...",
  "buyingPower": {...},
  "equity": [...],
  "positions": [
    {
      "instrument": {
        "symbol": "QQQ",
        "name": "Invesco QQQ Trust",
        "type": "EQUITY"
      },
      "quantity": "4",
      "currentValue": "2445.52",
      ...
    },
    {
      "instrument": {
        "symbol": "SPY251021C00580000",
        "name": "SPY Oct 21 2025 $580 Call",
        "type": "OPTION"
      },
      "quantity": "2",
      ...
    }
  ],
  "orders": [...]
}
```

Reference: [Public.com Portfolio API](https://public.com/api/docs/resources/account-details/get-account-portfolio-v2)

---

### 2. Position Parser

**File**: `services/live-trading-service/src/services/live_trading/position_parser.py`

Parses positions from Public.com format to database format:

**Stock Position**:
```python
{
  "symbol": "QQQ",
  "instrument_type": "EQUITY",
  "quantity": 4,
  "average_price": 604.52,
  "current_price": 611.38,
  "unrealized_pnl": 27.44
}
```

**Options Position**:
```python
{
  "symbol": "SPY251021C00580000",
  "instrument_type": "OPTION",
  "underlying_symbol": "SPY",
  "option_type": "CALL",
  "strike_price": 580.0,
  "expiration_date": "2025-10-21",
  "quantity": 2,
  "average_price": 1.20,
  "legs_data": [{...}]
}
```

---

### 3. Database Sync

**File**: `services/live-trading-service/src/services/live_trading/account_sync_service.py`

**Process**:
1. Fetch portfolio from Public.com
2. Parse all positions (stocks + options)
3. Mark existing DB positions as CLOSED
4. Insert/update new positions from Public.com
5. Store options with `legs_data` populated

---

### 4. API Endpoint

**Endpoint**: `POST /api/v1/sync/{account_id}/positions`

**Triggers**:
- Manual sync via API call
- Automatic sync (can be scheduled)
- On-demand from monitor script

---

## Usage

### Manual Sync

```bash
# Trigger position sync
bash scripts/sync_positions_from_public.sh

# Or via make
make sync-positions

# Or via API
curl -X POST "http://localhost:11120/api/v1/sync/19c25392-8b61-4b71-a344-0eb04d275528/positions"
```

---

### Automatic Sync

**Add to Kubernetes Cronjob** (every 5 minutes):

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: position-sync
  namespace: trading-system
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: sync
            image: localhost:32000/live-trading-service:latest
            command:
            - python
            - -c
            - |
              import asyncio
              from src.services.live_trading.account_sync_service import AccountSyncService
              
              async def sync():
                  # ... sync logic ...
                  pass
              
              asyncio.run(sync())
```

---

### View Synced Positions

```bash
# Show all positions
make show-positions

# Show only options
make show-options-positions

# Via monitor
make -f makefiles/Makefile.live-trading live-trading-monitor
```

---

## Options Position Display

### Before Sync
```
💼 Current Positions (2):
  QQQ: 4 shares @ $604.52 (Current: $611.38, P&L: $27.44)
  AAPL: 1 shares @ $256.14 (Current: $262.77, P&L: $6.63)
```

### After Sync (with options)
```
💼 Current Positions (12):

  📈 STOCK POSITIONS (2):
  QQQ: 4 shares @ $604.52 (Current: $611.38, P&L: $27.44)
  AAPL: 1 shares @ $256.14 (Current: $262.77, P&L: $6.63)

  📊 OPTIONS POSITIONS (10):
  SPY251021C00580000:
    CALL $580 exp 2025-10-21 x2 @ $1.20
    P&L: +$0.60 (+50.0%)
  
  QQQ251021C00505000:
    CALL $505 exp 2025-10-21 x1 @ $0.95
    P&L: +$0.45 (+47.4%)
  
  ... (8 more options positions)

🕒 PENDING OPTIONS ORDERS (81):
  DIS CALL $125 x1 - Submitted 2025-10-21
  QCOM CALL $185 x1 - Submitted 2025-10-22
  ... (79 more pending)
```

---

## Troubleshooting

### Issue: No options positions showing after sync

**Check**:
1. Verify Public.com has options positions:
   ```bash
   curl -X POST "http://localhost:11120/api/v1/sync/19c25392-8b61-4b71-a344-0eb04d275528/positions" | jq '.options_positions'
   ```

2. Check sync logs:
   ```bash
   kubectl logs -n trading-system deployment/live-trading-service --tail=100 | grep -i "option"
   ```

3. Verify parser is working:
   ```bash
   kubectl logs -n trading-system deployment/live-trading-service --tail=100 | grep -i "parsed"
   ```

---

### Issue: Sync fails with authentication error

**Solution**:
```bash
# Re-authenticate with Public.com
# (This would require logging in again via the web UI)
```

---

### Issue: Options shown incorrectly

**Check option symbol format**:
- Public.com format: `SPY251021C00580000`
- Decoded: SPY Oct 21, 2025 $580 Call

**Parser handles**:
- Underlying ticker extraction
- Date parsing (YYMMDD)
- Call/Put identification
- Strike price (divide by 1000)

---

## API Endpoints

### Sync Positions
```bash
POST /api/v1/sync/{account_id}/positions
```

**Response**:
```json
{
  "success": true,
  "positions_synced": 12,
  "stock_positions": 2,
  "options_positions": 10,
  "positions_inserted": 12,
  "synced_at": "2025-10-21T18:52:00"
}
```

### Get Positions
```bash
GET /api/v1/trading/positions?account_id={account_id}&status_filter=OPEN
```

**Response includes**:
- Stock positions (legs_data = null)
- Options positions (legs_data = JSON array)

---

## Files Created/Modified

### New Files:
- ✅ `services/live-trading-service/src/services/live_trading/position_parser.py`
- ✅ `services/live-trading-service/routes/sync.py`
- ✅ `scripts/sync_positions_from_public.sh`
- ✅ `makefiles/Makefile.live-trading-sync`

### Modified Files:
- ✅ `services/live-trading-service/src/services/live_trading/public_api_client.py`
- ✅ `services/live-trading-service/src/services/live_trading/account_sync_service.py`
- ✅ `services/live-trading-service/main.py`
- ✅ `scripts/monitoring/live_trading_monitor.py`

---

## Summary

✅ **Position sync now works for both stocks and options**
✅ **Public.com portfolio/v2 API integrated**
✅ **Options positions parsed and stored with legs_data**
✅ **Monitor displays both position types**
✅ **Sync can be triggered manually or automated**

**Your live trading monitor now shows complete portfolio from Public.com!** 🎉









