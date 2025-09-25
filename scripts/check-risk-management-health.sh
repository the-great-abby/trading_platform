#!/bin/bash

# Risk Management Service Health Check
# Comprehensive health check script for the risk management framework

set -euo pipefail

# Configuration
NAMESPACE="trading"
SERVICE_NAME="risk-management-service"
HEALTH_CHECK_TIMEOUT="30s"
PORT_FORWARD_PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
}

# Check namespace exists
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
}

# Check if service exists
check_service_exists() {
    if ! kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" &> /dev/null; then
        log_error "Service $SERVICE_NAME does not exist in namespace $NAMESPACE"
        exit 1
    fi
}

# Check pod status
check_pod_status() {
    log_info "Checking pod status..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=risk-management-service --no-headers)
    
    if [ -z "$pods" ]; then
        log_error "No pods found for risk management service"
        return 1
    fi
    
    local running_pods=0
    local total_pods=0
    
    while IFS= read -r line; do
        total_pods=$((total_pods + 1))
        local pod_name
        pod_name=$(echo "$line" | awk '{print $1}')
        local status
        status=$(echo "$line" | awk '{print $3}')
        
        if [ "$status" = "Running" ]; then
            running_pods=$((running_pods + 1))
            log_success "Pod $pod_name is running"
        else
            log_warning "Pod $pod_name is in state: $status"
        fi
    done <<< "$pods"
    
    log_info "Pod status: $running_pods/$total_pods pods running (resource-constrained: expecting 1)"
    
    if [ "$running_pods" -eq 0 ]; then
        log_error "No pods are running"
        return 1
    fi
    
    if [ "$running_pods" -gt 1 ]; then
        log_warning "More than 1 pod running (resource-constrained deployment expects 1)"
    fi
    
    return 0
}

# Check service endpoints
check_service_endpoints() {
    log_info "Checking service endpoints..."
    
    local endpoints
    endpoints=$(kubectl get endpoints "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}')
    
    if [ -z "$endpoints" ]; then
        log_error "No endpoints found for service $SERVICE_NAME"
        return 1
    fi
    
    local endpoint_count
    endpoint_count=$(echo "$endpoints" | wc -w)
    log_success "Service has $endpoint_count endpoint(s): $endpoints"
    
    return 0
}

# Check service health endpoint
check_health_endpoint() {
    log_info "Checking service health endpoint..."
    
    # Set up port-forward
    log_info "Setting up port-forward to service..."
    kubectl port-forward service/"$SERVICE_NAME" "$PORT_FORWARD_PORT":80 -n "$NAMESPACE" &
    local port_forward_pid=$!
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Check health endpoint
    local health_response
    if health_response=$(curl -f -s --max-time 10 "http://localhost:$PORT_FORWARD_PORT/health" 2>/dev/null); then
        log_success "Health endpoint is responding"
        
        # Parse health response
        local status
        status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
        
        if [ "$status" = "success" ]; then
            log_success "Service health check passed"
            
            # Check database health
            local db_health
            db_health=$(echo "$health_response" | jq -r '.data.database.postgresql.status' 2>/dev/null || echo "unknown")
            if [ "$db_health" = "healthy" ]; then
                log_success "Database health check passed"
            else
                log_warning "Database health status: $db_health"
            fi
            
            # Check Redis health
            local redis_health
            redis_health=$(echo "$health_response" | jq -r '.data.database.redis.status' 2>/dev/null || echo "unknown")
            if [ "$redis_health" = "healthy" ]; then
                log_success "Redis health check passed"
            else
                log_warning "Redis health status: $redis_health"
            fi
            
        else
            log_error "Service health check failed with status: $status"
        fi
    else
        log_error "Health endpoint is not responding"
    fi
    
    # Clean up port-forward
    kill $port_forward_pid 2>/dev/null || true
    wait $port_forward_pid 2>/dev/null || true
}

# Check API endpoints
check_api_endpoints() {
    log_info "Checking API endpoints..."
    
    # Set up port-forward
    kubectl port-forward service/"$SERVICE_NAME" "$PORT_FORWARD_PORT":80 -n "$NAMESPACE" &
    local port_forward_pid=$!
    sleep 5
    
    # Test VaR calculation endpoint
    log_info "Testing VaR calculation endpoint..."
    local var_response
    if var_response=$(curl -f -s --max-time 10 -X POST "http://localhost:$PORT_FORWARD_PORT/api/risk/var-calculation" \
        -H "Content-Type: application/json" \
        -d '{
            "portfolio_id": "test-portfolio-123",
            "confidence_levels": [0.95, 0.99],
            "calculation_method": "historical_simulation",
            "data_period_days": 252,
            "include_expected_shortfall": true,
            "include_risk_contributions": true
        }' 2>/dev/null); then
        
        local var_status
        var_status=$(echo "$var_response" | jq -r '.status' 2>/dev/null || echo "unknown")
        
        if [ "$var_status" = "success" ]; then
            log_success "VaR calculation endpoint is working"
        else
            log_warning "VaR calculation endpoint returned status: $var_status"
        fi
    else
        log_warning "VaR calculation endpoint is not responding"
    fi
    
    # Test stress test endpoint
    log_info "Testing stress test endpoint..."
    local stress_response
    if stress_response=$(curl -f -s --max-time 10 -X POST "http://localhost:$PORT_FORWARD_PORT/api/risk/stress-test" \
        -H "Content-Type: application/json" \
        -d '{
            "portfolio_id": "test-portfolio-123",
            "scenarios": ["market_crash", "volatility_spike"],
            "include_position_impacts": true,
            "include_sector_impacts": true
        }' 2>/dev/null); then
        
        local stress_status
        stress_status=$(echo "$stress_response" | jq -r '.status' 2>/dev/null || echo "unknown")
        
        if [ "$stress_status" = "success" ]; then
            log_success "Stress test endpoint is working"
        else
            log_warning "Stress test endpoint returned status: $stress_status"
        fi
    else
        log_warning "Stress test endpoint is not responding"
    fi
    
    # Clean up port-forward
    kill $port_forward_pid 2>/dev/null || true
    wait $port_forward_pid 2>/dev/null || true
}

# Check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Get pod resource usage
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=risk-management-service --no-headers -o custom-columns=NAME:.metadata.name)
    
    while IFS= read -r pod_name; do
        if [ -n "$pod_name" ]; then
            log_info "Resource usage for pod: $pod_name"
            
            # Get resource usage
            local resource_usage
            resource_usage=$(kubectl top pod "$pod_name" -n "$NAMESPACE" --no-headers 2>/dev/null || echo "N/A")
            
            if [ "$resource_usage" != "N/A" ]; then
                echo "  $resource_usage"
            else
                log_warning "Could not get resource usage for pod $pod_name"
            fi
        fi
    done <<< "$pods"
}

