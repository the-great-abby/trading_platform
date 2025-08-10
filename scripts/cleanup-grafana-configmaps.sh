#!/bin/bash

# Cleanup Grafana ConfigMaps Script
# This script removes conflicting Grafana ConfigMaps and ensures we use only the single, consolidated one

echo "🧹 Cleaning up conflicting Grafana ConfigMaps..."

# List current Grafana ConfigMaps
echo "📋 Current Grafana ConfigMaps:"
kubectl get configmaps -n trading-system | grep grafana || echo "No Grafana ConfigMaps found"

echo ""
echo "🗑️  Removing conflicting ConfigMaps..."

# Remove conflicting ConfigMaps (these should not exist)
kubectl delete configmap grafana-dashboards-all-fixed -n trading-system 2>/dev/null || echo "✅ grafana-dashboards-all-fixed not found"
kubectl delete configmap grafana-dashboards-complete -n trading-system 2>/dev/null || echo "✅ grafana-dashboards-complete not found"
kubectl delete configmap grafana-dashboards-fixed-v2 -n trading-system 2>/dev/null || echo "✅ grafana-dashboards-fixed-v2 not found"
kubectl delete configmap grafana-dashboards-fixed-v3 -n trading-system 2>/dev/null || echo "✅ grafana-dashboards-fixed-v3 not found"

# Remove duplicate from k8s/ directory if it exists
kubectl delete configmap grafana-dashboards -n trading-system 2>/dev/null || echo "✅ k8s grafana-dashboards not found"

echo ""
echo "🔄 Consolidating dashboards from conflicting ConfigMaps..."

# Run the consolidation script to extract useful dashboards
if [ -f "scripts/consolidate-grafana-dashboards.sh" ]; then
    ./scripts/consolidate-grafana-dashboards.sh
    echo "✅ Dashboard consolidation completed"
else
    echo "⚠️  Consolidation script not found, skipping dashboard consolidation"
fi

echo ""
echo "📦 Ensuring primary ConfigMap exists..."

# Apply the primary ConfigMap
if [ -f "monitoring/grafana-dashboards-configmap.yaml" ]; then
    kubectl apply -f monitoring/grafana-dashboards-configmap.yaml
    echo "✅ Applied primary ConfigMap from monitoring/grafana-dashboards-configmap.yaml"
else
    echo "❌ Primary ConfigMap file not found: monitoring/grafana-dashboards-configmap.yaml"
    echo "   Please ensure this file exists with the consolidated dashboard definitions"
fi

echo ""
echo "🔄 Restarting Grafana deployment..."

# Restart Grafana to pick up the ConfigMap changes
kubectl rollout restart deployment/grafana -n trading-system
echo "✅ Grafana deployment restart initiated"

echo ""
echo "⏳ Waiting for Grafana to be ready..."
kubectl rollout status deployment/grafana -n trading-system --timeout=60s

echo ""
echo "📊 Final ConfigMap status:"
kubectl get configmaps -n trading-system | grep grafana

echo ""
echo "🔍 Verifying Grafana is using correct ConfigMap:"
kubectl describe deployment grafana -n trading-system | grep -A 5 -B 5 grafana-dashboards

echo ""
echo "🎉 Cleanup completed!"
echo "📋 Remember: Always use monitoring/grafana-dashboards-configmap.yaml for dashboard updates"
echo "🔗 Access Grafana at: http://localhost:11044 (admin/admin)" 