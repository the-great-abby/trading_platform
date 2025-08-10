#!/bin/bash

# 🏴‍☠️ POWER UP THE SHIP! 🏴‍☠️
# Space Pirate Trading System - Full Fleet Deployment

set -e

# Colors for pirate theming
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] 🏴‍☠️${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS] ⚓${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING] ⚠️${NC} $1"
}

error() {
    echo -e "${RED}[ERROR] 💀${NC} $1" >&2
}

pirate_logo() {
    echo -e "${CYAN}"
    echo "    ╔══════════════════════════════════════════════════════════════╗"
    echo "    ║                    🏴‍☠️ SPACE PIRATES 🏴‍☠️                    ║"
    echo "    ║                   Trading Fleet Deployment                   ║"
    echo "    ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    error "kubectl not found! Ye need to install it first, matey!"
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    error "Cannot connect to Kubernetes cluster! Check yer connection, captain!"
    exit 1
fi

pirate_logo

log "Ahoy, Captain! Powering up the entire trading fleet..."

# Define all required services for AI analysis functionality
REQUIRED_SERVICES=(
    "timescaledb:Database - TimescaleDB for time-series data"
    "redis:Cache - Redis for session and cache management"
    "rabbitmq:Message Queue - RabbitMQ for async processing"
    "market-data-service:Market Data - Real-time stock and options data"
    "market-data-worker:Market Data Worker - Background data processing"
    "rss-feed-service:News Feed - RSS feed aggregation and sentiment"
    "llm-proxy:AI Proxy - LLM service for AI analysis"
    "ai-analysis-service:AI Analysis - Centralized AI recommendations"
    "data-analysis-service:Data Analysis - Comprehensive data analysis"
    "data-transformation-pipeline:Data Pipeline - Data transformation"
    "postgres-vector-storage:Vector DB - Vector embeddings storage"
    "backtest-api:Backtest API - Strategy backtesting service"
    "strategy-service:Strategy Service - Strategy management"
    "trading-engine:Trading Engine - Core trading logic"
    "unified-trading-dashboard:Trading Dashboard - Main trading interface"
    "unified-analytics-dashboard:Analytics Dashboard - AI analysis interface"
    "unified-news-dashboard:News Dashboard - News and sentiment"
    "grafana:Monitoring - Grafana dashboards"
    "notification-service:Notifications - Alert and notification system"
    "trading-monitor:Trading Monitor - Real-time monitoring"
    "report-viewer-service:Report Viewer - Report generation"
)

# Define service dependencies (what needs to start first)
SERVICE_DEPENDENCIES=(
    "timescaledb:"
    "redis:"
    "rabbitmq:"
    "market-data-service:timescaledb"
    "market-data-worker:market-data-service,rabbitmq"
    "rss-feed-service:timescaledb"
    "llm-proxy:"
    "ai-analysis-service:market-data-service,llm-proxy"
    "data-analysis-service:timescaledb,data-transformation-pipeline"
    "data-transformation-pipeline:timescaledb"
    "postgres-vector-storage:timescaledb"
    "backtest-api:timescaledb"
    "strategy-service:timescaledb"
    "trading-engine:timescaledb,rabbitmq"
    "unified-trading-dashboard:backtest-api,market-data-service"
    "unified-analytics-dashboard:ai-analysis-service,data-analysis-service,postgres-vector-storage"
    "unified-news-dashboard:rss-feed-service"
    "grafana:timescaledb"
    "notification-service:timescaledb"
    "trading-monitor:trading-engine"
    "report-viewer-service:timescaledb"
)

# Function to check if a service is running
check_service_status() {
    local service_name="$1"
    local namespace="trading-system"
    
    # Check if deployment exists and is running
    if kubectl get deployment "$service_name" -n "$namespace" &>/dev/null; then
        local ready_replicas=$(kubectl get deployment "$service_name" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired_replicas=$(kubectl get deployment "$service_name" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [ "$ready_replicas" = "$desired_replicas" ] && [ "$ready_replicas" != "0" ]; then
            return 0  # Service is running
        fi
    fi
    
    return 1  # Service is not running
}

# Function to start a service
start_service() {
    local service_name="$1"
    local namespace="trading-system"
    
    log "Starting $service_name..."
    
    # Check if service YAML exists
    local yaml_file="k8s/${service_name}.yaml"
    if [ ! -f "$yaml_file" ]; then
        warning "No YAML file found for $service_name, checking for alternative names..."
        
        # Try alternative naming patterns
        local alt_files=(
            "k8s/${service_name}-deployment.yaml"
            "k8s/${service_name}-service.yaml"
            "k8s/${service_name}-minimal.yaml"
        )
        
        yaml_file=""
        for alt_file in "${alt_files[@]}"; do
            if [ -f "$alt_file" ]; then
                yaml_file="$alt_file"
                break
            fi
        done
    fi
    
    if [ -n "$yaml_file" ] && [ -f "$yaml_file" ]; then
        log "Applying $yaml_file..."
        if kubectl apply -f "$yaml_file"; then
            success "$service_name deployment applied"
        else
            error "Failed to apply $yaml_file"
            return 1
        fi
    else
        warning "No YAML file found for $service_name - it may already be deployed"
    fi
    
    # Wait for service to be ready
    log "Waiting for $service_name to be ready..."
    local timeout=120
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if check_service_status "$service_name"; then
            success "$service_name is ready!"
            return 0
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
        echo -n "."
    done
    
    error "$service_name failed to start within $timeout seconds"
    return 1
}

# Helper function to get service description
get_service_description() {
    local service_name="$1"
    for service_info in "${REQUIRED_SERVICES[@]}"; do
        IFS=':' read -r srv_name srv_desc <<< "$service_info"
        if [ "$srv_name" = "$service_name" ]; then
            echo "$srv_desc"
            return 0
        fi
    done
    echo "Unknown service"
}

# Helper function to get service dependencies
get_service_dependencies() {
    local service_name="$1"
    for dep_info in "${SERVICE_DEPENDENCIES[@]}"; do
        IFS=':' read -r dep_service dep_deps <<< "$dep_info"
        if [ "$dep_service" = "$service_name" ]; then
            echo "$dep_deps"
            return 0
        fi
    done
    echo ""
}

# Function to check dependencies
check_dependencies() {
    local service_name="$1"
    local dependencies=""
    
    # Find dependencies for this service
    for dep_info in "${SERVICE_DEPENDENCIES[@]}"; do
        IFS=':' read -r dep_service dep_deps <<< "$dep_info"
        if [ "$dep_service" = "$service_name" ]; then
            dependencies="$dep_deps"
            break
        fi
    done
    
    if [ -z "$dependencies" ]; then
        return 0  # No dependencies
    fi
    
    IFS=',' read -ra deps <<< "$dependencies"
    for dep in "${deps[@]}"; do
        dep=$(echo "$dep" | xargs)  # Trim whitespace
        if ! check_service_status "$dep"; then
            warning "$service_name depends on $dep, but $dep is not running"
            return 1
        fi
    done
    
    return 0
}

# Function to start services in dependency order
start_services_in_order() {
    local started_services=()
    local failed_services=()
    
    # Start services with no dependencies first
    for service_info in "${REQUIRED_SERVICES[@]}"; do
        IFS=':' read -r service_name service_description <<< "$service_info"
        if check_dependencies "$service_name" && [ -z "$(get_service_dependencies "$service_name")" ]; then
            if start_service "$service_name"; then
                started_services+=("$service_name")
            else
                failed_services+=("$service_name")
            fi
        fi
    done
    
    # Start remaining services
    local max_iterations=10
    local iteration=0
    
    while [ $iteration -lt $max_iterations ]; do
        local started_this_round=false
        
        for service_info in "${REQUIRED_SERVICES[@]}"; do
            IFS=':' read -r service_name service_description <<< "$service_info"
            # Skip if already started or failed
            if [[ " ${started_services[@]} " =~ " ${service_name} " ]] || [[ " ${failed_services[@]} " =~ " ${service_name} " ]]; then
                continue
            fi
            
            # Check if dependencies are met
            if check_dependencies "$service_name"; then
                if start_service "$service_name"; then
                    started_services+=("$service_name")
                    started_this_round=true
                else
                    failed_services+=("$service_name")
                fi
            fi
        done
        
        # If no services were started this round, we're done
        if [ "$started_this_round" = false ]; then
            break
        fi
        
        iteration=$((iteration + 1))
    done
    
    # Report results
    echo
    log "🏴‍☠️ Fleet Deployment Complete! 🏴‍☠️"
    echo
    
    if [ ${#started_services[@]} -gt 0 ]; then
        success "Successfully started services (${#started_services[@]}):"
        for service in "${started_services[@]}"; do
            local description=$(get_service_description "$service")
            echo -e "  ${GREEN}✅${NC} $service - $description"
        done
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        error "Failed to start services (${#failed_services[@]}):"
        for service in "${failed_services[@]}"; do
            local description=$(get_service_description "$service")
            echo -e "  ${RED}❌${NC} $service - $description"
        done
    fi
    
    echo
    log "Checking port forwarding..."
    start_port_forwarding
}

# Function to start port forwarding
start_port_forwarding() {
    log "Setting up port forwarding for dashboards..."
    
    # Kill existing port forwards
    pkill -f "kubectl port-forward" 2>/dev/null || true
    sleep 2
    
    # Start port forwarding for dashboards
    log "Starting port forwarding..."
    
    # Unified Trading Dashboard
    kubectl port-forward service/unified-trading-dashboard 11115:80 -n trading-system &
    sleep 1
    
    # Unified Analytics Dashboard
    kubectl port-forward service/unified-analytics-dashboard 11114:80 -n trading-system &
    sleep 1
    
    # Unified News Dashboard
    kubectl port-forward service/unified-news-dashboard 11113:80 -n trading-system &
    sleep 1
    
    # Grafana
    kubectl port-forward service/grafana 11044:3000 -n trading-system &
    sleep 1
    
    # Wait for port forwarding to establish
    sleep 5
    
    # Test port forwarding
    log "Testing port forwarding..."
    local ports=("11113" "11114" "11115" "11044")
    local services=("News" "Analytics" "Trading" "Grafana")
    
    for i in "${!ports[@]}"; do
        if curl -s "http://localhost:${ports[$i]}/health" >/dev/null 2>&1; then
            success "${services[$i]} Dashboard: http://localhost:${ports[$i]}/"
        else
            warning "${services[$i]} Dashboard: http://localhost:${ports[$i]}/ (may still be starting)"
        fi
    done
}

# Function to show service status
show_fleet_status() {
    echo
    log "🏴‍☠️ Current Fleet Status 🏴‍☠️"
    echo
    
    local running=0
    local total=0
    
    for service_info in "${REQUIRED_SERVICES[@]}"; do
        IFS=':' read -r service_name service_description <<< "$service_info"
        total=$((total + 1))
        if check_service_status "$service_name"; then
            echo -e "  ${GREEN}✅${NC} $service_name - $service_description"
            running=$((running + 1))
        else
            echo -e "  ${RED}❌${NC} $service_name - $service_description"
        fi
    done
    
    echo
    log "Fleet Status: $running/$total services running"
    
    if [ $running -eq $total ]; then
        success "All systems operational, Captain! The fleet is ready for action!"
    else
        warning "Some systems are offline. Consider running 'power-up-ship.sh' to deploy the fleet."
    fi
}

# Main execution
case "${1:-deploy}" in
    "deploy"|"start")
        start_services_in_order
        ;;
    "status"|"check")
        show_fleet_status
        ;;
    "ports"|"forward")
        start_port_forwarding
        ;;
    "help"|"-h"|"--help")
        echo "🏴‍☠️ Space Pirate Trading Fleet Commands 🏴‍☠️"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  deploy, start  - Deploy the entire trading fleet"
        echo "  status, check  - Check current fleet status"
        echo "  ports, forward - Start port forwarding for dashboards"
        echo "  help          - Show this help message"
        echo
        echo "Dashboard URLs (after deployment):"
        echo "  Trading Dashboard:    http://localhost:11115/"
        echo "  Analytics Dashboard:  http://localhost:11114/"
        echo "  News Dashboard:       http://localhost:11113/"
        echo "  Grafana Monitoring:   http://localhost:11044/"
        echo
        echo "Required Services for AI Analysis:"
        for service_info in "${REQUIRED_SERVICES[@]}"; do
            IFS=':' read -r service_name service_description <<< "$service_info"
            echo "  - $service_name: $service_description"
        done
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
