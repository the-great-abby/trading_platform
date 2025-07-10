# Trading System Makefile
# CQRS-based algorithmic trading system
# SECURITY: All Python scripts and executables run inside Docker containers

.PHONY: help install test lint format clean build deploy docker-build docker-up docker-down docker-logs docker-shell k8s-deploy k8s-delete k8s-logs setup-dev setup-prod docker-dev docker-test docker-stop docker-clean python-run python-install python-test python-run python-install python-test

# Variables
PROJECT_NAME = trading-system
DOCKER_COMPOSE = docker-compose
KUBECTL = kubectl
NAMESPACE = trading-system

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Trading System - CQRS & Microservices (Containerized)${NC}"
	@echo "$(BLUE)==================================================${NC}"
	@echo ""
	@echo "$(GREEN)Available commands:${NC}"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Quick Start:${NC}"
	@echo "  make setup-dev    # Set up development environment"
	@echo "  make docker-up    # Start all services with Docker Compose"
	@echo "  make test         # Run tests in Docker"
	@echo "  make deploy       # Deploy to production"
	@echo ""
	@echo "$(GREEN)Container Python Commands:${NC}"
	@echo "  make python-run SCRIPT=src/main.py  # Run Python script in container"
	@echo "  make python-install PACKAGE=yfinance # Install package in container"
	@echo "  make python-test                     # Run Python tests in container"
	@echo ""
	@echo "$(GREEN)Registry Operations:${NC}"
	@echo "  make registry-setup                  # Complete registry setup"
	@echo "  make registry-check                  # Check registry accessibility"
	@echo "  make k8s-deploy-registry             # Deploy with registry images"

# Registry Operations (delegate to Makefile.registry)
registry-check: ## Check local registry accessibility
	@make -f Makefile.registry registry-check

registry-setup: ## Complete registry setup (build, push, config, update-k8s)
	@make -f Makefile.registry registry-setup

registry-build: ## Build all images for local registry
	@make -f Makefile.registry registry-build

registry-push: ## Push all images to local registry
	@make -f Makefile.registry registry-push

registry-build-push: ## Build and push all images to local registry
	@make -f Makefile.registry registry-build-push

k8s-deploy-registry: ## Deploy to Kubernetes using registry images
	@make -f Makefile.registry k8s-deploy-registry









# Development Setup
setup-dev: ## Set up development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp config.env.example .env; \
		echo "$(YELLOW)Created .env file. Please edit it with your API credentials.$(NC)"; \
	fi
	@mkdir -p logs data monitoring
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env file with your API credentials"
	@echo "  2. Run: make docker-up"
	@echo "  3. Run: make test"

setup-prod: ## Set up production environment
	@echo "$(GREEN)Setting up production environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp config.env.example .env; \
		echo "$(YELLOW)Created .env file. Please edit it with production credentials.$(NC)"; \
	fi
	@mkdir -p logs data monitoring
	@echo "$(GREEN)Production environment ready!$(NC)"

# Installation (Docker-based)
install: ## Install Python dependencies in Docker
	@echo "$(GREEN)Installing Python dependencies in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli pip install -r requirements.txt

install-dev: ## Install development dependencies in Docker
	@echo "$(GREEN)Installing development dependencies in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli pip install -r requirements-dev.txt

# Testing (Docker-based)
test: ## Run all tests in Docker
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit: ## Run unit tests only in Docker
	@echo "$(GREEN)Running unit tests in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only in Docker
	@echo "$(GREEN)Running integration tests in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests in Docker
	@echo "$(GREEN)Running end-to-end tests in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/e2e/ -v

test-coverage: ## Run tests with coverage report in Docker
	@echo "$(GREEN)Running tests with coverage in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

# Code Quality (Docker-based)
lint: ## Run linting checks in Docker
	@echo "$(GREEN)Running linting checks in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m flake8 src/ tests/
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m black --check src/ tests/
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m isort --check-only src/ tests/

format: ## Format code with black and isort in Docker
	@echo "$(GREEN)Formatting code in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m black src/ tests/
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m isort src/ tests/

type-check: ## Run type checking in Docker
	@echo "$(GREEN)Running type checks in Docker...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m mypy src/

# Docker Operations
docker-build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml build

docker-build-no-cache: ## Build Docker images without cache
	@echo "$(GREEN)Building Docker images without cache...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml build --no-cache

# Backtest Database and Docker Targets
docker-build-backtest: ## Rebuild Docker image for backtest with updated code
	@echo "$(GREEN)Rebuilding Docker image for backtest with updated code...$(NC)"
	@echo "$(YELLOW)This will rebuild the trading-bot image with the latest backtest code...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml build --no-cache trading-cli
	@echo "$(GREEN)Docker image rebuilt successfully!$(NC)"
	@echo "$(YELLOW)Next: Run 'make k8s-deploy' to deploy with the new image$(NC)"

db-create-backtest-tables: ## Create backtest database tables
	@echo "$(GREEN)Creating backtest database tables...$(NC)"
	@echo "$(YELLOW)This will create the required tables: backtest_runs, backtest_trades, backtest_equity_curves$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.append('/workspace/src'); from services.database.backtest_results_service import BacktestResultsService; service = BacktestResultsService(); print('✅ Backtest database tables created successfully!')"
	@echo "$(GREEN)Database tables created!$(NC)"

db-check-backtest-tables: ## Check if backtest database tables exist
	@echo "$(GREEN)Checking backtest database tables...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.append('/workspace/src'); from sqlalchemy import create_engine, text; engine = create_engine('postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot'); conn = engine.connect(); result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\' AND table_name IN (\\'backtest_runs\\', \\'backtest_trades\\', \\'backtest_equity_curves\\') ORDER BY table_name')); tables = [row[0] for row in result]; print('📊 Found tables:', tables); print('✅ All backtest tables exist!' if len(tables) == 3 else '❌ Missing tables. Run: make db-create-backtest-tables'); conn.close()"

