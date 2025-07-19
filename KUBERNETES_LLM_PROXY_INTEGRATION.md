# 🚀 Kubernetes LLM Proxy Integration Guide

## Overview

This guide explains how to integrate your external LLM proxy system with the Kubernetes-based trading platform. The integration allows the trading system to use your LLM proxy instead of the internal Ollama service.

## 🏗️ Architecture

### Current Setup
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trading       │    │   LLM Service   │    │   Ollama        │
│   Platform      │───▶│   (K8s)         │───▶│   (K8s)         │
│   (K8s)         │    │   :8008         │    │   :11434        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### New Setup with LLM Proxy
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trading       │    │   LLM Service   │    │   LLM Proxy     │
│   Platform      │───▶│   (K8s)         │───▶│   (External)    │
│   (K8s)         │    │   :8008         │    │   :8081         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration Changes

### 1. Kubernetes Service Configuration

**File**: `k8s/llm-proxy-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-proxy
  namespace: trading-system
spec:
  type: ExternalName
  externalName: host.docker.internal
  ports:
  - port: 8081
    targetPort: 8081
    protocol: TCP
```

### 2. LLM Service Configuration Update

**File**: `k8s/llm-service.yaml`
```yaml
data:
  LLM_SERVICE_CONFIG: |
    {
      "base_url": "http://llm-proxy:8081",
      "api_key": "",
      "timeout": 30,
      "max_retries": 3,
      "rate_limit_requests": 100,
      "rate_limit_window": 60,
      "cache_ttl": 300,
      "health_check_interval": 60
    }
```

### 3. Application Configuration Update

**File**: `src/utils/trading_config.py`
```python
LLM_SERVICE_CONFIG = {
    'base_url': os.getenv('LLM_BASE_URL', 'http://llm-proxy:8081'),
    # ... other config
}
```

## 🚀 Deployment Steps

### Step 1: Deploy the Integration

```bash
# Make the deployment script executable
chmod +x deploy_llm_proxy_integration.sh

# Run the deployment
./deploy_llm_proxy_integration.sh
```

### Step 2: Verify the Deployment

```bash
# Check if the proxy service is accessible from within the cluster
kubectl run test-proxy --image=curlimages/curl --rm -it --restart=Never \
  -- curl -f http://llm-proxy:8081/

# Check LLM service pods
kubectl get pods -n trading-system -l app=llm-service

# Check LLM service logs
kubectl logs -f deployment/llm-service -n trading-system
```

### Step 3: Test the Integration

```bash
# Run the Kubernetes integration test
python test_kubernetes_llm_integration.py
```

## 🔍 Testing the Integration

### Local Testing
```bash
# Test proxy connectivity
python test_llm_proxy_integration.py

# Test Kubernetes integration
python test_kubernetes_llm_integration.py
```

### Kubernetes Testing
```bash
# Port-forward to LLM service
kubectl port-forward service/llm-service 8008:8008 -n trading-system

# Test health endpoint
curl http://localhost:8008/health

# Test LLM operations
curl -X POST http://localhost:8008/api/v1/llm \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "sentiment",
    "data": {"text": "Test message"},
    "model": "gpt-3.5-turbo"
  }'
```

## 📊 Monitoring

### Health Checks
```bash
# Check LLM service health
kubectl get pods -n trading-system -l app=llm-service

# Check service endpoints
kubectl get endpoints llm-proxy -n trading-system

# Check service logs
kubectl logs -f deployment/llm-service -n trading-system
```

### Metrics
```bash
# Get LLM service metrics
kubectl port-forward service/llm-service 8008:8008 -n trading-system
curl http://localhost:8008/metrics

# Get request history
curl http://localhost:8008/history?limit=10
```

## 🔄 Rollback Procedure

If you need to revert to the original Ollama setup:

### Step 1: Update Configuration
```bash
# Update LLM service config to use Ollama
kubectl patch configmap llm-service-config -n trading-system \
  --patch '{"data":{"LLM_SERVICE_CONFIG":"{\"base_url\":\"http://ollama:11434\",...}"}}'
```

