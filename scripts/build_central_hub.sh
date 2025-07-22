#!/bin/bash

# Build and Deploy Central Hub Dashboard
# This script builds the central hub dashboard and deploys it to Kubernetes

set -e

echo "🚀 Building Central Hub Dashboard..."

# Build the Docker image
docker build -t localhost:32000/central-hub-dashboard:latest services/central-hub-dashboard/

# Push to local registry
docker push localhost:32000/central-hub-dashboard:latest

echo "✅ Central Hub Dashboard built and pushed to registry"

# Deploy to Kubernetes
echo "📦 Deploying to Kubernetes..."
kubectl apply -f k8s/trading-platform-comprehensive.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/central-hub-dashboard -n trading-system

echo "🎉 Central Hub Dashboard deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: make central-hub"
echo "  2. Open: http://localhost:11080"
echo "  3. Navigate to all your services from one place!"
echo ""
echo "🔗 Available services from the hub:"
echo "   • Trading Dashboard"
echo "   • Health Dashboard" 
echo "   • Performance Dashboard"
echo "   • RSS Dashboard"
echo "   • Backtest Reports"
echo "   • API Gateway"
echo "   • Backtest API"
echo "   • Analytics Service" 