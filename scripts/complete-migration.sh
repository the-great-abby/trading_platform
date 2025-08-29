#!/bin/bash

# Complete Database Migration Script
# Shuts down internal databases and ensures all services use external databases

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  check-status     - Check current database usage status"
    echo "  update-configs   - Update remaining service configurations"
    echo "  shutdown-internal - Shutdown internal databases"
    echo "  restart-services - Restart services to use new databases"
    echo "  complete         - Execute complete migration process"
    echo
    echo "Examples:"
    echo "  $0 check-status"
    echo "  $0 complete"
}

# Function to check current database usage status
check_status() {
    log "🔍 Checking current database usage status..."
    
    echo
    echo "📊 Internal Database Status:"
    kubectl get pods -n trading-system | grep -E "(timescaledb|postgres-vector-storage|redis)" || echo "No internal databases found"
    
    echo
    echo "📊 External Database Port Forwards:"
    if lsof -i :11150 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ TimescaleDB External: localhost:11150${NC}"
    else
        echo -e "${RED}❌ TimescaleDB External: localhost:11150 (INACTIVE)${NC}"
    fi
    
    if lsof -i :11151 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Vector Storage External: localhost:11151${NC}"
    else
        echo -e "${RED}❌ Vector Storage External: localhost:11151 (INACTIVE)${NC}"
    fi
    
    if lsof -i :11152 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Apache AGE External: localhost:11152${NC}"
    else
        echo -e "${RED}❌ Apache AGE External: localhost:11152 (INACTIVE)${NC}"
    fi
    
    if lsof -i :11153 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Regular PostgreSQL External: localhost:11153${NC}"
    else
        echo -e "${RED}❌ Regular PostgreSQL External: localhost:11153 (INACTIVE)${NC}"
    fi
    
    echo
    echo "📊 Service Database URL Status:"
    echo "Checking key services for external database URLs..."
    
    # Check a few key services
    local services=(
        "services/unified-analytics-dashboard/main.py"
        "services/unified-trading-dashboard/main.py"
        "services/unified-news-dashboard/main.py"
    )
    
    for service in "${services[@]}"; do
        if [ -f "$service" ]; then
            echo -n "  $service: "
            if grep -q "localhost:11" "$service"; then
                echo -e "${GREEN}✅ Using external databases${NC}"
            else
                echo -e "${RED}❌ Still using internal databases${NC}"
            fi
        fi
    done
}

# Function to update remaining service configurations
update_configs() {
    log "🔧 Updating remaining service configurations..."
    
    # Create backup directory
    local backup_dir="backup/service-configs-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # List of services that might still need updating
    local services=(
        "services/background-vectorization-service/main.py"
        "services/architecture-vectorizer/main.py"
        "services/ai-stock-dashboard/main.py"
    )
    
    for service in "${services[@]}"; do
        if [ -f "$service" ]; then
            log "🔧 Updating $service..."
            
            # Backup original
            cp "$service" "$backup_dir/"
            
            # Update database URLs
            sed -i.bak 's|postgres-vector-storage:80|localhost:11151|g' "$service"
            sed -i.bak 's|postgres-vector-storage:11006|localhost:11151|g' "$service"
            sed -i.bak 's|timescaledb\.trading-system\.svc\.cluster\.local|localhost:11150|g' "$service"
            
            # Remove backup files
            rm -f "$service.bak"
            
            success "✅ Updated $service"
        fi
    done
    
    success "✅ Service configurations updated"
}

# Function to shutdown internal databases
shutdown_internal() {
    log "🛑 Shutting down internal databases..."
    
    # Scale down internal database deployments
    log "📊 Scaling down TimescaleDB..."
    kubectl scale deployment timescaledb --replicas=0 -n trading-system
    
    log "📊 Scaling down Vector Storage..."
    kubectl scale deployment postgres-vector-storage --replicas=0 -n trading-system
    
    log "📊 Scaling down Redis..."
    kubectl scale deployment redis --replicas=0 -n trading-system
    
    # Wait for pods to terminate
    log "⏳ Waiting for internal database pods to terminate..."
    kubectl wait --for=delete pod -l app=timescaledb -n trading-system --timeout=60s || true
    kubectl wait --for=delete pod -l app=postgres-vector-storage -n trading-system --timeout=60s || true
    kubectl wait --for=delete pod -l app=redis -n trading-system --timeout=60s || true
    
    success "✅ Internal databases shut down"
}

# Function to restart services to use new databases
restart_services() {
    log "🔄 Restarting services to use new external databases..."
    
    # List of services to restart
    local services=(
        "unified-analytics-dashboard"
        "unified-trading-dashboard"
        "unified-news-dashboard"
        "background-vectorization-service"
        "architecture-vectorizer"
        "ai-stock-dashboard"
    )
    
    for service in "${services[@]}"; do
        log "🔄 Restarting $service..."
        kubectl rollout restart deployment "$service" -n trading-system || warning "⚠️ Could not restart $service"
    done
    
    # Wait for rollouts to complete
    log "⏳ Waiting for service rollouts to complete..."
    for service in "${services[@]}"; do
        kubectl rollout status deployment "$service" -n trading-system --timeout=300s || warning "⚠️ Rollout timeout for $service"
    done
    
    success "✅ Services restarted"
}

# Function to execute complete migration process
complete() {
    log "🚀 Starting complete migration process..."
    
    check_status
    echo
    read -p "Continue with migration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Migration cancelled by user"
        exit 0
    fi
    
    update_configs
    shutdown_internal
    restart_services
    
    log "⏳ Waiting for services to stabilize..."
    sleep 30
    
    check_status
    
    success "🎉 Complete migration process finished!"
    echo
    echo "📋 Next Steps:"
    echo "1. Verify all services are running correctly"
    echo "2. Test database connections from services"
    echo "3. Monitor application logs for any errors"
    echo "4. Consider removing internal database PVCs if no longer needed"
}

# Main script logic
case "${1:-}" in
    check-status)
        check_status
        ;;
    update-configs)
        update_configs
        ;;
    shutdown-internal)
        shutdown_internal
        ;;
    restart-services)
        restart_services
        ;;
    complete)
        complete
        ;;
    *)
        usage
        exit 1
        ;;
esac
