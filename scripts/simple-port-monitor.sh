#!/bin/bash

# Simple Port Monitor - Continuously monitors and restarts failed port forwards
# This script runs as a daemon and automatically restarts failed port forwarding

set -e

echo "🚀 Starting Simple Port Monitor (Daemon Mode)..."
echo "📋 This will continuously monitor and restart failed port forwards"
echo "🔌 Monitoring ports: 11113, 11114, 11115, 11102, 11379, 11180, 11181, 11182"
echo ""

# Configuration
NAMESPACE="trading-system"
LOG_DIR="port_monitor_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MONITOR_INTERVAL=30  # Check every 30 seconds

# Create log directory
mkdir -p "$LOG_DIR"

# Service configurations (external_port:service_name:internal_port)
SERVICES=(
    "11113:unified-news-dashboard:80"
    "11114:unified-analytics-dashboard:80"
    "11115:unified-trading-dashboard:80"
    "11102:backtest-api:11101"
    "11379:redis:6379"
    "11180:postgres-vector-storage:80"
    "11181:timescaledb:5432"
    "11182:rabbitmq:5672"
)

# Function to log events
log_event() {
    local level=$1
    local message=$2
    local service_name=${3:-"system"}
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] [$service_name] $message" | tee -a "$LOG_DIR/port_monitor_$TIMESTAMP.log"
}

# Function to check if port is listening
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port is listening
    else
        return 1  # Port is not listening
    fi
}

# Function to start port forward for a service
start_port_forward() {
    local external_port=$1
    local service_name=$2
    local internal_port=$3
    
    log_event "INFO" "Starting port forward: localhost:$external_port → $service_name:$internal_port" "$service_name"
    
    # Kill any existing port forward for this service
    pkill -f "kubectl port-forward.*$service_name" || true
    sleep 1
    
    # Start new port forward
    kubectl port-forward service/$service_name $external_port:$internal_port -n $NAMESPACE >/dev/null 2>&1 &
    local pid=$!
    
    # Wait and check if it's working
    sleep 5
    if check_port $external_port; then
        log_event "SUCCESS" "Port forward started successfully (PID: $pid)" "$service_name"
        return 0
    else
        log_event "ERROR" "Port forward failed to start" "$service_name"
        return 1
    fi
}

# Function to check and restart failed port forwards
check_and_restart() {
    local any_restarts=false
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r external_port service_name internal_port <<< "$service_config"
        
        if ! check_port $external_port; then
            log_event "WARNING" "Port forward down for $service_name (port $external_port) - restarting..." "$service_name"
            if start_port_forward $external_port $service_name $internal_port; then
                log_event "SUCCESS" "Successfully restarted port forward for $service_name" "$service_name"
                any_restarts=true
            else
                log_event "ERROR" "Failed to restart port forward for $service_name" "$service_name"
            fi
        fi
    done
    
    if $any_restarts; then
        log_event "INFO" "Port forward status check completed - some services were restarted" "monitor"
    else
        log_event "INFO" "Port forward status check completed - all services healthy" "monitor"
    fi
}

# Function to show current status
show_status() {
    echo ""
    echo "📊 Current Port Forward Status:"
    echo "================================"
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r external_port service_name internal_port <<< "$service_config"
        
        if check_port $external_port; then
            echo "✅ $service_name: localhost:$external_port → $service_name:$internal_port"
        else
            echo "❌ $service_name: localhost:$external_port (NOT LISTENING)"
        fi
    done
    echo ""
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Port Monitor..."
    log_event "INFO" "Port Monitor shutting down" "monitor"
    
    # Don't kill the port forwards - let them keep running
    # Just exit the monitor
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Initial setup - start all port forwards
echo "🚀 Initial setup: Starting all port forwards..."
for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r external_port service_name internal_port <<< "$service_config"
    start_port_forward $external_port $service_name $internal_port
done

# Show initial status
show_status

echo "🔍 Port Monitor is now running in daemon mode..."
echo "📊 Checking port forwards every $MONITOR_INTERVAL seconds..."
echo "📝 Logs saved to: $LOG_DIR/port_monitor_$TIMESTAMP.log"
echo "🛑 Press Ctrl+C to stop monitoring (port forwards will continue running)"
echo ""

# Main monitoring loop
while true; do
    check_and_restart
    sleep $MONITOR_INTERVAL
done





