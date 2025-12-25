#!/bin/bash
# Verify Capital Allocation Fix
# =============================
# This script verifies that the capital allocation fixes have been applied

echo "======================================================================"
echo "CAPITAL ALLOCATION & EXIT MONITORING VERIFICATION"
echo "======================================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "1. Checking Risk Profiles in Database..."
echo "----------------------------------------------------------------------"

kubectl exec -n trading-system deployment/timescaledb -- psql -U trading_user -d trading_db -c "
SELECT 
    account_id,
    max_position_size,
    max_portfolio_risk,
    max_daily_loss,
    max_daily_trades,
    updated_at
FROM risk_profiles;
" 2>/dev/null

echo ""
echo "2. Checking for Positions Exceeding Loss Limits..."
echo "----------------------------------------------------------------------"

kubectl exec -n trading-system deployment/timescaledb -- psql -U trading_user -d trading_db -c "
SELECT 
    symbol,
    strategy,
    entry_price,
    current_price,
    unrealized_pnl,
    unrealized_pnl_pct,
    created_at
FROM live_positions
WHERE status = 'OPEN'
    AND unrealized_pnl_pct <= -0.08
ORDER BY unrealized_pnl_pct ASC;
" 2>/dev/null

echo ""
echo "3. Checking Position Monitor Cronjobs..."
echo "----------------------------------------------------------------------"

kubectl get cronjobs -n trading-system -l component=monitoring

echo ""
echo "4. Checking Recent Cronjob Runs..."
echo "----------------------------------------------------------------------"

kubectl get jobs -n trading-system -l component=monitoring --sort-by=.metadata.creationTimestamp | tail -10

echo ""
echo "5. Expected Risk Profile Values:"
echo "----------------------------------------------------------------------"
echo "  Max Position Size: \$800.00 (20% of \$4,000 portfolio)"
echo "  Max Portfolio Risk: 0.15 (15%)"
echo "  Max Daily Loss: \$200.00 (5% of \$4,000 portfolio)"
echo "  Max Daily Trades: 10"

echo ""
echo "======================================================================"
echo "VERIFICATION COMPLETE"
echo "======================================================================"

echo ""
echo -e "${GREEN}✅ If the above values match expected values, the fix was successful!${NC}"
echo -e "${YELLOW}⚠️  If positions exceed 8% loss, run the emergency exit script${NC}"
echo -e "${RED}❌ If risk profiles don't match, run the fix job again${NC}"









