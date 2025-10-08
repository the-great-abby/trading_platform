#!/bin/bash
# Secret update script
# Updates Kubernetes secrets from .env file

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENV_FILE="${1:-$PROJECT_ROOT/.env}"
NAMESPACE="${NAMESPACE:-default}"
DRY_RUN="${DRY_RUN:-false}"

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
    
    log_error "$message"
    
    echo "Next steps:"
    case "$error_type" in
        "cluster_error")
            echo "  1. Check cluster connectivity: kubectl cluster-info"
            echo "  2. Verify kubeconfig: kubectl config current-context"
            echo "  3. Switch context if needed: kubectl config use-context <context>"
            ;;
        "permission_error")
            echo "  1. Check cluster permissions: kubectl auth can-i create secrets"
            echo "  2. Verify namespace access: kubectl auth can-i create secrets --namespace=$NAMESPACE"
            echo "  3. Contact cluster administrator for access"
            ;;
        "validation_error")
            echo "  1. Validate .env file: $SCRIPT_DIR/validate-env.sh $ENV_FILE"
            echo "  2. Check file permissions: ls -la $ENV_FILE"
            echo "  3. Fix any validation errors and retry"
            ;;
        "kubectl_error")
            echo "  1. Check kubectl version: kubectl version"
            echo "  2. Verify cluster is accessible: kubectl get nodes"
            echo "  3. Check namespace exists: kubectl get namespace $NAMESPACE"
            ;;
    esac
    
    exit 1
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    # Check kubectl is available
    if ! command -v kubectl &> /dev/null; then
        handle_error "cluster_error" "kubectl command not found"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        handle_error "cluster_error" "Cannot connect to Kubernetes cluster"
    fi
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist, creating..."
        if [[ "$DRY_RUN" != "true" ]]; then
            kubectl create namespace "$NAMESPACE" || handle_error "kubectl_error" "Failed to create namespace $NAMESPACE"
        fi
    fi
    
    # Check permissions
    if ! kubectl auth can-i create secrets --namespace="$NAMESPACE" &> /dev/null; then
        handle_error "permission_error" "Insufficient permissions to create secrets in namespace $NAMESPACE"
    fi
    
    # Validate .env file
    if ! "$SCRIPT_DIR/validate-env.sh" "$ENV_FILE" &> /dev/null; then
        handle_error "validation_error" ".env file validation failed"
    fi
    
    log_success "Prerequisites validated"
}

# Load environment variables
load_env_variables() {
    log_info "Loading environment variables from $ENV_FILE"
    
    # Source the .env file
    set -a  # Automatically export variables
    source "$ENV_FILE"
    set +a  # Stop automatically exporting
    
    log_success "Environment variables loaded"
}

# Convert environment variable name to Kubernetes secret name
convert_to_k8s_name() {
    local env_var="$1"
    echo "$env_var" | tr '[:upper:]' '[:lower:]' | tr '_' '-'
}

# Create or update API key secrets
update_api_key_secrets() {
    local updated_secrets=()
    
    # API key variables and their corresponding secret names
    local api_keys=(
        "POLYGON_API_KEY:polygon-api-key"
        "ALPHA_VANTAGE_API_KEY:alpha-vantage-api-key"
        "TWILIO_API_KEY:twilio-api-key"
        "SENDGRID_API_KEY:sendgrid-api-key"
    )
    
    for api_key_mapping in "${api_keys[@]}"; do
        local env_var="${api_key_mapping%:*}"
        local secret_name="${api_key_mapping#*:}"
        
        if [[ -n "${!env_var:-}" ]]; then
            log_info "Processing API key: $env_var → $secret_name"
            
            # Create temporary file for secret data
            local temp_file
            temp_file=$(mktemp)
            echo "api-key=${!env_var}" > "$temp_file"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "Would create/update secret: $secret_name"
                kubectl create secret generic "$secret_name" \
                    --from-env-file="$temp_file" \
                    --namespace="$NAMESPACE" \
                    --dry-run=client -o yaml
            else
                # Check if secret exists
                if kubectl get secret "$secret_name" --namespace="$NAMESPACE" &> /dev/null; then
                    # Update existing secret
                    kubectl create secret generic "$secret_name" \
                        --from-env-file="$temp_file" \
                        --namespace="$NAMESPACE" \
                        --dry-run=client -o yaml | kubectl apply -f -
                    log_success "Updated secret: $secret_name"
                else
                    # Create new secret
                    kubectl create secret generic "$secret_name" \
                        --from-env-file="$temp_file" \
                        --namespace="$NAMESPACE"
                    log_success "Created secret: $secret_name"
                fi
                updated_secrets+=("$secret_name")
            fi
            
            # Clean up
            rm -f "$temp_file"
        fi
    done
    
    echo "${updated_secrets[@]}"
}

