# Backtest Test Validation Framework

## Overview

The Backtest Test Validation Framework is a comprehensive system designed to ensure the trustworthiness and reliability of backtest scripts in the trading system. It addresses the core requirement of bringing backtest scripts under proper quality control through systematic validation, testing, and monitoring.

## Problem Statement

Previously, backtest scripts in the trading system did not go through a normal testing process, leading to occasional issues and trustworthiness concerns. This framework provides:

- **Systematic Validation**: All backtest scripts are automatically discovered and validated
- **Isolated Execution**: Scripts run in complete isolation to prevent interference
- **Result Verification**: Comprehensive validation against expected metrics with configurable tolerances
- **Quality Assurance**: Standardized testing process ensures consistency and reliability

## Architecture

### Core Components

1. **Script Discovery Service** (`src/validation/discovery/`)
   - Automatically discovers backtest scripts using configurable patterns
   - Extracts metadata and validates script structure
   - Supports multiple script types (backtest, simulation, etc.)

2. **Script Execution Service** (`src/validation/execution/`)
   - Executes scripts in isolated subprocess environments
   - Configurable timeouts and resource limits
   - Support for both synchronous and asynchronous execution

3. **Result Validation Service** (`src/validation/validation/`)
   - Validates execution results against expected metrics
   - Configurable tolerance levels for floating-point comparisons
   - Multiple validation strategies (exact, tolerance, range)

4. **Batch Validation Service** (`src/validation/execution/`)
   - Parallel execution of multiple script validations
   - Progress tracking and status monitoring
   - Comprehensive batch reporting

5. **Report Generation Service** (`src/validation/reporting/`)
   - Generates comprehensive validation reports
   - Multiple output formats (JSON, HTML, PDF)
   - Includes metrics, charts, and detailed analysis

### Integration Services

1. **Database Integration** (`src/validation/integration/`)
   - External database connectivity with retry logic
   - Circuit breaker patterns for resilience
   - Health monitoring and connection management

2. **Logging Integration** (`src/validation/integration/`)
   - Structured logging with JSON formatting
   - Correlation IDs for request tracking
   - Integration with existing trading system logging

3. **Metrics Collection** (`src/validation/integration/`)
   - Prometheus metrics for monitoring and alerting
   - Custom metrics for validation operations
   - Performance monitoring and optimization

### API Layer

1. **REST API** (`src/validation/api/`)
   - Complete REST API with OpenAPI documentation
   - Script discovery, validation, and batch operation endpoints
   - Real-time status monitoring and progress tracking

2. **CLI Interface** (`src/validation/cli/`)
   - Command-line interface for validation operations
   - Integration with existing development workflows
   - Support for automation and scripting

3. **Pytest Plugin** (`src/validation/plugin/`)
   - Integration with existing pytest framework
   - Custom markers and test collection
   - Seamless integration with CI/CD pipelines

## Quick Start

### Prerequisites

- Python 3.11+
- Kubernetes cluster with trading-system namespace
- External PostgreSQL database
- Docker and kubectl

### Installation

1. **Build and Deploy**
   ```bash
   # Build validation framework Docker image
   make validation-build
   
   # Deploy to Kubernetes
   make validation-deploy
   
   # Port forward for local access
   make validation-port-forward
   ```

2. **Verify Installation**
   ```bash
   # Check health
   make validation-health
   
   # Test API
   curl -s http://localhost:11080/health | jq
   ```

### Basic Usage

1. **Discover Backtest Scripts**
   ```bash
   # Using CLI
   make validation-discover
   
   # Using API
   curl -s http://localhost:11080/api/v1/scripts/discover | jq
   ```

2. **Validate Individual Scripts**
   ```bash
   # Using CLI
   make validation-validate SCRIPT_ID=my_backtest_script
   
   # Using API
   curl -X POST http://localhost:11080/api/v1/validation/execute \
     -H "Content-Type: application/json" \
     -d '{"script_id": "my_backtest_script"}'
   ```

