#!/bin/bash

# Port Forwarding for External Databases
# This script manages port forwarding to make external databases accessible locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Port assignments
TIMESCALE_PORT=11150
VECTOR_PORT=11151
AGE_PORT=11152
REGULAR_PORT=11153

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start       - Start all external database port forwards"
    echo "  stop        - Stop all external database port forwards"
    echo "  status      - Show status of port forwards"
    echo "  restart     - Restart all port forwards"
    echo "  test        - Test database connections"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 test"
}

# Function to start port forwarding
start_port_forwards() {
    echo -e "${BLUE}🚀 Starting external database port forwards...${NC}"
    
    # Start TimescaleDB port forward
    if ! lsof -i :$TIMESCALE_PORT > /dev/null 2>&1; then
        kubectl port-forward service/postgres-timescale-external $TIMESCALE_PORT:5432 -n postgres-infra > /dev/null 2>&1 &
        echo -e "${GREEN}✅ TimescaleDB: localhost:$TIMESCALE_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  TimescaleDB port $TIMESCALE_PORT already in use${NC}"
    fi
    
    # Start Vector Storage port forward
    if ! lsof -i :$VECTOR_PORT > /dev/null 2>&1; then
        kubectl port-forward service/postgres-vector-external $VECTOR_PORT:5432 -n postgres-infra > /dev/null 2>&1 &
        echo -e "${GREEN}✅ Vector Storage: localhost:$VECTOR_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  Vector Storage port $VECTOR_PORT already in use${NC}"
    fi
    
    # Start Apache AGE port forward
    if ! lsof -i :$AGE_PORT > /dev/null 2>&1; then
        kubectl port-forward service/postgres-age-external $AGE_PORT:5432 -n postgres-infra > /dev/null 2>&1 &
        echo -e "${GREEN}✅ Apache AGE: localhost:$AGE_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  Apache AGE port $AGE_PORT already in use${NC}"
    fi
    
    # Start Regular PostgreSQL port forward
    if ! lsof -i :$REGULAR_PORT > /dev/null 2>&1; then
        kubectl port-forward service/postgres-regular-external $REGULAR_PORT:5432 -n postgres-infra > /dev/null 2>&1 &
        echo -e "${GREEN}✅ Regular PostgreSQL: localhost:$REGULAR_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  Regular PostgreSQL port $REGULAR_PORT already in use${NC}"
    fi
    
    echo -e "${BLUE}⏳ Waiting for port forwards to establish...${NC}"
    sleep 3
}

# Function to stop port forwarding
stop_port_forwards() {
    echo -e "${BLUE}🛑 Stopping external database port forwards...${NC}"
    
    # Kill processes using our ports
    pkill -f "kubectl port-forward.*postgres-timescale-external" || true
    pkill -f "kubectl port-forward.*postgres-vector-external" || true
    pkill -f "kubectl port-forward.*postgres-age-external" || true
    pkill -f "kubectl port-forward.*postgres-regular-external" || true
    
    echo -e "${GREEN}✅ All external database port forwards stopped${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 External Database Port Forward Status${NC}"
    echo
    
    # Check TimescaleDB
    if lsof -i :$TIMESCALE_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ TimescaleDB: localhost:$TIMESCALE_PORT (ACTIVE)${NC}"
    else
        echo -e "${RED}❌ TimescaleDB: localhost:$TIMESCALE_PORT (INACTIVE)${NC}"
    fi
    
    # Check Vector Storage
    if lsof -i :$VECTOR_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Vector Storage: localhost:$VECTOR_PORT (ACTIVE)${NC}"
    else
        echo -e "${RED}❌ Vector Storage: localhost:$VECTOR_PORT (INACTIVE)${NC}"
    fi
    
    # Check Apache AGE
    if lsof -i :$AGE_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Apache AGE: localhost:$AGE_PORT (ACTIVE)${NC}"
    else
        echo -e "${RED}❌ Apache AGE: localhost:$AGE_PORT (INACTIVE)${NC}"
    fi
    
    # Check Regular PostgreSQL
    if lsof -i :$REGULAR_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Regular PostgreSQL: localhost:$REGULAR_PORT (ACTIVE)${NC}"
    else
        echo -e "${RED}❌ Regular PostgreSQL: localhost:$REGULAR_PORT (INACTIVE)${NC}"
    fi
}

# Function to test database connections
test_connections() {
    echo -e "${BLUE}🧪 Testing external database connections...${NC}"
    echo
    
    # Test TimescaleDB
    echo -e "${BLUE}Testing TimescaleDB (localhost:$TIMESCALE_PORT)...${NC}"
    if PGPASSWORD=postgres psql -h localhost -p $TIMESCALE_PORT -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ TimescaleDB: Connection successful${NC}"
    else
        echo -e "${RED}❌ TimescaleDB: Connection failed${NC}"
    fi
    
    # Test Vector Storage
    echo -e "${BLUE}Testing Vector Storage (localhost:$VECTOR_PORT)...${NC}"
    if PGPASSWORD=postgres psql -h localhost -p $VECTOR_PORT -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Vector Storage: Connection successful${NC}"
    else
        echo -e "${RED}❌ Vector Storage: Connection failed${NC}"
    fi
    
    # Test Apache AGE
    echo -e "${BLUE}Testing Apache AGE (localhost:$AGE_PORT)...${NC}"
    if PGPASSWORD=postgres psql -h localhost -p $AGE_PORT -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Apache AGE: Connection successful${NC}"
    else
        echo -e "${RED}❌ Apache AGE: Connection failed${NC}"
    fi
    
    # Test Regular PostgreSQL
    echo -e "${BLUE}Testing Regular PostgreSQL (localhost:$REGULAR_PORT)...${NC}"
    if PGPASSWORD=postgres psql -h localhost -p $REGULAR_PORT -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Regular PostgreSQL: Connection successful${NC}"
    else
        echo -e "${RED}❌ Regular PostgreSQL: Connection failed${NC}"
    fi
}

# Function to restart port forwards
restart_port_forwards() {
    echo -e "${BLUE}🔄 Restarting external database port forwards...${NC}"
    stop_port_forwards
    sleep 2
    start_port_forwards
}

# Main script logic
case "${1:-}" in
    start)
        start_port_forwards
        ;;
    stop)
        stop_port_forwards
        ;;
    status)
        show_status
        ;;
    restart)
        restart_port_forwards
        ;;
    test)
        test_connections
        ;;
    *)
        usage
        exit 1
        ;;
esac
