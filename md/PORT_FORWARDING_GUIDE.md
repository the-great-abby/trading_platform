# 🚀 Port Forwarding Management Guide

## 📋 Overview

The `Makefile.port-forward` provides a comprehensive system for managing all service port forwarding in the trading system. It maps all services to appropriate ports in the 11000-11999 range and provides easy commands for starting, stopping, and monitoring services.

## 🏴‍☠️ **PORT MIGRATION COMPLETE**

### **✅ Updated Services (Proper Project Port Range)**
- **Trading Engine**: Port 11080 (was 8080)
- **Prometheus**: Port 11190 (was 9090)  
- **Grafana**: Port 11044 (already correct)

### **🎯 Why We Migrated**
- **Project Standard**: All services now use 11000-11999 port range
- **Avoid Conflicts**: No more conflicts with default ports (8080, 9090)
- **Consistency**: Follows project-wide port allocation standards
- **Scalability**: Room for future services in proper ranges

## 🎯 Quick Start

### **Start All Services**
```bash
make -f Makefile.port-forward start-all
```

### **Start Specific Categories**
```bash
# Start only dashboard services
make -f Makefile.port-forward start-dashboards

# Start only monitoring services  
make -f Makefile.port-forward start-monitoring

# Start only data processing services
make -f Makefile.port-forward start-data-services

# Start only trading services
make -f Makefile.port-forward start-trading-services

# Start only AI/ML services
make -f Makefile.port-forward start-ai-services
```

### **Start Individual Services**
```bash
# Start specific dashboards
make -f Makefile.port-forward start-unified-analytics
make -f Makefile.port-forward start-unified-trading
make -f Makefile.port-forward start-central-hub

# Start monitoring
make -f Makefile.port-forward start-grafana
make -f Makefile.port-forward start-prometheus

# Start databases
make -f Makefile.port-forward start-timescaledb
make -f Makefile.port-forward start-redis
```

## 📊 Service Port Mapping

### **🎯 Core Unified Dashboard Services (Primary)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Unified Analytics Dashboard** | 11115 | http://localhost:11115/ | **Main analytics dashboard with AI analysis, data pipeline, central hub** |
| **Unified Trading Dashboard** | 11114 | http://localhost:11114/ | **Trading interface with performance and health monitoring** |
| **Unified News Dashboard** | 11113 | http://localhost:11113/ | **RSS feeds and news aggregation** |

### **📊 Supporting Dashboard Services (11000-11099)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Central Hub | 11080 | http://localhost:11080/ | Main navigation hub |
| Performance | 11000 | http://localhost:11000/dashboard | Performance analytics |
| Health | 11002 | http://localhost:11002/dashboard | System health monitoring |
| RSS Dashboard | 11003 | http://localhost:11003/ | RSS feed viewer |
| AI Stock | 11086 | http://localhost:11086/ | AI stock analysis |

### **💼 Trading Services (11099-11109)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Trading Ultra | 11099 | http://localhost:11099/ | All-in-one trading service |
| Market Data | 11084 | http://localhost:11084/ | Market data service |
| Backtest API | 11101 | http://localhost:11101/ | Backtesting service |

### **📈 Monitoring Services (11190-11199)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Grafana | 11044 | http://localhost:11044/ | Monitoring dashboards |
| Prometheus | 11190 | http://localhost:11190/ | Metrics collection |
| Postgres Exporter | 11191 | localhost:11191 | Database metrics |
| RabbitMQ Exporter | 11192 | localhost:11192 | Message queue metrics |
| Node Exporter | 11193 | localhost:11193 | System metrics |

### **🔄 Data Processing Services (11100-11119)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Data Processing | 11095 | localhost:11095 | Data processing pipeline |
| Data Transformation | 11135 | localhost:11135 | Data transformation |
| Data Analysis | 11136 | localhost:11136 | Data analysis service |
| Metrics Test | 11100 | localhost:11100 | Metrics testing |

