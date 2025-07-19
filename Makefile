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
include Makefile.rss

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
	@echo "  $(YELLOW)make k8s-port-forward-strategy$(NC) - Port forward strategy service"

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

# Colored Log Viewing
logs-colored: ## View colored logs from a pod
	@POD=$$(test -n "$(POD)" && echo "$(POD)" || (echo "$(RED)POD variable required. Usage: make logs-colored POD=pod-name$(NC)" && exit 1)); \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	echo "$(GREEN)🎨 Viewing colored logs for pod: $$POD$(NC)"; \
	kubectl logs -n $$NAMESPACE $$POD -f | python3 scripts/log_colorizer.py

logs-colored-tail: ## View colored logs with tail
	@POD=$$(test -n "$(POD)" && echo "$(POD)" || (echo "$(RED)POD variable required. Usage: make logs-colored-tail POD=pod-name$(NC)" && exit 1)); \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	LINES=$${LINES:-50}; \
	echo "$(GREEN)🎨 Viewing colored logs (last $$LINES lines) for pod: $$POD$(NC)"; \
	kubectl logs -n $$NAMESPACE $$POD --tail=$$LINES | python3 scripts/log_colorizer.py

# GRC Log Viewing (Generic Colouriser)
logs-grc: ## View logs with grc colorizer
	@POD=$$(test -n "$(POD)" && echo "$(POD)" || (echo "$(RED)POD variable required. Usage: make logs-grc POD=pod-name$(NC)" && exit 1)); \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	echo "$(GREEN)🎨 Viewing logs with grc for pod: $$POD$(NC)"; \
	kubectl logs -n $$NAMESPACE $$POD -f | grc -c ~/.grc/trading-logs.conf cat

logs-grc-tail: ## View logs with grc colorizer and tail
	@POD=$$(test -n "$(POD)" && echo "$(POD)" || (echo "$(RED)POD variable required. Usage: make logs-grc-tail POD=pod-name$(NC)" && exit 1)); \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	LINES=$${LINES:-50}; \
	echo "$(GREEN)🎨 Viewing logs with grc (last $$LINES lines) for pod: $$POD$(NC)"; \
	kubectl logs -n $$NAMESPACE $$POD --tail=$$LINES | grc -c ~/.grc/trading-logs.conf cat

logs-grc-file: ## View log file with grc colorizer
	@FILE=$$(test -n "$(FILE)" && echo "$(FILE)" || (echo "$(RED)FILE variable required. Usage: make logs-grc-file FILE=logs/trading_system.log$(NC)" && exit 1)); \
	echo "$(GREEN)🎨 Viewing log file with grc: $$FILE$(NC)"; \
	tail -f $$FILE | grc -c ~/.grc/trading-logs.conf cat

# Ollama GRC Log Viewing
logs-ollama-grc: ## View Ollama logs with grc colorizer
	@POD=$${POD:-ollama}; \
	NAMESPACE=$${NAMESPACE:-trading-system}; \
	echo "$(GREEN)🎨 Viewing Ollama logs with grc for pod: $$POD$(NC)"; \
	kubectl logs -n $$NAMESPACE $$POD -f | grc -c $$HOME/.grc/ollama-logs.conf cat

logs-ollama-host: ## View Ollama logs from host with grc colorizer
	@LOG_FILE=$${LOG_FILE:-/var/log/ollama.log}; \
	echo "$(GREEN)🎨 Viewing Ollama logs from host: $$LOG_FILE$(NC)"; \
	if [ -f "$$LOG_FILE" ]; then \
		grc -c $$HOME/.grc/ollama-logs.conf tail -f $$LOG_FILE; \
	else \
		echo "$(YELLOW)Log file not found: $$LOG_FILE$(NC)"; \
		echo "$(BLUE)Try: make logs-ollama-host LOG_FILE=/path/to/ollama.log$(NC)"; \
		echo "$(BLUE)Or: ollama serve 2>&1 | grc -c $$HOME/.grc/ollama-logs.conf cat$(NC)"; \
	fi

logs-ollama-live: ## View live Ollama logs from host process
	@echo "$(GREEN)🎨 Viewing live Ollama logs from host process$(NC)"; \
	echo "$(BLUE)Starting Ollama serve with grc colorization...$(NC)"; \
	ollama serve 2>&1 | grc -c $$HOME/.grc/ollama-logs.conf cat

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

# Performance Dashboard
dashboard-build: ## Build performance dashboard Docker image
	@echo "$(GREEN)🔨 Building Performance Dashboard...$(NC)"
	docker build -t localhost:5000/performance-dashboard:latest services/performance-dashboard/
	docker push localhost:5000/performance-dashboard:latest

dashboard-deploy: ## Deploy performance dashboard to Kubernetes
	@echo "$(GREEN)🚀 Deploying Performance Dashboard...$(NC)"
	kubectl apply -f k8s/performance-dashboard.yaml
	@echo "$(BLUE)Performance Dashboard deployed!$(NC)"

dashboard-port-forward: ## Port forward to performance dashboard
	@echo "$(GREEN)🔗 Port forwarding to Performance Dashboard...$(NC)"
	kubectl port-forward -n trading-system svc/performance-dashboard 8081:80

dashboard-logs: ## View performance dashboard logs
	@echo "$(GREEN)📋 Performance Dashboard logs:$(NC)"
	kubectl logs -n trading-system -l app=performance-dashboard -f

dashboard-status: ## Check performance dashboard status
	@echo "$(GREEN)📊 Performance Dashboard Status:$(NC)"
	kubectl get pods -n trading-system -l app=performance-dashboard
	@echo "$(BLUE)Access at: http://localhost:8081/dashboard$(NC)"

