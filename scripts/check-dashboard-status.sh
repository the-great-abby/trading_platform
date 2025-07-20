#!/bin/bash

# Quick Dashboard Status Check

echo "🔍 Checking dashboard status..."
echo ""

# Performance Dashboard
echo "📊 Performance Dashboard (port 11000):"
if curl -s http://localhost:11000/health > /dev/null 2>&1; then
    echo "   ✅ ONLINE - http://localhost:11000/dashboard"
else
    echo "   ❌ OFFLINE"
fi

# Trading Dashboard
echo "📈 Trading Dashboard (port 11001):"
if curl -s http://localhost:11001/dashboard/health > /dev/null 2>&1; then
    echo "   ✅ ONLINE - http://localhost:11001/"
else
    echo "   ❌ OFFLINE"
fi

# Backtest Request Service
echo "🔧 Backtest Request (port 11031):"
if curl -s http://localhost:11031/health > /dev/null 2>&1; then
    echo "   ✅ ONLINE - http://localhost:11031/"
else
    echo "   ❌ OFFLINE"
fi

# Health Dashboard
echo "🏥 Health Dashboard (port 11002):"
if curl -s http://localhost:11002/health > /dev/null 2>&1; then
    echo "   ✅ ONLINE - http://localhost:11002/dashboard"
else
    echo "   ❌ OFFLINE"
fi

echo ""
echo "💡 To start all dashboards: make port-forward-all"
echo "💡 To stop all port forwarding: make port-forward-stop" 