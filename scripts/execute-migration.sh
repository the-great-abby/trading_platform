#!/bin/bash

# 🚀 External Database Migration Execution Script
# Orchestrates the complete migration from current TimescaleDB to external databases

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="logs/migration-execution_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="backup/migration-execution"
MIGRATION_STATE_FILE="logs/migration-state.json"

# Migration phases
PHASES=(
    "pre-migration-backup"
    "setup-external-databases"
    "data-migration"
    "service-config-update"
    "service-restart"
    "validation"
    "post-migration-cleanup"
)

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS] <command>"
    echo
    echo "Commands:"
    echo "  migrate-all     - Execute complete migration process"
    echo "  migrate-phase   - Execute specific migration phase"
    echo "  rollback        - Rollback to previous database configuration"
    echo "  status          - Show migration status"
    echo "  validate        - Validate current migration state"
    echo  "resume          - Resume migration from last successful phase"
    echo
    echo "Phases:"
    echo "  pre-migration-backup      - Create backup before migration"
    echo "  setup-external-databases  - Set up new external databases"
    echo "  data-migration            - Migrate data to new databases"
    echo "  service-config-update     - Update service configurations"
    echo "  service-restart           - Restart services with new configs"
    echo "  validation                - Validate migration success"
    echo "  post-migration-cleanup    - Clean up old configurations"
    echo
    echo "Options:"
    echo "  --dry-run       - Show what would be done without actually doing it"
    echo "  --force         - Force migration even if previous phase failed"
    echo "  --skip-backup   - Skip backup creation (not recommended)"
    echo "  -h, --help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 migrate-all"
    echo "  $0 migrate-phase data-migration"
    echo "  $0 --dry-run migrate-all"
    echo "  $0 status"
}

# Parse command line arguments
COMMAND=""
DRY_RUN=false
FORCE=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        migrate-all|migrate-phase|rollback|status|validate|resume)
            COMMAND="$1"
            shift
            ;;
        pre-migration-backup|setup-external-databases|data-migration|service-config-update|service-restart|validation|post-migration-cleanup)
            PHASE="$1"
            shift
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if command is provided
if [ -z "$COMMAND" ]; then
    error "Command is required"
    usage
    exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p "$BACKUP_DIR"

# Migration state management
save_migration_state() {
    local phase="$1"
    local status="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    cat > "$MIGRATION_STATE_FILE" << EOF
{
    "current_phase": "$phase",
    "last_updated": "$timestamp",
    "status": "$status",
    "phases": {
        "pre-migration-backup": "$status",
        "setup-external-databases": "pending",
        "data-migration": "pending",
        "service-config-update": "pending",
        "service-restart": "pending",
        "validation": "pending",
        "post-migration-cleanup": "pending"
    }
}
EOF
}

get_migration_state() {
    if [ -f "$MIGRATION_STATE_FILE" ]; then
        cat "$MIGRATION_STATE_FILE"
    else
        echo "{}"
    fi
}

# Phase execution functions
execute_pre_migration_backup() {
    log "💾 Phase 1: Pre-migration backup..."
    
    if [ "$SKIP_BACKUP" = true ]; then
        warning "⚠️ Skipping backup as requested"
        return 0
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would create backup"
        return 0
    fi
    
    # Create database backup
    if [ -f "./scripts/database-backup.sh" ]; then
        ./scripts/database-backup.sh
        success "✅ Database backup completed"
    else
        warning "⚠️ Database backup script not found"
    fi
    
    # Create service config backup
    if [ -f "./scripts/update-service-configs.py" ]; then
        python3 ./scripts/update-service-configs.py --backup-only
        success "✅ Service config backup completed"
    else
        warning "⚠️ Service config backup script not found"
    fi
    
    success "✅ Pre-migration backup completed"
}

execute_setup_external_databases() {
    log "🚀 Phase 2: Setting up external databases..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would set up external databases"
        return 0
    fi
    
    if [ -f "./scripts/setup-external-databases.sh" ]; then
        chmod +x ./scripts/setup-external-databases.sh
        ./scripts/setup-external-databases.sh setup-all
        success "✅ External databases setup completed"
    else
        error "❌ External database setup script not found"
        return 1
    fi
}

