#!/bin/bash

# Docker Registry Setup Script
# This script helps manage the local Docker registry at host.docker.internal:5000

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_HOST="host.docker.internal:5000"
PROJECT_NAME="trading-bot"
IMAGE_TAG="latest"

echo -e "${GREEN}🐳 Docker Registry Setup for Trading Bot${NC}"
echo -e "${YELLOW}Registry: ${REGISTRY_HOST}${NC}"
echo ""

# Function to check if registry is accessible
check_registry() {
    echo -e "${YELLOW}Checking registry accessibility...${NC}"
    if curl -s http://${REGISTRY_HOST}/v2/ > /dev/null; then
        echo -e "${GREEN}✓ Registry is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ Registry is not accessible${NC}"
        echo -e "${YELLOW}Make sure your local registry is running at ${REGISTRY_HOST}${NC}"
        return 1
    fi
}

# Function to build and tag images
build_and_tag() {
    local service_name=$1
    local dockerfile=$2
    local context=$3
    
    echo -e "${YELLOW}Building ${service_name}...${NC}"
    
    # Build the image
    docker build -f ${dockerfile} -t ${PROJECT_NAME}-${service_name}:${IMAGE_TAG} ${context}
    
    # Tag for local registry
    docker tag ${PROJECT_NAME}-${service_name}:${IMAGE_TAG} ${REGISTRY_HOST}/${PROJECT_NAME}-${service_name}:${IMAGE_TAG}
    
    echo -e "${GREEN}✓ Built and tagged ${service_name}${NC}"
}

# Function to push images to registry
push_to_registry() {
    local service_name=$1
    
    echo -e "${YELLOW}Pushing ${service_name} to registry...${NC}"
    docker push ${REGISTRY_HOST}/${PROJECT_NAME}-${service_name}:${IMAGE_TAG}
    echo -e "${GREEN}✓ Pushed ${service_name} to registry${NC}"
}

# Function to update Kubernetes manifests
update_k8s_manifests() {
    echo -e "${YELLOW}Updating Kubernetes manifests with registry URLs...${NC}"
    
    # Find all Kubernetes YAML files and update image references
    find k8s/ -name "*.yaml" -type f | while read -r file; do
        echo "Processing: $file"
        # Update image references to use local registry
        sed -i.bak "s|image: ${PROJECT_NAME}:${IMAGE_TAG}|image: ${REGISTRY_HOST}/${PROJECT_NAME}:${IMAGE_TAG}|g" "$file"
        sed -i.bak "s|image: ${PROJECT_NAME}-|image: ${REGISTRY_HOST}/${PROJECT_NAME}-|g" "$file"
    done
    
    echo -e "${GREEN}✓ Updated Kubernetes manifests${NC}"
}

# Function to create registry configuration
create_registry_config() {
    echo -e "${YELLOW}Creating registry configuration...${NC}"
    
    cat > docker-registry-config.env << EOF
# Docker Registry Configuration
DOCKER_REGISTRY_HOST=${REGISTRY_HOST}
DOCKER_REGISTRY_PROJECT=${PROJECT_NAME}
DOCKER_REGISTRY_TAG=${IMAGE_TAG}

# Image URLs
TRADING_BOT_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}:${IMAGE_TAG}
TRADING_SERVICE_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-trading-service:${IMAGE_TAG}
MARKET_DATA_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-market-data:${IMAGE_TAG}
PORTFOLIO_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-portfolio:${IMAGE_TAG}
RISK_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-risk:${IMAGE_TAG}
STRATEGY_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-strategy:${IMAGE_TAG}
ORDER_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-order:${IMAGE_TAG}
ANALYTICS_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-analytics:${IMAGE_TAG}
USER_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-user:${IMAGE_TAG}
GATEWAY_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-gateway:${IMAGE_TAG}
COMMAND_API_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-command-api:${IMAGE_TAG}
QUERY_API_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-query-api:${IMAGE_TAG}
PUBLIC_API_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-public-api:${IMAGE_TAG}
HEALTH_DASHBOARD_IMAGE=${REGISTRY_HOST}/${PROJECT_NAME}-health-dashboard:${IMAGE_TAG}
EOF

    echo -e "${GREEN}✓ Created registry configuration${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  check       - Check registry accessibility"
    echo "  build       - Build all images and tag for registry"
    echo "  push        - Push all images to registry"
    echo "  build-push  - Build and push all images"
    echo "  update-k8s  - Update Kubernetes manifests with registry URLs"
    echo "  config      - Create registry configuration file"
    echo "  all         - Run all setup steps"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 build-push"
    echo "  $0 all"
}

# Main script logic
case "${1:-help}" in
    "check")
        check_registry
        ;;
    "build")
        check_registry
        build_and_tag "main" "Dockerfile.dev" "."
        build_and_tag "trading-service" "services/trading-service/Dockerfile" "services/trading-service"
        build_and_tag "market-data-service" "services/market-data-service/Dockerfile" "services/market-data-service"
        build_and_tag "portfolio-service" "services/portfolio-service/Dockerfile" "services/portfolio-service"
        build_and_tag "risk-service" "services/risk-service/Dockerfile" "services/risk-service"
        build_and_tag "strategy-service" "services/strategy-service/Dockerfile" "services/strategy-service"
        build_and_tag "order-service" "services/order-service/Dockerfile" "services/order-service"
        build_and_tag "analytics-service" "services/analytics-service/Dockerfile" "services/analytics-service"
        build_and_tag "user-service" "services/user-service/Dockerfile" "services/user-service"
        build_and_tag "gateway" "services/gateway/Dockerfile" "services/gateway"
        build_and_tag "command-api" "services/command-api/Dockerfile" "services/command-api"
        build_and_tag "query-api" "services/query-api/Dockerfile" "services/query-api"
        build_and_tag "public-api" "services/public-api/Dockerfile" "services/public-api"
        build_and_tag "health-dashboard" "services/health-dashboard/Dockerfile" "services/health-dashboard"
        ;;
    "push")
        check_registry
        push_to_registry "main"
        push_to_registry "trading-service"
        push_to_registry "market-data-service"
        push_to_registry "portfolio-service"
        push_to_registry "risk-service"
        push_to_registry "strategy-service"
        push_to_registry "order-service"
        push_to_registry "analytics-service"
        push_to_registry "user-service"
        push_to_registry "gateway"
        push_to_registry "command-api"
        push_to_registry "query-api"
        push_to_registry "public-api"
        push_to_registry "health-dashboard"
        ;;
    "build-push")
        $0 build
        $0 push
        ;;
    "update-k8s")
        update_k8s_manifests
        ;;
    "config")
        create_registry_config
        ;;
    "all")
        check_registry
        $0 build-push
        $0 config
        $0 update-k8s
        echo -e "${GREEN}🎉 All setup steps completed!${NC}"
        ;;
    "help"|*)
        show_usage
        ;;
esac 