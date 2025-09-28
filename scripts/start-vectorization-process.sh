#!/bin/bash
# Vector Database Indexing Process Starter
# This script starts the complete vectorization process for your trading system documentation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi
    log "kubectl found"
}

# Check if we're connected to the right cluster
check_cluster() {
    local current_context=$(kubectl config current-context)
    log "Current kubectl context: $current_context"
    
    if [[ "$current_context" != *"docker-desktop"* ]] && [[ "$current_context" != *"trading"* ]]; then
        warning "Current context doesn't look like the trading system cluster"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check if postgres-vector-storage is running
check_vector_storage() {
    log "Checking postgres-vector-storage service..."
    
    local vector_pods=$(kubectl get pods -n trading-system | grep postgres-vector-storage | wc -l)
    
    if [ "$vector_pods" -eq 0 ]; then
        warning "postgres-vector-storage is not running. Deploying..."
        kubectl apply -f k8s/services/postgres-vector-storage.yaml
        
        log "Waiting for postgres-vector-storage to be ready..."
        kubectl wait --for=condition=ready pod -l app=postgres-vector-storage -n trading-system --timeout=300s
        
        if [ $? -eq 0 ]; then
            success "postgres-vector-storage is now running"
        else
            error "Failed to start postgres-vector-storage"
            exit 1
        fi
    else
        success "postgres-vector-storage is running"
    fi
}

# Check if ollama-controller is running
check_ollama_controller() {
    log "Checking ollama-controller service..."
    
    local ollama_pods=$(kubectl get pods -n ollama-controller 2>/dev/null | grep ollama-controller | wc -l)
    
    if [ "$ollama_pods" -eq 0 ]; then
        warning "ollama-controller is not running in the ollama-controller namespace"
        log "Please ensure Ollama is running locally on port 11434"
        
        # Test local Ollama connection
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            success "Local Ollama is running"
        else
            error "Local Ollama is not accessible on localhost:11434"
            log "Please start Ollama locally: ollama serve"
            exit 1
        fi
    else
        success "ollama-controller is running in Kubernetes"
    fi
}

# Start vectorization job
start_vectorization_job() {
    log "Starting vectorization job..."
    
    # Check if there's a cronjob to create a job from
    local cronjob_exists=$(kubectl get cronjobs -n trading-system | grep architecture-vectorizer | wc -l)
    
    if [ "$cronjob_exists" -gt 0 ]; then
        log "Creating manual vectorization job from cronjob..."
        local job_name="manual-vectorization-$(date +%s)"
        kubectl create job --from=cronjob/architecture-vectorizer-cronjob "$job_name" -n trading-system
        
        success "Vectorization job '$job_name' created"
        
        # Wait for job to complete
        log "Waiting for vectorization job to complete..."
        kubectl wait --for=condition=complete job/"$job_name" -n trading-system --timeout=1800s
        
        if [ $? -eq 0 ]; then
            success "Vectorization job completed successfully"
        else
            error "Vectorization job failed or timed out"
            log "Check job logs: kubectl logs job/$job_name -n trading-system"
        fi
    else
        # Run local vectorization script
        warning "No Kubernetes cronjob found. Running local vectorization script..."
        
        if [ -f "scripts/vectorize-repo-locally.py" ]; then
            log "Running local vectorization script..."
            python3 scripts/vectorize-repo-locally.py
            
            if [ $? -eq 0 ]; then
                success "Local vectorization completed"
            else
                error "Local vectorization failed"
                exit 1
            fi
        else
            error "Local vectorization script not found"
            exit 1
        fi
    fi
}

# Check vectorization results
check_results() {
    log "Checking vectorization results..."
    
    # Get vector storage pod
    local vector_pod=$(kubectl get pods -n trading-system -l app=postgres-vector-storage -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$vector_pod" ]; then
        log "Checking vector database contents..."
        
        # Query the vector database
        kubectl exec -n trading-system "$vector_pod" -- psql -c "
        SELECT 
            content_type,
            COUNT(*) as count,
            MAX(created_at) as last_indexed
        FROM vector_embeddings 
        GROUP BY content_type 
        ORDER BY count DESC;
        " 2>/dev/null || warning "Could not query vector database"
    else
        warning "Could not find vector storage pod to check results"
    fi
}

# Show next steps
show_next_steps() {
    log "Vectorization process completed!"
    echo
    echo "Next steps:"
    echo "1. Check vectorization results:"
    echo "   kubectl logs -n trading-system -l app=architecture-vectorizer --tail=50"
    echo
    echo "2. Test search functionality:"
    echo "   curl -X POST http://localhost:11006/api/vectors/search \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"query\": \"How does the trading system work?\", \"limit\": 5}'"
    echo
    echo "3. Access RAG chat services:"
    echo "   - Kubernetes RAG Chat: http://localhost:11006"
    echo "   - Unified Trading Dashboard: http://localhost:11000"
    echo "   - AI IDE Service: http://localhost:11050"
    echo
    echo "4. Monitor vectorization jobs:"
    echo "   kubectl get jobs -n trading-system | grep vectorizer"
    echo
    echo "5. Check documentation:"
    echo "   - Vector Database Indexing Guide: docs/VECTOR_DATABASE_INDEXING_GUIDE.md"
    echo "   - Data Flow Documentation: docs/VECTOR_DATABASE_DATA_FLOW.md"
}

# Main execution
main() {
    log "Starting Vector Database Indexing Process"
    echo "========================================"
    
    check_kubectl
    check_cluster
    check_vector_storage
    check_ollama_controller
    start_vectorization_job
    check_results
    show_next_steps
    
    success "Vectorization process completed successfully!"
}

# Run main function
main "$@"










