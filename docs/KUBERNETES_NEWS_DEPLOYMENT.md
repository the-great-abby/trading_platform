# 🚀 Kubernetes News System Deployment Guide

This guide shows you how to deploy the historical news system to Kubernetes for production use.

## 🎯 Overview

The news system can run in Kubernetes as:
- **One-time jobs** for initial data fetching
- **CronJobs** for regular news updates
- **Backtest jobs** for news-enhanced backtesting

## 📋 Prerequisites

### 1. **Kubernetes Cluster**
- Working Kubernetes cluster (Docker Desktop, Minikube, or cloud)
- `kubectl` configured and connected
- `trading-system` namespace exists

### 2. **Polygon.io API Key**
```bash
export POLYGON_API_KEY='your_polygon_api_key_here'
```

### 3. **Database Setup**
- PostgreSQL database running in Kubernetes
- `db-secret` with database connection details
- `backtest-data-pvc` for persistent storage

## 🚀 Quick Deployment

### Step 1: Set Up Polygon API Key Secret

```bash
# Run the setup script
./setup_polygon_secret.sh
```

This creates a Kubernetes secret with your Polygon API key.

### Step 2: Deploy News Jobs

```bash
# Deploy the news fetch job
kubectl apply -f k8s/news-fetch-job.yaml

# Deploy the news scanning cronjob
kubectl apply -f k8s/news-scanning-cronjob.yaml

# Deploy the news-enhanced backtest job
kubectl apply -f k8s/news-backtest-job.yaml
```

### Step 3: Monitor Jobs

```bash
# Check job status
kubectl get jobs -n trading-system
kubectl get cronjobs -n trading-system

# View job logs
kubectl logs -n trading-system job/fetch-historical-news
kubectl logs -n trading-system job/news-enhanced-backtest
```

## 📊 Job Types

### 1. **One-Time News Fetch Job** (`news-fetch-job.yaml`)

**Purpose**: Initial fetch of historical news data

**When to use**:
- First-time setup
- Fetching large date ranges
- Bulk data collection

**Deployment**:
```bash
kubectl apply -f k8s/news-fetch-job.yaml
```

**Monitoring**:
```bash
# Check job status
kubectl get job fetch-historical-news -n trading-system

# View logs
kubectl logs -n trading-system job/fetch-historical-news -f
```

### 2. **News Scanning CronJob** (`news-scanning-cronjob.yaml`)

**Purpose**: Regular news updates every 6 hours

**Schedule**: `0 */6 * * *` (every 6 hours)

**When to use**:
- Keeping news data fresh
- Incremental updates
- Continuous data collection

**Deployment**:
```bash
kubectl apply -f k8s/news-scanning-cronjob.yaml
```

**Monitoring**:
```bash
# Check cronjob status
kubectl get cronjob news-scanning-cronjob -n trading-system

# View recent job logs
kubectl get jobs -n trading-system -l app=news-scanner
kubectl logs -n trading-system job/news-scanning-cronjob-<timestamp>
```

### 3. **News-Enhanced Backtest Job** (`news-backtest-job.yaml`)

**Purpose**: Run backtests with news data

**When to use**:
- Testing news-enhanced strategies
- Comparing backtest results with/without news
- Strategy validation

**Deployment**:
```bash
kubectl apply -f k8s/news-backtest-job.yaml
```

**Customization**:
```bash
# Edit job parameters
kubectl edit job news-enhanced-backtest -n trading-system

# Or apply with custom parameters
kubectl patch job news-enhanced-backtest -n trading-system -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "news-backtest",
          "env": [
            {"name": "BACKTEST_SYMBOLS", "value": "AAPL,TSLA,MSFT"},
            {"name": "BACKTEST_START_DATE", "value": "2024-01-01"},
            {"name": "BACKTEST_END_DATE", "value": "2024-01-31"}
          ]
        }]
      }
    }
  }
}'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYGON_API_KEY` | Polygon.io API key | Required |
| `DATABASE_URL` | PostgreSQL connection URL | From secret |
| `LOG_LEVEL` | Logging level | INFO |
| `UPDATE_MODE` | incremental/full | incremental |
| `BACKTEST_SYMBOLS` | Comma-separated symbols | AAPL,TSLA,MSFT,GOOGL |
| `BACKTEST_START_DATE` | Backtest start date | 2024-01-01 |
| `BACKTEST_END_DATE` | Backtest end date | 2024-01-31 |

### Resource Limits

