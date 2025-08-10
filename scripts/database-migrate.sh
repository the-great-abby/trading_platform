#!/bin/bash

# Database Migration Script for Trading System
# This script runs Alembic migrations safely

set -e

# Configuration
MIGRATION_LOG="backup/migration_log_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$MIGRATION_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$MIGRATION_LOG" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$MIGRATION_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$MIGRATION_LOG"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS] <command>"
    echo
    echo "Commands:"
    echo "  current     Show current migration version"
    echo "  history     Show migration history"
    echo "  upgrade     Run all pending migrations"
    echo "  downgrade   Downgrade to a specific revision"
    echo "  stamp       Mark database as being at a specific revision"
    echo "  check       Check if migrations are up to date"
    echo "  backup      Create backup before migration"
    echo
    echo "Options:"
    echo "  -f, --force     Force migration without confirmation"
    echo "  -d, --dry-run   Show what would be migrated without actually doing it"
    echo "  -h, --help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 current"
    echo "  $0 upgrade"
    echo "  $0 --dry-run upgrade"
    echo "  $0 downgrade 65a77fa65587"
}

# Parse command line arguments
FORCE=false
DRY_RUN=false
COMMAND=""
REVISION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            else
                REVISION="$1"
            fi
            shift
            ;;
    esac
done

# Check if command is provided
if [ -z "$COMMAND" ]; then
    error "No command specified"
    usage
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Check if the database pod is running
log "Checking database pod status..."
if ! kubectl get pod -n trading-system -l app=timescaledb -o jsonpath='{.items[0].status.phase}' | grep -q "Running"; then
    error "TimescaleDB pod is not running"
    exit 1
fi

# Get database pod name
DB_POD=$(kubectl get pod -n trading-system -l app=timescaledb -o jsonpath='{.items[0].metadata.name}')

if [ -z "$DB_POD" ]; then
    error "Could not find TimescaleDB pod"
    exit 1
fi

log "Found database pod: $DB_POD"

# Create migration log directory
mkdir -p backup

# Function to run alembic command
run_alembic() {
    local cmd="$1"
    log "Running: alembic $cmd"
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN - Would execute: alembic $cmd"
        return 0
    fi
    
    kubectl exec -n trading-system "$DB_POD" -- bash -c "
        cd /tmp && 
        export DATABASE_URL='postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot' &&
        alembic $cmd
    "
}

# Function to create backup before migration
create_backup() {
    log "Creating backup before migration..."
    ./scripts/database-backup.sh
}

# Handle different commands
case "$COMMAND" in
    current)
        log "Checking current migration version..."
        run_alembic "current"
        ;;
        
    history)
        log "Showing migration history..."
        run_alembic "history"
        ;;
        
    check)
        log "Checking if migrations are up to date..."
        run_alembic "check"
        ;;
        
    upgrade)
        log "Running database migrations..."
        
        if [ "$DRY_RUN" = false ] && [ "$FORCE" = false ]; then
            echo
            warning "This will modify the database schema!"
            read -p "Do you want to create a backup first? (yes/no): " -r
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                create_backup
            fi
        fi
        
        run_alembic "upgrade head"
        success "Database migrations completed!"
        ;;
        
    downgrade)
        if [ -z "$REVISION" ]; then
            error "Revision required for downgrade command"
            usage
            exit 1
        fi
        
        log "Downgrading to revision: $REVISION"
        
        if [ "$DRY_RUN" = false ] && [ "$FORCE" = false ]; then
            echo
            warning "This will downgrade the database schema!"
            warning "This may result in data loss!"
            read -p "Are you sure you want to continue? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                log "Downgrade cancelled by user"
                exit 0
            fi
        fi
        
        run_alembic "downgrade $REVISION"
        success "Database downgrade completed!"
        ;;
        
    stamp)
        if [ -z "$REVISION" ]; then
            error "Revision required for stamp command"
            usage
            exit 1
        fi
        
        log "Stamping database at revision: $REVISION"
        run_alembic "stamp $REVISION"
        success "Database stamped at revision: $REVISION"
        ;;
        
    backup)
        create_backup
        ;;
        
    *)
        error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac

if [ "$DRY_RUN" = false ]; then
    success "Migration command completed!"
    log "Migration log saved to: $MIGRATION_LOG"
fi


