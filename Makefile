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

# Space Station Monitor
monitor: ## Start Space Trading Station Monitor
	@echo "$(GREEN)🚀 Starting Space Trading Station Monitor...$(NC)"
	@echo "$(BLUE)This is ORION, Mission Control. All systems are go!$(NC)"
	python space_station_monitor.py

monitor-quick: ## Start Space Station Monitor (Quick Mode)
	@echo "$(GREEN)🚀 Starting Space Trading Station Monitor (Quick Mode)...$(NC)"
	python -c "import asyncio; from src.utils.space_station_monitor import SpaceStationMonitor; asyncio.run(SpaceStationMonitor(refresh_interval=1).start_monitoring())"

monitor-demo: ## Start Space Station Monitor with Demo Data
	@echo "$(GREEN)🚀 Starting Space Trading Station Monitor Demo...$(NC)"
	@echo "$(BLUE)This will show simulated trading data in real-time.$(NC)"
	python demo_monitor.py

monitor-demo-api: ## Run the monitor with API integration demo
	@echo "$(GREEN)🚀 Starting Monitor with API Integration Demo...$(NC)"
	@echo "$(BLUE)This will connect to the Kubernetes API for real data.$(NC)"
	python demo_monitor_with_api.py

# Kubernetes Pod Monitoring
monitor-pod: ## Monitor a Kubernetes pod with periodic status and log checks
	@POD=$$(test -n "$(POD)" && echo "$(POD)" || (echo "$(RED)POD variable required. Usage: make monitor-pod POD=pod-name$(NC)" && exit 1)); \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	INTERVAL=$${INTERVAL:-60}; \
	LOG_LINES=$${LOG_LINES:-5}; \
	echo "$(GREEN)🔍 Monitoring pod: $$POD in namespace: $$NAMESPACE$(NC)"; \
	echo "$(BLUE)Interval: $$INTERVAL seconds, Log lines: $$LOG_LINES$(NC)"; \
	echo "$(YELLOW)Press Ctrl+C to stop monitoring$(NC)"; \
	echo ""; \
	while true; do \
		echo "=== $$(date) ==="; \
		kubectl get pods -n $$NAMESPACE | grep $$POD || echo "$(RED)Pod not found$(NC)"; \
		echo "--- Recent logs ---"; \
		kubectl logs -n $$NAMESPACE $$(kubectl get pods -n $$NAMESPACE | grep $$POD | awk '{print $$1}' | head -1) --tail=$$LOG_LINES 2>/dev/null || echo "$(RED)No logs available$(NC)"; \
		echo "=================="; \
		sleep $$INTERVAL; \
	done

# Python Virtual Environment
venv-create: ## Create Python virtual environment in .venv
	python3 -m venv .venv

venv-activate: ## Activate the Python virtual environment
	@echo "Run: source .venv/bin/activate"

venv-install: venv-create ## Install Python dependencies in venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install loguru psutil

venv-monitor: venv-install ## Run Space Station Monitor in venv
	.venv/bin/python space_station_monitor.py

venv-monitor-demo: venv-install ## Run Space Station Monitor Demo in venv
	.venv/bin/python demo_monitor.py

# API Services
api-backtest: venv-install ## Start Backtest Results API on port 10001
	@echo "$(GREEN)🚀 Starting Backtest Results API on port 10001...$(NC)"
	@echo "$(BLUE)API will be available at: http://localhost:10001$(NC)"
	.venv/bin/python -m uvicorn src.api.backtest_api:app --host 0.0.0.0 --port 10001 --reload

api-backtest-demo: venv-install ## Demo the backtest API client
	@echo "$(GREEN)🚀 Running Backtest API Demo...$(NC)"
	.venv/bin/python demo_backtest_api.py

# .PHONY declarations
.PHONY: help setup deploy backtest status clean dev-workflow monitor monitor-quick monitor-demo monitor-pod api-backtest api-backtest-demo 