# Create or update database credentials secret
update_database_secret() {
    local db_vars=("DB_HOST" "DB_USERNAME" "DB_PASSWORD" "DB_NAME" "DB_PORT" "DB_SSL_MODE")
    local has_db_vars=false
    local temp_file
    temp_file=$(mktemp)
    
    # Check if any database variables exist
    for var in "${db_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            has_db_vars=true
            echo "$var=${!var}" >> "$temp_file"
        fi
    done
    
    if [[ "$has_db_vars" == "true" ]]; then
        log_info "Processing database credentials → db-credentials"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "Would create/update secret: db-credentials"
            kubectl create secret generic "db-credentials" \
                --from-env-file="$temp_file" \
                --namespace="$NAMESPACE" \
                --dry-run=client -o yaml
        else
            # Check if secret exists
            if kubectl get secret "db-credentials" --namespace="$NAMESPACE" &> /dev/null; then
                # Update existing secret
                kubectl create secret generic "db-credentials" \
                    --from-env-file="$temp_file" \
                    --namespace="$NAMESPACE" \
                    --dry-run=client -o yaml | kubectl apply -f -
                log_success "Updated secret: db-credentials"
            else
                # Create new secret
                kubectl create secret generic "db-credentials" \
                    --from-env-file="$temp_file" \
                    --namespace="$NAMESPACE"
                log_success "Created secret: db-credentials"
            fi
            echo "db-credentials"
        fi
    fi
    
    # Clean up
    rm -f "$temp_file"
}

# Display next steps
display_next_steps() {
    echo ""
    log_success "Secret update completed successfully!"
    
    echo ""
    log_info "Next steps:"
    echo "  1. Verify secrets: kubectl get secrets --namespace=$NAMESPACE"
    echo "  2. Check specific secret: kubectl describe secret <secret-name> --namespace=$NAMESPACE"
    echo "  3. List all secrets: make secrets-list"
    
    echo ""
    log_info "To restart services using these secrets:"
    echo "  1. Find deployments using secrets: kubectl get deployments --namespace=$NAMESPACE"
    echo "  2. Restart affected services: kubectl rollout restart deployment/<service-name> --namespace=$NAMESPACE"
    echo "  3. Monitor logs: kubectl logs -f deployment/<service-name> --namespace=$NAMESPACE"
}

# Main execution function
main() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Running in dry-run mode (no changes will be made)"
    fi
    
    log_info "Updating Kubernetes secrets from .env file..."
    log_info "Environment file: $ENV_FILE"
    log_info "Namespace: $NAMESPACE"
    
    # Run all steps
    validate_prerequisites
    load_env_variables
    
    # Update secrets
    local api_secrets
    api_secrets=$(update_api_key_secrets)
    local db_secret
    db_secret=$(update_database_secret)
    
    # Combine all updated secrets
    local all_secrets=()
    if [[ -n "$api_secrets" ]]; then
        all_secrets+=($api_secrets)
    fi
    if [[ -n "$db_secret" ]]; then
        all_secrets+=("$db_secret")
    fi
    
    if [[ ${#all_secrets[@]} -gt 0 ]]; then
        log_success "Updated ${#all_secrets[@]} secret(s): ${all_secrets[*]}"
    else
        log_warning "No secrets were updated"
    fi
    
    display_next_steps
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [ENV_FILE]"
            echo ""
            echo "Options:"
            echo "  --dry-run           Show what would be done without making changes"
            echo "  --namespace NAME    Kubernetes namespace (default: default)"
            echo "  --env-file FILE     Path to .env file (default: .env)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use default .env file"
            echo "  $0 /path/to/.env                     # Use specific .env file"
            echo "  $0 --dry-run                         # Show what would be done"
            echo "  $0 --namespace trading               # Use specific namespace"
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            ENV_FILE="$1"
            shift
            ;;
    esac
done

# Run main function
main "$@"













