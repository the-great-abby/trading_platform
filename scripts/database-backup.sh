#!/bin/bash

# Database Backup Script for Trading System
# This script creates a complete backup of the TimescaleDB database

set -e

# Configuration
BACKUP_DIR="backup/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="trading_db_backup_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
COMPRESSED_BACKUP="${BACKUP_PATH}.gz"

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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

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

# Create backup directory
log "Creating backup directory..."
mkdir -p "$BACKUP_DIR"

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

# Create backup using pg_dump
log "Starting database backup..."
log "Backup file: $BACKUP_PATH"

# Use kubectl exec to run pg_dump inside the pod
if kubectl exec -n trading-system "$DB_POD" -- bash -c "
    export PGPASSWORD='$DB_PASSWORD' &&
    pg_dump \
        -h '$DB_HOST' \
        -p '$DB_PORT' \
        -U '$DB_USER' \
        -d '$DB_NAME' \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --no-owner \
        --no-privileges \
        --schema=public \
        --file='/tmp/$BACKUP_FILE'
"; then
    
    # Copy backup file from pod to local filesystem
    log "Copying backup file from pod..."
    kubectl cp "trading-system/$DB_POD:/tmp/$BACKUP_FILE" "$BACKUP_PATH"
    
    # Compress the backup
    log "Compressing backup file..."
    gzip "$BACKUP_PATH"
    
    # Verify the backup file exists and has content
    if [ -f "$COMPRESSED_BACKUP" ] && [ -s "$COMPRESSED_BACKUP" ]; then
        BACKUP_SIZE=$(du -h "$COMPRESSED_BACKUP" | cut -f1)
        success "Database backup completed successfully!"
        log "Backup file: $COMPRESSED_BACKUP"
        log "Backup size: $BACKUP_SIZE"
        log "Backup timestamp: $TIMESTAMP"
        
        # Clean up the temporary file in the pod
        kubectl exec -n trading-system "$DB_POD" -- rm -f "/tmp/$BACKUP_FILE"
        
        # List recent backups
        echo
        log "Recent backups:"
        ls -lah "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -5 || warning "No previous backups found"
        
    else
        error "Backup file is empty or was not created"
        exit 1
    fi
    
else
    error "Database backup failed"
    exit 1
fi

# Create a backup manifest for tracking
MANIFEST_FILE="${BACKUP_DIR}/backup_manifest_${TIMESTAMP}.json"
cat > "$MANIFEST_FILE" << EOF
{
    "backup_file": "$BACKUP_FILE.gz",
    "timestamp": "$TIMESTAMP",
    "database": {
        "name": "$DB_NAME",
        "host": "$DB_HOST",
        "port": "$DB_PORT",
        "user": "$DB_USER"
    },
    "pod": "$DB_POD",
    "namespace": "trading-system",
    "backup_size": "$BACKUP_SIZE",
    "compressed": true,
    "created_by": "database-backup.sh"
}
EOF

log "Backup manifest created: $MANIFEST_FILE"

# Optional: Keep only last 10 backups to save space
log "Cleaning up old backups (keeping last 10)..."
cd "$BACKUP_DIR"
ls -t *.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f

success "Database backup process completed!"
