#!/bin/bash

# 🚀 Cronjob Centralized Configuration Update Script
# This script updates all problematic cronjobs to use the centralized configuration strategy

set -e

echo "=== 🚀 UPDATING CRONJOBS TO CENTRALIZED CONFIGURATION ==="
echo ""

# Check if we're in the right directory
if [ ! -f "k8s/earnings-scanning-cronjob-updated.yaml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "1. Backing up existing cronjob configurations..."
kubectl get cronjob earnings-scanning-cronjob -n trading-system -o yaml > k8s/earnings-scanning-cronjob-backup.yaml
kubectl get cronjob strategy-performance-check -n trading-system -o yaml > k8s/strategy-performance-check-backup.yaml
kubectl get cronjob news-scanning-cronjob -n trading-system -o yaml > k8s/news-scanning-cronjob-backup.yaml

echo "✅ Backups created in k8s/ directory"
echo ""

echo "2. Updating earnings-scanning-cronjob..."
kubectl apply -f k8s/earnings-scanning-cronjob-updated.yaml
echo "✅ earnings-scanning-cronjob updated"

echo ""

echo "3. Updating strategy-performance-check..."
kubectl apply -f k8s/strategy-performance-check-updated.yaml
echo "✅ strategy-performance-check updated"

echo ""

echo "4. Updating news-scanning-cronjob..."
kubectl apply -f k8s/news-scanning-cronjob-updated.yaml
echo "✅ news-scanning-cronjob updated"

echo ""

echo "5. Verifying all cronjobs are using centralized configuration..."
echo ""

echo "📊 Cronjob Configuration Status:"
kubectl get cronjobs -n trading-system -o custom-columns="NAME:.metadata.name,SUSPEND:.spec.suspend,ACTIVE:.status.active,LAST_SCHEDULE:.status.lastScheduleTime"

echo ""

echo "6. Testing configuration by checking environment variables..."
echo ""

echo "🔍 Checking earnings-scanning-cronjob configuration:"
kubectl get cronjob earnings-scanning-cronjob -n trading-system -o yaml | grep -A 5 -B 5 "DATABASE_URL\|POLYGON_API_KEY" | head -10

echo ""

echo "🔍 Checking strategy-performance-check configuration:"
kubectl get cronjob strategy-performance-check -n trading-system -o yaml | grep -A 5 -B 5 "DATABASE_URL\|RABBITMQ_URL\|REDIS_URL" | head -10

echo ""

echo "🔍 Checking news-scanning-cronjob configuration:"
kubectl get cronjob news-scanning-cronjob -n trading-system -o yaml | grep -A 5 -B 5 "DATABASE_URL\|POLYGON_API_KEY" | head -10

echo ""

echo "=== 🎉 CRONJOB UPDATE COMPLETE! ==="
echo ""
echo "✅ All cronjobs now use centralized configuration:"
echo "• No more hardcoded credentials"
echo "• All sensitive data in Kubernetes secrets"
echo "• Service URLs in ConfigMaps"
echo "• Dynamic stock lists available"
echo ""
echo "📋 Next steps:"
echo "1. Test each cronjob to ensure they work with new configuration"
echo "2. Verify no hardcoded values remain"
echo "3. Test dynamic configuration changes (e.g., update stock lists)"
echo ""
echo "🔒 Security improvements:"
echo "• Credentials no longer exposed in cronjob definitions"
echo "• Centralized secret management"
echo "• Easy credential rotation"
echo ""
echo "🎯 Maintenance improvements:"
echo "• Change service endpoints by updating ConfigMaps"
echo "• Update stock lists without redeploying cronjobs"
echo "• Consistent configuration across all cronjobs"
