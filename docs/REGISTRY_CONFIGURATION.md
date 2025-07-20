# Registry Configuration Guide

## Overview

The trading system uses a local Docker registry for storing container images. This document explains the registry configuration and how to resolve common port mismatch issues.

## Registry Architecture

### Port Configuration
- **Internal Port**: 5000 (used by Kubernetes pods inside the cluster)
- **External Port**: 32000 (NodePort for external access from your local machine)
- **Service Type**: NodePort

### Service Details
```bash
# Registry service configuration
kubectl get svc registry -n default
NAME       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
registry   NodePort   10.96.61.155   <none>        5000:32000/TCP   14d
```

## Common Issues

### Port Mismatch Problem
**Problem**: Docker build/push commands fail because they try to use `localhost:5000` but the registry is accessible on `localhost:32000`.

**Symptoms**:
- `docker push localhost:5000/image:tag` fails with connection refused
- Build commands hang or timeout
- Images not found when deploying to Kubernetes

**Root Cause**: The registry service exposes port 5000 internally but uses NodePort 32000 for external access.

## Solution

### 1. Use Correct Ports
- **For Docker commands** (build/push): Use `localhost:32000`
- **For Kubernetes YAML**: Keep `localhost:5000` (internal cluster access)

### 2. Automated Fix
Run the registry URL fix script:
```bash
make fix-registry-urls
```

This script updates:
- Makefiles with Docker build/push commands
- Registry configuration files
- Build scripts

### 3. Manual Verification
Check registry status:
```bash
make check-registry
```

## Configuration Files

### Centralized Configuration
- `config/registry.env` - Registry configuration variables
- `Makefile.registry` - Registry-specific operations

### Updated Files
The fix script updates these file types:
- `Makefile*` - Build and deployment targets
- `scripts/*.sh` - Build and deployment scripts

## Usage Examples

### Building and Pushing Images
```bash
# Correct way (after fix)
docker build -t localhost:32000/my-service:latest .
docker push localhost:32000/my-service:latest

# Wrong way (before fix)
docker build -t localhost:5000/my-service:latest .
docker push localhost:5000/my-service:latest
```

### Kubernetes Deployment
```yaml
# Correct (internal cluster access)
image: localhost:5000/my-service:latest
```

### Registry Operations
```bash
# Check registry status
make check-registry

# Fix registry URLs
make fix-registry-urls

# Build and push performance dashboard
make dashboard-build
```

## Troubleshooting

### Registry Not Accessible
1. Check if registry service is running:
   ```bash
   kubectl get pods -n default | grep registry
   ```

2. Check registry service:
   ```bash
   kubectl get svc registry -n default
   ```

3. Test external access:
   ```bash
   curl http://localhost:32000/v2/_catalog
   ```

### Build/Push Failures
1. Verify correct port usage:
   ```bash
   grep -r "localhost:32000" Makefile* scripts/*.sh
   ```

2. Check registry catalog:
   ```bash
   curl -s http://localhost:32000/v2/_catalog | jq .
   ```

3. Test simple push:
   ```bash
   docker pull hello-world
   docker tag hello-world localhost:32000/hello-world:latest
   docker push localhost:32000/hello-world:latest
   ```

## Best Practices

1. **Always use the fix script** when setting up a new environment
2. **Keep Kubernetes YAML files unchanged** - they use internal ports
3. **Use centralized configuration** in `config/registry.env`
4. **Verify registry access** before building images
5. **Check registry catalog** to confirm successful pushes

## Related Commands

```bash
# Registry management
make check-registry          # Check registry status
make fix-registry-urls       # Fix registry URLs
make dashboard-build         # Build and push dashboard

# Registry operations (from Makefile.registry)
make -f Makefile.registry registry-status    # Check registry
make -f Makefile.registry registry-logs      # View logs
make -f Makefile.registry registry-clean     # Clean up
``` 