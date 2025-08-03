#!/bin/bash

# Update Grafana Dashboards ConfigMap
echo "🔄 Updating Grafana dashboards..."

# Create a new configmap with all dashboards
kubectl create configmap grafana-dashboards-updated \
  --from-file=monitoring/grafana/dashboards/ \
  --from-file=monitoring/grafana/dashboards/dashboard-provider.yaml \
  -n trading-system --dry-run=client -o yaml > /tmp/new-dashboards.yaml

# Apply the new configmap
kubectl apply -f /tmp/new-dashboards.yaml -n trading-system

# Restart Grafana to pick up new dashboards
echo "🔄 Restarting Grafana pod..."
kubectl rollout restart deployment/grafana -n trading-system

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
kubectl rollout status deployment/grafana -n trading-system

echo "✅ Grafana dashboards updated successfully!"
echo "📊 Access Grafana at: http://localhost:11044"
echo ""
echo "📋 Available Dashboards:"
echo "  • Trading System Overview"
echo "  • Market Data Dashboard" 
echo "  • Strategy Performance"
echo "  • Risk Management"
echo "  • AI Performance"
echo "  • System Infrastructure"
echo "  • Backtest Performance (NEW)"
echo "  • Risk Management Enhanced (NEW)" 