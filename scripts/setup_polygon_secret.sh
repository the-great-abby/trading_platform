#!/bin/bash

# Setup Polygon API Key Secret for Kubernetes
# This script creates a Kubernetes secret with your Polygon.io API key

echo "🔐 Setting up Polygon API Key Secret for Kubernetes"
echo "=" * 60

# Check if POLYGON_API_KEY is set
if [ -z "$POLYGON_API_KEY" ]; then
    echo "❌ POLYGON_API_KEY environment variable not set"
    echo "   Please set your Polygon.io API key:"
    echo "   export POLYGON_API_KEY='your_api_key_here'"
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to Kubernetes cluster"
    echo "   Please ensure kubectl is configured correctly"
    exit 1
fi

echo "✅ Kubernetes cluster connection verified"
echo "🔑 Using Polygon API key: ${POLYGON_API_KEY:0:10}..."

# Create the secret
echo "📦 Creating Polygon API key secret..."
kubectl create secret generic polygon-secret \
    --namespace=trading-system \
    --from-literal=api-key="$POLYGON_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

if [ $? -eq 0 ]; then
    echo "✅ Polygon API key secret created successfully"
    echo "📋 Secret details:"
    kubectl get secret polygon-secret -n trading-system -o yaml | grep -v "api-key:"
else
    echo "❌ Failed to create Polygon API key secret"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now run news jobs in Kubernetes:"
echo ""
echo "📰 To fetch historical news:"
echo "   kubectl apply -f k8s/news-fetch-job.yaml"
echo ""
echo "🔄 To set up regular news scanning:"
echo "   kubectl apply -f k8s/news-scanning-cronjob.yaml"
echo ""
echo "🧪 To run news-enhanced backtests:"
echo "   kubectl apply -f k8s/news-backtest-job.yaml"
echo ""
echo "📊 To check job status:"
echo "   kubectl get jobs -n trading-system"
echo "   kubectl get cronjobs -n trading-system" 