backtest-setup: ## Complete backtest setup (rebuild image + create tables + deploy)
	@echo "$(GREEN)Setting up complete backtest environment...$(NC)"
	@echo "$(YELLOW)Step 1: Rebuilding Docker image...$(NC)"
	$(MAKE) docker-build-backtest
	@echo "$(YELLOW)Step 2: Creating database tables...$(NC)"
	$(MAKE) db-create-backtest-tables
	@echo "$(YELLOW)Step 3: Deploying to Kubernetes...$(NC)"
	$(MAKE) k8s-deploy
	@echo "$(GREEN)✅ Backtest setup complete!$(NC)"
	@echo "$(YELLOW)You can now run: make k8s-backtest SCRIPT=run_backtest_with_real_data.py$(NC)"

backtest-run-db-only: ## Run backtest with database-only mode (complete workflow)
	@echo "$(GREEN)Running backtest with database-only mode...$(NC)"
	@echo "$(YELLOW)This will run the comprehensive backtest using only database data$(NC)"
	$(KUBECTL) delete job backtest-job -n $(NAMESPACE) --ignore-not-found=true
	$(KUBECTL) apply -f k8s/backtest-job.yaml -n $(NAMESPACE)
	@echo "$(GREEN)Backtest job started!$(NC)"
	@echo "$(YELLOW)Monitor with: kubectl logs -f job/backtest-job -n $(NAMESPACE)$(NC)"
	@echo "$(YELLOW)Check status with: kubectl get pods -n $(NAMESPACE) | grep backtest-job$(NC)"

backtest-check-results: ## Check if backtest results were stored in database
	@echo "$(GREEN)Checking backtest results in database...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.append('/workspace/src'); from sqlalchemy import create_engine, text; engine = create_engine('postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot'); conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM backtest_runs')); count = result.fetchone()[0]; print(f'📊 Backtest runs in database: {count}'); print('✅ Backtest results found in database!' if count > 0 else '❌ No backtest results found in database'); conn.close()"

docker-up: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting services with Docker Compose...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d

docker-up-build: ## Start services and build images
	@echo "$(GREEN)Building and starting services...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d --build

docker-down: ## Stop all Docker Compose services
	@echo "$(GREEN)Stopping Docker Compose services...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-restart: ## Restart all services
	@echo "$(GREEN)Restarting services...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml restart

docker-logs: ## Show logs for all services
	@echo "$(GREEN)Showing logs for all services...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

docker-logs-service: ## Show logs for specific service (usage: make docker-logs-service SERVICE=api-gateway)
	@echo "$(GREEN)Showing logs for $(SERVICE)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f $(SERVICE)

docker-shell: ## Open shell in specific service (usage: make docker-shell SERVICE=api-gateway)
	@echo "$(GREEN)Opening shell in $(SERVICE)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec $(SERVICE) /bin/bash

docker-clean: ## Clean up Docker resources
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

# Kubernetes Operations (Preferred)
k8s-deploy: ## Deploy to Kubernetes
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	$(KUBECTL) apply -f k8s/namespace.yaml
	$(KUBECTL) apply -f k8s/configmap.yaml
	$(KUBECTL) apply -f k8s/secrets.yaml
	$(KUBECTL) apply -f k8s/ -n $(NAMESPACE)
	@echo "$(GREEN)Kubernetes deployment completed!$(NC)"

k8s-delete: ## Delete Kubernetes deployment
	@echo "$(GREEN)Deleting Kubernetes deployment...$(NC)"
	$(KUBECTL) delete -f k8s/ -n $(NAMESPACE) || true
	$(KUBECTL) delete namespace $(NAMESPACE) || true

k8s-logs: ## Show logs for Kubernetes pods
	@echo "$(GREEN)Showing Kubernetes logs...$(NC)"
	$(KUBECTL) logs -f -l app=trading-service -n $(NAMESPACE)

k8s-pods: ## Show Kubernetes pods status
	@echo "$(GREEN)Kubernetes pods status:$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE)

k8s-services: ## Show Kubernetes services
	@echo "$(GREEN)Kubernetes services:$(NC)"
	$(KUBECTL) get services -n $(NAMESPACE)

k8s-scale: ## Scale Kubernetes deployment (usage: make k8s-scale DEPLOYMENT=trading-service REPLICAS=3)
	@echo "$(GREEN)Scaling $(DEPLOYMENT) to $(REPLICAS) replicas...$(NC)"
	$(KUBECTL) scale deployment $(DEPLOYMENT) --replicas=$(REPLICAS) -n $(NAMESPACE)

k8s-test: ## Run tests in Kubernetes
	@echo "$(GREEN)Running tests in Kubernetes...$(NC)"
	$(KUBECTL) exec -it deployment/trading-service -- python -m pytest tests/ -v -n $(NAMESPACE)

k8s-shell: ## Open shell in Kubernetes pod (usage: make k8s-shell POD=trading-service)
	@echo "$(GREEN)Opening shell in $(POD) pod...$(NC)"
	$(KUBECTL) exec -it deployment/$(POD) -- /bin/bash -n $(NAMESPACE)

k8s-port-forward: ## Port forward service (usage: make k8s-port-forward SERVICE=trading-service PORT=8000)
	@echo "$(GREEN)Port forwarding $(SERVICE) on port $(PORT)...$(NC)"
	$(KUBECTL) port-forward deployment/$(SERVICE) $(PORT):$(PORT) -n $(NAMESPACE)

k8s-exec: ## Execute command in pod (usage: make k8s-exec POD=trading-service CMD="python src/main.py")
	@echo "$(GREEN)Executing command in $(POD)...$(NC)"
	$(KUBECTL) exec -it deployment/$(POD) -- $(CMD) -n $(NAMESPACE)

# Kubernetes Backtest Operations
k8s-backtest-copy-results: ## Copy backtest results from host to project directory
	@echo "$(GREEN)Copying backtest results from host to project directory...$(NC)"
	@if [ -d "./backtest_results" ]; then \
		echo "$(GREEN)Results already in ./backtest_results/$(NC)"; \
	else \
		echo "$(YELLOW)No results found in ./backtest_results$(NC)"; \
	fi

k8s-backtest: ## Run backtest in Kubernetes (usage: make k8s-backtest SCRIPT=run_backtest.py)
	@if [ -z "$(SCRIPT)" ]; then \
		echo "$(RED)Error: SCRIPT parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest SCRIPT=run_backtest.py"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running backtest $(SCRIPT) in Kubernetes...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -v $(PWD):/workspace trading-cli python scripts/create_backtest_job.py $(SCRIPT) --output /workspace/backtest-job.yaml -- --start-date=2023-07-06 --end-date=2025-07-03
	$(KUBECTL) apply -f backtest-job.yaml -n $(NAMESPACE)
	@rm -f backtest-job.yaml
	@echo "$(YELLOW)Job created. Run 'make k8s-backtest-copy-results' after job completion to get results.$(NC)"