### Step 2: Restart Services
```bash
# Restart LLM service
kubectl rollout restart deployment/llm-service -n trading-system

# Restart LLM workers
kubectl rollout restart deployment/llm-worker -n trading-system
```

### Step 3: Verify Rollback
```bash
# Check service health
kubectl logs -f deployment/llm-service -n trading-system

# Test with Ollama
kubectl port-forward service/ollama 11434:11434 -n trading-system
curl http://localhost:11434/api/tags
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Proxy Not Accessible
```bash
# Check if proxy is running locally
curl http://localhost:8081/

# Check Kubernetes service
kubectl get service llm-proxy -n trading-system

# Test from within cluster
kubectl run test-proxy --image=curlimages/curl --rm -it --restart=Never \
  -- curl -v http://llm-proxy:8081/
```

#### 2. LLM Service Not Starting
```bash
# Check pod status
kubectl get pods -n trading-system -l app=llm-service

# Check pod logs
kubectl logs deployment/llm-service -n trading-system

# Check events
kubectl describe pod -l app=llm-service -n trading-system
```

#### 3. Connection Timeouts
```bash
# Check network connectivity
kubectl run netcat --image=busybox --rm -it --restart=Never \
  -- nc -zv llm-proxy 8081

# Check DNS resolution
kubectl run nslookup --image=busybox --rm -it --restart=Never \
  -- nslookup llm-proxy
```

### Debug Commands

```bash
# Get detailed service information
kubectl describe service llm-proxy -n trading-system

# Check endpoints
kubectl get endpoints -n trading-system

# Check configmaps
kubectl get configmap llm-service-config -n trading-system -o yaml

# Check secrets
kubectl get secrets -n trading-system
```

## 📈 Performance Considerations

### Resource Allocation
- **LLM Service**: 512Mi memory, 250m CPU (requests)
- **LLM Workers**: 512Mi memory, 250m CPU (requests)
- **Proxy**: External service (no K8s resources)

### Scaling
```bash
# Scale LLM service
kubectl scale deployment llm-service --replicas=3 -n trading-system

# Scale LLM workers
kubectl scale deployment llm-worker --replicas=5 -n trading-system
```

### Monitoring
```bash
# Monitor resource usage
kubectl top pods -n trading-system

# Monitor service metrics
kubectl port-forward service/llm-service 8008:8008 -n trading-system
curl http://localhost:8008/metrics
```

## 🔐 Security Considerations

### Network Security
- Proxy service is external to cluster
- Use HTTPS for production proxy endpoints
- Consider VPN or private network for proxy access

### Authentication
- Configure API keys for proxy access
- Use service accounts for internal communication
- Implement proper RBAC for service access

## 📝 Configuration Reference

### Environment Variables
```bash
# LLM Service Configuration
LLM_BASE_URL=http://llm-proxy:8081
LLM_API_KEY=your_api_key
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
LLM_RATE_LIMIT=100
LLM_RATE_LIMIT_WINDOW=60
LLM_CACHE_TTL=300
LLM_HEALTH_CHECK_INTERVAL=60
```

### Service Configuration
```yaml
# LLM Service ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-service-config
  namespace: trading-system
data:
  LLM_SERVICE_CONFIG: |
    {
      "base_url": "http://llm-proxy:8081",
      "api_key": "",
      "timeout": 30,
      "max_retries": 3,
      "rate_limit_requests": 100,
      "rate_limit_window": 60,
      "cache_ttl": 300,
      "health_check_interval": 60
    }
```

## 🎯 Next Steps

1. **Deploy the integration** using the provided script
2. **Test the integration** with the test scripts
3. **Monitor performance** and adjust resources as needed
4. **Configure callbacks** for your specific use cases
5. **Set up monitoring** and alerting for the integration

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the service logs: `kubectl logs -f deployment/llm-service -n trading-system`
3. Test connectivity: `kubectl run test-proxy --image=curlimages/curl --rm -it --restart=Never -- curl -v http://llm-proxy:8081/`
4. Verify configuration: `kubectl get configmap llm-service-config -n trading-system -o yaml` 