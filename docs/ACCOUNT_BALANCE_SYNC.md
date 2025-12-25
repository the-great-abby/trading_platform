# Account Balance Synchronization

## Overview

The system maintains synchronized account balances even when orders take time to fill (20 minutes to several days). Since Public.com doesn't expose direct balance/position APIs, we use an **order-based reconciliation approach**.

## How It Works

### 1. Order Status Monitoring
- **Order Sync Worker** runs every 2 minutes
- Fetches all `PENDING` orders from database
- Queries Public.com API for current status
- Updates database when status changes

### 2. Automatic Balance Recalculation
When orders transition to `FILLED`:
- System automatically triggers balance recalculation
- Calculates positions from all filled trades
- Updates `equity` in `live_trading_accounts` table
- Maintains estimated cash flow

### 3. Balance Calculation Method
```
For each FILLED trade:
  BUY:  cash_flow -= (quantity × price)
        Add to position or create new position
        
  SELL: cash_flow += (quantity × price)
        Reduce position or close if quantity = 0

Equity = Sum of all open position values
```

## Components

### Order Sync Service
**File**: `services/live-trading-service/src/services/live_trading/order_sync_service.py`

**Methods**:
- `sync_pending_orders()` - Fetches and updates order statuses
- `recalculate_account_balance()` - Recalculates balance from filled trades

### API Endpoints
**Base URL**: `http://live-trading-service:8080/api/v1`

- `POST /orders/sync/{account_id}` - Sync orders and recalculate balance
- `GET /account/balance/{account_id}` - Get current balance from database

### CronJobs

#### Order Sync Worker
- **Schedule**: Every 2 minutes during market hours
- **Purpose**: Monitor order status changes
- **Auto-triggers**: Balance recalculation on fills

#### Account Sync Worker (Optional)
- **Schedule**: Every 5 minutes
- **Purpose**: Additional balance validation
- **Note**: Currently experimental (Public.com lacks balance API)

## Management Commands

### Check Current Balance
```bash
make -f makefiles/Makefile.account-sync check-balance
```

### Manual Sync
```bash
make -f makefiles/Makefile.order-sync manual-sync
```

### View Sync Status
```bash
make -f makefiles/Makefile.order-sync status-sync-worker
```

## Balance Accuracy

### What's Accurate
✅ Order status (PENDING, FILLED, REJECTED)  
✅ Filled quantities and prices  
✅ Position tracking (symbols, quantities)  
✅ Cash flow from trades  

### What's Estimated
⚠️  Real-time position values (uses last fill price)  
⚠️  Cash balance (requires manual initial balance setup)  
⚠️  Buying power (not provided by Public.com API)  

## Initial Setup

To set accurate cash balance, manually update once:

```sql
UPDATE live_trading_accounts
SET cash_balance = <your_actual_balance>,
    equity = <sum_of_position_values>,
    buying_power = <your_buying_power>
WHERE account_id = '19c25392-8b61-4b71-a344-0eb04d275528';
```

After this, the system will track changes from filled orders.

## Monitoring

### View Balance
```python
python3 live_trading_monitor.py
```

Shows:
- Current cash balance
- Equity (position values)
- Portfolio value
- Open positions

### Discord Notifications
System sends alerts when:
- Orders fill
- Exit orders execute
- Balance updates occur

## Troubleshooting

### Balance Seems Wrong
1. Check order sync worker status
2. Verify all orders are properly linked (no TEMP_ IDs)
3. Run manual sync
4. Check for failed order syncs in logs

### Orders Not Updating
1. Verify order sync worker is running
2. Check API token hasn't expired
3. Review worker logs for errors
4. Ensure orders have real Public.com IDs

### Sync Logs
```bash
make -f makefiles/Makefile.order-sync logs-sync-worker
```

## Best Practices

1. **Let the system sync automatically** - Workers handle most cases
2. **Check balance after large fills** - Verify accuracy manually
3. **Monitor Discord notifications** - Stay informed of fills
4. **Review worker logs periodically** - Catch issues early

## Limitations

- Public.com doesn't expose balance API
- Real-time prices not available from API
- Initial balance must be set manually
- Balance is calculated, not fetched

Despite these limitations, the order-based approach provides reliable tracking for automated trading.