### **🤖 AI/ML Services (11120-11139)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Ollama | 11120 | http://localhost:11120/ | LLM service |
| LLM Proxy | 11121 | http://localhost:11121/ | LLM proxy service |
| Analytics Service | 11122 | http://localhost:11122/ | Analytics API |
| Postgres Vector | 11123 | http://localhost:11123/ | Vector storage |
| Report Viewer | 11124 | http://localhost:11124/ | Report viewing |
| Notification | 11125 | localhost:11125 | Notification service |

### **🗄️ Database Services (11140-11149)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| TimescaleDB | 11140 | localhost:11140 | Time-series database |
| PostgreSQL | 11141 | localhost:11141 | Legacy database |
| Redis | 11142 | localhost:11142 | Cache database |
| Redis Dev | 11143 | localhost:11143 | Development cache |
| RabbitMQ | 11144 | localhost:11144 | Message queue |

## 🔧 Management Commands

### **View All Available Commands**
```bash
make -f Makefile.port-forward help
```

### **Check Service Status**
```bash
# View all active port forwards
make -f Makefile.port-forward status

# Health check all services
make -f Makefile.port-forward check-all
```

### **Stop All Services**
```bash
make -f Makefile.port-forward stop-all
```

### **View All Service URLs**
```bash
make -f Makefile.port-forward urls
```

## 📋 Unified Dashboard Services List

### **🎯 Complete Service Inventory for Unified Dashboard System**

The following services should come up as part of the unified dashboard system (excluding Ollama as underlying infrastructure):

#### **📊 Core Unified Dashboard Services (Primary)**
| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| **Unified Analytics Dashboard** | 11115 | AI analysis, data pipeline, central hub | LLM Proxy, Market Data, Backtest API |
| **Unified Trading Dashboard** | 11114 | Trading interface, performance, health | Backtest API, Redis, Database |
| **Unified News Dashboard** | 11113 | RSS feeds, news aggregation | RSS Feed Service, Strategy Service |

#### **🤖 AI/ML Services (Required for Unified Dashboards)**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **LLM Proxy** | 11121 | API wrapper for LLM services | ✅ **INCLUDED** |
| **LLM Service** | 11109 | Enhanced LLM with caching/rate limiting | ✅ **INCLUDED** |
| **AI Stock Dashboard** | 11086 | Standalone AI analysis interface | ✅ **INCLUDED** |
| **Analytics Service** | 11122 | Data analytics and processing | ✅ **INCLUDED** |

#### **📊 Supporting Data Services**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Market Data Service** | 11084 | Real-time market data | ✅ **INCLUDED** |
| **Backtest API** | 11101 | Strategy backtesting | ✅ **INCLUDED** |
| **Data Pipeline** | 11135 | Data transformation pipeline | ✅ **INCLUDED** |
| **Data Processing Service** | 11095 | Data processing and analysis | ✅ **INCLUDED** |

#### **💼 Trading Services**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Trading Ultra Service** | 11099 | Advanced trading operations | ✅ **INCLUDED** |
| **Strategy Service** | 11103 | Trading strategy management | ✅ **INCLUDED** |
| **Order Service** | 11105 | Order management | ✅ **INCLUDED** |
| **Portfolio Service** | 11106 | Portfolio management | ✅ **INCLUDED** |

#### **📰 News & RSS Services**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **RSS Feed Service** | 11004 | RSS feed aggregation | ✅ **INCLUDED** |
| **RSS Dashboard** | 11003 | RSS feed display | ✅ **INCLUDED** |

#### **📈 Monitoring & Infrastructure Services**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Grafana** | 11102 | Monitoring dashboards | ✅ **INCLUDED** |
| **Prometheus** | 11190 | Metrics collection | ✅ **INCLUDED** |
| **Node Exporter** | 11193 | System metrics collection | ✅ **INCLUDED** |
| **Performance Dashboard** | 11000 | Performance metrics | ✅ **INCLUDED** |
| **Health Dashboard** | 11002 | System health monitoring | ✅ **INCLUDED** |

