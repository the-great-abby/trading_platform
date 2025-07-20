#!/bin/bash

# Robust Port Forwarding Script
# Continuously restarts port forwarding when it fails

set -e

NAMESPACE="trading-system"
LOG_FILE="/tmp/robust-port-forward.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    lsof -i :$port > /dev/null 2>&1
}

# Function to kill existing port forwards
kill_port_forwards() {
    log "🔄 Stopping existing port forwards..."
    pkill -f "kubectl port-forward" || true
    sleep 2
}

# Function to start port forward with retry
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local container_port=$3
    local max_retries=5
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        log "🚀 Starting $service_name on port $local_port (attempt $((retry_count + 1))/$max_retries)"
        
        # Kill any existing port forward for this port
        if is_port_in_use $local_port; then
            log "⚠️  Port $local_port is in use, killing existing process..."
            lsof -ti :$local_port | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        
        # Start port forward
        kubectl port-forward -n "$NAMESPACE" "svc/$service_name" "$local_port:$container_port" >> "$LOG_FILE" 2>&1 &
        local pid=$!
        
        # Wait a moment for it to start
        sleep 3
        
        # Check if it's working
        if is_port_in_use $local_port; then
            log "✅ $service_name started successfully (PID: $pid)"
            return 0
        else
            log "❌ $service_name failed to start, retrying..."
            kill $pid 2>/dev/null || true
            retry_count=$((retry_count + 1))
            sleep 2
        fi
    done
    
    log "❌ Failed to start $service_name after $max_retries attempts"
    return 1
}

# Function to monitor and restart failed port forwards
monitor_port_forwards() {
    log "🔍 Starting port forward monitoring..."
    
    # Define services
    services=(
        "performance-dashboard:11000:80"
        "trading-dashboard-service:11001:8000"
        "backtest-request-service:11031:80"
        "health-dashboard:11002:80"
    )
    
    # Start initial port forwards
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port container_port <<< "$service_config"
        start_port_forward "$service_name" "$local_port" "$container_port"
    done
    
    log "✅ All port forwards started!"
    log "📊 Performance Dashboard: http://localhost:11000/dashboard"
    log "📈 Trading Dashboard: http://localhost:11001/"
    log "🔧 Backtest Request: http://localhost:11031/"
    log "🏥 Health Dashboard: http://localhost:11002/dashboard"
    
    # Monitor and restart failed port forwards
    while true; do
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name local_port container_port <<< "$service_config"
            
            if ! is_port_in_use $local_port; then
                log "🔄 Port $local_port is down, restarting $service_name..."
                start_port_forward "$service_name" "$local_port" "$container_port"
            fi
        done
        
        # Check every 10 seconds
        sleep 10
    done
}

# Function to stop all port forwarding
stop_all_port_forwards() {
    log "🛑 Stopping all port forwarding..."
    pkill -f "kubectl port-forward" || true
    log "✅ All port forwarding stopped"
}

# Handle script termination
trap stop_all_port_forwards EXIT INT TERM

# Main execution
case "${1:-monitor}" in
    "start")
        log "🚀 Starting robust port forwarding..."
        kill_port_forwards
        monitor_port_forwards
        ;;
    "stop")
        stop_all_port_forwards
        ;;
    "status")
        echo "🔍 Port forwarding status:"
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name local_port container_port <<< "$service_config"
            if is_port_in_use $local_port; then
                echo "✅ $service_name (localhost:$local_port) - ONLINE"
            else
                echo "❌ $service_name (localhost:$local_port) - OFFLINE"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        echo "  start  - Start robust port forwarding with auto-restart"
        echo "  stop   - Stop all port forwarding"
        echo "  status - Show current port forwarding status"
        exit 1
        ;;
esac 