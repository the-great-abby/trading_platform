#!/bin/bash

# Quick Grafana Deployment for External Server
# Simplified version for rapid deployment

set -e

EXTERNAL_GRAFANA_URL=${1:-"http://localhost:3000"}
ADMIN_PASSWORD=${2:-"admin"}

if [ -z "$1" ]; then
    echo "Usage: $0 <external-grafana-url> [admin-password]"
    echo "Example: $0 http://your-server:3000 admin"
    exit 1
fi

echo "🚀 Quick deploying to external Grafana at $EXTERNAL_GRAFANA_URL..."

# Test connection
echo "🔍 Testing connection to Grafana..."
if ! curl -s -f "$EXTERNAL_GRAFANA_URL/api/health" > /dev/null; then
    echo "❌ Cannot connect to Grafana at $EXTERNAL_GRAFANA_URL"
    echo "   Make sure Grafana is running and accessible"
    exit 1
fi

# Create Trading System folder
echo "📁 Creating 'Trading System' folder..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"Trading System"}' \
  "$EXTERNAL_GRAFANA_URL/api/folders" \
  -u admin:$ADMIN_PASSWORD 2>/dev/null || echo "   Folder may already exist"

# Key dashboards to deploy (prioritized list)
KEY_DASHBOARDS=(
    "trading-system-overview.json"
    "strategy-performance.json"
    "risk-management.json"
    "system-infrastructure.json"
    "market-data.json"
)

echo "📊 Deploying key dashboards..."

for dashboard in "${KEY_DASHBOARDS[@]}"; do
    dashboard_file="monitoring/grafana/dashboards/$dashboard"
    if [ -f "$dashboard_file" ]; then
        echo "   📈 Importing $dashboard..."
        
        # Update the JSON to ensure it goes to the right folder
        temp_file=$(mktemp)
        jq --arg folderId "1" '.folderId = ($folderId | tonumber)' "$dashboard_file" > "$temp_file"
        
        curl -X POST \
          -H "Content-Type: application/json" \
          -d @"$temp_file" \
          "$EXTERNAL_GRAFANA_URL/api/dashboards/db" \
          -u admin:$ADMIN_PASSWORD 2>/dev/null && echo "     ✅ Success" || echo "     ⚠️  May already exist"
        
        rm -f "$temp_file"
    else
        echo "   ⚠️  Dashboard $dashboard not found, skipping..."
    fi
done

echo ""
echo "✅ Quick deployment complete!"
echo "📊 Access your external Grafana: $EXTERNAL_GRAFANA_URL"
echo "🔑 Login: admin/$ADMIN_PASSWORD"
echo "📁 Check the 'Trading System' folder for imported dashboards"
echo ""
echo "💡 Note: Dashboards expect Prometheus at:"
echo "   http://prometheus.trading-system.svc.cluster.local:11190"
echo "   Configure this datasource in your external Grafana for cross-namespace access"
