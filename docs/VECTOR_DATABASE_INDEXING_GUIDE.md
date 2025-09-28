# Vector Database Indexing Guide

## 🎯 **Overview**

This guide explains how to load information into your Kubernetes vectors database using the Ollama controller to create embeddings and index your system documentation. The system provides intelligent semantic search capabilities across your entire trading system architecture.

## 🏗️ **System Architecture**

### **Components Overview**

```mermaid
graph TB
    A[System Documentation] --> B[Architecture Vectorizer]
    B --> C[Ollama Controller]
    C --> D[Embeddings Generation]
    D --> E[Postgres Vector Storage]
    E --> F[Vector Database]
    F --> G[RAG Chat Services]
    F --> H[AI IDE Service]
    F --> I[Unified Dashboards]
    
    J[Kubernetes Jobs] --> B
    K[Local Scripts] --> B
    L[Background Service] --> B
```

### **Key Services**

1. **Postgres Vector Storage** (`postgres-vector-storage`)
   - Stores vector embeddings using pgvector extension
   - Provides semantic search capabilities
   - Connected to TimescaleDB for metadata

2. **Architecture Vectorizer** (`architecture-vectorizer`)
   - Scans repository for documentation files
   - Processes and chunks content
   - Sends to vector storage for indexing

3. **Ollama Controller** (`ollama-controller`)
   - Generates embeddings using LLM models
   - Handles embedding requests from vectorizer
   - Provides fallback embedding generation

4. **RAG Chat Services**
   - `kubernetes-rag-chat` - Kubernetes-specific knowledge
   - `unified-trading-dashboard` - Trading system knowledge
   - `ai-ide-service` - Development knowledge

## 📁 **What Gets Indexed**

### **File Types Processed**
- **Markdown**: `.md` files (documentation, READMEs, guides)
- **Configuration**: `.yaml`, `.yml` files (Kubernetes, Docker)
- **Code**: `.py`, `.js` files (with docstrings and comments)
- **Scripts**: `.sh` files (automation and setup scripts)
- **Text**: `.txt`, `.rst` files (additional documentation)

### **Directory Priorities**
1. **High Priority**: `docs/`, `k8s/`, `services/`, `src/`
2. **Medium Priority**: Configuration files, scripts
3. **Low Priority**: Generated files, logs

### **Content Categories**
- **Kubernetes**: Deployment configs, service definitions, pod specs
- **Architecture**: System design, service interactions, data flow
- **Trading**: Strategies, backtesting, portfolio management
- **Monitoring**: Grafana dashboards, Prometheus configs, health checks
- **Database**: Schema definitions, migrations, queries
- **API**: Endpoint definitions, service interfaces

## 🚀 **Indexing Process**

### **Method 1: Kubernetes Job (Recommended)**

The system runs periodic jobs to index documentation:

```bash
# Check current vectorization jobs
kubectl get jobs -n trading-system | grep vectorizer

# View job logs
kubectl logs -n trading-system architecture-vectorizer-job-<job-id>

# Manually trigger a new vectorization job
kubectl create job --from=cronjob/architecture-vectorizer-cronjob manual-vectorization-$(date +%s) -n trading-system
```

### **Method 2: Local Script**

For development and testing:

```bash
# Run local vectorization script
cd /Users/abby/code/trading
python scripts/vectorize-repo-locally.py
```

### **Method 3: Background Service**

The architecture vectorizer can run as a continuous service:

```bash
# Deploy as background service
kubectl apply -f k8s/background-vectorization-service-production.yaml

# Check service status
kubectl get pods -n trading-system | grep vectorization
```

## 🔧 **Configuration**

### **Environment Variables**

**Architecture Vectorizer:**
```yaml
VECTOR_STORAGE_URL: "http://postgres-vector-storage:80"
REPO_ROOT: "/app"
VECTORIZE_INTERVAL: "3600"  # 1 hour
RUN_ONCE: "false"  # Set to "true" for one-time runs
```

**Postgres Vector Storage:**
```yaml
DATABASE_URL: "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot"
LLM_PROXY_URL: "http://ollama-controller-api-service.ollama-controller.svc.cluster.local:12001"
```

**Ollama Controller:**
```yaml
OLLAMA_URL: "http://host.docker.internal:11434"
MODEL: "llama3.1:8b-instruct-q6_K"
```

### **Vector Storage Schema**

```sql
-- Vector embeddings table
CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    content_id INTEGER NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vectorization jobs tracking
CREATE TABLE vectorization_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 📊 **Monitoring & Status**

### **Check Vectorization Status**

```bash
# View recent vectorization jobs
kubectl get jobs -n trading-system | grep vectorizer

# Check vector storage service
kubectl get pods -n trading-system | grep postgres-vector

