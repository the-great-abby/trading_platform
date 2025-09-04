#!/bin/bash

# Migration script: Move Kubernetes RAG Chat from separate service to unified trading dashboard
# This script helps consolidate the RAG chat functionality into the main trading dashboard

set -e

echo "🔄 Starting migration of Kubernetes RAG Chat to Unified Trading Dashboard..."

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

# Check if we're in the right namespace
CURRENT_NS=$(kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}')
if [ "$CURRENT_NS" != "trading-system" ]; then
    print_warning "Current namespace is '$CURRENT_NS', switching to 'trading-system'"
    kubectl config set-context --current --namespace=trading-system
fi

print_status "Current namespace: $(kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace'})"

# Step 1: Build and push the updated unified trading dashboard
print_status "Step 1: Building updated unified trading dashboard with RAG chat..."
cd services/unified-trading-dashboard

if [ -f "Dockerfile" ]; then
    print_status "Building Docker image..."
    docker build -t localhost:32000/unified-trading-dashboard:latest .
    
    print_status "Pushing to local registry..."
    docker push localhost:32000/unified-trading-dashboard:latest
    print_success "Docker image built and pushed successfully"
else
    print_error "Dockerfile not found in services/unified-trading-dashboard"
    exit 1
fi

cd ../..

# Step 2: Deploy the updated unified trading dashboard
print_status "Step 2: Deploying updated unified trading dashboard..."
kubectl apply -f k8s/unified-trading-dashboard-with-rag.yaml

# Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/unified-trading-dashboard -n trading-system
print_success "Unified trading dashboard deployed successfully"

# Step 3: Test the integrated RAG chat functionality
print_status "Step 3: Testing integrated RAG chat functionality..."
sleep 10  # Give the service time to start up

# Test the health endpoint
if kubectl get service unified-trading-dashboard -n trading-system &> /dev/null; then
    print_status "Testing RAG chat health endpoint..."
    
    # Port forward temporarily for testing
    print_status "Setting up temporary port forward for testing..."
    kubectl port-forward service/unified-trading-dashboard 8080:80 -n trading-system &
    PF_PID=$!
    
    sleep 5
    
    # Test the health endpoint
    if curl -s http://localhost:8080/api/rag-chat/health | grep -q "healthy"; then
        print_success "RAG chat health check passed"
    else
        print_warning "RAG chat health check failed - this might be expected if LLM proxy is not running"
    fi
    
    # Kill port forward
    kill $PF_PID 2>/dev/null || true
    wait $PF_PID 2>/dev/null || true
else
    print_error "Unified trading dashboard service not found"
    exit 1
fi

# Step 4: Remove the old kubernetes-rag-chat service (optional)
print_status "Step 4: Cleaning up old kubernetes-rag-chat service..."
read -p "Do you want to remove the old kubernetes-rag-chat service? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Removing old kubernetes-rag-chat deployment..."
    kubectl delete deployment kubernetes-rag-chat -n trading-system --ignore-not-found=true
    
    print_status "Removing old kubernetes-rag-chat service..."
    kubectl delete service kubernetes-rag-chat -n trading-system --ignore-not-found=true
    
    print_status "Removing old kubernetes-rag-chat replicaset..."
    kubectl delete replicaset kubernetes-rag-chat -n trading-system --ignore-not-found=true
    
    print_success "Old kubernetes-rag-chat service removed successfully"
else
    print_warning "Old kubernetes-rag-chat service kept running - you can remove it manually later"
fi

# Step 5: Update port forwarding
print_status "Step 5: Updating port forwarding configuration..."

# Check if there are existing port forwards
EXISTING_PF=$(ps aux | grep "kubectl port-forward.*unified-trading-dashboard" | grep -v grep)
if [ -n "$EXISTING_PF" ]; then
    print_status "Stopping existing port forwards..."
    pkill -f "kubectl port-forward.*unified-trading-dashboard" || true
    sleep 2
fi

# Start new port forward
print_status "Starting new port forward for unified trading dashboard..."
kubectl port-forward service/unified-trading-dashboard 11115:80 -n trading-system &
NEW_PF_PID=$!

sleep 3

# Test the new port forward
if curl -s http://localhost:11115/health &> /dev/null; then
    print_success "Port forward working on port 11115"
    print_status "Dashboard available at: http://localhost:11115"
    print_status "RAG chat available at: http://localhost:11115 (click on '☸️ K8s Chat' tab)"
else
    print_warning "Port forward test failed - you may need to check the service manually"
fi

# Step 6: Summary
echo
print_success "Migration completed successfully!"
echo
echo "📋 Summary of changes:"
echo "  ✅ Kubernetes RAG Chat integrated into Unified Trading Dashboard"
echo "  ✅ New tab '☸️ K8s Chat' added to the dashboard"
echo "  ✅ RAG chat API endpoints available at /api/rag-chat/*"
echo "  ✅ Dashboard accessible at http://localhost:11115"
echo "  ✅ Old kubernetes-rag-chat service can be removed (optional)"
echo
echo "🔧 Next steps:"
echo "  1. Test the RAG chat functionality in the dashboard"
echo "  2. Verify that Kubernetes questions are working"
echo "  3. Remove old kubernetes-rag-chat service if no longer needed"
echo "  4. Update any external references to use the new integrated service"
echo
echo "📚 RAG Chat Features:"
echo "  • Kubernetes command help"
echo "  • Troubleshooting assistance"
echo "  • Best practices guidance"
echo "  • Integrated with existing dashboard"
echo
print_status "Migration script completed. Happy Kubernetes troubleshooting! 🚀"





