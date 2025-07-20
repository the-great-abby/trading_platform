#!/bin/bash

# Simple Port Forwarding Script
# Starts essential services without complex monitoring

set -e

NAMESPACE="trading-system"

echo "🚀 Starting essential port forwarding..."

# Kill any existing port forwards
echo "🔄 Stopping existing port forwards..."
pkill -f "kubectl port-forward" || true
sleep 2

# Start essential services
echo "📊 Starting performance dashboard (port 11000)..."
kubectl port-forward -n "$NAMESPACE" svc/performance-dashboard 11000:80 &
PF1_PID=$!

echo "📈 Starting trading dashboard (port 11001)..."
kubectl port-forward -n "$NAMESPACE" svc/trading-dashboard-service 11001:8000 &
PF2_PID=$!

echo "🔧 Starting backtest request service (port 11031)..."
kubectl port-forward -n "$NAMESPACE" svc/backtest-request-service 11031:80 &
PF3_PID=$!

echo "🏥 Starting health dashboard (port 11002)..."
kubectl port-forward -n "$NAMESPACE" svc/health-dashboard 11002:80 &
PF4_PID=$!

# Wait a moment for services to start
sleep 3

echo ""
echo "✅ Port forwarding started!"
echo "📊 Performance Dashboard: http://localhost:11000/dashboard"
echo "📈 Trading Dashboard: http://localhost:11001/"
echo "🔧 Backtest Request: http://localhost:11031/"
echo "🏥 Health Dashboard: http://localhost:11002/dashboard"
echo ""
echo "Press Ctrl+C to stop all port forwarding"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all port forwarding..."
    kill $PF1_PID $PF2_PID $PF3_PID $PF4_PID 2>/dev/null || true
    pkill -f "kubectl port-forward" || true
    echo "✅ All port forwarding stopped"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM EXIT

# Keep script running
while true; do
    sleep 10
done 