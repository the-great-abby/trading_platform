#!/bin/bash

# Dashboard Status Checker
# Shows which dashboards are currently accessible

echo "🔍 Checking Dashboard Availability..."
echo "=================================="
echo ""

# Function to check if a service is accessible
check_service() {
    local name=$1
    local port=$2
    local path=$3
    
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${path}" > /dev/null 2>&1; then
        echo "✅ $name - http://localhost:${port}${path}"
    else
        echo "❌ $name - http://localhost:${port}${path}"
    fi
}

echo "📊 Core Monitoring Dashboards:"
check_service "Grafana" "11102" ""
check_service "Prometheus" "11101" ""
check_service "Infrastructure Metrics" "11103" "/metrics"
echo ""

echo "💼 Trading System Dashboards:"
check_service "Strategy Service" "11104" ""
check_service "Health Dashboard" "11114" ""
echo ""

echo "🔧 Additional Services (if running):"
check_service "Trading Service" "11105" ""
check_service "Order Service" "11106" ""
check_service "Portfolio Service" "11107" ""
check_service "Risk Service" "11108" ""
check_service "Market Data Service" "11109" ""
echo ""

echo "🤖 AI & Analytics Services:"
check_service "AI Analysis Service" "11110" ""
check_service "AI Stock Dashboard" "11111" ""
check_service "LLM Service" "11112" ""
check_service "Analytics Service" "11113" ""
echo ""

echo "📈 Performance Dashboards:"
check_service "Performance Dashboard" "11115" ""
check_service "Central Hub Dashboard" "11116" ""
check_service "RSS Dashboard" "11117" ""
check_service "Trading Dashboard" "11118" ""
echo ""

echo "🧪 Backtesting Services:"
check_service "Backtest API" "11119" ""
check_service "Backtest Request Service" "11120" ""
echo ""

echo "📊 Data & Processing:"
check_service "Data Processing Service" "11121" ""
check_service "Market Data Worker" "11122" ""
check_service "Postgres Vector Storage" "11123" ""
echo ""

echo "⚙️ Management Services:"
check_service "Strategy Management" "11124" ""
check_service "Order Management" "11125" ""
check_service "Signal Management" "11126" ""
check_service "Risk Management" "11127" ""
echo ""

echo "🔔 Additional Services:"
check_service "Notification Service" "11128" ""
check_service "Public API" "11129" ""
check_service "Report Viewer Service" "11130" ""
check_service "RSS Feed Service" "11131" ""
check_service "Trading Core Service" "11132" ""
check_service "Trading Ultra Service" "11133" ""
check_service "Metrics Test Service" "11134" ""
echo ""

echo "=================================="
echo "💡 Tip: Use 'kubectl port-forward service/SERVICE_NAME PORT:PORT -n trading-system &' to start additional services"
echo "💡 Tip: Use 'pkill -f kubectl' to stop all port forwarding"
echo "💡 Tip: Use './scripts/start_port_watcher.sh' to start comprehensive monitoring" 