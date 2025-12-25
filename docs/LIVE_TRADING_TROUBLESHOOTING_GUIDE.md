# 🔍 Live Trading Troubleshooting Guide

**Last Updated**: 2025-10-17  
**Status**: ✅ **COMPREHENSIVE DIAGNOSTIC SYSTEM READY**

## 🚀 Quick Start

### Run Complete Diagnostic
```bash
# Full system diagnostic
make -f Makefile.live-trading troubleshoot

# Or use the alias
make -f Makefile.live-trading live-trading-troubleshooting
```

This single command provides a comprehensive diagnostic including:
- ✅ Kubernetes deployment status
- ✅ Pod health and status
- ✅ Port forward status
- ✅ Service health checks
- ✅ Authentication & token expiry
- ✅ Emergency stop status
- ✅ Trading mode (paper vs live)
- ✅ Risk limit configuration
- ✅ Market hours status
- ✅ Recent activity and logs
- ✅ Available Docker images
- ✅ Quick fix command suggestions

---

## 📊 What the Troubleshooter Checks

### 1. **Kubernetes Deployments**
Checks status of:
- `live-trading-service` (both trading-system and default namespaces)
- `paper-trading-k8s`
- `live-trading-executor` CronJob

### 2. **Pod Status**
Shows:
- Running live trading pods
- Recent CronJob execution pods
- Pod age and restart counts

### 3. **Port Forwards & Services**
Verifies:
- Active port forwards on 11120, 11180, 11181
- Kubernetes service endpoints
- Service availability

### 4. **Health Checks**
Tests:
- Live Trading Service (port 11120)
- Multi-Strategy Ensemble (port 11180)
- API response times

### 5. **Authentication**
Checks:
- API token expiration status
- Hours remaining until token expires
- Token validity

### 6. **Emergency Stop Status**
Shows:
- Whether emergency stop is active
- Stop reason and timestamp
- Trading enabled/disabled state

### 7. **Trading Configuration**
Displays:
- Trading mode (PAPER or LIVE)
- Risk limits (daily loss, position size, max positions)
- Portfolio heat limits

### 8. **Market Hours**
Verifies:
- Current Eastern Time
- Day of week (weekday vs weekend)
- Market open/closed status

### 9. **Recent Activity**
Shows:
- Last 5 CronJob executions
- Recent logs (last 10 lines)
- Execution timestamps

### 10. **Docker Images**
Lists:
- Available images in local registry
- Image availability for deployment

---

## 🛠️ Quick Fix Commands

The troubleshooter provides contextual commands based on what it finds:

### Deployment
```bash
make -f Makefile.live-trading deploy-auto-trading
```

### Port Forwards
```bash
kubectl port-forward -n trading-system service/live-trading-service 11120:8080 &
kubectl port-forward -n trading-system service/enhanced-portfolio-service 11180:80 &
```

### Monitoring
```bash
make -f Makefile.live-trading logs-auto-trading-live
make -f Makefile.live-trading status-auto-trading
```

### Emergency Controls
```bash
make -f Makefile.live-trading emergency-stop
make -f Makefile.live-trading emergency-resume
```

### Configuration
```bash
make -f Makefile.live-trading set-paper-mode
make -f Makefile.live-trading set-risk-conservative
```

### Testing
```bash
make -f Makefile.live-trading test-execution
make -f Makefile.live-trading check-token-expiry
```

---

## 📋 Other Useful Commands

### Status & Monitoring
```bash
# Quick status
make -f Makefile.live-trading status-auto-trading
make -f Makefile.live-trading quick-status

# View logs
make -f Makefile.live-trading logs-auto-trading        # Last execution
make -f Makefile.live-trading logs-auto-trading-live   # Real-time
make -f Makefile.live-trading quick-logs               # Alias

# Job history
make -f Makefile.live-trading jobs-auto-trading
```

### Risk Management
```bash
# Set risk levels
make -f Makefile.live-trading set-risk-conservative    # Safe
make -f Makefile.live-trading set-risk-moderate        # Balanced
make -f Makefile.live-trading set-risk-aggressive      # High risk

# View current limits
make -f Makefile.live-trading show-risk-limits
```

