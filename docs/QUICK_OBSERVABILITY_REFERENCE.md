# 🔍 Quick Observability Reference

## 🚀 Quick Start

### 1. Deploy Observability Stack
```bash
# Deploy complete observability stack
./scripts/setup-observability.sh
```

### 2. Access Dashboards
- **Jaeger UI**: http://localhost:16686
- **Grafana**: http://localhost:11044 (admin/admin)
- **Prometheus**: http://localhost:11190

## 📊 Key Dashboards

### Jaeger UI - Distributed Tracing
- **Search Traces**: Find requests by service, operation, tags
- **Trace Details**: View complete request flow with timing
- **Service Dependencies**: See how services interact
- **Error Analysis**: Identify failed requests

### Grafana - Request Tracing Dashboard
- **Request Flow Overview**: Request volume by service
- **Performance Metrics**: Response times, error rates
- **Bottleneck Detection**: Slow endpoints and services
- **Database Performance**: Query times and connections
- **External API Performance**: Third-party service metrics

## 🔍 Bottleneck Identification

### 1. High Response Times
```promql
# Find slow endpoints
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service, endpoint))

# Top 10 slowest services
topk(10, sum(rate(http_request_duration_seconds_sum[5m])) by (service))
```

### 2. Database Bottlenecks
```promql
# Slow database queries
histogram_quantile(0.95, sum(rate(db_query_duration_seconds_bucket[5m])) by (le, service, table))

# High query volume
sum(rate(db_queries_total[5m])) by (service, table)
```

### 3. External API Issues
```promql
# External API performance
histogram_quantile(0.95, sum(rate(http_client_duration_seconds_bucket[5m])) by (le, target_service))

# External API errors
sum(rate(http_client_errors_total[5m])) by (target_service, error_type)
```

### 4. Message Queue Bottlenecks
```promql
# Queue depth
mq_queue_depth{queue=~".*"}

# Consumer lag
mq_consumer_lag{queue=~".*"}

# Message processing time
histogram_quantile(0.95, sum(rate(mq_message_duration_seconds_bucket[5m])) by (le, queue))
```

## 🛠️ Service Integration

### 1. Add Tracing to Your Service
```python
# In your FastAPI service
from src.utils.tracing_middleware import setup_tracing_middleware
from src.utils.distributed_tracing import trace_request, trace_database_operation

app = FastAPI()
setup_tracing_middleware(app, service_name="your-service")

@app.post("/api/endpoint")
@trace_request(operation="your_operation")
async def your_endpoint():
    pass
```

### 2. Trace Database Operations
```python
@trace_database_operation(operation="select", table="your_table")
async def your_database_operation():
    pass
```

### 3. Trace External API Calls
```python
@trace_external_api_call("external-service", "/api/endpoint")
async def call_external_api():
    pass
```

### 4. Trace Message Queue Operations
```python
@trace_message_queue(operation="publish", queue="your-queue")
async def publish_message():
    pass
```

## 📈 Key Metrics to Monitor

### Request Metrics
- `http_requests_total{service="your-service"}`
- `http_request_duration_seconds{service="your-service"}`
- `http_requests_total{status=~"4..|5.."}` (error rate)

### Database Metrics
- `db_queries_total{service="your-service"}`
- `db_query_duration_seconds{service="your-service"}`
- `db_connections_active{service="your-service"}`

### External API Metrics
- `http_client_requests_total{target_service="external-api"}`
- `http_client_duration_seconds{target_service="external-api"}`
- `http_client_errors_total{target_service="external-api"}`

### Message Queue Metrics
- `mq_messages_total{queue="your-queue"}`
- `mq_message_duration_seconds{queue="your-queue"}`
- `mq_queue_depth{queue="your-queue"}`

## 🚨 Common Issues & Solutions

### 1. No Traces in Jaeger
```bash
# Check Jaeger deployment
kubectl get pods -n trading-system -l app=jaeger

# Check service environment variables
kubectl exec deployment/your-service -n trading-system -- env | grep TRACING

# Verify tracing is enabled
kubectl get configmap jaeger-config -n trading-system -o yaml
```

### 2. High Memory Usage
```bash
# Check Jaeger memory usage
kubectl top pods -n trading-system -l app=jaeger

# Adjust memory limits if needed
kubectl patch deployment jaeger -n trading-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"jaeger","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

### 3. Missing Dependencies
```bash
# Install OpenTelemetry dependencies
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-redis opentelemetry-instrumentation-rabbitmq opentelemetry-instrumentation-prometheus-client opentelemetry-exporter-jaeger
```

## 🎯 Performance Optimization

### 1. Sampling in High-Traffic Environments
```bash
# Set environment variable for sampling
export TRACE_SAMPLE_RATE=0.1  # Sample 10% of traces
```

### 2. Batch Processing
```bash
# Configure batch settings
export BATCH_SIZE=100
export BATCH_TIMEOUT=5s
```

### 3. Memory Optimization
```bash
# Adjust Jaeger memory limits
kubectl patch deployment jaeger -n trading-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"jaeger","resources":{"requests":{"memory":"256Mi"},"limits":{"memory":"512Mi"}}}]}}}}'
```

## 📚 Useful Commands

### Check Service Status
```bash
# Check all observability services
kubectl get pods -n trading-system -l app=jaeger
kubectl get pods -n trading-system -l app=grafana
kubectl get pods -n trading-system -l app=prometheus

# Check service logs
kubectl logs deployment/jaeger -n trading-system
kubectl logs deployment/grafana -n trading-system
kubectl logs deployment/prometheus -n trading-system
```

### Port Forwarding
```bash
# Start port forwarding
kubectl port-forward service/jaeger 16686:16686 -n trading-system &
kubectl port-forward service/grafana 11044:3000 -n trading-system &
kubectl port-forward service/prometheus 11190:11190 -n trading-system &

# Stop port forwarding
pkill -f 'kubectl port-forward'
```

### Restart Services
```bash
# Restart Grafana after dashboard changes
kubectl rollout restart deployment/grafana -n trading-system

# Restart Jaeger if needed
kubectl rollout restart deployment/jaeger -n trading-system
```

## 🔗 Quick Links

- **Jaeger UI**: http://localhost:16686
- **Grafana**: http://localhost:11044
- **Prometheus**: http://localhost:11190
- **Full Documentation**: docs/OBSERVABILITY_GUIDE.md
- **Example Implementation**: services/trading-service/main_with_tracing.py

## 🎯 Next Steps

1. **Deploy the observability stack**: `./scripts/setup-observability.sh`
2. **Integrate tracing into your services**: Use the provided utilities
3. **Monitor performance**: Use the dashboards to identify bottlenecks
4. **Set up alerts**: Configure alerts for performance issues
5. **Optimize performance**: Use tracing data to improve system performance

This quick reference provides everything you need to get started with observability and request tracking in your trading system.


