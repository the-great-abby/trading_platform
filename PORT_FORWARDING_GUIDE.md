# 🚀 Port Forwarding Management Guide

## 📋 Overview

The `Makefile.port-forward` provides a comprehensive system for managing all service port forwarding in the trading system. It maps all services to appropriate ports in the 11000-11999 range and provides easy commands for starting, stopping, and monitoring services.

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

### **📊 Dashboard Services (11000-11099)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Central Hub | 11080 | http://localhost:11080/ | Main navigation hub |
| Performance | 11000 | http://localhost:11000/dashboard | Performance analytics |
| Health | 11002 | http://localhost:11002/dashboard | System health monitoring |
| RSS Dashboard | 11003 | http://localhost:11003/ | RSS feed viewer |
| AI Stock | 11086 | http://localhost:11086/ | AI stock analysis |

### **📈 Unified Dashboards (11110-11119)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Unified Analytics | 11115 | http://localhost:11115/ | **Main analytics dashboard with data fetch controls** |
| Unified Trading | 11114 | http://localhost:11114/ | Trading interface |
| Unified News | 11113 | http://localhost:11113/ | News dashboard |

### **💼 Trading Services (11099-11109)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Trading Ultra | 11099 | http://localhost:11099/ | All-in-one trading service |
| Market Data | 11084 | http://localhost:11084/ | Market data service |
| Backtest API | 11101 | http://localhost:11101/ | Backtesting service |

### **📈 Monitoring Services (11190-11199)**
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Grafana | 11102 | http://localhost:11102/ | Monitoring dashboards |
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