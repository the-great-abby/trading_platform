#!/bin/bash

# Build Risk Management Service
# Builds and optionally pushes the risk management service Docker image

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVICE_NAME="risk-management-service"
IMAGE_NAME="risk-management-service"
IMAGE_TAG="latest"
REGISTRY_URL="localhost:32000"

echo -e "${GREEN}🛡️  Building Risk Management Service${NC}"
echo -e "${YELLOW}====================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if registry is accessible
echo "Checking registry connectivity..."
if curl -s http://${REGISTRY_URL}/v2/_catalog > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Registry is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Registry not accessible, building locally only${NC}"
fi

echo ""
echo "Building Docker image..."

# Build the image
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f services/${SERVICE_NAME}/Dockerfile .

echo ""
echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Tag for registry if registry is accessible
if curl -s http://${REGISTRY_URL}/v2/_catalog > /dev/null 2>&1; then
    echo ""
    echo "Tagging for registry..."
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}
    echo "Registry image: ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Push to registry
    echo ""
    echo "Pushing to registry..."
    docker push ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}
    echo -e "${GREEN}✅ Image pushed to registry${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Skipping registry push (registry not accessible)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Risk Management Service build completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Deploy the service: make services-deploy-risk-management"
echo "2. Start port forwards: make port-start-risk-management"
echo "3. Check status: make services-risk-management-status"