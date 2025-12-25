# Database Configuration Fix - postgres-infra Migration

**Date**: 2025-10-09  
**Issue**: Some services were incorrectly pointing to the old `trading-system` namespace database instead of the centralized `postgres-infra` database.

## Problem Summary

The recommendations engine and related services were connecting to the **wrong database**:
- ❌ OLD: `timescaledb.trading-system.svc.cluster.local:5432`
- ✅ NEW: `postgres-timescale-external.postgres-infra.svc.cluster.local:5432`

## Services Fixed

### ✅ Files Updated

1. **k8s/strategy-service.yaml** - Recommendations API (port 11001)
   - Before: `timescaledb.trading-system.svc.cluster.local`
   - After: `postgres-timescale-external.postgres-infra.svc.cluster.local`

2. **k8s/configmap.yaml** - Shared configuration
   - Updated all three database URL variables
   - DATABASE_URL_WRITE, DATABASE_URL_READ, DATABASE_URL_TIMESERIES

3. **k8s/rss-feed-service.yaml**
   - Before: `timescaledb.trading-system.svc.cluster.local`
   - After: `postgres-timescale-external.postgres-infra.svc.cluster.local`

4. **k8s/unified-news-dashboard.yaml**
   - Before: `timescaledb.trading-system.svc.cluster.local`
   - After: `postgres-timescale-external.postgres-infra.svc.cluster.local`

5. **k8s/trading-monitor.yaml** (not deployed, but fixed for future use)
   - Before: `timescaledb.trading-system.svc.cluster.local`
   - After: `postgres-timescale-external.postgres-infra.svc.cluster.local`

### ✅ Services Already Correct

These services were already using the correct postgres-infra database:
- `market-data-service` ✅
- `unified-trading-dashboard` ✅
- `unified-analytics-dashboard` ✅
- `data-analysis-service` ✅

## Database Architecture

### postgres-infra Namespace
The centralized database infrastructure:
- **postgres-timescale-external** - Primary trading database
- **postgres-vector-external** - Vector storage for embeddings
- **postgres-age-external** - Graph database
- **postgres-regular-external** - Regular PostgreSQL

### trading-system Namespace (Deprecated)
These should NOT be used for new services:
- ⚠️ `timescaledb.trading-system` - Old database (deprecated)
- ⚠️ `postgresql-service.trading-system` - Risk management database (specific use only)

## Deployment Instructions

### Step 1: Apply ConfigMap Changes
```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 2: Apply Service Changes
```bash
# Update strategy-service (recommendations API)
kubectl apply -f k8s/strategy-service.yaml
kubectl rollout restart deployment/strategy-service -n trading-system

# Update rss-feed-service
kubectl apply -f k8s/rss-feed-service.yaml
kubectl rollout restart deployment/rss-feed-service -n trading-system

# Update unified-news-dashboard
kubectl apply -f k8s/unified-news-dashboard.yaml
kubectl rollout restart deployment/unified-news-dashboard -n trading-system
```

### Step 3: Verify Changes
```bash
# Check strategy-service is using correct database
kubectl get deployment strategy-service -n trading-system -o yaml | grep DATABASE_URL

# Check pod logs
kubectl logs -n trading-system deployment/strategy-service --tail=50

# Test recommendations endpoint
curl -s "http://localhost:11001/api/trading/recommendations?limit=3" | jq
```

### Step 4: Monitor for Issues
```bash
# Watch pod status
kubectl get pods -n trading-system -w

# Check for any errors
kubectl logs -n trading-system deployment/strategy-service --tail=100 | grep -i error
```

## Rollback Plan

If issues occur, rollback to previous database:

```bash
# Emergency rollback for strategy-service
kubectl set env deployment/strategy-service -n trading-system \
  DATABASE_URL="postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot"

kubectl rollout restart deployment/strategy-service -n trading-system
```

## Verification Checklist

- [ ] ConfigMap updated
- [ ] strategy-service redeployed and healthy
- [ ] rss-feed-service redeployed and healthy
- [ ] unified-news-dashboard redeployed and healthy
- [ ] Recommendations API returning data
- [ ] No database connection errors in logs
- [ ] All services connecting to postgres-infra

## Impact

**Affected Components:**
- Recommendations Engine (`make recommendations-all`)
- Strategy Service API (port 11001)
- RSS Feed Service
- Unified News Dashboard

**User Impact:**
- Recommendations will now use the centralized database
- Data consistency across all services
- Better performance with optimized postgres-infra setup

## Related Documentation

- [DATABASE_BACKUP_RESTORE_GUIDE.md](DATABASE_BACKUP_RESTORE_GUIDE.md)
- [PORT_MAP.md](PORT_MAP.md)
- [EXTERNAL_DATABASE_CONFIGURATION.md](../md/EXTERNAL_DATABASE_CONFIGURATION.md)



















