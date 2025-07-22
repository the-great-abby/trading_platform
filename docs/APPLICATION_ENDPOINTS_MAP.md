# 📍 Application Endpoints Map

## 🎯 Port Allocation Scheme: 11000-11999

### 📊 **Dashboard Services (11000-11009)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11000** | Performance Dashboard | `http://localhost:11000/dashboard` | Trading performance analytics and metrics | ✅ Active |
| **11001** | Trading Dashboard | `http://localhost:11001/` | Main trading interface and portfolio view | ✅ Active |
| **11002** | Health Dashboard | `http://localhost:11002/dashboard` | System health monitoring and status | ✅ Active |
| **11003** | RSS Dashboard | `http://localhost:11003/` | RSS feed viewer and management | ✅ Active |
| **11004** | RSS Feed Service | `http://localhost:11004/` | RSS feed generation and API | ✅ Active |

### 🔧 **API Services (11010-11029)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11010** | Strategy Service | `http://localhost:11010/` | Trading strategy management | 🔄 Pending |
| **11011** | Market Data Service | `http://localhost:11011/` | Real-time market data | 🔄 Pending |
| **11012** | Backtest API | `http://localhost:11012/` | Backtesting engine API | 🔄 Pending |
| **11013** | Portfolio Service | `http://localhost:11013/` | Portfolio management | 🔄 Pending |
| **11014** | Order Service | `http://localhost:11014/` | Order execution and management | 🔄 Pending |
| **11015** | Risk Service | `http://localhost:11015/` | Risk management and monitoring | 🔄 Pending |
| **11016** | Notification Service | `http://localhost:11016/` | Alert and notification system | 🔄 Pending |
| **11017** | User Service | `http://localhost:11017/` | User management and authentication | 🔄 Pending |
| **11018** | Query API | `http://localhost:11018/` | Data querying and reporting | 🔄 Pending |
| **11019** | Public API | `http://localhost:11019/` | Public-facing API endpoints | 🔄 Pending |

### 📈 **Trading Services (11030-11049)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11031** | Backtest Request Service | `http://localhost:11031/` | Backtest job submission | ✅ Active |
| **11032** | Trading Service | `http://localhost:11032/` | Core trading engine | 🔄 Pending |
| **11033** | Market Data Worker | Internal | Market data ingestion | ✅ Active |
| **11034** | News Worker | Internal | News data processing | 🔄 Pending |
| **11035** | Signal Worker | Internal | Trading signal generation | 🔄 Pending |
| **11036** | End-of-Day Worker | Internal | Daily analysis and reports | 🔄 Pending |

### 🔍 **Analytics Services (11050-11069)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11050** | Analytics Service | `http://localhost:11050/` | Data analytics and insights | 🔄 Pending |
| **11051** | Report Viewer Service | `http://localhost:11051/` | Report generation and viewing | 🔄 Pending |
| **11052** | Performance Analytics | `http://localhost:11052/` | Performance analysis tools | 🔄 Pending |

### 🌐 **Gateway & Infrastructure (11070-11089)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11070** | API Gateway | `http://localhost:11070/` | Main API gateway and routing | 🔄 Pending |
| **11071** | Load Balancer | `http://localhost:11071/` | Load balancing and traffic management | 🔄 Pending |

### 🔧 **Development & Monitoring (11090-11099)**

| Port | Service | URL | Purpose | Status |
|------|---------|-----|---------|--------|
| **11090** | Development Dashboard | `http://localhost:11090/` | Development tools and debugging | 🔄 Pending |
| **11091** | Monitoring Dashboard | `http://localhost:11091/` | System monitoring and metrics | 🔄 Pending |

---

## 🔗 **Service Dependencies & Communication**

### **Internal Service Communication**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RSS Feed      │───▶│  Strategy       │───▶│  Market Data    │
│   Service       │    │  Service        │    │  Service        │
│   (11004)       │    │  (11010)        │    │  (11011)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Backtest      │    │   Portfolio     │    │   Order         │
│   API (11012)   │    │   Service       │    │   Service       │
│                 │    │   (11013)       │    │   (11014)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **External API Dependencies**
- **Polygon API**: Market data provider
- **RabbitMQ**: Message queue (internal)
- **PostgreSQL**: Database (internal)
- **Redis**: Caching (internal)

---

## 📋 **Health Check Endpoints**

| Service | Health Endpoint | Status |
|---------|-----------------|--------|
| Performance Dashboard | `http://localhost:11000/health` | ✅ |
| Trading Dashboard | `http://localhost:11001/health` | ✅ |
| Health Dashboard | `http://localhost:11002/health` | ✅ |
| RSS Dashboard | `http://localhost:11003/health` | ✅ |
| RSS Feed Service | `http://localhost:11004/health` | ✅ |
| Backtest Request | `http://localhost:11031/health` | ✅ |

---

## 🚀 **Quick Access Commands**

### **Start All Port Forwarding**
```bash
./scripts/robust-port-forward.sh start
```

### **Check Service Status**
```bash
./scripts/robust-port-forward.sh status
```

### **Stop All Port Forwarding**
```bash
./scripts/robust-port-forward.sh stop
```

### **Individual Service Port Forward**
```bash
# RSS Feed Service
kubectl port-forward -n trading-system svc/rss-feed-service 11004:80

# Performance Dashboard
kubectl port-forward -n trading-system svc/performance-dashboard 11000:80

# Trading Dashboard
kubectl port-forward -n trading-system svc/trading-dashboard-service 11001:8000
```

---

## 📝 **Notes**

- **Port Range**: All application ports are in 11000-11999 range
- **Internal Services**: Some services (workers) don't need external ports
- **Status Legend**: 
  - ✅ Active: Currently deployed and accessible
  - 🔄 Pending: Configured but not yet deployed
  - ❌ Inactive: Not yet configured

---

## 🔄 **Last Updated**
- **Date**: 2025-07-22
- **Version**: 1.0
- **Updated By**: Orion (AI Assistant) 