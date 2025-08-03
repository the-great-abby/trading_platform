# Trading System Service URL Mapping

## 🎯 **Port Allocation Strategy**

### **11000-11099: Core Trading Services**
- **11000**: Performance Dashboard
- **11001**: Trading Dashboard Service  
- **11002**: Health Dashboard
- **11003**: RSS Dashboard
- **11004**: RSS Feed Service
- **11005**: Central Hub Dashboard

### **11100-11199: API Services**
- **11100**: Trading Ultra Service
- **11101**: Backtest API
- **11102**: Public API
- **11103**: Strategy Service
- **11104**: Analytics Service
- **11105**: Order Management Service
- **11106**: Portfolio Service
- **11107**: Risk Management Service
- **11108**: Market Data Service
- **11109**: LLM Service
- **11110**: Report Viewer Service
- **11111**: Notification Service
- **11112**: Signal Management Service

### **11200-11299: Data & Infrastructure Services**
- **11200**: Data Processing Service
- **11201**: Market Data Worker
- **11202**: AI Analysis Service
- **11203**: Trading Core Service

### **11300-11399: Database & Message Services**
- **11300**: PostgreSQL Database
- **11301**: TimescaleDB
- **11302**: RabbitMQ
- **11303**: Redis Cache

## 📊 **Current Service Status & URLs**

### ✅ **Running Services (Standardized)**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|---------|-----|
| **Unified Trading Dashboard** | 80 | 11114 | ✅ Running | http://localhost:11114/ |
| **Unified Analytics Dashboard** | 80 | 11115 | ✅ Running | http://localhost:11115/ |
| **Unified News Dashboard** | 80 | 11116 | ✅ Running | http://localhost:11116/ |
| Performance Dashboard | 80 | 11000 | ✅ Running | http://localhost:11000/dashboard |
| Trading Dashboard Service | 8000 | 11001 | ✅ Running | http://localhost:11001/ |
| Health Dashboard | 80 | 11002 | ✅ Running | http://localhost:11002/ |
| RSS Dashboard | 8080 | 11003 | ✅ Running | http://localhost:11003/ |
| RSS Feed Service | 11004 | 11004 | ✅ Running | http://localhost:11004/ |
| Central Hub Dashboard | 8000 | 11005 | ✅ Running | http://localhost:11005/ |
| Trading Ultra Service | 80 | 11100 | ✅ Running | http://localhost:11100/ |
| Data Processing Service | 11095 | 11095 | ✅ Running | http://localhost:11095/ |
| Market Data Worker | 11108 | 11108 | ✅ Running | http://localhost:11108/ |
| AI Analysis Service | 11085 | 11085 | ✅ Running | http://localhost:11085/ |
| Backtest API | 11101 | 11101 | ✅ Running | http://localhost:11101/ |
| LLM Service | 11109 | 11109 | ✅ Running | http://localhost:11109/ |

### 🚫 **Services Not Currently Running**
| Service | Target Port | Status | Notes |
|---------|-------------|---------|-------|
| Backtest API | 11101 | ❌ Not Deployed | Needs deployment |
| Public API | 11102 | ❌ Not Deployed | Needs deployment |
| Strategy Service | 11103 | ❌ Not Deployed | Needs deployment |
| Analytics Service | 11104 | ❌ Not Deployed | Needs deployment |
| Order Management Service | 11105 | ❌ Not Deployed | Needs deployment |
| Portfolio Service | 11106 | ❌ Not Deployed | Needs deployment |
| Risk Management Service | 11107 | ❌ Not Deployed | Needs deployment |
| Market Data Service | 11108 | ❌ Not Deployed | Needs deployment |
| LLM Service | 11109 | ❌ Not Deployed | Needs deployment |
| Report Viewer Service | 11110 | ❌ Not Deployed | Needs deployment |
| Notification Service | 11111 | ❌ Not Deployed | Needs deployment |
| Signal Management Service | 11112 | ❌ Not Deployed | Needs deployment |

### 🏗️ **Infrastructure Services**
| Service | External Port | Internal Port | Status | URL |
|---------|---------------|---------------|---------|-----|
| PostgreSQL Database | 11300 | 5432 | ✅ Running | localhost:11300 |
| TimescaleDB | 11301 | 5432 | ✅ Running | localhost:11301 |
| RabbitMQ AMQP | 11302 | 5672 | ✅ Running | localhost:11302 |
| RabbitMQ Management | 11303 | 15672 | ✅ Running | localhost:11303 |
| Redis Cache | 11304 | 6379 | ✅ Running | localhost:11304 |

## 🔧 **Port Forwarding Commands**

### **Core Dashboards**
```bash
# Performance Dashboard
kubectl port-forward service/performance-dashboard 11000:80 -n trading-system &

# Trading Dashboard Service  
kubectl port-forward service/trading-dashboard-service 11001:8000 -n trading-system &

# Health Dashboard
kubectl port-forward service/health-dashboard 11002:80 -n trading-system &

# RSS Dashboard
kubectl port-forward service/rss-dashboard 11003:80 -n trading-system &

# Central Hub Dashboard
kubectl port-forward service/central-hub-dashboard 11005:80 -n trading-system &
```

