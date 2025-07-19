# 🚀 Kubernetes Stock Recommendations Guide

## Overview

This guide covers deploying and using the Stock Recommendations API in Kubernetes. The system provides comprehensive buy/sell signals with exit strategies, combining multiple analysis approaches in a containerized environment.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kubernetes    │    │  Strategy       │    │  External       │
│   Cluster       │    │  Service        │    │  Services       │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Ingress     │ │    │ │ Multi-      │ │    │ │ Ollama      │ │
│ │ Controller  │ │    │ │ Strategy    │ │    │ │ AI Service  │ │
│ │             │ │    │ │ Analysis    │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Strategy    │ │    │ │ AI-Powered  │ │    │ │ News        │ │
│ │ Service     │ │    │ │ Analysis    │ │    │ │ Scanner     │ │
│ │ Pods        │ │    │ │             │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Database    │ │    │ │ Risk        │ │    │ │ Market      │ │
│ │ (PostgreSQL)│ │    │ │ Assessment  │ │    │ │ Data        │ │
│ │             │ │    │ │             │ │    │ │ Service     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Deployment

### 1. Deploy Strategy Service

```bash
# Deploy using the deployment script
./deploy-strategy-service.sh

# Or deploy using Makefile
make k8s-deploy-strategy-service
```

### 2. Verify Deployment

```bash
# Check pod status
kubectl get pods -n trading-system -l app=strategy-service

# Check service
kubectl get svc -n trading-system strategy-service

# Check ingress
kubectl get ingress -n trading-system | grep strategy
```

### 3. Port Forward for Local Access

```bash
# Port forward the service
kubectl port-forward svc/strategy-service 8000:80 -n trading-system
```

## 📊 API Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **Kubernetes**: `http://strategy-service:80` (internal)
- **Ingress**: `http://trading.example.com/api/v1/strategies`

### Available Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Get Available Strategies
```bash
curl http://localhost:8000/strategies
```

#### 3. Get Stock Recommendation
```bash
curl -X POST http://localhost:8000/recommendations/stock \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "include_ai_analysis": true,
    "include_news_sentiment": true,
    "include_risk_assessment": true,
    "strategies": ["rsi_strategy", "macd_strategy", "bollinger_bands"]
  }'
```

## 🛠️ Usage Examples

### 1. Basic Recommendation

```bash
# Get recommendation for AAPL
python stock_recommendation_cli.py AAPL

# Get recommendation with specific strategies
python stock_recommendation_cli.py GOOGL --strategies rsi_strategy,macd_strategy

# Get JSON output
python stock_recommendation_cli.py MSFT --format json
```

### 2. Risk-Only Analysis

```bash
# Get risk assessment only
python stock_recommendation_cli.py TSLA --risk-only

# Get summary format
python stock_recommendation_cli.py AAPL --risk-only --format summary
```

### 3. Without AI Analysis

```bash
# Exclude AI analysis
python stock_recommendation_cli.py GOOGL --no-ai

# Exclude news sentiment
python stock_recommendation_cli.py MSFT --no-news
```

### 4. Run Demo

```bash
# Run comprehensive demo
python demo_stock_recommendations.py
```

## 🔧 Kubernetes Operations

### Deployment Commands

```bash
# Deploy strategy service
make k8s-deploy-strategy-service

# Deploy all services
make k8s-deploy

# Check deployment status
make k8s-status-strategy
```

### Port Forwarding

```bash
# Port forward strategy service
make k8s-port-forward-strategy

# Port forward backtest API
make k8s-port-forward-backtest
```

### Monitoring

```bash
# View logs
kubectl logs -n trading-system deployment/strategy-service -f

# Check pod status
kubectl get pods -n trading-system -l app=strategy-service

# Check service endpoints
kubectl get endpoints -n trading-system strategy-service
```

### Troubleshooting

```bash
# Check pod events
kubectl describe pod -n trading-system -l app=strategy-service

# Check service events
kubectl describe svc -n trading-system strategy-service

# Check ingress events
kubectl describe ingress -n trading-system strategy-service-ingress
```

## 📈 Integration Examples

### 1. Python Integration

```python
import asyncio
import httpx

async def get_stock_recommendation(symbol: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/recommendations/stock",
            json={"symbol": symbol}
        )
        return response.json()

# Usage
recommendation = await get_stock_recommendation("AAPL")
print(f"Recommendation: {recommendation['overall_recommendation']}")
```

### 2. Batch Processing

```python
async def batch_recommendations(symbols: list):
    tasks = []
    for symbol in symbols:
        task = get_stock_recommendation(symbol)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
recommendations = await batch_recommendations(symbols)
```

### 3. Real-time Monitoring

```python
async def monitor_stock(symbol: str, interval: int = 300):
    while True:
        try:
            recommendation = await get_stock_recommendation(symbol)
            if recommendation['overall_recommendation'] != "HOLD":
                print(f"🚨 Signal for {symbol}: {recommendation['overall_recommendation']}")
            
            await asyncio.sleep(interval)
        except Exception as e:
            print(f"Error monitoring {symbol}: {e}")
            await asyncio.sleep(60)

# Usage
await monitor_stock("AAPL")
```

