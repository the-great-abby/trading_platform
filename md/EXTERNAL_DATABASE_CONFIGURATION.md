# 🗄️ External Database Configuration Guide

## 🎯 **Overview**

Your AI IDE integration has been updated to use externalized databases instead of internal ones. This provides better scalability, reliability, and separation of concerns.

## 🏗️ **External Database Architecture**

### **Database Services:**
- **TimescaleDB External**: `postgres-timescale-external.postgres-infra.svc.cluster.local:5432`
- **Apache AGE External**: `postgres-age-external.postgres-infra.svc.cluster.local:5432`
- **Vector Storage External**: `postgres-vector-external.postgres-infra.svc.cluster.local:5432`
- **Regular PostgreSQL External**: `postgres-regular-external.postgres-infra.svc.cluster.local:5432`

## 🔧 **AI IDE Service Configuration**

### **Updated Configuration:**
```yaml
# In k8s/ai-ide-service.yaml
env:
- name: VECTOR_STORAGE_URL
  value: "http://postgres-vector-external.postgres-infra.svc.cluster.local:5432"
```

### **Service Code:**
```python
# In services/ai-ide-service/main.py
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-external.postgres-infra.svc.cluster.local:5432")
```

## 🚀 **Deployment Steps**

### **1. Verify External Databases:**
```bash
# Check if external databases are accessible
kubectl get svc -n postgres-infra

# Test connectivity to vector storage
kubectl run test-connectivity --image=curlimages/curl --rm -it --restart=Never -- \
  curl -v http://postgres-vector-external.postgres-infra.svc.cluster.local:5432/health
```

### **2. Deploy AI IDE Service:**
```bash
# Build and deploy with external database configuration
cd services/ai-ide-service
docker build -t localhost:32000/ai-ide-service:latest .
docker push localhost:32000/ai-ide-service:latest

# Deploy to Kubernetes
kubectl apply -f k8s/ai-ide-service.yaml

# Verify deployment
kubectl get pods -n trading-system | grep ai-ide-service
```

### **3. Test External Database Connection:**
```bash
# Port forward for testing
kubectl port-forward service/ai-ide-service 11050:11050 -n trading-system

# Test health endpoint
curl http://localhost:11050/api/health

# Test vector search
curl -X POST http://localhost:11050/api/query-architecture \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our trading system architecture?"}'
```

## 🔍 **Database Connectivity Testing**

### **Test Vector Storage:**
```bash
# From within cluster
kubectl run test-vector --image=curlimages/curl --rm -it --restart=Never -- \
  curl -X POST http://postgres-vector-external.postgres-infra.svc.cluster.local:5432/api/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```

### **Test TimescaleDB:**
```bash
# From within cluster
kubectl run test-timescale --image=postgres:15 --rm -it --restart=Never -- \
  psql -h postgres-timescale-external.postgres-infra.svc.cluster.local -p 5432 -U trading_user -d trading_bot -c "SELECT 1;"
```

### **Test Apache AGE:**
```bash
# From within cluster
kubectl run test-age --image=postgres:15 --rm -it --restart=Never -- \
  psql -h postgres-age-external.postgres-infra.svc.cluster.local -p 5432 -U trading_user -d trading_bot -c "SELECT 1;"
```

## 🚨 **Troubleshooting**

### **Connection Issues:**
```bash
# Check service endpoints
kubectl get endpoints -n postgres-infra

# Check DNS resolution
kubectl run test-dns --image=busybox --rm -it --restart=Never -- \
  nslookup postgres-vector-external.postgres-infra.svc.cluster.local

# Check network connectivity
kubectl run test-ping --image=busybox --rm -it --restart=Never -- \
  ping -c 3 postgres-vector-external.postgres-infra.svc.cluster.local
```

### **AI IDE Service Issues:**
```bash
# Check service logs
kubectl logs deployment/ai-ide-service -n trading-system

# Check service status
kubectl describe deployment ai-ide-service -n trading-system

# Check environment variables
kubectl exec deployment/ai-ide-service -n trading-system -- env | grep VECTOR
```

### **Database Migration Issues:**
```bash
# Check if migration completed
kubectl get jobs -n trading-system | grep migration

# Check migration logs
kubectl logs job/migration-job -n trading-system

# Verify data in external databases
kubectl run verify-data --image=postgres:15 --rm -it --restart=Never -- \
  psql -h postgres-vector-external.postgres-infra.svc.cluster.local -p 5432 -U trading_user -d trading_bot -c "SELECT COUNT(*) FROM vectors;"
```

## 🔧 **Configuration Updates**

### **Environment Variables:**
```bash
# Set environment variables for external databases
export VECTOR_STORAGE_URL="http://postgres-vector-external.postgres-infra.svc.cluster.local:5432"
export TIMESCALE_URL="postgres-timescale-external.postgres-infra.svc.cluster.local:5432"
export AGE_URL="postgres-age-external.postgres-infra.svc.cluster.local:5432"
export REGULAR_POSTGRES_URL="postgres-regular-external.postgres-infra.svc.cluster.local:5432"
```

### **Kubernetes ConfigMaps:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: external-database-config
  namespace: trading-system
data:
  VECTOR_STORAGE_URL: "http://postgres-vector-external.postgres-infra.svc.cluster.local:5432"
  TIMESCALE_URL: "postgres-timescale-external.postgres-infra.svc.cluster.local:5432"
  AGE_URL: "postgres-age-external.postgres-infra.svc.cluster.local:5432"
  REGULAR_POSTGRES_URL: "postgres-regular-external.postgres-infra.svc.cluster.local:5432"
```

## 🎯 **Benefits of External Databases**

### **Scalability:**
- ✅ Independent scaling of database services
- ✅ Better resource allocation
- ✅ Reduced resource contention

### **Reliability:**
- ✅ Dedicated database infrastructure
- ✅ Better backup and recovery
- ✅ Improved monitoring and alerting

### **Security:**
- ✅ Network isolation
- ✅ Dedicated security policies
- ✅ Better access control

### **Maintenance:**
- ✅ Independent database updates
- ✅ Easier troubleshooting
- ✅ Better separation of concerns

## 🚀 **Migration Status**

### **Completed:**
- ✅ AI IDE Service updated to use external vector storage
- ✅ Configuration files updated
- ✅ Documentation updated

### **Next Steps:**
1. **Verify Migration**: Ensure all data has been migrated to external databases
2. **Test Connectivity**: Verify all services can connect to external databases
3. **Update Other Services**: Update remaining services to use external databases
4. **Cleanup**: Remove old internal database configurations

## 🔍 **Verification Checklist**

- [ ] External databases are accessible from trading-system namespace
- [ ] AI IDE service can connect to vector storage
- [ ] Vector search functionality works
- [ ] Architecture queries return results
- [ ] Code analysis works with external context
- [ ] All database connections are stable
- [ ] Performance is acceptable
- [ ] Monitoring is in place

## 📚 **Additional Resources**

- **Database Migration Guide**: Check your migration documentation
- **Network Policies**: Ensure proper network access between namespaces
- **Service Discovery**: Verify DNS resolution for external services
- **Monitoring**: Set up monitoring for external database connections

Your AI IDE integration is now configured to use external databases for better scalability and reliability! 🚀
