# 🎯 Recommendations System Complete Guide

**Last Updated**: 2025-10-17  
**Status**: ✅ **ALL SERVICES OPERATIONAL**

## 📊 System Overview

The recommendations system provides multi-timeframe trading analysis by combining:
- **Daily analysis** (40% weight) - Long-term trends
- **Hourly analysis** (40% weight) - Momentum signals  
- **15-minute analysis** (20% weight) - Entry timing

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Recommendations System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌────────────┐│
│  │   Strategy   │◄────►│ Market Data  │◄────►│  Elliott   ││
│  │   Service    │      │   Service    │      │    Wave    ││
│  │  (Port 11001)│      │ (Port 11084) │      │(Port 11085)││
│  └──────────────┘      └──────────────┘      └────────────┘│
│         │                     │                      │       │
│         └─────────────────────┴──────────────────────┘       │
│                              │                                │
│                    Multi-Timeframe Analysis                   │
│                    Technical Indicators                       │
│                    Pattern Recognition                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Check System Status
```bash
make recommendations-troubleshooting
```

### 2. Deploy Required Services (if needed)
```bash
# Deploy market-data-service
make recommendations-deploy-market-data

# Or deploy all recommendation services at once
make deploy-recommendations-services
```

### 3. Setup Port Forwards
```bash
make recommendations-port-forwards
```

### 4. Test Services
```bash
make recommendations-test
```

### 5. Get Recommendations!
```bash
# Multi-timeframe analysis (recommended)
make recommendations-multi

# Other options
make recommendations-enhanced    # Daily swing trading
make recommendations-hourly      # Hourly analysis
make recommendations-intraday    # Day trading signals
make recommendations-15m         # Ultra-fast scalping
```

---

## 📋 Required Services

### **1. Strategy Service** ✅ Running
- **Status**: REQUIRED
- **Port**: 11001
- **Image**: `localhost:32000/strategy-service:latest`
- **Deployment**: `k8s/strategy-service.yaml`
- **Purpose**: Main recommendation engine with multi-timeframe logic

**Deploy:**
```bash
make deploy-service SERVICE=strategy-service
kubectl port-forward -n trading-system service/strategy-service 11001:80 &
```

### **2. Market Data Service** ✅ Running
- **Status**: REQUIRED
- **Port**: 11084
- **Image**: `localhost:32000/market-data-service:latest`
- **Deployment**: `k8s/market-data-service.yaml`
- **Purpose**: Provides historical market data for technical analysis

**Deploy:**
```bash
make deploy-service SERVICE=market-data-service
kubectl port-forward -n trading-system service/market-data-service 11084:11084 &
```

**Note**: If deployment fails with `CreateContainerConfigError` about `iex-cloud-api-key`, this has been fixed by making the secret optional.

### **3. Elliott Wave Service** ✅ Running
- **Status**: OPTIONAL (enhances analysis)
- **Port**: 11085
- **Image**: `localhost:32000/elliott-wave-service:latest`
- **Deployment**: `k8s/elliott-wave-service.yaml`
- **Purpose**: Elliott Wave pattern detection for additional signals

**Deploy:**
```bash
make deploy-service SERVICE=elliott-wave-service
kubectl port-forward -n trading-system service/elliott-wave-service 11085:8000 &
```

---

## 🛠️ Universal Service Management

### New Universal Build/Deploy Commands

**List All Available Services:**
```bash
make services-list
```

**Build Any Service:**
```bash
make build-service SERVICE=<service-name>

# Examples:
make build-service SERVICE=market-data-service
make build-service SERVICE=rss-feed-service
make build-service SERVICE=analytics-service
```

**Deploy Any Service:**
```bash
make deploy-service SERVICE=<service-name>

# Examples:
make deploy-service SERVICE=elliott-wave-service
make deploy-service SERVICE=live-trading-service
```

### Pre-defined Service Shortcuts

These shortcuts are still available for commonly used services:

```bash
# Trading Services
make build-strategy / deploy-strategy
make build-market-data / deploy-market-data
make build-elliott-wave / deploy-elliott-wave

# Dashboards
make build-dashboards / deploy-dashboards

# AI Services
make build-ai-analysis / deploy-ai-analysis

# MCP Service
make build-mcp / deploy-mcp
```

