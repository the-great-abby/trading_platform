# 🚀 Space Trading Station Monitor ↔ API Architecture Guide

## Overview

This guide documents how the Space Trading Station Monitor (running on your host) connects to the Backtest API (running in Kubernetes) to display real-time trading performance data.

## 📡 Architecture Diagram

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐    SQL    ┌─────────────────┐
│   Host Monitor  │ ←──────────────→ │  Backtest API   │ ←────────→ │   PostgreSQL    │
│   (Your Machine)│                 │   (Kubernetes)  │           │   (Kubernetes)  │
└─────────────────┘                 └─────────────────┘           └─────────────────┘
```

## 🎯 Why This Architecture?

- **Separation of Concerns**: Monitor runs locally, data services run in containers
- **Real Data**: No more simulated data - actual backtest results
- **Scalability**: Multiple monitors can connect to the same API
- **Security**: Database access only through controlled API endpoints
- **Flexibility**: Monitor can run anywhere with network access

## 🚀 Quick Start

### 1. Deploy the Backtest API

```bash
# Deploy the API to Kubernetes
./scripts/deploy-backtest-api.sh

# Or use Makefile
make -f Makefile.kubernetes k8s-deploy-backtest-api
```

### 2. Port Forward the API (for local access)

```bash
# Forward the API service to localhost
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system

# Keep this running in a separate terminal
```

### 3. Run the Monitor

```bash
# Run monitor with API integration
make monitor-demo-api

# Or run directly
python demo_monitor_with_api.py
```

## 📋 Detailed Process

### Step 1: Build and Deploy API

The deployment script does the following:

1. **Build Docker Image**
   ```bash
   docker build -t localhost:5000/backtest-api:latest services/backtest-api/
   ```

2. **Push to Local Registry**
   ```bash
   docker push localhost:5000/backtest-api:latest
   ```

3. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/backtest-api.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

4. **Wait for Deployment**
   ```bash
   kubectl wait --for=condition=available --timeout=300s deployment/backtest-api -n trading-system
   ```

### Step 2: Verify API is Running

```bash
# Check pod status
kubectl get pods -l app=backtest-api -n trading-system

# Check service
kubectl get svc backtest-api -n trading-system

# View logs
kubectl logs deployment/backtest-api -n trading-system
```

### Step 3: Access the API

#### Option A: Port Forwarding (Development)
```bash
# Forward service to localhost
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system

# API available at: http://localhost:10001
```

#### Option B: Direct Kubernetes Access (Production)
```bash
# From within Kubernetes cluster
curl http://trading-ingress.trading-system.svc.cluster.local/api/v1/backtest/

# From host (if ingress is configured)
curl http://trading.example.com/api/v1/backtest/
```

### Step 4: Run the Monitor

The monitor automatically detects the API connection and fetches real data:

```bash
# Run with API integration
python demo_monitor_with_api.py

# Or use Makefile
make monitor-demo-api
```

## 🔧 Configuration

### API Configuration

The API service configuration is in `k8s/backtest-api.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backtest-api
  namespace: trading-system
spec:
  replicas: 2
  containers:
  - name: backtest-api
    image: localhost:5000/backtest-api:latest
    ports:
    - containerPort: 10001
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: read-url
```

### Monitor Configuration

The monitor automatically detects the environment:

```python
# In src/utils/space_station_monitor.py
if os.getenv('KUBERNETES_SERVICE_HOST'):
    # Running in Kubernetes
    api_url = "http://trading-ingress.trading-system.svc.cluster.local/api/v1/backtest"
else:
    # Local development
    api_url = "http://localhost:10001"
```

## 📊 Data Flow

### 1. Monitor Initialization
```python
# Monitor starts and initializes API client
monitor = SpaceStationMonitor()
# → Creates BacktestAPIClient()
# → Detects environment (local vs Kubernetes)
# → Sets appropriate API URL
```

### 2. Data Collection Loop
```python
# Every 3-5 seconds, monitor fetches data
async def _collect_performance_data(self):
    # Fetch from API every few cycles
    if self.backtest_api_client:
        await self.fetch_api_data()
    
    # Update local metrics
    self.active_strategies = len(self.strategy_performance)
    self.pnl_history.append(self.total_pnl)
```

### 3. API Data Fetching
```python
async def fetch_api_data(self):
    # Fetch recent backtest runs
    runs = await self.backtest_api_client.list_backtest_runs(limit=10)
    
    # Update strategy performance
    for run in runs:
        strategy_name = run.get('strategy_name', 'Unknown')
        strategy = self.strategy_performance[strategy_name]
        strategy.total_pnl = run.get('total_pnl', 0.0)
        strategy.total_trades = run.get('total_trades', 0)
