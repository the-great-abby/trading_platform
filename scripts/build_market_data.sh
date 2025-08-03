#!/bin/bash

# Build and deploy Market Data Service
set -e

echo "📊 Building Market Data Service..."

# Build Docker image
docker build -t localhost:32000/market-data-service:latest -f services/market-data-service/Dockerfile .

# Push to local registry
docker push localhost:32000/market-data-service:latest

echo "✅ Market Data Service image built and pushed"

# Deploy to Kubernetes
echo "🚀 Deploying Market Data Service to Kubernetes..."

# Apply the deployment
kubectl apply -f k8s/market-data-service.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for Market Data Service to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/market-data-service -n trading-system

echo "✅ Market Data Service deployed successfully!"

# Check service status
echo "📊 Service Status:"
kubectl get pods -n trading-system | grep market-data-service

echo ""
echo "🔗 Access Market Data Service:"
echo "  - Health Check: http://localhost:11084/health"
echo "  - Cache Status: http://localhost:11084/cache/status"
echo "  - Historical Data: POST http://localhost:11084/market-data/historical"
echo ""
echo "💡 Test the service:"
echo "  curl -X POST http://localhost:11084/market-data/historical -H 'Content-Type: application/json' -d '{\"symbol\": \"AAPL\", \"start_date\": \"2024-12-01\", \"end_date\": \"2024-12-31\"}'"
echo "  curl -X POST http://localhost:11084/cache/clear"
echo "" 