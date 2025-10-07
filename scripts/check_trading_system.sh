#!/bin/bash
# Quick health check script for the entire live trading system
# Usage: ./scripts/check_trading_system.sh

set -e

echo "🏥 Live Trading System Health Check"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" == "ok" ]; then
        echo -e "${GREEN}✅${NC} $message"
    elif [ "$status" == "warn" ]; then
        echo -e "${YELLOW}⚠️${NC}  $message"
    else
        echo -e "${RED}❌${NC} $message"
    fi
}

# Check Live Trading Executor
echo "📊 Live Trading Executor"
echo "------------------------"

LTE_STATUS=$(kubectl get cronjob live-trading-executor -n default -o jsonpath='{.spec.suspend}' 2>/dev/null || echo "not_found")
if [ "$LTE_STATUS" == "not_found" ]; then
    print_status "error" "Live Trading Executor: NOT DEPLOYED"
elif [ "$LTE_STATUS" == "true" ]; then
    print_status "warn" "Live Trading Executor: SUSPENDED"
else
    print_status "ok" "Live Trading Executor: ACTIVE"
    
    # Get last run time
    LAST_SCHEDULE=$(kubectl get cronjob live-trading-executor -n default -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "")
    if [ -n "$LAST_SCHEDULE" ]; then
        echo "   Last run: $LAST_SCHEDULE"
    fi
    
    # Get recent job status
    RECENT_JOB=$(kubectl get jobs -n default -l app=live-trading-executor --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$RECENT_JOB" ]; then
        JOB_STATUS=$(kubectl get job "$RECENT_JOB" -n default -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "")
        if [ "$JOB_STATUS" == "Complete" ]; then
            print_status "ok" "Recent job: $RECENT_JOB - COMPLETED"
        else
            print_status "warn" "Recent job: $RECENT_JOB - $JOB_STATUS"
        fi
    fi
fi

echo ""

# Check Order Sync Worker
echo "🔄 Order Sync Worker"
echo "--------------------"

OSW_STATUS=$(kubectl get cronjob order-sync-worker -n default -o jsonpath='{.spec.suspend}' 2>/dev/null || echo "not_found")
if [ "$OSW_STATUS" == "not_found" ]; then
    print_status "error" "Order Sync Worker: NOT DEPLOYED"
elif [ "$OSW_STATUS" == "true" ]; then
    print_status "warn" "Order Sync Worker: SUSPENDED"
else
    print_status "ok" "Order Sync Worker: ACTIVE"
    
    # Get last run time
    LAST_SCHEDULE=$(kubectl get cronjob order-sync-worker -n default -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "")
    if [ -n "$LAST_SCHEDULE" ]; then
        echo "   Last run: $LAST_SCHEDULE"
    fi
    
    # Get recent job status
    RECENT_JOB=$(kubectl get jobs -n default -l app=order-sync-worker --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$RECENT_JOB" ]; then
        JOB_STATUS=$(kubectl get job "$RECENT_JOB" -n default -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "")
        if [ "$JOB_STATUS" == "Complete" ]; then
            print_status "ok" "Recent job: $RECENT_JOB - COMPLETED"
        else
            print_status "warn" "Recent job: $RECENT_JOB - $JOB_STATUS"
        fi
    fi
fi

echo ""

# Check Services
echo "🔧 Required Services"
echo "--------------------"

# Live Trading Service
LTS_READY=$(kubectl get deployment live-trading-service -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
LTS_DESIRED=$(kubectl get deployment live-trading-service -n default -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
if [ "$LTS_READY" == "$LTS_DESIRED" ] && [ "$LTS_READY" != "0" ]; then
    print_status "ok" "Live Trading Service: $LTS_READY/$LTS_DESIRED ready"
else
    print_status "error" "Live Trading Service: $LTS_READY/$LTS_DESIRED ready"
fi

# Strategy Service
SS_READY=$(kubectl get deployment strategy-service -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
SS_DESIRED=$(kubectl get deployment strategy-service -n default -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
if [ "$SS_READY" == "$SS_DESIRED" ] && [ "$SS_READY" != "0" ]; then
    print_status "ok" "Strategy Service: $SS_READY/$SS_DESIRED ready"
else
    print_status "error" "Strategy Service: $SS_READY/$SS_DESIRED ready"
fi

# TimescaleDB
DB_READY=$(kubectl get deployment timescaledb -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
DB_DESIRED=$(kubectl get deployment timescaledb -n default -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
if [ "$DB_READY" == "$DB_DESIRED" ] && [ "$DB_READY" != "0" ]; then
    print_status "ok" "TimescaleDB: $DB_READY/$DB_DESIRED ready"
else
    print_status "error" "TimescaleDB: $DB_READY/$DB_DESIRED ready"
fi

echo ""

# Check Database Orders
echo "💰 Order Status"
echo "---------------"

PENDING_COUNT=$(kubectl exec deployment/timescaledb -n default -- \
    psql -U admin -d trading -t -c \
    "SELECT COUNT(*) FROM live_trades WHERE status = 'PENDING';" 2>/dev/null | tr -d ' \r\n' || echo "0")
[ -z "$PENDING_COUNT" ] && PENDING_COUNT="0"

FILLED_TODAY=$(kubectl exec deployment/timescaledb -n default -- \
    psql -U admin -d trading -t -c \
    "SELECT COUNT(*) FROM live_trades WHERE status = 'FILLED' AND filled_at::date = CURRENT_DATE;" 2>/dev/null | tr -d ' \r\n' || echo "0")
[ -z "$FILLED_TODAY" ] && FILLED_TODAY="0"

REJECTED_TODAY=$(kubectl exec deployment/timescaledb -n default -- \
    psql -U admin -d trading -t -c \
    "SELECT COUNT(*) FROM live_trades WHERE status = 'REJECTED' AND created_at::date = CURRENT_DATE;" 2>/dev/null | tr -d ' \r\n' || echo "0")
[ -z "$REJECTED_TODAY" ] && REJECTED_TODAY="0"

if [ "$PENDING_COUNT" -gt 0 ]; then
    print_status "warn" "Pending Orders: $PENDING_COUNT (waiting for fill)"
else
    print_status "ok" "Pending Orders: $PENDING_COUNT"
fi

if [ "$FILLED_TODAY" -gt 0 ]; then
    print_status "ok" "Filled Today: $FILLED_TODAY"
else
    echo "   Filled Today: $FILLED_TODAY"
fi

if [ "$REJECTED_TODAY" -gt 0 ]; then
    print_status "warn" "Rejected Today: $REJECTED_TODAY"
else
    echo "   Rejected Today: $REJECTED_TODAY"
fi

echo ""

# Check Emergency Stop
echo "🚨 Emergency Controls"
echo "---------------------"

EMERGENCY_STOP=$(kubectl get configmap live-trading-executor-emergency-stop -n default -o jsonpath='{.data.emergency_stop}' 2>/dev/null || echo "unknown")
if [ "$EMERGENCY_STOP" == "false" ]; then
    print_status "ok" "Emergency Stop: INACTIVE (trading allowed)"
elif [ "$EMERGENCY_STOP" == "true" ]; then
    print_status "warn" "Emergency Stop: ACTIVE (trading halted)"
    STOP_REASON=$(kubectl get configmap live-trading-executor-emergency-stop -n default -o jsonpath='{.data.stop_reason}' 2>/dev/null || echo "")
    if [ -n "$STOP_REASON" ]; then
        echo "   Reason: $STOP_REASON"
    fi
else
    print_status "warn" "Emergency Stop: UNKNOWN (config not found)"
fi

echo ""

# Summary
echo "📋 Summary"
echo "----------"

# Determine overall status
OVERALL_STATUS="ok"

if [ "$LTE_STATUS" != "false" ] || [ "$OSW_STATUS" != "false" ]; then
    OVERALL_STATUS="warn"
fi

if [ "$LTS_READY" != "$LTS_DESIRED" ] || [ "$SS_READY" != "$SS_DESIRED" ] || [ "$DB_READY" != "$DB_DESIRED" ]; then
    OVERALL_STATUS="error"
fi

if [ "$EMERGENCY_STOP" == "true" ]; then
    OVERALL_STATUS="warn"
fi

if [ "$OVERALL_STATUS" == "ok" ]; then
    echo -e "${GREEN}✅ All systems operational${NC}"
elif [ "$OVERALL_STATUS" == "warn" ]; then
    echo -e "${YELLOW}⚠️  Some warnings detected (see above)${NC}"
else
    echo -e "${RED}❌ Critical issues detected (see above)${NC}"
fi

echo ""
echo "For more details, run:"
echo "  make -f Makefile.live-trading status-auto-trading"
echo "  make -f Makefile.order-sync status-sync-worker"
echo ""
echo "Documentation: docs/LIVE_TRADING_COMPLETE_STATUS.md"

