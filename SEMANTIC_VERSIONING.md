# Semantic Versioning Quick Reference

## 🚀 Quick Commands

### Version Information
```bash
make version                    # Show current semantic version
./scripts/version.sh --help    # Show all available options
```

### Single Service
```bash
make build-mcp                 # Build MCP service only
make deploy-mcp                # Build + Push + Deploy MCP service
make build-trading             # Build trading service only
make deploy-trading            # Build + Push + Deploy trading service
```

### All Services
```bash
make build                     # Build all services
make deploy                    # Build + Push + Deploy all services
make clean                     # Clean up old Docker images (keep last 5)
make clean-system              # Clean up system (dangling images, containers)
make clean-versions            # Clean up with custom version count (keep last 3)
make test                      # Test deployed services
```

## 📋 Available Services

- `mcp-service` - MCP Service
- `trading-service` - Trading Service  
- `market-data-service` - Market Data Service
- `ai-analysis-service` - AI Analysis Service
- `backtest-api` - Backtest API
- `strategy-service` - Strategy Service
- `unified-analytics-dashboard` - Analytics Dashboard
- `unified-trading-dashboard` - Trading Dashboard
- `unified-news-dashboard` - News Dashboard

## 🏷️ Version Tags

Each build creates multiple tags:
- `0.1.0-ci.21` - Full semantic version
- `0.1` - Major.Minor
- `0` - Major only
- `latest` - Latest build

## 🔧 Advanced Usage

### Script Options
```bash
./scripts/version.sh --version-only           # Show version only
./scripts/version.sh --build-only mcp-service # Build only (no push/deploy)
./scripts/version.sh --no-push mcp-service    # Build + Deploy (no push)
./scripts/version.sh --no-deploy mcp-service  # Build + Push (no deploy)
./scripts/version.sh --all-services           # All services
./scripts/version.sh --clean mcp-service      # Clean up old MCP service versions
./scripts/version.sh --clean --all-services   # Clean up all services
./scripts/version.sh --clean --system-only    # Clean up system only
./scripts/version.sh --clean --keep-versions 3 # Keep last 3 versions
```

### Service-Specific Targets
```bash
# Build targets
make build-mcp make build-trading make build-market-data
make build-ai-analysis make build-backtest make build-strategy
make build-dashboards

# Deploy targets  
make deploy-mcp make deploy-trading make deploy-market-data
make deploy-ai-analysis make deploy-backtest make deploy-strategy
make deploy-dashboards

# Cleanup targets
make clean-mcp make clean-trading make clean-system
make clean-versions
```

## 🚫 What NOT to Use

❌ **Avoid these manual commands:**
```bash
docker build -t localhost:32000/mcp-service:latest
kubectl set image deployment/mcp-service mcp-service=localhost:32000/mcp-service:latest
docker tag mcp-service:latest localhost:32000/mcp-service:v1.2.3
```

✅ **Use these instead:**
```bash
make build-mcp
make deploy-mcp
./scripts/version.sh mcp-service
```

## 🎯 Benefits

1. **Consistent Versioning** - All services use the same semantic version
2. **No Repository Bloat** - Proper versioned tags instead of random names
3. **Automated Workflows** - Single command handles build-push-deploy
4. **Rollback Capability** - Easy rollback to specific versions
5. **Audit Trail** - Clear version history and change tracking

## 🔍 Troubleshooting

### Check Current Version
```bash
make version
```

### Check Service Status
```bash
kubectl get pods -n trading-system | grep mcp-service
kubectl get svc -n trading-system | grep mcp-service
```

### View Logs
```bash
kubectl logs deployment/mcp-service -n trading-system
```

### Test Service
```bash
make test
curl http://localhost:11120/health
```
