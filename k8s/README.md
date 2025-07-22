# Kubernetes Configuration - Consolidated Structure

This directory contains the consolidated Kubernetes configuration for the trading system.

## 📁 Directory Structure

```
k8s/
├── core/                    # Core namespace and configuration
│   └── namespace.yaml      # Namespace, secrets, and config maps
├── infrastructure/          # Infrastructure services
│   ├── database.yaml       # PostgreSQL and Redis
│   └── rabbitmq.yaml       # RabbitMQ message broker
├── services/               # Application services
│   ├── core-services.yaml  # Core trading services
│   └── dashboard-services.yaml # UI and dashboard services
├── templates/              # Reusable templates
│   └── job-template.yaml   # Job template for backtests/analysis
└── jobs/                   # Generated job files (auto-created)
```

## 🚀 Quick Start

### Deploy the entire system:
```bash
./scripts/deploy-consolidated.sh
```

### Generate a backtest job:
```bash
./scripts/generate-job-from-template.py \
  --job-type backtest \
  --strategy-name momentum \
  --symbols "AAPL,NVDA,TSLA" \
  --start-date "2024-01-01" \
  --end-date "2024-12-31" \
  --output k8s/jobs/backtest-momentum.yaml
```

### Apply a generated job:
```bash
kubectl apply -f k8s/jobs/backtest-momentum.yaml
```

## 📊 Services Overview

### Core Services (core-services.yaml)
- **strategy-service**: Core trading logic and backtesting
- **market-data-service**: Real-time market data
- **market-data-worker**: Background data processing
- **backtest-api**: Backtest API endpoints

### Dashboard Services (dashboard-services.yaml)
- **trading-dashboard-service**: Main trading interface
- **performance-dashboard**: Trading performance metrics
- **health-dashboard**: System health monitoring
- **rss-feed-service**: Trading recommendations feed
- **rss-dashboard**: RSS feed viewer

### Infrastructure (infrastructure/)
- **PostgreSQL**: Main database
- **Redis**: Caching and session storage
- **RabbitMQ**: Message broker

## 🔧 Configuration

### Environment Variables
All services use centralized configuration from:
- `trading-secrets`: Sensitive data (API keys, passwords)
- `trading-config`: Non-sensitive configuration

### Registry
All images use: `localhost:32000`

### Resource Limits
- **Core services**: 1Gi memory, 500m CPU
- **Dashboard services**: 512Mi memory, 200m CPU
- **Jobs**: 2Gi memory, 1000m CPU

## 📈 Monitoring

### Health Checks
All services include:
- **Liveness probes**: HTTP GET /health
- **Readiness probes**: HTTP GET /ready
- **Resource limits**: Memory and CPU constraints

### Port Forwarding
Use the robust port forwarding script:
```bash
./scripts/robust-port-forward.sh start
```

## 🧹 Maintenance

### Cleanup old files:
```bash
./scripts/cleanup-old-k8s.sh
```

### View service status:
```bash
kubectl get pods -n trading-system
kubectl get services -n trading-system
kubectl get deployments -n trading-system
```

## 🔄 Migration from Old Structure

The old scattered YAML files have been consolidated into logical groups:

| Old Files | New Location |
|-----------|--------------|
| strategy-service.yaml | core-services.yaml |
| market-data-*.yaml | core-services.yaml |
| *-dashboard.yaml | dashboard-services.yaml |
| rabbitmq-deployment.yaml | infrastructure/rabbitmq.yaml |
| postgres-deployment.yaml | infrastructure/database.yaml |

## 📝 Benefits of New Structure

1. **Reduced Complexity**: 68 files → 6 main files
2. **Better Organization**: Logical grouping by function
3. **Reusable Templates**: Job template for consistent job creation
4. **Centralized Configuration**: Shared secrets and config maps
5. **Easier Maintenance**: Single file per service type
6. **Consistent Standards**: Uniform resource limits and health checks

## 🚨 Important Notes

- All services use the `trading-system` namespace
- Registry is set to `localhost:32000`
- Database passwords are stored in Kubernetes secrets
- Health checks are configured for all services
- Resource limits prevent resource exhaustion 