3. **Run Batch Validation**
   ```bash
   # Using CLI
   make validation-batch
   
   # Using API
   curl -X POST http://localhost:11080/api/v1/batch/execute \
     -H "Content-Type: application/json" \
     -d '{"script_ids": ["script1", "script2", "script3"]}'
   ```

4. **Generate Reports**
   ```bash
   # Using CLI
   make validation-report
   
   # Using API
   curl -X POST http://localhost:11080/api/v1/reports/generate \
     -H "Content-Type: application/json" \
     -d '{"report_type": "summary", "format": "json"}'
   ```

## Configuration

### Environment Variables

The framework uses environment variables for configuration. Key variables include:

```bash
# Discovery Configuration
VALIDATION_DEFAULT_DIRECTORY=./backtests
VALIDATION_PATTERNS=["*_backtest*.py", "*_simulation*.py"]
VALIDATION_MAX_DEPTH=3

# Execution Configuration
VALIDATION_DEFAULT_TIMEOUT=300
VALIDATION_MAX_CONCURRENT=5
VALIDATION_MEMORY_LIMIT_MB=1024

# Validation Configuration
VALIDATION_TOLERANCE_RETURN=0.01
VALIDATION_TOLERANCE_SHARPE=0.1
VALIDATION_TOLERANCE_DRAWDOWN=0.05

# Database Configuration
VALIDATION_DB_HOST=postgres.external-namespace.svc.cluster.local
VALIDATION_DB_PORT=5432
VALIDATION_DB_NAME=validation_framework

# API Configuration
VALIDATION_CORS_ORIGINS=["*"]
VALIDATION_RATE_LIMIT_RPM=100
VALIDATION_REQUEST_TIMEOUT=30

# Logging Configuration
VALIDATION_LOG_LEVEL=INFO
VALIDATION_LOG_FORMAT=json
```

### Configuration Files

Configuration can also be managed through Kubernetes ConfigMaps:

```bash
# Update configuration
kubectl apply -f k8s/validation-configmap.yaml

# Restart service to apply changes
kubectl rollout restart deployment/validation-service -n trading-system
```

## API Reference

### Script Discovery Endpoints

- `GET /api/v1/scripts/discover` - Discover backtest scripts
- `GET /api/v1/scripts/` - List all scripts with filtering
- `GET /api/v1/scripts/{script_id}` - Get script information
- `POST /api/v1/scripts/{script_id}/refresh` - Refresh script metadata

### Validation Endpoints

- `POST /api/v1/validation/execute` - Execute validation
- `GET /api/v1/validation/status/{script_id}` - Get validation status
- `GET /api/v1/validation/results/{script_id}` - Get validation results
- `DELETE /api/v1/validation/cancel/{script_id}` - Cancel validation

### Batch Validation Endpoints

- `POST /api/v1/batch/execute` - Execute batch validation
- `GET /api/v1/batch/status/{batch_id}` - Get batch status
- `GET /api/v1/batch/results/{batch_id}` - Get batch results
- `DELETE /api/v1/batch/cancel/{batch_id}` - Cancel batch validation

### Report Generation Endpoints

- `POST /api/v1/reports/generate` - Generate validation report
- `GET /api/v1/reports/{report_id}` - Get generated report
- `GET /api/v1/reports/{report_id}/download` - Download report file
- `GET /api/v1/reports/` - List generated reports

### Configuration Endpoints

- `GET /api/v1/config/` - List configurations
- `POST /api/v1/config/` - Create configuration
- `GET /api/v1/config/{config_id}` - Get configuration
- `PUT /api/v1/config/{config_id}` - Update configuration
- `DELETE /api/v1/config/{config_id}` - Delete configuration

### Result Retrieval Endpoints

- `GET /api/v1/results/` - Query validation results
- `GET /api/v1/results/{script_id}/latest` - Get latest result
- `GET /api/v1/results/{script_id}/history` - Get result history
- `GET /api/v1/results/{script_id}/metrics` - Get script metrics
- `GET /api/v1/results/comparison/{script1}/{script2}` - Compare results

