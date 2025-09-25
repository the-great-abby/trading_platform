# 🚀 Trading System Deployment Map

## 📊 Deployment Status Overview

**Last Updated**: 2025-09-13 06:15:00 EEST  
**Total Deployments**: 50+  
**Active Deployments**: 14  
**Deprecated Deployments**: 8  
**Failed Deployments**: 2  

## 🎯 Deployment Categories

### **✅ ACTIVE DEPLOYMENTS (Production Ready)**
| Service | Deployment File | Status | Version | Description |
|---------|----------------|--------|---------|-------------|
| ai-analysis-service | `k8s/ai-analysis-service.yaml` | ✅ Running | 0.1.0-ci.22 | AI analysis service |
| backtest-api | `k8s/backtest-api.yaml` | ✅ Running | 0.1.0-ci.22 | Backtest API service |
| cqrs-api | `k8s/cqrs-api.yaml` | ✅ Running | latest | CQRS API service |
| data-analysis-service | `k8s/data-analysis-service.yaml` | ✅ Running | latest | Data analysis service |
| data-transformation-pipeline | `k8s/data-transformation-pipeline.yaml` | ✅ Running | latest | Data transformation pipeline |
| kubernetes-rag-chat | `k8s/kubernetes-rag-chat.yaml` | ✅ Running | latest | RAG pipeline service |
| market-data-service | `k8s/market-data-service.yaml` | ✅ Running | latest | Market data service |
| mcp-service | `k8s/mcp-service.yaml` | ✅ Running | 0.1.0-ci.22 | MCP service with documentation |
| node-exporter | `k8s/node-exporter.yaml` | ✅ Running | latest | System metrics collection |
| playwright-server | `k8s/playwright-server.yaml` | ✅ Running | latest | Playwright server |
| postgres-vector-storage | `k8s/postgres-vector-storage.yaml` | ✅ Running | latest | Vector storage database |
| strategy-service | `k8s/strategy-service.yaml` | ✅ Running | 0.1.0-ci.22 | Strategy service (fixed readiness probe) |
| unified-analytics-dashboard | `k8s/unified-analytics-dashboard.yaml` | ✅ Running | 0.1.0-ci.22 | Analytics dashboard service |
| unified-news-dashboard | `k8s/unified-news-dashboard.yaml` | ✅ Running | 0.1.0-ci.22 | News dashboard service |
| unified-trading-dashboard | `k8s/unified-trading-dashboard.yaml` | ✅ Running | 0.1.0-ci.22 | Trading dashboard service |

### **⚠️ DEPRECATED DEPLOYMENTS (Moved to k8s/deprecated/)**
| Service | Deployment File | Status | Reason |
|---------|----------------|--------|--------|
| ai-analysis-service-simple | `k8s/deprecated/ai-analysis-service-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| analytics-service-simple | `k8s/deprecated/analytics-service-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| order-service-simple | `k8s/deprecated/order-service-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| risk-service-simple | `k8s/deprecated/risk-service-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| trading-service-simple | `k8s/deprecated/trading-service-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| trading-engine-simple | `k8s/deprecated/trading-engine-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| backtest-fast-simple | `k8s/deprecated/backtest-fast-simple.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| backtest-fast-simple-fixed | `k8s/deprecated/backtest-fast-simple-fixed.yaml` | ⚠️ Deprecated | Replaced by standard deployment |
| performance-dashboard | `k8s/deprecated/performance-dashboard.yaml` | ⚠️ Deprecated | Functionality moved to unified-trading-dashboard |

### **⚠️ MINIMAL DEPLOYMENTS (Should be Deprecated)**
| Service | Deployment File | Status | Recommendation |
|---------|----------------|--------|----------------|
| ai-analysis-service-minimal | `k8s/ai-analysis-service-minimal.yaml` | ⚠️ Should Deprecate | Use standard ai-analysis-service.yaml |
| market-data-service-minimal | `k8s/market-data-service-minimal.yaml` | ⚠️ Should Deprecate | Use standard market-data-service.yaml |

### **🔄 DEPLOYED BUT FAILING**
| Service | Deployment File | Status | Issue | Priority |
|---------|----------------|--------|-------|----------|
| daily-recommendations-worker | `k8s/daily-recommendations-worker.yaml` | 🔄 CrashLoopBackOff | 617 restarts, 4+ days | High |
| news-scanning-cronjob | `k8s/news-scanning-cronjob.yaml` | 🔄 CrashLoopBackOff | 5 restarts, recent | Low |

### **📋 AVAILABLE BUT NOT DEPLOYED**
| Service | Deployment File | Status | Priority |
|---------|----------------|--------|----------|
| background-vectorization-service | `k8s/background-vectorization-service.yaml` | ❌ Not Deployed | Medium |

## 🏗️ Deployment Patterns

### **Standard Pattern (Recommended)**
- **File Naming**: `{service-name}.yaml`
- **Image Tagging**: `localhost:32000/{service-name}:latest`
- **Resource Limits**: Defined with requests and limits
- **Health Checks**: Readiness and liveness probes
- **Status**: ✅ Production Ready

### **Minimal Pattern (Deprecated)**
- **File Naming**: `{service-name}-minimal.yaml`
- **Image Tagging**: `localhost:32000/{service-name}:latest`
- **Resource Limits**: Minimal or none
- **Health Checks**: Basic or none
- **Status**: ⚠️ Should be deprecated

### **Simple Pattern (Deprecated)**
- **File Naming**: `{service-name}-simple.yaml`
- **Image Tagging**: `localhost:32000/{service-name}:latest`
- **Resource Limits**: Basic
- **Health Checks**: Basic
- **Status**: ⚠️ Moved to deprecated/

## 🔧 Image Registry Status

### **Registry Information**
- **Registry URL**: `localhost:32000`
- **Status**: ✅ Running
- **Total Images**: 50+
- **Last Check**: 2025-09-03 20:05:00

### **✅ Available Images (Successfully Built)**
| Service | Image Name | Status | Last Updated |
|---------|------------|--------|--------------|
| unified-analytics-dashboard | `localhost:32000/unified-analytics-dashboard:latest` | ✅ Available | 2025-09-03 20:10 |
| unified-trading-dashboard | `localhost:32000/unified-trading-dashboard:latest` | ✅ Available | 2025-09-03 20:12 |
| ai-analysis-service | `localhost:32000/ai-analysis-service:latest` | ✅ Available | 2025-09-03 20:14 |
| trading-system | `localhost:32000/trading-system:latest` | ✅ Available | Previously built |

## 🚀 Quick Commands

### **Check Deployment Status**
```bash
# Check all deployments
kubectl get deployments -n trading-system

