# Makefile Reference - Containerized Execution

## Overview

This Makefile implements a **secure, containerized execution model** where **all Python scripts and executables run inside Docker containers**. The Makefile is the only interface executed on the host system, ensuring enhanced security and isolation.

## Security Model

### Containerized Execution
- **All Python scripts run in `trading-cli` container**
- **No code execution on host system**
- **Makefile commands orchestrate Docker containers**
- **Isolated execution environments**

### Command Structure
```bash
# ❌ OLD WAY (Insecure - runs on host)
python script.py

# ✅ NEW WAY (Secure - runs in container)
make command-name
# or
docker-compose -f docker-compose.dev.yml run --rm trading-cli python script.py
```

## Core Commands

### Development Setup
```bash
make setup-dev          # Set up development environment (host only)
make docker-build       # Build all Docker images
make docker-up          # Start all services
make docker-down        # Stop all services
```

### Testing (Containerized)
```bash
make test               # Run all tests in container
make test-unit          # Run unit tests in container
make test-integration   # Run integration tests in container
make test-coverage      # Run tests with coverage in container
```

### Code Quality (Containerized)
```bash
make lint               # Run linting checks in container
make format             # Format code in container
make type-check         # Run type checking in container
```

### Trading Operations (Containerized)
```bash
make run-api            # Start API server in container
make run-trader         # Start trading engine in container
make run-backtest       # Run backtesting in container
make run-news-bot       # Run news bot in container
```

### CLI Operations (Containerized)
```bash
make cli-health         # Check all services health
make cli-portfolio      # Get portfolio summary
make cli-market-data SYMBOL=AAPL  # Get market data
make cli-strategies     # Get available strategies
make cli-risk           # Get risk assessment
make cli-orders         # Get orders
make cli-analytics REPORT=performance  # Get analytics
```

### Service Health Checks (Containerized)
```bash
make health-api         # Check API gateway health
make health-trading     # Check trading service health
make health-market-data # Check market data service health
make health-risk        # Check risk service health
make health-portfolio   # Check portfolio service health
make health-strategy    # Check strategy service health
make health-order       # Check order service health
make health-analytics   # Check analytics service health
make health-user        # Check user service health
```

## Advanced Commands

### Backtesting (Containerized)
```bash
make run-backtest       # Full backtesting analysis
make backtest-quick     # Quick backtest with fewer symbols
make backtest-single    # Single strategy backtest
make docker-backtest    # Backtesting in Docker (legacy)
make docker-view-results # View results in Docker
```

### News and AI (Containerized)
```bash
make run-news-bot       # News bot demo
make docker-news-ai-demo # News + AI enhanced trading
make docker-ollama-setup # Setup Ollama models
make docker-ollama-status # Check Ollama status
```

### RabbitMQ (Containerized)
```bash
make docker-rabbitmq-demo # RabbitMQ workers demo
make docker-start-workers # Start background workers
make docker-rabbitmq-status # Check queue status
```

### Yahoo Finance (Containerized)
```bash
make yahoo-demo         # Yahoo Finance demo in container
make yahoo-test-single  # Test single symbol in container
make yahoo-test-batch   # Test batch retrieval in container
make yahoo-backtest-real # Backtest with real data in container
```

### Event Replay (Containerized)
```bash
make replay-events FROM_DATE=2023-12-01 TO_DATE=2023-12-02
make replay-scenario SCENARIO=trading_day
make replay-aggregate AGGREGATE_ID=order-123 SNAPSHOT_VERSION=10
make replay-restore RESTORE_POINT=start_of_day
make replay-list FROM_DATE=2023-12-01 TO_DATE=2023-12-02
```

## Docker Management

### Container Operations
```bash
make docker-build       # Build images
make docker-up          # Start services
make docker-down        # Stop services
make docker-restart     # Restart services
make docker-clean       # Clean up resources
```

### Logs and Debugging
```bash
make docker-logs        # Show all service logs
make docker-logs-service SERVICE=api-gateway  # Specific service logs
make docker-shell SERVICE=api-gateway  # Shell into service
```

### Development Shell
```bash
make dev-shell          # Development shell in container
make dev-logs           # Development logs
```

## Kubernetes Commands

### Deployment
```bash
make kube-deploy-all    # Deploy all components
make kube-namespace     # Create namespace
make kube-secrets       # Apply secrets
make kube-rabbitmq      # Deploy RabbitMQ
make kube-workers       # Deploy workers
make kube-news-cronjob  # Deploy news scanning
```

### Management
```bash
make kube-status        # Check pod status
make kube-jobs          # Check job status
make kube-logs          # View logs
make kube-rabbitmq-ui   # Port-forward RabbitMQ UI
make kube-clean         # Clean up resources
```

### Backtesting on Kubernetes
```bash
make kube-backtest      # Run backtest job
make kube-backtest-status # Check backtest status
make kube-backtest-logs # Get backtest logs
```

## Utility Commands

### System Information
```bash
make version            # Show version information (containerized)
make env-check          # Check environment configuration
make status             # Show system status
```

### Security and Quality
```bash
make security-scan      # Run security scans in container
make benchmark          # Run performance benchmarks in container
```

### Documentation
```bash
make docs               # Generate documentation in container
make docs-serve         # Serve documentation in container
```

## Quick Start Commands

### Development
```bash
make dev                # Quick development setup
make quick-start        # Quick start development environment
```

### Production
```bash
make prod               # Quick production setup
make deploy             # Deploy to production
```

## Environment Variables

### Required Variables
- `PUBLIC_API_KEY`: API key for external services
- `PUBLIC_API_SECRET`: API secret for external services
- `DATABASE_URL`: Database connection string

### Container Environment
- All services run with environment variables from `.env`
- Docker Compose manages container environment
- Kubernetes uses ConfigMaps and Secrets

## Best Practices

### 1. Always Use Makefile
- **Never run Python scripts directly on host**
- **Use `make` commands for all operations**
- **Leverage containerized execution**

### 2. Development Workflow
```bash
# 1. Setup
make setup-dev
make docker-build
make docker-up

# 2. Development
make test
make lint
make format

# 3. Operations
make cli-health
make run-backtest

# 4. Monitoring
make docker-logs
make status
```

### 3. Security
- **All code execution in containers**
- **No host system contamination**
- **Isolated dependencies**
- **Controlled network access**

### 4. Troubleshooting
```bash
# Check container status
make docker-logs

# Debug specific service
make docker-shell SERVICE=service-name

# Check system health
make cli-health
make status
```

## Command Categories

### Host-Only Commands
- `setup-dev`: Environment setup
- `docker-build`: Build images
- `docker-up/down`: Container orchestration
- `kube-*`: Kubernetes management

### Containerized Commands
- All Python script execution
- Testing and linting
- Trading operations
- CLI operations
- Data processing

### Monitoring Commands
- `docker-logs`: Container logs
- `status`: System status
- `cli-health`: Service health
- `version`: Version information

## Security Benefits

1. **Code Isolation**: No Python execution on host
2. **Network Security**: Internal service communication only
3. **Resource Control**: Container limits and isolation
4. **Audit Trail**: All operations through Makefile
5. **Reproducible Environments**: Consistent execution across systems

This containerized execution model ensures maximum security while providing a simple, consistent interface for all trading system operations. 