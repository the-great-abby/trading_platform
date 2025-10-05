# Quickstart: Backtest Test Validation Framework

## Overview

The Backtest Test Validation Framework automatically discovers, executes, and validates backtest scripts to ensure they produce reliable and consistent results. This guide shows you how to get started with the framework.

## Prerequisites

- Python 3.11+
- pytest framework
- Access to the trading system codebase
- Kubernetes cluster (for production deployment)

## Installation

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements-validation.txt

# Install the validation framework
pip install -e .
```

### 2. Configure Environment

```bash
# Set up environment variables
export VALIDATION_DB_HOST="postgres.external-namespace.svc.cluster.local"
export VALIDATION_DB_PORT="5432"
export VALIDATION_DB_NAME="validation_framework"
export VALIDATION_LOG_LEVEL="INFO"
export VALIDATION_MAX_CONCURRENT="5"
```

### 3. Build and Deploy

```bash
# Build validation framework Docker image
make validation-build

# Deploy to Kubernetes
make validation-deploy

# Port forward for local access
make validation-port-forward

# Verify installation
make validation-health
```

## Basic Usage

### 1. Discover Backtest Scripts

```python
from src.validation.discovery.script_discovery import BacktestScriptDiscovery

# Discover all backtest scripts in the codebase
discovery = BacktestScriptDiscovery()
scripts = await discovery.discover_scripts()

print(f"Found {len(scripts)} backtest scripts")
for script in scripts:
    print(f"- {script.script_name}: {script.file_path}")
```

### 2. Run Single Script Validation

```python
from src.validation.execution.script_executor import ScriptExecutor
from src.validation.validation.result_validator import ResultValidator

# Create services
executor = ScriptExecutor()
validator = ResultValidator()

# Execute and validate a specific script
script_path = "/path/to/your_backtest_script.py"
result = await executor.execute_script(script_path=script_path, timeout_seconds=300)

if result.validation_status == "PASSED":
    print(f"✅ Validation passed: {result.metrics}")
else:
    print(f"❌ Validation failed: {result.error_message}")
```

### 3. Run Batch Validation

```python
from src.validation.execution.batch_validator import BatchValidator

# Create batch validator
batch_validator = BatchValidator()

# Validate multiple scripts in parallel
script_ids = ["script1", "script2", "script3"]
results = await batch_validator.validate_batch(
    script_ids=script_ids,
    parallel_execution=True,
    max_concurrent=5
)

# Print summary
total = len(results)
successful = sum(1 for r in results if r.get("status") == "PASSED")
failed = total - successful
print(f"Total: {total}, Passed: {successful}, Failed: {failed}")
```

### 4. Generate Validation Report

```python
from src.validation.reporting.report_generator import ReportGenerator

# Create report generator
report_gen = ReportGenerator()

# Generate comprehensive report
report = await report_gen.generate_report(
    script_ids=["script1", "script2", "script3"],
    report_type="summary",
    format="json",
    include_metrics=True
)

# Print report summary
print(f"Report generated: {report['report_id']}")
print(f"Total scripts: {report['summary']['total_scripts']}")
print(f"Successful: {report['summary']['successful_scripts']}")
```

## Command Line Interface

### Discover Scripts

```bash
# Discover all backtest scripts
make validation-discover

# Discover scripts with filters
python -m src.validation.cli.validation_cli discover --pattern "*_backtest*.py"
```

### Validate Scripts

```bash
# Validate single script
make validation-validate SCRIPT_ID=my_backtest_script

# Validate multiple scripts
make validation-batch

# Validate with custom configuration
python -m src.validation.cli.validation_cli validate --script-id script-id --config custom-config
```

### Generate Reports

```bash
# Generate validation report
make validation-report

# Generate report with analysis
python -m src.validation.cli.validation_cli report --format json --include-metrics
```

## Pytest Integration

### 1. Add to pytest.ini

```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v
    --tb=short
    --validation-plugin
    --validation-config=default
markers =
    backtest_validation: marks tests as backtest validation tests
    slow: marks tests as slow (deselect with '-m "not slow"')
```

### 2. Run Validation Tests

```bash
# Run all validation tests
make validation-test

# Run validation tests with specific markers
pytest -m validation

# Run validation tests for specific components
make validation-test-discovery
make validation-test-execution
make validation-test-api
```

### 3. Custom Validation Test

```python
import pytest
from src.validation.execution.script_executor import ScriptExecutor
from src.validation.validation.result_validator import ResultValidator

@pytest.mark.validation
async def test_strategy_backtest_validation():
    """Test that strategy backtest produces consistent results"""
    
    executor = ScriptExecutor()
    validator = ResultValidator()
    
    # Run validation multiple times
    results = []
    for i in range(3):
        result = await executor.execute_script(
            script_path="/path/to/strategy_script.py",
            timeout_seconds=300
        )
        results.append(result)
    
    # Check consistency
    first_result = results[0]
    for result in results[1:]:
        assert result.metrics["total_return_pct"] == pytest.approx(
            first_result.metrics["total_return_pct"], 
            rel=0.001
        )
        assert result.metrics["trades_count"] == first_result.metrics["trades_count"]
