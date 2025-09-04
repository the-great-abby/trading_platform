# 🚀 Trading System Deployment Map

## 📊 Deployment Status Overview

**Last Updated**: 2025-09-03 20:15:00 EEST  
**Total Deployments**: 50+  
**Active Deployments**: 6  
**Deprecated Deployments**: 8  
**Failed Deployments**: 0  

## 🎯 Deployment Categories

### **✅ ACTIVE DEPLOYMENTS (Production Ready)**
| Service | Deployment File | Status | Description |
|---------|----------------|--------|-------------|
| kubernetes-rag-chat-rs | `k8s/kubernetes-rag-chat-rs.yaml` | ✅ Running | RAG pipeline service |
| node-exporter | `k8s/node-exporter.yaml` | ✅ Running | System metrics collection |
| unified-analytics-dashboard | `k8s/unified-analytics-dashboard.yaml` | ✅ Running | Analytics dashboard service |
| unified-trading-dashboard | `k8s/unified-trading-dashboard.yaml` | ✅ Running | Trading dashboard service (includes performance metrics) |
| unified-news-dashboard | `k8s/unified-news-dashboard.yaml` | ✅ Running | News dashboard service (port 11116) |
| ai-analysis-service | `k8s/ai-analysis-service.yaml` | ✅ Running | AI analysis service |
| market-data-service | `k8s/market-data-service.yaml` | ✅ Running | Market data service |
| news-scanning-cronjob | `k8s/news-scanning-cronjob.yaml` | ✅ Running | News scanning cronjob |

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

### **📋 AVAILABLE BUT NOT DEPLOYED**
| Service | Deployment File | Status | Priority |
|---------|----------------|--------|----------|
| market-data-service | `k8s/market-data-service.yaml` | ❌ Not Deployed | High |
| background-vectorization-service | `k8s/background-vectorization-service.yaml` | ❌ Not Deployed | Medium |
| unified-news-dashboard | `k8s/unified-news-dashboard.yaml` | ❌ Not Deployed | Medium |
| backtest-api | `k8s/backtest-api.yaml` | ❌ Not Deployed | Low |

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
