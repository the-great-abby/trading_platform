#!/bin/bash
# Port forward script that properly detaches

NAMESPACE="default"
SERVICE_NAME="live-trading-service"
LOCAL_PORT="11120"
REMOTE_PORT="8080"

echo "Attempting to start port-forward for ${SERVICE_NAME}..."

# Check if port is already in use
if lsof -i :${LOCAL_PORT} > /dev/null; then
    echo "Port ${LOCAL_PORT} is already in use. Checking if it's our port-forward..."
    PF_PID=$(lsof -t -i :${LOCAL_PORT})
    if ps -p $PF_PID -o command | grep -q "kubectl port-forward"; then
        echo "✅ Existing kubectl port-forward found on port ${LOCAL_PORT} (PID: ${PF_PID})."
        echo "🔗 Service available at http://localhost:${LOCAL_PORT}"
        echo "🛑 To stop: kill ${PF_PID}"
        exit 0
    else
        echo "❌ Port ${LOCAL_PORT} is in use by another process (PID: ${PF_PID}). Please stop it manually."
        exit 1
    fi
fi

# Start port-forward in the background using nohup to prevent cursor capture
nohup kubectl port-forward -n ${NAMESPACE} svc/${SERVICE_NAME} ${LOCAL_PORT}:${REMOTE_PORT} > /tmp/live_trading_port_forward.log 2>&1 &

# Get the PID of the background process
PF_PID=$!

echo "Waiting for port-forward to establish (PID: ${PF_PID})..."
sleep 5 # Give it a few seconds to start

# Check if the port-forward process is still running
if ps -p $PF_PID > /dev/null; then
    echo "✅ Port forward active (PID: ${PF_PID})"
    echo "🔗 Service available at http://localhost:${LOCAL_PORT}"
    echo "🛑 To stop: kill ${PF_PID}"
else
    echo "❌ Port forward failed to start. Check /tmp/live_trading_port_forward.log for details."
    exit 1
fi
