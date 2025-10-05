#!/bin/bash
# Run Backtest with Real Market Data
# This script sets up port-forwarding and DATABASE_URL to use real historical data

set -e

echo "🚀 Setting up backtest with REAL market data..."
echo ""

# Check if TimescaleDB is running in Kubernetes
if ! kubectl get svc -n trading-system timescaledb &> /dev/null; then
    echo "❌ TimescaleDB service not found in trading-system namespace"
    echo "   Make sure Kubernetes is running and TimescaleDB is deployed"
    exit 1
fi

echo "✅ TimescaleDB service found"
echo ""

# Get database password from secret
echo "🔐 Getting database credentials..."
DB_PASSWORD=$(kubectl get secret -n trading-system trading-secrets -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Could not get database password from trading-secrets"
    exit 1
fi

echo "✅ Database credentials retrieved"
echo ""

# Check if port 5432 is already forwarded
if lsof -i :5432 &> /dev/null; then
    echo "⚠️  Port 5432 is already in use"
    echo "   Checking if it's a port-forward..."
    if ps aux | grep -v grep | grep "kubectl port-forward.*timescaledb" &> /dev/null; then
        echo "✅ Port-forward already active"
    else
        echo "❌ Port 5432 is used by another process"
        echo "   Please free up port 5432 or stop the conflicting process"
        exit 1
    fi
else
    # Start port-forward in background
    echo "🔌 Starting port-forward to TimescaleDB..."
    kubectl port-forward -n trading-system svc/timescaledb 5432:5432 > /dev/null 2>&1 &
    PF_PID=$!
    
    # Wait for port-forward to be ready
    sleep 2
    
    if ! kill -0 $PF_PID 2>/dev/null; then
        echo "❌ Port-forward failed to start"
        exit 1
    fi
    
    echo "✅ Port-forward active (PID: $PF_PID)"
fi

echo ""

# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@localhost:5432/trading"

echo "✅ DATABASE_URL configured"
echo ""

# Run the backtest
echo "📊 Running 2-year backtest with REAL market data..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 run/run_2year_automated_backtest.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Backtest complete!"
echo ""
echo "📝 Note: Port-forward is still running in the background"
echo "   To stop it: kill $(pgrep -f 'kubectl port-forward.*timescaledb')"







