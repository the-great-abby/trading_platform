#!/bin/bash

# Consolidated Kubernetes Deployment Script
# Deploys the trading system using the new consolidated structure

set -e

NAMESPACE="trading-system"
REGISTRY="localhost:32000"

echo "🚀 Deploying Trading System (Consolidated Structure)"
echo "📊 Namespace: $NAMESPACE"
echo "🐳 Registry: $REGISTRY"
echo ""

# Function to apply YAML files
apply_yaml() {
    local file=$1
    local description=$2
    
    echo "📋 Applying $description..."
    kubectl apply -f "$file"
    echo "✅ $description applied successfully"
    echo ""
}

# Function to check if namespace exists
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        echo "📦 Creating namespace $NAMESPACE..."
        kubectl create namespace "$NAMESPACE"
        echo "✅ Namespace created"
        echo ""
    else
        echo "✅ Namespace $NAMESPACE already exists"
        echo ""
    fi
}

# Function to wait for deployments
wait_for_deployments() {
    echo "⏳ Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/strategy-service -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout=300s deployment/market-data-service -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout=300s deployment/market-data-worker -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout=300s deployment/backtest-api -n "$NAMESPACE"
    echo "✅ All core services are ready"
    echo ""
}

# Function to show service status
show_status() {
    echo "📊 Service Status:"
    echo "=================="
    kubectl get pods -n "$NAMESPACE" -o wide
    echo ""
    echo "🌐 Services:"
    echo "============"
    kubectl get services -n "$NAMESPACE"
    echo ""
    echo "📈 Deployments:"
    echo "==============="
    kubectl get deployments -n "$NAMESPACE"
    echo ""
}

# Main deployment process
main() {
    echo "🔍 Checking prerequisites..."
    check_namespace
    
    echo "🏗️  Deploying infrastructure..."
    apply_yaml "k8s/core/namespace.yaml" "Core namespace and secrets"
    apply_yaml "k8s/infrastructure/database.yaml" "Database infrastructure (PostgreSQL & Redis)"
    apply_yaml "k8s/infrastructure/rabbitmq.yaml" "RabbitMQ infrastructure"
    
    echo "⏳ Waiting for infrastructure to be ready..."
    sleep 30
    
    echo "🚀 Deploying core services..."
    apply_yaml "k8s/services/core-services.yaml" "Core trading services"
    
    echo "⏳ Waiting for core services..."
    sleep 30
    
    echo "📊 Deploying dashboard services..."
    apply_yaml "k8s/services/dashboard-services.yaml" "Dashboard and UI services"
    
    echo "⏳ Waiting for all services to be ready..."
    wait_for_deployments
    
    echo "🎉 Deployment completed successfully!"
    echo ""
    show_status
    
    echo "🌐 Access URLs:"
    echo "==============="
    echo "📈 Trading Dashboard: http://localhost:11001"
    echo "📊 Performance Dashboard: http://localhost:11000/dashboard"
    echo "🏥 Health Dashboard: http://localhost:11002/dashboard"
    echo "📰 RSS Dashboard: http://localhost:11005"
    echo "🔧 Backtest API: http://localhost:11031"
    echo ""
    echo "💡 To start port forwarding:"
    echo "   ./scripts/robust-port-forward.sh start"
    echo ""
}

# Run main function
main "$@" 