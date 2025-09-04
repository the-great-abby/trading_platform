#!/bin/bash

# Fleet Status Check Script
# This script provides a quick overview of the trading system fleet status

echo "🏴‍☠️ Trading System Fleet Status Report - Captain's View"
echo "================================================================"

# Function to check service health
check_service() {
    local url=$1
    local name=$2
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo "✅ $name"
    else
        echo "❌ $name"
    fi
}

# Core Services Health Check
echo ""
echo "⚓ CRITICAL SERVICES STATUS:"
echo "----------------------------"

# Check if pods are running
echo "🏗️ Kubernetes Pods:"
kubectl get pods -n trading-system --no-headers | grep -E "(timescaledb|redis|rabbitmq|prometheus|grafana|trading-engine|strategy-service|market-data)" | while read line; do
    pod_name=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $3}')
    if [ "$status" = "Running" ]; then
        echo "  ✅ $pod_name"
    else
        echo "  ❌ $pod_name ($status)"
    fi
done

echo ""
echo "🌐 Service Endpoints:"
check_service "http://localhost:11044/api/health" "Grafana (Monitoring)"
check_service "http://localhost:11114/health" "Analytics Dashboard"
check_service "http://localhost:11113/health" "News Dashboard"

echo ""
echo "📊 FLEET STATISTICS:"
echo "--------------------"

# Count running pods
total_pods=$(kubectl get pods -n trading-system --no-headers | wc -l | tr -d ' ')
running_pods=$(kubectl get pods -n trading-system --no-headers | grep Running | wc -l | tr -d ' ')
pending_pods=$(kubectl get pods -n trading-system --no-headers | grep Pending | wc -l | tr -d ' ')
failed_pods=$(kubectl get pods -n trading-system --no-headers | grep -E "(CrashLoopBackOff|Error|ImagePullBackOff)" | wc -l | tr -d ' ')

echo "🎯 Total Pods: $total_pods"
echo "⚓ Running: $running_pods"
echo "⏳ Pending: $pending_pods"
echo "💀 Failed: $failed_pods"

# Calculate fleet health percentage
if [ "$total_pods" -gt 0 ]; then
    health_percent=$((running_pods * 100 / total_pods))
    echo "🏴‍☠️ Fleet Health: $health_percent%"
    
    if [ "$health_percent" -ge 90 ]; then
        echo "🎉 Fleet Status: EXCELLENT"
    elif [ "$health_percent" -ge 70 ]; then
        echo "⚠️ Fleet Status: GOOD"
    elif [ "$health_percent" -ge 50 ]; then
        echo "🚨 Fleet Status: NEEDS ATTENTION"
    else
        echo "💀 Fleet Status: CRITICAL"
    fi
fi

echo ""
echo "🗺️ QUICK ACCESS URLS:"
echo "---------------------"
echo "📊 Fleet Status Dashboard: http://localhost:11044/d/e9039c45-bb79-4f8a-833e-97ed7f8f3b81/fleet-status-overview-captain-s-dashboard"
echo "📈 Analytics Dashboard: http://localhost:11114/"
echo "📰 News Dashboard: http://localhost:11113/"
echo "🔧 Grafana Main: http://localhost:11044/"

echo ""
echo "🔧 RESOURCE USAGE:"
echo "------------------"
kubectl describe nodes | grep -A 5 "Allocated resources:" | grep -E "(cpu|memory)" | head -2

echo ""
echo "================================================================"
echo "🏴‍☠️ End of Fleet Status Report"











