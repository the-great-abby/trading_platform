# Available Services for Restoration

**Date**: November 4, 2025  
**Currently Running**: 5 core services  
**Available to Deploy**: 44+ additional services

---

## ✅ Currently Running (5 services)

| Service | Port | Status | Version | Purpose |
|---------|------|--------|---------|---------|
| live-trading-service | 11120 | ✅ RUNNING | 0.1.0-ci.34 | Live trading with Public.com API |
| elliott-wave-service | 11085 | ✅ RUNNING | 0.1.0-ci.34 | Elliott Wave pattern detection |
| strategy-service | 11001 | ✅ RUNNING | 0.1.0-ci.34 | Strategy management & backtesting |
| market-data-service | 11084 | ✅ RUNNING | 0.1.0-ci.34 | Market data API (Polygon primary) |
| backtest-api | 11101 | ✅ RUNNING | 0.1.0-ci.34 | Backtest execution API |

---

## 📊 Available Services by Category (49 total)

### 🎨 Dashboards & UI (9 services)

**Priority: HIGH** - User interface for system interaction

| Service | Port (PORT_MAP) | Build Command | Purpose |
|---------|-----------------|---------------|---------|
| **unified-trading-dashboard** | 11115 | `make build-service SERVICE=unified-trading-dashboard` | Main trading interface with live positions |
| **unified-analytics-dashboard** | 11114 | `make build-service SERVICE=unified-analytics-dashboard` | AI analysis and recommendations UI |
| **unified-news-dashboard** | 11116 | `make build-service SERVICE=unified-news-dashboard` | News sentiment and analysis |
| trading-dashboard-service | - | `make build-service SERVICE=trading-dashboard-service` | Alternative trading dashboard |
| performance-dashboard | - | `make build-service SERVICE=performance-dashboard` | Performance metrics visualization |
| data-pipeline-dashboard | - | `make build-service SERVICE=data-pipeline-dashboard` | Data pipeline monitoring |
| rss-dashboard | 8080 | `make build-service SERVICE=rss-dashboard` | RSS feed viewer |
| ai-stock-dashboard | - | `make build-service SERVICE=ai-stock-dashboard` | AI stock analysis dashboard |
| ai-ide-service | - | `make build-service SERVICE=ai-ide-service` | AI-powered IDE features |

**Recommended Next**: Deploy the 3 unified dashboards for full UI access.

---

### 📈 Data Services (8 services)

**Priority: MEDIUM-HIGH** - Data ingestion and processing

| Service | Port | Build Command | Purpose |
|---------|------|---------------|---------|
| **market-data-worker** | - | Build manually (see workaround below) | Background market data updates |
| **rss-feed-service** | 11004 | `make build-service SERVICE=rss-feed-service` | News aggregation & sentiment |
| **data-transformation-pipeline** | 11135 | `make build-service SERVICE=data-transformation-pipeline` | Data preprocessing |
| **data-analysis-service** | 11136 | `Technical analysis engine |
| data-processing-service | 11095 | `make build-service SERVICE=data-processing-service` | General data processing |
| earnings-data-service | - | `make build-service SERVICE=earnings-data-service` | Earnings calendar data |

**Recommended**: market-data-worker (critical for real-time data), rss-feed-service (news)

---

### 🤖 AI & ML Services (6 services)

**Priority: MEDIUM** - Advanced AI features

| Service | Port | Build Command | Purpose |
|---------|------|---------------|---------|
| **ai-analysis-service** | 11085 | `make build-service SERVICE=ai-analysis-service` | AI-powered stock recommendations |
| **kubernetes-rag-chat** | 11116 | `make build-service SERVICE=kubernetes-rag-chat` | RAG chat interface for docs |
| llm-service | 11109 | `make build-service SERVICE=llm-service` | LLM processing service |
| llm-worker | - | `make build-service SERVICE=llm-worker` | Background LLM tasks |

**Note**: These require Ollama to be running (currently scaled down for resources)

---

### 💼 Trading Services (6 services)

**Priority**: Depends on use case

| Service | Port | Build Command | Purpose |
|---------|------|---------------|---------|
| portfolio-service | - | `make build-service SERVICE=portfolio-service` | Portfolio management |
| order-service | - | `make build-service SERVICE=order-service` | Order management |
| trading-service | - | `make build-service SERVICE=trading-service` | Additional trading logic |
| risk-service | - | `make build-service SERVICE=risk-service` | Risk management |
| risk-management-service | 11182 | `make build-service SERVICE=risk-management-service` | Advanced risk (VaR, stress tests) |
| risk-integration-service | - | `make build-service SERVICE=risk-integration-service` | Risk system integration |
| backtest-request-service | - | `make build-service SERVICE=backtest-request-service` | Backtest job management |

---

### 📊 Monitoring & Infrastructure (2 services + 1 deployment)

**Priority: HIGH** - System observability

| Service | Port | Deploy Command | Purpose |
|---------|------|----------------|---------|
| **Prometheus** | 11190 | `kubectl apply -f k8s/prometheus-deployment.yaml` | Metrics collection (already configured) |
| notification-service | - | `make build-service SERVICE=notification-service` | Alerts & notifications |
| mcp-service | 11117 | `make build-service SERVICE=mcp-service` | Model Context Protocol |
| gateway | - | `make build-service SERVICE=gateway` | API gateway |

**Note**: Prometheus doesn't need building - just deploy the existing k8s manifest.

---

## 🚀 Quick Deployment Recipes

### Recipe 1: Full User Interface
**What**: Deploy all 3 unified dashboards for complete UI  
**Time**: ~8-10 minutes  
**Resource**: ~300m CPU, ~768Mi RAM

```bash
# Build dashboards
make build-service SERVICE=unified-trading-dashboard
make build-service SERVICE=unified-analytics-dashboard  
make build-service SERVICE=unified-news-dashboard