k8s-backtest-db-only: ## Run backtest in Kubernetes with database-only mode (usage: make k8s-backtest-db-only SCRIPT=run_backtest.py)
	@if [ -z "$(SCRIPT)" ]; then \
		echo "$(RED)Error: SCRIPT parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest-db-only SCRIPT=run_backtest.py"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running backtest $(SCRIPT) in Kubernetes (database-only mode)...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -v $(PWD):/workspace trading-cli python scripts/create_backtest_job.py $(SCRIPT) --database-only --output /workspace/backtest-job.yaml -- --start-date=2023-07-06 --end-date=2025-07-03
	$(KUBECTL) apply -f backtest-job.yaml -n $(NAMESPACE)
	@rm -f backtest-job.yaml
	@echo "$(YELLOW)Job created. Run 'make k8s-backtest-copy-results' after job completion to get results.$(NC)"

k8s-backtest-portfolio: ## Run portfolio backtest in Kubernetes (usage: make k8s-backtest-portfolio SCRIPT=run_portfolio_backtest.py)
	@if [ -z "$(SCRIPT)" ]; then \
		echo "$(RED)Error: SCRIPT parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest-portfolio SCRIPT=run_portfolio_backtest.py"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running portfolio backtest $(SCRIPT) in Kubernetes...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -v $(PWD):/workspace trading-cli python scripts/create_backtest_job.py $(SCRIPT) --job-name portfolio-backtest-$(shell date +%Y%m%d-%H%M%S) --output /workspace/portfolio-backtest-job.yaml
	$(KUBECTL) apply -f portfolio-backtest-job.yaml -n $(NAMESPACE)
	@rm -f portfolio-backtest-job.yaml

k8s-backtest-portfolio-db-only: ## Run portfolio backtest in Kubernetes with database-only mode (usage: make k8s-backtest-portfolio-db-only SCRIPT=run_portfolio_backtest.py)
	@if [ -z "$(SCRIPT)" ]; then \
		echo "$(RED)Error: SCRIPT parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest-portfolio-db-only SCRIPT=run_portfolio_backtest.py"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running portfolio backtest $(SCRIPT) in Kubernetes (database-only mode)...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -v $(PWD):/workspace trading-cli python scripts/create_backtest_job.py $(SCRIPT) --database-only --job-name portfolio-backtest-db-only-$(shell date +%Y%m%d-%H%M%S) --output /workspace/portfolio-backtest-job.yaml
	$(KUBECTL) apply -f portfolio-backtest-job.yaml -n $(NAMESPACE)
	@rm -f portfolio-backtest-job.yaml

k8s-backtest-logs: ## View backtest job logs (usage: make k8s-backtest-logs JOB=backtest-20241201-120000)
	@if [ -z "$(JOB)" ]; then \
		echo "$(RED)Error: JOB parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest-logs JOB=backtest-20241201-120000"; \
		echo "Available jobs:"; \
		$(KUBECTL) get jobs -n $(NAMESPACE) | grep backtest; \
		exit 1; \
	fi
	@echo "$(GREEN)Viewing logs for backtest job $(JOB)...$(NC)"
	$(KUBECTL) logs -f -n $(NAMESPACE) job/$(JOB)

k8s-backtest-jobs: ## List all backtest jobs
	@echo "$(GREEN)Listing all backtest jobs...$(NC)"
	$(KUBECTL) get jobs -n $(NAMESPACE) | grep backtest

k8s-backtest-cleanup: ## Clean up completed backtest jobs
	@echo "$(GREEN)Cleaning up completed backtest jobs...$(NC)"
	$(KUBECTL) delete jobs -n $(NAMESPACE) --field-selector=status.successful=1 --ignore-not-found=true
	$(KUBECTL) delete jobs -n $(NAMESPACE) --field-selector=status.failed=1 --ignore-not-found=true
	@echo "$(GREEN)Completed backtest jobs cleaned up!$(NC)"

k8s-backtest-status: ## Check status of all backtest jobs
	@echo "$(GREEN)Checking status of all backtest jobs...$(NC)"
	@echo "$(BLUE)Jobs:$(NC)"
	$(KUBECTL) get jobs -n $(NAMESPACE) | grep backtest
	@echo "$(BLUE)Pods:$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) | grep backtest

k8s-backtest-shell: ## Open shell in backtest job pod (usage: make k8s-backtest-shell JOB=backtest-20241201-120000)
	@if [ -z "$(JOB)" ]; then \
		echo "$(RED)Error: JOB parameter is required$(NC)"; \
		echo "Usage: make k8s-backtest-shell JOB=backtest-20241201-120000"; \
		exit 1; \
	fi
	@echo "$(GREEN)Opening shell in backtest job $(JOB)...$(NC)"
	$(KUBECTL) exec -it job/$(JOB) -n $(NAMESPACE) -- /bin/bash

k8s-backtest-exec: ## Execute command in backtest job (usage: make k8s-backtest-exec JOB=backtest-20241201-120000 CMD="python view_backtest_results.py")
	@if [ -z "$(JOB)" ] || [ -z "$(CMD)" ]; then \
		echo "$(RED)Error: JOB and CMD parameters are required$(NC)"; \
		echo "Usage: make k8s-backtest-exec JOB=backtest-20241201-120000 CMD=\"python view_backtest_results.py\""; \
		exit 1; \
	fi
	@echo "$(GREEN)Executing command in backtest job $(JOB)...$(NC)"
	$(KUBECTL) exec -it job/$(JOB) -n $(NAMESPACE) -- $(CMD)

# Backtest Results Management
backtest-list: ## List backtest runs from database
	@echo "$(GREEN)Listing backtest runs...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py list

backtest-list-detailed: ## List backtest runs with detailed information
	@echo "$(GREEN)Listing backtest runs with details...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py list --details

