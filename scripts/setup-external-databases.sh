#!/bin/bash

# 🗄️ External Database Setup Script
# Sets up new external databases for migration from current TimescaleDB

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="logs/external-db-setup_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="backup/external-db-migration"

# Database configurations (using port forwarding)
TIMESCALE_EXTERNAL="localhost:11150"
AGE_EXTERNAL="localhost:11152"
VECTOR_EXTERNAL="localhost:11151"
REGULAR_EXTERNAL="localhost:11153"

# Unified database name
UNIFIED_DB_NAME="trading"

# Default credentials (should be updated with actual values)
DB_USER="postgres"
DB_PASSWORD="postgres"

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
    echo "  setup-all      - Set up all external databases"
    echo "  setup-timescale - Set up TimescaleDB external"
    echo "  setup-age      - Set up Apache AGE external"
    echo "  setup-vector   - Set up Vector Storage external"
    echo "  setup-regular  - Set up Regular PostgreSQL external"
    echo "  validate       - Validate all database connections"
    echo "  backup         - Create backup before setup"
    echo
    echo "Options:"
    echo "  -u, --user     - Database user (default: postgres)"
    echo "  -p, --password - Database password (default: postgres)"
    echo "  -h, --help     - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 setup-all"
    echo "  $0 --user admin --password secret setup-timescale"
    echo "  $0 validate"
}

# Parse command line arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        -p|--password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        setup-all|setup-timescale|setup-age|setup-vector|setup-regular|validate|backup)
            COMMAND="$1"
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

# Function to test database connectivity
test_connection() {
    local host_port="$1"
    local database="$2"
    local user="$3"
    local password="$4"
    
    log "Testing connection to $host_port/$database as $user..."
    
    PGPASSWORD="$password" psql -h "${host_port%:*}" -p "${host_port#*:}" -U "$user" -d "$database" -c "SELECT version();" >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        success "✅ Connected to $host_port/$database"
        return 0
    else
        error "❌ Failed to connect to $host_port/$database"
        return 1
    fi
}

# Function to create database and extensions
create_database() {
    local host_port="$1"
    local database="$2"
    local user="$3"
    local password="$4"
    local extensions="$5"
    
    log "Creating database $database on $host_port..."
    
    # Create database
    PGPASSWORD="$password" psql -h "${host_port%:*}" -p "${host_port#*:}" -U "$user" -d postgres -c "CREATE DATABASE $database;" 2>/dev/null || warning "Database $database may already exist"
    
    # Create extensions
    if [ -n "$extensions" ]; then
        for ext in $extensions; do
            log "Creating extension $ext in $database..."
            PGPASSWORD="$password" psql -h "${host_port%:*}" -p "${host_port#*:}" -U "$user" -d "$database" -c "CREATE EXTENSION IF NOT EXISTS $ext;" 2>/dev/null || warning "Extension $ext may already exist or failed to create"
        done
    fi
    
    success "✅ Database $database setup completed"
}

# Function to set up TimescaleDB external
setup_timescale_external() {
    log "🚀 Setting up TimescaleDB External..."
    
    create_database "$TIMESCALE_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD" "timescaledb"
    
    # Create core trading tables
    log "Creating core trading tables..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${TIMESCALE_EXTERNAL%:*}" -p "${TIMESCALE_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        -- Core trading tables
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            side VARCHAR(4) NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            strategy VARCHAR(100),
            pnl DECIMAL(10,2),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS historical_prices (
            symbol VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            open_price DECIMAL(10,2) NOT NULL,
            high_price DECIMAL(10,2) NOT NULL,
            low_price DECIMAL(10,2) NOT NULL,
            close_price DECIMAL(10,2) NOT NULL,
            volume INTEGER NOT NULL,
            provider VARCHAR(50) NOT NULL,
            interval VARCHAR(10) DEFAULT '1d',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (symbol, date)
        );
        
        CREATE TABLE IF NOT EXISTS backtest_runs (
            id SERIAL PRIMARY KEY,
            strategy_name VARCHAR(100) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            initial_capital DECIMAL(15,2) NOT NULL,
            final_capital DECIMAL(15,2),
            total_return DECIMAL(10,4),
            sharpe_ratio DECIMAL(10,4),
            max_drawdown DECIMAL(10,4),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            signal_type VARCHAR(20) NOT NULL,
            strength DECIMAL(3,2),
            timestamp TIMESTAMPTZ NOT NULL,
            strategy VARCHAR(100),
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    "
    
    # Convert to hypertable for time-series data
    log "Converting tables to TimescaleDB hypertables..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${TIMESCALE_EXTERNAL%:*}" -p "${TIMESCALE_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        -- Fix primary key for historical_prices to work with TimescaleDB partitioning
        ALTER TABLE historical_prices DROP CONSTRAINT IF EXISTS historical_prices_pkey;
        ALTER TABLE historical_prices ADD CONSTRAINT historical_prices_pkey PRIMARY KEY (date, symbol);
        
        -- Create hypertables
        SELECT create_hypertable('historical_prices', 'date', if_not_exists => TRUE);
        SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE);
        SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);
    "
    
    success "✅ TimescaleDB External setup completed"
}

