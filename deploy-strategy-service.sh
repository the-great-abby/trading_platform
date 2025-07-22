#!/bin/bash

# Strategy Service Deployment Script
# This script builds and deploys the strategy service to Kubernetes

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Strategy Service Deployment Script${NC}"
echo -e "${BLUE}====================================${NC}"

# Configuration
REGISTRY="localhost:32000"
SERVICE_NAME="strategy-service"
NAMESPACE="trading-system"
IMAGE_TAG="latest"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    exit 1
fi

# Check if Kubernetes cluster is accessible
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ Kubernetes cluster is not accessible${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
cd services/strategy-service

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in services/strategy-service${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found in services/strategy-service${NC}"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found in services/strategy-service${NC}"
    exit 1
fi

docker build -t ${REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Push to registry
echo -e "${YELLOW}📤 Pushing image to registry...${NC}"
docker push ${REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to push image to registry${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image pushed to registry successfully${NC}"

# Deploy to Kubernetes
echo -e "${YELLOW}🚀 Deploying to Kubernetes...${NC}"
cd ../..

# Check if namespace exists
if ! kubectl get namespace ${NAMESPACE} >/dev/null 2>&1; then
    echo -e "${YELLOW}📦 Creating namespace ${NAMESPACE}...${NC}"
    kubectl create namespace ${NAMESPACE}
fi

# Apply Kubernetes manifests
echo -e "${YELLOW}📋 Applying Kubernetes manifests...${NC}"
kubectl apply -f k8s/strategy-service.yaml

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to apply Kubernetes manifests${NC}"
    exit 1
fi

# Wait for deployment to be ready
echo -e "${YELLOW}⏳ Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/strategy-service -n ${NAMESPACE}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed to become ready${NC}"
    echo -e "${YELLOW}📋 Checking pod status...${NC}"
    kubectl get pods -n ${NAMESPACE} -l app=strategy-service
    echo -e "${YELLOW}📋 Checking pod logs...${NC}"
    kubectl logs -n ${NAMESPACE} deployment/strategy-service --tail=20
    exit 1
fi

echo -e "${GREEN}✅ Strategy service deployed successfully${NC}"

# Show deployment status
echo -e "${YELLOW}📊 Deployment status:${NC}"
kubectl get pods -n ${NAMESPACE} -l app=strategy-service

echo -e "${YELLOW}🌐 Service endpoints:${NC}"
kubectl get svc -n ${NAMESPACE} strategy-service

echo -e "${YELLOW}🔗 Ingress routes:${NC}"
kubectl get ingress -n ${NAMESPACE} | grep strategy

# Show usage instructions
echo -e "${BLUE}📖 Usage Instructions:${NC}"
echo -e "${GREEN}1. Port forward the service:${NC}"
echo -e "   kubectl port-forward svc/strategy-service 11003:80 -n ${NAMESPACE}"
echo -e ""
echo -e "${GREEN}2. Test the API:${NC}"
echo -e "   curl -X POST http://localhost:11003/recommendations/stock \\"
echo -e "     -H \"Content-Type: application/json\" \\"
echo -e "     -d '{\"symbol\": \"AAPL\"}'"
echo -e ""
echo -e "${GREEN}3. Use the CLI tool:${NC}"
echo -e "   python stock_recommendation_cli.py AAPL"
echo -e ""
echo -e "${GREEN}4. Run the demo:${NC}"
echo -e "   python demo_stock_recommendations.py"
echo -e ""
echo -e "${GREEN}5. Check logs:${NC}"
echo -e "   kubectl logs -n ${NAMESPACE} deployment/strategy-service -f"
echo -e ""
echo -e "${GREEN}6. Check service health:${NC}"
echo -e "   curl http://localhost:11003/health"

echo -e "${GREEN}🎉 Strategy service deployment complete!${NC}" 