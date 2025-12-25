# Rejected Trade Tracking System

## Overview

The rejected trade tracking system captures and displays trade attempts that were rejected by the system **before** they were submitted to the broker. This provides visibility into why trades aren't being executed and helps with strategy tuning.

## What Gets Tracked

The system now tracks trade rejections in these categories:

### 1. **BUYING_POWER** 💸
- Insufficient buying power to execute the trade
- Shows required amount vs. available amount

### 2. **RISK** ⚠️
- Risk validation failures
- Includes violations like:
  - Daily loss limits exceeded
  - Daily trade limits exceeded
  - Greeks exposure limits exceeded
  - Emergency stop active

### 3. **CONFIDENCE** 📉
- Signal confidence too low
- For BUY signals: Below minimum threshold (typically 50%)
- For SELL signals: Below exit threshold (typically 60%)

### 4. **POSITION_EXISTS** 🔄
- Already holding a position in the symbol
- System prevents adding to existing positions

### 5. **VALIDATION** ❌
- Order data validation failures
- Invalid parameters, missing data, etc.

## Database Schema

### Table: `rejected_trade_attempts`

```sql
CREATE TABLE rejected_trade_attempts (
    attempt_id UUID PRIMARY KEY,
    account_id UUID REFERENCES live_trading_accounts(account_id),
    symbol VARCHAR(50),
    strategy VARCHAR(100),
    action VARCHAR(20),
    quantity INTEGER,
    estimated_premium NUMERIC(15,2),
    rejection_reason TEXT,
    rejection_category VARCHAR(50),
    confidence_score NUMERIC(5,4),
    current_price NUMERIC(10,4),
    option_type VARCHAR(10),
    strike_price NUMERIC(10,4),
    expiration_date TIMESTAMP,
    rejection_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoint

### GET `/api/v1/trading/rejected-attempts`

**Parameters:**
- `account_id` (required): Trading account ID
- `limit` (optional): Maximum number of records to return (default: 100)

**Response:**
```json
{
  "success": true,
  "rejected_attempts": [
    {
      "attempt_id": "uuid",
      "symbol": "NVDA",
      "strategy": "MULTI_STRATEGY_ENSEMBLE",
      "action": "BUY",
      "rejection_reason": "Signal confidence too low: 0.45 (minimum 0.50 required)",
      "rejection_category": "CONFIDENCE",
      "confidence_score": 0.45,
      "current_price": 892.70,
      "created_at": "2025-10-15T14:45:05Z",
      "rejection_details": {
        "action_signal": "BUY",
        "recommendation_score": 0.68,
        "minimum_confidence": 0.50
      }
    }
  ],
  "total_count": 1
}
```

## Live Trading Monitor Display

The `live_trading_monitor_api.py` now shows rejected attempts in a dedicated section:

```
🚫 Recent Rejected Trade Attempts (5):
  📉 14:45:05 MDT | NVDA | MULTI_STRATEGY_ENSEMBLE | BUY (confidence: 0.45)
     Reason: Signal confidence too low: 0.45 (minimum 0.50 required)
  
  💸 14:30:04 MDT | AAPL | MULTI_STRATEGY_ENSEMBLE | BUY
     Reason: Insufficient buying power: $85.00 (minimum $100 required)
```

### Icons by Category:
- 💸 BUYING_POWER - Insufficient funds
- ⚠️ RISK - Risk validation failed
- 📉 CONFIDENCE - Signal confidence too low
- 🔄 POSITION_EXISTS - Already holding position
- ❌ VALIDATION - Order validation failed
- 🚫 OTHER - Other rejection reasons

## Setup Instructions

### 1. Run Database Migration

```bash
# Navigate to project root
cd /Users/abby/code/trading

# Activate virtual environment
source .venv/bin/activate

# Ensure database is port-forwarded (if using Kubernetes)
# Note: Database is in postgres-infra namespace, not trading-system
kubectl port-forward -n postgres-infra service/postgres-timescale-external 5432:5432 &

# Run migration
alembic upgrade head
```

### 2. Verify Table Creation

```sql
-- Check if table exists
SELECT COUNT(*) FROM rejected_trade_attempts;

