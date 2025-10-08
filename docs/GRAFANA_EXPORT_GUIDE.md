# 📊 Grafana Dashboard Export Guide

## Overview

This guide shows you how to export your trading system dashboards to Grafana at `http://localhost:14000/dashboards`.

## Quick Start

### Option 1: Automated Export (Recommended)

```bash
# Run the automated export script
./scripts/export-dashboards-to-grafana.sh
```

This will automatically import all **52+ dashboards** from `monitoring/grafana/dashboards/` to your Grafana instance.

### Option 2: Manual Import

1. Open Grafana: http://localhost:14000
2. Log in (default: admin/admin)
3. Click **+** → **Import**
4. Upload dashboard JSON files from `monitoring/grafana/dashboards/`

## Available Dashboards

### 🎯 Core Trading Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| **Trading System Overview** | `trading-system-overview.json` | High-level system metrics |
| **Strategy Performance** | `strategy-performance-fixed.json` | Strategy execution metrics |
| **Order Execution** | `fixed-order-execution-dashboard.json` | Order flow and execution |
| **Risk Management** | `risk-management-enhanced-fixed.json` | Risk metrics and limits |
| **Market Data** | `market-data-dashboard-fixed.json` | Market data service metrics |
| **Paper Trading Metrics** | `paper-trading-metrics.json` | Paper trading orders and P&L |
| **Unified Dashboards** | `unified-dashboards-overview.json` | All unified dashboard metrics |

### 📈 Infrastructure Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| **System Infrastructure** | `system-infrastructure-fixed-v2.json` | Infrastructure metrics |
| **Database Performance** | `database-performance-dashboard.json` | TimescaleDB metrics |
| **Message Queue Health** | `message-queue-health-dashboard.json` | RabbitMQ/Redis metrics |

### 🤖 AI & Analytics Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| **AI Performance** | `ai-performance-fixed.json` | AI service metrics |
| **LLM Proxy** | `llm-proxy-dashboard.json` | LLM proxy metrics |
| **Backtest Performance** | `backtest-performance-dashboard-fixed.json` | Backtest metrics |

## Configuration

### Environment Variables

```bash
# Customize the export script
export GRAFANA_URL="http://localhost:14000"
export GRAFANA_USER="admin"
export GRAFANA_PASSWORD="admin"

./scripts/export-dashboards-to-grafana.sh
```

### Custom Export

```bash
# Export specific dashboard
DASHBOARD_DIR="./monitoring/grafana/dashboards" \
GRAFANA_URL="http://localhost:14000" \
./scripts/export-dashboards-to-grafana.sh
```

## Manual API Import

If you want more control, use the Grafana API directly:

```bash
# Import a single dashboard
dashboard_file="./monitoring/grafana/dashboards/trading-system-overview.json"
dashboard_json=$(cat "${dashboard_file}")

curl -X POST \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": '"${dashboard_json}"',
    "overwrite": true
  }' \
  "http://localhost:14000/api/dashboards/db"
```

## Setting Up Data Sources

### 1. Prometheus Data Source

Your dashboards need Prometheus as a data source:

```bash
# Add Prometheus data source
curl -X POST \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus.trading-system.svc.cluster.local:9090",
    "access": "proxy",
    "isDefault": true
  }' \
  "http://localhost:14000/api/datasources"
```

### 2. TimescaleDB Data Source (Optional)

For direct database queries:

```bash
curl -X POST \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TimescaleDB",
    "type": "postgres",
    "url": "timescaledb.trading-system.svc.cluster.local:5432",
    "database": "trading_bot",
    "user": "trading_user",
    "secureJsonData": {
      "password": "trading_pass"
    },
    "access": "proxy"
  }' \
  "http://localhost:14000/api/datasources"
```

## Port Forwarding Setup

If Grafana isn't accessible on port 14000:

```bash
# Forward Grafana from Kubernetes
kubectl port-forward svc/grafana 14000:3000 -n trading-system &

# Or use the standard port
kubectl port-forward svc/grafana 11102:3000 -n trading-system &
```

## Dashboard Customization

### Adding Custom Panels

1. Open a dashboard in Grafana
2. Click **Add panel**
3. Configure data source and query:

**Example: Total Trades Query**
```promql
sum(increase(paper_trading_orders_total[24h]))
```

**Example: Portfolio Value**
```promql
paper_trading_portfolio_value
```

### Creating New Dashboards

Use existing dashboards as templates:

```bash
# Download existing dashboard
curl -u "admin:admin" \
  "http://localhost:14000/api/dashboards/uid/trading-overview" \
  > my-custom-dashboard.json

# Modify and re-import
# Edit my-custom-dashboard.json
curl -X POST \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -d @my-custom-dashboard.json \
  "http://localhost:14000/api/dashboards/db"
```

## Prometheus Metrics Available

Your services expose these metrics for Grafana:

### Paper Trading Service (port 8080/9090)
- `paper_trading_orders_total` - Total orders
- `paper_trading_orders_filled_total` - Filled orders
- `paper_trading_portfolio_value` - Portfolio value
- `paper_trading_total_pnl` - Total P&L

### Strategy Service (port 11001)
- `strategy_requests_total` - Strategy requests
- `strategy_request_duration_seconds` - Request latency

### Market Data Service (port 11084)
- `market_data_requests_total` - Market data requests
- `market_data_request_duration_seconds` - Request latency

### Risk Management Service (port 11182)
- `risk_assessments_total` - Risk assessments
- `risk_violations_total` - Risk violations
- `portfolio_var` - Value at Risk

## Troubleshooting

### Dashboard Import Fails

```bash
# Check Grafana logs
kubectl logs -f deployment/grafana -n trading-system

# Verify API connectivity
curl -u "admin:admin" http://localhost:14000/api/health
```

### Metrics Not Showing

```bash
# Check Prometheus is scraping your services
curl http://localhost:11190/api/v1/targets

# Verify service metrics endpoints
curl http://localhost:8080/metrics
curl http://localhost:11001/metrics
curl http://localhost:11084/metrics
```

### Authentication Issues

```bash
# Reset Grafana admin password
kubectl exec -it deployment/grafana -n trading-system -- \
  grafana-cli admin reset-admin-password newpassword
```

## Best Practices

1. **Use Folders**: Organize dashboards into folders (Trading, Infrastructure, AI)
2. **Set Refresh Rates**: Use appropriate refresh rates (10s for trading, 1m for infrastructure)
3. **Add Annotations**: Mark important events (deployments, issues)
4. **Create Alerts**: Set up Grafana alerts for critical metrics
5. **Version Control**: Keep dashboard JSON in git for backup

## Grafana Dashboard URLs

After import, access your dashboards at:

- **Main Dashboards**: http://localhost:14000/dashboards
- **Trading Overview**: http://localhost:14000/d/trading-overview
- **Paper Trading**: http://localhost:14000/d/paper-trading-metrics
- **Strategy Performance**: http://localhost:14000/d/strategy-performance
- **Risk Management**: http://localhost:14000/d/risk-management

## Additional Resources

- Grafana Documentation: https://grafana.com/docs/
- Prometheus Query Language: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Your dashboards: `monitoring/grafana/dashboards/`
- Export script: `scripts/export-dashboards-to-grafana.sh`

---

*Last Updated: 2025-10-07*