---

## 🔍 Troubleshooting Commands

### **recommendations-troubleshooting**
Comprehensive diagnostic that checks:
- ✅ Pod status for all services
- ✅ Port forward status
- ✅ Docker images in registry
- ✅ Quick fix suggestions

```bash
make recommendations-troubleshooting
```

**Sample Output:**
```
🔍 RECOMMENDATIONS SYSTEM TROUBLESHOOTING
=========================================

📋 Checking Required Services...

1. Strategy Service (Port 11001):
strategy-service-df844469d-h76gl   1/1     Running   0          45m
  ✅ Port forward active

2. Market Data Service (Port 11084):
market-data-service-7db94d8448-5kwh2   1/1     Running   0          5m
  ✅ Port forward active

3. Elliott Wave Service (Port 11085) [Optional]:
elliott-wave-service-77dc88888b-j257k   1/1     Running   0          16h
  ✅ Port forward active

💡 Quick Fix Commands:
  make recommendations-deploy-all
  make recommendations-port-forwards
  make recommendations-test
```

### **recommendations-deploy-market-data**
Deploys and scales up the market-data-service specifically:
```bash
make recommendations-deploy-market-data
```

### **recommendations-deploy-all**
Deploys all recommendation services at once:
```bash
make recommendations-deploy-all
```

### **recommendations-port-forwards**
Sets up all required port forwards (kills existing ones first):
```bash
make recommendations-port-forwards
```

### **recommendations-test**
Tests all service health endpoints and the multi-timeframe API:
```bash
make recommendations-test
```

### **recommendations-logs**
Shows recent logs from all recommendation services:
```bash
make recommendations-logs
```

---

## 📊 Recommendation Commands

### **recommendations-multi** (Recommended)
Multi-timeframe analysis combining daily, hourly, and 15m signals:
```bash
make recommendations-multi
```

**Output Example:**
```
🎯 MULTI-TIMEFRAME ANALYSIS
============================

📊 Combining Daily trend + Hourly momentum + 15m timing...

🎯 CSCO @ $70.12 - BUY (Score: 49.52)
   Confidence: 49% | Alignment Boost: 1.0x | Timeframes: 3
   ⚠️ Mixed signals across timeframes
   Daily: BUY | Hourly: STRONG_BUY | 15m: HOLD
```

### Other Recommendation Commands

```bash
# Enhanced daily recommendations
make recommendations-enhanced

# Hourly timeframe
make recommendations-hourly

# Intraday trading (1h default)
make recommendations-intraday

# Ultra-fast 15-minute signals
make recommendations-15m

# Scan for Elliott Wave patterns
make recommendations-scan

# Quick top 3 recommendations
make recommendations-quick

# All recommendations (up to 10)
make recommendations-all

# Specific symbol
make recommendation SYMBOL=AAPL
```

---

## 🔧 Manual Service Management

If you need more control, you can manage services directly:

### Check Service Status
```bash
kubectl get pods -n trading-system | grep -E "(strategy|market-data|elliott-wave)"
kubectl get deployments -n trading-system | grep -E "(strategy|market-data|elliott-wave)"
```

### Scale Services
```bash
# Scale up
kubectl scale deployment market-data-service --replicas=1 -n trading-system
kubectl scale deployment elliott-wave-service --replicas=1 -n trading-system
kubectl scale deployment strategy-service --replicas=1 -n trading-system

# Scale down
kubectl scale deployment market-data-service --replicas=0 -n trading-system
```

### View Logs
```bash
kubectl logs -n trading-system -l app=strategy-service --tail=50 -f
kubectl logs -n trading-system -l app=market-data-service --tail=50 -f
kubectl logs -n trading-system -l app=elliott-wave-service --tail=50 -f
```

### Port Forward Manually
```bash
kubectl port-forward -n trading-system service/strategy-service 11001:80 &
kubectl port-forward -n trading-system service/market-data-service 11084:11084 &
kubectl port-forward -n trading-system service/elliott-wave-service 11085:8000 &
```

