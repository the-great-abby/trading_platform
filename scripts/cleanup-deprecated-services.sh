#!/bin/bash

# Cleanup Deprecated Services Script
# This script removes deprecated services from the trading system

echo "🏴‍☠️ Cleaning up deprecated services, Captain Abby!"

# Check current status
echo "📋 Current postgres services:"
kubectl get pods -n trading-system | grep postgres
echo ""

echo "📋 Current postgres services:"
kubectl get services -n trading-system | grep postgres
echo ""

# Confirm with user
read -p "Do you want to remove the deprecated postgres-dev service? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing deprecated postgres-dev service..."
    
    # Remove postgres-dev deployment
    kubectl delete deployment postgres-dev -n trading-system 2>/dev/null || echo "✅ postgres-dev deployment not found"
    
    # Remove postgres-dev service
    kubectl delete service postgres-dev -n trading-system 2>/dev/null || echo "✅ postgres-dev service not found"
    
    # Check for persistent volumes
    echo "📋 Checking for persistent volumes..."
    kubectl get pvc -n trading-system | grep postgres-dev || echo "No postgres-dev PVCs found"
    
    echo ""
    echo "✅ Cleanup completed!"
    echo ""
    echo "📋 Remaining postgres services:"
    kubectl get pods -n trading-system | grep postgres
    echo ""
    kubectl get services -n trading-system | grep postgres
    
else
    echo "⏹️  Cleanup cancelled by user"
fi

echo ""
echo "📊 Current database architecture:"
echo "✅ TimescaleDB (Primary) - timescaledb.trading-system.svc.cluster.local:5432"
echo "✅ Vector Storage - postgres-vector-storage.trading-system.svc.cluster.local:80"
echo "✅ Redis (Cache) - redis.trading-system.svc.cluster.local:6379"
echo ""
echo "🔗 All services use: postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot"





