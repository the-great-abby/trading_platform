#!/bin/bash

# Proactive Pod Monitor - Catches issues before port forwarding fails
# Usage: ./scripts/pod-monitor.sh [namespace]

NAMESPACE=${1:-trading-system}
LOG_FILE="logs/pod-monitor-$(date +%Y%m%d).log"
ALERT_FILE="logs/pod-alerts-$(date +%Y%m%d).log"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🔍 Starting proactive pod monitoring for namespace: $NAMESPACE"
echo "📝 Logs: $LOG_FILE"
echo "🚨 Alerts: $ALERT_FILE"
echo "⏰ Started at: $(date)"
echo ""

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    echo "🚨 [$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $1" | tee -a "$ALERT_FILE"
    echo "🚨 [$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $1" | tee -a "$LOG_FILE"
}

# Function to check pod health
check_pod_health() {
    local pod_name=$1
    local pod_status=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null)
    local restart_count=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null)
    local ready_status=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)
    
    echo "$pod_name|$pod_status|$restart_count|$ready_status"
}

# Function to check resource usage
check_resource_usage() {
    local pod_name=$1
    local node_name=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.spec.nodeName}' 2>/dev/null)
    
    if [ -n "$node_name" ]; then
        local cpu_usage=$(kubectl top pod "$pod_name" -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{print $2}')
        local memory_usage=$(kubectl top pod "$pod_name" -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{print $3}')
        echo "$pod_name|$node_name|$cpu_usage|$memory_usage"
    else
        echo "$pod_name|unknown|unknown|unknown"
    fi
}

# Function to check recent events
check_recent_events() {
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10 | grep -E "(Warning|Error|Failed|Killing|BackOff)" || true
}

# Function to check service endpoints
check_service_endpoints() {
    local service_name=$1
    local endpoints=$(kubectl get endpoints "$service_name" -n "$NAMESPACE" -o jsonpath='{.subsets[0].addresses[*].ip}' 2>/dev/null)
    local endpoint_count=$(echo "$endpoints" | wc -w)
    echo "$service_name|$endpoint_count|$endpoints"
}

# Main monitoring loop
while true; do
    log "=== Pod Health Check ==="
    
    # Get all pods in namespace
    pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
    
    if [ -z "$pods" ]; then
        alert "No pods found in namespace $NAMESPACE"
        sleep 30
        continue
    fi
    
    # Check each pod
    for pod in $pods; do
        health_info=$(check_pod_health "$pod")
        IFS='|' read -r pod_name status restart_count ready_status <<< "$health_info"
        
        # Check for issues
        if [ "$status" != "Running" ] && [ "$status" != "Completed" ]; then
            alert "Pod $pod_name is not running: $status"
        fi
        
        if [ "$restart_count" -gt 2 ]; then
            alert "Pod $pod_name has restarted $restart_count times"
        fi
        
        if [ "$ready_status" != "true" ] && [ "$status" = "Running" ]; then
            alert "Pod $pod_name is running but not ready"
        fi
        
        log "Pod: $pod_name | Status: $status | Restarts: $restart_count | Ready: $ready_status"
    done
    
    log "=== Resource Usage Check ==="
    for pod in $pods; do
        resource_info=$(check_resource_usage "$pod")
        IFS='|' read -r pod_name node_name cpu_usage memory_usage <<< "$resource_info"
        log "Pod: $pod_name | Node: $node_name | CPU: $cpu_usage | Memory: $memory_usage"
    done
    
    log "=== Service Endpoints Check ==="
    services=$(kubectl get services -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
    for service in $services; do
        endpoint_info=$(check_service_endpoints "$service")
        IFS='|' read -r service_name endpoint_count endpoints <<< "$endpoint_info"
        
        if [ "$endpoint_count" -eq 0 ]; then
            alert "Service $service_name has no endpoints"
        fi
        
        log "Service: $service_name | Endpoints: $endpoint_count | IPs: $endpoints"
    done
    
    log "=== Recent Events Check ==="
    recent_events=$(check_recent_events)
    if [ -n "$recent_events" ]; then
        alert "Recent problematic events detected:"
        echo "$recent_events" | while read -r event; do
            log "  $event"
        done
    else
        log "No recent problematic events"
    fi
    
    log "=== Port Forwarding Status ==="
    # Check if port forwarding processes are still running
    for port in 11000 11001 11002 11003 11010; do
        if lsof -i :$port >/dev/null 2>&1; then
            log "Port $port: ACTIVE"
        else
            alert "Port $port: INACTIVE - Port forwarding may have failed"
        fi
    done
    
    log "=== End of Check ==="
    log ""
    
    # Wait before next check
    sleep 30
done 