**News Fetch Job**:
- CPU: 250m request, 500m limit
- Memory: 512Mi request, 1Gi limit

**News Scanning CronJob**:
- CPU: 250m request, 500m limit
- Memory: 512Mi request, 1Gi limit

**News Backtest Job**:
- CPU: 500m request, 1000m limit
- Memory: 1Gi request, 2Gi limit

## 📈 Monitoring and Logging

### Check Job Status

```bash
# List all jobs
kubectl get jobs -n trading-system

# List cronjobs
kubectl get cronjobs -n trading-system

# Get detailed job info
kubectl describe job fetch-historical-news -n trading-system
```

### View Logs

```bash
# Follow job logs
kubectl logs -n trading-system job/fetch-historical-news -f

# Get logs from specific pod
kubectl logs -n trading-system <pod-name>

# Get logs from cronjob
kubectl logs -n trading-system job/news-scanning-cronjob-<timestamp>
```

### Check Database

```bash
# Connect to database pod
kubectl exec -it postgres-dev-<pod-id> -n trading-system -- psql -U trading_user -d trading_bot

# Check news tables
\dt historical_news*
SELECT COUNT(*) FROM historical_news;
SELECT symbol, COUNT(*) FROM historical_news GROUP BY symbol ORDER BY COUNT(*) DESC LIMIT 10;
```

## 🛠️ Troubleshooting

### Common Issues

1. **Job Fails to Start**
   ```bash
   # Check pod events
   kubectl describe pod <pod-name> -n trading-system
   
   # Check if secrets exist
   kubectl get secrets -n trading-system
   ```

2. **API Key Issues**
   ```bash
   # Verify secret exists
   kubectl get secret polygon-secret -n trading-system
   
   # Recreate secret
   ./setup_polygon_secret.sh
   ```

3. **Database Connection Issues**
   ```bash
   # Check database pod
   kubectl get pods -n trading-system | grep postgres
   
   # Test database connection
   kubectl exec -it <postgres-pod> -n trading-system -- psql -U trading_user -d trading_bot -c "SELECT 1;"
   ```

4. **Rate Limiting**
   ```bash
   # Check Polygon API limits
   kubectl logs -n trading-system job/fetch-historical-news | grep "rate limit"
   
   # Wait and retry
   kubectl delete job fetch-historical-news -n trading-system
   kubectl apply -f k8s/news-fetch-job.yaml
   ```

### Debug Commands

```bash
# Get job details
kubectl get job fetch-historical-news -n trading-system -o yaml

# Check pod status
kubectl get pods -n trading-system -l app=news-fetch

# View recent events
kubectl get events -n trading-system --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n trading-system
```

## 🔄 Automation

### Create a Deployment Script

```bash
#!/bin/bash
# deploy_news_system.sh

echo "🚀 Deploying News System to Kubernetes"

# Set up secrets
./setup_polygon_secret.sh

# Deploy jobs
kubectl apply -f k8s/news-fetch-job.yaml
kubectl apply -f k8s/news-scanning-cronjob.yaml
kubectl apply -f k8s/news-backtest-job.yaml

# Wait for jobs to complete
echo "⏳ Waiting for initial news fetch to complete..."
kubectl wait --for=condition=complete job/fetch-historical-news -n trading-system --timeout=3600s

echo "✅ News system deployed successfully!"
```

### Schedule Regular Backtests

```bash
# Create a cronjob for regular backtests
kubectl create cronjob news-backtest-weekly \
  --image=trading-bot:latest \
  --schedule="0 2 * * 0" \
  --namespace=trading-system \
  -- python demo_news_backtest.py
```

## 📊 Performance Optimization

### Resource Tuning

```yaml
# For high-volume news fetching
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Parallel Processing

```yaml
# Run multiple news fetch jobs in parallel
parallelism: 3
completions: 10
```

### Storage Optimization

```yaml
# Use faster storage for news data
volumeMounts:
- name: fast-storage
  mountPath: /app/data
volumes:
- name: fast-storage
  persistentVolumeClaim:
    claimName: fast-storage-pvc
```

## 🎉 Success!

Your news system is now running in Kubernetes! You can:

- **Fetch historical news** automatically
- **Keep news data fresh** with regular updates
- **Run news-enhanced backtests** in the cloud
- **Scale resources** based on demand
- **Monitor performance** with Kubernetes tools

The system will provide realistic news data for your backtesting, making your strategies more robust and comprehensive. 