# ============================================================================
# RISK MANAGEMENT TARGETS
# ============================================================================

.PHONY: risk-deploy risk-deploy-all risk-start risk-stop risk-logs risk-status risk-config risk-test

# Deploy risk management system
risk-deploy:
	@echo "🛡️ Deploying Risk Management System..."
	kubectl apply -f k8s/risk-worker.yaml
	@echo "✅ Risk Management System deployed"

# Deploy all risk management components
risk-deploy-all: risk-deploy
	@echo "🔄 Waiting for risk worker to be ready..."
	kubectl wait --for=condition=ready pod -l app=risk-worker -n trading-system --timeout=300s
	@echo "✅ All risk management components deployed and ready"

# Start risk management system
risk-start:
	@echo "🚀 Starting Risk Management System..."
	kubectl scale deployment risk-worker -n trading-system --replicas=2
	@echo "✅ Risk Management System started"

# Stop risk management system
risk-stop:
	@echo "🛑 Stopping Risk Management System..."
	kubectl scale deployment risk-worker -n trading-system --replicas=0
	@echo "✅ Risk Management System stopped"

# View risk management logs
risk-logs:
	@echo "📋 Risk Management Logs:"
	kubectl logs -f deployment/risk-worker -n trading-system

# Check risk management status
risk-status:
	@echo "📊 Risk Management Status:"
	kubectl get pods -l app=risk-worker -n trading-system
	kubectl get services -l app=risk-worker -n trading-system
	kubectl get configmaps -l app=risk-worker -n trading-system

# Update risk configuration
risk-config:
	@echo "⚙️ Updating Risk Configuration..."
	kubectl apply -f k8s/risk-worker.yaml
	@echo "✅ Risk Configuration updated"

# Test risk management system
risk-test:
	@echo "🧪 Testing Risk Management System..."
	@echo "Testing risk worker health..."
	kubectl exec -n trading-system deployment/risk-worker -- curl -f http://localhost:8000/health || echo "❌ Risk worker health check failed"
	@echo "Testing risk configuration..."
	kubectl get configmap risk-config -n trading-system -o yaml
	@echo "✅ Risk Management System tests completed"

# Risk management monitoring
risk-monitor:
	@echo "📈 Risk Management Monitoring:"
	@echo "Pod Status:"
	kubectl get pods -l app=risk-worker -n trading-system -o wide
	@echo ""
	@echo "Resource Usage:"
	kubectl top pods -l app=risk-worker -n trading-system
	@echo ""
	@echo "Recent Logs:"
	kubectl logs --tail=50 deployment/risk-worker -n trading-system

# Risk management troubleshooting
risk-troubleshoot:
	@echo "🔧 Risk Management Troubleshooting:"
	@echo "1. Checking pod status..."
	kubectl get pods -l app=risk-worker -n trading-system
	@echo ""
	@echo "2. Checking events..."
	kubectl get events -n trading-system --sort-by='.lastTimestamp' | grep risk-worker
	@echo ""
	@echo "3. Checking configuration..."
	kubectl describe configmap risk-config -n trading-system
	@echo ""
	@echo "4. Checking service endpoints..."
	kubectl get endpoints risk-worker-service -n trading-system

# Risk management cleanup
risk-cleanup:
	@echo "🧹 Cleaning up Risk Management System..."
	kubectl delete -f k8s/risk-worker.yaml --ignore-not-found=true
	@echo "✅ Risk Management System cleaned up"

# Risk management backup
risk-backup:
	@echo "💾 Backing up Risk Management Configuration..."
	kubectl get configmap risk-config -n trading-system -o yaml > backup/risk-config-$(shell date +%Y%m%d_%H%M%S).yaml
	@echo "✅ Risk Management Configuration backed up"

# Risk management restore
risk-restore:
	@echo "🔄 Restoring Risk Management Configuration..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify BACKUP_FILE=<filename>"; \
		exit 1; \
	fi
	kubectl apply -f backup/$(BACKUP_FILE)
	@echo "✅ Risk Management Configuration restored"

# Risk management scaling
risk-scale:
	@echo "📏 Scaling Risk Management System..."
	@if [ -z "$(REPLICAS)" ]; then \
		echo "❌ Please specify REPLICAS=<number>"; \
		exit 1; \
	fi
	kubectl scale deployment risk-worker -n trading-system --replicas=$(REPLICAS)
	@echo "✅ Risk Management System scaled to $(REPLICAS) replicas"

# Risk management performance test
risk-perf-test:
	@echo "⚡ Risk Management Performance Test:"
	@echo "1. Testing risk check throughput..."
	@echo "2. Testing portfolio risk assessment..."
	@echo "3. Testing stress test scenarios..."
	@echo "4. Testing alert processing..."
	@echo "✅ Risk Management Performance Test completed"

# Risk management security audit
risk-security-audit:
	@echo "🔒 Risk Management Security Audit:"
	@echo "1. Checking RBAC permissions..."
	kubectl auth can-i get pods --as=system:serviceaccount:trading-system:risk-worker-sa -n trading-system
	@echo "2. Checking network policies..."
	kubectl get networkpolicy risk-worker-network-policy -n trading-system
	@echo "3. Checking secret access..."
	kubectl auth can-i get secrets --as=system:serviceaccount:trading-system:risk-worker-sa -n trading-system
	@echo "✅ Risk Management Security Audit completed"

# .PHONY declarations
.PHONY: help setup deploy backtest status clean dev-workflow monitor monitor-quick monitor-demo monitor-pod api-backtest api-backtest-demo 