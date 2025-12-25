# 🔧 Service Restoration Guide - Using Wizard System

**Last Updated**: December 4, 2025  
**Status**: 2 services need restoration (market-data-service, rss-feed-service)  
**Root Cause**: Database and RabbitMQ connection configuration issues

---

## 🎯 Problem Summary

| Service | Status | Issue | Fix Required |
|---------|--------|-------|--------------|
| **market-data-service** | ❌ CrashLoopBackOff | Hardcoded IP `10.42.0.35` no longer valid | Update to use service DNS |
| **rss-feed-service** | ⏸️ Pending | Wrong RabbitMQ service name | Update RabbitMQ URL |

**Current Infrastructure Status:**
- ✅ Database: Running in `postgres-infra` namespace
  - Service: `postgres-timescale-external.postgres-infra.svc.cluster.local:5432`
- ✅ RabbitMQ: Running in `rabbitmq-system` namespace
  - Service: `rabbitmq.rabbitmq-system.svc.cluster.local:5672`
- ✅ Redis: Running in `redis` namespace
  - Service: `redis.redis.svc.cluster.local:6379`

---

## 🧙 Wizard-Based Restoration Walkthrough

This guide uses the **Trading System Wizard** for an interactive experience!

### Step 0: Launch the Wizard

```bash
make wizard
# Or the shortcut:
make wiz
```

---

## 📋 Phase 1: Fix Configuration Issues

### Fix 1: Market Data Service - Database Connection

**Issue**: Using hardcoded IP address instead of DNS service name

**Manual Fix Steps:**

1. **Update the deployment configuration:**

```bash
# Edit the market-data-service deployment
kubectl edit deployment market-data-service -n trading-system
```

2. **Find this line** (around line 26):
```yaml
- name: DATABASE_URL
  value: "postgresql://postgres:postgres@10.42.0.35:5432/trading_bot"
```

3. **Replace with:**
```yaml
- name: DATABASE_URL
  value: "postgresql://postgres:password@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot"
```

4. **Save and exit** (`:wq` in vim or `Ctrl+X` then `Y` in nano)

**Verification:**
```bash
# Watch the pod restart
kubectl get pods -n trading-system -w
# Wait until market-data-service shows 1/1 Running
```

---

### Fix 2: RSS Feed Service - RabbitMQ Connection

**Issue**: Looking for `rabbitmq-service` instead of `rabbitmq.rabbitmq-system.svc.cluster.local`

**Manual Fix Steps:**

1. **Update the deployment configuration:**

```bash
# Edit the rss-feed-service deployment
kubectl edit deployment rss-feed-service -n trading-system
```

2. **Find this line** (around line 31):
```yaml
- name: RABBITMQ_URL
  value: "amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost"
```

3. **Replace with:**
```yaml
- name: RABBITMQ_URL
  value: "amqp://guest:guest@rabbitmq.rabbitmq-system.svc.cluster.local:5672/"
```

**Note:** The RabbitMQ in `rabbitmq-system` uses default `guest:guest` credentials, not `trading_user:trading_pass`.

4. **Save and exit**

**Verification:**
```bash
# Watch the pod start
kubectl get pods -n trading-system -w
# Wait until rss-feed-service shows 1/1 Running
```

---

## 🧙 Phase 2: Using Wizard for Verification

Once manual fixes are complete, use the wizard to verify system status!

### Wizard Navigation Steps:

1. **Launch Wizard:**
```bash
make wizard
```

2. **Check System Status:**
   - Select: `9` (Quick Status)
   - Select: `1` (status)
   - This shows you port forwards, pods, and overall health

3. **Check Kubernetes Pods:**
   - Select: `6` (Kubernetes)
   - Select: `2` (k8s-pods)
   - Verify all services show `Running` status

4. **Check Service Logs:**
   - Select: `6` (Kubernetes)
   - Select: `3` (k8s-logs)
   - Check market-data-service and rss-feed-service logs

---

## 🔌 Phase 3: Setup Port Forwarding (Using Wizard!)

### Option A: Using Wizard (Recommended)

1. **Launch Wizard:**
```bash
make wizard
```

2. **Start All Port Forwards:**
   - Select: `8` (Port Forwarding)
   - Select: `1` (port-start)
   - This will start port forwards for all active services!

3. **Check Port Forward Status:**
   - Select: `8` (Port Forwarding)
   - Select: `3` (port-status)
   - Verify ports are active

4. **Health Check All Ports:**
   - Select: `8` (Port Forwarding)
   - Select: `4` (port-health-check)
   - Confirms services are responding

### Option B: Manual Port Forward Commands

If you prefer manual control:

```bash
# Market Data Service
kubectl port-forward -n trading-system svc/market-data-service 11084:11084 &

# RSS Feed Service  
kubectl port-forward -n trading-system svc/rss-feed-service 11004:11004 &

# Check all port forwards
ps aux | grep "kubectl port-forward" | grep -v grep
```

---

## 🧙 Phase 4: Test Services (Using Wizard!)

### Using Wizard for Testing:

1. **Launch Wizard:**
```bash
make wizard
```

2. **Check Service Status:**
   - Select: `2` (Service Management)
   - Select: `3` (services-status)
   - Shows all running services with health status

3. **View Service Logs:**
   - Select: `6` (Kubernetes)
   - Select: `3` (k8s-logs)
   - Follow prompts to view specific service logs

### Manual Testing Commands:

```bash
# Test Market Data Service
curl -s http://localhost:11084/health | jq

# Test RSS Feed Service
curl -s http://localhost:11004/health | jq

# Check service logs
kubectl logs -n trading-system deployment/market-data-service --tail=50
kubectl logs -n trading-system deployment/rss-feed-service --tail=50
```

---

## 📊 Phase 5: Full System Health Check

### Using Wizard for Complete Status:

```bash
make wizard
# Select: 9 (Quick Status)
# Select: 1 (status)
```

This will show:
- ✅ Active port forwards
- ✅ Running pods
- ✅ Registry status
- ✅ References to PORT_MAP.md and DEPLOY_MAP.md

### Expected Output After Restoration:

```
☸️  Kubernetes Pods:
  Running: 9/9  ✅

🔌 Port Forwards:
  Active: 9  ✅

🐳 Registry:
  ✅ Registry active

📋 All services healthy!
```

---

## 🎯 Quick Reference: Wizard Command Flow

### For Status Checks:
```
make wizard
→ 9 (Quick Status)
  → 1 (status) - Overall system status
  → 2 (sync) - Team sync view
  → 3 (critical) - Critical issues
```

### For Service Management:
```
make wizard
→ 2 (Service Management)
  → 1 (services-start) - Start all services
  → 3 (services-status) - Check service health
```

### For Port Forwarding:
```
make wizard
→ 8 (Port Forwarding)
  → 1 (port-start) - Start all port forwards
  → 3 (port-status) - Check port forward status
  → 4 (port-health-check) - Test service health
```

### For Kubernetes Operations:
```
make wizard
→ 6 (Kubernetes)
  → 1 (k8s-status) - Cluster status
  → 2 (k8s-pods) - Pod status
  → 3 (k8s-logs) - View logs
  → 4 (k8s-describe) - Detailed pod info
```

---

## 🔧 Permanent Fix: Update YAML Files

To prevent this issue in the future, update the source YAML files:

### File: `k8s/market-data-service.yaml`

```bash
# Edit the file
nano k8s/market-data-service.yaml

# Change line 26 from:
value: "postgresql://postgres:postgres@10.42.0.35:5432/trading_bot"

# To:
value: "postgresql://postgres:password@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot"
```

### File: `k8s/rss-feed-service.yaml`

```bash
# Edit the file
nano k8s/rss-feed-service.yaml

# Change line 31 from:
value: "amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost"

# To:
value: "amqp://guest:guest@rabbitmq.rabbitmq-system.svc.cluster.local:5672/"
```

