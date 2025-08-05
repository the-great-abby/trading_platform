# 🚀 Current Port Mapping Guide

## 📊 Active Port Forwards

### **Currently Active Port Forwards**
| Service | External Port | Internal Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Unified Analytics Dashboard | 11141 | 80 | ✅ Active | http://localhost:11141/ |
| AI Analysis Service | 11085 | 11085 | ✅ Active | http://localhost:11085/ |
| LLM Proxy | 11081 | 11081 | ✅ Active | http://localhost:11081/ |
| LLM Service | 11109 | 11109 | ✅ Active | http://localhost:11109/ |

## 🎯 Service Categories

### **📊 Dashboard Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Unified Analytics Dashboard | 80 | 11141 | ✅ Active | http://localhost:11141/ |
| Unified Trading Dashboard | 80 | - | ⏸️ LoadBalancer | http://localhost:32193/ |
| Unified News Dashboard | 80 | - | ⏸️ LoadBalancer | http://localhost:31531/ |
| Central Hub Dashboard | 80 | - | ⏸️ LoadBalancer | http://localhost:32250/ |
| AI Stock Dashboard | 80 | - | ❌ Not Forwarded | - |
| Performance Dashboard | 80 | - | ❌ Not Forwarded | - |
| Health Dashboard | 80 | - | ❌ Not Forwarded | - |
| RSS Dashboard | 80 | - | ❌ Not Forwarded | - |
| Data Pipeline Dashboard | 11137 | - | ❌ Not Forwarded | - |

### **🤖 AI/ML Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| AI Analysis Service | 11085 | 11085 | ✅ Active | http://localhost:11085/ |
| LLM Proxy | 11081 | 11081 | ✅ Active | http://localhost:11081/ |
| LLM Service | 11109 | 11109 | ✅ Active | http://localhost:11109/ |
| Ollama | 11434 | - | ❌ Not Forwarded | - |
| Analytics Service | 8006 | - | ❌ Not Forwarded | - |
| Postgres Vector Storage | 80 | - | ❌ Not Forwarded | - |
| Report Viewer Service | 80 | - | ❌ Not Forwarded | - |

### **📈 Data Processing Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Market Data Service | 11084 | - | ❌ Not Forwarded | - |
| Data Processing Service | 11095 | - | ❌ Not Forwarded | - |
| Data Transformation Pipeline | 11135 | - | ❌ Not Forwarded | - |
| Data Analysis Service | 11136 | - | ❌ Not Forwarded | - |
| Metrics Test Service | 11100 | - | ❌ Not Forwarded | - |
| Market Data Worker | 11108 | - | ❌ Not Forwarded | - |

### **💼 Trading Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Trading Ultra Service | 80 | - | ❌ Not Forwarded | - |
| Trading Core Service | 11090 | - | ❌ Not Forwarded | - |
| Trading Dashboard Service | 11129 | - | ❌ Not Forwarded | - |
| Trading Service | 80 | - | ❌ Not Forwarded | - |
| Trading Gateway | 80 | - | ⏸️ LoadBalancer | http://localhost:30430/ |
| Backtest API | 11101 | - | ❌ Not Forwarded | - |
| Backtest Request Service | 80 | - | ❌ Not Forwarded | - |

### **📊 Monitoring Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Grafana | 3000 | - | ❌ Not Forwarded | - |
| Prometheus | 9090 | - | ❌ Not Forwarded | - |
| Postgres Exporter | 9187 | - | ❌ Not Forwarded | - |
| RabbitMQ Exporter | 9419 | - | ❌ Not Forwarded | - |
| Node Exporter | 9100 | - | ❌ Not Forwarded | - |
| Infrastructure Metrics Collector | 11103 | - | ❌ Not Forwarded | - |

### **🗄️ Database Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| TimescaleDB | 5432 | - | ❌ Not Forwarded | - |
| PostgreSQL | 5432 | - | ❌ Not Forwarded | - |
| PostgreSQL Dev | 5432 | - | ❌ Not Forwarded | - |
| PostgreSQL Service | 5432 | - | ❌ Not Forwarded | - |
| Redis | 6379 | - | ❌ Not Forwarded | - |
| Redis Dev | 11304 | - | ❌ Not Forwarded | - |
| Redis Service | 6379 | - | ❌ Not Forwarded | - |
| RabbitMQ | 5672,15672 | - | ❌ Not Forwarded | - |
| RabbitMQ Service | 11302,11303 | - | ❌ Not Forwarded | - |

### **📰 News & RSS Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| RSS Feed Service | 11004 | - | ❌ Not Forwarded | - |

### **🔧 Management Services**
| Service | Internal Port | External Port | Status | URL |
|---------|---------------|---------------|--------|-----|
| Notification Service | 8007 | - | ❌ Not Forwarded | - |
| Order Management Service | 11123 | - | ❌ Not Forwarded | - |
| Order Service | 80 | - | ❌ Not Forwarded | - |
| Portfolio Service | 80 | - | ❌ Not Forwarded | - |
| Risk Management Service | 11124 | - | ❌ Not Forwarded | - |
| Risk Service | 80 | - | ❌ Not Forwarded | - |
| Signal Management Service | 11125 | - | ❌ Not Forwarded | - |
| Strategy Management Service | 11126 | - | ❌ Not Forwarded | - |
| Strategy Performance Monitor | 11127 | - | ❌ Not Forwarded | - |
| Strategy Service | 80 | - | ❌ Not Forwarded | - |
| Compliance Service | 11120 | - | ❌ Not Forwarded | - |
| Public API | 80 | - | ❌ Not Forwarded | - |

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

---

*This document is automatically updated when port forwarding changes are made.* 