### Test Health Endpoints
```bash
curl http://localhost:11001/health | jq
curl http://localhost:11084/health | jq
curl http://localhost:11085/elliott-wave/health | jq
```

---

## 🐛 Common Issues & Solutions

### Issue: Market Data Service Fails to Start
**Error:** `CreateContainerConfigError: couldn't find key iex-cloud-api-key`

**Solution:**
The deployment has been fixed to make the IEX Cloud API key optional:
```bash
kubectl apply -f k8s/market-data-service.yaml
kubectl rollout restart deployment/market-data-service -n trading-system
```

### Issue: No Recommendations Returned
**Possible Causes:**
1. Market data not available for symbols
2. Services not fully initialized
3. Port forwards not active

**Solution:**
```bash
# 1. Check all services are running
make recommendations-troubleshooting

# 2. Check logs for errors
make recommendations-logs

# 3. Test endpoints individually
make recommendations-test
```

### Issue: Port Forwards Keep Dying
**Solution:**
Use the automated port forward manager:
```bash
make recommendations-port-forwards
```

This kills old port forwards and starts fresh ones.

### Issue: Service Won't Deploy
**Error:** Image not found or image pull errors

**Solution:**
Build and push the service image:
```bash
make build-service SERVICE=market-data-service
```

Or use the full deploy which builds automatically:
```bash
make deploy-service SERVICE=market-data-service
```

---

## 📚 Complete Command Reference

### Service Discovery
```bash
make services-list                          # List all buildable services
make services-available                     # Same as services-list
```

### Universal Service Management
```bash
make build-service SERVICE=<name>           # Build any service
make deploy-service SERVICE=<name>          # Deploy any service
```

### Recommendations System
```bash
make recommendations-troubleshooting        # Diagnose issues
make recommendations-deploy-market-data     # Deploy market data service
make recommendations-deploy-elliott-wave    # Deploy elliott wave service
make recommendations-deploy-all             # Deploy all services
make recommendations-port-forwards          # Setup port forwards
make recommendations-test                   # Test all endpoints
make recommendations-logs                   # View service logs
```

### Recommendations Analysis
```bash
make recommendations-multi                  # Multi-timeframe (best)
make recommendations-enhanced               # Daily analysis
make recommendations-hourly                 # Hourly analysis
make recommendations-intraday               # Day trading (1h)
make recommendations-15m                    # Scalping (15m)
make recommendations-scan                   # Elliott Wave patterns
make recommendations-quick                  # Top 3 only
make recommendations-all                    # Top 10
make recommendation SYMBOL=<symbol>         # Specific symbol
```

### Versioning System
```bash
make version                                # Show version info
make build                                  # Build all services
make push                                   # Build and push all
make deploy                                 # Build, push, deploy all
make clean                                  # Clean up images
```

---

## 📖 Additional Resources

- **Port Mapping**: `docs/PORT_MAP.md`
- **Deployment Management**: `DEPLOY_MAP.md`
- **Timeframe Reference**: `TIMEFRAME_QUICK_REFERENCE.md`
- **Backtest Guide**: `BACKTEST_QUICK_REFERENCE.md`
- **Bug Fixes**: `BUGFIX_SUMMARY.md`

---

## ✅ Current Status

**All Systems Operational** ✅

| Service | Status | Port | Health Check |
|---------|--------|------|--------------|
| Strategy Service | ✅ Running | 11001 | ✅ Healthy |
| Market Data Service | ✅ Running | 11084 | ✅ Healthy |
| Elliott Wave Service | ✅ Running | 11085 | ✅ Healthy |

**Port Forwards**: ✅ Active  
**Multi-Timeframe Analysis**: ✅ Working  
**Market Data**: ✅ Available  
**Elliott Wave Integration**: ✅ Functional

---

## 🎉 Success!

You now have a fully operational recommendations system with:
- ✅ Multi-timeframe analysis
- ✅ Universal service build/deploy commands
- ✅ Comprehensive troubleshooting tools
- ✅ Automated port forward management
- ✅ Easy service discovery

**Start trading smarter with:**
```bash
make recommendations-multi
```

---

**Questions or Issues?**
Run `make recommendations-troubleshooting` for diagnostic information and quick fix suggestions.


