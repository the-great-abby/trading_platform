#!/bin/bash
# Centralized Semantic Versioning Script for Trading System
# Uses GitVersion to generate semantic versions for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="localhost:32000"
NAMESPACE="trading-system"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_service() {
    echo -e "${PURPLE}[SERVICE]${NC} $1"
}

# Function to check if GitVersion is available
check_gitversion() {
    if ! command -v gitversion &> /dev/null; then
        print_status "GitVersion not found locally, using Docker image..."
        # Use absolute path for Docker volume mount - go to git root
        REPO_PATH=$(pwd)
        GITVERSION_CMD="docker run --rm -v ${REPO_PATH}:/repo gittools/gitversion:5.12.0 /repo"
    else
        GITVERSION_CMD="gitversion"
    fi
}

# Function to get semantic version
get_semantic_version() {
    # Get the semantic version (suppress output)
    SEMVER=$($GITVERSION_CMD /showvariable SemVer 2>/dev/null)
    
    if [ -z "$SEMVER" ]; then
        print_error "Failed to generate semantic version"
        exit 1
    fi
    
    echo "$SEMVER"
}

# Function to get version info
get_version_info() {
    print_status "Getting version information..."
    
    # Get various version components
    FULL_SEMVER=$($GITVERSION_CMD /showvariable FullSemVer)
    MAJOR=$($GITVERSION_CMD /showvariable Major)
    MINOR=$($GITVERSION_CMD /showvariable Minor)
    PATCH=$($GITVERSION_CMD /showvariable Patch)
    PRE_RELEASE_TAG=$($GITVERSION_CMD /showvariable PreReleaseTag)
    PRE_RELEASE_NUMBER=$($GITVERSION_CMD /showvariable PreReleaseNumber)
    COMMITS_SINCE_VERSION_SOURCE=$($GITVERSION_CMD /showvariable CommitsSinceVersionSource)
    SHA=$($GITVERSION_CMD /showvariable Sha)
    
    # Display version information
    echo "=========================================="
    echo "Trading System Version Information"
    echo "=========================================="
    echo "Full SemVer: $FULL_SEMVER"
    echo "Major: $MAJOR"
    echo "Minor: $MINOR"
    echo "Patch: $PATCH"
    echo "Pre-release Tag: $PRE_RELEASE_TAG"
    echo "Pre-release Number: $PRE_RELEASE_NUMBER"
    echo "Commits Since Version Source: $COMMITS_SINCE_VERSION_SOURCE"
    echo "SHA: $SHA"
    echo "=========================================="
}

# Function to build Docker image for a specific service
build_service_image() {
    local service_name=$1
    local service_path=$2
    local version=$3
    local dockerfile=${4:-"Dockerfile"}
    
    print_service "Building $service_name with version $version..."
    
    if [ ! -d "$service_path" ]; then
        print_error "Service directory not found: $service_path"
        return 1
    fi
    
    # Build the image with version tags
    local image_name="${REGISTRY}/${service_name}"
    
    # Build with full semantic version
    print_status "Building ${image_name}:${version}..."
    
    # Check if the Dockerfile expects to be built from project root
    if grep -q "COPY src /app/src" "${service_path}/${dockerfile}" 2>/dev/null; then
        # Build from project root for services that need shared code
        docker build -t "${image_name}:${version}" -f "${service_path}/${dockerfile}" .
    else
        # Build from service directory for self-contained services
        docker build -t "${image_name}:${version}" -f "${service_path}/${dockerfile}" "$service_path"
    fi
    
    # Create additional tags
    local major_minor="${MAJOR}.${MINOR}"
    local major_only="${MAJOR}"
    
    print_status "Creating additional tags..."
    docker tag "${image_name}:${version}" "${image_name}:${major_minor}"
    docker tag "${image_name}:${version}" "${image_name}:${major_only}"
    docker tag "${image_name}:${version}" "${image_name}:latest"
    
    print_success "Docker image built successfully with tags:"
    echo "  - ${image_name}:${version}"
    echo "  - ${image_name}:${major_minor}"
    echo "  - ${image_name}:${major_only}"
    echo "  - ${image_name}:latest"
}

# Function to push Docker images for a service
push_service_images() {
    local service_name=$1
    local version=$2
    local image_name="${REGISTRY}/${service_name}"
    
    print_service "Pushing $service_name images to registry..."
    
    # Push all tags
    docker push "${image_name}:${version}"
    docker push "${image_name}:${MAJOR}.${MINOR}"
    docker push "${image_name}:${MAJOR}"
    docker push "${image_name}:latest"
    
    print_success "All images pushed successfully to registry"
}

