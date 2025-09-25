# Ollama Controller Port Map

## Overview
This document maps all services, ports, and endpoints within the `ollama-controller` namespace for easy reference and troubleshooting.

## Services and Ports

### Core Services

| Service Name | Type | Internal Port | External Port | Purpose | Status |
|--------------|------|---------------|---------------|---------|---------|
| `ollama-controller-api-service` | ClusterIP | 12001 | 12001 | Main API service for LLM requests | ✅ Active |
| `ollama-internal` | ClusterIP | 11434 | - | Internal Ollama service access | ✅ Active |
| `ollama-host` | ExternalName | 11434 | - | External Ollama service (host.docker.internal) | ✅ Active |
| `ollama-local-forward` | ClusterIP | 11434 | - | Port forward to local Ollama instance | ✅ Active |

### Database Services

| Service Name | Type | Internal Port | External Port | Purpose | Status |
|--------------|------|---------------|---------------|---------|---------|
| `postgres` | ClusterIP | 5432 | - | PostgreSQL database for request tracking | ⚠️ **DEPRECATED** - Use external postgres |
| `rabbitmq` | ClusterIP | 5672 | - | Message queue for async processing | ⚠️ **DEPRECATED** - Use external rabbitmq |

### External Database Services (Recommended)

| Service Name | Namespace | Internal Port | Purpose | Status |
|--------------|-----------|---------------|---------|---------|
| `postgres-timescale-external` | `postgres-infra` | 5432 | External PostgreSQL for request tracking | ✅ Active |
| `postgres-vector-external` | `postgres-infra` | 5432 | External PostgreSQL for vector storage | ✅ Active |
| `rabbitmq-external` | `trading-system` | 5672 | External RabbitMQ for message queue | ✅ Active |

### Pods and Deployments

| Pod Name | Image | Ports | Purpose | Status |
|----------|-------|-------|---------|---------|
| `ollama-74687d54c8-dwm5r` | `ollama/ollama:latest` | 11434 | Core Ollama service | ✅ Running |
| `ollama-controller-api-65c744f74b-45sxv` | `localhost:32000/ollama-controller-api:latest` | 12001 | API service | ✅ Running |
| `ollama-controller-worker-7b68fc4d5-brf7v` | `localhost:32000/ollama-controller-worker:latest` | - | Background worker | ✅ Running |
| `ollama-local-forward-8695648598-7lqct` | `alpine/socat:latest` | 11434 | Port forward service | ✅ Running |
| `ollama-proxy-6d9b988544-5lsrj` | `localhost:32000/ollama-proxy:latest` | 11434 | Proxy service | ✅ Running |
| `postgres-0` | `postgres:16` | 5432 | Database | ⚠️ **DEPRECATED** - Use external postgres |
| `rabbitmq-0` | `rabbitmq:3-management` | 5672, 15672 | Message queue | ⚠️ **DEPRECATED** - Use external rabbitmq |

## Port Forwarding Commands

### External Access (from localhost)
```bash
# Ollama Controller API (Main service)
kubectl port-forward svc/ollama-controller-api-service 12001:12001 -n ollama-controller

# Direct Ollama service access
kubectl port-forward pod/ollama-74687d54c8-dwm5r 11434:11434 -n ollama-controller

# Ollama Proxy service
kubectl port-forward svc/ollama-proxy 11435:11434 -n ollama-controller
```

### Internal Service URLs (within Kubernetes)
```bash
# Ollama Controller API
http://ollama-controller-api-service.ollama-controller.svc.cluster.local:12001

# Ollama service (internal)
http://ollama-internal.ollama-controller.svc.cluster.local:11434

# Ollama service (external)
http://ollama-host.ollama-controller.svc.cluster.local:11434

# Ollama local forward
http://ollama-local-forward.ollama-controller.svc.cluster.local:11434
```

## API Endpoints

