# 🐳 Local Docker Registry Guide

This guide explains how to use the local Docker registry setup at `host.docker.internal:5000` for your trading bot project.

## 📋 Overview

Your local Docker registry allows you to:
- Store and manage Docker images locally
- Speed up deployments by avoiding repeated image pulls
- Maintain consistent image versions across environments
- Share images between different Docker Compose setups and Kubernetes deployments

## 🚀 Quick Start

### 1. Check Registry Status

```bash
# Check if your registry is accessible
make -f Makefile.registry registry-check

# Or use the script directly
./scripts/docker-registry-setup.sh check
```

### 2. Complete Setup

```bash
# Run complete registry setup (build, push, config, update-k8s)
make -f Makefile.registry registry-setup
```

This will:
- Check registry accessibility
- Build all images and tag them for the registry
- Push all images to the registry
- Create configuration files
- Update Kubernetes manifests

### 3. Deploy with Registry Images

```bash
# Deploy to Kubernetes using registry images
make -f Makefile.registry k8s-deploy-registry

# Or use Docker Compose with registry
docker-compose -f docker-compose.yml -f docker-compose.registry.yml up -d
```

## 🛠️ Available Commands

### Registry Management

```bash
# Check registry accessibility
make -f Makefile.registry registry-check

# Build all images for registry
make -f Makefile.registry registry-build

# Push all images to registry
make -f Makefile.registry registry-push

# Build and push all images
make -f Makefile.registry registry-build-push

# List images in registry
make -f Makefile.registry registry-list

# Clean local images (keep registry images)
make -f Makefile.registry registry-clean
```

### Individual Service Operations

```bash
# Build main trading-bot image
make -f Makefile.registry registry-build-main

# Build specific service
make -f Makefile.registry registry-build-service SERVICE=gateway

# Push specific service
make -f Makefile.registry registry-push-service SERVICE=gateway
```

### Kubernetes Integration

```bash
# Deploy to Kubernetes with registry images
make -f Makefile.registry k8s-deploy-registry

# Quick deploy (minimal services)
make -f Makefile.registry k8s-deploy-registry-quick

# Update Kubernetes manifests
make -f Makefile.registry registry-update-k8s
```

## 📁 Configuration Files

### Registry Configuration

The setup creates `docker-registry-config.env` with:

```bash
# Docker Registry Configuration
DOCKER_REGISTRY_HOST=host.docker.internal:5000
DOCKER_REGISTRY_PROJECT=trading-bot
DOCKER_REGISTRY_TAG=latest

# Image URLs
TRADING_BOT_IMAGE=host.docker.internal:5000/trading-bot:latest
TRADING_SERVICE_IMAGE=host.docker.internal:5000/trading-bot-trading-service:latest
MARKET_DATA_IMAGE=host.docker.internal:5000/trading-bot-market-data:latest
# ... and more
```

### Docker Compose Override

Use `docker-compose.registry.yml` to override image references:

```bash
# Use registry images with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.registry.yml up -d

# Build and use registry images
docker-compose -f docker-compose.yml -f docker-compose.registry.yml up -d --build
```

## 🔄 Development Workflow

### 1. Development Cycle

```bash
# 1. Make code changes
# 2. Build and push to registry
make -f Makefile.registry registry-build-push

# 3. Deploy with new images
make -f Makefile.registry k8s-deploy-registry

# 4. Test and iterate
```

### 2. Service-Specific Development

```bash
# Work on a specific service
make -f Makefile.registry registry-build-service SERVICE=gateway
make -f Makefile.registry registry-push-service SERVICE=gateway

# Deploy just that service
kubectl rollout restart deployment/gateway -n trading-system
```

### 3. Complete Development Workflow

```bash
# Run complete workflow
make -f Makefile.registry dev-registry-workflow
```

## 🐛 Troubleshooting

### Registry Not Accessible

```bash
# Check if registry is running
curl http://host.docker.internal:5000/v2/

# If not accessible, ensure your registry is running:
docker run -d -p 5000:5000 --name registry registry:2
```

### Image Push Failures

```bash
# Check Docker daemon configuration
# Ensure insecure registry is configured in Docker Desktop
# Or add to /etc/docker/daemon.json:
{
  "insecure-registries": ["host.docker.internal:5000"]
}
```

### Kubernetes Image Pull Errors

```bash
# Check if images exist in registry
make -f Makefile.registry registry-list

# Rebuild and push if needed
make -f Makefile.registry registry-build-push
```

## 📊 Registry Management

### View Registry Contents

```bash
# List all repositories
curl http://host.docker.internal:5000/v2/_catalog

# List tags for a repository
curl http://host.docker.internal:5000/v2/trading-bot/tags/list

# Get manifest for specific tag
curl http://host.docker.internal:5000/v2/trading-bot/manifests/latest
```

### Clean Up Registry

```bash
# Remove old images (if registry supports deletion)
# Note: Basic registry doesn't support deletion by default

# Clean local images
make -f Makefile.registry registry-clean
```

## 🔧 Advanced Configuration

### Custom Registry Host

Edit the script or Makefile to change registry host:

```bash
# In scripts/docker-registry-setup.sh
REGISTRY_HOST="your-registry-host:port"

# In Makefile.registry
REGISTRY_HOST := your-registry-host:port
```

### Multiple Tags

```bash
# Build with multiple tags
docker build -t trading-bot:latest -t trading-bot:v1.0.0 .
docker tag trading-bot:latest host.docker.internal:5000/trading-bot:latest
docker tag trading-bot:latest host.docker.internal:5000/trading-bot:v1.0.0
docker push host.docker.internal:5000/trading-bot:latest
docker push host.docker.internal:5000/trading-bot:v1.0.0
```

### Registry Authentication

If your registry requires authentication:

```bash
# Login to registry
docker login host.docker.internal:5000

# Use in scripts
echo "password" | docker login host.docker.internal:5000 -u username --password-stdin
```

## 🎯 Best Practices

1. **Always check registry accessibility** before building/pushing
2. **Use consistent tagging** (latest, version tags)
3. **Clean up local images** after pushing to registry
4. **Update Kubernetes manifests** after registry changes
5. **Test deployments** with registry images before production
6. **Monitor registry storage** to avoid disk space issues

## 📚 Related Documentation

- [Docker Registry Documentation](https://docs.docker.com/registry/)
- [Kubernetes Image Pull Policy](https://kubernetes.io/docs/concepts/containers/images/)
- [Docker Compose Override Files](https://docs.docker.com/compose/extends/)

## 🆘 Getting Help

If you encounter issues:

1. Check registry accessibility: `make -f Makefile.registry registry-check`
2. Verify Docker daemon configuration
3. Check Kubernetes events: `kubectl get events -n trading-system`
4. Review logs: `kubectl logs -n trading-system deployment/backtest-scanner` 