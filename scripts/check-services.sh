#!/bin/bash

# Service status checker for trading system
# Checks all services in the 11000-12000 port range

echo "🔍 Checking status of all trading system services..."
echo ""

# Function to check service status
check_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local description=$4
    
    echo -n "📊 $description (localhost:$port): "
    
    if curl -s --max-time 5 "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo "✅ ONLINE"
    else
        echo "❌ OFFLINE"
    fi
}

# Check dashboards
echo "📊 DASHBOARDS:"
check_service "performance-dashboard" 11000 "/health" "Performance Dashboard"
check_service "trading-dashboard" 11001 "/" "Trading Dashboard"
check_service "health-dashboard" 11002 "/health" "Health Dashboard"
check_service "comprehensive-dashboard" 11003 "/health" "Comprehensive Dashboard"

echo ""
echo "🔌 APIs:"
check_service "backtest-api" 11010 "/health" "Backtest API"
check_service "public-api" 11011 "/health" "Public API"
check_service "strategy-service" 11012 "/health" "Strategy Service"
check_service "analytics-service" 11013 "/health" "Analytics Service"

echo ""
echo "⚙️  CORE SERVICES:"
check_service "order-service" 11020 "/health" "Order Service"
check_service "portfolio-service" 11021 "/health" "Portfolio Service"
check_service "risk-service" 11022 "/health" "Risk Service"
check_service "trading-service" 11023 "/health" "Trading Service"

echo ""
echo "📈 DATA SERVICES:"
check_service "market-data-service" 11030 "/health" "Market Data Service"
check_service "backtest-request-service" 11031 "/health" "Backtest Request Service"
check_service "report-viewer-service" 11032 "/health" "Report Viewer Service"
check_service "notification-service" 11033 "/health" "Notification Service"

echo ""
echo "🤖 AI SERVICES:"
check_service "llm-service" 11050 "/health" "LLM Service"
check_service "strategy-performance-monitor" 11051 "/health" "Strategy Performance Monitor"
check_service "llm-proxy" 12001 "/api/v1/health" "Ollama LLM Proxy"

echo ""
echo "🗄️  INFRASTRUCTURE:"
echo -n "📊 PostgreSQL (localhost:11040): "
if nc -z localhost 11040 2>/dev/null; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

echo -n "📊 RabbitMQ (localhost:11041): "
if nc -z localhost 11041 2>/dev/null; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

echo -n "📊 Redis (localhost:11042): "
if nc -z localhost 11042 2>/dev/null; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

echo -n "📊 Ollama (localhost:11043): "
if curl -s --max-time 5 "http://localhost:11043/api/tags" > /dev/null 2>&1; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

echo ""
echo "💡 Quick access URLs:"
echo "  Performance Dashboard: http://localhost:11000/dashboard"
echo "  Trading Dashboard:     http://localhost:11001/"
echo "  Health Dashboard:      http://localhost:11002/"
echo "  Backtest API:          http://localhost:11010/" 