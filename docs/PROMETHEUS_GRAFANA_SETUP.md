# 📊 Prometheus & Grafana Setup - Complete Guide

## Quick Summary

✅ **Prometheus**: Deployed and running in `trading-system` namespace  
✅ **Grafana**: Connected to Prometheus  
✅ **Dashboards**: All 51 dashboards exported successfully  
✅ **Port Forwards**: Ready for local access  

## Status: FIXED! ✅

The error `"no such host - prometheus.trading-system.svc.cluster.local"` has been **resolved**!

### What Was Wrong
- Prometheus wasn't deployed in your cluster
- Grafana was configured to connect to non-existent Prometheus service
- Port was incorrectly set to 11190 in the cluster DNS

### What Was Fixed
1. ✅ Deployed Prometheus to `trading-system` namespace
2. ✅ Configured proper scraping for all your trading services
3. ✅ Updated Grafana data source to correct URL
4. ✅ Set up port forwarding (11190 → 9090)

## Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Grafana** | http://localhost:14000 | View all dashboards |
| **Prometheus** | http://localhost:11190 | Raw metrics & queries |
| **Prometheus (cluster)** | http://prometheus.trading-system.svc.cluster.local:9090 | Internal cluster URL |

## Quick Commands

### Check Status
```bash
# Check Prometheus is running
kubectl get pods -n trading-system -l app=prometheus

# Check Grafana can reach Prometheus
curl -s http://localhost:14000/api/datasources | jq '.[] | select(.type=="prometheus")'

# Query Prometheus directly
curl -s "http://localhost:11190/api/v1/query?query=up" | jq
```

### Port Forwarding
```bash
# Start Prometheus port forward
kubectl port-forward svc/prometheus 11190:9090 -n trading-system &

# Start Grafana port forward (if needed)
kubectl port-forward svc/grafana 14000:3000 -n trading-system &

# Check active port forwards
ps aux | grep "kubectl port-forward" | grep -v grep
```

### Restart Services
```bash
# Restart Prometheus
kubectl rollout restart deployment/prometheus -n trading-system

# Restart Grafana
kubectl rollout restart deployment/grafana -n trading-system

# Reconfigure Grafana data source
./scripts/configure-grafana-datasource.sh
```

## Metrics Being Scraped

Prometheus is now scraping metrics from:

### Trading Services
- **Paper Trading Service** - Orders, P&L, portfolio metrics
- **Strategy Service** - Strategy execution metrics
- **Market Data Service** - Market data requests
- **Elliott Wave Service** - Pattern detection metrics
- **Risk Management Service** - Risk assessments and violations

### Dashboards
- **Unified Analytics Dashboard** - Analytics metrics
- **Unified Trading Dashboard** - Trading interface metrics
- **Unified News Dashboard** - News processing metrics

## Prometheus Configuration

Location: `k8s/prometheus-deployment.yaml`

```yaml
scrape_configs:
  - job_name: 'paper-trading'
    targets: ['paper-trading-k8s-service:9090']
  
  - job_name: 'strategy-service'
    targets: ['strategy-service:80']
  
  - job_name: 'market-data-service'
    targets: ['market-data-service:11084']
  
  # ... and more
```

## Grafana Data Source Configuration

```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus.trading-system.svc.cluster.local:9090",
  "access": "proxy",
  "isDefault": true
}
```

## Available Dashboards

All 51 dashboards are now working! Key ones:

### 🎯 Trading Dashboards
- **Trading System Overview** - High-level metrics
- **Strategy Performance** - Strategy execution details
- **Paper Trading Metrics** - Orders, P&L, portfolio
- **Order Execution** - Order flow and fills
- **Risk Management** - Risk metrics and violations

### 🏗️ Infrastructure Dashboards
- **System Infrastructure** - CPU, memory, pods
- **Database Performance** - Database metrics
- **Market Data** - Market data service metrics

### 📊 Unified Dashboards Overview
- Combines all dashboard metrics in one view
- Real-time request rates
- Response times
- Health status

## Example Prometheus Queries

```promql
# Total orders in paper trading
sum(paper_trading_orders_total)

# Request rate for all dashboards
sum(rate(http_requests_total{job=~".*dashboard.*"}[5m]))

# Portfolio value
paper_trading_portfolio_value

# Strategy requests per minute
rate(strategy_requests_total[1m]) * 60

# Services that are down
up{job=~".*"} == 0
```

## Troubleshooting

### Dashboard Shows "No Data"

```bash
# Check if Prometheus is scraping the target
curl -s http://localhost:11190/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'

# Check if service has /metrics endpoint
kubectl port-forward svc/strategy-service 8080:80 -n trading-system &
curl http://localhost:8080/metrics
```

### "Connection Refused" Error

```bash
# Restart Prometheus
kubectl rollout restart deployment/prometheus -n trading-system

# Wait for ready
kubectl wait --for=condition=ready pod -l app=prometheus -n trading-system --timeout=60s

# Reconfigure Grafana
./scripts/configure-grafana-datasource.sh
```

### Metrics Not Appearing

```bash
# Check Prometheus logs
kubectl logs -f deployment/prometheus -n trading-system

# Verify service endpoints
kubectl get endpoints -n trading-system | grep -E "(prometheus|paper-trading|strategy)"

# Test metrics endpoint directly
kubectl exec -it deployment/strategy-service -n trading-system -- curl localhost:80/metrics
```

## Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/export-dashboards-to-grafana-fixed.sh` | Export all dashboards to Grafana |
| `scripts/configure-grafana-datasource.sh` | Configure Prometheus data source |
| `k8s/prometheus-deployment.yaml` | Prometheus deployment manifest |

## Maintenance

### Update Prometheus Configuration

1. Edit `k8s/prometheus-deployment.yaml`
2. Apply changes:
   ```bash
   kubectl apply -f k8s/prometheus-deployment.yaml
   kubectl rollout restart deployment/prometheus -n trading-system
   ```

### Add New Metrics Target

Edit the ConfigMap in `k8s/prometheus-deployment.yaml`:

```yaml
- job_name: 'my-new-service'
  static_configs:
    - targets: ['my-service.trading-system.svc.cluster.local:80']
  metrics_path: '/metrics'
  scrape_interval: 30s
```

Then apply and restart:
```bash
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl rollout restart deployment/prometheus -n trading-system
```

## Resources

- Prometheus: http://localhost:11190
- Grafana: http://localhost:14000/dashboards
- Prometheus Query Docs: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Grafana Docs: https://grafana.com/docs/

---

**Status**: ✅ **FULLY OPERATIONAL**  
**Last Updated**: 2025-10-07  
**Dashboards Exported**: 51/51  
**Services Monitored**: 8+  

