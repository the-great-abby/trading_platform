# 🚀 Port Mapping Guide - Trading System

## 📊 Current Status

**Last Updated**: 2025-09-07 08:35:00 EEST  
**Active Port Forwards**: 10  
**Total Services**: 50+  

## 🎯 Currently Active Port Forwards

| Service | External Port | Internal Port | Status | URL | Last Checked |
|---------|---------------|---------------|--------|-----|--------------|
| Registry | 32000 | 5000 | ✅ Active | http://localhost:32000/ | 2025-09-03 21:30 |
| Unified Analytics Dashboard | 11114 | 80 | ✅ Active | http://localhost:11114/ | 2025-09-03 21:30 |
| Unified Trading Dashboard | 11115 | 80 | ✅ Active | http://localhost:11115/ | 2025-09-03 21:30 |
| Unified News Dashboard | 11116 | 80 | ✅ Active | http://localhost:11116/ | 2025-09-03 21:30 |
| MCP Service | 11117 | 8000 | ✅ Active | http://localhost:11117/ | 2025-09-04 05:41 |
| PostgreSQL Timescale | 13001 | 5432 | ✅ Active | localhost:13001 | 2025-09-03 21:30 |
| PostgreSQL Age | 13002 | 5432 | ✅ Active | localhost:13002 | 2025-09-03 21:30 |
| PostgreSQL Vector | 13003 | 5432 | ✅ Active | localhost:13003 | 2025-09-03 21:30 |
| PostgreSQL Regular | 13004 | 5432 | ✅ Active | localhost:13004 | 2025-09-03 21:30 |

## 📋 Service Categories & Port Assignments

### **🔧 Core Infrastructure (11000-11099)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| TimescaleDB | 11140 | 5432 | ⚠️ **DEPRECATED** | localhost:11140 | **DEPRECATED** - Moved to external database |
| Redis | 11379 | 6379 | ⚠️ **DEPRECATED** | localhost:11379 | **DEPRECATED** - Moved to external Redis service |
| RabbitMQ | 11144 | 5672 | ❌ Not Forwarded | localhost:11144 | internal message queue |
| PostgreSQL Vector | 11180 | 5432 | ⚠️ **DEPRECATED** | localhost:11180 | **DEPRECATED** - Moved to external vector storage |

### **📊 Unified Dashboards (11110-11119)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Unified Analytics | 11114 | 80 | ✅ Active | http://localhost:11114/ | Main analytics dashboard |
| Unified Trading | 11115 | 80 | ✅ Active | http://localhost:11115/ | Trading interface (includes performance metrics) |
| Unified News | 11116 | 80 | ✅ Active | http://localhost:11116/ | News dashboard |
| MCP Service | 11117 | 8000 | ✅ Active | http://localhost:11117/ | Model Context Protocol service |
| Performance Dashboard | 11116 | 80 | ⚠️ **DEPRECATED** | http://localhost:11116/ | **DEPRECATED** - Functionality moved to unified-trading-dashboard |

### **💼 Trading Services (11080-11099)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Market Data Service | 11084 | 11084 | ❌ Not Forwarded | http://localhost:11084/ | Market data API |
| Backtest API | 11101 | 10001 | ❌ Not Forwarded | http://localhost:11101/ | Backtesting service |
| Trading Engine | 11080 | 8080 | ❌ Not Forwarded | http://localhost:11080/ | Core trading engine |

### **🤖 AI/ML Services (11120-11139)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| LLM Proxy | 11081 | 11081 | ❌ Not Forwarded | http://localhost:11081/ | LLM proxy service |
| AI Analysis Service | 11085 | 11085 | ❌ Not Forwarded | http://localhost:11085/ | AI analysis API |
| LLM Service | 11109 | 11109 | ❌ Not Forwarded | http://localhost:11109/ | LLM service |

### **📈 Monitoring Services (11190-11199)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Prometheus | 11190 | 9090 | ❌ Not Forwarded | http://localhost:11190/ | Metrics collection |
| Grafana | 11102 | 3000 | ⚠️ **DEPRECATED** | http://localhost:11102/ |  **DEPRECATED** Monitoring dashboards |
| Postgres Exporter | 11191 | 9187 | ❌ Not Forwarded | localhost:11191 | Database metrics |
| RabbitMQ Exporter | 11192 | 9419 | ❌ Not Forwarded | localhost:11192 | Message queue metrics |
| Node Exporter | 11193 | 9100 | ❌ Not Forwarded | localhost:11193 | System metrics |

### **🔄 Data Processing Services (11100-11119)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| Data Processing | 11095 | 11095 | ❌ Not Forwarded | localhost:11095 | Data processing pipeline |
| Data Transformation | 11135 | 11135 | ❌ Not Forwarded | localhost:11135 | Data transformation |
| Data Analysis | 11136 | 11136 | ❌ Not Forwarded | localhost:11136 | Data analysis service |

