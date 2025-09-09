# 🚀 Trading System Deployment Guide

## 🏴‍☠️ Quick Start (Pirate Mode)

Ahoy matey! Here's how to get this ship sailing:

### **1. Check Registry Status**
```bash
# Check if registry is running
curl -s http://localhost:32000/v2/_catalog

# If not running, start it
kubectl port-forward -n default service/registry 32000:5000 &
```

### **2. Build and Deploy Core Services**
```bash
# Build essential services
make build-core

# Deploy to Kubernetes
make deploy-core

# Start port forwarding
make port-start
```

### **3. Check System Health**
```bash
# Check overall status
make simple-status

# Check port forwarding
make port-status

# Check specific services
make port-check
```

## 📋 Service Categories

### **Core Services (Must Have)**
- `kubernetes-rag-chat-rs` - RAG pipeline
- `unified-analytics-dashboard` - Main dashboard
- `market-data-service` - Market data API
- `ai-analysis-service` - AI analysis

### **Infrastructure Services**
- `timescaledb` - Database (external)
- `redis` - Cache (external)
- `rabbitmq` - Message queue (external)

### **Optional Services**
- `grafana` - Monitoring (deprecated)
- `prometheus` - Metrics collection
- `background-vectorization-service` - Data processing

## 🔧 Troubleshooting

### **Registry Issues**
```bash
# Check registry status
kubectl get pods -n default | grep registry

# Restart registry if needed
kubectl rollout restart deployment/registry -n default
```

### **Image Pull Issues**
```bash
# Check for missing images
kubectl get pods -n trading-system | grep -E "(ErrImageNeverPull|ImagePullBackOff)"

# Rebuild and push images
make build-all
make push-all
```

### **Port Forwarding Issues**
```bash
# Check active port forwards
make port-status

# Restart port forwarding
make port-stop
make port-start
```

## 📊 Current Status

- **Registry**: ✅ Running on port 32000
- **Core Services**: 🔄 Need to be deployed
- **Port Forwarding**: ❌ Not active
- **Database**: ⚠️ External (deprecated internal)

## 🎯 Next Steps

1. Build and deploy core services
2. Set up port forwarding
3. Verify system health
4. Clean up deprecated services

---

*This guide follows the new rules system and pirate mode protocols! 🏴‍☠️*

