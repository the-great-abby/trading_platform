#!/bin/bash
# Migrate live trading data from trading-system database to postgres-infra database

set -e

echo "🔄 Migrating Live Trading Data to postgres-infra"
echo "================================================"
echo ""

SOURCE_POD="timescaledb-85dd6d8d96-sjlxv"
SOURCE_NS="trading-system"
SOURCE_USER="trading_user"
SOURCE_DB="trading_bot"

TARGET_POD="postgres-timescale-bb5658c4f-vpvf7"
TARGET_NS="postgres-infra"
TARGET_USER="postgres"
TARGET_DB="trading_bot"

# Tables to migrate (in order to respect foreign keys)
TABLES=(
    "live_trading_accounts"
    "api_credentials"
    "live_positions"
    "live_trades"
    "active_trades"
    "order_status_history"
    "recovery_sessions"
    "recovery_logs"
    "risk_profiles"
    "strategy_configurations"
    "strategy_assignments"
    "trade_signals"
    "trailing_stop_configurations"
    "paper_trading_orders"
    "paper_trading_order_legs"
)

echo "📊 Step 1: Export schemas from trading-system database"
echo "-----------------------------------------------------"

for TABLE in "${TABLES[@]}"; do
    echo "  Exporting schema for $TABLE..."
    kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
        pg_dump -U $SOURCE_USER -d $SOURCE_DB \
        --schema-only --table=$TABLE \
        > /tmp/schema_${TABLE}.sql
done

echo ""
echo "📦 Step 2: Export data from trading-system database"
echo "---------------------------------------------------"

for TABLE in "${TABLES[@]}"; do
    echo "  Exporting data for $TABLE..."
    kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
        pg_dump -U $SOURCE_USER -d $SOURCE_DB \
        --data-only --table=$TABLE \
        --column-inserts \
        > /tmp/data_${TABLE}.sql
done

echo ""
echo "📥 Step 3: Import schemas to postgres-infra database"
echo "----------------------------------------------------"

for TABLE in "${TABLES[@]}"; do
    echo "  Importing schema for $TABLE..."
    kubectl exec -i -n $TARGET_NS $TARGET_POD -- \
        psql -U $TARGET_USER -d $TARGET_DB \
        < /tmp/schema_${TABLE}.sql || echo "  ⚠️  Schema may already exist"
done

echo ""
echo "📥 Step 4: Import data to postgres-infra database"
echo "-------------------------------------------------"

for TABLE in "${TABLES[@]}"; do
    echo "  Importing data for $TABLE..."
    
    # Check if table has data
    COUNT=$(kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
        psql -U $SOURCE_USER -d $SOURCE_DB -t -c "SELECT COUNT(*) FROM $TABLE")
    
    if [ "$COUNT" -gt 0 ]; then
        echo "    Found $COUNT rows to migrate"
        kubectl exec -i -n $TARGET_NS $TARGET_POD -- \
            psql -U $TARGET_USER -d $TARGET_DB \
            < /tmp/data_${TABLE}.sql
    else
        echo "    No data to migrate"
    fi
done

echo ""
echo "✅ Migration completed!"
echo ""
echo "🔍 Verification:"
echo "---------------"

for TABLE in "${TABLES[@]}"; do
    SOURCE_COUNT=$(kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
        psql -U $SOURCE_USER -d $SOURCE_DB -t -c "SELECT COUNT(*) FROM $TABLE" | xargs)
    TARGET_COUNT=$(kubectl exec -n $TARGET_NS $TARGET_POD -- \
        psql -U $TARGET_USER -d $TARGET_DB -t -c "SELECT COUNT(*) FROM $TABLE" | xargs)
    
    if [ "$SOURCE_COUNT" == "$TARGET_COUNT" ]; then
        echo "  ✅ $TABLE: $SOURCE_COUNT rows (match)"
    else
        echo "  ⚠️  $TABLE: source=$SOURCE_COUNT, target=$TARGET_COUNT (MISMATCH)"
    fi
done

echo ""
echo "🧹 Cleanup temporary files..."
rm -f /tmp/schema_*.sql /tmp/data_*.sql

echo ""
echo "✅ All done! Next steps:"
echo "  1. Update live-trading-service to use postgres-infra database"
echo "  2. Test the live-trading-service"
echo "  3. Delete the trading-system database deployment"