backtest-show: ## Show details for a specific backtest run (usage: make backtest-show RUN_ID=backtest_20250705_123456_BollingerBandsStrategy)
	@if [ -z "$(RUN_ID)" ]; then \
		echo "$(RED)Error: RUN_ID parameter is required$(NC)"; \
		echo "Usage: make backtest-show RUN_ID=backtest_20250705_123456_BollingerBandsStrategy"; \
		exit 1; \
	fi
	@echo "$(GREEN)Showing details for run $(RUN_ID)...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py show $(RUN_ID)

backtest-show-trades: ## Show trades for a specific backtest run (usage: make backtest-show-trades RUN_ID=backtest_20250705_123456_BollingerBandsStrategy)
	@if [ -z "$(RUN_ID)" ]; then \
		echo "$(RED)Error: RUN_ID parameter is required$(NC)"; \
		echo "Usage: make backtest-show-trades RUN_ID=backtest_20250705_123456_BollingerBandsStrategy"; \
		exit 1; \
	fi
	@echo "$(GREEN)Showing trades for run $(RUN_ID)...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py show $(RUN_ID) --show-trades

backtest-compare: ## Compare performance of different strategies
	@echo "$(GREEN)Comparing strategy performance...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py compare

backtest-export: ## Export backtest results to CSV (usage: make backtest-export OUTPUT=results.csv)
	@echo "$(GREEN)Exporting backtest results...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -v $(PWD):/workspace trading-cli python scripts/backtest_cli.py export $(if $(OUTPUT),--output /workspace/$(OUTPUT))

backtest-delete: ## Delete a backtest run (usage: make backtest-delete RUN_ID=backtest_20250705_123456_BollingerBandsStrategy)
	@if [ -z "$(RUN_ID)" ]; then \
		echo "$(RED)Error: RUN_ID parameter is required$(NC)"; \
		echo "Usage: make backtest-delete RUN_ID=backtest_20250705_123456_BollingerBandsStrategy"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Deleting backtest run $(RUN_ID)...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/backtest_cli.py delete $(RUN_ID) --force

# Backtest API
backtest-api: ## Start the backtest results API server
	@echo "$(GREEN)Starting backtest results API server...$(NC)"
	@echo "$(YELLOW)API will be available at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API docs at: http://localhost:8000/docs$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm -p 8000:8000 trading-cli uvicorn src.api.backtest_api:app --host 0.0.0.0 --port 8000 --reload

backtest-api-docs: ## Open the backtest API documentation
	@echo "$(GREEN)Opening API documentation...$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "$(YELLOW)Please open http://localhost:8000/docs in your browser$(NC)"

# Backtest Results Examples
backtest-examples: ## Show example CLI commands
	@echo "$(GREEN)Backtest Results CLI Examples:$(NC)"
	@echo ""
	@echo "$(YELLOW)List recent runs:$(NC)"
	@echo "  make backtest-list"
	@echo ""
	@echo "$(YELLOW)List runs with details:$(NC)"
	@echo "  make backtest-list-detailed"
	@echo ""
	@echo "$(YELLOW)Show specific run details:$(NC)"
	@echo "  make backtest-show RUN_ID=backtest_20250705_123456_BollingerBandsStrategy"
	@echo ""
	@echo "$(YELLOW)Show trades for a run:$(NC)"
	@echo "  make backtest-show-trades RUN_ID=backtest_20250705_123456_BollingerBandsStrategy"
	@echo ""
	@echo "$(YELLOW)Compare strategies:$(NC)"
	@echo "  make backtest-compare"
	@echo ""
	@echo "$(YELLOW)Export results to CSV:$(NC)"
	@echo "  make backtest-export OUTPUT=my_results.csv"
	@echo ""
	@echo "$(YELLOW)Start API server:$(NC)"
	@echo "  make backtest-api"
	@echo ""
	@echo "$(YELLOW)API endpoints:$(NC)"
	@echo "  GET  /api/v1/runs                    - List runs"
	@echo "  GET  /api/v1/runs/{run_id}          - Get run details"
	@echo "  GET  /api/v1/runs/{run_id}/trades   - Get run trades"
	@echo "  GET  /api/v1/runs/{run_id}/equity   - Get equity curve"
	@echo "  GET  /api/v1/compare                - Compare strategies"
	@echo "  GET  /api/v1/strategies             - List strategies"
	@echo "  GET  /api/v1/stats                  - Get statistics"
	@echo "  DELETE /api/v1/runs/{run_id}        - Delete run"

# Database Operations
db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python -m alembic upgrade head

db-rollback: ## Rollback database migrations
	@echo "$(GREEN)Rolling back database migrations...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python -m alembic downgrade -1

db-backup: ## Backup databases
	@echo "$(GREEN)Backing up databases...$(NC)"
	$(DOCKER_COMPOSE) exec write-db pg_dump -U postgres trading_write > backup_write_$(shell date +%Y%m%d_%H%M%S).sql
	$(DOCKER_COMPOSE) exec read-db pg_dump -U postgres trading_read > backup_read_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup completed!$(NC)"

db-restore: ## Restore databases (usage: make db-restore WRITE_BACKUP=backup_write_20231201_120000.sql READ_BACKUP=backup_read_20231201_120000.sql)
	@echo "$(GREEN)Restoring databases...$(NC)"
	$(DOCKER_COMPOSE) exec -T write-db psql -U postgres trading_write < $(WRITE_BACKUP)
	$(DOCKER_COMPOSE) exec -T read-db psql -U postgres trading_read < $(READ_BACKUP)

# Backtest Data Scanner
backtest-scan: ## Scan and store backtest data (usage: make backtest-scan SYMBOLS="AAPL MSFT GOOGL")
	@echo "$(GREEN)Scanning backtest data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python scan_backtest_data.py --symbols $(SYMBOLS)

backtest-scan-period: ## Scan specific period (usage: make backtest-scan-period SYMBOLS="AAPL MSFT" START_DATE="2024-01-01" END_DATE="2024-12-31")
	@echo "$(GREEN)Scanning backtest data for specific period...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python scan_backtest_data.py --symbols $(SYMBOLS) --start-date $(START_DATE) --end-date $(END_DATE)

backtest-scan-multi: ## Scan multiple common backtest periods
	@echo "$(GREEN)Scanning multiple backtest periods...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python scan_backtest_data.py --multi-period

