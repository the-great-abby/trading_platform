#!/bin/bash

# Clean Populate Symbols Database
# This script completely cleans the database and repopulates it with the central list

echo "🧹 Starting Clean Symbol Database Population..."
echo "=================================================="

# Check if dashboard is accessible
if ! curl -s http://localhost:11114/health > /dev/null; then
    echo "❌ Dashboard not accessible. Make sure port forwarding is active."
    exit 1
fi

echo "✅ Dashboard is accessible"

# Get current symbols
echo "📊 Getting current symbols..."
CURRENT_SYMBOLS=$(curl -s http://localhost:11114/api/symbols/all | jq -r '.[].name' 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$CURRENT_SYMBOLS" ]; then
    echo "📊 Current symbols in database: $(echo "$CURRENT_SYMBOLS" | wc -l)"
    
    # Delete ALL current symbols
    echo "🗑️  Deleting ALL existing symbols..."
    for symbol in $CURRENT_SYMBOLS; do
        if curl -s -X DELETE "http://localhost:11114/api/symbols/delete/$symbol" > /dev/null; then
            echo "   🗑️  Deleted $symbol"
        else
            echo "   ❌ Failed to delete $symbol"
        fi
    done
else
    echo "📊 No existing symbols found"
fi

# Wait a moment for cleanup
sleep 2

# Verify database is empty
EMPTY_CHECK=$(curl -s http://localhost:11114/api/symbols/all | jq 'length')
if [ "$EMPTY_CHECK" -eq 0 ]; then
    echo "✅ Database is now empty"
else
    echo "⚠️  Database still has $EMPTY_CHECK symbols"
fi

echo ""
echo "📝 Adding symbols from central list..."

SUCCESSFUL_ADDS=0

# Function to add a symbol
add_symbol() {
    local symbol=$1
    local category=$2
    local description=$3
    local priority=$4
    
    if curl -s -X POST "http://localhost:11114/api/symbols/add" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$symbol\",\"description\":\"$description\",\"category\":\"$category\",\"priority\":$priority,\"active\":true}" > /dev/null; then
        
        echo "   ✅ Added $symbol ($category) - Priority $priority"
        return 0
    else
        echo "   ❌ Failed to add $symbol"
        return 1
    fi
}

# Add all symbols
add_symbol "AAPL" "Technology" "Apple Inc." 1 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "MSFT" "Technology" "Microsoft Corporation" 2 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "GOOGL" "Technology" "Alphabet Inc." 3 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "AMZN" "Technology" "Amazon.com Inc." 4 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "TSLA" "Technology" "Tesla Inc." 5 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "NVDA" "Technology" "NVIDIA Corporation" 6 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "META" "Technology" "Meta Platforms Inc." 7 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "NFLX" "Technology" "Netflix Inc." 8 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "AMD" "Technology" "Advanced Micro Devices Inc." 9 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "INTC" "Technology" "Intel Corporation" 10 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "JPM" "Finance" "JPMorgan Chase & Co." 11 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "BAC" "Finance" "Bank of America Corporation" 12 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "WFC" "Finance" "Wells Fargo & Company" 13 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "GS" "Finance" "Goldman Sachs Group Inc." 14 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "MS" "Finance" "Morgan Stanley" 15 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "JNJ" "Healthcare" "Johnson & Johnson" 16 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "PFE" "Healthcare" "Pfizer Inc." 17 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "UNH" "Healthcare" "UnitedHealth Group Inc." 18 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "HD" "Consumer Discretionary" "Home Depot Inc." 19 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "DIS" "Consumer Discretionary" "Walt Disney Co." 20 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "V" "Finance" "Visa Inc." 21 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "MA" "Finance" "Mastercard Inc." 22 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "PYPL" "Technology" "PayPal Holdings Inc." 23 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "ADBE" "Technology" "Adobe Inc." 24 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "CRM" "Technology" "Salesforce Inc." 25 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "ORCL" "Technology" "Oracle Corporation" 26 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "CSCO" "Technology" "Cisco Systems Inc." 27 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "QCOM" "Technology" "Qualcomm Incorporated" 28 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "TXN" "Technology" "Texas Instruments Incorporated" 29 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "AVGO" "Technology" "Broadcom Inc." 30 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "SPY" "ETF" "SPDR S&P 500 ETF Trust" 31 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "QQQ" "ETF" "Invesco QQQ Trust" 32 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "VTI" "ETF" "Vanguard Total Stock Market ETF" 33 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "VOO" "ETF" "Vanguard S&P 500 ETF" 34 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "VUG" "ETF" "Vanguard Growth ETF" 35 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "XLK" "ETF" "Technology Select Sector SPDR Fund" 36 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "XLF" "ETF" "Financial Select Sector SPDR Fund" 37 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "XLE" "ETF" "Energy Select Sector SPDR Fund" 38 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "XLV" "ETF" "Health Care Select Sector SPDR Fund" 39 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "XLY" "ETF" "Consumer Discretionary Select Sector SPDR Fund" 40 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))
add_symbol "SMCI" "Technology" "Super Micro Computer Inc." 41 && SUCCESSFUL_ADDS=$((SUCCESSFUL_ADDS + 1))

echo ""
echo "🎉 Population completed!"
echo "   Successfully added: $SUCCESSFUL_ADDS/41 symbols"

# Verify final count
FINAL_COUNT=$(curl -s http://localhost:11114/api/symbols/all | jq 'length')
echo "📊 Final symbol count in database: $FINAL_COUNT"

if [ $SUCCESSFUL_ADDS -eq 41 ] && [ "$FINAL_COUNT" -eq 41 ]; then
    echo ""
    echo "💡 The Symbol Management interface now controls the central list!"
    echo "   You can now:"
    echo "   1. View all symbols in the web interface"
    echo "   2. Activate/deactivate symbols"
    echo "   3. Change priorities and categories"
    echo "   4. Add new custom symbols"
    echo ""
    echo "🌐 Open http://localhost:11114/ and go to Symbol Management tab"
else
    echo ""
    echo "⚠️  Some symbols failed to add or count mismatch. Check the errors above."
fi