### Ollama Controller API (Port 12001)
- `POST /api/generate` - Generate text completions
- `POST /api/embeddings` - Generate embeddings
- `GET /api/status/{request_id}` - Check request status
- `GET /api/v1/health` - Health check
- `GET /api/queue` - View request queue

### Ollama Service (Port 11434)
- `POST /api/generate` - Generate text completions
- `POST /api/embeddings` - Generate embeddings
- `GET /api/tags` - List available models
- `POST /api/pull` - Pull a model

## Configuration

### Environment Variables
- `OLLAMA_BASE_URL`: Points to internal Ollama service (`http://ollama-internal:11434`)
- `DATABASE_URL`: PostgreSQL connection string (use external service)
- `RABBITMQ_URL`: RabbitMQ connection string (use external service)

### External Database Configuration (Recommended)

#### PostgreSQL Configuration
```bash
# For request tracking (ollama-controller database)
DATABASE_URL=postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/ollama_controller

# For vector storage (separate database)
VECTOR_DATABASE_URL=postgresql://postgres:postgres@postgres-vector-external.postgres-infra.svc.cluster.local:5432/trading
```

#### RabbitMQ Configuration
```bash
# External RabbitMQ for message queue
RABBITMQ_URL=amqp://guest:guest@rabbitmq-external.trading-system.svc.cluster.local:5672/
```

### Migration Status
- ⚠️ **DEPRECATED**: Internal `postgres` and `rabbitmq` services in ollama-controller namespace
- ✅ **RECOMMENDED**: Use external services from `postgres-infra` and `trading-system` namespaces
- 🔄 **IN PROGRESS**: Update ollama-controller configuration to use external databases

### Models Available
- `nomic-embed-text:latest` - For embeddings
- `phi3:mini` - Small language model
- `gpt-oss:20b` - Large language model (requires 12.5GB RAM)

## Troubleshooting

### Common Issues

1. **Database Connection Refused**
   - **Symptom**: `ConnectionRefusedError: [Errno 111] Connection refused`
   - **Cause**: Using deprecated internal PostgreSQL pod (unhealthy)
   - **Fix**: Update configuration to use external PostgreSQL service
   - **Recommended**: Use `postgres-timescale-external.postgres-infra.svc.cluster.local:5432`

2. **Service Unavailable (503)**
   - **Symptom**: `{"detail":"Ollama service is not healthy"}`
   - **Cause**: Ollama service health check failing
   - **Fix**: Check Ollama pod logs and model availability

3. **Memory Issues**
   - **Symptom**: `model requires more system memory than is available`
   - **Cause**: Model too large for available memory
   - **Fix**: Use smaller model (phi3:mini) or increase memory limits

### Health Checks

```bash
# Check all pods
kubectl get pods -n ollama-controller

# Check service health
curl http://localhost:12001/api/v1/health

# Check Ollama models
curl http://localhost:11434/api/tags

# Check database
kubectl logs postgres-0 -n ollama-controller
```

## Service Dependencies

```mermaid
graph TD
    A[RAG Chat Service] --> B[Ollama Controller API]
    B --> C[PostgreSQL Database]
    B --> D[RabbitMQ Queue]
    B --> E[Ollama Service]
    E --> F[Ollama Models]
    
    G[Architecture Vectorizer] --> B
    H[PostgreSQL Vector Storage] --> B
```

## Last Updated
- **Date**: 2025-09-11
- **Status**: Internal PostgreSQL database experiencing issues (25 restarts)
- **Root Cause**: Using deprecated internal database instead of external service
- **Next Action**: Update ollama-controller configuration to use external PostgreSQL service
- **Recommended Fix**: Change `DATABASE_URL` to point to `postgres-timescale-external.postgres-infra.svc.cluster.local:5432`

## Notes
- The `ollama-local-forward` service forwards traffic to the Ollama Controller API, not directly to Ollama
- Priority 99 requests are processed first in the queue
- The system supports both synchronous and asynchronous request processing
- All services use the `ollama-controller` namespace