backtest-coverage: ## Check database coverage (usage: make backtest-coverage SYMBOLS="AAPL MSFT" START_DATE="2024-01-01" END_DATE="2024-12-31")
	@echo "$(GREEN)Checking database coverage...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python scan_backtest_data.py --check-coverage --symbols $(SYMBOLS) --start-date $(START_DATE) --end-date $(END_DATE)

backtest-cleanup: ## Clean up old backtest data
	@echo "$(GREEN)Cleaning up old backtest data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python scan_backtest_data.py --cleanup
	@echo "$(GREEN)Cleanup completed!$(NC)"

# Build Comprehensive Backtest Data
backtest-build: ## Build comprehensive backtest data (usage: make backtest-build PERIODS=comprehensive)
	@echo "$(GREEN)Building comprehensive backtest data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --periods $(PERIODS)

backtest-build-recent: ## Build recent backtest data (2022-2024)
	@echo "$(GREEN)Building recent backtest data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --periods recent

backtest-build-comprehensive: ## Build comprehensive backtest data (5+ years)
	@echo "$(GREEN)Building comprehensive backtest data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --periods comprehensive

backtest-build-crisis: ## Build crisis period data for stress testing
	@echo "$(GREEN)Building crisis period data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --periods crisis

backtest-build-intraday: ## Build intraday data for high-frequency strategies
	@echo "$(GREEN)Building intraday data...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --periods intraday

backtest-estimate: ## Estimate storage requirements for backtest data
	@echo "$(GREEN)Estimating storage requirements...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --estimate-storage

backtest-dry-run: ## Show what would be built without executing
	@echo "$(GREEN)Showing dry run of backtest data build...$(NC)"
	$(DOCKER_COMPOSE) exec trading-service python build_backtest_data.py --dry-run --periods comprehensive

# Backtest Scanner Kubernetes Operations
k8s-scanner-deploy: ## Deploy backtest scanner to Kubernetes
	@echo "$(GREEN)Deploying backtest scanner to Kubernetes...$(NC)"
	$(KUBECTL) apply -f k8s/backtest-scanner-configmap.yaml -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/backtest-scanner-deployment.yaml -n $(NAMESPACE)
	$(KUBECTL) apply -f k8s/backtest-scanner-ingress.yaml -n $(NAMESPACE)
	@echo "$(GREEN)Backtest scanner deployed!$(NC)"

k8s-scanner-delete: ## Delete backtest scanner from Kubernetes
	@echo "$(RED)Deleting backtest scanner from Kubernetes...$(NC)"
	$(KUBECTL) delete -f k8s/backtest-scanner-ingress.yaml -n $(NAMESPACE) --ignore-not-found=true
	$(KUBECTL) delete -f k8s/backtest-scanner-deployment.yaml -n $(NAMESPACE) --ignore-not-found=true
	$(KUBECTL) delete -f k8s/backtest-scanner-configmap.yaml -n $(NAMESPACE) --ignore-not-found=true
	@echo "$(RED)Backtest scanner deleted!$(NC)"

k8s-scanner-logs: ## View backtest scanner logs
	@echo "$(GREEN)Viewing backtest scanner logs...$(NC)"
	$(KUBECTL) logs -f deployment/backtest-scanner -n $(NAMESPACE)

k8s-scanner-shell: ## Access backtest scanner pod shell
	@echo "$(GREEN)Accessing backtest scanner pod shell...$(NC)"
	$(KUBECTL) exec -it deployment/backtest-scanner -n $(NAMESPACE) -- /bin/bash

k8s-scanner-job: ## Run backtest scanner job
	@echo "$(GREEN)Running backtest scanner job...$(NC)"
	$(KUBECTL) create job --from=cronjob/backtest-scanner-daily manual-scan-$(shell date +%Y%m%d-%H%M%S) -n $(NAMESPACE)

k8s-scanner-coverage: ## Check database coverage
	@echo "$(GREEN)Checking database coverage...$(NC)"
	$(KUBECTL) create job --from=cronjob/backtest-scanner-daily coverage-check-$(shell date +%Y%m%d-%H%M%S) -n $(NAMESPACE) -- python scan_backtest_data.py --check-coverage

k8s-scanner-scale: ## Scale backtest scanner (usage: make k8s-scanner-scale REPLICAS=3)
	@echo "$(GREEN)Scaling backtest scanner to $(REPLICAS) replicas...$(NC)"
	$(KUBECTL) scale deployment backtest-scanner --replicas=$(REPLICAS) -n $(NAMESPACE)

k8s-scanner-exec: ## Execute command in backtest scanner pod (usage: make k8s-scanner-exec CMD="python scan_backtest_data.py --symbols AAPL MSFT")
	@echo "$(GREEN)Executing command in backtest scanner...$(NC)"
	$(KUBECTL) exec -it deployment/backtest-scanner -n $(NAMESPACE) -- $(CMD)

# 5-Year Data Population Jobs
k8s-populate-5year: ## Deploy 5-year data population jobs (2020-2025)
	@echo "$(GREEN)Deploying 5-year data population jobs...$(NC)"
	$(KUBECTL) apply -f k8s/backtest-scanner-5year-jobs.yaml -n $(NAMESPACE)
	@echo "$(GREEN)5-year data population jobs deployed!$(NC)"
	@echo "$(YELLOW)Jobs will run in parallel for faster processing$(NC)"

k8s-populate-5year-logs: ## View logs from all 5-year population jobs
	@echo "$(GREEN)Viewing logs from all 5-year population jobs...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop following logs$(NC)"
	$(KUBECTL) logs -f job/backtest-scanner-2020 -n $(NAMESPACE) & \
	$(KUBECTL) logs -f job/backtest-scanner-2021 -n $(NAMESPACE) & \
	$(KUBECTL) logs -f job/backtest-scanner-2022 -n $(NAMESPACE) & \
	$(KUBECTL) logs -f job/backtest-scanner-2023 -n $(NAMESPACE) & \
	$(KUBECTL) logs -f job/backtest-scanner-2024 -n $(NAMESPACE) & \
	$(KUBECTL) logs -f job/backtest-scanner-2025 -n $(NAMESPACE) & \
	wait

