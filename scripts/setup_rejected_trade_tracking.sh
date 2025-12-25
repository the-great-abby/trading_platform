#!/bin/bash
# Setup script for Rejected Trade Tracking feature

set -e  # Exit on error

echo "🚀 Setting up Rejected Trade Tracking feature..."
echo ""

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found at .venv"
    exit 1
fi

echo "1️⃣  Activating virtual environment..."
source .venv/bin/activate

echo "2️⃣  Checking database connection..."
# Check if port-forward is running
if ! ps aux | grep -v grep | grep "kubectl port-forward.*postgres-timescale-external.*5432" > /dev/null; then
    echo "⚠️  Database port-forward not detected"
    echo "   Starting port-forward to TimescaleDB (postgres-infra namespace)..."
    kubectl port-forward -n postgres-infra service/postgres-timescale-external 5432:5432 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    echo "   Port-forward started (PID: $PORT_FORWARD_PID)"
    sleep 3  # Wait for port-forward to establish
else
    echo "✅ Database port-forward already running"
fi

echo "3️⃣  Running database migration..."
if alembic upgrade head; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

echo "4️⃣  Verifying table creation..."
PGPASSWORD="${DB_PASSWORD:-postgres}" psql \
    -h localhost \
    -p 5432 \
    -U postgres \
    -d trading_bot \
    -c "SELECT COUNT(*) as initial_count FROM rejected_trade_attempts;" || {
    echo "⚠️  Could not verify table (this is okay if credentials are different)"
}

echo "5️⃣  Restarting live-trading-service..."
if kubectl rollout restart deployment/live-trading-service -n trading-system > /dev/null 2>&1; then
    echo "✅ Live trading service restart initiated"
    echo "   Waiting for rollout to complete..."
    kubectl rollout status deployment/live-trading-service -n trading-system --timeout=60s
else
    echo "⚠️  Could not restart live trading service via kubectl"
    echo "   You may need to restart manually if running locally"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Next steps:"
echo "   1. Run the live trading monitor:"
echo "      python scripts/live_trading_monitor_api.py"
echo ""
echo "   2. Or query the API directly:"
echo "      curl 'http://localhost:11120/api/v1/trading/rejected-attempts?account_id=19c25392-8b61-4b71-a344-0eb04d275528'"
echo ""
echo "   3. View documentation:"
echo "      cat REJECTED_TRADE_TRACKING.md"
echo ""