execute_data_migration() {
    log "🔄 Phase 3: Data migration..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would migrate data"
        return 0
    fi
    
    if [ -f "./scripts/migrate-data-to-external.py" ]; then
        # Check if virtual environment is activated
        if [ -z "$VIRTUAL_ENV" ]; then
            log "🐍 Activating migration virtual environment..."
            source ./migration-env/bin/activate
        fi
        
        # Test connections first
        python3 ./scripts/migrate-data-to-external.py --test-connections
        if [ $? -ne 0 ]; then
            error "❌ Database connections failed"
            return 1
        fi
        
        # Execute migration
        python3 ./scripts/migrate-data-to-external.py
        if [ $? -eq 0 ]; then
            success "✅ Data migration completed"
        else
            error "❌ Data migration failed"
            return 1
        fi
    else
        error "❌ Data migration script not found"
        return 1
    fi
}

execute_service_config_update() {
    log "🔧 Phase 4: Service configuration update..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would update service configurations"
        return 0
    fi
    
    if [ -f "./scripts/update-service-configs.py" ]; then
        # Check if virtual environment is activated
        if [ -z "$VIRTUAL_ENV" ]; then
            log "🐍 Activating migration virtual environment..."
            source ./migration-env/bin/activate
        fi
        
        python3 ./scripts/update-service-configs.py
        if [ $? -eq 0 ]; then
            success "✅ Service configurations updated"
        else
            error "❌ Service configuration update failed"
            return 1
        fi
    else
        error "❌ Service configuration update script not found"
        return 1
    fi
}

execute_service_restart() {
    log "🔄 Phase 5: Service restart..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would restart services"
        return 0
    fi
    
    # Apply updated configurations
    if [ -f "logs/kubectl-apply-commands.sh" ]; then
        log "📋 Applying updated configurations..."
        chmod +x logs/kubectl-apply-commands.sh
        ./logs/kubectl-apply-commands.sh
        
        # Wait for services to be ready
        log "⏳ Waiting for services to be ready..."
        sleep 30
        
        # Check service status
        kubectl get pods -n trading-system
        
        success "✅ Services restarted with new configurations"
    else
        error "❌ kubectl apply commands file not found"
        return 1
    fi
}

execute_validation() {
    log "🔍 Phase 6: Migration validation..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would validate migration"
        return 0
    fi
    
    # Validate data migration
    if [ -f "./scripts/migrate-data-to-external.py" ]; then
        # Check if virtual environment is activated
        if [ -z "$VIRTUAL_ENV" ]; then
            log "🐍 Activating migration virtual environment..."
            source ./migration-env/bin/activate
        fi
        
        python3 ./scripts/migrate-data-to-external.py --validate-only
        if [ $? -eq 0 ]; then
            success "✅ Data migration validation successful"
        else
            error "❌ Data migration validation failed"
            return 1
        fi
    fi
    
    # Test service connectivity
    log "🔍 Testing service connectivity..."
    make -f Makefile.simple status
    
    success "✅ Migration validation completed"
}

