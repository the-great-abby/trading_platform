#!/bin/bash
# Secret listing script
# Lists Kubernetes secrets managed by this system

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
NAMESPACE="${1:-${NAMESPACE:-default}}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-table}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
            echo "  1. Check cluster permissions: kubectl auth can-i list secrets"
            echo "  2. Verify namespace access: kubectl auth can-i list secrets --namespace=$NAMESPACE"
            echo "  3. Contact cluster administrator for access"
            ;;
        "namespace_error")
            echo "  1. Check namespace exists: kubectl get namespace $NAMESPACE"
            echo "  2. Create namespace if needed: kubectl create namespace $NAMESPACE"
            echo "  3. Use different namespace: $0 <namespace>"
            ;;
    esac
    
    exit 1
}

# Validate prerequisites
validate_prerequisites() {
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
        handle_error "namespace_error" "Namespace $NAMESPACE does not exist"
    fi
    
    # Check permissions
    if ! kubectl auth can-i list secrets --namespace="$NAMESPACE" &> /dev/null; then
        handle_error "permission_error" "Insufficient permissions to list secrets in namespace $NAMESPACE"
    fi
}

# Get managed secrets
get_managed_secrets() {
    local secrets_json
    secrets_json=$(kubectl get secrets --namespace="$NAMESPACE" -o json)
    
    # Filter for secrets we manage (API keys and database credentials)
    echo "$secrets_json" | jq -r '
        .items[] | 
        select(
            .metadata.name | test("^(polygon-api-key|alpha-vantage-api-key|twilio-api-key|sendgrid-api-key|db-credentials)$")
        ) |
        {
            name: .metadata.name,
            type: .metadata.type,
            created: .metadata.creationTimestamp,
            keys: (.data | keys | sort)
        }
    '
}

# Display secrets in table format
display_secrets_table() {
    local secrets_data="$1"
    
    if [[ -z "$secrets_data" ]]; then
        log_warning "No managed secrets found in namespace '$NAMESPACE'"
        echo ""
        log_info "To create secrets, run: make secrets-update"
        return
    fi
    
    log_success "Listing Kubernetes secrets..."
    echo -e "${CYAN}📋 Managed secrets in namespace '$NAMESPACE':${NC}"
    echo ""
    
    # Parse and display each secret
    echo "$secrets_data" | jq -r '
        .name as $name |
        .keys as $keys |
        .created as $created |
        .type as $type |
        
        # Determine secret type based on name
        (if $name | test("api-key") then "api-key" else "database" end) as $secret_type |
        
        # Format created date
        ($created | split("T")[0]) as $date |
        
        # Display secret info
        "Name: " + $name + "\n" +
        "Type: " + $secret_type + "\n" +
        "Created: " + $date + "\n" +
        "Keys: [" + ($keys | join(", ")) + "]\n"
    '
}

# Display secrets in JSON format
display_secrets_json() {
    local secrets_data="$1"
    
    if [[ -z "$secrets_data" ]]; then
        echo '{"status": "success", "secrets": [], "namespace": "'"$NAMESPACE"'", "message": "No managed secrets found"}'
        return
    fi
    
    # Convert to proper JSON array
    local json_output
    json_output=$(echo "$secrets_data" | jq -s '
        {
            status: "success",
            namespace: "'"$NAMESPACE"'",
            secrets: [.[] | {
                name: .name,
                type: (if .name | test("api-key") then "api-key" else "database" end),
                created: .created,
                keys: .keys
            }]
        }
    ')
    
    echo "$json_output"
}

# Display secrets summary
display_secrets_summary() {
    local secrets_data="$1"
    
    if [[ -z "$secrets_data" ]]; then
        echo "No managed secrets found"
        return
    fi
    
    local total_secrets
    local api_secrets
    local db_secrets
    
    total_secrets=$(echo "$secrets_data" | jq -s 'length')
    api_secrets=$(echo "$secrets_data" | jq -s '[.[] | select(.name | test("api-key"))] | length')
    db_secrets=$(echo "$secrets_data" | jq -s '[.[] | select(.name == "db-credentials")] | length')
    
    echo "Total secrets: $total_secrets"
    echo "API key secrets: $api_secrets"
    echo "Database secrets: $db_secrets"
}

# Show secret details
show_secret_details() {
    local secret_name="$1"
    
    log_info "Details for secret: $secret_name"
    
    # Get secret details
    local secret_info
    secret_info=$(kubectl get secret "$secret_name" --namespace="$NAMESPACE" -o json 2>/dev/null)
    
    if [[ -z "$secret_info" ]]; then
        log_error "Secret '$secret_name' not found in namespace '$NAMESPACE'"
        return 1
    fi
    
    # Display secret information
    echo "$secret_info" | jq -r '
        "Name: " + .metadata.name + "\n" +
        "Namespace: " + .metadata.namespace + "\n" +
        "Type: " + .type + "\n" +
        "Created: " + .metadata.creationTimestamp + "\n" +
        "Keys: " + (.data | keys | join(", "))
    '
    
    echo ""
    log_info "To view secret values (base64 encoded):"
    echo "  kubectl get secret $secret_name --namespace=$NAMESPACE -o yaml"
    
    echo ""
    log_info "To decode a specific key:"
    echo "  kubectl get secret $secret_name --namespace=$NAMESPACE -o jsonpath='{.data.<key>}' | base64 -d"
}

# Main execution function
main() {
    log_info "Listing Kubernetes secrets..."
    log_info "Namespace: $NAMESPACE"
    log_info "Output format: $OUTPUT_FORMAT"
    
    # Validate prerequisites
    validate_prerequisites
    
    # Get managed secrets
    local secrets_data
    secrets_data=$(get_managed_secrets)
    
    # Display based on output format
    case "$OUTPUT_FORMAT" in
        "json")
            display_secrets_json "$secrets_data"
            ;;
        "summary")
            display_secrets_summary "$secrets_data"
            ;;
        "table"|*)
            display_secrets_table "$secrets_data"
            ;;
    esac
    
    # Show additional information
    if [[ "$OUTPUT_FORMAT" == "table" ]]; then
        echo ""
        log_info "Additional commands:"
        echo "  • View all secrets: kubectl get secrets --namespace=$NAMESPACE"
        echo "  • Describe secret: kubectl describe secret <secret-name> --namespace=$NAMESPACE"
        echo "  • Get secret YAML: kubectl get secret <secret-name> --namespace=$NAMESPACE -o yaml"
        echo "  • List in JSON: $0 --format json"
        echo "  • Summary only: $0 --format summary"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --details)
            if [[ $# -lt 2 ]]; then
                log_error "Secret name required for --details option"
                exit 1
            fi
            validate_prerequisites
            show_secret_details "$2"
            exit 0
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [NAMESPACE]"
            echo ""
            echo "Options:"
            echo "  --format FORMAT    Output format: table, json, summary (default: table)"
            echo "  --namespace NAME   Kubernetes namespace (default: default)"
            echo "  --details SECRET   Show detailed information for specific secret"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # List secrets in default namespace"
            echo "  $0 trading                           # List secrets in 'trading' namespace"
            echo "  $0 --format json                     # Output in JSON format"
            echo "  $0 --details polygon-api-key         # Show details for specific secret"
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            NAMESPACE="$1"
            shift
            ;;
    esac
done

# Run main function
main "$@"











