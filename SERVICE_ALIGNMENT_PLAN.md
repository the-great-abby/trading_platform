# Service Alignment Plan - PORT_MAP.md vs Current State

**Date**: November 4, 2025  
**Purpose**: Align services with PORT_MAP.md definitions

## 📊 Current State Analysis

### What's Running vs What PORT_MAP Says Should Run:

| Service | PORT_MAP Expected | Current Status | Action Needed |
|---------|------------------|----------------|---------------|
| **Live Trading Service** | Port 11120 | ❌ Not Deployed | Deploy with correct port |
| **Market Data Service** | Port 11084 | ✅ Deployed | ✅ Correct port |
| **Strategy Service** | Port 11001 | ⚠️ Port 80 (wrong) | Update to port 11001 |
| **Elliott Wave Service** | Port 11085 | ❌ Not Deployed | Build & deploy |
| **Unified Analytics Dashboard** | Port 11114 | ❌ Not Deployed | Build & deploy |
| **Unified Trading Dashboard** | Port 11115 | ❌ Not Deployed | Build & deploy |
| **Unified News Dashboard** | Port 11116 | ❌ Not Deployed | Build & deploy |
| **MCP Service** | Port 11117 | ❌ Not Deployed | Build & deploy |
| **Backtest API** | Port 11101 | ❌ Not Deployed | Build & deploy |
| **Prometheus** | Port 11190 | ❌ Not Deployed | Deploy |
| **RSS Feed Service** | Port 11004 | ❌ Not Deployed | Build & deploy |

### Infrastructure Services (External):

| Service | PORT_MAP Status | Current Location | Action Needed |
|---------|----------------|------------------|---------------|
| **Redis** | ⚠️ DEPRECATED (11379) | ✅ redis namespace | ✅ Already using external |
| **RabbitMQ** | ⚠️ DEPRECATED (11144) | ✅ rabbitmq-system namespace | ✅ Already using external |
| **TimescaleDB** | ⚠️ DEPRECATED (11140) | ✅ postgres-infra namespace | ✅ Already using external |
| **PostgreSQL Vector** | ⚠️ DEPRECATED (11180) | ✅ postgres-infra namespace | ✅ Already using external |

## 🎯 Alignment Actions

### Step 1: Fix Strategy Service Port
```bash
# Update strategy-service to use port 11001 instead of 80
# Edit k8s/strategy-service.yaml
```

### Step 2: Deploy Core Trading Services (Priority Order)

**High Priority (Essential for trading):**
1. **Live Trading Service** (11120) - Core trading functionality
2. **Elliott Wave Service** (11085) - Signal generation
3. **Backtest API** (11101) - Strategy testing

**Medium Priority (Dashboards & Monitoring):**
4. **Unified Trading Dashboard** (11115) - User interface
5. **Unified Analytics Dashboard** (11114) - Analytics
6. **Prometheus** (11190) - Monitoring

**Lower Priority (Additional Features):**
7. **Unified News Dashboard** (11116) - News analysis
8. **RSS Feed Service** (11004) - News feeds
9. **MCP Service** (11117) - MCP protocol

### Step 3: Build Required Docker Images

```bash
# Core services
make build-service SERVICE=live-trading-service
make build-service SERVICE=elliott-wave-service
make build-service SERVICE=backtest-api

# Dashboards
make build-service SERVICE=unified-trading-dashboard
make build-service SERVICE=unified-analytics-dashboard
make build-service SERVICE=unified-news-dashboard

# Additional
make build-service SERVICE=rss-feed-service
make build-service SERVICE=mcp-service
```

### Step 4: Deploy Services

```bash
# Deploy each service
kubectl apply -f k8s/live-trading-service.yaml
kubectl apply -f k8s/elliott-wave-service.yaml
kubectl apply -f k8s/backtest-api.yaml
kubectl apply -f k8s/unified-trading-dashboard.yaml
kubectl apply -f k8s/unified-analytics-dashboard.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
```

### Step 5: Setup Port Forwarding

According to PORT_MAP.md, port forwards should be set up for external access:
```bash
kubectl port-forward -n trading-system svc/live-trading-service 11120:8080 &
kubectl port-forward -n trading-system svc/market-data-service 11084:11084 &
kubectl port-forward -n trading-system svc/elliott-wave-service 11085:8000 &
kubectl port-forward -n trading-system svc/strategy-service 11001:80 &
kubectl port-forward -n trading-system svc/unified-trading-dashboard 11115:80 &
kubectl port-forward -n trading-system svc/unified-analytics-dashboard 11114:80 &
kubectl port-forward -n postgres-infra svc/prometheus 11190:9090 &
kubectl port-forward -n redis svc/redis 11379:6379 &
```

### Step 6: Update PORT_MAP.md

After deployment, update PORT_MAP.md with:
- Current active services
- Status indicators (✅ Active, ❌ Not Forwarded)
- Last updated timestamp
- Remove deprecated services

## 🔄 Service Migration Path

### Orphaned Services to Remove:
- `trading-ultra-service` (no deployment backing it)

### Services to Keep:
- `market-data-service` ✅
- `strategy-service` ⚠️ (fix port)

### Services to Add:
Based on PORT_MAP priorities, we should deploy services in this order based on available resources.

## 💾 Resource Budget Check

**Current Usage:**
- CPU: 186m used (~9%)
- Memory: 2.4Gi used (~40%)

**Available for New Services:**
- CPU: ~1800m
- Memory: ~3.6Gi

**Estimated Needs (from PORT_MAP services):**
- Live Trading Service: 250m CPU, 512Mi RAM
- Elliott Wave: 100m CPU, 256Mi RAM
- Dashboards (3x): 300m CPU, 768Mi RAM total
- Backtest API: 250m CPU, 512Mi RAM
- Prometheus: 200m CPU, 256Mi RAM

**Total Estimated**: ~1100m CPU, ~2.3Gi RAM
**Verdict**: ✅ We have enough resources!

## 🚀 Quick Start Command

To align everything at once:
```bash
# 1. Update strategy service port
# 2. Build essential services
make build-service SERVICE=live-trading-service
make build-service SERVICE=elliott-wave-service

# 3. Deploy services
kubectl apply -f k8s/live-trading-service.yaml
kubectl apply -f k8s/elliott-wave-service.yaml

# 4. Start port forwards as per PORT_MAP
./scripts/start-all-services.sh
```

---

**Next Action**: Shall I proceed with fixing the strategy-service port and deploying the core services according to PORT_MAP.md?