#### **🗄️ Database & Infrastructure Services**
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **TimescaleDB** | 11140 | Time-series database | ✅ **INCLUDED** |
| **PostgreSQL** | 11141 | Relational database | ✅ **INCLUDED** |
| **Redis** | 11142 | Caching and session storage | ✅ **INCLUDED** |
| **RabbitMQ** | 11144 | Message queuing | ✅ **INCLUDED** |

#### **🚫 Excluded Services**
| Service | Reason for Exclusion |
|---------|---------------------|
| **Ollama LLM** | ❌ **EXCLUDED** - Underlying infrastructure, not part of unified dashboard |

**Total Services: 26 services** (including Node Exporter, excluding Ollama)

### **📊 Service Dependencies Map**
```
Unified Analytics Dashboard
├── LLM Proxy (11121)
├── Market Data Service (11084)
├── Backtest API (11101)
└── Data Pipeline (11135)

Unified Trading Dashboard
├── Backtest API (11101)
├── Redis (11142)
└── TimescaleDB (11140)

Unified News Dashboard
├── RSS Feed Service (11004)
└── Strategy Service (11103)

Monitoring Stack
├── Grafana (11044)
├── Prometheus (11190)
└── Node Exporter (11193)

Trading Engine Stack
├── Trading Engine (11080)
├── Strategy Service (11103)
├── Market Data Service (11084)
├── TimescaleDB (11140)
└── Redis (11142)
```

## 🚀 Quick Start for Unified Dashboard System

### **Start All Unified Dashboard Services**
```bash
# Start all services needed for unified dashboard system
make -f Makefile.port-forward start-all
```

### **Start Core Unified Dashboards Only**
```bash
# Start the three main unified dashboards
make -f Makefile.port-forward start-unified-dashboards
```

**Or start individually:**
```bash
make -f Makefile.port-forward start-unified-analytics
make -f Makefile.port-forward start-unified-trading  
make -f Makefile.port-forward start-unified-news
```

### **Start by Category**
```bash
# Start AI/ML services (includes LLM Proxy)
make -f Makefile.port-forward start-ai-services

# Start supporting data services
make -f Makefile.port-forward start-data-services

# Start trading services
make -f Makefile.port-forward start-trading-services

# Start monitoring services (includes Node Exporter)
make -f Makefile.port-forward start-monitoring
```

### **Check Unified Dashboard Health**
```bash
# Health check all services
make -f Makefile.port-forward check-all

# Check specific unified dashboard
curl http://localhost:11115/health  # Unified Analytics
curl http://localhost:11114/health  # Unified Trading
curl http://localhost:11113/health  # Unified News

# Check critical services (updated ports)
curl http://localhost:11080/health  # Trading Engine
curl http://localhost:11190/-/healthy # Prometheus
curl http://localhost:11044/api/health # Grafana
```

## 🏴‍☠️ **CRITICAL SERVICES FOR APPLICATION TO RUN**

### **⚓ Essential Services (Application WILL NOT WORK without these)**
| Priority | Service | Port | Status | Purpose | MacBook Air Resource |
|----------|---------|------|--------|---------|---------------------|
| **CRITICAL** | **TimescaleDB** | 11140 | ✅ RUNNING | Primary database | High (512Mi/500m) |
| **CRITICAL** | **Redis** | 11142 | ✅ RUNNING | Cache & sessions | Medium (256Mi/200m) |
| **CRITICAL** | **RabbitMQ** | 11144 | ✅ RUNNING | Message queue | Medium (256Mi/200m) |
| **CRITICAL** | **Prometheus** | 11190 | ✅ RUNNING | Metrics collection | Medium (256Mi/200m) |
| **CRITICAL** | **Grafana** | 11044 | ✅ RUNNING | Monitoring dashboards | Medium (256Mi/200m) |
| **CRITICAL** | **Trading Engine** | 11080 | ✅ RUNNING | Core trading logic | Low (128Mi/100m) |
| **CRITICAL** | **Strategy Service** | 11103 | ✅ RUNNING | Strategy management | Low (128Mi/100m) |
| **CRITICAL** | **Market Data Service** | 11084 | ✅ RUNNING | Market data feeds | Low (128Mi/100m) |

