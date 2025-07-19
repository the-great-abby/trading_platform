#!/bin/bash

# Deploy LLM Proxy Integration for Kubernetes Trading System
# This script updates the trading system to use your external LLM proxy

set -e

echo "🚀 Deploying LLM Proxy Integration for Kubernetes Trading System"
echo "================================================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to the right cluster
echo "🔍 Checking Kubernetes cluster connection..."
kubectl cluster-info

# Check if trading-system namespace exists
if ! kubectl get namespace trading-system &> /dev/null; then
    echo "❌ trading-system namespace not found. Please create it first."
    exit 1
fi

echo "✅ Connected to Kubernetes cluster with trading-system namespace"

# Step 1: Deploy the LLM proxy service
echo ""
echo "📦 Step 1: Deploying LLM Proxy Service..."
kubectl apply -f k8s/llm-proxy-service.yaml

# Step 2: Update the LLM service configuration
echo ""
echo "📦 Step 2: Updating LLM Service Configuration..."
kubectl apply -f k8s/llm-service.yaml

# Step 3: Check if the proxy service is accessible
echo ""
echo "🔍 Step 3: Testing LLM Proxy connectivity from within cluster..."

# Create a temporary pod to test connectivity
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: llm-proxy-test
  namespace: trading-system
spec:
  containers:
  - name: test
    image: curlimages/curl:latest
    command: ['sh', '-c', 'curl -f http://llm-proxy:8081/ && echo "✅ Proxy accessible" || echo "❌ Proxy not accessible"']
  restartPolicy: Never
EOF

# Wait for the test pod to complete
echo "   Waiting for connectivity test..."
kubectl wait --for=condition=Ready pod/llm-proxy-test -n trading-system --timeout=30s
kubectl logs llm-proxy-test -n trading-system

# Clean up test pod
kubectl delete pod llm-proxy-test -n trading-system

# Step 4: Restart LLM service to pick up new configuration
echo ""
echo "🔄 Step 4: Restarting LLM Service..."
kubectl rollout restart deployment/llm-service -n trading-system
kubectl rollout restart deployment/llm-worker -n trading-system

# Wait for rollout to complete
echo "   Waiting for LLM service rollout..."
kubectl rollout status deployment/llm-service -n trading-system --timeout=120s
kubectl rollout status deployment/llm-worker -n trading-system --timeout=120s

# Step 5: Verify the deployment
echo ""
echo "✅ Step 5: Verifying deployment..."

echo "   Checking LLM service pods:"
kubectl get pods -n trading-system -l app=llm-service

echo "   Checking LLM worker pods:"
kubectl get pods -n trading-system -l app=llm-worker

echo "   Checking LLM proxy service:"
kubectl get service llm-proxy -n trading-system

# Step 6: Test the integration
echo ""
echo "🧪 Step 6: Testing LLM Service Integration..."

# Get the LLM service URL
LLM_SERVICE_URL=$(kubectl get service llm-service -n trading-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$LLM_SERVICE_URL" ]; then
    # If no LoadBalancer, use port-forward
    echo "   Setting up port-forward for LLM service..."
    kubectl port-forward service/llm-service 8008:8008 -n trading-system &
    PF_PID=$!
    sleep 5
    LLM_SERVICE_URL="http://localhost:8008"
fi

echo "   Testing LLM service health at $LLM_SERVICE_URL/health"
curl -f "$LLM_SERVICE_URL/health" || echo "❌ Health check failed"

# Clean up port-forward if we started it
if [ ! -z "$PF_PID" ]; then
    kill $PF_PID 2>/dev/null || true
fi

echo ""
echo "🎉 LLM Proxy Integration Deployment Complete!"
echo "=============================================="
echo ""
echo "📋 Summary:"
echo "   ✅ LLM Proxy Service deployed"
echo "   ✅ LLM Service updated to use proxy"
echo "   ✅ LLM Workers updated to use proxy"
echo "   ✅ Services restarted with new configuration"
echo ""
echo "🔗 Your trading system is now using your LLM proxy at:"
echo "   External: http://localhost:8081"
echo "   Internal: http://llm-proxy:8081"
echo ""
echo "📊 To monitor the integration:"
echo "   kubectl logs -f deployment/llm-service -n trading-system"
echo "   kubectl logs -f deployment/llm-worker -n trading-system"
echo ""
echo "🔄 To revert to Ollama (if needed):"
echo "   kubectl apply -f k8s/ollama-deployment.yaml"
echo "   Update LLM_SERVICE_CONFIG base_url to 'http://ollama:11434'" 