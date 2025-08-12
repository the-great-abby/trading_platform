#!/bin/bash

# 🏴‍☠️ Trading System Status Check Script
# This script checks the status of all critical services

echo "🏴‍☠️ CAPTAIN ABBY'S TRADING SYSTEM STATUS CHECK 🏴‍☠️"
echo "=================================================="
echo ""

# Check critical infrastructure services
echo "📊 CRITICAL INFRASTRUCTURE SERVICES:"
echo "-----------------------------------"
kubectl get pods -n trading-system | grep -E "(timescaledb|redis|rabbitmq)" | while read line; do
    echo "  $line"
done
echo ""

# Check monitoring services
echo "📈 MONITORING SERVICES:"
echo "----------------------"
kubectl get pods -n trading-system | grep -E "(prometheus|grafana|infrastructure-metrics)" | while read line; do
    echo "  $line"
done
echo ""

# Check core trading services
echo "💼 CORE TRADING SERVICES:"
echo "------------------------"
kubectl get pods -n trading-system | grep -E "(trading-engine|strategy-service|market-data-service)" | while read line; do
    echo "  $line"
done
echo ""

# Check important services
echo "⚡ IMPORTANT SERVICES:"
echo "---------------------"
kubectl get pods -n trading-system | grep -E "(unified-analytics|unified-news|llm-proxy|backtest-api|data-analysis)" | while read line; do
    echo "  $line"
done
echo ""

# Check problematic services
echo "🚨 PROBLEMATIC SERVICES:"
echo "----------------------"
kubectl get pods -n trading-system | grep -E "(llm-service|ImagePullBackOff|CrashLoopBackOff)" | while read line; do
    echo "  $line"
done
echo ""

# Health checks
echo "🔍 HEALTH CHECKS:"
echo "----------------"
echo "  Trading Engine: $(curl -s http://localhost:11080/health 2>/dev/null | jq -r '.status // "UNREACHABLE"')"
echo "  Prometheus: $(curl -s http://localhost:11190/-/healthy 2>/dev/null | grep -o 'Prometheus Server is Healthy' || echo 'UNREACHABLE')"
echo "  Grafana: $(curl -s http://localhost:11044/api/health 2>/dev/null | jq -r '.database // "UNREACHABLE"')"
echo ""

# Port forward status
echo "🔌 PORT FORWARD STATUS:"
echo "----------------------"
ps aux | grep "kubectl port-forward" | grep -v grep | while read line; do
    echo "  $line" | awk '{print "  " $11 " " $12 " " $13}'
done
echo ""

# Resource usage
echo "📊 RESOURCE USAGE:"
echo "-----------------"
kubectl top nodes 2>/dev/null || echo "  Resource metrics not available"
echo ""

echo "🏴‍☠️ STATUS CHECK COMPLETE! 🏴‍☠️"





