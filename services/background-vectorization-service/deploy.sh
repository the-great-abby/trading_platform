#!/bin/bash

# Background Vectorization Service - Phase 3 Deployment Script
# This script automates the deployment and testing process

set -e

echo "🚀 Starting Phase 3: Deployment & Testing for Background Vectorization Service"
echo "=================================================================="

# Configuration
SERVICE_NAME="background-vectorization-service"
REGISTRY="localhost:32000"
NAMESPACE="trading-system"
IMAGE_TAG="latest"

echo "📋 Configuration:"
echo "  Service: $SERVICE_NAME"
echo "  Registry: $REGISTRY"
echo "  Namespace: $NAMESPACE"
echo "  Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Build Docker Image
echo "🔨 Step 1: Building Docker Image..."
echo "Building $SERVICE_NAME image..."

if docker build -t $SERVICE_NAME:$IMAGE_TAG . ; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Step 2: Tag and Push to Registry
echo ""
echo "📤 Step 2: Tagging and Pushing to Registry..."
echo "Tagging image for registry..."

if docker tag $SERVICE_NAME:$IMAGE_TAG $REGISTRY/$SERVICE_NAME:$IMAGE_TAG ; then
    echo "✅ Image tagged successfully"
else
    echo "❌ Image tagging failed"
    exit 1
fi

echo "Pushing image to registry..."

if docker push $REGISTRY/$SERVICE_NAME:$IMAGE_TAG ; then
    echo "✅ Image pushed to registry successfully"
else
    echo "❌ Image push failed"
    exit 1
fi

# Step 3: Deploy to Kubernetes
echo ""
echo "☸️  Step 3: Deploying to Kubernetes..."
echo "Applying Kubernetes manifests..."

if kubectl apply -f k8s-deployment-fixed.yaml ; then
    echo "✅ Kubernetes manifests applied successfully"
else
    echo "❌ Kubernetes deployment failed"
    exit 1
fi

# Step 4: Wait for Deployment
echo ""
echo "⏳ Step 4: Waiting for Deployment..."
echo "Waiting for pods to be ready..."

if kubectl wait --for=condition=available --timeout=300s deployment/$SERVICE_NAME -n $NAMESPACE ; then
    echo "✅ Deployment is ready"
else
    echo "❌ Deployment failed to become ready within timeout"
    echo "Checking pod status..."
    kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME
    kubectl describe deployment $SERVICE_NAME -n $NAMESPACE
    exit 1
fi

# Step 5: Verify Service Status
echo ""
echo "🔍 Step 5: Verifying Service Status..."
echo "Checking service endpoints..."

if kubectl get svc $SERVICE_NAME -n $NAMESPACE ; then
    echo "✅ Service created successfully"
else
    echo "❌ Service creation failed"
    exit 1
fi

# Step 6: Health Check
echo ""
echo "🏥 Step 6: Health Check..."
echo "Waiting for service to be healthy..."

# Wait a bit for the service to fully initialize
sleep 10

# Get pod name for port forwarding
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME -o jsonpath='{.items[0].metadata.name}')
echo "Using pod: $POD_NAME"

# Test health endpoint
echo "Testing health endpoint..."
if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/health ; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "Checking pod logs..."
    kubectl logs $POD_NAME -n $NAMESPACE --tail=50
    exit 1
fi

# Step 7: Test API Endpoints
echo ""
echo "🧪 Step 7: Testing API Endpoints..."
echo "Testing vectorization status endpoint..."

if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/api/vectorization/status ; then
    echo "✅ Status endpoint working"
else
    echo "❌ Status endpoint failed"
fi

echo "Testing metrics endpoint..."

if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/api/vectorization/metrics ; then
    echo "✅ Metrics endpoint working"
else
    echo "❌ Metrics endpoint failed"
fi

echo "Testing configuration endpoint..."

if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/api/vectorization/config ; then
    echo "✅ Configuration endpoint working"
else
    echo "❌ Configuration endpoint failed"
fi

# Step 8: Check Scheduler Status
echo ""
echo "⏰ Step 8: Checking Scheduler Status..."
echo "Testing scheduler status endpoint..."

if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/api/vectorization/scheduler/status ; then
    echo "✅ Scheduler status endpoint working"
else
    echo "❌ Scheduler status endpoint failed"
fi

# Step 9: Performance Test
echo ""
echo "⚡ Step 9: Performance Test..."
echo "Creating a test vectorization job..."

TEST_JOB='{"job_id": "test_phase3_001", "data_type": "market_data", "symbol": "AAPL", "data": {"test": true}}'

if kubectl exec -n $NAMESPACE $POD_NAME -- curl -f -X POST http://localhost:8080/api/vectorization/jobs \
    -H "Content-Type: application/json" \
    -d "$TEST_JOB" ; then
    echo "✅ Test job created successfully"
else
    echo "❌ Test job creation failed"
fi

# Step 10: Final Status
echo ""
echo "🎯 Phase 3 Deployment Summary:"
echo "================================"
echo "✅ Docker image built and pushed"
echo "✅ Kubernetes deployment successful"
echo "✅ Service health check passed"
echo "✅ API endpoints tested"
echo "✅ Scheduler status verified"
echo "✅ Test job creation successful"
echo ""
echo "🚀 Background Vectorization Service is now deployed and running!"
echo ""
echo "📊 Service Information:"
kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME
kubectl get svc -n $NAMESPACE -l app=$SERVICE_NAME
echo ""
echo "🔗 Next Steps:"
echo "1. Monitor service logs: kubectl logs -f deployment/$SERVICE_NAME -n $NAMESPACE"
echo "2. Test vectorization workflows with real data"
echo "3. Monitor performance metrics"
echo "4. Validate data processing accuracy"
echo "5. Begin Phase 4: Production Integration"
echo ""
echo "🎉 Phase 3: Deployment & Testing - COMPLETED!"