```

### 4. Display Update
```python
# Monitor displays real-time dashboard
def _print_dashboard(self):
    print("🚀 SPACE TRADING STATION - MISSION CONTROL DASHBOARD")
    print(f"Total P&L: ${self.total_pnl:,.2f}")
    print(f"Active Strategies: {self.active_strategies}")
    # ... more metrics
```

## 🛠️ Troubleshooting

### API Connection Issues

**Problem**: Monitor can't connect to API
```bash
# Check if API is running
kubectl get pods -l app=backtest-api -n trading-system

# Check API logs
kubectl logs deployment/backtest-api -n trading-system

# Test API directly
curl http://localhost:10001/
```

**Solution**: Ensure port forwarding is active
```bash
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
```

### Database Connection Issues

**Problem**: API can't connect to database
```bash
# Check database pod
kubectl get pods -l app=postgres -n trading-system

# Check database logs
kubectl logs deployment/postgres -n trading-system

# Test database connection
kubectl exec -it deployment/postgres -n trading-system -- psql -U trading_user -d trading_db
```

### Monitor Issues

**Problem**: Monitor shows no data
```bash
# Check if API client is available
python -c "from src.utils.backtest_api_client import BacktestAPIClient; print('API client available')"

# Test API connection
python demo_backtest_api.py
```

## 📈 API Endpoints

The backtest API provides these endpoints:

- `GET /` - Health check
- `GET /api/v1/runs` - List backtest runs
- `GET /api/v1/runs/{id}` - Get specific run details
- `GET /api/v1/runs/{id}/trades` - Get trades for a run
- `GET /api/v1/runs/{id}/equity` - Get equity curve data
- `GET /api/v1/compare` - Compare strategies
- `GET /api/v1/strategies` - List all strategies
- `GET /api/v1/stats` - Get overall statistics

## 🔄 Development Workflow

### 1. Make Changes to API
```bash
# Edit API code in services/backtest-api/
vim services/backtest-api/main.py

# Rebuild and redeploy
./scripts/deploy-backtest-api.sh
```

### 2. Make Changes to Monitor
```bash
# Edit monitor code
vim src/utils/space_station_monitor.py

# Test immediately (no deployment needed)
python demo_monitor_with_api.py
```

### 3. Test New Features
```bash
# Test API endpoints
curl http://localhost:10001/api/v1/runs

# Test monitor integration
make monitor-demo-api
```

## 🎯 Best Practices

### 1. Always Use Port Forwarding for Development
```bash
# Keep this running in a separate terminal
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
```

### 2. Check API Health Before Running Monitor
```bash
# Test API connection
curl http://localhost:10001/

# Should return: {"status": "healthy"}
```

### 3. Monitor API Logs During Development
```bash
# Watch API logs
kubectl logs -f deployment/backtest-api -n trading-system
```

### 4. Use Makefile Targets for Common Operations
```bash
# Deploy API
make -f Makefile.kubernetes k8s-deploy-backtest-api

# Check status
make -f Makefile.kubernetes k8s-status-backtest

# View logs
make -f Makefile.kubernetes k8s-logs-backtest

# Run monitor
make monitor-demo-api
```

## 🚨 Common Issues and Solutions

### Issue: "Connection refused" when running monitor
**Cause**: API service not running or port forwarding not active
**Solution**: 
```bash
# Deploy API first
./scripts/deploy-backtest-api.sh

# Then port forward
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system
```

### Issue: Monitor shows "No data available"
**Cause**: Database has no backtest results
**Solution**:
```bash
# Run a backtest first
make backend-kube-backtest

# Then run monitor
make monitor-demo-api
```

### Issue: API returns 500 errors
**Cause**: Database connection issues or missing tables
**Solution**:
```bash
# Check database migrations
kubectl apply -f k8s/apply-merge-migration-job.yaml

# Check database logs
kubectl logs deployment/postgres -n trading-system
```

## 📚 Related Documentation

- [Kubernetes First Guide](KUBERNETES_FIRST_GUIDE.md)
- [Backtesting Guide](BACKTESTING_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Monitor Configuration](MONITOR_CONFIGURATION.md)

## 🎯 Quick Reference

### Essential Commands
```bash
# Deploy API
./scripts/deploy-backtest-api.sh

# Port forward
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system

# Run monitor
make monitor-demo-api

# Check status
make -f Makefile.kubernetes k8s-status-backtest
```

### File Locations
- API Service: `services/backtest-api/`
- Kubernetes Config: `k8s/backtest-api.yaml`
- Monitor Code: `src/utils/space_station_monitor.py`
- API Client: `src/utils/backtest_api_client.py`
- Demo Script: `demo_monitor_with_api.py`

### Environment Variables
- `DATABASE_URL`: Database connection string
- `API_PORT`: API service port (default: 10001)
- `KUBERNETES_SERVICE_HOST`: Detects Kubernetes environment

---

**This is ORION, Mission Control. The monitor ↔ API architecture is now fully documented! 🚀** 