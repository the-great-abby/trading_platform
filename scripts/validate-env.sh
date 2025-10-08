#!/bin/bash
# Environment file validation script
# Validates .env file format and required variables

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SCRIPT_DIR/secret-config.yaml"

# Default values
ENV_FILE="${1:-$PROJECT_ROOT/.env}"
NAMESPACE="${NAMESPACE:-default}"

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

# Error handling function
handle_error() {
    local error_type="$1"
    local message="$2"
    local env_var="${3:-}"
    
    log_error "Validation Error: $message"
    
    if [[ -n "$env_var" ]]; then
        echo "Variable: $env_var"
    fi
    
    echo "Next steps:"
    case "$error_type" in
        "file_not_found")
            echo "  1. Create .env file: cp $PROJECT_ROOT/config.env.example $PROJECT_ROOT/.env"
            echo "  2. Add your secret values to .env"
            echo "  3. Set permissions: chmod 600 $PROJECT_ROOT/.env"
            ;;
        "permission_error")
            echo "  1. Set restrictive permissions: chmod 600 $ENV_FILE"
            echo "  2. Verify file ownership: ls -la $ENV_FILE"
            ;;
        "invalid_format")
            echo "  1. Check .env file format (key=value pairs)"
            echo "  2. Remove empty lines and invalid characters"
            echo "  3. Ensure no spaces around equals signs"
            ;;
        "missing_required")
            echo "  1. Add missing required variables to .env"
            echo "  2. Check $PROJECT_ROOT/config.env.example for examples"
            echo "  3. Re-run validation: $0 $ENV_FILE"
            ;;
        "empty_value")
            echo "  1. Provide values for all variables"
            echo "  2. Remove variables with empty values"
            echo "  3. Check for trailing spaces or special characters"
            ;;
        "invalid_naming")
            echo "  1. Use uppercase letters and underscores for variable names"
            echo "  2. Follow pattern: ^[A-Z][A-Z0-9_]*$"
            echo "  3. Examples: POLYGON_API_KEY, DB_HOST"
            ;;
    esac
    
    exit 1
}

# Validate file exists and is readable
validate_file_exists() {
    if [[ ! -f "$ENV_FILE" ]]; then
        handle_error "file_not_found" ".env file not found: $ENV_FILE"
    fi
    
    if [[ ! -r "$ENV_FILE" ]]; then
        handle_error "permission_error" "Cannot read .env file: $ENV_FILE"
    fi
}

# Validate file permissions
validate_file_permissions() {
    local perms
    perms=$(stat -f "%OLp" "$ENV_FILE" 2>/dev/null || stat -c "%a" "$ENV_FILE" 2>/dev/null)
    
    # Convert to decimal if octal
    if [[ $perms =~ ^[0-7]+$ ]]; then
        perms=$((8#$perms))
    fi
    
    # Check if permissions are too permissive (greater than 600)
    if [[ $perms -gt 600 ]]; then
        handle_error "permission_error" "File permissions too permissive: $perms (should be 600 or less)"
    fi
}

# Load and validate .env file
load_env_file() {
    local temp_file
    temp_file=$(mktemp)
    
    # Clean the .env file (remove comments and empty lines)
    grep -v '^#' "$ENV_FILE" | grep -v '^[[:space:]]*$' > "$temp_file"
    
    # Validate format
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^[A-Z][A-Z0-9_]*=.+$ ]]; then
            handle_error "invalid_format" "Invalid line format: $line"
        fi
    done < "$temp_file"
    
    # Source the clean file
    source "$temp_file"
    
    # Clean up
    rm -f "$temp_file"
}

# Validate environment variable naming
validate_var_naming() {
    local var_name
    local value
    
    for var_name in "${!POLYGON_API_KEY@}" "${!ALPHA_VANTAGE_API_KEY@}" "${!DB_HOST@}" "${!DB_USERNAME@}" "${!DB_PASSWORD@}" "${!DB_NAME@}"; do
        if [[ -n "${!var_name:-}" ]]; then
            # Check naming pattern
            if [[ ! "$var_name" =~ ^[A-Z][A-Z0-9_]*$ ]]; then
                handle_error "invalid_naming" "Invalid variable name pattern: $var_name" "$var_name"
            fi
            
            # Check value is not empty
            value="${!var_name}"
            if [[ -z "$value" ]]; then
                handle_error "empty_value" "Variable has empty value" "$var_name"
            fi
            
            # Check value length
            if [[ ${#value} -lt 1 ]]; then
                handle_error "empty_value" "Variable value too short" "$var_name"
            fi
            
            if [[ ${#value} -gt 1024 ]]; then
                handle_error "invalid_format" "Variable value too long (>1024 chars)" "$var_name"
            fi
        fi
    done
}

# Validate required variables
validate_required_vars() {
    local required_vars=(
        "POLYGON_API_KEY"
        "DB_HOST"
        "DB_USERNAME"
        "DB_PASSWORD"
        "DB_NAME"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        local missing_list
        missing_list=$(IFS=", "; echo "${missing_vars[*]}")
        handle_error "missing_required" "Missing required variables: $missing_list"
    fi
}

# Count and display validated secrets
display_validated_secrets() {
    local api_keys=0
    local db_vars=0
    
    # Count API keys
    for var in POLYGON_API_KEY ALPHA_VANTAGE_API_KEY TWILIO_API_KEY SENDGRID_API_KEY; do
        if [[ -n "${!var:-}" ]]; then
            ((api_keys++))
        fi
    done
    
    # Count database variables
    for var in DB_HOST DB_USERNAME DB_PASSWORD DB_NAME DB_PORT DB_SSL_MODE; do
        if [[ -n "${!var:-}" ]]; then
            ((db_vars++))
        fi
    done
    
    log_success "Found $api_keys API key configuration(s)"
    log_success "Found $db_vars database credential variable(s)"
    
    if [[ $api_keys -gt 0 ]]; then
        log_info "API Keys will be stored as individual secrets:"
        for var in POLYGON_API_KEY ALPHA_VANTAGE_API_KEY TWILIO_API_KEY SENDGRID_API_KEY; do
            if [[ -n "${!var:-}" ]]; then
                local k8s_name
                k8s_name=$(echo "$var" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
                echo "  - $var → $k8s_name"
            fi
        done
    fi
    
    if [[ $db_vars -gt 0 ]]; then
        log_info "Database credentials will be combined into: db-credentials"
        echo "  - DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME → db-credentials"
    fi
}

# Main validation function
main() {
    log_info "Validating .env file: $ENV_FILE"
    
    # Run all validations
    validate_file_exists
    validate_file_permissions
    load_env_file
    validate_var_naming
    validate_required_vars
    
    # Display results
    log_success "All validations passed"
    display_validated_secrets
    log_success "Ready to update secrets"
    
    echo ""
    log_info "Next steps:"
    echo "  1. Run: make secrets-update"
    echo "  2. Verify secrets: kubectl get secrets"
    echo "  3. Check specific secret: kubectl describe secret <secret-name>"
}

# Run main function
main "$@"













