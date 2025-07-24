#!/bin/bash

echo "🚀 Starting Data Fetching Dashboard..."
echo ""
echo "Setting up port forwarding for Central Hub Dashboard..."
echo "Data Fetching Dashboard will be available at: http://localhost:11001/data-fetch"
echo ""
echo "Press Ctrl+C to stop port forwarding"

# Start port forwarding for central hub dashboard
kubectl port-forward -n trading-system service/central-hub-dashboard 11001:80 