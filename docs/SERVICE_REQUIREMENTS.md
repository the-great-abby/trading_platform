# 🏴‍☠️ Trading System Service Requirements

## 📋 Overview

This document outlines all services required for the trading system to function properly, their current status, dependencies, and resource requirements.

## 🎯 **CRITICAL SERVICES (System WILL NOT WORK without these)**

### **⚓ Core Infrastructure Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **TimescaleDB** | ✅ RUNNING | 11140 | Primary database | 512Mi/500m | `kubectl get pod -l app=timescaledb` |
| **Redis** | ✅ RUNNING | 11142 | Cache & sessions | 256Mi/200m | `kubectl get pod -l app=redis` |
| **RabbitMQ** | ✅ RUNNING | 11144 | Message queue | 256Mi/200m | `kubectl get pod -l app=rabbitmq` |

### **📊 Monitoring & Observability**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Prometheus** | ✅ RUNNING | 11190 | Metrics collection | 256Mi/200m | `curl http://localhost:11190/-/healthy` |
| **Grafana** | ✅ RUNNING | 11044 | Monitoring dashboards | 256Mi/200m | `curl http://localhost:11044/api/health` |
| **Infrastructure Metrics Collector** | ✅ RUNNING | - | System metrics | 128Mi/100m | `kubectl get pod -l app=infrastructure-metrics-collector` |

### **💼 Core Trading Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Trading Engine** | ✅ RUNNING | 11080 | Core trading logic | 128Mi/100m | `curl http://localhost:11080/health` |
| **Strategy Service** | ✅ RUNNING | 11103 | Strategy management | 128Mi/100m | `curl http://localhost:11103/health` |
| **Market Data Service** | ✅ RUNNING | 11084 | Market data feeds | 128Mi/100m | `curl http://localhost:11084/health` |

## ⚡ **IMPORTANT SERVICES (Reduced functionality without these)**

### **🤖 AI/ML Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **LLM Proxy** | ✅ RUNNING | 11121 | AI/LLM services | 128Mi/100m | `curl http://localhost:11121/health` |
| **LLM Worker** | ✅ RUNNING | - | Background AI tasks | 128Mi/100m | `kubectl get pod -l app=llm-worker` |
| **LLM Service** | ❌ CRASHLOOP | - | LLM processing | 128Mi/100m | `kubectl get pod -l app=llm-service` |

### **📈 Analytics & Data Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Unified Analytics Dashboard** | ✅ RUNNING | 11114 | Main analytics interface | 128Mi/100m | `curl http://localhost:11114/health` |
| **Unified News Dashboard** | ✅ RUNNING | 11113 | News and RSS feeds | 128Mi/100m | `curl http://localhost:11113/health` |
| **Data Analysis Service** | ✅ RUNNING | 11136 | Data processing | 128Mi/100m | `curl http://localhost:11136/health` |
| **Data Transformation Pipeline** | ✅ RUNNING | - | Data transformation | 128Mi/100m | `kubectl get pod -l app=data-transformation-pipeline` |

### **🔄 Backtesting Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Backtest API** | ✅ RUNNING | 11101 | Strategy backtesting | 128Mi/100m | `curl http://localhost:11101/health` |
| **Backtest Request Service** | ✅ RUNNING | - | Backtest requests | 128Mi/100m | `kubectl get pod -l app=backtest-request-service` |

### **📰 News & RSS Services**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **RSS Feed Service** | ✅ RUNNING | 11004 | RSS processing | 64Mi/50m | `curl http://localhost:11004/health` |

## 🔧 **OPTIONAL SERVICES (Nice to have)**

### **📊 Additional Dashboards**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Unified Trading Dashboard** | ✅ RUNNING | 11115 | Trading interface | 128Mi/100m | `curl http://localhost:11115/health` |
| **Trading Monitor** | ✅ RUNNING | - | Trading monitoring | 128Mi/100m | `kubectl get pod -l app=trading-monitor` |

### **📈 Market Data Workers**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Market Data Worker** | ✅ RUNNING (3 replicas) | - | Market data processing | 128Mi/100m | `kubectl get pod -l app=market-data-worker` |

