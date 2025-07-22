#!/bin/bash

# Application Endpoints Status Checker
# Shows current status of all trading system services

set -e

NAMESPACE="trading-system"
LOG_FILE="/tmp/endpoints-status.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    lsof -i :$port > /dev/null 2>&1
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local health_endpoint=$3
    
    echo -e "\n${BLUE}🔍 Checking $service_name (Port: $port)${NC}"
    
    # Check if port is forwarded
    if is_port_in_use $port; then
        echo -e "  ✅ Port $port is forwarded"
        
        # Check health endpoint if provided
        if [ ! -z "$health_endpoint" ]; then
            if curl -s "$health_endpoint" > /dev/null 2>&1; then
                echo -e "  ✅ Health check passed"
            else
                echo -e "  ${RED}❌ Health check failed${NC}"
            fi
        fi
    else
        echo -e "  ${RED}❌ Port $port is not forwarded${NC}"
    fi
}

# Function to check Kubernetes service status
check_k8s_service() {
    local service_name=$1
    
    if kubectl get svc -n $NAMESPACE $service_name > /dev/null 2>&1; then
        echo -e "  ✅ Kubernetes service exists"
        
        # Check if pods are running
        local pod_count=$(kubectl get pods -n $NAMESPACE -l app=$service_name --no-headers 2>/dev/null | grep Running | wc -l)
        if [ "$pod_count" -gt 0 ]; then
            echo -e "  ✅ $pod_count pod(s) running"
        else
            echo -e "  ${YELLOW}⚠️  No running pods${NC}"
        fi
    else
        echo -e "  ${RED}❌ Kubernetes service not found${NC}"
    fi
}

# Main execution
log "🚀 Starting application endpoints status check..."

echo -e "\n${GREEN}📍 APPLICATION ENDPOINTS STATUS${NC}"
echo -e "${GREEN}================================${NC}"

# Dashboard Services
echo -e "\n${YELLOW}📊 DASHBOARD SERVICES${NC}"
echo -e "${YELLOW}=====================${NC}"

check_service_health "Performance Dashboard" "11000" "http://localhost:11000/health"
check_k8s_service "performance-dashboard"

check_service_health "Trading Dashboard" "11001" "http://localhost:11001/health"
check_k8s_service "trading-dashboard-service"

check_service_health "Health Dashboard" "11002" "http://localhost:11002/health"
check_k8s_service "health-dashboard"

check_service_health "RSS Dashboard" "11003" "http://localhost:11003/health"
check_k8s_service "rss-dashboard"

check_service_health "RSS Feed Service" "11004" "http://localhost:11004/health"
check_k8s_service "rss-feed-service"

# Trading Services
echo -e "\n${YELLOW}📈 TRADING SERVICES${NC}"
echo -e "${YELLOW}==================${NC}"

check_service_health "Backtest Request Service" "11031" "http://localhost:11031/health"
check_k8s_service "backtest-request-service"

# Check internal services (no external ports)
echo -e "\n${YELLOW}🔧 INTERNAL SERVICES${NC}"
echo -e "${YELLOW}===================${NC}"

check_k8s_service "market-data-worker"
check_k8s_service "strategy-service"
check_k8s_service "market-data-service"

# Infrastructure Services
echo -e "\n${YELLOW}🏗️  INFRASTRUCTURE SERVICES${NC}"
echo -e "${YELLOW}=========================${NC}"

check_k8s_service "postgres-dev"
check_k8s_service "redis-dev"
check_k8s_service "rabbitmq-deployment"

# Summary
echo -e "\n${GREEN}📋 SUMMARY${NC}"
echo -e "${GREEN}=========${NC}"

# Count active port forwards
active_ports=$(lsof -i :11000-11099 2>/dev/null | grep LISTEN | wc -l)
echo -e "  🔌 Active port forwards: $active_ports"

# Count running pods
running_pods=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep Running | wc -l)
echo -e "  🐳 Running pods: $running_pods"

# Count total services
total_services=$(kubectl get svc -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
echo -e "  🔗 Total services: $total_services"

echo -e "\n${BLUE}💡 Quick Commands:${NC}"
echo -e "  Start port forwarding: ${GREEN}./scripts/robust-port-forward.sh start${NC}"
echo -e "  Check status: ${GREEN}./scripts/robust-port-forward.sh status${NC}"
echo -e "  Stop port forwarding: ${GREEN}./scripts/robust-port-forward.sh stop${NC}"
echo -e "  View endpoints map: ${GREEN}cat docs/APPLICATION_ENDPOINTS_MAP.md${NC}"

log "✅ Application endpoints status check completed" 