### Trading Mode
```bash
# Switch modes
make -f Makefile.live-trading set-paper-mode          # Safe testing
make -f Makefile.live-trading set-live-mode           # Real money (⚠️)

# Set execution intervals
make -f Makefile.live-trading set-interval-15         # Every 15 min
make -f Makefile.live-trading set-interval-30         # Every 30 min
make -f Makefile.live-trading set-interval-60         # Every 60 min
```

### Emergency Controls
```bash
# Stop trading immediately
make -f Makefile.live-trading emergency-stop
make -f Makefile.live-trading quick-stop              # Alias

# Resume trading
make -f Makefile.live-trading emergency-resume
make -f Makefile.live-trading quick-resume            # Alias

# Nuclear option (completely delete)
make -f Makefile.live-trading kill-auto-trading
```

### Token Management
```bash
# Check token expiry
make -f Makefile.live-trading check-token-expiry

# Update token
make -f Makefile.live-trading update-token TOKEN=eyJhbGc...
```

### Testing
```bash
# Manual execution trigger
make -f Makefile.live-trading test-execution

# Check market hours
make -f Makefile.live-trading test-market-hours
```

### Maintenance
```bash
# Clean old jobs
make -f Makefile.live-trading clean-old-jobs

# Backup configuration
make -f Makefile.live-trading backup-config

# Restore from backup
make -f Makefile.live-trading restore-config
```

### Deployment
```bash
# Deploy/redeploy
make -f Makefile.live-trading deploy-auto-trading
make -f Makefile.live-trading redeploy-auto-trading

# Remove
make -f Makefile.live-trading undeploy-auto-trading
```

---

## 🔍 Sample Troubleshooting Output

```
═══════════════════════════════════════════════════════
🔍 LIVE TRADING SYSTEM TROUBLESHOOTING
═══════════════════════════════════════════════════════

📊 SYSTEM OVERVIEW
═══════════════════════════════════════════════════════
Timestamp: 2025-10-17 11:26:10 MDT

🏗️  KUBERNETES DEPLOYMENTS
─────────────────────────────────────────────────────
Live Trading Service:
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
live-trading-service   1/1     1            1           41h

Paper Trading (K8s):
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
paper-trading-k8s   0/0     0            0           10d

CronJob Executor:
NAME                    SCHEDULE         SUSPEND   ACTIVE   LAST SCHEDULE
live-trading-executor   */15 * * * 1-5   False     0        41m

📦 POD STATUS
─────────────────────────────────────────────────────
Live Trading Pods:
NAME                                    READY   STATUS    RESTARTS   AGE
live-trading-service-75569bb88c-w2dgk   1/1     Running   0          16h

🏥 HEALTH CHECKS
─────────────────────────────────────────────────────
Live Trading Service (Port 11120):
  ✅ Service healthy

Multi-Strategy Ensemble (Port 11180):
  ✅ Service healthy

⚠️  EMERGENCY STOP STATUS
─────────────────────────────────────────────────────
  ✅ Emergency stop NOT active
  Trading is enabled

📈 TRADING MODE & CONFIGURATION
─────────────────────────────────────────────────────
  Mode: LIVE TRADING (REAL MONEY)

Risk Limits:
  Max Daily Loss: $500
  Max Position Size: 0.20
  Max Positions: 5

🕐 MARKET HOURS
─────────────────────────────────────────────────────
  Current ET time: 2025-10-17 13:26:12 EDT
  Day: Friday (Weekday)
  Market status: ✅ OPEN

📊 RECENT ACTIVITY
─────────────────────────────────────────────────────
Recent CronJob Executions:
live-trading-executor-29345325   Complete   1/1   36m

💡 QUICK FIX COMMANDS
═══════════════════════════════════════════════════════
... [contextual commands based on findings]
```

---

## 🐛 Common Issues & Solutions

### Issue: Services Not Running
**Symptoms**: No pods found, deployment shows 0/0

**Solution**:
```bash
# Deploy the service
make -f Makefile.live-trading deploy-auto-trading

# Or scale up existing deployment
kubectl scale deployment live-trading-service --replicas=1 -n trading-system
```

### Issue: Port Forwards Not Active
**Symptoms**: Health checks fail, "Not accessible" messages

**Solution**:
```bash
# Setup port forwards
kubectl port-forward -n trading-system service/live-trading-service 11120:8080 &
kubectl port-forward -n trading-system service/enhanced-portfolio-service 11180:80 &
```