# View vectorization logs
kubectl logs -n trading-system -l app=architecture-vectorizer --tail=50
```

### **Database Queries**

```sql
-- Check vectorization progress
SELECT 
    job_type,
    status,
    progress,
    total_items,
    processed_items,
    started_at,
    completed_at
FROM vectorization_jobs 
ORDER BY created_at DESC 
LIMIT 10;

-- Check indexed content
SELECT 
    content_type,
    COUNT(*) as count,
    MAX(created_at) as last_indexed
FROM vector_embeddings 
GROUP BY content_type 
ORDER BY count DESC;

-- Search for specific content
SELECT 
    content_type,
    metadata->>'file_name' as file_name,
    metadata->>'category' as category,
    created_at
FROM vector_embeddings 
WHERE metadata->>'category' = 'kubernetes'
ORDER BY created_at DESC 
LIMIT 10;
```

## 🔍 **Search & Query**

### **RAG Chat Integration**

The vectorized content is accessible through:

1. **Kubernetes RAG Chat**: `http://localhost:11006`
2. **Unified Trading Dashboard**: `http://localhost:11000`
3. **AI IDE Service**: `http://localhost:11050`

### **API Endpoints**

```bash
# Search vectorized content
curl -X POST http://localhost:11006/api/vectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the trading system work?",
    "limit": 5,
    "namespace": "architecture_trading"
  }'

# Get vectorization stats
curl http://localhost:11006/api/vectors/stats

# Health check
curl http://localhost:11006/health
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Vector Storage Not Running**
   ```bash
   # Deploy vector storage service
   kubectl apply -f k8s/services/postgres-vector-storage.yaml
   
   # Check service status
   kubectl get pods -n trading-system | grep postgres-vector
   ```

2. **Ollama Controller Issues**
   ```bash
   # Check Ollama controller status
   kubectl get pods -n ollama-controller
   
   # Test embedding generation
   curl -X POST http://localhost:12001/api/embed \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test embedding", "task_type": "embedding"}'
   ```

3. **Vectorization Jobs Failing**
   ```bash
   # Check job logs
   kubectl logs -n trading-system architecture-vectorizer-job-<job-id>
   
   # Check vector storage connectivity
   kubectl exec -n trading-system -it <vectorizer-pod> -- curl http://postgres-vector-storage:80/health
   ```

### **Performance Optimization**

1. **Chunk Size Tuning**
   - Adjust `max_chunk_size` in vectorizer (default: 1000 characters)
   - Balance between context preservation and processing speed

2. **Batch Processing**
   - Process files in batches to avoid memory issues
   - Use `VECTORIZATION_BATCH_SIZE` environment variable

3. **Caching**
   - Embeddings are cached to avoid regeneration
   - Clear cache if content changes significantly

## 📈 **Best Practices**

### **Content Organization**

1. **Use Clear File Names**: `KUBERNETES_DEPLOYMENT_GUIDE.md`
2. **Add Metadata**: Include category tags in file headers
3. **Structure Documentation**: Use consistent markdown headers
4. **Keep Content Updated**: Regular re-indexing of changed files

### **Vectorization Strategy**

1. **Incremental Updates**: Only re-index changed files
2. **Category-Based Indexing**: Use namespaces for different content types
3. **Quality Control**: Monitor embedding quality and search results
4. **Regular Maintenance**: Clean up old or duplicate embeddings

### **Search Optimization**

1. **Query Refinement**: Use specific, descriptive search terms
2. **Namespace Filtering**: Search within specific categories when possible
3. **Result Ranking**: Use similarity scores to rank results
4. **Context Building**: Combine multiple search results for better answers

## 🔄 **Maintenance**

### **Regular Tasks**

1. **Weekly**: Check vectorization job status
2. **Monthly**: Review indexed content and search quality
3. **Quarterly**: Update vectorization patterns and categories
4. **As Needed**: Re-index after major documentation updates

### **Monitoring Commands**

```bash
# Daily status check
kubectl get jobs -n trading-system | grep vectorizer | tail -5

# Weekly content review
kubectl exec -n trading-system -it <postgres-vector-pod> -- psql -c "
SELECT content_type, COUNT(*) as count 
FROM vector_embeddings 
GROUP BY content_type 
ORDER BY count DESC;"

# Monthly performance check
kubectl top pods -n trading-system | grep -E "(vector|postgres)"
```

## 📚 **Related Documentation**

- [Architecture RAG Chat Solution](ARCHITECTURE_RAG_CHAT_SOLUTION.md)
- [Kubernetes Learning Guide](KUBERNETES_LEARNING_GUIDE.md)
- [AI IDE Integration Guide](AI_IDE_INTEGRATION_GUIDE.md)
- [Unified Analytics Dashboard Guide](UNIFIED_ANALYTICS_DASHBOARD_GUIDE.md)

---

**Last Updated**: $(date)
**Version**: 1.0
**Maintainer**: Orion AI Assistant










