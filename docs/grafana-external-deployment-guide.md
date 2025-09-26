# 🚀 Grafana External Server Deployment Guide

This guide provides multiple methods to deploy your trading system's Grafana dashboards and schema to an external Grafana server.

## 📋 Prerequisites

- External Grafana server running (version 8.0+ recommended)
- Access to the external Grafana server (admin credentials)
- Network connectivity between your system and the external server
- **Cross-namespace access**: Your external Grafana must be able to reach `prometheus.trading-system.svc.cluster.local:11190`
- Kubernetes cluster access (if external Grafana is outside the cluster)

## 🎯 Available Deployment Methods

### Method 1: Quick API Deployment (Recommended for Testing)

**Best for**: Quick testing, small deployments, immediate results

```bash
# Run the quick deployment script
./scripts/quick-grafana-deploy.sh http://your-external-server:3000 admin

# Or with custom password
./scripts/quick-grafana-deploy.sh http://your-external-server:3000 your-password
```

**What it does**:
- Tests connection to external Grafana
- Creates "Trading System" folder
- Imports 5 key dashboards
- Provides immediate feedback

### Method 2: Complete Schema Export (Recommended for Production)

**Best for**: Full deployment, production environments, comprehensive setup

```bash
# Export complete schema
./scripts/export-grafana-schema.sh

# This creates a timestamped export directory with:
# - All dashboard JSON files
# - Datasource configurations
# - Provisioning files
# - Docker Compose setup
# - API import scripts
# - Deployment documentation
```

**Deployment Options**:

#### Option 2A: Docker Compose Deployment
```bash
# On your external server
cd grafana-export-YYYYMMDD_HHMMSS/
docker-compose up -d
```

#### Option 2B: API Import
```bash
# On your external server
cd grafana-export-YYYYMMDD_HHMMSS/
./import-via-api.sh http://localhost:3000 admin
```

#### Option 2C: Manual Import via UI
1. Access external Grafana UI
2. Go to "+" → "Import"
3. Upload each JSON file from `dashboards/` folder
4. Configure datasources manually

### Method 3: Manual Dashboard-by-Dashboard Import

**Best for**: Selective deployment, custom modifications

1. **Access External Grafana UI**
   - Navigate to your external Grafana server
   - Login with admin credentials

2. **Create Folder Structure**
   - Go to "Browse" → "New Folder"
   - Create "Trading System" folder

3. **Import Individual Dashboards**
   - Go to "+" → "Import"
   - Copy/paste or upload JSON content from:
     - `monitoring/grafana/dashboards/trading-system-overview.json`
     - `monitoring/grafana/dashboards/strategy-performance.json`
     - `monitoring/grafana/dashboards/risk-management.json`
     - `monitoring/grafana/dashboards/system-infrastructure.json`
     - `monitoring/grafana/dashboards/ai-performance.json`
     - `monitoring/grafana/dashboards/market-data.json`

## 🔧 Configuration Updates

### Datasource Configuration

Your dashboards expect a Prometheus datasource accessible from the `trading-system` namespace. Configure the datasource URL in your external Grafana:

1. **Via UI**:
   - Go to "Configuration" → "Data Sources"
   - Add/Edit Prometheus datasource
   - Set URL to: `http://prometheus.trading-system.svc.cluster.local:11190`

2. **Via API**:
   ```bash
   # Create new Prometheus datasource
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Prometheus",
       "type": "prometheus",
       "access": "proxy",
       "url": "http://prometheus.trading-system.svc.cluster.local:11190",
       "isDefault": true
     }' \
     "$EXTERNAL_GRAFANA_URL/api/datasources" \
     -u admin:$ADMIN_PASSWORD
   ```

### Dashboard Modifications

If your external Prometheus has different metric names or labels, you may need to update:

1. **Metric Queries**: Update PromQL queries in dashboard panels
2. **Variable Definitions**: Modify dashboard variables for your environment
3. **Data Source References**: Ensure all panels reference the correct datasource

## 📊 Key Dashboards Overview

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| **Trading System Overview** | High-level system health | Active positions, P&L, win rates |
| **Strategy Performance** | Individual strategy analysis | Sharpe ratios, max drawdown, trade counts |
| **Risk Management** | Risk monitoring | VaR, position limits, portfolio beta |
| **AI Performance** | LLM and AI monitoring | Request rates, model accuracy, cache hits |
| **System Infrastructure** | Infrastructure monitoring | CPU, memory, network, database connections |
| **Market Data** | Market data feed monitoring | Feed health, latency, data quality |

## 🔍 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if Grafana is running
   curl -I http://your-server:3000/api/health
   ```

2. **Authentication Failed**
   ```bash
   # Test credentials
   curl -u admin:password http://your-server:3000/api/user
   ```

3. **Dashboard Import Errors**
   - Check Grafana version compatibility
   - Verify JSON format is valid
   - Ensure datasources are configured

4. **No Data in Dashboards**
   - Verify Prometheus datasource URL
   - Check if metrics are being scraped
   - Validate metric names in your environment

### Validation Steps

1. **Test Connection**:
   ```bash
   curl -s http://your-server:3000/api/health | jq .
   ```

2. **Verify Dashboards**:
   ```bash
   curl -s -u admin:password http://your-server:3000/api/search?folderIds=1
   ```

3. **Check Datasources**:
   ```bash
   curl -s -u admin:password http://your-server:3000/api/datasources
   ```

## 🚀 Quick Start Commands

```bash
# 1. Test your external Grafana
curl -I http://your-external-server:3000/api/health

# 2. Configure Prometheus datasource (cross-namespace)
./scripts/configure-prometheus-datasource.sh http://your-external-server:3000 admin

# 3. Quick deployment (recommended first step)
./scripts/quick-grafana-deploy.sh http://your-external-server:3000 admin

# 4. Full export for production deployment
./scripts/export-grafana-schema.sh

# 5. Copy to external server and deploy
scp grafana-schema-export-*.tar.gz user@your-server:/path/to/deploy/
```

## 🌐 Cross-Namespace Access

Your external Grafana needs to access Prometheus in the `trading-system` namespace. The full service address is:

```
http://prometheus.trading-system.svc.cluster.local:11190
```

### Network Requirements

1. **Same Kubernetes Cluster**: If your external Grafana is in the same cluster but different namespace, this should work automatically.

2. **Different Kubernetes Cluster**: You'll need to set up network policies or use port-forwarding:
   ```bash
   # Port-forward from your local machine
   kubectl port-forward -n trading-system svc/prometheus 11190:11190
   # Then use: http://localhost:11190
   ```

3. **External to Kubernetes**: Set up a LoadBalancer or NodePort service for Prometheus:
   ```yaml
   # Add to your Prometheus service
   spec:
     type: LoadBalancer
     ports:
     - port: 11190
       targetPort: 11190
   ```

## 📝 Notes

- **Port Considerations**: Ensure your external Grafana is accessible on the expected port
- **Security**: Consider using HTTPS and secure authentication for production
- **Backup**: Always backup your external Grafana before major imports
- **Updates**: Use the same scripts to update dashboards when you make changes

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify network connectivity and credentials
3. Review Grafana logs on the external server
4. Test with a simple dashboard first before importing all

---

**Ready to deploy?** Start with the quick deployment script and then move to the full export for production use!