## 🔍 Debugging

### 1. Check Service Health

```bash
# Health check
curl http://localhost:8000/health

# Service status
kubectl get svc -n trading-system strategy-service
```

### 2. Check Logs

```bash
# View logs
kubectl logs -n trading-system deployment/strategy-service

# Follow logs
kubectl logs -n trading-system deployment/strategy-service -f

# View logs with timestamps
kubectl logs -n trading-system deployment/strategy-service --timestamps
```

### 3. Check Resource Usage

```bash
# Check pod resource usage
kubectl top pods -n trading-system -l app=strategy-service

# Check node resource usage
kubectl top nodes
```

### 4. Common Issues

#### Service Not Available
```bash
# Check if service is running
kubectl get pods -n trading-system -l app=strategy-service

# Check service endpoints
kubectl get endpoints -n trading-system strategy-service

# Check service events
kubectl describe svc -n trading-system strategy-service
```

#### Image Pull Issues
```bash
# Check image pull status
kubectl describe pod -n trading-system -l app=strategy-service

# Check if image exists in registry
docker images | grep strategy-service
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec -n trading-system deployment/strategy-service -- curl -f http://localhost:8000/health

# Check database pod
kubectl get pods -n trading-system -l app=postgres
```

## 📊 Performance Monitoring

### 1. Resource Monitoring

```bash
# Monitor CPU and memory usage
kubectl top pods -n trading-system -l app=strategy-service

# Monitor resource limits
kubectl describe pod -n trading-system -l app=strategy-service | grep -A 5 "Limits:"
```

### 2. API Performance

```bash
# Test API response time
time curl -X POST http://localhost:8000/recommendations/stock \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# Load test
for i in {1..10}; do
  curl -X POST http://localhost:8000/recommendations/stock \
    -H "Content-Type: application/json" \
    -d '{"symbol": "AAPL"}' &
done
wait
```

### 3. Scaling

```bash
# Scale up the service
kubectl scale deployment strategy-service -n trading-system --replicas=3

# Scale down the service
kubectl scale deployment strategy-service -n trading-system --replicas=1

# Check scaling status
kubectl get pods -n trading-system -l app=strategy-service
```

## 🔧 Configuration

### Environment Variables

The strategy service supports these environment variables:

```yaml
env:
- name: DATABASE_URL
  value: "postgresql://trading_user:trading_pass@postgres:5432/trading_bot"
- name: REDIS_URL
  value: "redis://redis:6379"
- name: OLLAMA_URL
  value: "http://host.docker.internal:11434"
- name: LOG_LEVEL
  value: "INFO"
- name: ENVIRONMENT
  value: "production"
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

## 🚀 Advanced Features

### 1. Auto-scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: strategy-service-hpa
  namespace: trading-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: strategy-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: strategy-service-network-policy
  namespace: trading-system
spec:
  podSelector:
    matchLabels:
      app: strategy-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: trading-system
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: trading-system
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: trading-system
    ports:
    - protocol: TCP
      port: 6379
```

### 3. Secrets Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: strategy-service-secrets
  namespace: trading-system
type: Opaque
data:
  database-url: cG9zdGdyZXNxbDovL3RyYWRpbmdfdXNlcjp0cmFkaW5nX3Bhc3NAcG9zdGdyZXM6NTQzMi90cmFkaW5nX2JvdA==
  redis-url: cmVkaXM6Ly9yZWRpczo2Mzc5
  ollama-url: aHR0cDovL2hvc3QuZG9ja2VyLmludGVybmFsOjExNDM0
```

## 📚 Additional Resources

- [Stock Recommendations Guide](docs/STOCK_RECOMMENDATIONS_GUIDE.md)
- [Kubernetes First Guide](docs/KUBERNETES_FIRST_GUIDE.md)
- [Docker Guide](docs/CONTAINER_FIRST_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)

## 🎯 Quick Reference

### Common Commands

```bash
# Deploy
make k8s-deploy-strategy-service

# Port forward
make k8s-port-forward-strategy

# Check status
make k8s-status-strategy

# View logs
kubectl logs -n trading-system deployment/strategy-service -f

# Test API
curl -X POST http://localhost:8000/recommendations/stock \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# Use CLI
python stock_recommendation_cli.py AAPL

# Run demo
python demo_stock_recommendations.py
```

### Troubleshooting Commands

```bash
# Check pod status
kubectl get pods -n trading-system -l app=strategy-service

# Check service
kubectl get svc -n trading-system strategy-service

# Check ingress
kubectl get ingress -n trading-system | grep strategy

# Check events
kubectl get events -n trading-system --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n trading-system deployment/strategy-service --tail=50
```

---

**🎉 Ready to deploy?** Run `./deploy-strategy-service.sh` to get started! 