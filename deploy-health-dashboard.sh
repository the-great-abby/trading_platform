#!/bin/bash

# Health Dashboard Kubernetes Deployment Script
set -e

echo "🚀 Deploying Health Dashboard to Kubernetes..."

# Build the health dashboard Docker image
echo "📦 Building health dashboard Docker image..."
docker build -t health-dashboard:latest services/health-dashboard/

# Apply Kubernetes namespace if it doesn't exist
echo "📋 Applying namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply health dashboard deployment
echo "🔧 Deploying health dashboard service..."
kubectl apply -f k8s/health-dashboard.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for health dashboard deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/health-dashboard -n trading-system

# Check deployment status
echo "📊 Health Dashboard Deployment Status:"
kubectl get pods -n trading-system -l app=health-dashboard

# Get service information
echo "🌐 Health Dashboard Service:"
kubectl get svc health-dashboard -n trading-system

# Check if ingress is configured
echo "🔗 Ingress Configuration:"
kubectl get ingress trading-ingress -n trading-system

echo "✅ Health Dashboard deployment completed!"
echo ""
echo "📋 Access URLs:"
echo "  - Health Check: http://trading.example.com/health"
echo "  - Dashboard: http://trading.example.com/dashboard"
echo "  - Metrics API: http://trading.example.com/dashboard/api/metrics"
echo ""
echo "🔍 To check logs:"
echo "  kubectl logs -f deployment/health-dashboard -n trading-system"
echo ""
echo "🔍 To check service status:"
echo "  kubectl get pods -n trading-system -l app=health-dashboard" 