k8s-populate-5year-status: ## Check status of 5-year population jobs
	@echo "$(GREEN)Checking status of 5-year population jobs...$(NC)"
	@echo "$(BLUE)Jobs:$(NC)"
	$(KUBECTL) get jobs -l app=backtest-scanner -n $(NAMESPACE)
	@echo "$(BLUE)Pods:$(NC)"
	$(KUBECTL) get pods -l app=backtest-scanner -n $(NAMESPACE)

k8s-populate-5year-cleanup: ## Clean up 5-year population jobs
	@echo "$(RED)Cleaning up 5-year population jobs...$(NC)"
	$(KUBECTL) delete jobs -l app=backtest-scanner -n $(NAMESPACE) --ignore-not-found=true
	@echo "$(GREEN)5-year population jobs cleaned up!$(NC)"

k8s-coverage-check: ## Run coverage check after data population
	@echo "$(GREEN)Running coverage check...$(NC)"
	$(KUBECTL) apply -f k8s/backtest-scanner-5year-jobs.yaml --selector=type=coverage-check -n $(NAMESPACE)

k8s-coverage-check-logs: ## View coverage check logs
	@echo "$(GREEN)Viewing coverage check logs...$(NC)"
	$(KUBECTL) logs -f job/backtest-coverage-check -n $(NAMESPACE)

# Monitoring and Logs
monitor: ## Start monitoring services
	@echo "$(GREEN)Starting monitoring services...$(NC)"
	$(DOCKER_COMPOSE) up -d prometheus grafana kibana elasticsearch

logs: ## Show application logs
	@echo "$(GREEN)Showing application logs...$(NC)"
	tail -f logs/trader.log

