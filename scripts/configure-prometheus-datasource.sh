#!/bin/bash

# Configure Prometheus Datasource for External Grafana
# This script sets up the Prometheus datasource with the correct cross-namespace URL

set -e

EXTERNAL_GRAFANA_URL=${1:-"http://localhost:3000"}
ADMIN_PASSWORD=${2:-"admin"}

if [ -z "$1" ]; then
    echo "Usage: $0 <external-grafana-url> [admin-password]"
    echo "Example: $0 http://your-server:3000 admin"
    exit 1
fi

echo "🔧 Configuring Prometheus datasource for external Grafana..."
echo "🌐 Grafana URL: $EXTERNAL_GRAFANA_URL"
echo "📊 Prometheus URL: http://prometheus.trading-system.svc.cluster.local:11190"

# Test connection
echo "🔍 Testing connection to Grafana..."
if ! curl -s -f "$EXTERNAL_GRAFANA_URL/api/health" > /dev/null; then
    echo "❌ Cannot connect to Grafana at $EXTERNAL_GRAFANA_URL"
    echo "   Make sure Grafana is running and accessible"
    exit 1
fi

# Check if datasource already exists
echo "🔍 Checking for existing Prometheus datasource..."
EXISTING_DS=$(curl -s -u admin:$ADMIN_PASSWORD "$EXTERNAL_GRAFANA_URL/api/datasources" | jq -r '.[] | select(.name=="Prometheus") | .id' 2>/dev/null || echo "")

if [ -n "$EXISTING_DS" ] && [ "$EXISTING_DS" != "null" ]; then
    echo "📊 Found existing Prometheus datasource (ID: $EXISTING_DS)"
    echo "🔄 Updating existing datasource..."
    
    # Update existing datasource
    curl -X PUT \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": "http://prometheus.trading-system.svc.cluster.local:11190",
        "isDefault": true,
        "editable": true
      }' \
      "$EXTERNAL_GRAFANA_URL/api/datasources/$EXISTING_DS" \
      -u admin:$ADMIN_PASSWORD
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully updated Prometheus datasource"
    else
        echo "❌ Failed to update datasource"
        exit 1
    fi
else
    echo "📊 Creating new Prometheus datasource..."
    
    # Create new datasource
    curl -X POST \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": "http://prometheus.trading-system.svc.cluster.local:11190",
        "isDefault": true,
        "editable": true
      }' \
      "$EXTERNAL_GRAFANA_URL/api/datasources" \
      -u admin:$ADMIN_PASSWORD
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully created Prometheus datasource"
    else
        echo "❌ Failed to create datasource"
        exit 1
    fi
fi

# Test the datasource
echo "🧪 Testing datasource connection..."
TEST_RESULT=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "access": "proxy",
    "url": "http://prometheus.trading-system.svc.cluster.local:11190"
  }' \
  "$EXTERNAL_GRAFANA_URL/api/datasources/proxy/1/api/v1/query?query=up" \
  -u admin:$ADMIN_PASSWORD 2>/dev/null || echo "failed")

if [[ "$TEST_RESULT" == *"success"* ]] || [[ "$TEST_RESULT" == *"up"* ]]; then
    echo "✅ Datasource test successful - Prometheus is reachable"
else
    echo "⚠️  Datasource test failed - check network connectivity to trading-system namespace"
    echo "   Make sure your external Grafana can reach: prometheus.trading-system.svc.cluster.local:11190"
fi

echo ""
echo "🎉 Prometheus datasource configuration complete!"
echo "📊 Access Grafana: $EXTERNAL_GRAFANA_URL"
echo "🔑 Login: admin/$ADMIN_PASSWORD"
echo "📈 Prometheus URL: http://prometheus.trading-system.svc.cluster.local:11190"
echo ""
echo "💡 Next steps:"
echo "1. Import your dashboards using: ./scripts/quick-grafana-deploy.sh $EXTERNAL_GRAFANA_URL $ADMIN_PASSWORD"
echo "2. Or use the full export: ./scripts/export-grafana-schema.sh"
