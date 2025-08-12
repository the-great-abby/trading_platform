#!/bin/bash

# Database Restore Script for Trading System
# This script restores the TimescaleDB database from a backup file

set -e

# Configuration
BACKUP_DIR="backup/database"
RESTORE_LOG="backup/restore_log_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$RESTORE_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$RESTORE_LOG" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$RESTORE_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$RESTORE_LOG"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS] <backup_file>"
    echo
    echo "Options:"
    echo "  -f, --force     Force restore without confirmation"
    echo "  -d, --dry-run   Show what would be restored without actually doing it"
    echo "  -h, --help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 backup/database/trading_db_backup_20250808_143022.sql.gz"
    echo "  $0 --dry-run backup/database/trading_db_backup_20250808_143022.sql.gz"
    echo "  $0 --force backup/database/trading_db_backup_20250808_143022.sql.gz"
    echo
    echo "Available backups:"
    ls -lah "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "No backups found in $BACKUP_DIR"
}

# Parse command line arguments
FORCE=false
DRY_RUN=false
BACKUP_FILE=""

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
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Check if backup file is provided
if [ -z "$BACKUP_FILE" ]; then
    error "No backup file specified"
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

# Database connection details
DB_HOST="timescaledb.trading-system.svc.cluster.local"
DB_PORT="5432"
DB_NAME="trading_bot"
DB_USER="trading_user"
DB_PASSWORD="trading_pass"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    echo
    echo "Available backups:"
    ls -lah "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "No backups found in $BACKUP_DIR"
    exit 1
fi

# Get backup file info
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_DATE=$(stat -c %y "$BACKUP_FILE" | cut -d' ' -f1)

log "Backup file: $BACKUP_FILE"
log "Backup size: $BACKUP_SIZE"
log "Backup date: $BACKUP_DATE"

# Check if backup is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "Backup file is compressed"
    COMPRESSED=true
else
    log "Backup file is uncompressed"
    COMPRESSED=false
fi

# Show what will be restored
log "This will restore the database to the state from: $BACKUP_DATE"
log "Current database will be completely replaced!"

if [ "$DRY_RUN" = true ]; then
    log "DRY RUN MODE - No changes will be made"
    log "Would restore from: $BACKUP_FILE"
    log "Would connect to pod: $DB_POD"
    log "Would restore to database: $DB_NAME"
    success "Dry run completed - no changes made"
    exit 0
fi

# Confirm restore (unless --force is used)
if [ "$FORCE" = false ]; then
    echo
    warning "WARNING: This will completely replace the current database!"
    warning "All current data will be lost!"
    echo
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

# Create restore directory in pod
log "Preparing restore environment..."
kubectl exec -n trading-system "$DB_POD" -- mkdir -p /tmp/restore

# Copy backup file to pod
log "Copying backup file to pod..."
kubectl cp "$BACKUP_FILE" "trading-system/$DB_POD:/tmp/restore/"

# Get the filename in the pod
BACKUP_FILENAME=$(basename "$BACKUP_FILE")

# Decompress if needed
if [ "$COMPRESSED" = true ]; then
    log "Decompressing backup file..."
    kubectl exec -n trading-system "$DB_POD" -- gunzip "/tmp/restore/$BACKUP_FILENAME"
    BACKUP_FILENAME="${BACKUP_FILENAME%.gz}"
fi

# Stop all applications that might be using the database
log "Stopping applications to prevent data corruption..."
kubectl scale deployment --all -n trading-system --replicas=0

# Wait for pods to stop
log "Waiting for pods to stop..."
sleep 10

# Restore the database
log "Starting database restore..."
if kubectl exec -n trading-system "$DB_POD" -- psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "/tmp/restore/$BACKUP_FILENAME"; then
    
    success "Database restore completed successfully!"
    
    # Clean up
    log "Cleaning up temporary files..."
    kubectl exec -n trading-system "$DB_POD" -- rm -rf /tmp/restore
    
    # Restart applications
    log "Restarting applications..."
    kubectl scale deployment --all -n trading-system --replicas=1
    
    # Wait for pods to start
    log "Waiting for pods to start..."
    sleep 30
    
    # Check if pods are running
    log "Checking application status..."
    kubectl get pods -n trading-system --no-headers | grep -v "Running\|Completed" && warning "Some pods may not be running yet"
    
    success "Database restore process completed!"
    log "Restore log saved to: $RESTORE_LOG"
    
else
    error "Database restore failed"
    
    # Clean up
    kubectl exec -n trading-system "$DB_POD" -- rm -rf /tmp/restore
    
    # Restart applications even if restore failed
    log "Restarting applications after failed restore..."
    kubectl scale deployment --all -n trading-system --replicas=1
    
    exit 1
fi



