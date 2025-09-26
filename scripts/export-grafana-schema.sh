#!/bin/bash

# Export Grafana Schema for External Server
# This script exports all dashboards and datasources for deployment to external Grafana

set -e

EXPORT_DIR="./grafana-export-$(date +%Y%m%d_%H%M%S)"
DASHBOARD_DIR="$EXPORT_DIR/dashboards"
DATASOURCE_DIR="$EXPORT_DIR/datasources"
PROVISIONING_DIR="$EXPORT_DIR/provisioning"

echo "🚀 Exporting Grafana schema for external deployment..."
echo "📁 Export directory: $EXPORT_DIR"

# Create export directory structure
mkdir -p "$DASHBOARD_DIR"
mkdir -p "$DATASOURCE_DIR"
mkdir -p "$PROVISIONING_DIR/dashboards"
mkdir -p "$PROVISIONING_DIR/datasources"

echo "📊 Copying dashboards..."

# Copy all dashboard JSON files
cp monitoring/grafana/dashboards/*.json "$DASHBOARD_DIR/" 2>/dev/null || true

# Copy datasources
cp monitoring/grafana/datasources/* "$DATASOURCE_DIR/" 2>/dev/null || true

# Create dashboard provider configuration
cat > "$PROVISIONING_DIR/dashboards/dashboard-provider.yaml" << 'EOF'
apiVersion: 1

providers:
  - name: 'Trading System Dashboards'
    orgId: 1
    folder: 'Trading System'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Create datasource provider configuration
cat > "$PROVISIONING_DIR/datasources/datasource-provider.yaml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.trading-system.svc.cluster.local:11190
    isDefault: true
    editable: true
EOF

# Create deployment instructions
cat > "$EXPORT_DIR/README.md" << 'EOF'
# Grafana Schema Export for External Server

This directory contains all the Grafana dashboards and configuration files needed to deploy the trading system monitoring to an external Grafana server.

## Contents

- `dashboards/` - All dashboard JSON files
- `datasources/` - Datasource configuration files
- `provisioning/` - Grafana provisioning configuration

## Deployment Options

### Option 1: Docker Compose (Recommended)
1. Copy this entire directory to your external server
2. Use the provided docker-compose.yml to start Grafana with provisioning

### Option 2: Manual Import
1. Start your external Grafana server
2. Import each dashboard JSON file through the Grafana UI
3. Configure datasources manually

### Option 3: Grafana API Import
1. Use the provided import script with Grafana API
2. Automatically import all dashboards and datasources

## Key Dashboards

- Trading System Overview - High-level system health
- Strategy Performance - Individual strategy analysis
- Risk Management - Comprehensive risk monitoring
- AI Performance - LLM and AI system monitoring
- System Infrastructure - Infrastructure monitoring
- Market Data Dashboard - Market data feed monitoring
- Backtest Performance - Backtesting results

## Prerequisites

- Prometheus datasource configured (URL: http://prometheus.trading-system.svc.cluster.local:11190)
- Grafana 8.0+ for full compatibility
- Proper network access to your monitoring endpoints
- Kubernetes cluster access for cross-namespace communication
EOF

# Create Docker Compose for external deployment
cat > "$EXPORT_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    container_name: trading-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./provisioning:/etc/grafana/provisioning:ro
      - ./dashboards:/var/lib/grafana/dashboards:ro
    restart: unless-stopped

volumes:
  grafana-storage:
EOF

# Create API import script
cat > "$EXPORT_DIR/import-via-api.sh" << 'EOF'
#!/bin/bash

# Import Grafana Dashboards via API
# Usage: ./import-via-api.sh <grafana-url> <admin-password>

GRAFANA_URL=${1:-"http://localhost:3000"}
ADMIN_PASSWORD=${2:-"admin"}

if [ -z "$1" ]; then
    echo "Usage: $0 <grafana-url> [admin-password]"
    echo "Example: $0 http://your-grafana-server:3000 admin"
    exit 1
fi

echo "🚀 Importing dashboards to $GRAFANA_URL..."

# Create folder first
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"Trading System"}' \
  "$GRAFANA_URL/api/folders" \
  -u admin:$ADMIN_PASSWORD

# Import each dashboard
for dashboard in dashboards/*.json; do
    if [ -f "$dashboard" ]; then
        echo "📊 Importing $(basename $dashboard)..."
        curl -X POST \
          -H "Content-Type: application/json" \
          -d @$dashboard \
          "$GRAFANA_URL/api/dashboards/db" \
          -u admin:$ADMIN_PASSWORD
    fi
done

echo "✅ Import complete!"
echo "📊 Access Grafana at: $GRAFANA_URL"
echo "🔑 Login: admin/$ADMIN_PASSWORD"
EOF

chmod +x "$EXPORT_DIR/import-via-api.sh"

# Create a compressed archive
echo "📦 Creating compressed archive..."
tar -czf "grafana-schema-export-$(date +%Y%m%d_%H%M%S).tar.gz" "$EXPORT_DIR"

echo ""
echo "✅ Export complete!"
echo "📁 Export directory: $EXPORT_DIR"
echo "📦 Compressed archive: grafana-schema-export-$(date +%Y%m%d_%H%M%S).tar.gz"
echo ""
echo "🚀 Next steps:"
echo "1. Copy the export directory or archive to your external server"
echo "2. Choose your deployment method from the README.md"
echo "3. Datasource configured for cross-namespace access:"
echo "   http://prometheus.trading-system.svc.cluster.local:11190"
echo "   Update this URL if your external Grafana can't access the trading-system namespace"
echo ""
echo "📊 Dashboard count: $(ls -1 $DASHBOARD_DIR/*.json 2>/dev/null | wc -l)"
echo "🔌 Datasource count: $(ls -1 $DATASOURCE_DIR/* 2>/dev/null | wc -l)"
