#!/bin/bash
"""
Quick Setup Script for Optimized Trading System Monitoring
Sets up port forwarding and starts monitoring
"""

echo "🚀 Setting up Optimized Trading System Monitoring..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "simplified_system_monitor.py" ]; then
    echo "❌ Please run this script from the trading directory"
    exit 1
fi

# Kill existing port forwards
echo "🔄 Cleaning up existing port forwards..."
pkill -f "kubectl port-forward.*strategy-service" 2>/dev/null || true

# Set up port forwarding
echo "🔌 Setting up port forwarding for strategy service..."
kubectl port-forward -n trading-system svc/strategy-service 11001:80 &
PORT_FORWARD_PID=$!

# Wait for port forward to establish
echo "⏳ Waiting for port forward to establish..."
sleep 3

# Test connection
echo "🔍 Testing connection..."
if curl -s http://localhost:11001/ > /dev/null; then
    echo "✅ Port forward established successfully"
else
    echo "❌ Port forward failed. Please check Kubernetes status."
    kill $PORT_FORWARD_PID 2>/dev/null || true
    exit 1
fi

# Run monitoring
echo "📊 Starting monitoring..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Run the monitoring script
python3 simplified_system_monitor.py continuous 5

# Cleanup on exit
echo ""
echo "🧹 Cleaning up..."
kill $PORT_FORWARD_PID 2>/dev/null || true
echo "✅ Cleanup complete"


















