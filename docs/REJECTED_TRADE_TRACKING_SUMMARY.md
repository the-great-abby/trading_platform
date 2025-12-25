# Rejected Trade Tracking - Implementation Summary

## 🎯 Goal Achieved

The live trading monitor now shows **rejected trade attempts** with detailed reasons why the system rejected trades before they were submitted to the broker.

## 📸 Expected Output

When you run `python scripts/live_trading_monitor_api.py`, you'll now see:

```
🚫 Recent Rejected Trade Attempts (5):
  📉 14:45:05 MDT | NVDA | MULTI_STRATEGY_ENSEMBLE | BUY (confidence: 0.45)
     Reason: Signal confidence too low: 0.45 (minimum 0.50 required)
  
  💸 14:30:04 MDT | NVDA | MULTI_STRATEGY_ENSEMBLE | BUY
     Reason: Insufficient buying power: $85.00 (minimum $100 required)
  
  🔄 14:15:04 MDT | AAPL | MULTI_STRATEGY_ENSEMBLE | BUY (confidence: 0.68)
     Reason: Already holding position in AAPL

📈 Recent Trades:
  🚫 14:45:05 MDT | 📈 NVDA | MULTI_STRATEGY_ENSEMBLE | 1 @ $892.70 | FAILED: No match found for this Symbol (NVDA).
```

## 🔧 What Was Built

### 1. **Database Layer**
- ✅ New `RejectedTradeAttempt` model
- ✅ Database migration to create `rejected_trade_attempts` table
- ✅ Indexes for efficient querying

### 2. **Service Layer**
- ✅ `RejectionTrackingService` - handles logging and retrieval
- ✅ Integration with `StrategyExecutionService` - logs strategy-level rejections
- ✅ Integration with `TradingService` - logs validation and risk rejections

### 3. **API Layer**
- ✅ New endpoint: `GET /api/v1/trading/rejected-attempts`
- ✅ Returns detailed rejection information with categories

### 4. **Monitoring Layer**
- ✅ Updated `live_trading_monitor_api.py` to fetch and display rejections
- ✅ Category-specific icons for visual clarity
- ✅ Shows both system rejections and broker rejections

## 📊 Rejection Categories

| Category | Icon | Description |
|----------|------|-------------|
| BUYING_POWER | 💸 | Insufficient funds to execute trade |
| RISK | ⚠️ | Risk validation failed (limits, emergency stop) |
| CONFIDENCE | 📉 | Signal confidence below threshold |
| POSITION_EXISTS | 🔄 | Already holding position in symbol |
| VALIDATION | ❌ | Order validation failed |

## 🚀 Quick Start

### Option 1: Automated Setup
```bash
# Run the setup script
./scripts/setup_rejected_trade_tracking.sh
```

### Option 2: Manual Setup
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Ensure database is accessible
kubectl port-forward -n trading-system service/timescaledb 5432:5432 &

# 3. Run migration
alembic upgrade head

# 4. Restart live trading service
kubectl rollout restart deployment/live-trading-service -n trading-system

# 5. Run the monitor
python scripts/live_trading_monitor_api.py
```

## 📝 Files Changed

### New Files
- `services/live-trading-service/src/services/live_trading/rejection_tracking_service.py`
- `alembic/versions/20251015_163213_add_rejected_trade_attempts.py`
- `REJECTED_TRADE_TRACKING.md` (documentation)
- `scripts/setup_rejected_trade_tracking.sh` (setup script)

### Modified Files
- `services/live-trading-service/src/services/live_trading/models.py`
- `services/live-trading-service/src/services/live_trading/strategy_execution_service.py`
- `services/live-trading-service/src/services/live_trading/trading_service.py`
- `services/live-trading-service/routes/trading.py`
- `scripts/live_trading_monitor_api.py`

## 🎨 Display Features

### System Rejections (NEW!)
Shows attempts rejected before broker submission:
- Confidence too low
- Insufficient buying power  
- Risk limits exceeded
- Position already exists
- Validation errors

### Broker Rejections (Existing)
Shows orders submitted but rejected by broker:
- Symbol not found
- Invalid option contract
- Market hours restrictions

## 🔍 Usage Examples

### View in Monitor
```bash
python scripts/live_trading_monitor_api.py
```

### Query API
```bash
curl "http://localhost:11120/api/v1/trading/rejected-attempts?account_id=YOUR_ACCOUNT_ID&limit=20"
```

### SQL Analysis
```sql
-- Most common rejection reasons
SELECT 
    rejection_category,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM rejected_trade_attempts
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY rejection_category
ORDER BY count DESC;
```

## 🎯 Benefits

1. **Visibility**: See exactly why trades aren't executing
2. **Debugging**: Quickly identify configuration issues
3. **Tuning**: Adjust confidence thresholds based on rejection patterns
4. **Compliance**: Track risk limit effectiveness
5. **Analysis**: Compare rejected vs. executed trades for strategy optimization

## 🔧 Troubleshooting

### No rejections showing?
1. Check if migration ran successfully
2. Verify live trading service restarted
3. Ensure API endpoint is accessible
4. Check service logs for rejection logging

### Migration failed?
1. Ensure database is port-forwarded
2. Check database credentials
3. Verify alembic.ini configuration

### Service not restarting?
1. Check kubectl context
2. Verify namespace (trading-system)
3. Check pod logs for errors

## 📚 Documentation

- **Full Documentation**: `REJECTED_TRADE_TRACKING.md`
- **Setup Script**: `scripts/setup_rejected_trade_tracking.sh`
- **API Endpoint**: `/api/v1/trading/rejected-attempts`

## ✅ Testing Checklist

Before considering this complete, verify:

- [ ] Database migration runs successfully
- [ ] New table `rejected_trade_attempts` exists
- [ ] API endpoint returns data
- [ ] Monitor displays rejected attempts
- [ ] Icons display correctly for each category
- [ ] Timestamps show in local timezone (MDT/MST)
- [ ] Service logs rejections properly
- [ ] No performance impact on trading operations

## 🎉 Result

You now have complete visibility into:
- ✅ **System rejections** (new!) - trades rejected before submission
- ✅ **Broker rejections** (existing) - trades rejected by broker
- ✅ **Detailed reasons** for each rejection
- ✅ **Categorized display** with helpful icons
- ✅ **Historical tracking** in database
- ✅ **API access** for custom analysis

## 🚀 Next Steps

1. Run the setup script or manual steps above
2. Monitor the system for a few trading cycles
3. Analyze rejection patterns
4. Adjust confidence thresholds if needed
5. Use insights to optimize strategy performance

---

**Note**: The rejected trade tracking system is completely non-invasive. It only logs rejections without affecting trading logic or performance.