# Check logs for errors
check_logs() {
    log_info "Checking logs for errors..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=risk-management-service --no-headers -o custom-columns=NAME:.metadata.name)
    
    while IFS= read -r pod_name; do
        if [ -n "$pod_name" ]; then
            log_info "Checking logs for pod: $pod_name"
            
            # Check for error logs in the last 5 minutes
            local error_logs
            error_logs=$(kubectl logs "$pod_name" -n "$NAMESPACE" --since=5m | grep -i "error\|exception\|fatal" | tail -5 || true)
            
            if [ -n "$error_logs" ]; then
                log_warning "Found error logs in pod $pod_name:"
                echo "$error_logs" | sed 's/^/  /'
            else
                log_success "No error logs found in pod $pod_name"
            fi
        fi
    done <<< "$pods"
}

# Generate health report
generate_health_report() {
    log_info "Generating health report..."
    
    local report_file="risk-management-health-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "Risk Management Service Health Report"
        echo "Generated: $(date)"
        echo "Namespace: $NAMESPACE"
        echo "Service: $SERVICE_NAME"
        echo "========================================"
        echo
        
        echo "Pod Status:"
        kubectl get pods -n "$NAMESPACE" -l app=risk-management-service
        echo
        
        echo "Service Status:"
        kubectl get services -n "$NAMESPACE" -l app=risk-management-service
        echo
        
        echo "Deployment Status:"
        kubectl get deployments -n "$NAMESPACE" -l app=risk-management-service
        echo
        
        echo "HPA Status:"
        kubectl get hpa -n "$NAMESPACE" -l app=risk-management-service
        echo
        
        echo "Resource Usage:"
        kubectl top pods -n "$NAMESPACE" -l app=risk-management-service
        echo
        
    } > "$report_file"
    
    log_success "Health report generated: $report_file"
}

# Main health check function
health_check() {
    log_info "Starting health check for risk management service..."
    
    check_kubectl
    check_namespace
    check_service_exists
    check_pod_status
    check_service_endpoints
    check_health_endpoint
    check_api_endpoints
    check_resource_usage
    check_logs
    generate_health_report
    
    log_success "Health check completed"
}

# Main script logic
case "${1:-health}" in
    health)
        health_check
        ;;
    pods)
        check_kubectl
        check_namespace
        check_pod_status
        ;;
    endpoints)
        check_kubectl
        check_namespace
        check_service_exists
        check_service_endpoints
        ;;
    api)
        check_kubectl
        check_namespace
        check_service_exists
        check_api_endpoints
        ;;
    resources)
        check_kubectl
        check_namespace
        check_resource_usage
        ;;
    logs)
        check_kubectl
        check_namespace
        check_logs
        ;;
    report)
        check_kubectl
        check_namespace
        generate_health_report
        ;;
    *)
        echo "Usage: $0 {health|pods|endpoints|api|resources|logs|report}"
        echo
        echo "Commands:"
        echo "  health     - Run complete health check (default)"
        echo "  pods       - Check pod status"
        echo "  endpoints  - Check service endpoints"
        echo "  api        - Check API endpoints"
        echo "  resources  - Check resource usage"
        echo "  logs       - Check logs for errors"
        echo "  report     - Generate health report"
        exit 1
        ;;
esac