# Function to update Kubernetes deployment
update_k8s_deployment() {
    local service_name=$1
    local version=$2
    
    print_service "Updating Kubernetes deployment for $service_name to version $version..."
    
    # Check if deployment exists
    if ! kubectl get deployment "$service_name" -n "$NAMESPACE" > /dev/null 2>&1; then
        print_warning "Deployment $service_name not found in namespace $NAMESPACE, skipping..."
        return 0
    fi
    
    # Update the deployment image
    kubectl set image deployment/${service_name} ${service_name}=${REGISTRY}/${service_name}:${version} -n ${NAMESPACE}
    
    # Wait for rollout to complete
    print_status "Waiting for deployment rollout to complete..."
    kubectl rollout status deployment/${service_name} -n ${NAMESPACE}
    
    print_success "Kubernetes deployment updated successfully"
}

# Function to build all services
build_all_services() {
    local version=$1
    local services=(
        "mcp-service:services/mcp-service"
        "trading-service:services/trading-service"
        "market-data-service:services/market-data-service"
        "ai-analysis-service:services/ai-analysis-service"
        "backtest-api:services/backtest-api"
        "strategy-service:services/strategy-service"
        "live-trading-service:services/live-trading-service"
        "elliott-wave-service:services/elliott-wave-service"
        "rss-feed-service:services/rss-feed-service"
        "analytics-service:services/analytics-service"
        "unified-analytics-dashboard:services/unified-analytics-dashboard"
        "unified-trading-dashboard:services/unified-trading-dashboard"
        "unified-news-dashboard:services/unified-news-dashboard"
    )
    
    print_status "Building all services with version $version..."
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"
        
        if [ -d "$service_path" ]; then
            build_service_image "$service_name" "$service_path" "$version"
        else
            print_warning "Service directory not found: $service_path, skipping $service_name"
        fi
    done
}

# Function to push all services
push_all_services() {
    local version=$1
    local services=(
        "mcp-service"
        "trading-service"
        "market-data-service"
        "ai-analysis-service"
        "backtest-api"
        "strategy-service"
        "live-trading-service"
        "elliott-wave-service"
        "rss-feed-service"
        "analytics-service"
        "unified-analytics-dashboard"
        "unified-trading-dashboard"
        "unified-news-dashboard"
    )
    
    print_status "Pushing all services with version $version..."
    
    for service_name in "${services[@]}"; do
        if docker images | grep -q "${REGISTRY}/${service_name}"; then
            push_service_images "$service_name" "$version"
        else
            print_warning "Image not found for $service_name, skipping push"
        fi
    done
}

# Function to deploy all services
deploy_all_services() {
    local version=$1
    local services=(
        "mcp-service"
        "trading-service"
        "market-data-service"
        "ai-analysis-service"
        "backtest-api"
        "strategy-service"
        "live-trading-service"
        "elliott-wave-service"
        "rss-feed-service"
        "analytics-service"
        "unified-analytics-dashboard"
        "unified-trading-dashboard"
        "unified-news-dashboard"
    )
    
    print_status "Deploying all services with version $version..."
    
    for service_name in "${services[@]}"; do
        update_k8s_deployment "$service_name" "$version"
    done
}

