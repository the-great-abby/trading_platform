#!/bin/bash

# Port forwarding script for all trading system services
# Maps services to ports 11000-12000 range to avoid conflicts

echo "🚀 Setting up port forwarding for all trading system services..."
echo "📊 Services will be available on ports 11000-12000"
echo ""

# Kill any existing port forwarding
echo "🛑 Stopping any existing port forwarding..."
pkill -f "kubectl port-forward" || true
sleep 2

# Function to start port forwarding in background
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local service_port=$3
    local description=$4
    
    echo "🔗 Starting $description on localhost:$local_port"
    kubectl port-forward -n trading-system svc/$service_name $local_port:$service_port > /dev/null 2>&1 &
    sleep 1
}

# Main services - Ports 11000-11099
start_port_forward "performance-dashboard" 11000 80 "Performance Dashboard"
start_port_forward "trading-dashboard-service" 11001 8000 "Trading Dashboard"
start_port_forward "health-dashboard" 11002 80 "Health Dashboard"
start_port_forward "comprehensive-dashboard-service" 11003 8081 "Comprehensive Dashboard"

# API Services - Ports 11010-11019
start_port_forward "backtest-api" 11010 10001 "Backtest API"
start_port_forward "public-api" 11011 80 "Public API"
start_port_forward "strategy-service" 11012 80 "Strategy Service"
start_port_forward "analytics-service" 11013 80 "Analytics Service"

# Core Services - Ports 11020-11029
start_port_forward "order-service" 11020 80 "Order Service"
start_port_forward "portfolio-service" 11021 80 "Portfolio Service"
start_port_forward "risk-service" 11022 80 "Risk Service"
start_port_forward "trading-service" 11023 80 "Trading Service"

# Data Services - Ports 11030-11039
start_port_forward "market-data-service" 11030 80 "Market Data Service"
start_port_forward "backtest-request-service" 11031 80 "Backtest Request Service"
start_port_forward "report-viewer-service" 11032 80 "Report Viewer Service"
start_port_forward "notification-service" 11033 80 "Notification Service"

# Infrastructure Services - Ports 11040-11049
start_port_forward "postgres-dev" 11040 5432 "PostgreSQL Database"
start_port_forward "rabbitmq-service" 11041 5672 "RabbitMQ"
start_port_forward "redis-dev" 11042 6379 "Redis"
start_port_forward "ollama" 11043 11434 "Ollama LLM"
start_port_forward "grafana" 11044 3000 "Grafana Monitoring"
start_port_forward "prometheus" 11045 9090 "Prometheus Metrics"

# LLM Services - Ports 11050-11059
start_port_forward "llm-service" 11050 8008 "LLM Service"
start_port_forward "strategy-performance-monitor-service" 11051 8080 "Strategy Performance Monitor"

# External LLM Proxy - Port 12001
start_port_forward "llm-proxy" 12001 8081 "Ollama LLM Proxy"

echo ""
echo "✅ All services are now accessible on localhost:"
echo ""
echo "📊 DASHBOARDS:"
echo "  Performance Dashboard:     http://localhost:11000/dashboard"
echo "  Trading Dashboard:         http://localhost:11001/"
echo "  Health Dashboard:          http://localhost:11002/"
echo "  Comprehensive Dashboard:   http://localhost:11003/"
echo ""
echo "🔌 APIs:"
echo "  Backtest API:              http://localhost:11010/"
echo "  Public API:                http://localhost:11011/"
echo "  Strategy Service:          http://localhost:11012/"
echo "  Analytics Service:         http://localhost:11013/"
echo ""
echo "⚙️  CORE SERVICES:"
echo "  Order Service:             http://localhost:11020/"
echo "  Portfolio Service:         http://localhost:11021/"
echo "  Risk Service:              http://localhost:11022/"
echo "  Trading Service:           http://localhost:11023/"
echo ""
echo "📈 DATA SERVICES:"
echo "  Market Data Service:       http://localhost:11030/"
echo "  Backtest Request Service:  http://localhost:11031/"
echo "  Report Viewer Service:     http://localhost:11032/"
echo "  Notification Service:      http://localhost:11033/"
echo ""
echo "🗄️  INFRASTRUCTURE:"
echo "  PostgreSQL:                localhost:11040"
echo "  RabbitMQ:                  localhost:11041"
echo "  Redis:                     localhost:11042"
echo "  Ollama:                    http://localhost:11043/"
echo "  Grafana:                   http://localhost:11044/"
echo "  Prometheus:                 http://localhost:11045/"
echo ""
echo "🤖 AI SERVICES:"
echo "  LLM Service:               http://localhost:11050/"
echo "  Strategy Performance:      http://localhost:11051/"
echo "  Ollama LLM Proxy:          http://localhost:12001/"
echo ""
echo "💡 To stop all port forwarding, run: pkill -f 'kubectl port-forward'"
echo "💡 To check if services are running: kubectl get pods -n trading-system" 