-- View recent rejections
SELECT 
    symbol,
    action,
    rejection_category,
    rejection_reason,
    created_at
FROM rejected_trade_attempts
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Restart Live Trading Service

The live trading service needs to be restarted to pick up the new code:

```bash
# If running in Kubernetes
kubectl rollout restart deployment/live-trading-service -n trading-system

# If running locally
# Stop and restart the service
```

## Usage Examples

### View Rejected Attempts in Monitor

```bash
# Run the live trading monitor
python scripts/live_trading_monitor_api.py
```

The monitor will automatically fetch and display rejected attempts in a dedicated section.

### Query API Directly

```bash
# Get recent rejected attempts
curl "http://localhost:11120/api/v1/trading/rejected-attempts?account_id=19c25392-8b61-4b71-a344-0eb04d275528&limit=50"
```

### Analyze Rejection Patterns

```sql
-- Most common rejection categories
SELECT 
    rejection_category,
    COUNT(*) as rejection_count
FROM rejected_trade_attempts
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY rejection_category
ORDER BY rejection_count DESC;

-- Symbols with most rejections
SELECT 
    symbol,
    rejection_category,
    COUNT(*) as rejection_count
FROM rejected_trade_attempts
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY symbol, rejection_category
ORDER BY rejection_count DESC
LIMIT 10;

-- Confidence-related rejections
SELECT 
    symbol,
    action,
    confidence_score,
    rejection_reason,
    created_at
FROM rejected_trade_attempts
WHERE rejection_category = 'CONFIDENCE'
ORDER BY created_at DESC
LIMIT 20;
```

## Troubleshooting

### Migration Fails with Connection Error

Ensure the database is accessible:
```bash
# Check port forwarding
ps aux | grep "kubectl port-forward" | grep postgres-timescale-external

# If not running, start it (note: postgres-infra namespace)
kubectl port-forward -n postgres-infra service/postgres-timescale-external 5432:5432 &

# Test connection
psql -h localhost -p 5432 -U postgres -d trading_bot -c "SELECT 1;"
```

### No Rejected Attempts Showing

1. Check if the table exists:
```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'rejected_trade_attempts'
);
```

2. Verify the service is logging rejections:
```bash
# Check live trading service logs
kubectl logs -n trading-system deployment/live-trading-service --tail=100 | grep "Skipping"
```

3. Ensure API endpoint is working:
```bash
curl "http://localhost:11120/api/v1/trading/rejected-attempts?account_id=19c25392-8b61-4b71-a344-0eb04d275528"
```

## Benefits

1. **Transparency**: See why trades aren't executing
2. **Strategy Tuning**: Identify if confidence thresholds are too high
3. **Risk Management**: Understand when risk limits are preventing trades
4. **Debugging**: Quickly identify configuration issues
5. **Performance Analysis**: Compare rejected vs. executed trades

## Files Modified

1. **Models**: `services/live-trading-service/src/services/live_trading/models.py`
   - Added `RejectedTradeAttempt` model

2. **Services**:
   - `services/live-trading-service/src/services/live_trading/rejection_tracking_service.py` (NEW)
   - `services/live-trading-service/src/services/live_trading/strategy_execution_service.py`
   - `services/live-trading-service/src/services/live_trading/trading_service.py`

3. **API Routes**: `services/live-trading-service/routes/trading.py`
   - Added `/api/v1/trading/rejected-attempts` endpoint

4. **Monitor**: `scripts/live_trading_monitor_api.py`
   - Added rejected attempts display section

5. **Migration**: `alembic/versions/20251015_163213_add_rejected_trade_attempts.py`

## Future Enhancements

Potential improvements for the future:

1. **Rejection Statistics Dashboard**
   - Weekly/monthly rejection trends
   - Rejection rate by strategy
   - Most problematic symbols

2. **Alerts**
   - Discord notifications for repeated rejections
   - Alert when rejection rate exceeds threshold

3. **Auto-tuning**
   - Automatically adjust confidence thresholds based on rejection patterns
   - Suggest optimal risk parameters

4. **Retention Policy**
   - Archive old rejections after 30 days
   - Summary statistics for historical analysis