# Function to clean up old Docker images and tags
clean_old_versions() {
    local service_name=$1
    local keep_versions=${2:-5}  # Keep last 5 versions by default
    
    print_service "Cleaning up old versions for $service_name (keeping last $keep_versions)..."
    
    local image_name="${REGISTRY}/${service_name}"
    
    # Get all tags for the service, sorted by creation date (newest first)
    local all_tags=$(docker images --format "{{.Tag}}" "${image_name}" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' | sort -V -r)
    
    if [ -z "$all_tags" ]; then
        print_warning "No versioned tags found for $service_name"
        return 0
    fi
    
    # Count total tags
    local total_tags=$(echo "$all_tags" | wc -l)
    print_status "Found $total_tags versioned tags for $service_name"
    
    if [ "$total_tags" -le "$keep_versions" ]; then
        print_status "Only $total_tags tags found, keeping all (limit: $keep_versions)"
        return 0
    fi
    
    # Calculate how many to remove
    local tags_to_remove=$((total_tags - keep_versions))
    print_status "Removing $tags_to_remove old tags (keeping $keep_versions newest)"
    
    # Get tags to remove (skip the first $keep_versions)
    local tags_to_delete=$(echo "$all_tags" | tail -n +$((keep_versions + 1)))
    
    # Remove old tags
    local removed_count=0
    while IFS= read -r tag; do
        if [ -n "$tag" ]; then
            print_status "Removing ${image_name}:${tag}..."
            if docker rmi "${image_name}:${tag}" > /dev/null 2>&1; then
                ((removed_count++))
                print_success "Removed ${image_name}:${tag}"
            else
                print_warning "Failed to remove ${image_name}:${tag} (may be in use)"
            fi
        fi
    done <<< "$tags_to_delete"
    
    print_success "Cleanup completed: removed $removed_count old tags for $service_name"
}

# Function to clean up all services
clean_all_services() {
    local keep_versions=${1:-5}
    
    print_status "Cleaning up old versions for all services (keeping last $keep_versions)..."
    
    local services=(
        "mcp-service"
        "trading-service"
        "market-data-service"
        "ai-analysis-service"
        "backtest-api"
        "strategy-service"
        "live-trading-service"
        "elliott-wave-service"
        "rss-feed-service"
        "analytics-service"
        "unified-analytics-dashboard"
        "unified-trading-dashboard"
        "unified-news-dashboard"
    )
    
    for service_name in "${services[@]}"; do
        if docker images | grep -q "${REGISTRY}/${service_name}"; then
            clean_old_versions "$service_name" "$keep_versions"
        else
            print_warning "No images found for $service_name, skipping..."
        fi
    done
}

# Function to clean up dangling images and unused containers
clean_system() {
    print_status "Cleaning up Docker system (dangling images, unused containers)..."
    
    # Remove dangling images
    local dangling_images=$(docker images -f "dangling=true" -q)
    if [ -n "$dangling_images" ]; then
        print_status "Removing dangling images..."
        docker rmi $dangling_images 2>/dev/null || print_warning "Some dangling images could not be removed (may be in use)"
    fi
    
    # Remove unused containers
    local unused_containers=$(docker ps -a -f "status=exited" -q)
    if [ -n "$unused_containers" ]; then
        print_status "Removing unused containers..."
        docker rm $unused_containers 2>/dev/null || print_warning "Some containers could not be removed (may be in use)"
    fi
    
    # Clean up build cache
    print_status "Cleaning up build cache..."
    docker builder prune -f
    
    print_success "System cleanup completed"
}

# Function to show cleanup help
show_cleanup_help() {
    echo "Docker Image Cleanup Options"
    echo "============================"
    echo ""
    echo "Usage: $0 --clean [OPTIONS] [SERVICE]"
    echo ""
    echo "Options:"
    echo "  --keep-versions N    Keep last N versions (default: 5)"
    echo "  --system-only        Only clean system (dangling images, containers)"
    echo "  --all-services       Clean all services"
    echo "  --dry-run            Show what would be removed without actually removing"
    echo ""
    echo "Examples:"
    echo "  $0 --clean mcp-service                    # Clean MCP service (keep last 5)"
    echo "  $0 --clean --keep-versions 3 mcp-service  # Clean MCP service (keep last 3)"
    echo "  $0 --clean --all-services                 # Clean all services"
    echo "  $0 --clean --system-only                  # Clean system only"
    echo "  $0 --clean --dry-run mcp-service          # Show what would be removed"
}

# Function to show usage
show_usage() {
    echo "Trading System Semantic Versioning"
    echo "=================================="
    echo ""
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "Options:"
    echo "  --version-only    Only show version information"
    echo "  --build-only      Only build Docker images (don't push or deploy)"
    echo "  --no-push         Build and deploy but don't push to registry"
    echo "  --no-deploy       Build and push but don't deploy to Kubernetes"
    echo "  --all-services    Build/push/deploy all services"
    echo "  --clean           Clean up old Docker images and tags"
    echo "  --help            Show this help message"
    echo ""
    echo "Services:"
    echo "  mcp-service                    MCP Service"
    echo "  trading-service                Trading Service"
    echo "  market-data-service            Market Data Service"
    echo "  ai-analysis-service            AI Analysis Service"
    echo "  backtest-api                   Backtest API"
    echo "  strategy-service               Strategy Service"
    echo "  live-trading-service           Live Trading Service"
    echo "  elliott-wave-service           Elliott Wave Service"
    echo "  rss-feed-service               RSS Feed Service"
    echo "  analytics-service              Analytics Service"
    echo "  unified-analytics-dashboard    Unified Analytics Dashboard"
    echo "  unified-trading-dashboard      Unified Trading Dashboard"
    echo "  unified-news-dashboard         Unified News Dashboard"
    echo ""
    echo "Examples:"
    echo "  $0 --version-only              # Show version information only"
    echo "  $0 --build-only mcp-service    # Build MCP service only"
    echo "  $0 --all-services              # Build, push, and deploy all services"
    echo "  $0 mcp-service                 # Full build, push, and deploy for MCP service"
    echo "  $0 --clean mcp-service         # Clean up old MCP service versions"
    echo "  $0 --clean --all-services      # Clean up all services"
}

# Function to get service path
get_service_path() {
    local service_name=$1
    case $service_name in
        "mcp-service")
            echo "services/mcp-service"
            ;;
        "trading-service")
            echo "services/trading-service"
            ;;
        "market-data-service")
            echo "services/market-data-service"
            ;;
        "ai-analysis-service")
            echo "services/ai-analysis-service"
            ;;
        "backtest-api")
            echo "services/backtest-api"
            ;;
        "strategy-service")
            echo "services/strategy-service"
            ;;
        "unified-analytics-dashboard")
            echo "services/unified-analytics-dashboard"
            ;;
        "unified-trading-dashboard")
            echo "services/unified-trading-dashboard"
            ;;
        "unified-news-dashboard")
            echo "services/unified-news-dashboard"
            ;;
        "live-trading-service")
            echo "services/live-trading-service"
            ;;
        "elliott-wave-service")
            echo "services/elliott-wave-service"
            ;;
        "rss-feed-service")
            echo "services/rss-feed-service"
            ;;
        "analytics-service")
            echo "services/analytics-service"
            ;;
        *)
            print_error "Unknown service: $service_name"
            return 1
            ;;
    esac
}

