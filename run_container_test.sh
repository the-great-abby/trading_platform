#!/bin/bash
# Container-based Python execution script
# Demonstrates the proper way to run Python scripts in containers

set -e

echo "🚀 Container-Based Python Execution Demo"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Function to run Python script in container
run_python_in_container() {
    local script=$1
    local service=${2:-trading-cli}
    
    echo "🐳 Running $script in $service container..."
    docker-compose -f docker-compose.dev.yml run --rm $service python $script
}

# Function to install package in container
install_package_in_container() {
    local package=$1
    local service=${2:-trading-cli}
    
    echo "📦 Installing $package in $service container..."
    docker-compose -f docker-compose.dev.yml run --rm $service pip install $package
}

# Function to run tests in container
run_tests_in_container() {
    local test_file=${1:-""}
    local service=${2:-trading-cli}
    
    if [ -n "$test_file" ]; then
        echo "🧪 Running $test_file in $service container..."
        docker-compose -f docker-compose.dev.yml run --rm $service python -m pytest tests/$test_file -v
    else
        echo "🧪 Running all tests in $service container..."
        docker-compose -f docker-compose.dev.yml run --rm $service python -m pytest tests/ -v
    fi
}

# Function to open Python shell in container
open_python_shell() {
    local service=${1:-trading-cli}
    
    echo "🐍 Opening Python shell in $service container..."
    docker-compose -f docker-compose.dev.yml run --rm $service python
}

# Main menu
show_menu() {
    echo ""
    echo "📋 Available Commands:"
    echo "1) Run Python script in container"
    echo "2) Install Python package in container"
    echo "3) Run tests in container"
    echo "4) Open Python shell in container"
    echo "5) Test cached market data system"
    echo "6) Exit"
    echo ""
}

# Interactive menu
while true; do
    show_menu
    read -p "Select an option (1-6): " choice
    
    case $choice in
        1)
            read -p "Enter script path (e.g., src/main.py): " script
            if [ -n "$script" ]; then
                run_python_in_container "$script"
            else
                echo "❌ Script path is required"
            fi
            ;;
        2)
            read -p "Enter package name (e.g., yfinance): " package
            if [ -n "$package" ]; then
                install_package_in_container "$package"
            else
                echo "❌ Package name is required"
            fi
            ;;
        3)
            read -p "Enter test file (optional, press Enter for all tests): " test_file
            run_tests_in_container "$test_file"
            ;;
        4)
            open_python_shell
            ;;
        5)
            echo "🧪 Testing cached market data system..."
            run_python_in_container "test_cached_market_data_container.py"
            ;;
        6)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-6."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done 