### Issue: Token Expired
**Symptoms**: "Token expired X hours ago" message

**Solution**:
```bash
# Update with new token
make -f Makefile.live-trading update-token TOKEN=<your_new_token>
```

### Issue: Emergency Stop Active
**Symptoms**: "EMERGENCY STOP ACTIVE" message, trading disabled

**Solution**:
```bash
# Resume trading
make -f Makefile.live-trading emergency-resume
```

### Issue: Wrong Trading Mode
**Symptoms**: In LIVE mode when you want PAPER (or vice versa)

**Solution**:
```bash
# Switch to paper mode (safe)
make -f Makefile.live-trading set-paper-mode

# Switch to live mode (⚠️ real money)
make -f Makefile.live-trading set-live-mode
```

### Issue: CronJob Not Executing
**Symptoms**: No recent executions, LAST SCHEDULE shows long ago

**Solution**:
```bash
# Check if suspended
kubectl get cronjob live-trading-executor -n default

# Manually trigger execution to test
make -f Makefile.live-trading test-execution

# Check logs for errors
make -f Makefile.live-trading logs-auto-trading
```

### Issue: High Risk Limits
**Symptoms**: Risk limits seem too aggressive

**Solution**:
```bash
# Set conservative limits
make -f Makefile.live-trading set-risk-conservative

# Or customize via kubectl
kubectl set env cronjob/live-trading-executor -n default \
  MAX_DAILY_LOSS=100 \
  MAX_POSITION_SIZE=0.05 \
  MAX_POSITIONS=2
```

---

## 📖 Integration with Other Systems

### Recommendations System
The live trading system can use recommendations from:
```bash
make recommendations-multi           # Multi-timeframe analysis
make recommendations-enhanced        # Daily recommendations
make recommendations-intraday        # Day trading signals
```

### Service Discovery
Check all available services:
```bash
make services-list                   # All buildable services
```

### Build & Deploy Any Service
```bash
make build-service SERVICE=live-trading-service
make deploy-service SERVICE=live-trading-service
```

---

## 🎯 Best Practices

### 1. **Always Start with Troubleshooting**
Before making changes:
```bash
make -f Makefile.live-trading troubleshoot
```

### 2. **Use Paper Mode First**
Test strategies in paper mode:
```bash
make -f Makefile.live-trading set-paper-mode
```

### 3. **Set Conservative Risk Limits**
Start with low risk:
```bash
make -f Makefile.live-trading set-risk-conservative
```

### 4. **Monitor Regularly**
Check status frequently:
```bash
make -f Makefile.live-trading status-auto-trading
make -f Makefile.live-trading check-token-expiry
```

### 5. **Keep Backups**
Backup before changes:
```bash
make -f Makefile.live-trading backup-config
```

### 6. **Use Emergency Stop When Needed**
Don't hesitate to stop trading:
```bash
make -f Makefile.live-trading emergency-stop
```

---

## 📚 Related Documentation

- **Port Mapping**: `docs/PORT_MAP.md`
- **Recommendations System**: `RECOMMENDATIONS_SYSTEM_GUIDE.md`
- **Service Management**: `Makefile.versioning`
- **Live Trading Makefile**: `Makefile.live-trading`

---

## ✅ Pre-Flight Checklist

Before enabling live trading, verify:

- [ ] Run troubleshooting: `make -f Makefile.live-trading troubleshoot`
- [ ] ✅ All services running and healthy
- [ ] ✅ Token valid and not expired
- [ ] ✅ Emergency stop NOT active
- [ ] ✅ Risk limits set appropriately
- [ ] ✅ Trading mode set correctly (paper vs live)
- [ ] ✅ Market hours checked
- [ ] ✅ Port forwards active
- [ ] ✅ Recent executions successful
- [ ] ✅ Logs show no errors

---

## 🎉 Success!

You now have a comprehensive live trading troubleshooting system!

**Quick diagnostic anytime**:
```bash
make -f Makefile.live-trading troubleshoot
```

**View all available commands**:
```bash
make -f Makefile.live-trading help
```

---

**Questions or Issues?**
Run `make -f Makefile.live-trading troubleshoot` for diagnostic information and contextual fix suggestions.

**⚠️ Important**: Always verify you're in the correct trading mode (paper vs live) before making changes!


