# Master Makefile - Trading Bot System
# This file includes all modular Makefiles and provides a unified interface

# Include all modular Makefiles
include Makefile.core
include Makefile.docker
include Makefile.kubernetes
include Makefile.database
include Makefile.backtest
include Makefile.services
include Makefile.quick-wins
include Makefile.registry

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Unified Help System
help: ## Show comprehensive help for all categories
	@echo "$(BLUE)🏗️  TRADING BOT SYSTEM - MASTER MAKEFILE$(NC)"
	@echo "$(BLUE)============================================$(NC)"
	@echo ""
	@echo "$(GREEN)📋 Available Categories:$(NC)"
	@echo "  $(YELLOW)core-*$(NC)      - Core development operations (install, test, lint, etc.)"
	@echo "  $(YELLOW)docker-*$(NC)    - Docker container management"
	@echo "  $(YELLOW)k8s-*$(NC)       - Kubernetes deployment and management"
	@echo "  $(YELLOW)db-*$(NC)        - Database operations (local and Kubernetes)"
	@echo "  $(YELLOW)backend-*$(NC)   - Backtesting operations"
	@echo "  $(YELLOW)service-*$(NC)   - Service management and execution"
	@echo "  $(YELLOW)registry-*$(NC)  - Docker registry operations"
	@echo "  $(YELLOW)quick-*$(NC)     - Quick wins operations"

	@echo ""
	@echo "$(GREEN)🚀 Quick Start Commands:$(NC)"
	@echo "  $(YELLOW)make core-setup$(NC)           - Setup development environment"
	@echo "  $(YELLOW)make docker-build$(NC)         - Build Docker images"
	@echo "  $(YELLOW)make k8s-deploy$(NC)           - Deploy to Kubernetes"
	@echo "  $(YELLOW)make backend-kube-backtest$(NC) - Run backtest in Kubernetes"

	@echo ""
	@echo "$(GREEN)📖 Detailed Help by Category:$(NC)"
	@echo "  $(YELLOW)make core-help$(NC)            - Core operations"
	@echo "  $(YELLOW)make docker-help$(NC)          - Docker operations"
	@echo "  $(YELLOW)make k8s-help$(NC)             - Kubernetes operations"
	@echo "  $(YELLOW)make db-help$(NC)              - Database operations"
	@echo "  $(YELLOW)make backend-help$(NC)         - Backtesting operations"
	@echo "  $(YELLOW)make service-help$(NC)         - Service operations"
	@echo "  $(YELLOW)make registry-help$(NC)        - Registry operations"
	@echo "  $(YELLOW)make quick-help$(NC)           - Quick wins operations"

# Quick Start Targets
setup: ## Complete system setup
	@echo "$(GREEN)🚀 Setting up complete trading bot system...$(NC)"
	make core-setup
	make docker-build
	@echo "$(GREEN)✅ Setup complete!$(NC)"

deploy: ## Deploy to Kubernetes
	@echo "$(GREEN)🚀 Deploying to Kubernetes...$(NC)"
	make k8s-deploy
	@echo "$(GREEN)✅ Deployment complete!$(NC)"

backtest: ## Run comprehensive backtest
	@echo "$(GREEN)📊 Running comprehensive backtest...$(NC)"
	make backend-kube-backtest
	@echo "$(GREEN)✅ Backtest complete!$(NC)"

# Status Targets
status: ## Check system status
	@echo "$(GREEN)📊 Checking system status...$(NC)"
	@echo "$(BLUE)Docker Status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
	@echo ""
	@echo "$(BLUE)Kubernetes Status:$(NC)"
	@kubectl -n trading-system get pods 2>/dev/null || echo "$(RED)Kubernetes not available$(NC)"

# Cleanup Targets
clean: ## Clean up all resources
	@echo "$(GREEN)🧹 Cleaning up all resources...$(NC)"
	make core-clean
	make docker-clean
	make k8s-clean
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

# Development Workflow
dev-workflow: ## Complete development workflow
	@echo "$(GREEN)🔄 Running complete development workflow...$(NC)"
	make core-setup
	make docker-build
	make k8s-deploy
	make backend-kube-backtest
	@echo "$(GREEN)✅ Development workflow complete!$(NC)"

# .PHONY declarations
.PHONY: help setup deploy backtest status clean dev-workflow 