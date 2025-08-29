#!/bin/bash

# Proper Database Migration Script
# Uses pg_dump/pg_restore for exact schema preservation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOURCE_HOST="localhost"
SOURCE_PORT="11140"
SOURCE_DB="trading_bot"
SOURCE_USER="trading_user"
SOURCE_PASSWORD="trading_pass"

# Target databases (using port forwarding)
TIMESCALE_TARGET="localhost:11150"
VECTOR_TARGET="localhost:11151"
AGE_TARGET="localhost:11152"
CONFIG_TARGET="localhost:11153"

TARGET_USER="postgres"
TARGET_PASSWORD="postgres"
TARGET_DB="trading"

# Backup directory
BACKUP_DIR="backup/proper-migration-$(date +%Y%m%d_%H%M%S)"
LOG_FILE="logs/proper-migration-$(date +%Y%m%d_%H%M%S).log"

# Create necessary directories
mkdir -p logs
mkdir -p "$BACKUP_DIR"

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
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  backup-schemas    - Backup schemas from source database"
    echo "  create-targets    - Create target databases with proper schemas"
    echo "  migrate-data      - Migrate data using pg_dump/pg_restore"
    echo "  validate          - Validate migration results"
    echo "  full-migration    - Execute complete migration process"
    echo "  cleanup           - Clean up temporary files"
    echo
    echo "Examples:"
    echo "  $0 backup-schemas"
    echo "  $0 full-migration"
}

