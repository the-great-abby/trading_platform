#!/bin/bash

# Persistent Port Forward Script
# Automatically restarts port forwarding when it dies

SERVICE_NAME="trading-ultra-service"
NAMESPACE="trading-system"
LOCAL_PORT="11100"
REMOTE_PORT="80"

echo "🔄 Starting persistent port forward for $SERVICE_NAME..."

while true; do
    echo "📡 Port forwarding $LOCAL_PORT -> $SERVICE_NAME:$REMOTE_PORT"
    kubectl port-forward service/$SERVICE_NAME $LOCAL_PORT:$REMOTE_PORT -n $NAMESPACE --address=0.0.0.0
    
    echo "⚠️  Port forward died, restarting in 5 seconds..."
    sleep 5
done 