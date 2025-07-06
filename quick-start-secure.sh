#!/bin/bash

# Quick Start Script for Secure Containerized Architecture
# This script sets up and demonstrates the secure trading system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Secure Trading System Quick Start    ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to check if Ollama is running (optional)
check_ollama() {
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running on host${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Ollama not detected on host (optional for AI features)${NC}"
        return 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    
    # Wait for API gateway
    echo "Waiting for API Gateway..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API Gateway is ready${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ API Gateway failed to start${NC}"
            exit 1
        fi
        sleep 2
    done
    
    # Wait for CLI container
    echo "Waiting for CLI container..."
    for i in {1..30}; do
        if docker exec trading-cli echo "ready" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ CLI container is ready${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ CLI container failed to start${NC}"
            exit 1
        fi
        sleep 2
    done
}

# Function to demonstrate CLI operations
demonstrate_cli() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  CLI Operations Demonstration        ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    echo -e "${YELLOW}1. Checking service health...${NC}"
    make cli-health
    
    echo -e "${YELLOW}2. Getting portfolio summary...${NC}"
    make cli-portfolio
    
    echo -e "${YELLOW}3. Getting available strategies...${NC}"
    make cli-strategies
    
    echo -e "${YELLOW}4. Getting market data for AAPL...${NC}"
    make cli-market-data SYMBOL=AAPL
    
    echo -e "${YELLOW}5. Getting risk assessment...${NC}"
    make cli-risk
    
    echo -e "${YELLOW}6. Getting performance analytics...${NC}"
    make cli-analytics REPORT=performance
    
    echo -e "${YELLOW}7. Generating trading signal...${NC}"
    make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL
}

# Function to demonstrate API operations
demonstrate_api() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  API Operations Demonstration        ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    echo -e "${YELLOW}1. API Gateway health check...${NC}"
    curl -s http://localhost:8000/health | jq .
    
    echo -e "${YELLOW}2. Getting portfolio via API...${NC}"
    curl -s http://localhost:8000/portfolio | jq .
    
    echo -e "${YELLOW}3. Getting strategies via API...${NC}"
    curl -s http://localhost:8000/strategies | jq .
    
    echo -e "${YELLOW}4. Getting engine status via API...${NC}"
    curl -s http://localhost:8000/engine/status | jq .
}

# Function to show system status
show_status() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  System Status                        ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    echo -e "${YELLOW}Docker containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo -e "${YELLOW}Network connectivity:${NC}"
    echo "External API: http://localhost:8000"
    echo "Internal services: Only accessible via CLI or API Gateway"
    
    echo ""
    echo -e "${YELLOW}Available commands:${NC}"
    echo "  make cli-health          - Check all services"
    echo "  make cli-portfolio       - Get portfolio summary"
    echo "  make cli-strategies      - Get available strategies"
    echo "  make cli-market-data SYMBOL=AAPL - Get market data"
    echo "  make cli-shell           - Open CLI shell"
    echo "  make docker-logs         - View all logs"
    echo "  make docker-down         - Stop all services"
}

# Main execution
main() {
    echo -e "${GREEN}Starting Secure Trading System...${NC}"
    
    # Check prerequisites
    check_docker
    check_ollama
    
    echo ""
    echo -e "${BLUE}Step 1: Building and starting services...${NC}"
    
    # Stop any existing containers
    echo "Stopping any existing containers..."
    make docker-down 2>/dev/null || true
    
    # Build and start services
    echo "Building and starting services..."
    make docker-up-build
    
    # Wait for services to be ready
    wait_for_services
    
    echo ""
    echo -e "${GREEN}✓ All services are running!${NC}"
    
    # Show system status
    show_status
    
    # Demonstrate operations
    demonstrate_cli
    demonstrate_api
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Setup Complete!                      ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Explore the CLI: make cli-shell"
    echo "2. Test the API: curl http://localhost:8000/health"
    echo "3. Run backtests: make docker-backtest"
    echo "4. View logs: make docker-logs"
    echo "5. Stop services: make docker-down"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "- SECURE_ARCHITECTURE_GUIDE.md"
    echo "- README.md"
    echo "- Makefile (run 'make help' for all commands)"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        echo -e "${YELLOW}Stopping all services...${NC}"
        make docker-down
        echo -e "${GREEN}Services stopped.${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}Restarting services...${NC}"
        make docker-restart
        echo -e "${GREEN}Services restarted.${NC}"
        ;;
    "logs")
        echo -e "${YELLOW}Showing logs...${NC}"
        make docker-logs
        ;;
    "status")
        show_status
        ;;
    "demo")
        wait_for_services
        demonstrate_cli
        demonstrate_api
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Start the complete system"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart all services"
        echo "  logs       - Show service logs"
        echo "  status     - Show system status"
        echo "  demo       - Run demonstrations"
        echo "  help       - Show this help"
        ;;
    *)
        main
        ;;
esac 