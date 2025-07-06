#!/bin/bash

# Comprehensive Kubernetes Deployment Script for Trading System
set -e

echo "🚀 Deploying Trading System to Kubernetes..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

print_status "Building Docker images..."

# Build health dashboard image
print_status "Building health dashboard image..."
docker build -t health-dashboard:latest services/health-dashboard/

# Build other service images if they exist
if [ -f "services/trading-service/Dockerfile" ]; then
    print_status "Building trading service image..."
    docker build -t trading-service:latest services/trading-service/
fi

if [ -f "services/market-data-service/Dockerfile" ]; then
    print_status "Building market data service image..."
    docker build -t market-data-service:latest services/market-data-service/
fi

print_status "Applying Kubernetes resources..."

# Apply namespace
kubectl apply -f k8s/namespace.yaml
print_success "Namespace applied"

# Apply Redis deployment
kubectl apply -f k8s/redis-deployment.yaml
print_success "Redis deployment applied"

# Apply health dashboard
kubectl apply -f k8s/health-dashboard.yaml
print_success "Health dashboard deployment applied"

# Apply other services if they exist
if [ -f "k8s/trading-service.yaml" ]; then
    kubectl apply -f k8s/trading-service.yaml
    print_success "Trading service deployment applied"
fi

# Apply ingress
kubectl apply -f k8s/ingress.yaml
print_success "Ingress applied"

# Wait for deployments to be ready
print_status "Waiting for deployments to be ready..."

# Wait for Redis
kubectl wait --for=condition=available --timeout=300s deployment/redis-dev -n trading-system
print_success "Redis is ready"

# Wait for health dashboard
kubectl wait --for=condition=available --timeout=300s deployment/health-dashboard -n trading-system
print_success "Health dashboard is ready"

# Display deployment status
echo ""
print_status "Deployment Status:"
kubectl get pods -n trading-system

echo ""
print_status "Services:"
kubectl get svc -n trading-system

echo ""
print_status "Ingress:"
kubectl get ingress -n trading-system

echo ""
print_success "🎉 Trading System deployment completed!"
echo ""
echo "📋 Access URLs:"
echo "  - Health Dashboard: http://trading.example.com/dashboard"
echo "  - Health Check: http://trading.example.com/health"
echo "  - Metrics API: http://trading.example.com/dashboard/api/metrics"
echo ""
echo "🔍 Useful Commands:"
echo "  - View logs: kubectl logs -f deployment/health-dashboard -n trading-system"
echo "  - Check status: kubectl get pods -n trading-system"
echo "  - Port forward: kubectl port-forward svc/health-dashboard 8080:80 -n trading-system"
echo "  - Delete deployment: kubectl delete -f k8s/ -n trading-system" 