#!/bin/bash

# Trading System Standardized Port Forwarding Script
# Based on SERVICE_URL_MAPPING.md

set -e

NAMESPACE="trading-system"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to start port forwarding
start_port_forward() {
    local service_name=$1
    local external_port=$2
    local internal_port=$3
    local description=$4
    
    echo -e "${BLUE}🚀 Starting port forward for $description${NC}"
    echo -e "   Service: $service_name"
    echo -e "   External: localhost:$external_port"
    echo -e "   Internal: $internal_port"
    
    if check_port $external_port; then
        kubectl port-forward service/$service_name $external_port:$internal_port -n $NAMESPACE &
        local pid=$!
        echo -e "${GREEN}✅ Started port forward (PID: $pid)${NC}"
        echo "$pid" >> /tmp/trading-port-forwards.pid
    else
        echo -e "${RED}❌ Skipping $service_name - port $external_port is busy${NC}"
    fi
    echo ""
}

# Function to stop all port forwards
stop_port_forwards() {
    echo -e "${YELLOW}🛑 Stopping all port forwards...${NC}"
    if [ -f /tmp/trading-port-forwards.pid ]; then
        while read -r pid; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "${BLUE}Stopping PID $pid${NC}"
                kill $pid
            fi
        done < /tmp/trading-port-forwards.pid
        rm -f /tmp/trading-port-forwards.pid
    fi
    echo -e "${GREEN}✅ All port forwards stopped${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Current Port Forward Status:${NC}"
    if [ -f /tmp/trading-port-forwards.pid ]; then
        echo -e "${GREEN}Active port forwards:${NC}"
        while read -r pid; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "  ✅ PID $pid is running"
            else
                echo -e "  ❌ PID $pid is not running"
            fi
        done < /tmp/trading-port-forwards.pid
    else
        echo -e "${YELLOW}No active port forwards found${NC}"
    fi
}

# Function to show available services
show_services() {
    echo -e "${BLUE}📋 Available Services:${NC}"
    echo -e "${GREEN}Core Dashboards:${NC}"
    echo -e "  Performance Dashboard: http://localhost:11000/dashboard"
    echo -e "  Trading Dashboard: http://localhost:11001/"
    echo -e "  Health Dashboard: http://localhost:11002/"
    echo -e "  RSS Dashboard: http://localhost:11003/"
    echo -e "  Central Hub: http://localhost:11005/"
    echo ""
    echo -e "${GREEN}API Services:${NC}"
    echo -e "  Trading Ultra Service: http://localhost:11100/"
    echo -e "  Data Processing Service: http://localhost:11095/"
    echo -e "  Market Data Worker: http://localhost:11108/"
    echo -e "  AI Analysis Service: http://localhost:11085/"
    echo -e "  Backtest API: http://localhost:11101/"
    echo -e "  LLM Service: http://localhost:11109/"
    echo ""
    echo -e "${GREEN}Infrastructure:${NC}"
    echo -e "  PostgreSQL: localhost:11300"
    echo -e "  RabbitMQ AMQP: localhost:11302"
    echo -e "  RabbitMQ Management: localhost:11303"
    echo -e "  Redis: localhost:11304"
}

# Main execution
case "${1:-start}" in
    "start")
        echo -e "${BLUE}🚀 Starting Trading System Port Forwards${NC}"
        echo -e "${YELLOW}Namespace: $NAMESPACE${NC}"
        echo ""
        
        # Clear PID file
        rm -f /tmp/trading-port-forwards.pid
        
        # Core Dashboards (11000-11099)
        start_port_forward "performance-dashboard" "11000" "80" "Performance Dashboard"
        start_port_forward "trading-dashboard-service" "11001" "8000" "Trading Dashboard Service"
        start_port_forward "health-dashboard" "11002" "80" "Health Dashboard"
        start_port_forward "rss-dashboard" "11003" "80" "RSS Dashboard"
        start_port_forward "central-hub-dashboard" "11005" "80" "Central Hub Dashboard"
        
        # API Services (11100-11199)
        start_port_forward "trading-ultra-service" "11100" "80" "Trading Ultra Service"
        start_port_forward "data-processing-service" "11095" "11095" "Data Processing Service"
        start_port_forward "market-data-worker" "11108" "11108" "Market Data Worker"
        start_port_forward "ai-analysis-service" "11085" "11085" "AI Analysis Service"
        start_port_forward "backtest-api" "11101" "11101" "Backtest API"
        start_port_forward "llm-service" "11109" "11109" "LLM Service"
        
        # Infrastructure Services (11300-11399)
        start_port_forward "postgres-dev" "11300" "5432" "PostgreSQL Database"
        start_port_forward "rabbitmq-service" "11302" "5672" "RabbitMQ AMQP"
        start_port_forward "rabbitmq-service" "11303" "15672" "RabbitMQ Management"
        start_port_forward "redis-dev" "11304" "6379" "Redis Cache"
        
        echo -e "${GREEN}✅ Port forwarding started!${NC}"
        echo -e "${BLUE}📋 Use './scripts/port-forward-standardized.sh status' to check status${NC}"
        echo -e "${BLUE}📋 Use './scripts/port-forward-standardized.sh stop' to stop all forwards${NC}"
        ;;
        
    "stop")
        stop_port_forwards
        ;;
        
    "status")
        show_status
        ;;
        
    "services")
        show_services
        ;;
        
    "restart")
        echo -e "${YELLOW}🔄 Restarting port forwards...${NC}"
        stop_port_forwards
        sleep 2
        $0 start
        ;;
        
    *)
        echo -e "${BLUE}Trading System Port Forwarding Script${NC}"
        echo ""
        echo -e "Usage: $0 [command]"
        echo ""
        echo -e "Commands:"
        echo -e "  start    - Start all port forwards (default)"
        echo -e "  stop     - Stop all port forwards"
        echo -e "  status   - Show current status"
        echo -e "  services - Show available service URLs"
        echo -e "  restart  - Restart all port forwards"
        echo ""
        echo -e "Examples:"
        echo -e "  $0 start"
        echo -e "  $0 stop"
        echo -e "  $0 status"
        ;;
esac 