# Push to registry
docker push localhost:32000/unified-trading-dashboard:latest
docker push localhost:32000/unified-analytics-dashboard:latest
docker push localhost:32000/unified-news-dashboard:latest

# Deploy
kubectl apply -f k8s/unified-trading-dashboard.yaml
kubectl apply -f k8s/unified-analytics-dashboard.yaml
kubectl apply -f k8s/unified-news-dashboard.yaml

# Port forward for access
kubectl port-forward -n trading-system svc/unified-trading-dashboard 11115:80 &
kubectl port-forward -n trading-system svc/unified-analytics-dashboard 11114:80 &
kubectl port-forward -n trading-system svc/unified-news-dashboard 11116:80 &
```

### Recipe 2: Data & Background Services
**What**: Deploy data workers and RSS feeds  
**Time**: ~5-7 minutes  
**Resource**: ~200m CPU, ~512Mi RAM

```bash
# market-data-worker (use docker build directly - Makefile has issue)
cd /Users/abby/code/trading
docker build -f services/market-data-worker/Dockerfile -t localhost:32000/market-data-worker:latest .
docker push localhost:32000/market-data-worker:latest
kubectl apply -f k8s/market-data-worker.yaml

# RSS feed service
make build-service SERVICE=rss-feed-service
docker push localhost:32000/rss-feed-service:latest
kubectl apply -f k8s/rss-feed-service.yaml
```

### Recipe 3: AI Analysis Suite
**What**: Deploy AI services (requires Ollama)  
**Time**: ~10-15 minutes  
**Resource**: ~500m+ CPU, ~1Gi+ RAM

```bash
# Scale up Ollama first (if needed)
kubectl scale deployment ollama-proxy --replicas=1 -n ollama-controller

# Build AI services
make build-service SERVICE=ai-analysis-service
make build-service SERVICE=kubernetes-rag-chat

# Deploy
docker push localhost:32000/ai-analysis-service:latest
docker push localhost:32000/kubernetes-rag-chat:latest
kubectl apply -f k8s/ai-analysis-service.yaml
kubectl apply -f k8s/kubernetes-rag-chat.yaml
```

### Recipe 4: Monitoring Stack
**What**: Add Prometheus for metrics  
**Time**: 1 minute  
**Resource**: 200m CPU, 256Mi RAM

```bash
# Just deploy - no build needed
kubectl apply -f k8s/prometheus-deployment.yaml

# Port forward
kubectl port-forward -n trading-system svc/prometheus 11190:9090 &
```

---

## ⚠️ Known Issues & Workarounds

### market-data-worker Build Issue
The Makefile build fails for market-data-worker. **Workaround**:
```bash
docker build -f services/market-data-worker/Dockerfile \
  -t localhost:32000/market-data-worker:latest .
docker push localhost:32000/market-data-worker:latest
```

---

## 💾 Resource Budget

**Current Usage:**
- CPU: 316m / ~2000m (15%)
- Memory: 3.0Gi / ~6Gi (50%)

**Available for New Services:**
- CPU: ~1684m (~8-10 more medium services)
- Memory: ~3Gi

**Service Resource Estimates:**
- Dashboard: ~100m CPU, ~256Mi RAM each
- Data Service: ~100m CPU, ~256Mi RAM
- AI Service: ~200m CPU, ~512Mi RAM
- Monitoring: ~200m CPU, ~256Mi RAM

---

## 🎯 Recommended Priority

Based on PORT_MAP.md and functionality:

**1. Dashboards** ⭐⭐⭐ (Essential for UI)
- unified-trading-dashboard
- unified-analytics-dashboard
- unified-news-dashboard

**2. Data Workers** ⭐⭐⭐ (Essential for fresh data)
- market-data-worker
- rss-feed-service

**3. Monitoring** ⭐⭐ (Important for observability)
- Prometheus

**4. AI Services** ⭐ (Nice to have)
- ai-analysis-service
- kubernetes-rag-chat

**5. Additional Trading** ⭐ (Optional enhancements)
- portfolio-service
- risk-management-service
- notification-service

---

## 📞 Quick Commands

```bash
# List all available services
make services-available

# Check what's currently running  
kubectl get pods -n trading-system

# Check resource usage
kubectl top nodes
kubectl top pods -n trading-system

# View updated service map
make k8s-services
```

---

**Note**: Your system is already functional with the 5 core services running. Additional services enhance functionality but aren't strictly required for basic trading operations.

Would you like me to deploy the dashboards next? That would give you full UI access to your trading system!



