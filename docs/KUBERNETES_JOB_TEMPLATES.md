# Kubernetes Job Templates System

## Overview

This system provides a reusable template-based approach for generating Kubernetes jobs, eliminating the need to create individual YAML files for each job. Instead, you can generate jobs dynamically with customizable parameters.

## Benefits

- **DRY Principle**: No more duplicate job definitions
- **Consistency**: All jobs follow the same structure and best practices
- **Flexibility**: Easy to customize parameters without editing YAML
- **Maintainability**: Centralized template management
- **Version Control**: Generated jobs are tracked in `k8s/generated/`

## Architecture

```
k8s/
├── job-templates/
│   └── base-job-template.yaml    # Base template with placeholders
├── generated/                    # Auto-generated job files
└── [existing job files]
```

## Quick Start

### 0. Setup Environment

```bash
# Run the setup script to create virtual environment
./setup_k8s_job_generator.sh

# Or manually create virtual environment
python3 -m venv k8s-job-generator-env
source k8s-job-generator-env/bin/activate
pip install pyyaml
```

### 1. Basic Backtest Job

```bash
# Generate a basic backtest job
make k8s-job-backtest SCRIPT=run_backtest.py

# Apply directly to Kubernetes
make k8s-job-backtest SCRIPT=run_backtest.py APPLY=true
```

### 2. LLM-Enhanced Backtest

```bash
# Generate backtest with LLM evaluation
make k8s-job-backtest SCRIPT=run_llm_evaluated_backtest.py USE_LLM=true APPLY=true
```

### 3. Custom Parameters

```bash
# Custom symbols and date range
make k8s-job-backtest SCRIPT=run_backtest.py \
  SYMBOLS=AAPL,TSLA,MSFT,GOOGL \
  START_DATE=2024-01-01 \
  END_DATE=2024-01-31 \
  APPLY=true
```

### 4. High-Resource Jobs

```bash
# Resource-intensive backtest
make k8s-job-backtest SCRIPT=run_comprehensive_backtest.py \
  MEMORY_REQUEST=2Gi \
  MEMORY_LIMIT=4Gi \
  CPU_REQUEST=1000m \
  CPU_LIMIT=2000m \
  APPLY=true
```

## Job Types

### Backtest Jobs (`k8s-job-backtest`)

**Purpose**: Run trading strategy backtests

**Parameters**:
- `SCRIPT`: Python script to run
- `SYMBOLS`: Comma-separated stock symbols
- `START_DATE`: Backtest start date (YYYY-MM-DD)
- `END_DATE`: Backtest end date (YYYY-MM-DD)
- `USE_LLM`: Enable LLM evaluation (true/false)
- `MEMORY_REQUEST/LIMIT`: Memory allocation
- `CPU_REQUEST/LIMIT`: CPU allocation

**Examples**:
```bash
# Basic backtest
make k8s-job-backtest SCRIPT=run_backtest.py

# LLM-enhanced with custom symbols
make k8s-job-backtest SCRIPT=run_llm_evaluated_backtest.py \
  USE_LLM=true SYMBOLS=AAPL,TSLA,MSFT

# Portfolio performance test
make k8s-job-backtest SCRIPT=run_portfolio_performance_test.py \
  SYMBOLS=AAPL,TSLA,MSFT,GOOGL,AMZN
```

### Analysis Jobs (`k8s-job-analysis`)

**Purpose**: Run data analysis and reporting

**Parameters**:
- `SCRIPT`: Python script to run
- `MEMORY_REQUEST/LIMIT`: Memory allocation
- `CPU_REQUEST/LIMIT`: CPU allocation

**Examples**:
```bash
# Portfolio analysis
make k8s-job-analysis SCRIPT=analyze_portfolio_performance.py

# Strategy performance analysis
make k8s-job-analysis SCRIPT=analyze_strategy_performance.py
```

### Data Jobs (`k8s-job-data`)

**Purpose**: Data processing and ingestion

