#!/bin/bash

# Setup Architecture RAG Chat System
# This script builds and deploys the architecture vectorizer and updates the trading dashboard

set -e

echo "🚀 Setting up Architecture RAG Chat System..."

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

# Step 1: Build and push the architecture vectorizer
print_status "Step 1: Building architecture vectorizer..."
cd services/architecture-vectorizer

if [ -f "Dockerfile" ]; then
    print_status "Building Docker image..."
    docker build -t localhost:32000/architecture-vectorizer:latest .
    
    print_status "Pushing to local registry..."
    docker push localhost:32000/architecture-vectorizer:latest
    print_success "Architecture vectorizer built and pushed successfully"
else
    print_error "Dockerfile not found in services/architecture-vectorizer"
    exit 1
fi

cd ../..

# Step 2: Build and push the updated unified trading dashboard
print_status "Step 2: Building updated unified trading dashboard with RAG chat..."
cd services/unified-trading-dashboard

if [ -f "Dockerfile" ]; then
    print_status "Building Docker image..."
    docker build -t localhost:32000/unified-trading-dashboard:latest .
    
    print_status "Pushing to local registry..."
    docker push localhost:32000/unified-trading-dashboard:latest
    print_success "Unified trading dashboard built and pushed successfully"
else
    print_error "Dockerfile not found in services/unified-trading-dashboard"
    exit 1
fi

cd ../..

# Step 3: Deploy the architecture vectorizer
print_status "Step 3: Deploying architecture vectorizer..."
kubectl apply -f k8s/architecture-vectorizer.yaml

# Wait for deployment to be ready
print_status "Waiting for architecture vectorizer to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/architecture-vectorizer -n trading-system
print_success "Architecture vectorizer deployed successfully"

# Step 4: Deploy the updated unified trading dashboard
print_status "Step 4: Deploying updated unified trading dashboard..."
kubectl apply -f k8s/unified-trading-dashboard-with-rag.yaml

# Wait for deployment to be ready
print_status "Waiting for unified trading dashboard to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/unified-trading-dashboard -n trading-system
print_success "Unified trading dashboard deployed successfully"

# Step 5: Run initial vectorization
print_status "Step 5: Running initial vectorization of repository..."
print_status "This will scan your docs folder and other repository files..."

# Create a one-time vectorization job
kubectl create job --from=cronjob/architecture-vectorizer-job initial-vectorization -n trading-system

print_status "Initial vectorization job created. Check logs with:"
print_status "kubectl logs job/initial-vectorization -n trading-system -f"

# Step 6: Test the system
print_status "Step 6: Testing the RAG chat system..."
sleep 10  # Give the services time to start up

# Test the trading dashboard
if kubectl get service unified-trading-dashboard -n trading-system &> /dev/null; then
    print_status "Testing unified trading dashboard..."
    
    # Port forward temporarily for testing
    print_status "Setting up temporary port forward for testing..."
    kubectl port-forward service/unified-trading-dashboard 8080:80 -n trading-system &
    PF_PID=$!
    
    sleep 5
    
    # Test the health endpoint
    if curl -s http://localhost:8080/health | grep -q "healthy"; then
        print_success "Trading dashboard health check passed"
    else
        print_warning "Trading dashboard health check failed"
    fi
    
    # Test the RAG chat endpoint
    if curl -s http://localhost:8080/api/rag-chat/health | grep -q "healthy"; then
        print_success "RAG chat health check passed"
    else
        print_warning "RAG chat health check failed"
    fi
    
    # Kill port forward
    kill $PF_PID 2>/dev/null || true
    wait $PF_PID 2>/dev/null || true
else
    print_error "Unified trading dashboard service not found"
    exit 1
fi

# Step 7: Update port forwarding
print_status "Step 7: Updating port forwarding configuration..."

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

# Step 8: Summary
echo
print_success "Architecture RAG Chat System setup completed successfully!"
echo
echo "📋 Summary of what was deployed:"
echo "  ✅ Architecture Vectorizer Service - Scans your repo for documentation"
echo "  ✅ Updated Unified Trading Dashboard - Now with real RAG chat functionality"
echo "  ✅ Vector Storage Integration - Uses your postgres-vector-storage database"
echo "  ✅ Background Vectorization - Runs every 6 hours to keep knowledge fresh"
echo
echo "🔧 How it works:"
echo "  1. Architecture Vectorizer scans your docs/, k8s/, services/, and src/ folders"
echo "  2. Documents are chunked and vectorized into your postgres-vector-storage"
echo "  3. RAG chat searches this knowledge base for relevant answers"
echo "  4. LLM proxy generates intelligent responses based on your architecture docs"
echo
echo "📚 What gets vectorized:"
echo "  • All .md files (documentation, READMEs, guides)"
echo "  • Kubernetes YAML files (deployments, services, configs)"
echo "  • Python files (docstrings and comments)"
echo "  • Shell scripts and configuration files"
echo
echo "🚀 Next steps:"
echo "  1. Wait for initial vectorization to complete (check logs above)"
echo "  2. Test the RAG chat by asking questions about your architecture"
echo "  3. The system will automatically keep knowledge fresh every 6 hours"
echo
echo "💡 Example questions to try:"
echo "  • 'How is our trading system deployed in Kubernetes?'"
echo "  • 'What services make up our architecture?'"
echo "  • 'How do we handle database connections?'"
echo "  • 'What monitoring tools do we use?'"
echo
print_status "Setup completed. Happy architecture exploration! 🚀"




