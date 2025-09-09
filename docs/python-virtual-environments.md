# Python Virtual Environments Architecture

## Overview

This document outlines the Python virtual environment strategy for the trading system project, including all active environments, their purposes, and management procedures.

## Virtual Environment Strategy

The project uses **dedicated virtual environments** for different purposes to ensure:
- **Dependency isolation** between different workflows
- **Resource optimization** for resource-constrained development
- **Clean separation** of concerns
- **Reproducible environments** across different use cases

## Active Virtual Environments

### 1. **Main Development Environment** (`.venv`)
- **Path**: `/Users/abby/code/trading/.venv`
- **Purpose**: Primary development environment for the trading system
- **Python Version**: Python 3.11
- **Dependencies**: Full production dependencies from `requirements.txt`
- **Usage**: 
  - Main application development
  - Production-like testing
  - Service development and debugging
- **Activation**: `source .venv/bin/activate`
- **Status**: ✅ Active (Primary)

### 2. **Test Environment** (`test-env`)
- **Path**: `/Users/abby/code/trading/test-env`
- **Purpose**: Dedicated testing environment with isolated dependencies
- **Python Version**: Python 3.11
- **Dependencies**: 
  - Base dependencies from `requirements.txt`
  - Test-specific packages: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-html`, `pytest-mock`
  - Database testing: `asyncpg`, `redis`, `aio-pika`
  - Development tools: `black`, `flake8`, `mypy`, `pre-commit`
- **Usage**:
  - CQRS testing and validation
  - Unit and integration tests
  - Test database operations
  - Code quality checks
- **Activation**: `source test-env/bin/activate`
- **Status**: ✅ Active (Testing)

### 3. **Kubernetes Job Generator Environment** (`k8s-job-generator-env`)
- **Path**: `/Users/abby/code/trading/k8s-job-generator-env`
- **Purpose**: Specialized environment for Kubernetes job generation and management
- **Python Version**: Python 3.11
- **Dependencies**: Kubernetes-specific packages and job generation tools
- **Usage**:
  - Kubernetes job creation and management
  - Batch processing workflows
  - Container orchestration tasks
- **Activation**: `source k8s-job-generator-env/bin/activate`
- **Status**: ✅ Active (K8s Jobs)

### 4. **Migration Environment** (`migration-env`)
- **Path**: `/Users/abby/code/trading/migration-env`
- **Purpose**: Database migration and schema management
- **Python Version**: Python 3.11
- **Dependencies**: 
  - Alembic for database migrations
  - Database connection libraries
  - Migration-specific tools
- **Usage**:
  - Database schema migrations
  - Data migration scripts
  - Database version management
- **Activation**: `source migration-env/bin/activate`
- **Status**: ✅ Active (Migrations)

## Environment Management

### Setup Scripts

#### Test Environment Setup
```bash
# Automated setup script
./scripts/setup_test_env.sh

# Manual setup
python3 -m venv test-env
source test-env/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-mock
pip install asyncpg redis aio-pika
pip install black flake8 mypy pre-commit
```

#### Environment Verification
```bash
# Verify test environment
source test-env/bin/activate
python -c "import pytest; print(f'pytest version: {pytest.__version__}')"
python -c "import asyncpg; print('asyncpg installed')"
python -c "import redis; print('redis installed')"
python -c "import aio_pika; print('aio-pika installed')"
```

### Environment Isolation

Each virtual environment provides:
- **Complete dependency isolation** from system Python
- **Version-specific package management**
- **Clean installation state** for reproducible builds
- **Resource-efficient** package management

### Resource Optimization

Given the resource constraints of the development environment:
- **Minimal overlap** between environments
- **Shared base dependencies** where possible
- **Environment-specific tools** only when needed
- **Efficient package caching** across environments

## Testing Strategy Integration

### Test Database Isolation
- **Separate database**: `trading_bot_test` (vs `trading_bot` production)
- **Separate Redis DB**: DB 1 (vs DB 0 production)
- **Separate RabbitMQ vhost**: `trading_vhost_test` (vs `trading_vhost` production)

### Test Environment Features
- **Async testing support** with `pytest-asyncio`
- **Coverage reporting** with `pytest-cov`
- **HTML test reports** with `pytest-html`
- **Mocking capabilities** with `pytest-mock`
- **Parallel test execution** with `pytest-xdist`

## Development Workflow

### Daily Development
1. **Main development**: Use `.venv` for application development
2. **Testing**: Switch to `test-env` for running tests
3. **Migrations**: Use `migration-env` for database changes
4. **K8s jobs**: Use `k8s-job-generator-env` for orchestration tasks

### Environment Switching
```bash
# Switch to test environment
deactivate  # if in another env
source test-env/bin/activate

# Run tests
python scripts/run_cqrs_tests.py

# Switch back to main development
deactivate
source .venv/bin/activate
```

## Best Practices

### Environment Management
- **Always activate** the appropriate environment before working
- **Keep environments updated** with latest dependencies
- **Use requirements files** for reproducible environments
- **Document environment-specific** setup procedures

### Testing
- **Use test environment** for all testing activities
- **Isolate test data** from production data
- **Run tests in clean state** before commits
- **Use appropriate test database** configurations

### Resource Management
- **Deactivate unused environments** to free resources
- **Clean up old environments** periodically
- **Monitor environment sizes** and dependencies
- **Use minimal environments** for specific tasks

## Troubleshooting

### Common Issues
1. **Environment not found**: Check path and ensure environment exists
2. **Package conflicts**: Use separate environments for different purposes
3. **Resource constraints**: Deactivate unused environments
4. **Test failures**: Ensure test environment is properly configured

### Environment Reset
```bash
# Reset test environment
rm -rf test-env
./scripts/setup_test_env.sh
```

## Integration with CI/CD

### Automated Testing
- **Test environment** used in CI/CD pipelines
- **Docker-based testing** for complete isolation
- **Environment validation** in deployment scripts
- **Dependency verification** in build processes

### Deployment
- **Production environment** uses main dependencies
- **Test environment** validates before deployment
- **Migration environment** handles database updates
- **K8s environment** manages container orchestration

## Future Considerations

### Scalability
- **Environment templates** for new use cases
- **Automated environment creation** scripts
- **Environment versioning** for reproducibility
- **Cross-platform compatibility** considerations

### Monitoring
- **Environment health checks** and validation
- **Dependency vulnerability scanning**
- **Resource usage monitoring**
- **Environment performance metrics**

---

## Summary

The trading system uses **4 active virtual environments** optimized for different purposes:

1. **`.venv`** - Main development (Primary)
2. **`test-env`** - Testing and validation (New)
3. **`k8s-job-generator-env`** - Kubernetes operations
4. **`migration-env`** - Database migrations

This strategy provides **complete isolation**, **resource efficiency**, and **reproducible environments** while maintaining the flexibility needed for a complex trading system.

**Last Updated**: September 7, 2024
**Status**: ✅ All environments operational and documented
