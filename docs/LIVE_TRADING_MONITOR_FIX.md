# Live Trading Monitor Fix - 2025-10-07

## Summary
Fixed the live trading monitor to accurately calculate portfolio value using real-time market prices and current positions.

## Problems Fixed

### 1. **Incorrect Trade Count** ❌ → ✅
**Before**: Counted ALL orders (including pending/rejected) as trades
**After**: Only counts FILLED orders as trades

### 2. **Incorrect Portfolio Value** ❌ → ✅
**Before**: Used static $4,000 initial capital
**After**: Calculates real value = (positions × current_price) + cash

### 3. **No Position Display** ❌ → ✅
**Before**: Didn't show current positions
**After**: Shows all open positions with entry prices

### 4. **No Real-Time Pricing** ❌ → ✅
**Before**: Used fixed prices
**After**: Fetches current market prices from Polygon API

## Current Portfolio Status

```
💰 Initial Capital: $4,000.00
📈 Current Value: $4,028.27
📊 Total P&L: $28.27 (+0.71%)

💼 Current Positions (4):
  AAPL: 1 shares @ $256.14
  GOOGL: 1 shares @ $246.70
  MSFT: 2 shares @ $522.96
  QQQ: 4 shares @ $604.52

📈 Total Filled Trades: 6
📅 Today's Trades: 1
📊 Today's P&L: $2.75
```

## How It Works Now

### 1. **Fetch Real Data**
```python
orders = await self.fetch_orders_from_api()      # All orders
positions = await self.fetch_positions_from_api() # Current positions
```

### 2. **Filter FILLED Orders**
```python
if order.get('status') == 'FILLED':
    new_trades.append(order)
```

### 3. **Calculate Position Value**
```python
for position in positions:
    if position.get('status') == 'OPEN':
        current_price = await self._get_current_price(symbol)
        position_value = quantity * current_price
        total_value += position_value
```

### 4. **Calculate Total Portfolio**
```python
cash_remaining = initial_capital - total_position_cost
total_value = total_position_value + cash_remaining
total_pnl = total_value - initial_capital
```

## Usage

### Run Once
```bash
python3 scripts/live_trading_monitor_api.py
```

### Continuous Monitoring
```bash
# When prompted, enter:
# - y (yes for continuous monitoring)
# - 5 (update every 5 minutes)
```

## Prerequisites

1. **Port Forward Must Be Active**
```bash
kubectl port-forward -n trading-system deployment/paper-trading-k8s 11120:8080
```

2. **Polygon API Key** (for real-time prices)
- Automatically fetched from k8s secret `polygon-api-key`
- Or set `POLYGON_API_KEY` environment variable

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/trading/orders` | Fetch all orders |
| `GET /api/v1/trading/positions` | Fetch current positions |
| Polygon `/v2/aggs/ticker/{symbol}/prev` | Get current prices |

## Strategy Performance Tracking

The monitor now shows per-strategy performance:

```
📊 Strategy Performance:
  ELLIOTT_WAVE_CORRECTIVE:
    Trades: 1 | Win Rate: 100.0%
    P&L: $2.75

  SimpleStrategy:
    Trades: 3 | Win Rate: 100.0%
    P&L: $43.51

  BUTTERFLY_SPREAD:
    Trades: 2 | Win Rate: 100.0%
    P&L: $1.51
```

## Next Steps

1. ✅ Monitor is now accurate
2. 🔄 Port forward must be active for it to work
3. 📊 Real-time prices update on each refresh
4. 💰 Shows true portfolio value with market fluctuations

## Technical Changes

### Files Modified
- `scripts/live_trading_monitor_api.py`

### Key Changes
1. Added `_get_current_price()` method for Polygon API integration
2. Updated `update_from_api()` to fetch positions and calculate real value
3. Added position tracking with `self.last_positions`
4. Updated `print_status()` to display current positions
5. Filtered trades to only count FILLED orders

### Dependencies
- `aiohttp` - for async API calls
- `requests` - for Polygon API (in calculation script)
- `kubectl` - for fetching API key from k8s secrets

## Troubleshooting

### Monitor shows $0 trades
**Solution**: Port forward isn't running
```bash
kubectl port-forward -n trading-system deployment/paper-trading-k8s 11120:8080
```

### Prices show as $0.00
**Solution**: Polygon API key not accessible
```bash
kubectl get secret polygon-api-key -n trading-system
```

### "Cannot connect to host localhost:11120"
**Solution**: Live trading service not running
```bash
kubectl get pods -n trading-system | grep paper-trading
```

## Related Documentation
- [Trading Endpoints Guide](TRADING_ENDPOINTS_GUIDE.md)
- [Port Mapping](../PORT_MAP.md)
- [Deploy Map](../DEPLOY_MAP.md)

