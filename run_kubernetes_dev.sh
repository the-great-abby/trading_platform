#!/bin/bash
# Kubernetes-First Development Script
# Demonstrates the preferred Kubernetes approach with Docker Compose fallback

set -e

echo "☸️  Kubernetes-First Development Demo"
echo "====================================="

# Check if kubectl is available and cluster is accessible
check_kubernetes() {
    if command -v kubectl &> /dev/null; then
        if kubectl cluster-info &> /dev/null; then
            echo "✅ Kubernetes cluster is accessible"
            return 0
        else
            echo "⚠️  kubectl found but cluster not accessible"
            return 1
        fi
    else
        echo "❌ kubectl not found"
        return 1
    fi
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "✅ Docker is available"
        return 0
    else
        echo "❌ Docker is not available"
        return 1
    fi
}

# Function to run Python script in Kubernetes
run_python_in_k8s() {
    local script=$1
    local service=${2:-trading-service}
    
    echo "☸️  Running $script in Kubernetes $service..."
    kubectl exec -it deployment/$service -- python $script -n trading-system
}

# Function to install package in Kubernetes
install_package_in_k8s() {
    local package=$1
    local service=${2:-trading-service}
    
    echo "📦 Installing $package in Kubernetes $service..."
    kubectl exec -it deployment/$service -- pip install $package -n trading-system
}

# Function to run tests in Kubernetes
run_tests_in_k8s() {
    local test_file=${1:-""}
    local service=${2:-trading-service}
    
    if [ -n "$test_file" ]; then
        echo "🧪 Running $test_file in Kubernetes $service..."
        kubectl exec -it deployment/$service -- python -m pytest tests/$test_file -v -n trading-system
    else
        echo "🧪 Running all tests in Kubernetes $service..."
        kubectl exec -it deployment/$service -- python -m pytest tests/ -v -n trading-system
    fi
}

# Function to run Python script in Docker Compose (fallback)
run_python_in_docker() {
    local script=$1
    local service=${2:-trading-service}
    
    echo "🐳 Running $script in Docker $service (fallback)..."
    docker-compose exec $service python $script
}

# Function to install package in Docker Compose (fallback)
install_package_in_docker() {
    local package=$1
    local service=${2:-trading-service}
    
    echo "📦 Installing $package in Docker $service (fallback)..."
    docker-compose exec $service pip install $package
}

# Function to run tests in Docker Compose (fallback)
run_tests_in_docker() {
    local test_file=${1:-""}
    local service=${2:-trading-cli}
    
    if [ -n "$test_file" ]; then
        echo "🧪 Running $test_file in Docker $service (fallback)..."
        docker-compose run --rm $service python -m pytest tests/$test_file -v
    else
        echo "🧪 Running all tests in Docker $service (fallback)..."
        docker-compose run --rm $service python -m pytest tests/ -v
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "📋 Available Commands:"
    echo "1) Run Python script (Kubernetes preferred)"
    echo "2) Install Python package (Kubernetes preferred)"
    echo "3) Run tests (Kubernetes preferred)"
    echo "4) Deploy to Kubernetes"
    echo "5) Check Kubernetes status"
    echo "6) Port forward service"
    echo "7) Exit"
    echo ""
}

# Interactive menu
while true; do
    show_menu
    read -p "Select an option (1-7): " choice
    
    case $choice in
        1)
            read -p "Enter script path (e.g., src/main.py): " script
            if [ -n "$script" ]; then
                if check_kubernetes; then
                    run_python_in_k8s "$script"
                elif check_docker; then
                    run_python_in_docker "$script"
                else
                    echo "❌ Neither Kubernetes nor Docker is available"
                fi
            else
                echo "❌ Script path is required"
            fi
            ;;
        2)
            read -p "Enter package name (e.g., yfinance): " package
            if [ -n "$package" ]; then
                if check_kubernetes; then
                    install_package_in_k8s "$package"
                elif check_docker; then
                    install_package_in_docker "$package"
                else
                    echo "❌ Neither Kubernetes nor Docker is available"
                fi
            else
                echo "❌ Package name is required"
            fi
            ;;
        3)
            read -p "Enter test file (optional, press Enter for all tests): " test_file
            if check_kubernetes; then
                run_tests_in_k8s "$test_file"
            elif check_docker; then
                run_tests_in_docker "$test_file"
            else
                echo "❌ Neither Kubernetes nor Docker is available"
            fi
            ;;
        4)
            if check_kubernetes; then
                echo "🚀 Deploying to Kubernetes..."
                make k8s-deploy
                echo "✅ Kubernetes deployment completed!"
            else
                echo "❌ Kubernetes is not available"
            fi
            ;;
        5)
            if check_kubernetes; then
                echo "📊 Kubernetes Status:"
                kubectl get pods -n trading-system
                echo ""
                echo "📊 Services:"
                kubectl get services -n trading-system
            else
                echo "❌ Kubernetes is not available"
            fi
            ;;
        6)
            if check_kubernetes; then
                read -p "Enter service name (e.g., trading-service): " service
                read -p "Enter port (e.g., 8000): " port
                if [ -n "$service" ] && [ -n "$port" ]; then
                    echo "🔗 Port forwarding $service on port $port..."
                    kubectl port-forward deployment/$service $port:$port -n trading-system
                else
                    echo "❌ Service name and port are required"
                fi
            else
                echo "❌ Kubernetes is not available"
            fi
            ;;
        7)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-7."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done 