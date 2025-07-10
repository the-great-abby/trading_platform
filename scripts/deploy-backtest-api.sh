#!/bin/bash

# Deploy Backtest API to Kubernetes
# This script builds the Docker image and deploys it to Kubernetes

set -e

echo "🚀 ORION Mission Control - Deploying Backtest API"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="localhost:5000"
IMAGE_NAME="backtest-api"
TAG="latest"
NAMESPACE="trading-system"

echo -e "${GREEN}1. Building Docker image...${NC}"
docker build -t ${REGISTRY}/${IMAGE_NAME}:${TAG} services/backtest-api/

echo -e "${GREEN}2. Pushing to local registry...${NC}"
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo -e "${GREEN}3. Deploying to Kubernetes...${NC}"
kubectl apply -f k8s/backtest-api.yaml
kubectl apply -f k8s/ingress.yaml

echo -e "${GREEN}4. Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/backtest-api -n ${NAMESPACE}

echo -e "${GREEN}5. Checking service status...${NC}"
kubectl get pods -l app=backtest-api -n ${NAMESPACE}

echo -e "${GREEN}✅ Backtest API deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}To access the API:${NC}"
echo "  • Kubernetes: http://trading-ingress.trading-system.svc.cluster.local/api/v1/backtest"
echo "  • Local port forward: kubectl port-forward svc/backtest-api 10001:10001 -n trading-system"
echo "  • Then access: http://localhost:10001"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  • Check logs: make -f Makefile.kubernetes k8s-logs-backtest"
echo "  • Check status: make -f Makefile.kubernetes k8s-status-backtest"
echo "  • Port forward: make -f Makefile.kubernetes k8s-port-forward-backtest"
echo ""
echo "This is ORION, Mission Control. Backtest API deployment complete!" 