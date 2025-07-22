# 🚀 Quick Reference Card

## 📍 **Most Used Endpoints**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Performance Dashboard** | 11000 | `http://localhost:11000/dashboard` | Trading performance analytics |
| **Trading Dashboard** | 11001 | `http://localhost:11001/` | Main trading interface |
| **Health Dashboard** | 11002 | `http://localhost:11002/dashboard` | System health monitoring |
| **RSS Feed Service** | 11004 | `http://localhost:11004/` | RSS feed generation |
| **Backtest Request** | 11031 | `http://localhost:11031/` | Backtest job submission |

## 🔧 **Quick Commands**

### **Port Forwarding**
```bash
# Start all port forwarding
./scripts/robust-port-forward.sh start

# Check status
./scripts/robust-port-forward.sh status

# Stop all port forwarding
./scripts/robust-port-forward.sh stop
```

### **Service Status**
```bash
# Check all endpoints status
./scripts/show-endpoints.sh

# View detailed endpoints map
cat docs/APPLICATION_ENDPOINTS_MAP.md
```

### **Individual Service Port Forward**
```bash
# RSS Feed Service
kubectl port-forward -n trading-system svc/rss-feed-service 11004:80

# Performance Dashboard
kubectl port-forward -n trading-system svc/performance-dashboard 11000:80

# Trading Dashboard
kubectl port-forward -n trading-system svc/trading-dashboard-service 11001:8000
```

## 🏥 **Health Checks**

```bash
# Quick health check all services
curl -s http://localhost:11000/health  # Performance Dashboard
curl -s http://localhost:11001/health  # Trading Dashboard
curl -s http://localhost:11002/health  # Health Dashboard
curl -s http://localhost:11004/health  # RSS Feed Service
curl -s http://localhost:11031/health  # Backtest Request
```

## 📊 **Current Status Summary**

- **Active Port Forwards**: 12
- **Running Pods**: 14
- **Total Services**: 28

## 🎯 **Port Allocation Rules**

- **11000-11009**: Dashboard Services
- **11010-11029**: API Services
- **11030-11049**: Trading Services
- **11050-11069**: Analytics Services
- **11070-11089**: Gateway & Infrastructure
- **11090-11099**: Development & Monitoring

## 🔄 **Last Updated**
- **Date**: 2025-07-22
- **Status**: All core services active
- **Port Range**: 11000-11999 ✅ 