# Main function
main() {
    local version_only=false
    local build_only=false
    local no_push=false
    local no_deploy=false
    local all_services=false
    local clean_mode=false
    local system_only=false
    local keep_versions=5
    local dry_run=false
    local service_name=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version-only)
                version_only=true
                shift
                ;;
            --build-only)
                build_only=true
                shift
                ;;
            --no-push)
                no_push=true
                shift
                ;;
            --no-deploy)
                no_deploy=true
                shift
                ;;
            --all-services)
                all_services=true
                shift
                ;;
            --clean)
                clean_mode=true
                shift
                ;;
            --system-only)
                system_only=true
                shift
                ;;
            --keep-versions)
                keep_versions="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$service_name" ]; then
                    service_name="$1"
                else
                    print_error "Multiple services specified. Use --all-services for multiple services."
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Please run this script from the git repository root."
        exit 1
    fi
    
    # Handle cleanup mode
    if [ "$clean_mode" = true ]; then
        if [ "$system_only" = true ]; then
            clean_system
            print_success "System cleanup completed. Exiting."
            exit 0
        elif [ "$all_services" = true ]; then
            clean_all_services "$keep_versions"
            print_success "All services cleanup completed. Exiting."
            exit 0
        elif [ -n "$service_name" ]; then
            clean_old_versions "$service_name" "$keep_versions"
            print_success "Service cleanup completed. Exiting."
            exit 0
        else
            print_error "Cleanup mode requires either --all-services or a specific service name"
            show_cleanup_help
            exit 1
        fi
    fi
    
    # Check GitVersion
    check_gitversion
    
    # Get version information
    get_version_info
    
    if [ "$version_only" = true ]; then
        print_success "Version information displayed. Exiting."
        exit 0
    fi
    
    # Get semantic version
    SEMVER=$(get_semantic_version)
    
    # Handle all services
    if [ "$all_services" = true ]; then
        # Build all services
        build_all_services "$SEMVER"
        
        if [ "$build_only" = true ]; then
            print_success "All services built. Exiting."
            exit 0
        fi
        
        # Push all services (unless --no-push)
        if [ "$no_push" = false ]; then
            push_all_services "$SEMVER"
        else
            print_warning "Skipping push to registry (--no-push specified)"
        fi
        
        # Deploy all services (unless --no-deploy)
        if [ "$no_deploy" = false ]; then
            deploy_all_services "$SEMVER"
        else
            print_warning "Skipping Kubernetes deployment (--no-deploy specified)"
        fi
        
        print_success "All services processed successfully!"
        exit 0
    fi
    
    # Handle single service
    if [ -z "$service_name" ]; then
        print_error "No service specified. Use --help for usage information."
        exit 1
    fi
    
    # Get service path
    service_path=$(get_service_path "$service_name")
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Build Docker image
    build_service_image "$service_name" "$service_path" "$SEMVER"
    
    if [ "$build_only" = true ]; then
        print_success "Docker image built. Exiting."
        exit 0
    fi
    
    # Push to registry (unless --no-push)
    if [ "$no_push" = false ]; then
        push_service_images "$service_name" "$SEMVER"
    else
        print_warning "Skipping push to registry (--no-push specified)"
    fi
    
    # Update Kubernetes deployment (unless --no-deploy)
    if [ "$no_deploy" = false ]; then
        update_k8s_deployment "$service_name" "$SEMVER"
    else
        print_warning "Skipping Kubernetes deployment (--no-deploy specified)"
    fi
    
    print_success "Semantic versioning workflow completed successfully for $service_name!"
    echo ""
    echo "Next steps:"
    echo "1. Test the deployment: kubectl get pods -n $NAMESPACE | grep $service_name"
    echo "2. Check service health: kubectl get svc -n $NAMESPACE | grep $service_name"
    echo "3. View logs: kubectl logs deployment/$service_name -n $NAMESPACE"
}

# Run main function with all arguments
main "$@"