**Parameters**:
- `SCRIPT`: Python script to run
- `MEMORY_REQUEST/LIMIT`: Memory allocation
- `CPU_REQUEST/LIMIT`: CPU allocation

**Examples**:
```bash
# Data ingestion
make k8s-job-data SCRIPT=fetch_polygon_data.py

# News data processing
make k8s-job-data SCRIPT=process_news_data.py
```

## Template System

### Base Template Structure

The base template (`k8s/job-templates/base-job-template.yaml`) includes:

- **Standard Environment Variables**: Database, API keys, services
- **Resource Management**: Memory and CPU limits
- **Volume Mounts**: Logs and data volumes
- **Service Account**: Security and permissions
- **Restart Policy**: Never (for jobs)

### Customization Points

1. **Environment Variables**: Add custom env vars via `CUSTOM_ENV_VARS`
2. **Volume Mounts**: Add custom volumes via `CUSTOM_VOLUME_MOUNTS`
3. **Resources**: Adjust memory/CPU via parameters
4. **Labels**: Customize job labels and metadata

## Advanced Usage

### 1. Custom Job Names

```bash
make k8s-job-backtest SCRIPT=run_backtest.py NAME=my-custom-backtest
```

### 2. Custom Output Files

```bash
make k8s-job-backtest SCRIPT=run_backtest.py OUTPUT=my-backtest.yaml
```

### 3. Direct Script Usage

```bash
# Generate job without applying
python3 scripts/generate_k8s_job.py --type backtest --script run_backtest.py

# Apply directly to Kubernetes
python3 scripts/generate_k8s_job.py --type backtest --script run_backtest.py --apply
```

### 4. Batch Job Generation

```bash
# Generate multiple jobs
for script in run_backtest.py run_llm_backtest.py run_portfolio_test.py; do
  make k8s-job-backtest SCRIPT=$script APPLY=true
done
```

## Best Practices

### 1. Naming Conventions

- Use descriptive script names
- Include job type in generated names
- Add timestamps for uniqueness

### 2. Resource Management

- Start with conservative resource limits
- Monitor job performance and adjust
- Use different resource profiles for different job types

### 3. Environment Variables

- Keep sensitive data in secrets
- Use configmaps for non-sensitive configuration
- Document custom environment variables

### 4. Monitoring

```bash
# Check job status
kubectl get jobs -n trading-system

# View job logs
kubectl logs -n trading-system job/<job-name>

# Monitor resource usage
kubectl top pods -n trading-system
```

## Migration from Static Jobs

### Before (Static YAML)
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: backtest-custom
spec:
  template:
    spec:
      containers:
      - name: backtest
        image: trading-system:latest
        command: ["python"]
        args: ["run_backtest.py"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
        # ... many more lines
```

### After (Template-Based)
```bash
make k8s-job-backtest SCRIPT=run_backtest.py APPLY=true
```

## Troubleshooting

### Common Issues

1. **Virtual Environment Issues**
   ```bash
   # Run setup script
   ./setup_k8s_job_generator.sh
   
   # Or manually activate virtual environment
   source k8s-job-generator-env/bin/activate
   ```

2. **Template Not Found**
   ```bash
   # Ensure template directory exists
   ls -la k8s/job-templates/
   ```

3. **Permission Issues**
   ```bash
   # Make script executable
   chmod +x scripts/generate_k8s_job.py
   ```

3. **Resource Limits**
   ```bash
   # Check cluster resources
   kubectl describe nodes
   ```

4. **Job Failures**
   ```bash
   # Check job events
   kubectl describe job <job-name> -n trading-system
   
   # Check pod logs
   kubectl logs -n trading-system job/<job-name>
   ```

## Future Enhancements

1. **CronJob Templates**: For recurring jobs
2. **Service Templates**: For long-running services
3. **ConfigMap Integration**: Dynamic configuration
4. **Job Dependencies**: Sequential job execution
5. **Monitoring Integration**: Prometheus/Grafana metrics

## Examples Directory

See `k8s/generated/` for examples of generated jobs and their parameters. 