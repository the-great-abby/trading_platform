#!/bin/bash

# Stable Port Forwarding Script
# Automatically restarts port forwarding when pods change

set -e

NAMESPACE="trading-system"
LOG_FILE="/tmp/port-forward.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if port forwarding is working
check_port_forward() {
    local port=$1
    local service_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start port forwarding for a service
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local container_port=$3
    
    log "Starting port forward for $service_name on localhost:$local_port"
    
    # Kill any existing port forward for this service
    pkill -f "kubectl port-forward.*$service_name" || true
    
    # Start new port forward in background
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" "$local_port:$container_port" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Wait a moment for it to start
    sleep 2
    
    # Check if it's working
    if check_port_forward "$local_port" "$service_name"; then
        log "✅ Port forward for $service_name started successfully (PID: $pid)"
        return 0
    else
        log "❌ Port forward for $service_name failed to start"
        kill $pid 2>/dev/null || true
        return 1
    fi
}

# Function to monitor and restart failed port forwards
monitor_port_forwards() {
    log "Starting port forward monitoring..."
    
    # Define services and their ports (compatible with all shells)
    services=(
        "performance-dashboard:11000:80"
        "trading-dashboard-service:11001:8000"
        "health-dashboard:11002:80"
        "backtest-api:11010:10001"
        "public-api:11011:80"
        "strategy-service:11012:80"
        "order-service:11020:80"
        "portfolio-service:11021:80"
        "risk-service:11022:80"
        "backtest-request-service:11031:80"
        "report-viewer-service:11032:80"
        "notification-service:11033:80"
    )
    
    # Start initial port forwards
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port container_port <<< "$service_config"
        start_port_forward "$service_name" "$local_port" "$container_port"
    done
    
    # Monitor and restart failed port forwards
    while true; do
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name local_port container_port <<< "$service_config"
            
            if ! check_port_forward "$local_port" "$service_name"; then
                log "🔄 Restarting port forward for $service_name (port $local_port)"
                start_port_forward "$service_name" "$local_port" "$container_port"
            fi
        done
        
        # Check every 30 seconds
        sleep 30
    done
}

# Function to stop all port forwarding
stop_all_port_forwards() {
    log "Stopping all port forwarding..."
    pkill -f "kubectl port-forward" || true
    log "All port forwarding stopped"
}

# Handle script termination
trap stop_all_port_forwards EXIT INT TERM

# Main execution
case "${1:-monitor}" in
    "start")
        log "Starting stable port forwarding..."
        monitor_port_forwards
        ;;
    "stop")
        stop_all_port_forwards
        ;;
    "status")
        echo "Port forwarding status:"
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name local_port container_port <<< "$service_config"
            if check_port_forward "$local_port" "$service_name"; then
                echo "✅ $service_name (localhost:$local_port) - ONLINE"
            else
                echo "❌ $service_name (localhost:$local_port) - OFFLINE"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        echo "  start  - Start monitoring and auto-restart port forwarding"
        echo "  stop   - Stop all port forwarding"
        echo "  status - Show current port forwarding status"
        exit 1
        ;;
esac 