# Secure Architecture Guide

## Overview

This trading system implements a **secure, containerized architecture** where **all Python scripts and executables run inside Docker containers**. This ensures that no code execution occurs on the host system, providing enhanced security and isolation.

## Security Principles

### 1. Containerized Execution
- **All Python scripts run inside Docker containers**
- **No code execution on the host system**
- **Makefile is the only interface executed on the host**
- **Isolated execution environments for each operation**

### 2. Network Security
- **API Gateway**: Only external entry point (port 8000)
- **Internal Services**: All other services run on internal Docker network
- **No direct external access** to internal microservices
- **CLI Container**: Secure internal operations interface

### 3. Data Isolation
- **Database connections**: Internal Docker networking only
- **File system**: Containerized with volume mounts for persistence
- **Environment variables**: Managed through Docker Compose
- **Secrets**: Kubernetes secrets or Docker secrets

## Architecture Components

### External Interface
```
┌─────────────────┐
│   API Gateway   │ ← Only external port (8000)
│   (Port 8000)   │
└─────────────────┘
```

### Internal Services (Docker Network)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Trading CLI    │  │  Market Data    │  │   Portfolio     │
│  (Internal)     │  │  (Internal)     │  │  (Internal)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     Risk        │  │   Strategy      │  │     Order       │
│  (Internal)     │  │  (Internal)     │  │  (Internal)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Analytics     │  │     User        │  │   Command API   │
│  (Internal)     │  │  (Internal)     │  │  (Internal)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Infrastructure Services (Internal)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Redis       │  │    RabbitMQ     │
│  (Internal)     │  │  (Internal)     │  │  (Internal)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   EventStore    │  │     Kafka       │  │   Prometheus    │
│  (Internal)     │  │  (Internal)     │  │  (Internal)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Execution Model

### Host System (Secure)
- **Makefile**: Only executable on host
- **Docker commands**: Container orchestration
- **Environment files**: Configuration management
- **Volume mounts**: Data persistence

### Containerized Execution
- **Python scripts**: All run inside `trading-cli` container
- **Testing**: All tests run in isolated containers
- **Development**: All development tools in containers
- **CLI operations**: Internal service communication

## Usage Examples

### Running Scripts (Secure)
```bash
# ❌ OLD WAY (Insecure - runs on host)
python run_backtest.py

# ✅ NEW WAY (Secure - runs in container)
make run-backtest
# or
docker-compose -f docker-compose.dev.yml run --rm trading-cli python run_backtest.py
```

### Testing (Secure)
```bash
# ❌ OLD WAY (Insecure)
python -m pytest tests/

# ✅ NEW WAY (Secure)
make test
# or
docker-compose -f docker-compose.dev.yml run --rm trading-cli python -m pytest tests/
```

### Development (Secure)
```bash
# ❌ OLD WAY (Insecure)
python -m black src/
python -m flake8 src/

# ✅ NEW WAY (Secure)
make format
make lint
```

### CLI Operations (Secure)
```bash
# Internal service communication via CLI container
make cli-health
make cli-portfolio
make cli-market-data SYMBOL=AAPL
```

## Security Benefits

### 1. Code Isolation
- **No Python execution on host**
- **Isolated dependencies per container**
- **No host system contamination**
- **Reproducible environments**

### 2. Network Security
- **Internal service communication only**
- **No direct external access to databases**
- **Controlled API exposure**
- **Docker network isolation**

### 3. Resource Control
- **Container resource limits**
- **Process isolation**
- **File system isolation**
- **Memory and CPU constraints**

### 4. Audit Trail
- **All operations through Makefile**
- **Docker logs for all executions**
- **Container-level monitoring**
- **Clear execution boundaries**

## Development Workflow

### 1. Setup (Host)
```bash
make setup-dev          # Create .env and directories
make docker-build       # Build container images
make docker-up          # Start all services
```

### 2. Development (Containerized)
```bash
make test               # Run tests in container
make lint               # Run linting in container
make format             # Format code in container
make run-backtest       # Run backtests in container
```

### 3. Operations (Containerized)
```bash
make cli-health         # Check service health
make cli-portfolio      # Get portfolio data
make cli-market-data SYMBOL=AAPL  # Get market data
```

### 4. Monitoring (Host)
```bash
make docker-logs        # View container logs
make docker-shell SERVICE=api-gateway  # Debug containers
make status             # Check system status
```

## Kubernetes Deployment

### Secure Kubernetes Architecture
- **All pods run in isolated namespace**
- **Internal service communication**
- **Secrets management**
- **Resource limits and quotas**

### Deployment Commands
```bash
make kube-deploy-all    # Deploy all components
make kube-status        # Check pod status
make kube-logs          # View logs
make kube-clean         # Clean up resources
```

## Best Practices

### 1. Always Use Makefile
- **Never run Python scripts directly on host**
- **Use `make` commands for all operations**
- **Leverage containerized execution**

### 2. Environment Management
- **Use `.env` files for configuration**
- **Never hardcode secrets**
- **Use Docker secrets or Kubernetes secrets**

### 3. Development
- **Use `make docker-shell` for debugging**
- **Run all tests in containers**
- **Use CLI container for internal operations**

### 4. Monitoring
- **Monitor container logs**
- **Use health checks**
- **Track resource usage**

## Troubleshooting

### Common Issues

#### Container Not Starting
```bash
make docker-logs SERVICE=service-name
make docker-shell SERVICE=service-name
```

#### Permission Issues
```bash
# Ensure proper file permissions
chmod 755 scripts/
chmod 644 .env
```

#### Network Issues
```bash
# Check Docker network
docker network ls
docker network inspect trading-system_default
```

#### Resource Issues
```bash
# Check container resources
docker stats
make docker-logs
```

## Security Checklist

- [ ] All Python scripts run in containers
- [ ] No direct host execution
- [ ] Internal service communication only
- [ ] API Gateway is only external entry point
- [ ] Environment variables properly configured
- [ ] Secrets managed securely
- [ ] Resource limits configured
- [ ] Monitoring and logging enabled
- [ ] Regular security updates
- [ ] Access controls implemented

## Conclusion

This secure architecture ensures that **all code execution is containerized**, providing:
- **Enhanced security** through isolation
- **Reproducible environments** across systems
- **Clear audit trails** for all operations
- **Simplified deployment** and management
- **Reduced attack surface** on host systems

The Makefile serves as the **single point of control** for all operations, ensuring that no unauthorized code execution occurs on the host system. 