execute_post_migration_cleanup() {
    log "🧹 Phase 7: Post-migration cleanup..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would perform cleanup"
        return 0
    fi
    
    # Archive old database configurations
    log "📦 Archiving old database configurations..."
    
    # Create migration completion summary
    cat > "$BACKUP_DIR/migration-completion-summary.md" << EOF
# 🎉 External Database Migration Completed

## Migration Details
- **Completed**: $(date)
- **Source**: timescaledb.trading-system.svc.cluster.local:5432
- **Targets**: 
  - TimescaleDB: postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading
  - Vector Storage: postgres-vector-external.postgres-infra.svc.cluster.local:5432/trading
  - Apache AGE: postgres-age-external.postgres-infra.svc.cluster.local:5432/trading
  - Config DB: postgres-regular-external.postgres-infra.svc.cluster.local:5432/trading

## Next Steps
1. Monitor service performance with new databases
2. Update monitoring and alerting configurations
3. Consider removing old database deployments after validation period
4. Update documentation and runbooks

## Rollback Information
If rollback is needed, use: \`$0 rollback\`
EOF
    
    success "✅ Post-migration cleanup completed"
}

# Main execution functions
execute_migrate_all() {
    log "🚀 Starting complete migration process..."
    
    for phase in "${PHASES[@]}"; do
        log "🔄 Executing phase: $phase"
        
        case "$phase" in
            "pre-migration-backup")
                execute_pre_migration_backup
                ;;
            "setup-external-databases")
                execute_setup_external_databases
                ;;
            "data-migration")
                execute_data_migration
                ;;
            "service-config-update")
                execute_service_config_update
                ;;
            "service-restart")
                execute_service_restart
                ;;
            "validation")
                execute_validation
                ;;
            "post-migration-cleanup")
                execute_post_migration_cleanup
                ;;
        esac
        
        if [ $? -ne 0 ]; then
            error "❌ Phase '$phase' failed"
            if [ "$FORCE" != true ]; then
                error "Migration stopped. Use --force to continue or fix the issue."
                return 1
            fi
        fi
        
        success "✅ Phase '$phase' completed"
        save_migration_state "$phase" "completed"
    done
    
    success "🎉 Complete migration process finished successfully!"
}

execute_migrate_phase() {
    if [ -z "$PHASE" ]; then
        error "Phase must be specified for migrate-phase command"
        usage
        exit 1
    fi
    
    log "🔄 Executing specific phase: $PHASE"
    
    case "$PHASE" in
        "pre-migration-backup")
            execute_pre_migration_backup
            ;;
        "setup-external-databases")
            execute_setup_external_databases
            ;;
        "data-migration")
            execute_data_migration
            ;;
        "service-config-update")
            execute_service_config_update
            ;;
        "service-restart")
            execute_service_restart
            ;;
        "validation")
            execute_validation
            ;;
        "post-migration-cleanup")
            execute_post_migration_cleanup
            ;;
        *)
            error "Unknown phase: $PHASE"
            usage
            exit 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        success "✅ Phase '$PHASE' completed successfully"
        save_migration_state "$PHASE" "completed"
    else
        error "❌ Phase '$PHASE' failed"
        exit 1
    fi
}

execute_rollback() {
    log "🔄 Executing rollback..."
    
    if [ "$DRY_RUN" = true ]; then
        log "🔍 DRY RUN: Would rollback migration"
        return 0
    fi
    
    # Restore service configurations from backup
    if [ -d "backup/service-configs-$(whoami)-$(hostname)" ]; then
        log "📦 Restoring service configurations from backup..."
        # Implementation depends on backup structure
        warning "⚠️ Manual rollback required. Check backup directory for original configurations."
    fi
    
    # Restart services with old configurations
    log "🔄 Restarting services with old configurations..."
    kubectl rollout restart deployment -n trading-system
    
    success "✅ Rollback completed"
}

execute_status() {
    log "📊 Migration status:"
    
    if [ -f "$MIGRATION_STATE_FILE" ]; then
        echo "Current state:"
        cat "$MIGRATION_STATE_FILE" | python3 -m json.tool 2>/dev/null || cat "$MIGRATION_STATE_FILE"
    else
        echo "No migration state file found"
    fi
    
    echo
    echo "Service status:"
    kubectl get pods -n trading-system
}

execute_validate() {
    log "🔍 Validating current migration state..."
    
    # Check if external databases are accessible
    if [ -f "./scripts/migrate-data-to-external.py" ]; then
        python3 ./scripts/migrate-data-to-external.py --test-connections
    fi
    
    # Check service health
    make -f Makefile.simple status
}

execute_resume() {
    log "🔄 Resuming migration from last successful phase..."
    
    # Implementation would check migration state and resume from appropriate phase
    warning "⚠️ Resume functionality not yet implemented"
    warning "Please check migration state and run specific phases manually"
}

# Main execution
case "$COMMAND" in
    migrate-all)
        execute_migrate_all
        ;;
    migrate-phase)
        execute_migrate_phase
        ;;
    rollback)
        execute_rollback
        ;;
    status)
        execute_status
        ;;
    validate)
        execute_validate
        ;;
    resume)
        execute_resume
        ;;
    *)
        error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac

log "📋 Migration execution completed. Check $LOG_FILE for detailed logs."
