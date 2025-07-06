# Kubernetes-First Development Rules

## ☸️ Kubernetes-First Development
- **PREFER** Kubernetes for development over Docker Compose
- **USE** `kubectl` commands for development workflows
- **USE** `make k8s-*` commands for Kubernetes operations
- **FALLBACK** to Docker Compose only for local testing or when Kubernetes is unavailable

## ✅ Preferred Commands (Kubernetes)

### Python Execution
```bash
# ✅ PREFERRED - Run Python in Kubernetes pod
kubectl exec -it deployment/trading-service -- python src/main.py
kubectl exec -it deployment/market-data-service -- python scripts/fetch_data.py

# ✅ PREFERRED - Run in temporary pod
kubectl run python-test --rm -it --image=python:3.11 -- python test_script.py

# ✅ PREFERRED - Use port-forward for local access
kubectl port-forward deployment/trading-service 8000:8000
```

### Package Management
```bash
# ✅ PREFERRED - Install packages in Kubernetes pod
kubectl exec -it deployment/trading-service -- pip install yfinance
kubectl exec -it deployment/market-data-service -- pip install -r requirements.txt

# ✅ PREFERRED - Update deployment with new dependencies
kubectl rollout restart deployment/trading-service
```

### Testing
```bash
# ✅ PREFERRED - Run tests in Kubernetes
kubectl exec -it deployment/trading-service -- python -m pytest tests/
kubectl exec -it deployment/trading-service -- python -m pytest tests/test_strategies.py -v

# ✅ PREFERRED - Use Makefile k8s commands
make k8s-test
make k8s-logs
```

### Database Operations
```bash
# ✅ PREFERRED - Database access through Kubernetes
kubectl exec -it deployment/postgres -- psql -U trading_user -d trading_bot
kubectl exec -it deployment/trading-service -- alembic upgrade head
```

## 🔄 Fallback Commands (Docker Compose)

### When Kubernetes is Unavailable
```bash
# 🔄 FALLBACK - Docker Compose for local testing
docker-compose exec trading-service python src/main.py
docker-compose run --rm trading-cli python test_script.py
docker-compose exec trading-service pip install yfinance
```

## 🛠️ Development Workflow

### 1. Start Kubernetes Environment
```bash
# Start Kubernetes cluster
make k8s-deploy

# Check pod status
make k8s-pods

# View logs
make k8s-logs
```

### 2. Run Python Scripts
```bash
# Run in specific service
kubectl exec -it deployment/trading-service -- python src/main.py

# Run in temporary pod
kubectl run python-script --rm -it --image=python:3.11 -- python test_script.py

# Use port-forward for local development
kubectl port-forward deployment/trading-service 8000:8000
```

### 3. Install Packages
```bash
# Install in running pod
kubectl exec -it deployment/trading-service -- pip install yfinance

# Update deployment with new image
kubectl rollout restart deployment/trading-service
```

### 4. Run Tests
```bash
# Run all tests
make k8s-test

# Run specific test
kubectl exec -it deployment/trading-service -- python -m pytest tests/test_strategies.py
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

## 🚀 Quick Start with Kubernetes

### 1. Deploy to Kubernetes
```bash
# Deploy all services
make k8s-deploy

# Check deployment status
make k8s-pods
```

### 2. Run Python Scripts
```bash
# Run main application
kubectl exec -it deployment/trading-service -- python src/main.py

# Run tests
kubectl exec -it deployment/trading-service -- python -m pytest tests/
```

### 3. Access Services
```bash
# Port forward for local access
kubectl port-forward deployment/trading-service 8000:8000 -n trading-system

# Access database
kubectl port-forward deployment/postgres 5432:5432 -n trading-system
```

## 🔄 Migration from Docker Compose

### When to Use Docker Compose
- Local development without Kubernetes cluster
- Quick testing and prototyping
- CI/CD pipeline testing
- When Kubernetes is not available

### When to Use Kubernetes
- Production-like development environment
- Testing microservices architecture
- Load testing and scaling
- Integration testing with multiple services

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

## 🚨 Troubleshooting

### Common Issues
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

### Debugging
```bash
# Interactive shell in pod
kubectl exec -it <pod-name> -- /bin/bash

# Copy files to/from pod
kubectl cp <local-file> <pod-name>:/path/ -n trading-system

# View events
kubectl get events -n trading-system
``` 