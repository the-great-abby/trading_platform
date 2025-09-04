# 🚀 Space Trading Station Deployment Guide - Docker Compose & Kubernetes

This guide covers deploying the Space Trading Station using Docker Compose for development and Kubernetes for production.

## 📋 Mission Control Prerequisites

### For Docker Compose
- Docker Desktop or Docker Engine
- Docker Compose
- At least 8GB RAM available for Docker

### For Kubernetes
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl CLI tool
- Helm (optional, for advanced deployments)

## 🐳 Docker Compose Deployment

### 1. Mission Control Environment Setup

```bash
# Copy environment template
cp config.env.example .env

# Edit with your configuration
nano .env
```

### 2. Deploy Space Station Infrastructure

```bash
# Start databases and message brokers
docker-compose up -d write-db read-db eventstore kafka zookeeper redis influxdb

# Wait for services to be ready
sleep 30
```

### 3. Deploy Space Station Modules

```bash
# Build and start all services
docker-compose up -d --build

# Or use the deployment script
./deploy.sh
```

### 4. Verify Space Station Status

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f trading-service

# Test health endpoints
curl http://localhost:8000/health
```

### 5. Access Mission Control Services

- **Mission Control Gateway**: http://localhost:8000
- **Command API**: http://localhost:8001
- **Query API**: http://localhost:8002
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kibana**: http://localhost:5601
- **Prometheus**: http://localhost:9090
- **EventStore**: http://localhost:2113

## ☸️ Kubernetes Space Station Deployment

### 1. Cluster Setup

```bash
# For local development with minikube
minikube start --memory=8192 --cpus=4

# For production cluster
# Use your cloud provider's managed Kubernetes service
```

### 2. Create Space Station Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3. Deploy Secrets and ConfigMaps

```bash
# Update secrets with your actual values
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Space Station Infrastructure

```bash
# Deploy databases and message brokers
kubectl apply -f k8s/infrastructure/ -n trading-system
```

### 5. Deploy Space Station Modules

```bash
# Deploy all services
kubectl apply -f k8s/ -n trading-system

# Or use the deployment script
./deploy.sh --k8s
```

### 6. Deploy Ingress (Optional)

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml
```

### 7. Verify Space Station Deployment

```bash
# Check pods
kubectl get pods -n trading-system

# Check services
kubectl get services -n trading-system

# Check ingress
kubectl get ingress -n trading-system

# View logs
kubectl logs -f deployment/trading-service -n trading-system
```

## 🔧 Mission Control Configuration

### Environment Variables

```bash
# Required for Public API
PUBLIC_API_KEY=your_public_api_key
PUBLIC_API_SECRET=your_public_api_secret
PUBLIC_BASE_URL=https://api.public.com
PUBLIC_USERNAME=your_username
PUBLIC_PASSWORD=your_password

# Database Configuration
DATABASE_URL_WRITE=postgresql://postgres:password@write-db:5432/trading_write
DATABASE_URL_READ=postgresql://postgres:password@read-db:5432/trading_read

# Event Store
EVENT_STORE_URL=eventstore:2113

# Message Broker
KAFKA_BROKERS=kafka:9092

# Cache
REDIS_URL=redis://redis.redis.svc.cluster.local:6379

# Time Series Database
INFLUXDB_URL=http://influxdb:8086
```

### Scaling Space Station Modules

```bash
# Docker Compose
docker-compose up -d --scale trading-service=3

# Kubernetes
kubectl scale deployment trading-service --replicas=3 -n trading-system
```

## 📊 Mission Control Monitoring & Logging

### Prometheus Metrics

```bash
# Access Prometheus
open http://localhost:9090

# Query metrics
# trading_orders_total
# trading_trades_total
# trading_portfolio_value
```

### Grafana Dashboards

```bash
# Access Grafana
open http://localhost:3000

# Default credentials: admin/admin
```

### ELK Stack

```bash
# Access Kibana
open http://localhost:5601

# View logs from all services
# Create index patterns for log analysis
```

## 🔍 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check logs
   docker-compose logs [service-name]
   
   # Check resource usage
   docker stats
   ```

2. **Database connection issues**
   ```bash
   # Test database connectivity
   docker-compose exec write-db psql -U postgres -d trading_write
   ```

3. **Kafka connectivity**
   ```bash
   # Check Kafka topics
   docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

4. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop > Settings > Resources > Memory: 8GB+
   ```

### Health Checks

```bash
# Docker Compose
curl http://localhost:8000/health

# Kubernetes
kubectl get pods -n trading-system -o wide
kubectl describe pod [pod-name] -n trading-system
```

## 🔄 Updates & Maintenance

### Rolling Updates

```bash
# Docker Compose
docker-compose pull
docker-compose up -d

# Kubernetes
kubectl set image deployment/trading-service trading-service=new-image:tag -n trading-system
```

### Database Migrations

```bash
# Run migrations
docker-compose exec trading-service python -m alembic upgrade head

# Kubernetes
kubectl exec -it deployment/trading-service -n trading-system -- python -m alembic upgrade head
```

### Backup & Restore

```bash
# Backup databases
docker-compose exec write-db pg_dump -U postgres trading_write > backup_write.sql
docker-compose exec read-db pg_dump -U postgres trading_read > backup_read.sql

# Restore databases
docker-compose exec -T write-db psql -U postgres trading_write < backup_write.sql
```

## 🚀 Production Considerations

### Security
- Use secrets management for sensitive data
- Enable TLS/SSL for all communications
- Implement proper authentication and authorization
- Regular security updates

### Performance
- Use resource limits and requests
- Implement horizontal pod autoscaling
- Monitor and optimize database queries
- Use CDN for static assets

### Reliability
- Implement circuit breakers
- Use health checks and readiness probes
- Set up proper logging and monitoring
- Implement disaster recovery procedures

### Scalability
- Use horizontal scaling for stateless services
- Implement database sharding if needed
- Use caching strategies
- Monitor and optimize resource usage

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [EventStore Documentation](https://eventstore.com/docs/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/) 