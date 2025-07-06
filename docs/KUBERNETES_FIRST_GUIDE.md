# Kubernetes-First Development Guide

## ☸️ Overview

This project now **prefers Kubernetes for development** over Docker Compose. This provides:

- **Production parity** - Same environment as production
- **Microservices architecture** - True service isolation
- **Scaling capabilities** - Easy to scale services up/down
- **Service discovery** - Built-in service discovery
- **Load balancing** - Automatic load balancing
- **Security** - RBAC, network policies, secrets management

## 🚫 Forbidden Commands

**NEVER** run these commands directly on your host system:

```bash
# ❌ DON'T DO THIS
python src/main.py
python3 test_script.py
pip install yfinance
pip3 install -r requirements.txt
```

## ✅ Preferred Commands (Kubernetes)

**ALWAYS** prefer these Kubernetes commands:

```bash
# ✅ PREFERRED - Run Python in Kubernetes
kubectl exec -it deployment/trading-service -- python src/main.py
kubectl exec -it deployment/market-data-service -- python scripts/fetch_data.py

# ✅ PREFERRED - Install packages in Kubernetes
kubectl exec -it deployment/trading-service -- pip install yfinance
kubectl exec -it deployment/market-data-service -- pip install -r requirements.txt

# ✅ PREFERRED - Run tests in Kubernetes
kubectl exec -it deployment/trading-service -- python -m pytest tests/
make k8s-test
```

## 🔄 Fallback Commands (Docker Compose)

**USE** Docker Compose only when Kubernetes is unavailable:

```bash
# 🔄 FALLBACK - Docker Compose for local testing
docker-compose exec trading-service python src/main.py
docker-compose run --rm trading-cli python test_script.py
docker-compose exec trading-service pip install yfinance
make test
```

## 🛠️ Quick Start with Kubernetes

### 1. Deploy to Kubernetes

```bash
# Deploy all services
make k8s-deploy

# Check deployment status
make k8s-pods

# View logs
make k8s-logs
```

### 2. Run Python Scripts

```bash
# Run main application
kubectl exec -it deployment/trading-service -- python src/main.py

# Run in temporary pod
kubectl run python-script --rm -it --image=python:3.11 -- python test_script.py

# Use port-forward for local development
kubectl port-forward deployment/trading-service 8000:8000 -n trading-system
```

### 3. Install Packages

```bash
# Install in running pod
kubectl exec -it deployment/trading-service -- pip install yfinance

# Update deployment with new dependencies
kubectl rollout restart deployment/trading-service -n trading-system
```

### 4. Run Tests

```bash
# Run all tests
make k8s-test

# Run specific test
kubectl exec -it deployment/trading-service -- python -m pytest tests/test_strategies.py -v
```

## 📋 Available Kubernetes Services

| Service | Purpose | Command |
|---------|---------|---------|
| `trading-service` | Main trading bot | `kubectl exec -it deployment/trading-service -- python` |
| `market-data-service` | Market data | `kubectl exec -it deployment/market-data-service -- python` |
| `portfolio-service` | Portfolio management | `kubectl exec -it deployment/portfolio-service -- python` |
| `strategy-service` | Trading strategies | `kubectl exec -it deployment/strategy-service -- python` |
| `analytics-service` | Data analysis | `kubectl exec -it deployment/analytics-service -- python` |
| `postgres` | Database | `kubectl exec -it deployment/postgres -- psql` |
| `redis` | Cache | `kubectl exec -it deployment/redis -- redis-cli` |

## 🔧 Common Kubernetes Commands

### Pod Management

```bash
# List pods
kubectl get pods -n trading-system

# Describe pod
kubectl describe pod <pod-name> -n trading-system

# Delete pod (will be recreated by deployment)
kubectl delete pod <pod-name> -n trading-system

# Scale deployment
kubectl scale deployment trading-service --replicas=3 -n trading-system
```

### Logging and Monitoring

```bash
# View logs
kubectl logs -f deployment/trading-service -n trading-system

# View logs for specific pod
kubectl logs -f <pod-name> -n trading-system

# Access Grafana
kubectl port-forward deployment/grafana 3000:3000 -n trading-system
```

### Configuration

```bash
# Apply configuration
kubectl apply -f k8s/ -n trading-system

# Update configuration
kubectl apply -f k8s/configmap.yaml -n trading-system

# View configuration
kubectl get configmap -n trading-system
```

## 🧪 Testing the Cached Market Data System

```bash
# Test in Kubernetes
kubectl exec -it deployment/trading-service -- python test_cached_market_data_container.py

# Test with port-forward for local access
kubectl port-forward deployment/trading-service 8000:8000 -n trading-system
curl http://localhost:8000/health
```

## 📊 Makefile Commands

```bash
# Kubernetes Operations
make k8s-deploy         # Deploy to Kubernetes
make k8s-delete         # Delete Kubernetes deployment
make k8s-pods           # Show pod status
make k8s-logs           # Show logs
make k8s-scale          # Scale deployment
make k8s-test           # Run tests in Kubernetes

# Docker Compose (Fallback)
make docker-up          # Start Docker Compose
make docker-down        # Stop Docker Compose
make test               # Run tests in Docker
```

## 🔒 Security Benefits

### Kubernetes Security
- **RBAC**: Role-based access control
- **Network Policies**: Controlled network access
- **Secrets Management**: Secure secret storage
- **Pod Security**: Isolated pod execution
- **Resource Limits**: Controlled resource usage

### Development Benefits
- **Production Parity**: Same environment as production
- **Scaling**: Easy to scale services up/down
- **Service Discovery**: Built-in service discovery
- **Load Balancing**: Automatic load balancing
- **Health Checks**: Built-in health monitoring

## 🔄 When to Use Each Approach

### Use Kubernetes When:
- Production-like development environment needed
- Testing microservices architecture
- Load testing and scaling
- Integration testing with multiple services
- Testing service discovery and load balancing
- Security testing with RBAC and network policies

### Use Docker Compose When:
- Local development without Kubernetes cluster
- Quick testing and prototyping
- CI/CD pipeline testing
- When Kubernetes is not available
- Simple single-service testing
- Resource-constrained environments

## 🚨 Troubleshooting

### Common Kubernetes Issues

```bash
# Pod not starting
kubectl describe pod <pod-name> -n trading-system
kubectl logs <pod-name> -n trading-system

# Service not accessible
kubectl get services -n trading-system
kubectl describe service <service-name> -n trading-system

# Configuration issues
kubectl get configmap -n trading-system
kubectl get secrets -n trading-system
```

### Debugging Commands

```bash
# Interactive shell in pod
kubectl exec -it <pod-name> -- /bin/bash

# Copy files to/from pod
kubectl cp <local-file> <pod-name>:/path/ -n trading-system

# View events
kubectl get events -n trading-system

# Check resource usage
kubectl top pods -n trading-system
```

### Fallback to Docker Compose

If Kubernetes is not working:

```bash
# Stop Kubernetes
make k8s-delete

# Start Docker Compose
make docker-up

# Run tests
make test

# Run Python scripts
docker-compose exec trading-service python src/main.py
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Container First Guide](CONTAINER_FIRST_GUIDE.md) - Container-first principles
- [Quick Wins Summary](QUICK_WINS_SUMMARY.md) - Performance improvements
- [Architecture Guide](ARCHITECTURE.md) - System architecture overview

---

**Remember**: Prefer Kubernetes for development to maintain production parity, but fall back to Docker Compose when needed for local testing or when Kubernetes is unavailable. 