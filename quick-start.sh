#!/bin/bash

# Quick Start Script for Trading System
# This script provides a fast way to test the deployment

set -e

echo "🚀 Quick Start - Trading System Deployment"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp config.env.example .env
    print_warning "Please edit .env file with your API credentials before continuing."
    print_warning "Press Enter when ready to continue..."
    read
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data monitoring

# Start infrastructure services
print_status "Starting infrastructure services..."
docker-compose up -d write-db read-db eventstore kafka zookeeper redis influxdb

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Test database connectivity
print_status "Testing database connectivity..."
if docker-compose exec -T write-db pg_isready -U postgres; then
    print_status "Write database is ready"
else
    print_error "Write database is not ready"
    exit 1
fi

if docker-compose exec -T read-db pg_isready -U postgres; then
    print_status "Read database is ready"
else
    print_error "Read database is not ready"
    exit 1
fi

# Start a subset of services for testing
print_status "Starting core services for testing..."
docker-compose up -d trading-service market-data-service portfolio-service

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Test service health
print_status "Testing service health..."

# Test API Gateway
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "API Gateway is healthy"
else
    print_warning "API Gateway health check failed"
fi

# Test Trading Service
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Trading Service is healthy"
else
    print_warning "Trading Service health check failed"
fi

# Test Market Data Service
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    print_status "Market Data Service is healthy"
else
    print_warning "Market Data Service health check failed"
fi

# Display service status
print_status "Service Status:"
docker-compose ps

# Display service URLs
echo ""
print_status "🎉 Quick start completed!"
echo ""
echo "📊 Service URLs:"
echo "  API Gateway:     http://localhost:8000"
echo "  Command API:     http://localhost:8001"
echo "  Query API:       http://localhost:8002"
echo ""
echo "📝 Next Steps:"
echo "  1. Configure your API credentials in .env"
echo "  2. Start all services: ./deploy.sh"
echo "  3. Access the web dashboard: http://localhost:8000"
echo "  4. View logs: docker-compose logs -f [service-name]"
echo ""

# Optional: Start monitoring
read -p "Do you want to start monitoring services (Grafana, Prometheus)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting monitoring services..."
    docker-compose up -d prometheus grafana kibana
    echo ""
    echo "📊 Monitoring URLs:"
    echo "  Grafana:        http://localhost:3000 (admin/admin)"
    echo "  Prometheus:     http://localhost:9090"
    echo "  Kibana:         http://localhost:5601"
fi

print_status "Quick start completed successfully! 🎉" 