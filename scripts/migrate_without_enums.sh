#!/bin/bash
# Migrate live trading data to postgres-infra WITHOUT ENUMs
# This creates tables with VARCHAR instead of ENUM types

set -e

echo "🔄 Migrating Live Trading Data (Without ENUMs)"
echo "=============================================="
echo ""

SOURCE_POD="timescaledb-85dd6d8d96-sjlxv"
SOURCE_NS="trading-system"
SOURCE_USER="trading_user"
SOURCE_DB="trading_bot"

TARGET_POD="postgres-timescale-bb5658c4f-vpvf7"
TARGET_NS="postgres-infra"
TARGET_USER="postgres"
TARGET_DB="trading_bot"

ACCOUNT_ID="19c25392-8b61-4b71-a344-0eb04d275528"

echo "📥 Step 1: Dump data from trading-system (CSV format)"
echo "-----------------------------------------------------"

# Dump live_trading_accounts
kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
    psql -U $SOURCE_USER -d $SOURCE_DB -c "\COPY live_trading_accounts TO STDOUT WITH CSV HEADER" \
    > /tmp/live_trading_accounts.csv

# Dump api_credentials  
kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
    psql -U $SOURCE_USER -d $SOURCE_DB -c "\COPY api_credentials TO STDOUT WITH CSV HEADER" \
    > /tmp/api_credentials.csv

# Dump live_positions
kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
    psql -U $SOURCE_USER -d $SOURCE_DB -c "\COPY live_positions TO STDOUT WITH CSV HEADER" \
    > /tmp/live_positions.csv

# Dump live_trades
kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
    psql -U $SOURCE_USER -d $SOURCE_DB -c "\COPY live_trades TO STDOUT WITH CSV HEADER" \
    > /tmp/live_trades.csv

echo "✅ Data exported"
echo ""

echo "📋 Step 2: Check what was exported"
echo "-----------------------------------"
echo "  live_trading_accounts: $(wc -l < /tmp/live_trading_accounts.csv) rows"
echo "  api_credentials: $(wc -l < /tmp/api_credentials.csv) rows"
echo "  live_positions: $(wc -l < /tmp/live_positions.csv) rows"
echo "  live_trades: $(wc -l < /tmp/live_trades.csv) rows"
echo ""

echo "📊 Current positions in source database:"
kubectl exec -n $SOURCE_NS $SOURCE_POD -- \
    psql -U $SOURCE_USER -d $SOURCE_DB -t -c \
    "SELECT symbol, quantity, average_price, status FROM live_positions WHERE account_id = '$ACCOUNT_ID' ORDER BY opened_at DESC;" | cat

echo ""
echo "✅ Migration data ready!"
echo ""
echo "⚠️  Next step: Create tables in postgres-infra with VARCHAR instead of ENUMs"
echo "   Then we can import this data"