# Function to backup schemas from source
backup_schemas() {
    log "🔍 Creating schema backups from source database..."
    
    # Create schema-only dumps for each target database
    local schemas_dir="$BACKUP_DIR/schemas"
    mkdir -p "$schemas_dir"
    
    # Get the database pod name
    local db_pod=$(kubectl get pods -n trading-system -l app=timescaledb -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$db_pod" ]; then
        error "❌ Could not find TimescaleDB pod"
        return 1
    fi
    log "📋 Using database pod: $db_pod"
    
    # TimescaleDB tables (core trading data)
    log "📋 Backing up TimescaleDB schema..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --schema-only \
        -t trades -t historical_prices -t backtest_runs -t backtest_trades \
        -t backtest_equity_curves -t signals -t orders -t positions \
        -t earnings_reports -t historical_options_snapshots \
        -t options_contracts_cache -t market_data -t market_data_cache \
        > "$schemas_dir/timescale_schema.sql"
    
    # Vector tables
    log "📋 Backing up Vector schema..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --schema-only \
        -t vector_embeddings -t vectorization_jobs -t vectorization_logs \
        -t vectorization_metrics -t historical_news -t news_cache \
        -t news_historical -t news_articles \
        > "$schemas_dir/vector_schema.sql"
    
    # Config tables
    log "📋 Backing up Config schema..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --schema-only \
        -t trading_config -t popular_symbols -t report_jobs -t risk_metrics \
        > "$schemas_dir/config_schema.sql"
    
    # AGE tables (graph analytics) - these are new tables, not existing ones
    log "📋 Creating AGE schema (new tables for graph analytics)..."
    cat > "$schemas_dir/age_schema.sql" << 'EOF'
-- Graph analytics tables for Apache AGE
CREATE TABLE IF NOT EXISTS trading_relationships (
    id SERIAL PRIMARY KEY,
    source_symbol VARCHAR(10) NOT NULL,
    target_symbol VARCHAR(10) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    correlation DECIMAL(5,4),
    strength DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_correlations (
    id SERIAL PRIMARY KEY,
    symbol1 VARCHAR(10) NOT NULL,
    symbol2 VARCHAR(10) NOT NULL,
    correlation_30d DECIMAL(5,4),
    correlation_90d DECIMAL(5,4),
    correlation_1y DECIMAL(5,4),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_networks (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL,
    affected_symbols TEXT[],
    related_news_ids INTEGER[],
    network_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
EOF
    
    success "✅ Schema backups created in $schemas_dir"
}

# Function to create target databases with proper schemas
create_targets() {
    log "🚀 Creating target databases with proper schemas..."
    
    # Create TimescaleDB target
    log "📊 Setting up TimescaleDB target..."
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${TIMESCALE_TARGET%:*}" -p "${TIMESCALE_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${TIMESCALE_TARGET%:*}" -p "${TIMESCALE_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "CREATE DATABASE $TARGET_DB;"
    
    # Install TimescaleDB extension
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${TIMESCALE_TARGET%:*}" -p "${TIMESCALE_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -c "
        CREATE EXTENSION IF NOT EXISTS timescaledb;
    "
    
    # Apply TimescaleDB schema
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${TIMESCALE_TARGET%:*}" -p "${TIMESCALE_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -f "$BACKUP_DIR/schemas/timescale_schema.sql"
    
    # Create Vector target
    log "📊 Setting up Vector target..."
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${VECTOR_TARGET%:*}" -p "${VECTOR_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${VECTOR_TARGET%:*}" -p "${VECTOR_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "CREATE DATABASE $TARGET_DB;"
    
    # Install vector extension
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${VECTOR_TARGET%:*}" -p "${VECTOR_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    # Apply Vector schema
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${VECTOR_TARGET%:*}" -p "${VECTOR_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -f "$BACKUP_DIR/schemas/vector_schema.sql"
    
    # Create Config target
    log "📊 Setting up Config target..."
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${CONFIG_TARGET%:*}" -p "${CONFIG_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${CONFIG_TARGET%:*}" -p "${CONFIG_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "CREATE DATABASE $TARGET_DB;"
    
    # Apply Config schema
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${CONFIG_TARGET%:*}" -p "${CONFIG_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -f "$BACKUP_DIR/schemas/config_schema.sql"
    
    # Create AGE target
    log "📊 Setting up AGE target..."
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${AGE_TARGET%:*}" -p "${AGE_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${AGE_TARGET%:*}" -p "${AGE_TARGET#*:}" -U "$TARGET_USER" -d postgres -c "CREATE DATABASE $TARGET_DB;"
    
    # Apply AGE schema
    PGPASSWORD="$TARGET_PASSWORD" psql -h "${AGE_TARGET%:*}" -p "${AGE_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB" -f "$BACKUP_DIR/schemas/age_schema.sql"
    
    success "✅ Target databases created with proper schemas"
}

# Function to migrate data using pg_dump/pg_restore
migrate_data() {
    log "🔄 Migrating data using pg_dump/pg_restore..."
    
    # Get the database pod name
    local db_pod=$(kubectl get pods -n trading-system -l app=timescaledb -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$db_pod" ]; then
        error "❌ Could not find TimescaleDB pod"
        return 1
    fi
    log "📋 Using database pod: $db_pod"
    
    # Migrate TimescaleDB data
    log "📊 Migrating TimescaleDB data..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --data-only \
        -t trades -t historical_prices -t backtest_runs -t backtest_trades \
        -t backtest_equity_curves -t signals -t orders -t positions \
        -t earnings_reports -t historical_options_snapshots \
        -t options_contracts_cache -t market_data -t market_data_cache \
        | PGPASSWORD="$TARGET_PASSWORD" psql -h "${TIMESCALE_TARGET%:*}" -p "${TIMESCALE_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB"
    
    # Migrate Vector data
    log "📊 Migrating Vector data..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --data-only \
        -t vector_embeddings -t vectorization_jobs -t vectorization_logs \
        -t vectorization_metrics -t historical_news -t news_cache \
        -t news_historical -t news_articles \
        | PGPASSWORD="$TARGET_PASSWORD" psql -h "${VECTOR_TARGET%:*}" -p "${VECTOR_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB"
    
    # Migrate Config data
    log "📊 Migrating Config data..."
    kubectl exec "$db_pod" -n trading-system -- pg_dump \
        -h localhost -U "$SOURCE_USER" -d "$SOURCE_DB" \
        --data-only \
        -t trading_config -t popular_symbols -t report_jobs -t risk_metrics \
        | PGPASSWORD="$TARGET_PASSWORD" psql -h "${CONFIG_TARGET%:*}" -p "${CONFIG_TARGET#*:}" -U "$TARGET_USER" -d "$TARGET_DB"
    
    # AGE tables are new and empty, no data to migrate
    log "📊 AGE tables are new (no data to migrate)..."
    
    success "✅ Data migration completed"
}

# Function to validate migration
validate() {
    log "🧪 Validating migration results..."
    
    # Check table counts in source vs target
    log "📊 Validating TimescaleDB..."
    validate_table_counts "$SOURCE_HOST" "$SOURCE_PORT" "$SOURCE_DB" "$SOURCE_USER" "$SOURCE_PASSWORD" \
                         "${TIMESCALE_TARGET%:*}" "${TIMESCALE_TARGET#*:}" "$TARGET_DB" "$TARGET_USER" "$TARGET_PASSWORD" \
                         "trades historical_prices backtest_runs backtest_trades backtest_equity_curves signals orders positions earnings_reports historical_options_snapshots options_contracts_cache market_data market_data_cache"
    
    log "📊 Validating Vector..."
    validate_table_counts "$SOURCE_HOST" "$SOURCE_PORT" "$SOURCE_DB" "$SOURCE_USER" "$SOURCE_PASSWORD" \
                         "${VECTOR_TARGET%:*}" "${VECTOR_TARGET#*:}" "$TARGET_DB" "$TARGET_USER" "$TARGET_PASSWORD" \
                         "vector_embeddings vectorization_jobs vectorization_logs vectorization_metrics historical_news news_cache news_historical news_articles"
    
    log "📊 Validating Config..."
    validate_table_counts "$SOURCE_HOST" "$SOURCE_PORT" "$SOURCE_DB" "$SOURCE_USER" "$SOURCE_PASSWORD" \
                         "${CONFIG_TARGET%:*}" "${CONFIG_TARGET#*:}" "$TARGET_DB" "$TARGET_USER" "$TARGET_PASSWORD" \
                         "trading_config popular_symbols report_jobs risk_metrics"
    
    log "📊 Validating AGE..."
    validate_table_counts "$SOURCE_HOST" "$SOURCE_PORT" "$SOURCE_DB" "$SOURCE_USER" "$SOURCE_PASSWORD" \
                         "${AGE_TARGET%:*}" "${AGE_TARGET#*:}" "$TARGET_DB" "$TARGET_USER" "$TARGET_PASSWORD" \
                         "trading_relationships market_correlations news_networks"
    
    success "✅ Validation completed"
}

# Helper function to validate table counts
validate_table_counts() {
    local source_host="$1"
    local source_port="$2"
    local source_db="$3"
    local source_user="$4"
    local source_password="$5"
    local target_host="$6"
    local target_port="$7"
    local target_db="$8"
    local target_user="$9"
    local target_password="${10}"
    local tables="${11}"
    
    for table in $tables; do
        # Check if table exists in source
        local source_count=$(PGPASSWORD="$source_password" psql -h "$source_host" -p "$source_port" -U "$source_user" -d "$source_db" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ')
        
        if [ -n "$source_count" ] && [ "$source_count" != "0" ]; then
            # Check if table exists in target
            local target_count=$(PGPASSWORD="$target_password" psql -h "$target_host" -p "$target_port" -U "$target_user" -d "$target_db" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ')
            
            if [ -n "$target_count" ]; then
                if [ "$source_count" = "$target_count" ]; then
                    log "✅ $table: $source_count rows (source) = $target_count rows (target)"
                else
                    warning "⚠️ $table: $source_count rows (source) ≠ $target_count rows (target)"
                fi
            else
                warning "⚠️ $table: exists in source ($source_count rows) but not in target"
            fi
        fi
    done
}

# Function to execute complete migration
full_migration() {
    log "🚀 Starting complete migration process..."
    
    backup_schemas
    create_targets
    migrate_data
    validate
    
    success "🎉 Complete migration process finished!"
}

# Function to cleanup temporary files
cleanup() {
    log "🧹 Cleaning up temporary files..."
    rm -rf "$BACKUP_DIR"
    success "✅ Cleanup completed"
}

# Main script logic
case "${1:-}" in
    backup-schemas)
        backup_schemas
        ;;
    create-targets)
        create_targets
        ;;
    migrate-data)
        migrate_data
        ;;
    validate)
        validate
        ;;
    full-migration)
        full_migration
        ;;
    cleanup)
        cleanup
        ;;
    *)
        usage
        exit 1
        ;;
esac
