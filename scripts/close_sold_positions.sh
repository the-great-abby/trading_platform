#!/bin/bash
# Close positions that were sold but not updated by sync workers

ACCOUNT_ID="19c25392-8b61-4b71-a344-0eb04d275528"

echo "🔄 Closing sold positions..."
echo ""

# Get a live-trading-service pod
POD=$(kubectl get pods -n default -l app=live-trading-service -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD" ]; then
    echo "❌ No live-trading-service pod found"
    exit 1
fi

echo "📊 Current open positions:"
kubectl exec -n default $POD -- curl -s "http://live-trading-service.default.svc.cluster.local:8080/api/v1/trading/positions?account_id=${ACCOUNT_ID}" | python3 -m json.tool

echo ""
echo "❓ Enter symbols to close (comma-separated, e.g., GOOGL,MSFT): "
read SYMBOLS

if [ -z "$SYMBOLS" ]; then
    echo "❌ No symbols provided"
    exit 1
fi

# Convert comma-separated list to array
IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"

for SYMBOL in "${SYMBOL_ARRAY[@]}"; do
    SYMBOL=$(echo $SYMBOL | xargs)  # Trim whitespace
    echo ""
    echo "💵 Closing position for $SYMBOL..."
    
    # Close the position via SQL
    kubectl exec -n trading-system $(kubectl get pods -n trading-system -l app=timescaledb -o jsonpath='{.items[0].metadata.name}') -- \
        psql -U trading_user -d trading_bot -c "\
        UPDATE live_trading_positions \
        SET status = 'CLOSED', \
            closed_at = NOW(), \
            updated_at = NOW() \
        WHERE symbol = '$SYMBOL' \
          AND account_id = '$ACCOUNT_ID' \
          AND status = 'OPEN' \
        RETURNING position_id, symbol, quantity, average_price;" | cat
    
    echo "✅ Position $SYMBOL closed"
done

echo ""
echo "📊 Updated positions:"
kubectl exec -n default $POD -- curl -s "http://live-trading-service.default.svc.cluster.local:8080/api/v1/trading/positions?account_id=${ACCOUNT_ID}" | python3 -m json.tool

echo ""
echo "✅ Done!"

