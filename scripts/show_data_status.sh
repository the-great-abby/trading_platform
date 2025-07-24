#!/bin/bash

echo "=== Current Data Status ==="
kubectl exec timescaledb-85dd6d8d96-ddr9m -n trading-system -- psql -U trading_user -d trading_bot -c "SELECT symbol, COUNT(*) as records, MIN(date) as earliest_date, MAX(date) as latest_date, COUNT(*) * 100.0 / 365 as coverage_pct FROM historical_prices GROUP BY symbol ORDER BY records DESC LIMIT 20;"

echo ""
echo "=== Recent Data Activity ==="
kubectl logs -n trading-system deployment/market-data-worker --tail=10 