# Function to set up Apache AGE external
setup_age_external() {
    log "🚀 Setting up Apache AGE External..."
    
    create_database "$AGE_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD" "age"
    
    # Create graph tables
    log "Creating graph analytics tables..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${AGE_EXTERNAL%:*}" -p "${AGE_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        -- Graph analytics tables
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
    "
    
    success "✅ Apache AGE External setup completed"
}

# Function to set up Vector Storage external
setup_vector_external() {
    log "🚀 Setting up Vector Storage External..."
    
    create_database "$VECTOR_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD" "vector"
    
    # Create vector tables
    log "Creating vector storage tables..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${VECTOR_EXTERNAL%:*}" -p "${VECTOR_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        -- Vector storage tables
        CREATE TABLE IF NOT EXISTS vector_embeddings (
            id SERIAL PRIMARY KEY,
            content_type VARCHAR(50) NOT NULL,
            content_id INTEGER NOT NULL,
            embedding vector(1536),
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS vectorization_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            total_items INTEGER,
            processed_items INTEGER DEFAULT 0,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS news_embeddings (
            id SERIAL PRIMARY KEY,
            news_id INTEGER NOT NULL,
            title_embedding vector(1536),
            content_embedding vector(1536),
            summary_embedding vector(1536),
            sentiment_vector vector(10),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    "
    
    # Create vector indexes
    log "Creating vector indexes..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${VECTOR_EXTERNAL%:*}" -p "${VECTOR_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        CREATE INDEX IF NOT EXISTS idx_vector_embeddings_content ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        CREATE INDEX IF NOT EXISTS idx_news_title_embedding ON news_embeddings USING ivfflat (title_embedding vector_cosine_ops) WITH (lists = 100);
        CREATE INDEX IF NOT EXISTS idx_news_content_embedding ON news_embeddings USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);
    "
    
    success "✅ Vector Storage External setup completed"
}

# Function to set up Regular PostgreSQL external
setup_regular_external() {
    log "🚀 Setting up Regular PostgreSQL External..."
    
    create_database "$REGULAR_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD" ""
    
    # Create configuration tables
    log "Creating configuration tables..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${REGULAR_EXTERNAL%:*}" -p "${REGULAR_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        -- Configuration tables
        CREATE TABLE IF NOT EXISTS trading_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value TEXT,
            config_type VARCHAR(50),
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS popular_symbols (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) UNIQUE NOT NULL,
            category VARCHAR(50),
            sector VARCHAR(100),
            market_cap DECIMAL(20,2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS report_jobs (
            id SERIAL PRIMARY KEY,
            job_name VARCHAR(100) NOT NULL,
            schedule VARCHAR(100),
            last_run TIMESTAMPTZ,
            next_run TIMESTAMPTZ,
            status VARCHAR(20) DEFAULT 'idle',
            config JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS risk_metrics (
            id SERIAL PRIMARY KEY,
            portfolio_id VARCHAR(50),
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,6),
            metric_date DATE NOT NULL,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    "
    
    # Insert default configuration
    log "Inserting default configuration..."
    PGPASSWORD="$DB_PASSWORD" psql -h "${REGULAR_EXTERNAL%:*}" -p "${REGULAR_EXTERNAL#*:}" -U "$DB_USER" -d "$UNIFIED_DB_NAME" -c "
        INSERT INTO trading_config (config_key, config_value, config_type, description) VALUES
        ('default_stocks', 'AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,NFLX,AMD,INTC', 'string', 'Default stock symbols for trading'),
        ('max_position_size', '0.1', 'decimal', 'Maximum position size as fraction of portfolio'),
        ('stop_loss_percentage', '0.02', 'decimal', 'Default stop loss percentage'),
        ('take_profit_percentage', '0.05', 'decimal', 'Default take profit percentage'),
        ('risk_free_rate', '0.04', 'decimal', 'Risk-free rate for calculations')
        ON CONFLICT (config_key) DO NOTHING;
        
        INSERT INTO popular_symbols (symbol, category, sector) VALUES
        ('AAPL', 'tech', 'Technology'),
        ('MSFT', 'tech', 'Technology'),
        ('GOOGL', 'tech', 'Technology'),
        ('AMZN', 'tech', 'Consumer Discretionary'),
        ('TSLA', 'tech', 'Consumer Discretionary'),
        ('NVDA', 'tech', 'Technology'),
        ('META', 'tech', 'Communication Services'),
        ('NFLX', 'tech', 'Communication Services'),
        ('AMD', 'tech', 'Technology'),
        ('INTC', 'tech', 'Technology')
        ON CONFLICT (symbol) DO NOTHING;
    "
    
    success "✅ Regular PostgreSQL External setup completed"
}

# Function to validate all connections
validate_connections() {
    log "🔍 Validating all database connections..."
    
    local all_connected=true
    
    # Test TimescaleDB External
    if test_connection "$TIMESCALE_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD"; then
        success "✅ TimescaleDB External: Connected"
    else
        error "❌ TimescaleDB External: Failed"
        all_connected=false
    fi
    
    # Test Apache AGE External
    if test_connection "$AGE_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD"; then
        success "✅ Apache AGE External: Connected"
    else
        error "❌ Apache AGE External: Failed"
        all_connected=false
    fi
    
    # Test Vector Storage External
    if test_connection "$VECTOR_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD"; then
        success "✅ Vector Storage External: Connected"
    else
        error "❌ Vector Storage External: Failed"
        all_connected=false
    fi
    
    # Test Regular PostgreSQL External
    if test_connection "$REGULAR_EXTERNAL" "$UNIFIED_DB_NAME" "$DB_USER" "$DB_PASSWORD"; then
        success "✅ Regular PostgreSQL External: Connected"
    else
        error "❌ Regular PostgreSQL External: Failed"
        all_connected=false
    fi
    
    if [ "$all_connected" = true ]; then
        success "🎉 All external databases are connected and ready!"
    else
        error "⚠️ Some external databases failed connection tests"
        exit 1
    fi
}

# Function to create backup
create_backup() {
    log "💾 Creating backup before setup..."
    
    # Backup current database
    if [ -f "./scripts/database-backup.sh" ]; then
        ./scripts/database-backup.sh
        success "✅ Backup completed"
    else
        warning "⚠️ Database backup script not found, skipping backup"
    fi
}

# Main execution
case "$COMMAND" in
    setup-all)
        log "🚀 Setting up all external databases..."
        create_backup
        setup_timescale_external
        setup_age_external
        setup_vector_external
        setup_regular_external
        validate_connections
        success "🎉 All external databases setup completed!"
        ;;
        
    setup-timescale)
        log "🚀 Setting up TimescaleDB External..."
        create_backup
        setup_timescale_external
        ;;
        
    setup-age)
        log "🚀 Setting up Apache AGE External..."
        create_backup
        setup_age_external
        ;;
        
    setup-vector)
        log "🚀 Setting up Vector Storage External..."
        create_backup
        setup_vector_external
        ;;
        
    setup-regular)
        log "🚀 Setting up Regular PostgreSQL External..."
        create_backup
        setup_regular_external
        ;;
        
    validate)
        validate_connections
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

log "📋 Setup completed. Check $LOG_FILE for detailed logs."
log "📚 Next step: Run data migration scripts to transfer data to new databases."