logs-clear: ## Clear application logs
	@echo "$(GREEN)Clearing application logs...$(NC)"
	rm -f logs/*.log

# Development Tools
jupyter: ## Start Jupyter notebook
	@echo "$(GREEN)Starting Jupyter notebook...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser

notebook: ## Start Jupyter lab
	@echo "$(GREEN)Starting Jupyter lab...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

# API Testing
test-api: ## Test API endpoints
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python test_public_api.py

test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL) delete namespace trading-system

# Run a backtest job on Kubernetes
kube-backtest:
	$(KUBECTL) apply -f k8s/backtest-job.yaml

# Check status of backtest job
kube-backtest-status:
	$(KUBECTL) -n trading-system get jobs

# Get logs from the backtest job
kube-backtest-logs:
	$(KUBECTL) -n trading-system logs job/trading-backtest

# Yahoo Finance Market Data Demos (Docker-based)
yahoo-demo: ## Run Yahoo Finance market data demo in Docker
	@echo "$(GREEN)Running Yahoo Finance market data demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_yahoo_finance.py

yahoo-demo-docker: ## Run Yahoo Finance demo inside Docker (legacy)
	@echo "$(GREEN)Running Yahoo Finance demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python demo_yahoo_finance.py

yahoo-test-single: ## Test single symbol data retrieval in Docker
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch: ## Test batch data retrieval in Docker
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

yahoo-backtest-real: ## Run backtest with real Yahoo Finance data in Docker
	@echo "$(GREEN)Running backtest with real Yahoo Finance data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-backtest-real-docker: ## Run backtest with real data inside Docker (legacy)
	@echo "$(GREEN)Running backtest with real data in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python run_backtest.py --use-real-data --symbols AAPL,GOOGL,MSFT --start-date 2024-01-01 --end-date 2024-12-31

yahoo-test-single-docker: ## Test single symbol data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing single symbol data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Info:', service.get_symbol_info('AAPL'))"

yahoo-test-batch-docker: ## Test batch data retrieval in Docker (legacy)
	@echo "$(GREEN)Testing batch data retrieval in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec trading-bot-dev python -c "import sys; sys.path.insert(0, 'src'); from services.market_data.yahoo_finance_service import get_market_data; from datetime import datetime, timedelta; end_date = datetime.now().strftime('%Y-%m-%d'); start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'); data = get_market_data(['AAPL', 'GOOGL'], start_date, end_date); print(f'Downloaded {len(data)} symbols'); [print(f'{symbol}: {len(df)} records') for symbol, df in data.items()]"

# Market Data Provider Tests
test-market-data: ## Test all market data providers
	@echo "$(GREEN)Testing all market data providers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python demo_market_data_providers.py

test-yahoo-finance: ## Test Yahoo Finance provider
	@echo "$(GREEN)Testing Yahoo Finance provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.yahoo_finance_service import YahooFinanceService; service = YahooFinanceService(); print('AAPL Price:', service.get_live_price('AAPL')); print('AAPL Data:', len(service.get_historical_data('AAPL', '2024-01-01', '2024-01-31') or []), 'records')"

test-alpha-vantage: ## Test Alpha Vantage provider
	@echo "$(GREEN)Testing Alpha Vantage provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import AlphaVantageProvider; provider = AlphaVantageProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-iex-cloud: ## Test IEX Cloud provider
	@echo "$(GREEN)Testing IEX Cloud provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import IEXCloudProvider; provider = IEXCloudProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

test-polygon: ## Test Polygon provider
	@echo "$(GREEN)Testing Polygon provider...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import PolygonProvider; provider = PolygonProvider(); print('Provider initialized:', provider.api_key is not None); print('AAPL Price:', provider.get_live_price('AAPL'))"

check-providers: ## Check status of all providers
	@echo "$(GREEN)Checking provider status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; manager = get_market_data_manager(); status = manager.get_provider_status(); [print(f'{p}: {\"✅ Working\" if s else \"❌ Failed\"}') for p, s in status.items()]"

get-live-prices: ## Get live prices for symbols (use SYMBOLS="AAPL,GOOGL,MSFT")
	@echo "$(GREEN)Getting live prices for $(SYMBOLS)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from src.services.market_data.market_data_provider import get_market_data_manager; import sys; symbols = '$(SYMBOLS)'.split(','); manager = get_market_data_manager(); prices = {s: manager.get_live_price(s) for s in symbols}; [print(f'{s}: ${p:.2f}' if p else f'{s}: No price') for s, p in prices.items()]"

run-backtest-real-data: ## Run backtest with real market data
	@echo "$(GREEN)Running backtest with real market data...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "import asyncio; from src.backtesting.backtest_engine import BacktestEngine; engine = BacktestEngine(use_real_data=True); result = asyncio.run(engine.run_backtest(['AAPL', 'GOOGL'], '2024-01-01', '2024-01-31', ['sma_crossover'])); print('Backtest completed:', len(result) if result else 0, 'strategies')"

docker-test-market-data: ## Test market data service integration in Docker
	@echo "$(GREEN)Testing market data service integration in Docker...$(NC)"
	docker exec trading-cli python test_market_data_integration.py

# Trading System Operations
run-api: ## Start the trading API server
	@echo "$(GREEN)Starting trading API server...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_api.py

run-trader: ## Start the trading engine directly
	@echo "$(GREEN)Starting trading engine...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_trader.py

run-signal-client: ## Run the signal client example
	@echo "$(GREEN)Running signal client example...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python send_signal_example.py

run-strategy-manager: ## Run the strategy manager demo
	@echo "$(GREEN)Running strategy manager demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python strategy_manager.py

run-news-bot: ## Run the news bot demo
	@echo "$(GREEN)Running news bot demo...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python news_bot_demo.py

run-backtest: ## Run comprehensive backtesting analysis
	@echo "$(GREEN)Running backtesting analysis...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py

backtest-quick: ## Run quick backtest with fewer symbols
	@echo "$(GREEN)Running quick backtest...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

backtest-single: ## Run backtest for single strategy
	@echo "$(GREEN)Running single strategy backtest...$(NC)"
	@read -p "Enter strategy name (sma_crossover/rsi/macd/bollinger_bands): " strategy; \
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -c "from run_backtest import main; import sys; sys.argv = ['single', '$$strategy']; main()"

docker-backtest: ## Run backtesting analysis in Docker container
	@echo "$(GREEN)Running backtesting analysis in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python run_backtest.py

docker-backtest-quick: ## Run quick backtest in Docker with fewer symbols
	@echo "$(GREEN)Running quick backtest in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "from run_backtest import main; import sys; sys.argv = ['quick']; main()"

docker-view-results: ## View backtest results in Docker
	@echo "$(GREEN)Viewing backtest results...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python view_backtest_results.py

docker-news-ai-demo: ## Run news + AI enhanced trading demo in Docker
	@echo "$(GREEN)Running news + AI enhanced trading demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python news_ai_demo.py

docker-rabbitmq-demo: ## Run RabbitMQ workers demo in Docker
	@echo "$(GREEN)Running RabbitMQ workers demo in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python demo_rabbitmq_workers.py

docker-start-workers: ## Start background workers in Docker
	@echo "$(GREEN)Starting background workers in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -m src.services.workers.worker_manager

docker-rabbitmq-status: ## Check RabbitMQ queue status
	@echo "$(GREEN)Checking RabbitMQ queue status...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev python -c "import asyncio; from src.services.queue.rabbitmq_service import RabbitMQService; from src.utils.config import Config; async def check(): config = Config(); rmq = RabbitMQService(config); await rmq.connect(); [print(f'{q}: {await rmq.get_queue_stats(q)}') for q in rmq.queues.values()]; await rmq.disconnect(); asyncio.run(check())"

docker-ollama-setup: ## Setup and pull Ollama models
	@echo "$(GREEN)Setting up Ollama models...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull llama2
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec ollama ollama pull codellama

docker-ollama-status: ## Check Ollama service status
	@echo "$(GREEN)Checking Ollama service status...$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)Ollama service not available$(NC)"

docker-run-api: ## Start API server in Docker
	@echo "$(GREEN)Starting API server in Docker...$(NC)"
	docker run -d --name trading-api -p 8000:8000 trading-bot-dev python run_api.py

docker-run-trader: ## Start trading engine in Docker
	@echo "$(GREEN)Starting trading engine in Docker...$(NC)"
	docker run -d --name trading-engine trading-bot-dev python run_trader.py

# Event Replay
replay-events: ## Replay events (usage: make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Replaying events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--dry-run

replay-events-execute: ## Execute event replay (usage: make replay-events-execute FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Executing event replay...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py replay \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE)

replay-scenario: ## Replay test scenario (usage: make replay-scenario SCENARIO=trading_day)
	@echo "$(GREEN)Replaying scenario: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO) --dry-run

replay-scenario-execute: ## Execute scenario replay (usage: make replay-scenario-execute SCENARIO=trading_day)
	@echo "$(GREEN)Executing scenario replay: $(SCENARIO)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py scenario $(SCENARIO)

replay-aggregate: ## Replay specific aggregate (usage: make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10)
	@echo "$(GREEN)Replaying aggregate $(AGGREGATE_ID) from version $(SNAPSHOT_VERSION)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py aggregate $(AGGREGATE_ID) $(SNAPSHOT_VERSION)

replay-restore: ## Restore system state (usage: make replay-restore RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Restoring system to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --dry-run

replay-restore-execute: ## Execute system restore (usage: make replay-restore-execute RESTORE_POINT=start_of_day)
	@echo "$(GREEN)Executing system restore to $(RESTORE_POINT)...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py restore $(RESTORE_POINT) --execute

replay-list: ## List events without replaying (usage: make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02)
	@echo "$(GREEN)Listing events...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python scripts/replay_events.py list \
		--from-date $(FROM_DATE) \
		--to-date $(TO_DATE) \
		--limit 100

# Performance Testing
benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/benchmark/ -v

# Security
security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m bandit -r src/
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m safety check

# Documentation
docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --html src/ --output-dir docs/

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-cli python -m pdoc --http :8080 src/

# Cleanup
clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log data/*.csv

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(GREEN)Cleaning everything...$(NC)"
	rm -rf venv/ .env

# Quick Commands
dev: setup-dev docker-up ## Quick development setup
	@echo "$(GREEN)Development environment ready!$(NC)"

prod: setup-prod docker-up monitor ## Quick production setup
	@echo "$(GREEN)Production environment ready!$(NC)"

quick-test: docker-up test docker-down ## Quick test run
	@echo "$(GREEN)Quick test completed!$(NC)"

status: ## Show system status
	@echo "$(GREEN)System Status:$(NC)"
	@echo "$(BLUE)Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""

# CLI commands for internal operations (secure architecture)
cli-health: ## Check health of all services via CLI
	@echo "$(GREEN)Checking service health via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health

cli-portfolio: ## Get portfolio summary via CLI
	@echo "$(GREEN)Getting portfolio summary via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py portfolio

cli-strategies: ## Get available strategies via CLI
	@echo "$(GREEN)Getting available strategies via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py strategies

cli-market-data: ## Get market data via CLI (usage: make cli-market-data SYMBOL=AAPL)
	@echo "$(GREEN)Getting market data for $(SYMBOL) via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py market-data --symbol $(SYMBOL)

cli-risk: ## Get risk assessment via CLI
	@echo "$(GREEN)Getting risk assessment via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py risk

cli-orders: ## Get orders via CLI
	@echo "$(GREEN)Getting orders via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py orders

cli-analytics: ## Get analytics via CLI (usage: make cli-analytics REPORT=performance)
	@echo "$(GREEN)Getting $(REPORT) analytics via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py analytics --report $(REPORT)

cli-trade: ## Execute trade via CLI (usage: make cli-trade SYMBOL=AAPL SIDE=buy QUANTITY=100 PRICE=150.0)
	@echo "$(GREEN)Executing trade via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py trade --symbol $(SYMBOL) --side $(SIDE) --quantity $(QUANTITY) --price $(PRICE)

cli-signal: ## Generate trading signal via CLI (usage: make cli-signal STRATEGY=sma_crossover SYMBOL=AAPL)
	@echo "$(GREEN)Generating trading signal via CLI...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py signal --strategy $(STRATEGY) --symbol $(SYMBOL)

# Interactive CLI shell
cli-shell: ## Open interactive CLI shell
	@echo "$(GREEN)Opening interactive CLI shell...$(NC)"
	docker exec -it trading-cli /bin/bash

# Service-specific health checks via CLI
health-api: ## Check API gateway health via CLI
	@echo "$(GREEN)Checking API gateway health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service api-gateway

health-trading: ## Check trading service health via CLI
	@echo "$(GREEN)Checking trading service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service trading

health-market-data: ## Check market data service health via CLI
	@echo "$(GREEN)Checking market data service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service market-data

health-risk: ## Check risk service health via CLI
	@echo "$(GREEN)Checking risk service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service risk

health-portfolio: ## Check portfolio service health via CLI
	@echo "$(GREEN)Checking portfolio service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service portfolio

health-strategy: ## Check strategy service health via CLI
	@echo "$(GREEN)Checking strategy service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service strategy

health-order: ## Check order service health via CLI
	@echo "$(GREEN)Checking order service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service order

health-analytics: ## Check analytics service health via CLI
	@echo "$(GREEN)Checking analytics service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service analytics

health-user: ## Check user service health via CLI
	@echo "$(GREEN)Checking user service health...$(NC)"
	docker exec trading-cli python scripts/trading_cli.py health --service user
	@echo "$(BLUE)Kubernetes (if available):$(NC)"
	$(KUBECTL) get pods -n $(NAMESPACE) 2>/dev/null || echo "Kubernetes not available"

# Utility Commands
env-check: ## Check environment configuration
	@echo "$(GREEN)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(PUBLIC_API_KEY|PUBLIC_API_SECRET|DATABASE_URL)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

version: ## Show version information
	@echo "$(GREEN)Version Information:$(NC)"
	@echo "Python: $$(docker-compose -f docker-compose.dev.yml run --rm trading-cli python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version)"
	@echo "Kubectl: $$($(KUBECTL) version --client 2>/dev/null | head -1 || echo 'Not installed')"

# Helpers
.PHONY: _check-env _check-docker _check-k8s

_check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make setup-dev' first.$(NC)"; \
		exit 1; \
	fi

_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)Error: Docker is not running.$(NC)"; \
		exit 1; \
	fi

_check-k8s:
	@if ! $(KUBECTL) version --client > /dev/null 2>&1; then \
		echo "$(RED)Error: kubectl is not installed or not configured.$(NC)"; \
		exit 1; \
	fi

# Docker-based development commands
docker-dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis kafka eventstore
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-dev

docker-test:
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres-test redis-test kafka-test eventstore-test
	@echo "$(GREEN)Waiting for test services to be ready...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up trading-bot-test

docker-stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

docker-clean:
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v
	docker system prune -f

# Development utilities
dev-shell:
	@echo "$(GREEN)Starting development shell...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml run --rm trading-bot-dev bash

dev-logs:
	@echo "$(GREEN)Showing development logs...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f trading-bot-dev

# Quick start for development
quick-start:
	@echo "$(GREEN)Quick start development environment...$(NC)"
	make docker-build
	make docker-dev

# Production deployment
deploy:
	@echo "$(GREEN)Deploying to production...$(NC)"
	./deploy.sh

# Health check
health-check:
	@echo "$(GREEN)Checking system health...$(NC)"
	curl -f http://localhost:8000/health || echo "API not responding"
	curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	curl -f http://localhost:3000/api/health || echo "Grafana not responding"

# Kubernetes Namespace
kube-namespace:
	$(KUBECTL) create namespace trading-system || true

# Apply all secrets and configmaps
kube-secrets:
	$(KUBECTL) apply -f k8s/secrets.yaml

# Deploy RabbitMQ (stateless)
kube-rabbitmq:
	$(KUBECTL) apply -f k8s/rabbitmq-deployment-simple.yaml

# Deploy RabbitMQ workers
kube-workers:
	$(KUBECTL) apply -f k8s/rabbitmq-workers-deployment.yaml

# Deploy News Scan CronJob
kube-news-cronjob:
	$(KUBECTL) apply -f k8s/news-scanning-cronjob.yaml

# Deploy all core components
kube-deploy-all: kube-namespace kube-secrets kube-rabbitmq kube-workers kube-news-cronjob

# Get status of all pods
kube-status:
	$(KUBECTL) -n trading-system get pods

# Get status of all jobs
kube-jobs:
	$(KUBECTL) -n trading-system get jobs

# Get logs from all worker pods
kube-logs:
	$(KUBECTL) -n trading-system logs -l app=rabbitmq-workers --tail=100

# Port-forward RabbitMQ management UI
kube-rabbitmq-ui:
	$(KUBECTL) -n trading-system port-forward svc/rabbitmq-service 15672:15672

# Clean up all resources
kube-clean:
	$(KUBECTL