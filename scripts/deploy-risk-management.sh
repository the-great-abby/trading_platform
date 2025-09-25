#!/bin/bash

# Deploy Risk Management Service
# Comprehensive deployment script for the risk management framework

set -euo pipefail

# Configuration
NAMESPACE="trading"
SERVICE_NAME="risk-management-service"
DEPLOYMENT_TIMEOUT="600s"
ROLLOUT_TIMEOUT="300s"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist, creating it..."
        kubectl create namespace "$NAMESPACE"
        log_success "Created namespace $NAMESPACE"
    fi
    
    log_success "Prerequisites check completed"
}

# Deploy database components
deploy_database() {
    log_info "Deploying database components..."
    
    # Deploy PostgreSQL
    kubectl apply -f k8s/risk-management-database.yaml -n "$NAMESPACE"
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgresql-service -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    
    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis-service -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    
    log_success "Database components deployed successfully"
}

# Deploy main service
deploy_service() {
    log_info "Deploying risk management service..."
    
    # Deploy main service
    kubectl apply -f k8s/risk-management-service.yaml -n "$NAMESPACE"
    
    # Wait for deployment to be ready
    log_info "Waiting for risk management service to be ready..."
    kubectl wait --for=condition=available deployment/"$SERVICE_NAME" -n "$NAMESPACE" --timeout="$DEPLOYMENT_TIMEOUT"
    
    log_success "Risk management service deployed successfully"
}

# Deploy monitoring components
deploy_monitoring() {
    log_info "Deploying monitoring components..."
    
    # Deploy monitoring configuration
    kubectl apply -f k8s/risk-management-monitoring.yaml -n "$NAMESPACE"
    
    log_success "Monitoring components deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if the single pod is running
    local running_pods
    running_pods=$(kubectl get pods -n "$NAMESPACE" -l app=risk-management-service --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [ "$running_pods" -eq 0 ]; then
        log_error "No running pods found for risk management service"
        return 1
    fi
    
    if [ "$running_pods" -eq 1 ]; then
        log_success "Found 1 running pod for risk management service (resource-constrained deployment)"
    else
        log_warning "Found $running_pods running pods (expected 1 for resource-constrained deployment)"
    fi
    
    # Check service health
    log_info "Checking service health..."
    
    # Get service URL
    local service_url
    service_url=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$service_url" ]; then
        # Use port-forward for local testing
        log_info "Setting up port-forward for health check..."
        kubectl port-forward service/"$SERVICE_NAME" 8080:80 -n "$NAMESPACE" &
        local port_forward_pid=$!
        sleep 5
        
        # Check health endpoint
        if curl -f -s http://localhost:8080/health > /dev/null; then
            log_success "Service health check passed"
        else
            log_error "Service health check failed"
            kill $port_forward_pid 2>/dev/null || true
            return 1
        fi
        
        kill $port_forward_pid 2>/dev/null || true
    else
        # Use load balancer URL
        if curl -f -s "http://$service_url/health" > /dev/null; then
            log_success "Service health check passed"
        else
            log_error "Service health check failed"
            return 1
        fi
    fi
    
    log_success "Deployment verification completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    
    # Show pods
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -l app=risk-management-service
    echo
    
    # Show services
    echo "Services:"
    kubectl get services -n "$NAMESPACE" -l app=risk-management-service
    echo
    
    # Show deployments
    echo "Deployments:"
    kubectl get deployments -n "$NAMESPACE" -l app=risk-management-service
    echo
    
    # Show HPA
    echo "Horizontal Pod Autoscaler:"
    kubectl get hpa -n "$NAMESPACE" -l app=risk-management-service
    echo
    
    # Show network policies
    echo "Network Policies:"
    kubectl get networkpolicies -n "$NAMESPACE" -l app=risk-management-service
    echo
}

# Cleanup function
cleanup() {
    log_info "Cleaning up resources..."
    
    # Delete main service
    kubectl delete -f k8s/risk-management-service.yaml -n "$NAMESPACE" --ignore-not-found=true
    
    # Delete monitoring
    kubectl delete -f k8s/risk-management-monitoring.yaml -n "$NAMESPACE" --ignore-not-found=true
    
    # Delete database
    kubectl delete -f k8s/risk-management-database.yaml -n "$NAMESPACE" --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment of risk management service..."
    
    check_prerequisites
    deploy_database
    deploy_service
    deploy_monitoring
    verify_deployment
    show_status
    
    log_success "Risk management service deployment completed successfully!"
    echo
    log_info "To access the service:"
    echo "  kubectl port-forward service/$SERVICE_NAME 8080:80 -n $NAMESPACE"
    echo "  curl http://localhost:8080/health"
    echo
    log_info "To view logs:"
    echo "  kubectl logs -f deployment/$SERVICE_NAME -n $NAMESPACE"
    echo
    log_info "To scale the service (if needed):"
    echo "  kubectl scale deployment $SERVICE_NAME --replicas=1 -n $NAMESPACE  # Resource-constrained: max 1 replica"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    cleanup)
        cleanup
        ;;
    status)
        show_status
        ;;
    verify)
        verify_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|status|verify}"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy the risk management service (default)"
        echo "  cleanup  - Remove all deployed resources"
        echo "  status   - Show deployment status"
        echo "  verify   - Verify deployment health"
        exit 1
        ;;
esac
