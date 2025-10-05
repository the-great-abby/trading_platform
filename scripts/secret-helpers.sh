#!/bin/bash
# Secret helper utilities script
# Provides utility functions for secret management

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Convert environment variable name to Kubernetes secret name
convert_name() {
    local env_var="$1"
    
    if [[ -z "$env_var" ]]; then
        log_error "Environment variable name is required"
        return 1
    fi
    
    # Validate input format
    if [[ ! "$env_var" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
        log_error "Invalid environment variable name: $env_var"
        log_error "Must match pattern: ^[A-Z][A-Z0-9_]*$"
        return 1
    fi
    
    # Convert to Kubernetes secret name
    local k8s_name
    k8s_name=$(echo "$env_var" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
    
    # Validate Kubernetes naming requirements
    if [[ ! "$k8s_name" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        log_error "Generated Kubernetes name is invalid: $k8s_name"
        return 1
    fi
    
    echo "$k8s_name"
}

# Convert multiple environment variable names
convert_names() {
    local input_file="$1"
    
    if [[ -z "$input_file" ]]; then
        log_error "Input file is required"
        return 1
    fi
    
    if [[ ! -f "$input_file" ]]; then
        log_error "Input file not found: $input_file"
        return 1
    fi
    
    log_info "Converting environment variable names to Kubernetes secret names..."
    
    while IFS= read -r env_var; do
        # Skip empty lines and comments
        if [[ -z "$env_var" || "$env_var" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        local k8s_name
        if k8s_name=$(convert_name "$env_var" 2>/dev/null); then
            echo "$env_var -> $k8s_name"
        else
            log_error "Failed to convert: $env_var"
            return 1
        fi
    done < "$input_file"
    
    log_success "Name conversion completed"
}

# Validate Kubernetes secret name
validate_k8s_name() {
    local k8s_name="$1"
    
    if [[ -z "$k8s_name" ]]; then
        log_error "Kubernetes secret name is required"
        return 1
    fi
    
    # Check naming pattern
    if [[ ! "$k8s_name" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        log_error "Invalid Kubernetes secret name: $k8s_name"
        log_error "Must match pattern: ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"
        return 1
    fi
    
    # Check length
    if [[ ${#k8s_name} -gt 253 ]]; then
        log_error "Kubernetes secret name too long: $k8s_name (${#k8s_name} chars)"
        log_error "Maximum length is 253 characters"
        return 1
    fi
    
    # Check for consecutive hyphens
    if [[ "$k8s_name" =~ -- ]]; then
        log_error "Kubernetes secret name contains consecutive hyphens: $k8s_name"
        return 1
    fi
    
    log_success "Kubernetes secret name is valid: $k8s_name"
    return 0
}

# Get secret type based on name
get_secret_type() {
    local secret_name="$1"
    
    if [[ -z "$secret_name" ]]; then
        log_error "Secret name is required"
        return 1
    fi
    
    # Determine type based on name patterns
    if [[ "$secret_name" =~ -api-key$ ]]; then
        echo "api-key"
    elif [[ "$secret_name" == "db-credentials" ]]; then
        echo "database"
    else
        echo "unknown"
    fi
}

# Generate secret mapping configuration
generate_mapping_config() {
    local env_file="${1:-$PROJECT_ROOT/.env}"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi
    
    log_info "Generating secret mapping configuration..."
    
    # API keys (individual secrets)
    local api_keys=()
    local db_vars=()
    
    # Parse .env file and categorize variables
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Remove whitespace
        key=$(echo "$key" | tr -d '[:space:]')
        
        # Categorize variables
        if [[ "$key" =~ ^(POLYGON_API_KEY|ALPHA_VANTAGE_API_KEY|TWILIO_API_KEY|SENDGRID_API_KEY)$ ]]; then
            api_keys+=("$key")
        elif [[ "$key" =~ ^DB_ ]]; then
            db_vars+=("$key")
        fi
    done < "$env_file"
    
    # Generate configuration
    echo "# Generated secret mapping configuration"
    echo "# Source: $env_file"
    echo ""
    
    if [[ ${#api_keys[@]} -gt 0 ]]; then
        echo "# API Keys (individual secrets)"
        for key in "${api_keys[@]}"; do
            local k8s_name
            k8s_name=$(convert_name "$key")
            echo "$key -> $k8s_name (api-key)"
        done
        echo ""
    fi
    
    if [[ ${#db_vars[@]} -gt 0 ]]; then
        echo "# Database Credentials (combined secret)"
        for key in "${db_vars[@]}"; do
            echo "$key -> db-credentials (database)"
        done
        echo ""
    fi
    
    log_success "Mapping configuration generated"
}

# Check cluster connectivity
check_cluster_connectivity() {
    local namespace="${1:-default}"
    
    log_info "Checking cluster connectivity..."
    
    # Check kubectl availability
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl command not found"
        return 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    # Check namespace
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        log_warning "Namespace '$namespace' does not exist"
    fi
    
    # Check permissions
    if ! kubectl auth can-i create secrets --namespace="$namespace" &> /dev/null; then
        log_warning "Insufficient permissions to create secrets in namespace '$namespace'"
    fi
    
    if ! kubectl auth can-i list secrets --namespace="$namespace" &> /dev/null; then
        log_warning "Insufficient permissions to list secrets in namespace '$namespace'"
    fi
    
    log_success "Cluster connectivity check completed"
}

# Performance test for name conversion
performance_test() {
    local iterations="${1:-1000}"
    
    log_info "Running performance test for name conversion..."
    log_info "Iterations: $iterations"
    
    local start_time
    start_time=$(date +%s%N)
    
    # Test variables
    local test_vars=(
        "POLYGON_API_KEY"
        "ALPHA_VANTAGE_API_KEY"
        "DB_HOST"
        "DB_USERNAME"
        "DB_PASSWORD"
        "DB_NAME"
        "TWILIO_API_KEY"
        "SENDGRID_API_KEY"
    )
    
    for ((i=0; i<iterations; i++)); do
        for var in "${test_vars[@]}"; do
            convert_name "$var" &> /dev/null
        done
    done
    
    local end_time
    end_time=$(date +%s%N)
    
    local duration_ms=$(( (end_time - start_time) / 1000000 ))
    local duration_s=$(( duration_ms / 1000 ))
    
    log_success "Performance test completed"
    echo "Total time: ${duration_s}.$(( (duration_ms % 1000) / 100 ))s"
    echo "Operations: $(( iterations * ${#test_vars[@]} ))"
    echo "Average: $(( duration_ms / (iterations * ${#test_vars[@]}) ))ms per operation"
}

# Show usage information
show_usage() {
    echo "Secret Helper Utilities"
    echo ""
    echo "Usage: $0 COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  convert-name ENV_VAR          Convert environment variable to K8s secret name"
    echo "  convert-names FILE            Convert multiple names from file"
    echo "  validate-k8s-name NAME        Validate Kubernetes secret name"
    echo "  get-secret-type NAME          Get secret type based on name"
    echo "  generate-mapping [FILE]       Generate mapping configuration"
    echo "  check-cluster [NAMESPACE]     Check cluster connectivity"
    echo "  performance-test [ITERATIONS] Run performance test"
    echo "  help                          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 convert-name POLYGON_API_KEY"
    echo "  $0 convert-names variables.txt"
    echo "  $0 validate-k8s-name polygon-api-key"
    echo "  $0 get-secret-type db-credentials"
    echo "  $0 generate-mapping .env"
    echo "  $0 check-cluster default"
    echo "  $0 performance-test 1000"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "convert-name")
            if [[ $# -lt 2 ]]; then
                log_error "Environment variable name required"
                echo "Usage: $0 convert-name ENV_VAR"
                exit 1
            fi
            convert_name "$2"
            ;;
        "convert-names")
            if [[ $# -lt 2 ]]; then
                log_error "Input file required"
                echo "Usage: $0 convert-names FILE"
                exit 1
            fi
            convert_names "$2"
            ;;
        "validate-k8s-name")
            if [[ $# -lt 2 ]]; then
                log_error "Kubernetes secret name required"
                echo "Usage: $0 validate-k8s-name NAME"
                exit 1
            fi
            validate_k8s_name "$2"
            ;;
        "get-secret-type")
            if [[ $# -lt 2 ]]; then
                log_error "Secret name required"
                echo "Usage: $0 get-secret-type NAME"
                exit 1
            fi
            get_secret_type "$2"
            ;;
        "generate-mapping")
            generate_mapping_config "${2:-}"
            ;;
        "check-cluster")
            check_cluster_connectivity "${2:-default}"
            ;;
        "performance-test")
            performance_test "${2:-1000}"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