**After editing, redeploy:**
```bash
kubectl apply -f k8s/market-data-service.yaml
kubectl apply -f k8s/rss-feed-service.yaml
```

---

## 🎓 Understanding the Fixes

### Why the Database Fix Works:

**Before (Broken):**
```
postgresql://postgres:postgres@10.42.0.35:5432/trading_bot
                                 ^^^^^^^^^^^
                                 Hardcoded Pod IP - changes on restart!
```

**After (Fixed):**
```
postgresql://postgres:password@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                DNS service name - stable across restarts!
```

### Why the RabbitMQ Fix Works:

**Before (Broken):**
```
amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost
                                  ^^^^^^^^^^^^^^^^
                                  Service doesn't exist in trading-system namespace!
```

**After (Fixed):**
```
amqp://guest:guest@rabbitmq.rabbitmq-system.svc.cluster.local:5672/
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                    Fully qualified service DNS in correct namespace!
```

---

## 🎉 Success Checklist

After completing this guide, you should have:

- [ ] market-data-service: Running (1/1)
- [ ] rss-feed-service: Running (1/1)
- [ ] All port forwards active (9 total)
- [ ] All health checks passing
- [ ] Able to access services via localhost ports
- [ ] No CrashLoopBackOff pods
- [ ] No pending pods (unless resource constrained)

---

## 🆘 Troubleshooting with Wizard

### If a service still won't start:

1. **Check logs via Wizard:**
```
make wizard → 6 (Kubernetes) → 3 (k8s-logs)
```

2. **Describe the pod:**
```
make wizard → 6 (Kubernetes) → 4 (k8s-describe)
```

3. **Check events:**
```
make wizard → 6 (Kubernetes) → 7 (k8s-events)
```

### Common Issues:

**Issue**: "ImagePullBackOff"
- **Solution**: Image doesn't exist, rebuild service
- **Wizard**: `3 (Build & Deploy) → 1 (build)`

**Issue**: "CrashLoopBackOff"
- **Solution**: Check logs for errors
- **Wizard**: `6 (Kubernetes) → 3 (k8s-logs)`

**Issue**: "Pending"
- **Solution**: Insufficient resources
- **Wizard**: `6 (Kubernetes) → 8 (k8s-resources)`

---

## 🔗 Related Documentation

- **Wizard System**: `docs/wizard-system.md`
- **Wizard Quick Reference**: `md/wizard-quick-reference.md`
- **Port Mapping**: Check `PORT_MAP.md` (if it exists)
- **Available Services**: `AVAILABLE_SERVICES_FOR_RESTORE.md`
- **Infrastructure Rules**: `.cursor/rules/infrastructure.mdc`
- **Port Mapping Rules**: `.cursor/rules/port-mapping.mdc`

---

## 🎯 Next Steps After Restoration

Once services are restored, consider:

1. **Deploy Additional Services** (see `AVAILABLE_SERVICES_FOR_RESTORE.md`)
2. **Setup Monitoring** (Prometheus, Grafana)
3. **Configure Alerts** (notification-service)
4. **Run Backtests** (via wizard or backtest-api)
5. **Check Trading Status** (via wizard: `12 (Trading Operations)`)

---

## 💡 Pro Tips

1. **Use the Wizard for Everything** - It's designed to make your life easier!
2. **Bookmark Common Flows** - Write down your most-used wizard paths
3. **Check Status First** - Always start with `make wizard → 9 → 1`
4. **Use Port Health Checks** - Regularly verify services with `make wizard → 8 → 4`
5. **Keep Logs Open** - Use `kubectl logs -f` in a separate terminal for real-time monitoring

---

**Questions or Issues?**

Use the wizard to diagnose:
```bash
make wizard
→ 9 (Quick Status) → 3 (critical)  # Shows critical issues
→ 6 (Kubernetes) → 7 (k8s-events)  # Recent cluster events
```

Good luck with your restoration! The wizard is here to guide you every step of the way! 🧙✨