## Testing

### Running Tests

```bash
# Run all validation tests
make validation-test

# Run specific test categories
make validation-test-discovery
make validation-test-execution
make validation-test-api
make validation-test-integration

# Run with coverage
pytest tests/ -m validation --cov=src/validation --cov-report=html
```

### Test Categories

- **Contract Tests**: API contract validation
- **Integration Tests**: End-to-end validation workflows
- **Unit Tests**: Individual component testing
- **Performance Tests**: Load and performance testing

## Monitoring

### Health Checks

```bash
# Check service health
make validation-health

# Check specific endpoints
curl -s http://localhost:11080/health | jq
curl -s http://localhost:11080/health/ready | jq
```

### Metrics

```bash
# Get Prometheus metrics
make validation-metrics

# View metrics in browser
open http://localhost:11080/metrics
```

### Logs

```bash
# View service logs
make validation-logs

# View logs in Kubernetes
kubectl logs -f deployment/validation-service -n trading-system
```

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   - Check Kubernetes deployment status: `kubectl get pods -n trading-system`
   - Check logs: `kubectl logs deployment/validation-service -n trading-system`
   - Verify configuration: `kubectl describe configmap validation-configmap -n trading-system`

2. **Database Connection Issues**
   - Verify database connectivity: `kubectl exec -it deployment/validation-service -n trading-system -- curl -s http://localhost:8000/health`
   - Check database configuration in secrets
   - Verify external database is accessible

3. **Validation Failures**
   - Check script syntax and dependencies
   - Verify timeout settings are appropriate
   - Review validation tolerance levels

4. **Performance Issues**
   - Monitor resource usage: `kubectl top pods -n trading-system`
   - Adjust concurrent execution limits
   - Check database connection pool settings

### Debug Mode

Enable debug logging:

```bash
# Set debug log level
kubectl set env deployment/validation-service VALIDATION_LOG_LEVEL=DEBUG -n trading-system

# Restart service
kubectl rollout restart deployment/validation-service -n trading-system
```

## Integration with Existing System

### Pytest Integration

The framework integrates with the existing pytest infrastructure:

```bash
# Run validation tests with pytest
pytest tests/ -m validation

# Use validation plugin
pytest tests/ --validation-config=config.json
```

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Validation Framework Tests
  run: |
    make validation-build
    make validation-test
    make validation-dev-lint
```

### Trading System Integration

The framework integrates with the existing trading system:

- Uses centralized configuration from `src/utils/trading_config.py`
- Follows existing logging and monitoring patterns
- Integrates with existing Kubernetes infrastructure
- Uses external database connectivity pattern

## Best Practices

### Script Development

1. **Naming Conventions**: Use `*_backtest*.py` or `*_simulation*.py` patterns
2. **Metadata**: Include proper docstrings and metadata
3. **Error Handling**: Implement proper error handling and logging
4. **Resource Management**: Be mindful of memory and CPU usage
5. **Dependencies**: Keep dependencies minimal and documented

### Configuration Management

1. **Environment Variables**: Use environment variables for configuration
2. **Secrets**: Store sensitive data in Kubernetes secrets
3. **ConfigMaps**: Use ConfigMaps for non-sensitive configuration
4. **Validation**: Validate configuration on startup

### Monitoring and Alerting

1. **Health Checks**: Implement comprehensive health checks
2. **Metrics**: Use Prometheus metrics for monitoring
3. **Logging**: Use structured logging with correlation IDs
4. **Alerting**: Set up alerts for critical failures

## Contributing

### Development Setup

```bash
# Set up development environment
make validation-dev-setup

# Run development tests
make validation-dev-test

# Lint and format code
make validation-dev-lint
make validation-dev-format
```

### Code Standards

- Follow existing code style and conventions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints and docstrings

## License

This framework is part of the trading system and follows the same licensing terms.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs and metrics
3. Check the API documentation at `http://localhost:11080/docs`
4. Contact the development team

---

*This documentation is automatically updated with the framework implementation.*

