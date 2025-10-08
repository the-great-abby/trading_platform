#!/bin/bash

# 🏴‍☠️ Quick Port Forward Restart Script
# Kills all existing port forwards and restarts them
# No questions asked - just does it!

NAMESPACE="trading-system"

echo "🏴‍☠️ Restarting all port forwards..."

# Kill all existing port forwards
echo "🛑 Stopping existing port forwards..."
pkill -f "kubectl port-forward" || true
sleep 3

echo "🚀 Starting port forwards..."

# Core Trading Services
kubectl port-forward -n $NAMESPACE service/strategy-service 11001:80 >/dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE service/elliott-wave-service 11085:8000 >/dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE service/market-data-service 11084:11084 >/dev/null 2>&1 &

# Paper Trading
kubectl port-forward -n $NAMESPACE service/paper-trading-k8s-service 11190:8080 >/dev/null 2>&1 &

# Live Trading (default namespace)
kubectl port-forward -n default service/live-trading-service 11120:8080 >/dev/null 2>&1 &

# RSS & News
kubectl port-forward -n $NAMESPACE service/rss-feed-service 11004:11004 >/dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE service/rss-dashboard 8080:80 >/dev/null 2>&1 &

# Dashboards
kubectl port-forward -n $NAMESPACE service/unified-analytics-dashboard 11114:80 >/dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE service/unified-trading-dashboard 11115:80 >/dev/null 2>&1 &

sleep 5

echo ""
echo "✅ Port forwards restarted!"
echo ""
echo "📊 Active services:"
ps aux | grep "kubectl port-forward" | grep -v grep | wc -l | xargs -I {} echo "   {} port forwards running"
echo ""
echo "💡 Quick test: curl http://localhost:11001/health"



