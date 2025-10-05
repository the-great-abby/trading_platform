# Kubernetes vs Local Backtests - Network Access Explained

## TL;DR

- **In Kubernetes**: Use `timescaledb.trading-system.svc.cluster.local` ✅ **NO port-forward needed!**
- **Locally**: Need `localhost:5432` via port-forward ❌ (because you're outside the cluster)

---

## The Network Architecture

### Kubernetes Cluster Network
```
┌─────────────────────────────────────────┐
│  Kubernetes Cluster (Internal Network) │
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │ Backtest    │───→│ TimescaleDB  │  │
│  │ Pod         │    │ Service      │  │
│  │             │    │ :5432        │  │
│  └─────────────┘    └──────────────┘  │
│         ↑                              │
│         │ Can access via               │
│         │ timescaledb.trading-system   │
│         │ .svc.cluster.local:5432      │
└─────────────────────────────────────────┘
```

### Local MacBook Network
```
┌─────────────────────────────────────────┐
│  Your MacBook (Outside Cluster)         │
│                                         │
│  ┌─────────────┐                       │
│  │ Backtest    │  ❌ CANNOT ACCESS     │
│  │ Script      │     timescaledb       │
│  │             │     .trading-system   │
│  └─────────────┘     .svc.cluster      │
│         │            .local             │
│         │                               │
│         ↓ port-forward required         │
└─────────────────────────────────────────┘
         │
         ↓ kubectl port-forward
┌─────────────────────────────────────────┐
│  Kubernetes Cluster                     │
│  ┌──────────────┐                      │
│  │ TimescaleDB  │←────────────────────┐│
│  │ :5432        │  localhost:5432     ││
│  └──────────────┘                      ││
└─────────────────────────────────────────┘
```

---

## When to Use Each Approach

### Use Kubernetes Service Address (No Port-Forward) ✅

**When**: Running backtest as Kubernetes Job/Pod

**Example**:
```bash
# Deploy backtest job to Kubernetes
kubectl apply -f k8s/backtest-2year-real-data.yaml

# Check logs
kubectl logs -n trading-system job/backtest-2year-real-data -f
```

**DATABASE_URL**:
```
postgresql://trading_user:password@timescaledb.trading-system.svc.cluster.local:5432/trading_bot
```

**Why it works**:
- Pod is inside cluster network
- Can resolve Kubernetes DNS names
- Direct service-to-service communication
- No port-forward needed!

---

### Use Port-Forward (Local Only) ❌

**When**: Running backtest script locally on MacBook

**Example**:
```bash
# 1. Port-forward
kubectl port-forward -n trading-system svc/timescaledb 5432:5432 &

# 2. Set DATABASE_URL with localhost
export DATABASE_URL="postgresql://trading_user:password@localhost:5432/trading_bot"

# 3. Run locally
python3 run/run_2year_automated_backtest.py
```

**Why it's needed**:
- MacBook is outside cluster network
- Cannot resolve `*.svc.cluster.local` DNS names
- Port-forward creates tunnel from localhost:5432 → timescaledb:5432

---

## Recommended Approach

### For Production/Real Backtests: Use Kubernetes ✅

```bash
# 1. Deploy backtest job
kubectl apply -f k8s/backtest-2year-real-data.yaml

# 2. Watch progress
kubectl logs -n trading-system job/backtest-2year-real-data -f

# 3. Get results
kubectl logs -n trading-system job/backtest-2year-real-data
```

**Advantages**:
- ✅ No port-forward setup needed
- ✅ Uses internal cluster network (faster)
- ✅ Proper resource limits/requests
- ✅ Can scale easily
- ✅ Logs are preserved
- ✅ Automatic retry on failure

### For Development/Testing: Use Local

```bash
# Quick local testing with port-forward
./run_backtest_with_real_data.sh
```

**Advantages**:
- ✅ Faster iteration
- ✅ Easier debugging
- ✅ Can use IDE debugger
- ✅ Immediate results

---

## Common Issues

### Issue 1: "Can't resolve timescaledb.trading-system.svc.cluster.local"

**Cause**: Running locally but using Kubernetes DNS name

**Solution**: Use port-forward and `localhost`:
```bash
kubectl port-forward -n trading-system svc/timescaledb 5432:5432
export DATABASE_URL="postgresql://...@localhost:5432/..."
```

### Issue 2: "Connection refused to localhost:5432"

**Cause**: No port-forward active or wrong port

**Solution**: Start port-forward:
```bash
# Check if running
ps aux | grep "port-forward.*timescaledb"

# Start if not running
kubectl port-forward -n trading-system svc/timescaledb 5432:5432
```

### Issue 3: Backtest uses mock data instead of real data

**Cause**: DATABASE_URL not set

**Solution**:
- **In Kubernetes**: Set in env vars (already done in job YAML)
- **Locally**: Export DATABASE_URL environment variable

---

## Current Status of Your Backtest Jobs

### ✅ Already Correct (Use Kubernetes Service):
- `k8s/alembic-migration-job.yaml` - Uses `timescaledb.trading-system.svc.cluster.local`
- `k8s/backtest-2year-real-data.yaml` - NEW: Proper backtest job

### ⚠️ Needs Update:
- `k8s/backtest-2year-comprehensive.yaml` - Missing DATABASE_URL (falls back to mock data!)

---

## Summary

| Environment | Service Address | Port-Forward Needed? | DATABASE_URL |
|------------|----------------|---------------------|--------------|
| **Kubernetes Job** | `timescaledb.trading-system.svc.cluster.local:5432` | ❌ No | Set in job YAML |
| **Local MacBook** | `localhost:5432` | ✅ Yes | Set in shell |

**You were absolutely right!** When running in Kubernetes, you should use the internal service address and don't need port-forward at all!