### **🧠 Vector Storage**
| Service | Status | Port | Purpose | Resource | Health Check |
|---------|--------|------|---------|----------|--------------|
| **Postgres Vector Storage** | ✅ RUNNING | - | AI embeddings | 128Mi/100m | `kubectl get pod -l app=postgres-vector-storage` |

## ❌ **PROBLEMATIC SERVICES (Need attention)**

### **🚨 Services with Issues**
| Service | Status | Issue | Action Required |
|---------|--------|-------|----------------|
| **LLM Service** | ❌ CRASHLOOP | Service crashing | Investigate logs, fix deployment |
| **Market Data Service** | ⚠️ IMAGEPULLBACKOFF | Image pull issues | Check image registry, fix deployment |

## 🎯 **MINIMAL SYSTEM SETUP**

### **⚡ Essential Services for Basic Operation**
```bash
# Core Infrastructure (CRITICAL)
kubectl get pod -l app=timescaledb
kubectl get pod -l app=redis  
kubectl get pod -l app=rabbitmq

# Monitoring (CRITICAL)
kubectl get pod -l app=prometheus
kubectl get pod -l app=grafana

# Trading Core (CRITICAL)
kubectl get pod -l app=trading-engine
kubectl get pod -l app=strategy-service
kubectl get pod -l app=market-data-service
```

### **📊 Health Check Commands**
```bash
# Critical Services
curl -s http://localhost:11080/health    # Trading Engine
curl -s http://localhost:11190/-/healthy # Prometheus
curl -s http://localhost:11044/api/health # Grafana
curl -s http://localhost:11103/health    # Strategy Service
curl -s http://localhost:11084/health    # Market Data

# Important Services
curl -s http://localhost:11114/health    # Unified Analytics
curl -s http://localhost:11113/health    # Unified News
curl -s http://localhost:11121/health    # LLM Proxy
curl -s http://localhost:11101/health    # Backtest API
```

### **🔍 Quick Status Check**
```bash
# Check all critical services
kubectl get pods -n trading-system | grep -E "(timescaledb|redis|rabbitmq|prometheus|grafana|trading-engine|strategy-service|market-data-service)"

# Check service health
for service in trading-engine strategy-service market-data-service; do
  echo "Checking $service..."
  kubectl get pod -l app=$service -n trading-system
done
```

## 📈 **RESOURCE USAGE**

### **MacBook Air Resource Allocation**
- **Critical Services**: ~2.5 CPU cores, ~2GB RAM
- **Important Services**: ~1 CPU core, ~1GB RAM  
- **Optional Services**: ~1 CPU core, ~1GB RAM
- **Total Estimated**: ~4.5 CPU cores, ~4GB RAM

### **Resource Optimization**
- All services use conservative resource limits for MacBook Air
- 1 replica per service (except market-data-worker: 3 replicas)
- Services scaled down when not needed

## 🚀 **DEPLOYMENT PRIORITIES**

### **Phase 1: Critical Infrastructure**
1. TimescaleDB, Redis, RabbitMQ
2. Prometheus, Grafana
3. Trading Engine, Strategy Service, Market Data Service

### **Phase 2: Important Services**
1. LLM Proxy, Data Analysis Service
2. Unified Dashboards
3. Backtest API

### **Phase 3: Optional Services**
1. Additional dashboards
2. Market data workers
3. Vector storage

## 🔧 **TROUBLESHOOTING**

### **Common Issues**
- **Port Forward Issues**: Restart port forwards when services restart
- **Resource Constraints**: Scale down optional services on MacBook Air
- **Image Pull Issues**: Check Docker registry connectivity
- **CrashLoopBackOff**: Check logs with `kubectl logs <pod-name>`

### **Recovery Commands**
```bash
# Restart problematic services
kubectl rollout restart deployment/<service-name> -n trading-system

# Scale down to free resources
kubectl scale deployment/<service-name> --replicas=0 -n trading-system

# Check logs
kubectl logs deployment/<service-name> -n trading-system
```

---

**Last Updated**: 2025-08-07  
**Status**: ✅ All critical services running  
**Issues**: LLM Service in CrashLoopBackOff, Market Data Service has ImagePullBackOff