### **⚡ Important Services (Reduced functionality without these)**
| Priority | Service | Port | Status | Purpose | MacBook Air Resource |
|----------|---------|------|--------|---------|---------------------|
| **HIGH** | **Unified Analytics Dashboard** | 11114 | ✅ RUNNING | Main analytics interface | Low (128Mi/100m) |
| **HIGH** | **Unified News Dashboard** | 11113 | ✅ RUNNING | News and RSS feeds | Low (128Mi/100m) |
| **HIGH** | **LLM Proxy** | 11121 | ✅ RUNNING | AI/LLM services | Low (128Mi/100m) |
| **MEDIUM** | **Backtest API** | 11101 | ✅ RUNNING | Strategy backtesting | Low (128Mi/100m) |
| **MEDIUM** | **Data Analysis Service** | 11136 | ✅ RUNNING | Data processing | Low (128Mi/100m) |

### **🔧 Optional Services (Nice to have)**
| Priority | Service | Port | Status | Purpose | MacBook Air Resource |
|----------|---------|------|--------|---------|---------------------|
| **LOW** | **Unified Trading Dashboard** | 11115 | ❌ SCALED DOWN | Trading interface (broken) | - |
| **LOW** | **RSS Feed Service** | 11004 | ✅ RUNNING | RSS processing | Low (64Mi/50m) |
| **LOW** | **LLM Worker** | - | ✅ RUNNING | Background AI tasks | Low (128Mi/100m) |

## 🎯 **MINIMAL SYSTEM SETUP**

### **⚡ Essential Port Forwards for Basic Operation**
```bash
# Start critical services only
kubectl port-forward service/timescaledb 11140:5432 -n trading-system &
kubectl port-forward service/redis 11142:6379 -n trading-system &
kubectl port-forward service/rabbitmq 11144:5672 -n trading-system &
kubectl port-forward service/prometheus 11190:11190 -n trading-system &
kubectl port-forward service/grafana 11044:3000 -n trading-system &
kubectl port-forward service/trading-engine 11080:11080 -n trading-system &
kubectl port-forward service/strategy-service 11103:80 -n trading-system &
kubectl port-forward service/market-data-service 11084:80 -n trading-system &
```

### **📊 URLs for Minimal System**
- **Grafana Monitoring**: http://localhost:11044/
- **Prometheus Metrics**: http://localhost:11190/
- **Trading Engine**: http://localhost:11080/
- **Strategy Service**: http://localhost:11103/
- **Market Data**: http://localhost:11084/

### **🔍 Health Check Commands**
```bash
# Check critical services
curl -s http://localhost:11080/health    # Trading Engine
curl -s http://localhost:11190/-/healthy # Prometheus
curl -s http://localhost:11044/api/health # Grafana
curl -s http://localhost:11103/health    # Strategy Service
curl -s http://localhost:11084/health    # Market Data
```
| **LOW** | **Vector Storage** | 11123 | ✅ RUNNING | AI embeddings | Low (128Mi/100m) |

### **🗑️ Deprecated Services (Should be removed)**
| Service | Status | Reason | Action |
|---------|--------|--------|--------|
| **postgres-dev** | ❌ SCALED DOWN | Replaced by TimescaleDB | Remove completely |

