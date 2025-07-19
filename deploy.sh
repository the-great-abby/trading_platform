#!/bin/bash

# Trading System Microservices Deployment Script
# This script deploys the entire CQRS-based trading system

set -e

echo "🚀 Deploying Trading System Microservices..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install it and try again."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    print_status "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    print_warning "No .env file found. Using default values."
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p monitoring

# Build and start infrastructure services
print_status "Starting infrastructure services..."
docker-compose up -d write-db read-db eventstore kafka zookeeper redis influxdb

# Wait for databases to be ready
print_status "Waiting for databases to be ready..."
sleep 30

# Run database migrations
print_status "Running database migrations..."

# Check if we're deploying to Kubernetes
if [ "$1" = "--k8s" ]; then
    print_status "Running Kubernetes database migrations..."
    
    # Create migration job
    kubectl apply -f k8s/db-setup-job.yaml -n trading-system
    
    # Wait for migration to complete
    print_status "Waiting for database setup to complete..."
    kubectl wait --for=condition=complete job/db-setup -n trading-system --timeout=300s
    
    # Show migration logs
    kubectl logs job/db-setup -n trading-system
    
    # Clean up migration job
    kubectl delete job db-setup -n trading-system
    
    # Run Alembic migrations
    kubectl apply -f k8s/alembic-migration-job.yaml -n trading-system
    kubectl wait --for=condition=complete job/alembic-migration -n trading-system --timeout=300s
    kubectl logs job/alembic-migration -n trading-system
    kubectl delete job alembic-migration -n trading-system
    
else
    print_status "Running local database migrations..."
    
    # Run database setup
    docker-compose run --rm trading-cli python scripts/create_backtest_tables.py
    
    # Run Alembic migrations
    docker-compose run --rm trading-cli alembic upgrade head
    
    # Ensure indexes are created
    docker-compose run --rm trading-cli python scripts/manage_indexes.py ensure
fi

# Build and start microservices
print_status "Building and starting microservices..."
docker-compose up -d trading-service market-data-service portfolio-service risk-service strategy-service order-service analytics-service user-service

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 60

# Start monitoring and logging
print_status "Starting monitoring and logging services..."
docker-compose up -d prometheus grafana elasticsearch kibana logstash

# Start API Gateway
print_status "Starting API Gateway..."
docker-compose up -d api-gateway

# Health check
print_status "Performing health checks..."
sleep 30

# Check if services are running
services=("trading-service" "market-data-service" "portfolio-service" "risk-service" "strategy-service" "order-service" "analytics-service" "user-service" "api-gateway")

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        print_status "$service is running"
    else
        print_error "$service is not running"
    fi
done

# Display service URLs
echo ""
print_status "🎉 Trading System deployed successfully!"
echo ""
echo "📊 Service URLs:"
echo "  API Gateway:     http://localhost:8000"
echo "  Command API:     http://localhost:8001"
echo "  Query API:       http://localhost:8002"
echo "  Grafana:         http://localhost:3000 (admin/admin)"
echo "  Kibana:          http://localhost:5601"
echo "  Prometheus:      http://localhost:9090"
echo "  EventStore:      http://localhost:2113"
echo ""
echo "📝 Useful commands:"
echo "  View logs:       docker-compose logs -f [service-name]"
echo "  Stop services:   docker-compose down"
echo "  Restart:         docker-compose restart [service-name]"
echo "  Scale service:   docker-compose up -d --scale [service-name]=3"
echo ""

# Optional: Deploy to Kubernetes
if [ "$1" = "--k8s" ]; then
    print_status "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install it and try again."
        exit 1
    fi
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Deploy services
    kubectl apply -f k8s/ -n trading-system
    
    print_status "Kubernetes deployment completed!"
    echo ""
    echo "🔍 Check deployment status:"
    echo "  kubectl get pods -n trading-system"
    echo "  kubectl get services -n trading-system"
    echo ""
fi

print_status "Deployment completed successfully! 🎉" 