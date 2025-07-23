#!/bin/bash

echo "🚀 Deploying Minimal Trading Platform..."

# Delete existing deployments to free up resources
echo "🗑️  Cleaning up existing deployments..."
kubectl delete deployment -n trading-system --all --grace-period=0 --force

# Wait for cleanup
echo "⏳ Waiting for cleanup..."
sleep 30

# Deploy minimal configuration
echo "📦 Deploying minimal configuration..."
kubectl apply -f k8s/trading-platform-minimal.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/trading-core-service -n trading-system
kubectl wait --for=condition=available --timeout=300s deployment/ai-analysis-service -n trading-system
kubectl wait --for=condition=available --timeout=300s deployment/central-hub-dashboard -n trading-system
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n trading-system
kubectl wait --for=condition=available --timeout=300s deployment/trading-gateway -n trading-system

# Show status
echo "📊 Current pod status:"
kubectl get pods -n trading-system

echo "✅ Minimal deployment complete!"
echo ""
echo "🌐 Access your services:"
echo "   Central Hub: http://localhost:11080/"
echo "   AI Analysis: http://localhost:11085/"
echo "   Trading Core: http://localhost:11090/"
echo "   Gateway: http://localhost:11081/" 