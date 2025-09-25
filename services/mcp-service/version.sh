#!/bin/bash
# Semantic Versioning Script for MCP Service
# Uses GitVersion to generate semantic versions for Docker builds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="localhost:32000"
SERVICE_NAME="mcp-service"
DOCKERFILE="Dockerfile"

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

# Function to check if GitVersion is available
check_gitversion() {
    if ! command -v gitversion &> /dev/null; then
        print_status "GitVersion not found locally, using Docker image..."
        # Use absolute path for Docker volume mount - go to git root
        REPO_PATH=$(git rev-parse --show-toplevel)
        GITVERSION_CMD="docker run --rm -v ${REPO_PATH}:/repo gittools/gitversion:5.12.0 /repo"
    else
        GITVERSION_CMD="gitversion"
    fi
}

# Function to get semantic version
get_semantic_version() {
    print_status "Generating semantic version..."
    
    # Get the semantic version
    SEMVER=$($GITVERSION_CMD /showvariable SemVer)
    
    if [ -z "$SEMVER" ]; then
        print_error "Failed to generate semantic version"
        exit 1
    fi
    
    print_success "Generated semantic version: $SEMVER"
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
    echo "Version Information:"
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

# Function to build Docker image with semantic versioning
build_docker_image() {
    local version=$1
    local build_args=""
    
    print_status "Building Docker image with version $version..."
    
    # Build the image with version tags
    local image_name="${REGISTRY}/${SERVICE_NAME}"
    
    # Build with full semantic version
    print_status "Building ${image_name}:${version}..."
    docker build -t "${image_name}:${version}" -f "$DOCKERFILE" .
    
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

# Function to push Docker images
push_docker_images() {
    local version=$1
    local image_name="${REGISTRY}/${SERVICE_NAME}"
    
    print_status "Pushing Docker images to registry..."
    
    # Push all tags
    docker push "${image_name}:${version}"
    docker push "${image_name}:${MAJOR}.${MINOR}"
    docker push "${image_name}:${MAJOR}"
    docker push "${image_name}:latest"
    
    print_success "All images pushed successfully to registry"
}

# Function to update Kubernetes deployment
update_k8s_deployment() {
    local version=$1
    local namespace="trading-system"
    
    print_status "Updating Kubernetes deployment to version $version..."
    
    # Update the deployment image
    kubectl set image deployment/${SERVICE_NAME} ${SERVICE_NAME}=${REGISTRY}/${SERVICE_NAME}:${version} -n ${namespace}
    
    # Wait for rollout to complete
    print_status "Waiting for deployment rollout to complete..."
    kubectl rollout status deployment/${SERVICE_NAME} -n ${namespace}
    
    print_success "Kubernetes deployment updated successfully"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --version-only    Only show version information"
    echo "  --build-only      Only build Docker image (don't push or deploy)"
    echo "  --no-push         Build and deploy but don't push to registry"
    echo "  --no-deploy       Build and push but don't deploy to Kubernetes"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full build, push, and deploy"
    echo "  $0 --version-only     # Show version information only"
    echo "  $0 --build-only       # Build Docker image only"
    echo "  $0 --no-push          # Build and deploy without pushing"
}

# Main function
main() {
    local version_only=false
    local build_only=false
    local no_push=false
    local no_deploy=false
    
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
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Please run this script from the git repository root."
        exit 1
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
    
    # Build Docker image
    build_docker_image "$SEMVER"
    
    if [ "$build_only" = true ]; then
        print_success "Docker image built. Exiting."
        exit 0
    fi
    
    # Push to registry (unless --no-push)
    if [ "$no_push" = false ]; then
        push_docker_images "$SEMVER"
    else
        print_warning "Skipping push to registry (--no-push specified)"
    fi
    
    # Update Kubernetes deployment (unless --no-deploy)
    if [ "$no_deploy" = false ]; then
        update_k8s_deployment "$SEMVER"
    else
        print_warning "Skipping Kubernetes deployment (--no-deploy specified)"
    fi
    
    print_success "Semantic versioning workflow completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Test the deployment: kubectl get pods -n trading-system | grep mcp"
    echo "2. Check service health: curl http://localhost:11120/health"
    echo "3. Test documentation endpoints: curl http://localhost:11120/api/mcp/docs/help"
}

# Run main function with all arguments
main "$@"
