# 🚀 Current Port Mapping Guide

## 📊 Active Port Forwards

### **Currently Active Port Forwards**
| Service | External Port | Internal Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Unified Analytics Dashboard | 11141 | 80 | ✅ Active | http://localhost:11141/ |
| AI Analysis Service | 11085 | 11085 | ✅ Active | http://localhost:11085/ |
| LLM Proxy | 11081 | 11081 | ✅ Active | http://localhost:11081/ |
| LLM Service | 11109 | 11109 | ✅ Active | http://localhost:11109/ |
| Market Data Service | 11084 | 11084 | ✅ Active | http://localhost:11084/ |

## 🎯 Service Categories

### **�� Dashboard Services (11000-11099)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Central Hub | 11080 | http://localhost:11080/ | ❌ Not Forwarded | Main navigation hub |
| Performance | 11000 | http://localhost:11000/dashboard | ❌ Not Forwarded | Performance analytics |
| Health | 11002 | http://localhost:11002/dashboard | ❌ Not Forwarded | System health monitoring |
| RSS Dashboard | 11003 | http://localhost:11003/ | ❌ Not Forwarded | RSS feed viewer |
| AI Stock | 11086 | http://localhost:11086/ | ❌ Not Forwarded | AI stock analysis |

### **📈 Unified Dashboards (11110-11119)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Unified Analytics | 11141 | http://localhost:11141/ | ✅ Active | **Main analytics dashboard with enhanced status tracking** |
| Unified Trading | 11114 | http://localhost:11114/ | ❌ Not Forwarded | Trading interface |
| Unified News | 11113 | http://localhost:11113/ | ❌ Not Forwarded | News dashboard |

### **💼 Trading Services (11099-11109)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Trading Ultra | 11099 | http://localhost:11099/ | ❌ Not Forwarded | All-in-one trading service |
| Market Data | 11084 | http://localhost:11084/ | ✅ Active | Market data service |
| Backtest API | 11101 | http://localhost:11101/ | ❌ Not Forwarded | Backtesting service |

### **📈 Monitoring Services (11190-11199)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Grafana | 11102 | http://localhost:11102/ | ❌ Not Forwarded | Monitoring dashboards |
| Prometheus | 11190 | http://localhost:11190/ | ❌ Not Forwarded | Metrics collection |
| Postgres Exporter | 11191 | localhost:11191 | ❌ Not Forwarded | Database metrics |
| RabbitMQ Exporter | 11192 | localhost:11192 | ❌ Not Forwarded | Message queue metrics |
| Node Exporter | 11193 | localhost:11193 | ❌ Not Forwarded | System metrics |

### **🔄 Data Processing Services (11100-11119)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Data Processing | 11095 | localhost:11095 | ❌ Not Forwarded | Data processing pipeline |
| Data Transformation | 11135 | localhost:11135 | ❌ Not Forwarded | Data transformation |
| Data Analysis | 11136 | localhost:11136 | ❌ Not Forwarded | Data analysis service |
| Metrics Test | 11100 | localhost:11100 | ❌ Not Forwarded | Metrics testing |

### **🤖 AI/ML Services (11120-11139)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| Ollama | 11120 | http://localhost:11120/ | ❌ Not Forwarded | LLM service |
| LLM Proxy | 11121 | http://localhost:11121/ | ❌ Not Forwarded | LLM proxy service |
| Analytics Service | 11122 | http://localhost:11122/ | ❌ Not Forwarded | Analytics API |
| Postgres Vector | 11123 | http://localhost:11123/ | ❌ Not Forwarded | Vector storage |
| Report Viewer | 11124 | http://localhost:11124/ | ❌ Not Forwarded | Report viewing |
| Notification | 11125 | localhost:11125 | ❌ Not Forwarded | Notification service |

### **🗄️ Database Services (11140-11149)**
| Service | Port | URL | Status | Description |
|---------|------|-----|--------|-------------|
| TimescaleDB | 11140 | localhost:11140 | ❌ Not Forwarded | Time-series database |
| PostgreSQL | 11141 | localhost:11141 | ❌ Not Forwarded | Legacy database |
| Redis | 11142 | localhost:11142 | ❌ Not Forwarded | Cache database |
| Redis Dev | 11143 | localhost:11143 | ❌ Not Forwarded | Development cache |
| RabbitMQ | 11144 | localhost:11144 | ❌ Not Forwarded | Message queue |

## 🚀 Quick Commands

### **Start Essential Services**
```bash
# Start main dashboard
kubectl port-forward -n trading-system service/unified-analytics-dashboard 11141:80 &

# Start AI services
kubectl port-forward -n trading-system service/ai-analysis-service 11085:11085 &
kubectl port-forward -n trading-system service/llm-proxy 11081:11081 &
kubectl port-forward -n trading-system service/llm-service 11109:11109 &

# Start data services
kubectl port-forward -n trading-system service/market-data-service 11084:11084 &
kubectl port-forward -n trading-system service/data-transformation-pipeline 11135:11135 &
kubectl port-forward -n trading-system service/data-analysis-service 11136:11136 &

# Start monitoring
kubectl port-forward -n trading-system service/grafana 11102:3000 &
kubectl port-forward -n trading-system service/prometheus 11190:9090 &
```

### **Stop All Port Forwards**
```bash
pkill -f "kubectl port-forward"
```

### **Check Active Port Forwards**
```bash
ps aux | grep "kubectl port-forward" | grep -v grep
```

## 📝 Notes

- **✅ Active**: Currently port-forwarded and accessible
- **⏸️ LoadBalancer**: Using LoadBalancer instead of port-forward
- **❌ Not Forwarded**: Available but not currently port-forwarded
- **Port Range**: All external ports use 11000-11999 range to avoid conflicts
- **Last Updated**: 2025-08-05

## 🔄 Update Process

After any port forwarding changes:
1. Update this document with new port mappings
2. Update any relevant configuration files
3. Test the new port forwards
4. Update the PORT_FORWARDING_GUIDE.md if needed

## 🆕 Enhanced Dashboard Features

The **Unified Analytics Dashboard** now includes:

### **Enhanced Central Hub Status:**
- **Worker Queue Status**: Shows active queues, consumers, and pending messages
- **Real-time Activity**: Tracks worker processing, market data, and pipeline activity
- **Data Coverage**: Shows actual symbols and coverage statistics
- **Polygon Status**: Detailed status with data source information

### **Worker Queue Information:**
- **Active Queues**: 8 LLM worker queues (llm.sentiment, llm.signal, etc.)
- **Active Consumers**: 10 total consumers across all queues
- **Pending Messages**: Real-time message count
- **Queue States**: Running status for each queue

### **Recent Activity Tracking:**
- **Worker Activity**: LLM worker processing status
- **Market Data**: Real-time market data service status
- **Processing**: Data transformation pipeline activity
- **Error Reporting**: Detailed error messages and status

---

*This document is automatically updated when port forwarding changes are made.*