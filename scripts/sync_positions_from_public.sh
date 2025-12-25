#!/bin/bash
# Sync Positions from Public.com
# ===============================
# This script triggers a position sync from Public.com to the database,
# ensuring both stock and options positions are updated.

echo "🔄 Syncing positions from Public.com..."
echo ""

ACCOUNT_ID="19c25392-8b61-4b71-a344-0eb04d275528"
API_URL="http://localhost:11120"

# Trigger position sync (endpoint is at /sync/ not /api/v1/sync/)
echo "📊 Triggering position sync..."
RESULT=$(curl -s -X POST "${API_URL}/sync/${ACCOUNT_ID}/positions" 2>/dev/null)

# Check if successful
SUCCESS=$(echo "$RESULT" | jq -r '.success // false')

if [ "$SUCCESS" = "true" ]; then
    echo "✅ Position sync successful!"
    echo ""
    echo "📊 Summary:"
    echo "  Total Synced: $(echo "$RESULT" | jq -r '.positions_synced // 0')"
    echo "  Stock Positions: $(echo "$RESULT" | jq -r '.stock_positions // 0')"
    echo "  Options Positions: $(echo "$RESULT" | jq -r '.options_positions // 0')"
    echo "  Inserted: $(echo "$RESULT" | jq -r '.positions_inserted // 0')"
    echo ""
    echo "🔍 Now checking positions in database..."
    echo ""
    
    # Show current positions
    curl -s "${API_URL}/api/v1/trading/positions?account_id=${ACCOUNT_ID}&status_filter=OPEN" | \
        jq -r '.positions[] | "\(.symbol): \(.quantity) @ $\(.average_price) - P&L: $\(.unrealized_pnl // 0) \(if .legs_data then "(OPTIONS)" else "(STOCK)" end)"'
else
    echo "❌ Position sync failed!"
    echo ""
    echo "Error: $(echo "$RESULT" | jq -r '.error // .detail // "Unknown error"')"
    exit 1
fi

echo ""
echo "✅ Sync complete!"

