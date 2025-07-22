#!/bin/bash

# Build and deploy AI Analysis Service
set -e

echo "🤖 Building AI Analysis Service..."

# Build Docker image
cd services/ai-analysis-service
docker build -t localhost:32000/ai-analysis-service:latest .

# Push to local registry
docker push localhost:32000/ai-analysis-service:latest

echo "✅ AI Analysis Service image built and pushed"

# Deploy to Kubernetes
echo "🚀 Deploying AI Analysis Service to Kubernetes..."

# Apply the deployment
kubectl apply -f ../../k8s/trading-platform-comprehensive.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for AI Analysis Service to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ai-analysis-service -n trading-system

echo "✅ AI Analysis Service deployed successfully!"

# Check service status
echo "📊 Service Status:"
kubectl get pods -n trading-system | grep ai-analysis-service

echo ""
echo "🔗 Access AI Analysis Service:"
echo "  - Health Check: http://localhost:8085/health"
echo "  - API Docs: http://localhost:8085/docs"
echo "  - Daily Recommendations: http://localhost:8085/api/recommendations/daily"
echo ""
echo "💡 Test the service:"
echo "  curl -X POST http://localhost:8085/api/analyze/symbol/AAPL"
echo "" 