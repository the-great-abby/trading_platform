# 🚀 Quick Reference: Monitor ↔ API Process

## 🎯 One-Page Cheat Sheet

### **Deploy API to Kubernetes**
```bash
# Build and deploy the backtest API
./scripts/deploy-backtest-api.sh

# Verify deployment
kubectl get pods -l app=backtest-api -n trading-system
```

### **Port Forward API (Keep Running)**
```bash
# Forward API to localhost (run in separate terminal)
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
```

### **Run Monitor with Real Data**
```bash
# Run monitor that connects to API
make monitor-demo-api

# Or run directly
python demo_monitor_with_api.py
```

## 🔧 Troubleshooting Commands

### **Check API Status**
```bash
# Check if API pods are running
kubectl get pods -l app=backtest-api -n trading-system

# Check API logs
kubectl logs deployment/backtest-api -n trading-system

# Test API connection
curl http://localhost:10001/
```

### **Check Database**
```bash
# Check database pods
kubectl get pods -l app=postgres -n trading-system

# Check database logs
kubectl logs deployment/postgres -n trading-system
```

### **Check Monitor**
```bash
# Test API client
python demo_backtest_api.py

# Check monitor logs
python demo_monitor_with_api.py
```

## 📊 Architecture Summary

```
Your Host ←→ Port Forward ←→ Kubernetes API ←→ Database
Monitor    ←→ localhost:10001 ←→ backtest-api ←→ PostgreSQL
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Run port forward command |
| "No data available" | Run a backtest first |
| API 500 errors | Check database migrations |
| Monitor shows old data | Restart monitor |

## 📋 File Locations

- **API Service**: `services/backtest-api/`
- **K8s Config**: `k8s/backtest-api.yaml`
- **Monitor**: `src/utils/space_station_monitor.py`
- **API Client**: `src/utils/backtest_api_client.py`
- **Deploy Script**: `scripts/deploy-backtest-api.sh`

## 🎯 Essential Makefile Targets

```bash
# Deploy API
make -f Makefile.kubernetes k8s-deploy-backtest-api

# Check status
make -f Makefile.kubernetes k8s-status-backtest

# View logs
make -f Makefile.kubernetes k8s-logs-backtest

# Run monitor
make monitor-demo-api
```

---

**Remember: Always run port forward before starting monitor! 🚀** 