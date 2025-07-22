#!/bin/bash

# Cleanup Old Kubernetes Files
# Removes the old scattered Kubernetes files after consolidation

set -e

echo "🧹 Cleaning up old Kubernetes files..."
echo "📁 This will remove the old scattered YAML files"
echo ""

# List of files to remove (old scattered files)
OLD_FILES=(
    "k8s/strategy-service.yaml"
    "k8s/market-data-service.yaml"
    "k8s/market-data-worker.yaml"
    "k8s/backtest-api.yaml"
    "k8s/trading-dashboard-service.yaml"
    "k8s/performance-dashboard.yaml"
    "k8s/health-dashboard.yaml"
    "k8s/rss-feed-service.yaml"
    "k8s/rss-dashboard.yaml"
    "k8s/rabbitmq-deployment.yaml"
    "k8s/postgres-deployment.yaml"
    "k8s/redis-deployment.yaml"
)

# Remove old files
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "🗑️  Removing: $file"
        rm "$file"
    fi
done

echo ""
echo "✅ Cleanup completed!"
echo "📋 New consolidated structure:"
echo "   k8s/core/namespace.yaml"
echo "   k8s/infrastructure/database.yaml"
echo "   k8s/infrastructure/rabbitmq.yaml"
echo "   k8s/services/core-services.yaml"
echo "   k8s/services/dashboard-services.yaml"
echo "   k8s/templates/job-template.yaml"
echo "" 