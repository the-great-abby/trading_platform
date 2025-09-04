#!/bin/bash
# Kubernetes Test Runner Script
# Runs comprehensive tests for Kubernetes configuration and services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="trading-system"
TEST_DIR="tests"
REPORT_DIR="test_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}🔍 Kubernetes Test Suite Runner${NC}"
echo "=================================="
echo "Namespace: $NAMESPACE"
echo "Test Directory: $TEST_DIR"
echo "Report Directory: $REPORT_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ kubectl is available and connected to cluster${NC}"
}

# Function to check if namespace exists
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
        echo "Available namespaces:"
        kubectl get namespaces
        exit 1
    fi
    
    echo -e "${GREEN}✅ Namespace $NAMESPACE exists${NC}"
}

# Function to check if pytest is available
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}⚠️  pytest is not installed, installing requirements...${NC}"
        pip install -r requirements-dev.txt
    fi
    
    echo -e "${GREEN}✅ pytest is available${NC}"
}

# Function to run configuration tests
run_config_tests() {
    echo -e "\n${BLUE}🔧 Running Kubernetes Configuration Tests...${NC}"
    
    local config_report="$REPORT_DIR/kubernetes_config_$TIMESTAMP.html"
    
    if pytest "$TEST_DIR/test_kubernetes_configuration.py" \
        --html="$config_report" \
        --self-contained-html \
        --tb=short \
        -v; then
        echo -e "${GREEN}✅ Configuration tests passed${NC}"
        echo "Report: $config_report"
    else
        echo -e "${RED}❌ Configuration tests failed${NC}"
        echo "Report: $config_report"
        return 1
    fi
}

# Function to run YAML validation tests
run_yaml_tests() {
    echo -e "\n${BLUE}📄 Running Kubernetes YAML Validation Tests...${NC}"
    
    local yaml_report="$REPORT_DIR/kubernetes_yaml_$TIMESTAMP.html"
    
    if pytest "$TEST_DIR/test_kubernetes_yaml_validation.py" \
        --html="$yaml_report" \
        --self-contained-html \
        --tb=short \
        -v; then
        echo -e "${GREEN}✅ YAML validation tests passed${NC}"
        echo "Report: $yaml_report"
    else
        echo -e "${RED}❌ YAML validation tests failed${NC}"
        echo "Report: $yaml_report"
        return 1
    fi
}

# Function to run service health tests
run_health_tests() {
    echo -e "\n${BLUE}🏥 Running Kubernetes Service Health Tests...${NC}"
    
    local health_report="$REPORT_DIR/kubernetes_health_$TIMESTAMP.html"
    
    if pytest "$TEST_DIR/test_kubernetes_service_health.py" \
        --html="$health_report" \
        --self-contained-html \
        --tb=short \
        -v; then
        echo -e "${GREEN}✅ Service health tests passed${NC}"
        echo "Report: $health_report"
    else
        echo -e "${RED}❌ Service health tests failed${NC}"
        echo "Report: $health_report"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    echo -e "\n${BLUE}🚀 Running All Kubernetes Tests...${NC}"
    
    local all_report="$REPORT_DIR/kubernetes_all_$TIMESTAMP.html"
    
    if pytest "$TEST_DIR/test_kubernetes_*.py" \
        --html="$all_report" \
        --self-contained-html \
        --tb=short \
        -v; then
        echo -e "${GREEN}✅ All tests passed${NC}"
        echo "Report: $all_report"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo "Report: $all_report"
        return 1
    fi
}

# Function to generate summary report
generate_summary() {
    echo -e "\n${BLUE}📊 Test Summary${NC}"
    echo "=================="
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Count test files
    for test_file in "$TEST_DIR"/test_kubernetes_*.py; do
        if [[ -f "$test_file" ]]; then
            echo "Test file: $(basename "$test_file")"
            total_tests=$((total_tests + 1))
        fi
    done
    
    echo ""
    echo "Total test files: $total_tests"
    echo "Reports generated in: $REPORT_DIR"
    echo ""
    
    # List generated reports
    echo "Generated reports:"
    for report in "$REPORT_DIR"/kubernetes_*_"$TIMESTAMP".html; do
        if [[ -f "$report" ]]; then
            echo "  - $(basename "$report")"
        fi
    done
}

# Function to show cluster status
show_cluster_status() {
    echo -e "\n${BLUE}📋 Cluster Status Summary${NC}"
    echo "========================="
    
    echo -e "\n${YELLOW}Namespaces:${NC}"
    kubectl get namespaces
    
    echo -e "\n${YELLOW}Pods in $NAMESPACE:${NC}"
    kubectl get pods -n "$NAMESPACE" --no-headers | wc -l | tr -d ' ' && echo " pods running"
    
    echo -e "\n${YELLOW}Services in $NAMESPACE:${NC}"
    kubectl get services -n "$NAMESPACE" --no-headers | wc -l | tr -d ' ' && echo " services"
    
    echo -e "\n${YELLOW}Deployments in $NAMESPACE:${NC}"
    kubectl get deployments -n "$NAMESPACE" --no-headers | wc -l | tr -d ' ' && echo " deployments"
}

# Main execution
main() {
    echo -e "${BLUE}Starting Kubernetes test suite...${NC}"
    
    # Pre-flight checks
    check_kubectl
    check_namespace
    check_pytest
    
    # Show current cluster status
    show_cluster_status
    
    # Parse command line arguments
    case "${1:-all}" in
        "config")
            run_config_tests
            ;;
        "yaml")
            run_yaml_tests
            ;;
        "health")
            run_health_tests
            ;;
        "all"|*)
            run_all_tests
            ;;
    esac
    
    # Generate summary
    generate_summary
    
    echo -e "\n${GREEN}🎉 Kubernetes test suite completed!${NC}"
}

# Handle command line arguments
case "${1:-all}" in
    "config"|"yaml"|"health"|"all"|"help"|"-h"|"--help")
        if [[ "$1" == "help" || "$1" == "-h" || "$1" == "--help" ]]; then
            echo "Usage: $0 [test_type]"
            echo ""
            echo "Test types:"
            echo "  config  - Run configuration tests only"
            echo "  yaml    - Run YAML validation tests only"
            echo "  health  - Run service health tests only"
            echo "  all     - Run all tests (default)"
            echo "  help    - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Run all tests"
            echo "  $0 config       # Run only configuration tests"
            echo "  $0 yaml         # Run only YAML validation tests"
            echo "  $0 health       # Run only service health tests"
            exit 0
        fi
        main "$1"
        ;;
    *)
        echo "Unknown test type: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac



