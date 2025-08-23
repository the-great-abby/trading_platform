#!/bin/bash

# Simple Port Forwarding for Current Trading System Services
# Manages the essential services that are actually running
# Note: Ollama service uses external port 12001 (not managed by this script)

set -e

echo "🚀 Starting Simple Port Forwarding for Trading System..."
echo "======================================================"

# Configuration
NAMESPACE="trading-system"
LOG_DIR="port_forward_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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
    echo "[$timestamp] [$level] [$service_name] $message" | tee -a "$LOG_DIR/port_forward_$TIMESTAMP.log"
}

# Function to check if port is already in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
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
    
    # Wait a moment and check if it's working
    sleep 5
    if check_port $external_port; then
        log_event "SUCCESS" "Port forward started successfully (PID: $pid)" "$service_name"
        return 0
    else
        log_event "ERROR" "Port forward failed to start - checking service status" "$service_name"
        
        # Log detailed troubleshooting info
        log_event "DEBUG" "Checking if service exists in namespace" "$service_name"
        if kubectl get service $service_name -n $NAMESPACE >/dev/null 2>&1; then
            log_event "DEBUG" "Service exists, checking endpoints" "$service_name"
            kubectl get endpoints $service_name -n $NAMESPACE >> "$LOG_DIR/port_forward_$TIMESTAMP.log" 2>&1
        else
            log_event "ERROR" "Service $service_name not found in namespace $NAMESPACE" "$service_name"
        fi
        
        return 1
    fi
}

# Function to stop all port forwards
stop_all_port_forwards() {
    echo "🛑 Stopping all port forwards..."
    pkill -f "kubectl port-forward" || true
    sleep 2
    echo "✅ All port forwards stopped"
}

# Function to cleanup ports before starting
cleanup_ports() {
    echo "🧹 Cleaning up ports before starting..."
    local ports=(11113 11114 11115 11102 11379 11180 11181 11182)
    
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            echo "   Killing processes using port $port..."
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    sleep 2
    echo "✅ Port cleanup completed"
}

# Function to show status
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
}

# Function to test all services
test_all_services() {
    echo ""
    echo "🧪 Testing all services..."
    echo "=========================="
    
    local all_healthy=true
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r external_port service_name internal_port <<< "$service_config"
        
        if [[ "$service_name" == "redis" ]]; then
            # Test Redis with Python
            if python3 -c "import redis; r = redis.from_url('redis://localhost:$external_port'); print('✅ Redis:', r.ping())" 2>/dev/null; then
                log_event "SUCCESS" "Service healthy" "$service_name"
            else
                log_event "ERROR" "Service unhealthy - Redis connection failed" "$service_name"
                all_healthy=false
            fi
        elif [[ "$service_name" == "ollama" ]]; then
            # Test Ollama
            if curl -s --connect-timeout 5 http://localhost:$external_port/api/v1/health >/dev/null 2>&1; then
                log_event "SUCCESS" "Service healthy" "$service_name"
            else
                log_event "ERROR" "Service unhealthy - Ollama health check failed" "$service_name"
                all_healthy=false
            fi
        else
            # Test HTTP services
            if curl -s --connect-timeout 5 http://localhost:$external_port/health >/dev/null 2>&1; then
                log_event "SUCCESS" "Service healthy" "$service_name"
            else
                log_event "ERROR" "Service unhealthy - HTTP health check failed" "$service_name"
                all_healthy=false
            fi
        fi
    done
    
    if $all_healthy; then
        echo ""
        echo "🎉 All services are healthy!"
    else
        echo ""
        echo "⚠️  Some services are unhealthy. Check logs above."
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Port Forward Logs:"
    echo "====================="
    
    if [ -d "$LOG_DIR" ]; then
        latest_log=$(ls -t "$LOG_DIR"/port_forward_*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            echo "📄 Latest log file: $latest_log"
            echo "📊 Last 20 entries:"
            echo "====================="
            tail -20 "$latest_log"
        else
            echo "❌ No log files found"
        fi
    else
        echo "❌ Log directory not found: $LOG_DIR"
    fi
}

# Main execution
case "${1:-start}" in
                    "start")
                    echo "🚀 Starting all port forwards..."
                    cleanup_ports
                    for service_config in "${SERVICES[@]}"; do
                        IFS=':' read -r external_port service_name internal_port <<< "$service_config"
                        start_port_forward $external_port $service_name $internal_port
                    done
        
        show_status
        test_all_services
        ;;
    "stop")
        stop_all_port_forwards
        ;;
    "restart")
        stop_all_port_forwards
        sleep 2
        $0 start
        ;;
    "status")
        show_status
        ;;
    "test")
        test_all_services
        ;;
    "logs")
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all port forwards"
        echo "  stop    - Stop all port forwards"
        echo "  restart - Restart all port forwards"
        echo "  status  - Show current status"
        echo "  test    - Test all services"
        echo "  logs    - Show troubleshooting logs"
        exit 1
        ;;
esac

echo ""
echo "💡 Tips:"
        echo "  - Run '$0 status' to check current status"
        echo "  - Run '$0 test' to test all services"
        echo "  - Run '$0 logs' to view troubleshooting logs"
        echo "  - Run '$0 restart' if services become unresponsive"
        echo "  - Add this script to your startup process for consistency" 