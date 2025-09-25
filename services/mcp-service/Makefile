# MCP Service Makefile
# Provides semantic versioning and build automation

.PHONY: help version build push deploy clean test

# Default target
help:
	@echo "MCP Service Build System"
	@echo "========================"
	@echo ""
	@echo "Available targets:"
	@echo "  version        Show version information only"
	@echo "  build          Build Docker image with semantic versioning"
	@echo "  push           Build and push to registry"
	@echo "  deploy         Build, push, and deploy to Kubernetes"
	@echo "  clean          Clean up Docker images and containers"
	@echo "  test           Test the deployed service"
	@echo "  help           Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make version   # Show current version"
	@echo "  make build     # Build image only"
	@echo "  make deploy    # Full build, push, and deploy"

# Show version information
version:
	@./version.sh --version-only

# Build Docker image with semantic versioning
build:
	@./version.sh --build-only

# Build and push to registry
push:
	@./version.sh --no-deploy

# Full build, push, and deploy
deploy:
	@./version.sh

# Clean up Docker images and containers
clean:
	@echo "Cleaning up Docker images and containers..."
	@docker system prune -f
	@docker image prune -f
	@echo "Cleanup completed"

# Test the deployed service
test:
	@echo "Testing MCP Service..."
	@echo "1. Checking service health..."
	@curl -s http://localhost:11120/health | jq . || echo "Service not accessible"
	@echo ""
	@echo "2. Testing documentation endpoints..."
	@curl -s http://localhost:11120/api/mcp/docs/help | jq . || echo "Documentation endpoints not accessible"
	@echo ""
	@echo "3. Testing architecture endpoints..."
	@curl -s http://localhost:11120/api/mcp/architecture | jq . || echo "Architecture endpoints not accessible"
	@echo ""
	@echo "Testing completed"

# Development workflow
dev: build test

# Production deployment
prod: deploy test





