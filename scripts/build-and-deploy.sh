#!/bin/bash

# 🏴‍☠️ Trading System Build and Deploy Script
# Ahoy matey! This script builds and deploys the trading system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏴‍☠️ Ahoy matey! Starting Trading System Build and Deploy${NC}"
echo -e "${YELLOW}====================================================${NC}"

# Check if registry is accessible
echo -e "${BLUE}🔍 Checking registry status...${NC}"
if ! curl -s http://localhost:32000/v2/_catalog > /dev/null; then
    echo -e "${YELLOW}⚠️ Registry not accessible, starting port forward...${NC}"
    kubectl port-forward -n default service/registry 32000:5000 > /dev/null 2>&1 &
    sleep 3
fi

# Check registry again
if curl -s http://localhost:32000/v2/_catalog > /dev/null; then
    echo -e "${GREEN}✅ Registry is accessible${NC}"
else
    echo -e "${RED}❌ Registry is not accessible. Please check registry status.${NC}"
    exit 1
fi

# Core services to build and deploy
CORE_SERVICES=(
    "kubernetes-rag-chat-rs"
    "unified-analytics-dashboard"
    "market-data-service"
    "ai-analysis-service"
    "background-vectorization-service"
)

echo -e "${BLUE}📦 Building core services...${NC}"
for service in "${CORE_SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        echo -e "${BLUE}🔨 Building $service...${NC}"
        cd "services/$service"
        
        # Build Docker image
        docker build -t "$service:latest" .
        docker tag "$service:latest" "localhost:32000/$service:latest"
        docker push "localhost:32000/$service:latest"
        
        echo -e "${GREEN}✅ $service built and pushed${NC}"
        cd ../..
    else
        echo -e "${YELLOW}⚠️ Service $service not found in services/ directory${NC}"
    fi
done

echo -e "${BLUE}🚀 Deploying to Kubernetes...${NC}"
# Deploy core services
kubectl apply -f k8s/kubernetes-rag-chat-rs.yaml
kubectl apply -f k8s/unified-analytics-dashboard.yaml
kubectl apply -f k8s/market-data-service.yaml
kubectl apply -f k8s/ai-analysis-service.yaml
kubectl apply -f k8s/background-vectorization-service.yaml

echo -e "${BLUE}⏳ Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/kubernetes-rag-chat-rs -n trading-system || true
kubectl wait --for=condition=available --timeout=300s deployment/unified-analytics-dashboard -n trading-system || true
kubectl wait --for=condition=available --timeout=300s deployment/market-data-service -n trading-system || true
kubectl wait --for=condition=available --timeout=300s deployment/ai-analysis-service -n trading-system || true

echo -e "${BLUE}🔌 Setting up port forwarding...${NC}"
# Start port forwarding for core services
kubectl port-forward -n trading-system service/unified-analytics-dashboard 11114:80 > /dev/null 2>&1 &
kubectl port-forward -n trading-system service/market-data-service 11084:11084 > /dev/null 2>&1 &
kubectl port-forward -n trading-system service/ai-analysis-service 11085:11085 > /dev/null 2>&1 &

echo -e "${GREEN}🎯 Build and Deploy Complete!${NC}"
echo -e "${YELLOW}===========================${NC}"
echo -e "${BLUE}📊 Service URLs:${NC}"
echo -e "  • Analytics Dashboard: http://localhost:11114/"
echo -e "  • Market Data Service: http://localhost:11084/"
echo -e "  • AI Analysis Service: http://localhost:11085/"
echo ""
echo -e "${BLUE}🔍 Check status with:${NC}"
echo -e "  make simple-status"
echo -e "  make port-status"
echo ""
echo -e "${GREEN}🏴‍☠️ Yo ho ho! The trading system is ready to sail!${NC}"

