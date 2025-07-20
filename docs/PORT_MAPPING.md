# 🚀 Trading System Port Mapping (11000-12000)

All services are now mapped to ports in the 11000-12000 range to avoid conflicts with commonly used ports.

## 📊 Quick Start

```bash
# Start all port forwarding
make port-forward-all

# Check service status
make check-services

# Stop all port forwarding
make port-forward-stop
```

## 🎯 Main Dashboards

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Performance Dashboard | 11000 | http://localhost:11000/dashboard | Main trading performance metrics |
| Trading Dashboard | 11001 | http://localhost:11001/ | Real-time trading interface |
| Health Dashboard | 11002 | http://localhost:11002/ | System health monitoring |
| Comprehensive Dashboard | 11003 | http://localhost:11003/ | All-in-one dashboard |

## 🔌 APIs

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Backtest API | 11010 | http://localhost:11010/ | Backtest results and analysis |
| Public API | 11011 | http://localhost:11011/ | Public trading API |
| Strategy Service | 11012 | http://localhost:11012/ | Strategy management |
| Analytics Service | 11013 | http://localhost:11013/ | Advanced analytics |

## ⚙️ Core Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Order Service | 11020 | http://localhost:11020/ | Order management |
| Portfolio Service | 11021 | http://localhost:11021/ | Portfolio tracking |
| Risk Service | 11022 | http://localhost:11022/ | Risk management |
| Trading Service | 11023 | http://localhost:11023/ | Core trading engine |

## 📈 Data Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Market Data Service | 11030 | http://localhost:11030/ | Real-time market data |
| Backtest Request Service | 11031 | http://localhost:11031/ | Backtest job management |
| Report Viewer Service | 11032 | http://localhost:11032/ | Report generation |
| Notification Service | 11033 | http://localhost:11033/ | System notifications |

## 🗄️ Infrastructure

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| PostgreSQL | 11040 | localhost:11040 | Main database |
| RabbitMQ | 11041 | localhost:11041 | Message queue |
| Redis | 11042 | localhost:11042 | Cache and sessions |
| Ollama | 11043 | http://localhost:11043/ | LLM service |

## 🤖 AI Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| LLM Service | 11050 | http://localhost:11050/ | AI/ML services |
| Strategy Performance Monitor | 11051 | http://localhost:11051/ | Strategy monitoring |
| Ollama LLM Proxy | 12001 | http://localhost:12001/ | External LLM proxy API |

## 🛠️ Management Commands

### Start Services
```bash
# Start all port forwarding
./scripts/port-forward-all.sh

# Or use Makefile
make port-forward-all
```

### Check Status
```bash
# Check all services
./scripts/check-services.sh

# Or use Makefile
make check-services
```

### Stop Services
```bash
# Stop all port forwarding
pkill -f "kubectl port-forward"

# Or use Makefile
make port-forward-stop
```

### Quick Access
```bash
# Open dashboards
make dashboard-performance
make dashboard-trading
make dashboard-health

# Open APIs
make api-backtest
make api-public
make api-llm-proxy
```

## 🔧 Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
```bash
# Stop all port forwarding
make port-forward-stop

# Wait a moment, then restart
make port-forward-all
```

### Service Not Responding
If a service shows as offline:
```bash
# Check if the pod is running
kubectl get pods -n trading-system

# Check pod logs
kubectl logs -n trading-system <pod-name>
```

### Reset Everything
```bash
# Stop all port forwarding
make port-forward-stop

# Restart Kubernetes services if needed
kubectl rollout restart deployment -n trading-system

# Start port forwarding again
make port-forward-all
```

## 📝 Notes

- All services use the 11000-12000 range to avoid conflicts
- Port forwarding runs in the background
- Use `make check-services` to verify all services are online
- The Performance Dashboard is the main entry point: http://localhost:11000/dashboard 