```

## Configuration

### Default Configuration

```python
# Default validation configuration
DEFAULT_CONFIG = {
    "tolerances": {
        "returns_tolerance_pct": 0.1,
        "ratios_tolerance": 0.01,
        "drawdown_tolerance_pct": 0.05,
        "win_rate_tolerance_pct": 0.5
    },
    "timeouts": {
        "quick_test_seconds": 30,
        "standard_test_seconds": 300,
        "comprehensive_test_seconds": 1800,
        "options_test_seconds": 600
    },
    "validation_rules": {
        "require_exact_trade_counts": True,
        "allow_missing_metrics": [],
        "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct"]
    },
    "execution_settings": {
        "parallel_execution": True,
        "max_parallel_jobs": 4,
        "retry_failed_tests": True,
        "max_retries": 2
    }
}
```

### Custom Configuration

```python
# Create custom configuration
custom_config = {
    "name": "Strict Validation",
    "tolerances": {
        "returns_tolerance_pct": 0.05,  # Stricter tolerance
        "ratios_tolerance": 0.005,
        "drawdown_tolerance_pct": 0.02,
        "win_rate_tolerance_pct": 0.25
    },
    "timeouts": {
        "quick_test_seconds": 15,  # Shorter timeouts
        "standard_test_seconds": 180,
        "comprehensive_test_seconds": 900,
        "options_test_seconds": 300
    },
    "validation_rules": {
        "require_exact_trade_counts": True,
        "allow_missing_metrics": [],
        "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate"]
    }
}

# Save custom configuration
from src.validation.config import ConfigManager
config_manager = ConfigManager()
config_id = config_manager.save_config(custom_config)
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Backtest Validation

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM
  workflow_dispatch:

jobs:
  validate-backtests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-testing.txt
    
    - name: Run backtest validation
      run: |
        python -m src.validation.cli validate --batch --all-scripts
    
    - name: Generate validation report
      run: |
        python -m src.validation.cli report --name "CI Validation Report" --all-scripts
    
    - name: Upload validation report
      uses: actions/upload-artifact@v3
      with:
        name: validation-report
        path: validation_report.json
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Validate Backtests') {
            steps {
                sh 'python -m src.validation.cli validate --batch --all-scripts'
            }
        }
        
        stage('Generate Report') {
            steps {
                sh 'python -m src.validation.cli report --name "Jenkins Validation Report" --all-scripts'
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'validation_report.json', fingerprint: true
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'validation_report.html',
                reportName: 'Validation Report'
            ])
        }
    }
}
```

## Monitoring and Alerting

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics for validation framework
validation_requests_total = Counter('validation_requests_total', 'Total validation requests', ['status'])
validation_duration_seconds = Histogram('validation_duration_seconds', 'Validation duration', ['script_type'])
active_validations = Gauge('active_validations', 'Currently active validations')
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Backtest Validation Framework",
    "panels": [
      {
        "title": "Validation Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(validation_requests_total{status=\"success\"}[5m]) / rate(validation_requests_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "Validation Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(validation_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Common Issues

1. **Script Discovery Fails**
   ```bash
   # Check script patterns
   python -m src.validation.cli discover --verbose
   
   # Validate script structure
   python -m src.validation.cli validate --check-script-structure script-id
   ```

2. **Validation Timeout**
   ```bash
   # Increase timeout
   python -m src.validation.cli validate script-id --timeout 600
   
   # Check script performance
   python -m src.validation.cli validate script-id --profile
   ```

3. **Inconsistent Results**
   ```bash
   # Run consistency check
   python -m src.validation.cli validate script-id --consistency-check --runs 5
   
   # Check for race conditions
   python -m src.validation.cli validate script-id --single-threaded
   ```

### Debug Mode

```bash
# Enable debug logging
export VALIDATION_LOG_LEVEL="DEBUG"

# Run with verbose output
python -m src.validation.cli validate script-id --verbose

# Generate debug report
python -m src.validation.cli report --name "Debug Report" --debug
```

## Next Steps

1. **Explore Advanced Features**: Learn about custom validation rules and performance optimization
2. **Integrate with Monitoring**: Set up alerts and dashboards for validation metrics
3. **Customize Configuration**: Create project-specific validation configurations
4. **Extend Framework**: Add support for new script types and validation rules

## Support

- **Documentation**: See `/docs/validation/` for detailed documentation
- **Examples**: Check `/examples/validation/` for usage examples
- **Issues**: Report issues in the project repository
- **Community**: Join the trading system community discussions