### **📊 Resource Summary for MacBook Air**
- **Total Critical Services**: 8 services
- **Total Important Services**: 5 services  
- **Total Optional Services**: 4 services
- **Estimated CPU**: ~2000m (2 cores)
- **Estimated Memory**: ~3Gi
- **Recommendation**: Keep 13-17 services running maximum

### **🚨 Service Health Check Commands**
```bash
# Check critical services health
curl -s http://localhost:11044/api/health  # Grafana
curl -s http://localhost:11114/health      # Analytics Dashboard
curl -s http://localhost:11113/health      # News Dashboard

# Check if critical pods are running
kubectl get pods -n trading-system | grep -E "(timescaledb|redis|rabbitmq|prometheus|grafana|trading-engine|strategy-service|market-data)"
```

### **⚓ Minimum Service Set for Basic Operation**
```bash
# Start only the absolute minimum (5 services)
kubectl port-forward service/timescaledb 11140:5432 -n trading-system &
kubectl port-forward service/redis 11142:6379 -n trading-system &
kubectl port-forward service/rabbitmq 11144:5672 -n trading-system &
kubectl port-forward service/prometheus 11190:9090 -n trading-system &
kubectl port-forward service/grafana 11044:3000 -n trading-system &
```

## 🎯 Key Services for Different Use Cases

### **For Data Fetching & Analytics**
```bash
# Start the main analytics dashboard with data fetch controls
make -f Makefile.port-forward start-unified-analytics

# Start market data service for data fetching
make -f Makefile.port-forward start-market-data

# Start TimescaleDB for data storage
make -f Makefile.port-forward start-timescaledb
```

### **For Trading**
```bash
# Start trading ultra service (all-in-one)
make -f Makefile.port-forward start-trading-ultra

# Start unified trading dashboard
make -f Makefile.port-forward start-unified-trading

# Start backtest API
make -f Makefile.port-forward start-backtest
```

### **For Monitoring**
```bash
# Start Grafana for dashboards
make -f Makefile.port-forward start-grafana

# Start Prometheus for metrics
make -f Makefile.port-forward start-prometheus

# Start all monitoring services
make -f Makefile.port-forward start-monitoring
```

### **For Development**
```bash
# Start all databases
make -f Makefile.port-forward start-databases

# Start AI/ML services
make -f Makefile.port-forward start-ai-services

# Start data processing services
make -f Makefile.port-forward start-data-services
```

## 🚨 Troubleshooting

### **If a Service Won't Start**
```bash
# Check if the service exists
kubectl get service -n trading-system | grep <service-name>

# Check if the pod is running
kubectl get pods -n trading-system | grep <service-name>

# Check pod logs
kubectl logs -n trading-system <pod-name>
```

### **If Port is Already in Use**
```bash
# Stop all port forwarding
make -f Makefile.port-forward stop-all

# Start specific service again
make -f Makefile.port-forward start-<service-name>
```

### **If Service is Unhealthy**
```bash
# Health check all services
make -f Makefile.port-forward check-all

# Check specific service health
curl http://localhost:<port>/health
```

## 📝 Notes

- **Port Range**: All services use ports in the 11000-11999 range to avoid conflicts
- **Service Mapping**: Each service is mapped to its appropriate internal port
- **Health Checks**: The system includes health check functionality for all services
- **Organized Categories**: Services are organized by type (dashboards, monitoring, data, trading, AI/ML, databases)
- **Easy Management**: Simple commands to start, stop, and monitor all services

## ✅ Benefits

1. **Centralized Management**: All port forwarding managed from one place
2. **Organized Ports**: Clear port mapping in 11000-11999 range
3. **Health Monitoring**: Built-in health checks for all services
4. **Easy Troubleshooting**: Clear commands for diagnosing issues
5. **Flexible Start Options**: Start all, categories, or individual services
6. **Documentation**: Clear mapping of all services and their purposes

This system makes it much easier to manage the complex port-forwarding requirements of the trading system! 🚀 