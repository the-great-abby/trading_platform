#!/bin/bash
"""
Deploy Enhanced Portfolio Management Services
Advanced portfolio management with MPT, Black-Litterman, Risk Parity, Tax Optimization, and Backtesting
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="trading-system"
SERVICES=(
    "enhanced-portfolio-service"
    "enhanced-risk-management-service"
)

echo -e "${BLUE}🚀 Deploying Enhanced Portfolio Management Services${NC}"
echo "=================================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
    exit 1
fi

# Check if Docker registry is accessible
if ! curl -s http://localhost:32000/v2/ &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker registry at localhost:32000 is not accessible${NC}"
    echo "Make sure Docker registry is running or update image references"
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Deploy services
echo -e "${YELLOW}🚀 Deploying Enhanced Portfolio Services...${NC}"

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}📦 Deploying $service...${NC}"
    
    # Apply the deployment
    if kubectl apply -f k8s/$service.yaml; then
        echo -e "${GREEN}✅ $service deployment applied successfully${NC}"
    else
        echo -e "${RED}❌ Failed to apply $service deployment${NC}"
        exit 1
    fi
done

# Wait for deployments to be ready
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}🔄 Waiting for $service...${NC}"
    
    if kubectl wait --for=condition=available --timeout=300s deployment/$service -n $NAMESPACE; then
        echo -e "${GREEN}✅ $service is ready${NC}"
    else
        echo -e "${RED}❌ $service failed to become ready${NC}"
        echo -e "${YELLOW}📋 Checking $service status...${NC}"
        kubectl describe deployment $service -n $NAMESPACE
        kubectl get pods -l app=$service -n $NAMESPACE
        exit 1
    fi
done

# Check service status
echo -e "${YELLOW}📊 Checking service status...${NC}"

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}📋 $service status:${NC}"
    kubectl get deployment $service -n $NAMESPACE
    kubectl get service $service -n $NAMESPACE
    echo ""
done

# Check pods
echo -e "${YELLOW}🔍 Checking pod status...${NC}"
kubectl get pods -l "app in (enhanced-portfolio-service,enhanced-risk-management-service)" -n $NAMESPACE

# Test service endpoints
echo -e "${YELLOW}🧪 Testing service endpoints...${NC}"

# Test Enhanced Portfolio Service
echo -e "${BLUE}🔍 Testing Enhanced Portfolio Service...${NC}"
if kubectl port-forward -n $NAMESPACE service/enhanced-portfolio-service 11180:80 &
then
    PORT_FORWARD_PID=$!
    sleep 5
    
    if curl -s http://localhost:11180/health > /dev/null; then
        echo -e "${GREEN}✅ Enhanced Portfolio Service health check passed${NC}"
    else
        echo -e "${RED}❌ Enhanced Portfolio Service health check failed${NC}"
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  Could not test Enhanced Portfolio Service (port forwarding failed)${NC}"
fi

# Test Enhanced Risk Management Service
echo -e "${BLUE}🔍 Testing Enhanced Risk Management Service...${NC}"
if kubectl port-forward -n $NAMESPACE service/enhanced-risk-management-service 11181:80 &
then
    PORT_FORWARD_PID=$!
    sleep 5
    
    if curl -s http://localhost:11181/health > /dev/null; then
        echo -e "${GREEN}✅ Enhanced Risk Management Service health check passed${NC}"
    else
        echo -e "${RED}❌ Enhanced Risk Management Service health check failed${NC}"
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  Could not test Enhanced Risk Management Service (port forwarding failed)${NC}"
fi

# Display deployment summary
echo -e "${GREEN}🎉 Enhanced Portfolio Management Services Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo "• Enhanced Portfolio Service: http://localhost:11180"
echo "• Enhanced Risk Management Service: http://localhost:11181"
echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo "1. Start port forwarding:"
echo "   kubectl port-forward -n $NAMESPACE service/enhanced-portfolio-service 11180:80 &"
echo "   kubectl port-forward -n $NAMESPACE service/enhanced-risk-management-service 11181:80 &"
echo ""
echo "2. Test the services:"
echo "   curl -s http://localhost:11180/api/v1/status"
echo "   curl -s http://localhost:11181/api/v1/status"
echo ""
echo "3. View service logs:"
echo "   kubectl logs -l app=enhanced-portfolio-service -n $NAMESPACE"
echo "   kubectl logs -l app=enhanced-risk-management-service -n $NAMESPACE"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "• PORT_MAP.md updated with new service ports"
echo "• Service configurations in k8s/enhanced-*-service.yaml"
echo "• API documentation available at /api/v1/docs endpoints"
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
