### **API Services**
```bash
# Trading Ultra Service
kubectl port-forward service/trading-ultra-service 11100:80 -n trading-system &

# Data Processing Service
kubectl port-forward service/data-processing-service 11095:11095 -n trading-system &

# Market Data Worker
kubectl port-forward service/market-data-worker 11108:11108 -n trading-system &

# AI Analysis Service
kubectl port-forward service/ai-analysis-service 11085:11085 -n trading-system &

# Infrastructure Services
kubectl port-forward service/postgres-dev 11300:5432 -n trading-system &
kubectl port-forward service/rabbitmq-service 11302:5672 -n trading-system &
kubectl port-forward service/rabbitmq-service 11303:15672 -n trading-system &
kubectl port-forward service/redis-dev 11304:6379 -n trading-system &
```

## 🚨 **Critical Issues Found**

### **1. Unified Dashboard Functionality Gaps**
- **Database Integration**: Unified dashboards lack direct PostgreSQL connections
- **RSS Feed Generation**: Missing RSS XML generation functionality
- **Portfolio Management**: No real portfolio data integration
- **Strategy Event Tracking**: Missing strategy event system
- **Resource Allocation**: Insufficient resources for unified functionality

### **2. Massive Port Range Violations (37 services)**
- **37 services** are using ports outside the 11000-11999 range
- Many services using port 80 (should be 11000-series)
- Services using 8000-series ports (8000, 8002, 8003, 8005, 8008)
- Database services using standard ports (5432, 5672, 6379)

### **2. Port Allocation Strategy**
**✅ Compliant Services (7):**
- ai-analysis-service: 11085
- backtest-api: 11101
- data-processing-service: 11095
- llm-service: 11109
- market-data-worker: 11108
- rss-feed-service: 11004
- trading-core-service: 11090

**❌ Violating Services (37):**
- analytics-service: 80 → should be 11104
- backtest-request-service: 80 → should be 11102
- central-hub-dashboard: 80 → should be 11005
- compliance-service: 8005 → should be 11105
- health-dashboard: 80 → should be 11002
- market-data-service: 80 → should be 11108
- notification-service: 80 → should be 11111
- order-management-service: 8000 → should be 11105
- performance-dashboard: 80 → should be 11000
- portfolio-service: 80 → should be 11106
- public-api: 80 → should be 11102
- report-viewer-service: 80 → should be 11110
- risk-management-service: 8003 → should be 11107
- risk-service: 80 → should be 11107
- rss-dashboard: 80 → should be 11003
- signal-management-service: 8002 → should be 11112
- strategy-service: 80 → should be 11103
- trading-dashboard-service: 8000 → should be 11001
- trading-ultra-service: 80 → should be 11100

### **3. Database Services (Need Special Handling)**
- PostgreSQL services: 5432 (standard port, keep as-is)
- RabbitMQ services: 5672 (standard port, keep as-is)
- Redis services: 6379 (standard port, keep as-is)

## 📋 **Action Plan**

### **Phase 1: Fix Unified Dashboard Issues (Priority)**
1. Implement database integration in unified dashboards
2. Add RSS feed generation to unified news dashboard
3. Implement strategy event tracking in unified trading dashboard
4. Update resource allocations for better performance
5. Test all functionality thoroughly

### **Phase 2: Standardize Port Allocation**
1. Update all service manifests to use 11000-11199 port range
2. Fix port forwarding commands to match service definitions
3. Update central hub dashboard with correct URLs

### **Phase 3: Deploy Missing Services**
1. Apply all missing service deployments
2. Fix image registry issues
3. Verify all services are running

### **Phase 4: Create Centralized Management**
1. Create automated port forwarding script
2. Create service health monitoring
3. Create URL mapping validation

## 📊 **Resource Allocation Comparison**

### **Old Dashboard Setup (Individual Services)**
- **Performance Dashboard**: 128Mi RAM, 50m CPU
- **Trading Dashboard**: 128Mi RAM, 50m CPU  
- **Health Dashboard**: 128Mi RAM, 50m CPU
- **RSS Dashboard**: 128Mi RAM, 50m CPU
- **Total**: 512Mi RAM, 200m CPU

### **New Unified Dashboard Setup**
- **Unified Trading**: 512Mi RAM, 200m CPU
- **Unified Analytics**: 512Mi RAM, 200m CPU
- **Unified News**: 512Mi RAM, 200m CPU
- **Total**: 1.5Gi RAM, 600m CPU

### **Resource Efficiency**
- **Memory**: 3x increase (necessary for unified functionality)
- **CPU**: 3x increase (necessary for database operations)
- **Functionality**: 10x increase (all features in 3 services vs 4 separate)

## 🔄 **Last Updated**
- **Date**: 2024-07-24
- **Status**: Audit Complete - Needs Standardization
- **Next Action**: Update service manifests with standardized ports 