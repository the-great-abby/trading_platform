# Capital Allocation & Exit Trading Fix

## 🚨 **Problems Identified**

### Problem 1: Capital Allocation Not Being Respected

**Root Cause**: Multiple conflicting configurations across different layers:

1. **YAML Configs** (`config/live_trading_strategies.yaml`):
   - Max single symbol: 20%
   - Max total exposure: 85%
   - Min cash reserve: 15%

2. **Database Risk Profile** (what's actually enforced):
   - `max_position_size`: $10,000 (absolute dollars, not percentage)
   - `max_portfolio_risk`: 5%
   - `max_daily_loss`: $1,000

**Impact**: The live trading service reads from the **database risk profile**, NOT the YAML configs. This means your intended capital allocation limits were never being enforced.

---

### Problem 2: Exit Trades NOT Being Executed

**Root Cause**: Position monitor service exists but is **never started**!

1. **Position Monitor exists** (`src/services/live_trading/position_monitor.py`) with proper stop-loss logic (8% stop loss)
2. **BUT** there's no code that calls `position_monitor.start_monitoring()` anywhere
3. **AND** your configs have `disable_engine_stop_loss: true` and `disable_engine_take_profit: true`

**Impact**: Losing positions can sit indefinitely without automatic exits. Exits only happen when:
- The strategy service is manually called
- The strategy returns a SELL recommendation with confidence >= 60%
- This means positions exceeding your loss limits may never exit!

---

## ✅ **Solutions Implemented**

### 1. Database Risk Profile Update Script

**File**: `scripts/fix_capital_allocation_and_exits.py`

Updates database risk profiles with correct capital allocation:
- Max position size: **$800** (20% of $4,000 portfolio)
- Max daily loss: **$200** (5% of $4,000 portfolio)
- Max portfolio risk: **15%** (allows 85% max exposure)
- Max daily trades: **10**

**Usage**:
```bash
# Connect to database via port-forward
kubectl port-forward -n trading-system deployment/timescaledb 5432:5432 &

# Run the fix script
python scripts/fix_capital_allocation_and_exits.py
```

---

### 2. Position Monitor Enablement Script

**File**: `scripts/enable_position_monitor.py`

Enables continuous position monitoring with automatic exit triggers:
- **Stop Loss**: 8% loss
- **Profit Target**: 15% gain
- **Max Holding**: 30 days
- **Min Holding**: 4 hours

**Usage**:
```bash
# Run manually (for testing)
python scripts/enable_position_monitor.py

# Or deploy as Kubernetes cronjob
kubectl apply -f k8s/position-monitor-cronjob.yaml
```

---

### 3. Emergency Exit Script

**File**: `scripts/emergency_exit_positions.py`

Immediately exits positions exceeding the 8% loss limit.

**Usage**:
```bash
# Dry run (show what would be exited)
python scripts/emergency_exit_positions.py

# Actually execute exits
python scripts/emergency_exit_positions.py --execute
```

---

### 4. Kubernetes Cronjobs

**File**: `k8s/position-monitor-cronjob.yaml`

Two automated monitoring jobs:

1. **Position Monitor** (every 5 minutes):
   - Checks all positions for exit conditions
   - Logs status and warnings

2. **Emergency Exit Check** (every 2 minutes):
   - Finds positions exceeding 8% loss
   - Automatically creates exit orders
   - **MORE AGGRESSIVE** to protect capital

**Deployment**:
```bash
kubectl apply -f k8s/position-monitor-cronjob.yaml
```

---

## 📋 **Step-by-Step Fix Process**

### Step 1: Update Database Risk Profile

```bash
# 1. Port-forward to database
kubectl port-forward -n trading-system deployment/timescaledb 5432:5432 &

# 2. Run fix script
python scripts/fix_capital_allocation_and_exits.py

# Expected output:
# ✅ Updated X risk profiles:
#    Max Position Size: $800.00 (20% of portfolio)
#    Max Portfolio Risk: 15.0%
#    Max Daily Loss: $200.00
```

### Step 2: Check for Positions Exceeding Limits

```bash
# Dry run to see what would be exited
python scripts/emergency_exit_positions.py

# If positions found with losses > 8%, execute exits
python scripts/emergency_exit_positions.py --execute
```

### Step 3: Enable Automatic Monitoring

```bash
# Deploy cronjobs for continuous monitoring
kubectl apply -f k8s/position-monitor-cronjob.yaml

# Verify cronjobs are running
kubectl get cronjobs -n trading-system

# Check logs
kubectl logs -n trading-system -l app=position-monitor --tail=50
```

### Step 4: Restart Live Trading Service

```bash
# Restart to apply changes
kubectl rollout restart -n trading-system deployment/live-trading-service

# Verify restart
kubectl get pods -n trading-system -l app=live-trading-service
```

---

## 🔍 **Verification**

### Check Risk Profile

```sql
-- Connect to database
kubectl exec -n trading-system deployment/timescaledb -- psql -U trading_user -d trading_db

-- Check risk profiles
SELECT 
    account_id,
    max_position_size,
    max_portfolio_risk,
    max_daily_loss,
    max_daily_trades
FROM risk_profiles;

-- Expected output:
-- max_position_size = 800.00
-- max_portfolio_risk = 0.15
-- max_daily_loss = 200.00
-- max_daily_trades = 10
```

### Check Positions

```sql
-- Find positions with excessive losses
SELECT 
    symbol,
    strategy,
    unrealized_pnl,
    unrealized_pnl_pct,
    created_at
FROM live_positions
WHERE status = 'OPEN'
    AND unrealized_pnl_pct <= -0.08
ORDER BY unrealized_pnl_pct ASC;

-- Should return 0 rows after emergency exits
```

### Check Cronjobs

```bash
# Check cronjob status
kubectl get cronjobs -n trading-system

# Check recent jobs
kubectl get jobs -n trading-system --sort-by=.metadata.creationTimestamp

# Check logs
kubectl logs -n trading-system -l app=position-monitor --tail=100
kubectl logs -n trading-system -l app=emergency-exit-check --tail=100
```

---

## 📊 **Capital Allocation Limits (Corrected)**

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| **Portfolio Value** | $4,000 | Initial capital |
| **Max Position Size** | $800 | 20% of portfolio |
| **Max Portfolio Risk** | 15% | Allows 85% exposure |
| **Max Daily Loss** | $200 | 5% of portfolio |
| **Max Daily Trades** | 10 | Conservative limit |
| **Stop Loss Per Position** | 8% | Auto-exit at -8% |
| **Profit Target Per Position** | 15% | Auto-exit at +15% |
| **Max Holding Period** | 30 days | Force exit after 30 days |

---

## 🔧 **Configuration Files Updated**

1. **Database Risk Profiles**:
   - Updated via `fix_capital_allocation_and_exits.py`
   - All accounts now use correct limits

2. **Position Monitor**:
   - Existing: `src/services/live_trading/position_monitor.py`
   - Now enabled via cronjob

3. **Emergency Exit**:
   - New: `scripts/emergency_exit_positions.py`
   - Automated via cronjob (every 2 minutes)

4. **Kubernetes Cronjobs**:
   - New: `k8s/position-monitor-cronjob.yaml`
   - Deploys 2 monitoring jobs

---

## ⚠️ **Important Notes**

### Why This Happened

1. **Configuration Layer Mismatch**: YAML configs were for display/documentation, but the actual enforcement was in the database risk profiles

2. **Missing Service Initialization**: The position monitor service was created but never integrated into the live trading service startup

3. **Disabled Engine Exits**: The configs had `disable_engine_stop_loss: true` which delegated exit responsibility to strategies, but strategies weren't reliably generating exit signals

### Prevention

1. **Single Source of Truth**: Database risk profiles are now the authoritative source
2. **Automated Monitoring**: Cronjobs ensure continuous position monitoring
3. **Multiple Safety Nets**:
   - Position monitor (every 5 minutes)
   - Emergency exit check (every 2 minutes)
   - Strategy-based exits (on strategy execution)

---

## 🚀 **Next Steps**

1. ✅ **Run the fix script** to update database risk profiles
2. ✅ **Check for positions** exceeding limits and exit if needed
3. ✅ **Deploy cronjobs** for continuous monitoring
4. ✅ **Restart live trading service** to apply changes
5. 📊 **Monitor logs** to verify everything is working

---

## 📞 **Support**

If you see:
- **Positions not exiting**: Check cronjob logs and verify position monitor is running
- **Capital limits not respected**: Verify database risk profiles were updated correctly
- **Cronjobs failing**: Check pod logs for errors

**Check Status**:
```bash
# All-in-one status check
kubectl get cronjobs,jobs,pods -n trading-system -l component=monitoring
```

---

## ✅ **Expected Results**

After applying these fixes:

1. ✅ **No position exceeds 20% of portfolio** ($800 limit enforced)
2. ✅ **No position exceeds 8% loss** (auto-exited within 2-5 minutes)
3. ✅ **Daily losses capped at $200** (5% of portfolio)
4. ✅ **Profitable positions auto-exit at 15% gain**
5. ✅ **All positions force-exited after 30 days max**

**You now have 3 layers of protection:**
1. Database risk limits (entry protection)
2. Position monitor (ongoing monitoring)
3. Emergency exit system (aggressive loss protection)









