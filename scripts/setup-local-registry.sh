#!/bin/bash

# Local Docker Registry Setup Script
# This script helps set up a local Docker registry if it's not already running

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

REGISTRY_HOST="host.docker.internal:5000"
REGISTRY_NAME="local-registry"
REGISTRY_PORT="5000"

echo -e "${GREEN}🐳 Local Docker Registry Setup${NC}"
echo ""

# Function to check if registry is already running
check_existing_registry() {
    echo -e "${YELLOW}Checking for existing registry...${NC}"
    
    # Check if registry container exists and is running
    if docker ps --format "table {{.Names}}" | grep -q "^${REGISTRY_NAME}$"; then
        echo -e "${GREEN}✓ Registry container is already running${NC}"
        return 0
    elif docker ps -a --format "table {{.Names}}" | grep -q "^${REGISTRY_NAME}$"; then
        echo -e "${YELLOW}Registry container exists but is not running${NC}"
        return 1
    else
        echo -e "${YELLOW}No registry container found${NC}"
        return 2
    fi
}

# Function to start existing registry
start_existing_registry() {
    echo -e "${YELLOW}Starting existing registry container...${NC}"
    docker start ${REGISTRY_NAME}
    echo -e "${GREEN}✓ Registry started${NC}"
}

# Function to create and start new registry
create_new_registry() {
    echo -e "${YELLOW}Creating new registry container...${NC}"
    
    # Stop and remove any existing container
    docker stop ${REGISTRY_NAME} 2>/dev/null || true
    docker rm ${REGISTRY_NAME} 2>/dev/null || true
    
    # Create new registry container
    docker run -d \
        --name ${REGISTRY_NAME} \
        -p ${REGISTRY_PORT}:5000 \
        -v registry-data:/var/lib/registry \
        --restart unless-stopped \
        registry:2
    
    echo -e "${GREEN}✓ New registry container created and started${NC}"
}

# Function to configure Docker daemon for insecure registry
configure_docker_daemon() {
    echo -e "${YELLOW}Configuring Docker daemon for insecure registry...${NC}"
    
    # Check if insecure registry is already configured
    if docker info 2>/dev/null | grep -q "host.docker.internal:5000"; then
        echo -e "${GREEN}✓ Insecure registry already configured${NC}"
        return 0
    fi
    
    # Detect OS and provide instructions
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}For macOS (Docker Desktop):${NC}"
        echo "1. Open Docker Desktop"
        echo "2. Go to Settings/Preferences"
        echo "3. Navigate to Docker Engine"
        echo "4. Add to the JSON configuration:"
        echo "   {"
        echo "     \"insecure-registries\": [\"host.docker.internal:5000\"]"
        echo "   }"
        echo "5. Click 'Apply & Restart'"
        echo ""
        echo -e "${YELLOW}After configuring, run this script again${NC}"
        return 1
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "${YELLOW}For Linux:${NC}"
        echo "1. Edit /etc/docker/daemon.json (create if it doesn't exist)"
        echo "2. Add the following configuration:"
        echo "   {"
        echo "     \"insecure-registries\": [\"host.docker.internal:5000\"]"
        echo "   }"
        echo "3. Restart Docker daemon: sudo systemctl restart docker"
        echo ""
        echo -e "${YELLOW}After configuring, run this script again${NC}"
        return 1
    else
        echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
        return 1
    fi
}

# Function to test registry accessibility
test_registry() {
    echo -e "${YELLOW}Testing registry accessibility...${NC}"
    
    # Wait a moment for registry to be ready
    sleep 3
    
    # Test registry API
    if curl -s http://${REGISTRY_HOST}/v2/ > /dev/null; then
        echo -e "${GREEN}✓ Registry is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ Registry is not accessible${NC}"
        return 1
    fi
}

# Function to show registry info
show_registry_info() {
    echo -e "${GREEN}📊 Registry Information:${NC}"
    echo "Host: ${REGISTRY_HOST}"
    echo "Container: ${REGISTRY_NAME}"
    echo "Port: ${REGISTRY_PORT}"
    echo ""
    echo -e "${GREEN}🔗 Registry API:${NC}"
    echo "Catalog: http://${REGISTRY_HOST}/v2/_catalog"
    echo "Health: http://${REGISTRY_HOST}/v2/"
    echo ""
    echo -e "${GREEN}🐳 Docker Commands:${NC}"
    echo "List images: curl http://${REGISTRY_HOST}/v2/_catalog"
    echo "List tags: curl http://${REGISTRY_HOST}/v2/trading-bot/tags/list"
    echo ""
    echo -e "${GREEN}📝 Next Steps:${NC}"
    echo "1. Run: make -f Makefile.registry registry-setup"
    echo "2. Or: ./scripts/docker-registry-setup.sh all"
}

# Main script logic
main() {
    echo -e "${YELLOW}Setting up local Docker registry...${NC}"
    
    # Check for existing registry
    check_existing_registry
    registry_status=$?
    
    case $registry_status in
        0)
            echo -e "${GREEN}Registry is already running${NC}"
            ;;
        1)
            echo -e "${YELLOW}Starting existing registry...${NC}"
            start_existing_registry
            ;;
        2)
            echo -e "${YELLOW}Creating new registry...${NC}"
            create_new_registry
            ;;
    esac
    
    # Test registry accessibility
    if test_registry; then
        show_registry_info
    else
        echo -e "${RED}Registry setup failed${NC}"
        echo -e "${YELLOW}Checking Docker daemon configuration...${NC}"
        configure_docker_daemon
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup      - Set up local registry (default)"
    echo "  check      - Check registry status"
    echo "  start      - Start existing registry"
    echo "  stop       - Stop registry"
    echo "  restart    - Restart registry"
    echo "  remove     - Remove registry container"
    echo "  info       - Show registry information"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 check"
    echo "  $0 restart"
}

# Parse command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "check")
        check_existing_registry
        test_registry
        ;;
    "start")
        start_existing_registry
        test_registry
        ;;
    "stop")
        echo -e "${YELLOW}Stopping registry...${NC}"
        docker stop ${REGISTRY_NAME}
        echo -e "${GREEN}✓ Registry stopped${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}Restarting registry...${NC}"
        docker restart ${REGISTRY_NAME}
        test_registry
        ;;
    "remove")
        echo -e "${YELLOW}Removing registry container...${NC}"
        docker stop ${REGISTRY_NAME} 2>/dev/null || true
        docker rm ${REGISTRY_NAME} 2>/dev/null || true
        echo -e "${GREEN}✓ Registry container removed${NC}"
        ;;
    "info")
        show_registry_info
        ;;
    "help"|*)
        show_usage
        ;;
esac 