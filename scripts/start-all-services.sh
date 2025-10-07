#!/bin/bash

# 🏴‍☠️ Trading System - Master Port Forward Startup Script
# Starts all essential port forwards for the trading system
# Based on current PORT_MAP.md configuration

set -e

NAMESPACE="trading-system"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🏴‍☠️ Ahoy! Starting Trading System Port Forwards..."
echo "=================================================="
echo "⏰ Time: $TIMESTAMP"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log with colors
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo "ℹ️  $1"
}

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start port forward
start_port_forward() {
    local service=$1
    local local_port=$2
    local service_port=$3
    local description=$4
    local namespace=${5:-$NAMESPACE}
    
    log_info "Starting $description on port $local_port..."
    
    # Check if port is already in use
    if check_port $local_port; then
        log_warning "$description already running on port $local_port"
        return 0
    fi
    
    # Start port forward in background
    kubectl port-forward -n $namespace service/$service $local_port:$service_port >/dev/null 2>&1 &
    local pid=$!
    
    # Wait a moment for it to start
    sleep 2
    
    # Verify it started
    if check_port $local_port; then
        log_success "$description started (PID: $pid)"
        return 0
    else
        log_error "$description failed to start"
        return 1
    fi
}

# Kill any existing port forwards (optional - comment out if you want to keep existing ones)
echo "🛑 Checking for existing port forwards..."
existing=$(ps aux | grep "kubectl port-forward" | grep -v grep | wc -l | tr -d ' ')
if [ "$existing" -gt 0 ]; then
    log_warning "Found $existing existing port forwards"
    read -p "   Kill existing port forwards? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "kubectl port-forward" || true
        sleep 2
        log_success "Killed existing port forwards"
    fi
fi

echo ""
echo "🚀 Starting Essential Services..."
echo "================================="

# Core Trading Services
start_port_forward "strategy-service" 11001 80 "Strategy Service"
start_port_forward "elliott-wave-service" 11085 8000 "Elliott Wave Service"
start_port_forward "market-data-service" 11084 11084 "Market Data Service"

# Paper Trading
start_port_forward "paper-trading-k8s-service" 11190 8080 "Paper Trading Service"

# Live Trading (in default namespace)
start_port_forward "live-trading-service" 11120 8080 "Live Trading Service" "default"

# RSS & News Services
start_port_forward "rss-feed-service" 11004 11004 "RSS Feed Service"
start_port_forward "rss-dashboard" 8080 80 "RSS Dashboard"

# Unified Dashboards
start_port_forward "unified-analytics-dashboard" 11114 80 "Unified Analytics Dashboard"
start_port_forward "unified-trading-dashboard" 11115 80 "Unified Trading Dashboard"
# Note: unified-news-dashboard deployment is scaled to 0

# Optional Services (uncomment if needed)
# start_port_forward "mcp-service" 11117 8000 "MCP Service"
# start_port_forward "enhanced-risk-management-service" 11081 80 "Risk Management Service"

echo ""
echo "🧪 Testing Services..."
echo "====================="

# Function to test service health
test_service() {
    local port=$1
    local name=$2
    local endpoint=${3:-/health}
    
    if curl -s --connect-timeout 3 http://localhost:$port$endpoint >/dev/null 2>&1; then
        log_success "$name is healthy"
        return 0
    else
        log_error "$name health check failed"
        return 1
    fi
}

# Test core services
test_service 11001 "Strategy Service"
test_service 11085 "Elliott Wave Service" "/"
test_service 11084 "Market Data Service"
test_service 11190 "Paper Trading Service"
test_service 11120 "Live Trading Service"
test_service 11004 "RSS Feed Service"
test_service 11114 "Unified Analytics Dashboard" "/"
test_service 11115 "Unified Trading Dashboard" "/"

echo ""
echo "📊 Current Port Forward Status"
echo "=============================="

# Show all active port forwards
ps aux | grep "kubectl port-forward" | grep -v grep | while read -r line; do
    # Extract port from the command
    port=$(echo "$line" | grep -oE ':[0-9]+:' | head -1 | tr -d ':')
    service=$(echo "$line" | grep -oE 'service/[^ ]+' | cut -d'/' -f2)
    pid=$(echo "$line" | awk '{print $2}')
    
    if [ -n "$port" ] && [ -n "$service" ]; then
        log_success "localhost:$port → $service (PID: $pid)"
    fi
done

echo ""
echo "🎯 Available Services:"
echo "====================="
echo ""
echo "📊 DASHBOARDS:"
echo "   Unified Analytics:       http://localhost:11114/"
echo "   Unified Trading:         http://localhost:11115/"
echo "   RSS Dashboard:           http://localhost:8080/"
echo ""
echo "⚡ TRADING SERVICES:"
echo "   Strategy Service:        http://localhost:11001/"
echo "   Elliott Wave Service:    http://localhost:11085/"
echo "   Market Data Service:     http://localhost:11084/"
echo "   Paper Trading:           http://localhost:11190/"
echo "   Live Trading:            http://localhost:11120/"
echo ""
echo "📰 NEWS & FEEDS:"
echo "   RSS Feed Service:        http://localhost:11004/"
echo ""
echo "💡 COMMANDS:"
echo "   Check status:            ps aux | grep 'kubectl port-forward' | grep -v grep"
echo "   Stop all:                pkill -f 'kubectl port-forward'"
echo "   Restart this script:     $0"
echo ""
log_success "All services started! Happy trading, matey! ⚓"

