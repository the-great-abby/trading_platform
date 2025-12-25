# Live Trading Deployment Options

## Current Status

You have **TWO deployment configurations** for live trading:

### 1. `paper-trading-k8s` ✅ CURRENTLY RUNNING

**File**: `k8s/paper-trading-k8s.yaml`
**Namespace**: `trading-system`
**Status**: ✅ Active and running

**Configuration**:
- Single replica
- Resource-constrained (50m CPU / 128Mi RAM)
- Port 8080
- Encryption key from secret: `live-trading-encryption-key`
- Database: postgres-infra namespace
- Environment: Paper trading mode

**Access**:
```bash
# Port forward
kubectl port-forward -n trading-system deployment/paper-trading-k8s 11120:8080

# Check status
make live-trading-status

# Logs
kubectl logs -n trading-system deployment/paper-trading-k8s
```

### 2. `live-trading-service` ❌ NOT DEPLOYED (Template)

**File**: `k8s/live-trading-service.yaml`
**Namespace**: `trading-system`
**Status**: ❌ Not deployed (production-ready template)

**Configuration**:
- 2 replicas (production)
- Higher resources (200m CPU / 256Mi RAM)
- Horizontal Pod Autoscaler (2-10 replicas)
- Pod Disruption Budget
- Ingress configuration
- Health checks (liveness/readiness probes)

**This is a more production-ready configuration** with:
- High availability (multiple replicas)
- Auto-scaling based on CPU/memory
- Load balancing
- Ingress for external access
- Proper health monitoring

## Which One Should You Use?

### Use `paper-trading-k8s` (Current) If:
- ✅ Development/testing environment
- ✅ Resource-constrained (M1 MacBook)
- ✅ Paper trading only
- ✅ Single instance is sufficient
- ✅ Quick iteration and testing

### Use `live-trading-service` If:
- 🚀 Production environment
- 🚀 Need high availability
- 🚀 Auto-scaling requirements
- 🚀 External access via ingress
- 🚀 Better fault tolerance

## IaC Configuration Files

All configurations now properly set up for Infrastructure as Code:

| File | Purpose | Status |
|------|---------|--------|
| `k8s/paper-trading-k8s.yaml` | Current paper trading deployment | ✅ Complete |
| `k8s/live-trading-service.yaml` | Production-ready template | ✅ Complete |
| `k8s/secrets/live-trading-encryption.yaml` | Encryption key secret | ✅ Created |
| `k8s/secrets/README.md` | Secrets management guide | ✅ Created |

## Encryption Key Configuration

Both deployments now have proper encryption key configuration:

### `paper-trading-k8s`
```yaml
- name: ENCRYPTION_KEY
  valueFrom:
    secretKeyRef:
      name: live-trading-encryption-key
      key: encryption-key
```

### `live-trading-service`
```yaml
- name: ENCRYPTION_KEY
  valueFrom:
    secretKeyRef:
      name: live-trading-service-secrets
      key: encryption-key
```

## Deploying from IaC

### Deploy Current (paper-trading-k8s)
```bash
# Apply secrets first
kubectl apply -f k8s/secrets/live-trading-encryption.yaml

# Apply deployment
kubectl apply -f k8s/paper-trading-k8s.yaml

# Check status
kubectl get deployment paper-trading-k8s -n trading-system
kubectl rollout status deployment/paper-trading-k8s -n trading-system
```

### Deploy Production (live-trading-service)
```bash
# Apply secrets first
kubectl apply -f k8s/live-trading-service.yaml

# Check status
kubectl get deployment live-trading-service -n trading-system
kubectl rollout status deployment/live-trading-service -n trading-system
```

## Migration Path

If you want to migrate from paper-trading to production:

1. **Test the production config** in your environment
2. **Update the encryption key** in the production secret
3. **Deploy the live-trading-service**
4. **Migrate port-forwards** from paper-trading-k8s to live-trading-service
5. **Scale down paper-trading-k8s** once validated

## Summary

✅ **Current Setup (Working)**:
- `paper-trading-k8s` is running
- Encryption key properly configured
- IaC files created and documented

📝 **Available Options**:
- Keep using `paper-trading-k8s` for development
- Use `live-trading-service` template for production deployment
- Both have proper encryption key configuration

🔐 **Security**:
- Encryption keys stored in Kubernetes secrets
- Secrets properly documented
- Ready for production use

## Next Steps

1. ✅ Continue using `paper-trading-k8s` for development
2. 📋 When ready for production, deploy `live-trading-service`
3. 🔄 Both configurations are now properly versioned in IaC
4. 📊 Monitor and adjust resources as needed

---

**Note**: The `live-trading-service.yaml` file was restored from git. It was accidentally emptied but has been recovered with proper encryption configuration added.