# Check pods with issues
kubectl get pods -n trading-system | grep -E "(ErrImageNeverPull|ImagePullBackOff|CrashLoopBackOff)"

# Check services
kubectl get services -n trading-system
```

### **Rebuild Missing Images**
```bash
# Rebuild specific service
cd services/{service-name}
docker build -t {service-name}:latest .
docker tag {service-name}:latest localhost:32000/{service-name}:latest
docker push localhost:32000/{service-name}:latest

# Or use the build script
./scripts/build-and-deploy.sh
```

### **Deploy Services**
```bash
# Deploy specific service
kubectl apply -f k8s/{service-name}.yaml

# Deploy all core services
kubectl apply -f k8s/unified-analytics-dashboard.yaml
kubectl apply -f k8s/market-data-service.yaml
kubectl apply -f k8s/ai-analysis-service.yaml
```

## 📝 Status Indicators

- **✅ Active**: Currently deployed and running
- **❌ Not Deployed**: Available but not deployed
- **⚠️ Deprecated**: Should not be used
- **🔄 Deployed but Failing**: Deployed but has issues
- **🔧 Maintenance**: Down for maintenance

## 🔄 Update Process

1. **Before making changes**: Check current deployment status
2. **After deployment**: Update this document with new status
3. **After deprecation**: Move files to `k8s/deprecated/`
4. **After image rebuild**: Update missing images section

## 🆕 Recent Changes

- **2025-09-13**: Applied semantic versioning (0.1.0-ci.22) to all services
- **2025-09-13**: Fixed strategy-service readiness probe issue (changed from /ready to /health)
- **2025-09-13**: Successfully deployed with semantic versioning: strategy-service, ai-analysis-service, backtest-api, mcp-service, unified-analytics-dashboard, unified-trading-dashboard, unified-news-dashboard
- **2025-09-13**: Removed unnecessary playwright-mcp service (was crashing) - using remote server at localhost:15000/mcp instead
- **2025-09-13**: Updated DEPLOY_MAP.md with current deployment status and version information
- **2025-09-13**: Identified 2 remaining failing services: daily-recommendations-worker (617 restarts), news-scanning-cronjob (5 restarts)
- **2025-09-03**: Created DEPLOY_MAP.md to track deployment patterns
- **2025-09-03**: Moved 8 "simple" deployments to deprecated/
- **2025-09-03**: Identified 4 services with ErrImageNeverPull errors
- **2025-09-03**: Marked "minimal" deployments for deprecation
- **2025-09-03**: Rebuilt and pushed missing images (unified-analytics-dashboard, unified-trading-dashboard, ai-analysis-service)
- **2025-09-03**: Fixed news-scanning-cronjob by recreating with correct image reference
- **2025-09-03**: All ErrImageNeverPull errors resolved - system now fully operational
- **2025-09-03**: Cleaned up Makefile.services to remove all deprecated -simple and -minimal references
- **2025-09-03**: Updated Makefile.backtest to use backtest-fast-optimized instead of deprecated backtest-fast-simple
- **2025-09-03**: Created clean, organized Makefile structure with no duplicate targets
- **2025-09-03**: Moved all old Makefiles to backup directory for reference
- **2025-09-03**: Resolved Makefile conflicts and created specialized, clean Makefiles
- **2025-09-03**: Eliminated all Makefile target override warnings - system now completely clean
- **2025-09-03**: Scaled market-data-service from 2 to 1 replica for resource optimization
- **2025-09-03**: Updated k8s/market-data-service.yaml to set replicas: 1 for persistent configuration
- **2025-09-03**: Launched dashboard port forwards - unified-analytics-dashboard (11114) and unified-trading-dashboard (11115) now accessible
- **2025-09-03**: Built and deployed unified-news-dashboard - now accessible on port 11117
- **2025-09-03**: Complete dashboard suite now running: Analytics (11114), Trading (11115), News (11117), Performance (11116)
- **2025-09-03**: Fixed performance dashboard port forwarding - now accessible on http://localhost:11116
- **2025-09-03**: DEPRECATED performance-dashboard - functionality moved to unified-trading-dashboard
- **2025-09-03**: Moved performance-dashboard.yaml to k8s/deprecated/ and scaled down service
- **2025-09-03**: Moved unified-news-dashboard from port 11117 to 11116 (freed up by performance dashboard deprecation)

---

*This document follows the deployment management standards and tracks all deployment patterns! 🏴‍☠️*
