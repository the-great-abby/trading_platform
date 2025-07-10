# ✅ Monitor ↔ API Setup Checklist

## 🚀 Initial Setup (One-time)

- [ ] **Deploy backtest API to Kubernetes**
  ```bash
  ./scripts/deploy-backtest-api.sh
  ```

- [ ] **Verify API is running**
  ```bash
  kubectl get pods -l app=backtest-api -n trading-system
  ```

- [ ] **Test API connection**
  ```bash
  curl http://localhost:10001/
  ```

## 🔄 Daily Usage

### **Step 1: Start Port Forward**
- [ ] **Open new terminal**
- [ ] **Run port forward command**
  ```bash
  kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
  ```
- [ ] **Keep this terminal open**

### **Step 2: Run Monitor**
- [ ] **Open another terminal**
- [ ] **Run monitor**
  ```bash
  make monitor-demo-api
  ```
- [ ] **Monitor should show real data**

## 🛠️ Troubleshooting

### **If Monitor Shows "Connection refused"**
- [ ] Check if port forward is running
- [ ] Restart port forward command
- [ ] Verify API pods are running

### **If Monitor Shows "No data available"**
- [ ] Run a backtest first
  ```bash
  make backend-kube-backtest
  ```
- [ ] Check database has data
- [ ] Restart monitor

### **If API Returns 500 Errors**
- [ ] Check database migrations
- [ ] Check database logs
- [ ] Restart API deployment

## 📋 Quick Commands Reference

| Action | Command |
|--------|---------|
| Deploy API | `./scripts/deploy-backtest-api.sh` |
| Port Forward | `kubectl port-forward svc/backtest-api 10001:10001 -n trading-system` |
| Run Monitor | `make monitor-demo-api` |
| Check API Status | `kubectl get pods -l app=backtest-api -n trading-system` |
| View API Logs | `kubectl logs deployment/backtest-api -n trading-system` |
| Test API | `curl http://localhost:10001/` |

## 🎯 Success Indicators

✅ **Port forward shows**: `Forwarding from 127.0.0.1:10001 -> 10001`  
✅ **API test returns**: `{"status": "healthy"}`  
✅ **Monitor shows**: Real strategy data and P&L  
✅ **No errors**: In monitor or API logs  

## 🚨 Emergency Reset

If everything breaks:

1. **Stop all processes** (Ctrl+C)
2. **Redeploy API**:
   ```bash
   ./scripts/deploy-backtest-api.sh
   ```
3. **Restart port forward**:
   ```bash
   kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
   ```
4. **Restart monitor**:
   ```bash
   make monitor-demo-api
   ```

---

**This is ORION, Mission Control. Follow this checklist for successful monitor ↔ API operation! 🚀** 