#!/bin/bash

# Port Watcher Launcher
# Monitors kubectl port-forward connections and captures logs on failure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WATCHER_SCRIPT="$SCRIPT_DIR/port_watcher_v2.py"
LOG_DIR="$PROJECT_DIR/port_watcher_logs"

echo "🚀 Starting Comprehensive Port Watcher..."
echo "📁 Log directory: $LOG_DIR"
echo "📝 Watcher log: $PROJECT_DIR/port_watcher.log"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Port Watcher..."
    
    # Kill any existing port forwarding processes
    echo "🧹 Cleaning up existing port forwarding processes..."
    pkill -f "kubectl port-forward" || true
    
    # Kill the watcher process
    if [ ! -z "$WATCHER_PID" ]; then
        echo "🔄 Terminating watcher process (PID: $WATCHER_PID)"
        kill "$WATCHER_PID" 2>/dev/null || true
    fi
    
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo "Please ensure kubectl is configured correctly"
    exit 1
fi

# Check if trading-system namespace exists
if ! kubectl get namespace trading-system &> /dev/null; then
    echo "❌ Error: trading-system namespace not found"
    echo "Please ensure the trading system is deployed"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start the port watcher
echo "🔍 Starting comprehensive port monitoring..."
cd "$PROJECT_DIR"
python3 "$WATCHER_SCRIPT" &
WATCHER_PID=$!

echo "📊 Port Watcher started (PID: $WATCHER_PID)"
echo "📋 Monitoring ALL trading system services:"
echo ""
echo "🔧 Core Monitoring:"
echo "   • Grafana (11102:3000)"
echo "   • Prometheus (11101:9090)"
echo "   • Infrastructure Metrics (11103:11103)"
echo ""
echo "💼 Core Trading Services:"
echo "   • Strategy Service (11104:80)"
echo "   • Trading Service (11105:80)"
echo "   • Order Service (11106:80)"
echo "   • Portfolio Service (11107:80)"
echo "   • Risk Service (11108:80)"
echo "   • Market Data Service (11109:80)"
echo ""
echo "🤖 AI & Analytics:"
echo "   • AI Analysis Service (11110:11085)"
echo "   • AI Stock Dashboard (11111:80)"
echo "   • LLM Service (11112:11109)"
echo "   • Analytics Service (11113:80)"
echo ""
echo "📊 Dashboards:"
echo "   • Health Dashboard (11114:80)"
echo "   • Performance Dashboard (11115:80)"
echo "   • Central Hub Dashboard (11116:80)"
echo "   • RSS Dashboard (11117:80)"
echo "   • Trading Dashboard (11118:8080)"
echo ""
echo "🧪 Backtesting:"
echo "   • Backtest API (11119:11101)"
echo "   • Backtest Request Service (11120:80)"
echo ""
echo "📈 Data & Processing:"
echo "   • Data Processing Service (11121:11095)"
echo "   • Market Data Worker (11122:11108)"
echo "   • Postgres Vector Storage (11123:80)"
echo ""
echo "⚙️ Management Services:"
echo "   • Strategy Management (11124:8000)"
echo "   • Order Management (11125:8000)"
echo "   • Signal Management (11126:8002)"
echo "   • Risk Management (11127:8003)"
echo ""
echo "🔔 Additional Services:"
echo "   • Notification Service (11128:80)"
echo "   • Public API (11129:80)"
echo "   • Report Viewer Service (11130:80)"
echo "   • RSS Feed Service (11131:11004)"
echo "   • Trading Core Service (11132:11090)"
echo "   • Trading Ultra Service (11133:80)"
echo "   • Metrics Test Service (11134:11100)"
echo ""
echo "📝 Logs will be saved to: $LOG_DIR/"
echo "📄 Main watcher log: port_watcher.log"
echo ""
echo "🛑 Press Ctrl+C to stop the watcher"
echo ""

# Wait for the watcher process
wait "$WATCHER_PID" 