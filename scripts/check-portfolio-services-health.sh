#!/bin/bash
"""
Health Check Script for Enhanced Portfolio Management Services
Comprehensive health monitoring for portfolio and risk management services
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="trading-system"
SERVICES=(
    "enhanced-portfolio-service:11180"
    "enhanced-risk-management-service:11181"
)

echo -e "${BLUE}🏥 Enhanced Portfolio Management Services Health Check${NC}"
echo "=================================================="
echo ""

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local local_port=$((port + 10000))  # Use different local port to avoid conflicts
    
    echo -e "${BLUE}🔍 Checking $service_name...${NC}"
    
    # Check if deployment exists
    if ! kubectl get deployment $service_name -n $NAMESPACE &> /dev/null; then
        echo -e "${RED}❌ Deployment $service_name not found${NC}"
        return 1
    fi
    
    # Check deployment status
    local ready_replicas=$(kubectl get deployment $service_name -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
    local desired_replicas=$(kubectl get deployment $service_name -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    
    if [ "$ready_replicas" = "$desired_replicas" ]; then
        echo -e "${GREEN}✅ Deployment: $ready_replicas/$desired_replicas replicas ready${NC}"
    else
        echo -e "${RED}❌ Deployment: $ready_replicas/$desired_replicas replicas ready (expected $desired_replicas)${NC}"
        return 1
    fi
    
    # Check service
    if ! kubectl get service $service_name -n $NAMESPACE &> /dev/null; then
        echo -e "${RED}❌ Service $service_name not found${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Service: Available${NC}"
    
    # Check pods
    local pod_count=$(kubectl get pods -l app=$service_name -n $NAMESPACE --no-headers | wc -l)
    local running_pods=$(kubectl get pods -l app=$service_name -n $NAMESPACE --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [ "$running_pods" = "$pod_count" ] && [ "$pod_count" -gt 0 ]; then
        echo -e "${GREEN}✅ Pods: $running_pods/$pod_count running${NC}"
    else
        echo -e "${RED}❌ Pods: $running_pods/$pod_count running (expected $pod_count)${NC}"
        return 1
    fi
    
    # Test HTTP endpoint
    echo -e "${YELLOW}🌐 Testing HTTP endpoint...${NC}"
    
    # Start port forward in background
    kubectl port-forward -n $NAMESPACE service/$service_name $local_port:80 &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 3
    
    # Test health endpoint
    if curl -s --max-time 10 http://localhost:$local_port/health > /dev/null; then
        echo -e "${GREEN}✅ Health endpoint: Responding${NC}"
    else
        echo -e "${RED}❌ Health endpoint: Not responding${NC}"
        kill $port_forward_pid 2>/dev/null || true
        return 1
    fi
    
    # Test API status endpoint
    if curl -s --max-time 10 http://localhost:$local_port/api/v1/status > /dev/null; then
        echo -e "${GREEN}✅ API endpoint: Responding${NC}"
    else
        echo -e "${YELLOW}⚠️  API endpoint: Not responding (may not be implemented yet)${NC}"
    fi
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    
    echo -e "${GREEN}✅ $service_name: All checks passed${NC}"
    return 0
}

# Function to check resource usage
check_resource_usage() {
    echo -e "${BLUE}📊 Resource Usage Summary${NC}"
    echo "----------------------------"
    
    for service in "${SERVICES[@]}"; do
        local service_name=$(echo $service | cut -d':' -f1)
        echo -e "${YELLOW}🔍 $service_name:${NC}"
        
        # Get resource usage
        kubectl top pods -l app=$service_name -n $NAMESPACE --no-headers 2>/dev/null || echo "  Metrics not available"
    done
    echo ""
}

# Function to check logs for errors
check_logs() {
    echo -e "${BLUE}📋 Recent Log Summary${NC}"
    echo "----------------------"
    
    for service in "${SERVICES[@]}"; do
        local service_name=$(echo $service | cut -d':' -f1)
        echo -e "${YELLOW}🔍 $service_name logs (last 10 lines):${NC}"
        
        kubectl logs -l app=$service_name -n $NAMESPACE --tail=10 2>/dev/null || echo "  No logs available"
        echo ""
    done
}

# Main health check
echo -e "${YELLOW}🚀 Starting health check...${NC}"
echo ""

# Check each service
overall_status=0
for service in "${SERVICES[@]}"; do
    local service_name=$(echo $service | cut -d':' -f1)
    local port=$(echo $service | cut -d':' -f2)
    
    if ! check_service_health $service_name $port; then
        overall_status=1
    fi
    echo ""
done

# Check resource usage
check_resource_usage

# Check logs if there are issues
if [ $overall_status -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Issues detected, checking logs...${NC}"
    check_logs
fi

# Display summary
echo -e "${BLUE}📊 Health Check Summary${NC}"
echo "========================"

if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}✅ All Enhanced Portfolio Management Services are healthy!${NC}"
    echo ""
    echo -e "${BLUE}🔧 Service URLs:${NC}"
    echo "• Enhanced Portfolio Service: http://localhost:11180"
    echo "• Enhanced Risk Management Service: http://localhost:11181"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo "• Portfolio Service: curl -s http://localhost:11180/api/v1/status"
    echo "• Risk Service: curl -s http://localhost:11181/api/v1/status"
else
    echo -e "${RED}❌ Some services are not healthy. Check the details above.${NC}"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting Commands:${NC}"
    echo "• Check deployments: kubectl get deployments -n $NAMESPACE"
    echo "• Check services: kubectl get services -n $NAMESPACE"
    echo "• Check pods: kubectl get pods -n $NAMESPACE"
    echo "• Check logs: kubectl logs -l app=enhanced-portfolio-service -n $NAMESPACE"
    echo "• Check logs: kubectl logs -l app=enhanced-risk-management-service -n $NAMESPACE"
fi

echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "• PORT_MAP.md: Port mapping and service information"
echo "• k8s/enhanced-*-service.yaml: Service configurations"
echo "• scripts/deploy-enhanced-portfolio-services.sh: Deployment script"

exit $overall_status






