### **📰 RSS & News Services (11150-11169)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| RSS Feed Service | 11150 | 11150 | ❌ Not Forwarded | localhost:11150 | RSS feed processing |
| News Scanning | 11151 | 11151 | ❌ Not Forwarded | localhost:11151 | News scanning service |

### **🔑 Authentication & Security (11170-11179)**
| Service | External Port | Internal Port | Status | URL | Description |
|---------|---------------|---------------|--------|-----|-------------|
| VAPID Service | 11170 | 11170 | ❌ Not Forwarded | localhost:11170 | VAPID key management |

## 🚀 Quick Commands

### **Check Current Status**
```bash
# Check active port forwards
ps aux | grep "kubectl port-forward" | grep -v grep

# Run health check
make simple-status
```

### **Start Essential Services**
```bash
# Start core infrastructure
kubectl port-forward -n trading-system service/timescaledb 11140:5432 &
kubectl port-forward -n trading-system service/redis 11379:6379 &
kubectl port-forward -n trading-system service/rabbitmq 11144:5672 &

# Start unified dashboards
kubectl port-forward -n trading-system service/unified-analytics-dashboard 11114:80 &
kubectl port-forward -n trading-system service/unified-trading-dashboard 11115:80 &
kubectl port-forward -n trading-system service/unified-news-dashboard 11113:80 &

# Start AI services
kubectl port-forward -n trading-system service/llm-proxy 11081:11081 &
kubectl port-forward -n trading-system service/ai-analysis-service 11085:11085 &
```

### **Stop All Port Forwards**
```bash
pkill -f "kubectl port-forward"
```

### **Test Port Forwards**
```bash
# Test specific service
curl -s http://localhost:11114/health

# Test multiple services
for port in 11114 11115 11113; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/health || echo "Port $port not responding"
done
```

## 📝 Status Indicators

- **✅ Active**: Currently port-forwarded and accessible
- **⏸️ LoadBalancer**: Using LoadBalancer instead of port-forward
- **❌ Not Forwarded**: Available but not currently port-forwarded
- **⚠️ DEPRECATED**: Service has been moved to external sources
- **🔧 Maintenance**: Service is down for maintenance
- **🚨 Issues**: Service has known issues

## 🔄 Update Process

Following the **Port Mapping Management Rule** (`.cursor/rules/port-mapping.mdc`):

1. **Before making changes**: Check current active port forwards
   ```bash
   ps aux | grep "kubectl port-forward" | grep -v grep
   ```

2. **After making changes**: Update this document with:
   - Current active port forwards
   - Service status (✅ Active, ❌ Not Forwarded, ⏸️ LoadBalancer)
   - Last updated timestamp

3. **Test changes**: Verify port forwards are working
   ```bash
   curl -s http://localhost:<port>/health
   ```

4. **Document changes**: Update relevant documentation

## 🎯 Port Range Standards

- **External Ports**: 11000-11999 (project standard)
- **Internal Ports**: Service-specific ports
- **Avoid Conflicts**: No default ports (3000, 5432, 6379, 8080, 9090)
- **Consistent Mapping**: Same external port for same service

## 🗄️ External Database Configuration

**Important**: Internal databases have been **DEPRECATED** and moved to external sources.

### **External Database Services:**
- **TimescaleDB**: Moved to external managed database service
- **Redis**: Moved to external managed cache service (redis://redis.redis.svc.cluster.local:6379)
- **RabbitMQ**: Moved to external managed message queue service
- **PostgreSQL Vector**: Moved to external managed vector database service

### **Configuration:**
- Database connections are configured via environment variables
- Services connect directly to external databases (no port forwarding needed)
- Internal database services should be scaled down or removed
- See `docs/EXTERNAL_DATABASE_CONFIGURATION.md` for detailed setup

### **Migration Status:**
- ✅ **Completed**: All services migrated to external databases
- ⚠️ **Deprecated**: Internal database services (TimescaleDB, Redis, RabbitMQ, PostgreSQL Vector)
- 🔄 **In Progress**: Cleanup of internal database deployments

## 🔗 Related Documentation

- **Port Forwarding Guide**: `docs/PORT_FORWARDING_GUIDE.md`
- **Port Mapping Rule**: `.cursor/rules/port-mapping.mdc`
- **Service Architecture**: `docs/ARCHITECTURE_DIAGRAM.md`
- **Makefile Commands**: `make port-*` (see main Makefile)

## 🆕 Recent Changes

- **2025-09-03**: Created standardized PORT_MAP.md following new rules format
- **2025-09-03**: Moved from `md/PORT_MAP.md` to root directory
- **2025-09-03**: Added comprehensive service categories and port assignments
- **2025-09-03**: Integrated with new rules system and update process
- **2025-09-03**: **IMPORTANT**: Marked internal databases as DEPRECATED - moved to external sources
- **2025-09-03**: Added external database configuration section and migration status

---

*This document follows the Port Mapping Management Rule and is automatically updated when port forwarding changes are made.*
