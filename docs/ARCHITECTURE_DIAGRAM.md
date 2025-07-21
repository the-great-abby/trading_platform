# 🏗️ System Architecture & Development Workflow (Updated July 2025)

## 📊 High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SPACE TRADING STATION (Updated)                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   DASHBOARDS    │    │   API GATEWAY   │    │   MONITORING    │            │
│  │   (Web UI)      │◄──►│   (Nginx)       │◄──►│   (Prometheus)  │            │
│  │                 │    │                 │    │                 │            │
│  │ • Performance   │    │ • localhost:8080│    │ • Health Checks │            │
│  │ • Trading       │    │ • Load Balancer │    │ • Metrics       │            │
│  │ • Health        │    │ • Rate Limiting │    │ • Alerts        │            │
│  │ • RSS (NEW)     │    │                 │    │                 │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                    │
│           └───────────────────────┼───────────────────────┘                    │
│                                   │                                            │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐  │
│  │                    MICROSERVICES LAYER                                   │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   TRADING   │ │  MARKET     │ │    RISK     │ │  PORTFOLIO  │        │  │
│  │  │  SERVICE    │ │   DATA      │ │  MANAGER    │ │  SERVICE    │        │  │
│  │  │             │ │  SERVICE    │ │             │ │             │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │  STRATEGY   │ │    NEWS     │ │    ORDER    │ │  ANALYTICS  │        │  │
│  │  │  SERVICE    │ │    BOT      │ │  MANAGEMENT │ │  SERVICE    │        │  │
│  │  │             │ │             │ │             │ │             │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   RSS       │ │   RSS       │ │    LLM      │ │    LLM      │        │  │
│  │  │  FEED       │ │ DASHBOARD   │ │  SERVICE    │ │   PROXY     │        │  │
│  │  │  SERVICE    │ │  (NEW)      │ │ (Ollama)    │ │  (NEW)      │        │  │
│  │  │             │ │             │ │             │ │             │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                            │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐  │
│  │                    DATA LAYER                                            │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │  RABBITMQ   │ │ EVENT STORE │ │   REDIS     │ │ POSTGRESQL  │        │  │
│  │  │ (Messages)  │ │ (Events)    │ │  (Cache)    │ │ (Database)  │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                            │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐  │
│  │                  EXTERNAL INTEGRATIONS                                   │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   PUBLIC    │ │   ALPACA    │ │   YAHOO     │ │   NEWS      │        │  │
│  │  │    API      │ │    API      │ │  FINANCE    │ │  SOURCES    │        │  │
│  │  │ (Trading)   │ │ (Trading)   │ │ (Market)    │ │ (Reuters,   │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ │ Bloomberg)  │        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                            │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐  │
│  │                  INFRASTRUCTURE                                          │  │
│  │                                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   DOCKER    │ │ KUBERNETES  │ │   REGISTRY  │ │   PORTS     │        │  │
│  │  │  REGISTRY   │ │ (Docker     │ │ (localhost: │ │ (11000-     │        │  │
│  │  │ (localhost: │ │ Desktop)    │ │   32000)    │ │  12001)     │        │  │
│  │  │   32000)    │ │             │ │             │ │             │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🐳 Docker Development Architecture

### **Development Environment with Docker**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT WORKFLOW WITH DOCKER                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           DEVELOPER MACHINE                                │ │
│  │                                                                             │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │ │
│  │  │   VS CODE /     │  │   TERMINAL      │  │   BROWSER       │            │ │
│  │  │   EDITOR        │  │   (Makefile)    │  │   (API Docs)    │            │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            │ │
│  │           │                     │                     │                    │ │
│  │           └─────────────────────┼─────────────────────┘                    │ │
│  │                                 │                                          │ │
│  │  ┌─────────────────────────────┼─────────────────────────────────────────┐ │ │
│  │  │                    DOCKER COMPOSE (DEV)                              │ │ │
│  │  │                                                                       │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │                 DEVELOPMENT CONTAINERS                         │ │ │ │
│  │  │  │                                                               │ │ │ │
│  │  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │ │ │ │
│  │  │  │  │   TRADING   │ │    NEWS     │ │   MARKET    │              │ │ │ │
│  │  │  │  │    BOT      │ │     BOT     │ │    DATA     │              │ │ │ │
│  │  │  │  │  (Python)   │ │  (Python)   │ │  (Python)   │              │ │ │ │
│  │  │  │  └─────────────┘ └─────────────┘ └─────────────┘              │ │ │ │
│  │  │  │                                                               │ │ │ │
│  │  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │ │ │ │
│  │  │  │  │   API       │ │   DATABASE  │ │   CACHE     │              │ │ │ │
│  │  │  │  │  GATEWAY    │ │ (PostgreSQL)│ │   (Redis)   │              │ │ │ │
│  │  │  │  │  (Nginx)    │ │             │ │             │              │ │ │ │
│  │  │  │  └─────────────┘ └─────────────┘ └─────────────┘              │ │ │ │
│  │  │  └───────────────────────────────────────────────────────────────┘ │ │ │
│  │  │                                                                       │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │                 VOLUME MOUNTS                                   │ │ │ │
│  │  │  │                                                               │ │ │ │
│  │  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │ │ │ │
│  │  │  │  │   SOURCE    │ │    LOGS     │ │   CONFIG    │              │ │ │ │
│  │  │  │  │    CODE     │ │             │ │   FILES     │              │ │ │ │
│  │  │  │  │  (Live)     │ │  (Persist)  │ │  (Mount)    │              │ │ │ │
│  │  │  │  └─────────────┘ └─────────────┘ └─────────────┘              │ │ │ │
│  │  │  └───────────────────────────────────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           DOCKER NETWORKING                                │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   HOST      │  │   BRIDGE    │  │   OVERLAY   │  │   NONE      │      │ │
│  │  │  NETWORK    │  │  NETWORK    │  │  NETWORK    │  │  NETWORK    │      │ │
│  │  │ (Port 8000) │  │ (Internal)  │  │ (Swarm)     │  │ (Isolated)  │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Development Workflow

### **1. Local Development with Docker**

```bash
# Development workflow commands
make docker-dev-build    # Build development container
make docker-dev-run      # Start development environment
make docker-dev-logs     # View logs
make docker-dev-shell    # Access container shell
make docker-dev-stop     # Stop development environment
```

### **2. Container Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONTAINER ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        DOCKERFILE.DEV                                      │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   BASE      │  │   PYTHON    │  │  DEPENDENCY │  │   SOURCE    │      │ │
│  │  │   IMAGE     │─►│   RUNTIME   │─►│  INSTALL    │─►│   CODE      │      │ │
│  │  │ (Ubuntu)    │  │ (Python 3.9)│  │ (pip install)│  │ (COPY .)    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                      DOCKER-COMPOSE.DEV.YML                                │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   TRADING   │  │    NEWS     │  │   DATABASE  │  │   CACHE     │      │ │
│  │  │   SERVICE   │  │    BOT      │  │ (PostgreSQL)│  │   (Redis)   │      │ │
│  │  │  (Port 8000)│  │  (Port 8001)│  │  (Port 5432)│  │  (Port 6379)│      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           VOLUME MOUNTS                                    │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   SOURCE    │  │    LOGS     │  │   CONFIG    │  │   DATA      │      │ │
│  │  │    CODE     │  │             │  │   FILES     │  │   PERSIST   │      │ │
│  │  │  (Live)     │  │  (Persist)  │  │  (Mount)    │  │  (Mount)    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Service Communication Flow

### **Development Mode Communication**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT COMMUNICATION FLOW                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    HTTP/REST    ┌─────────────┐    HTTP/REST    ┌─────────────┐
│  │   BROWSER   │◄──────────────►│   API       │◄──────────────►│   TRADING   │
│  │  (Port 8000)│                 │  GATEWAY    │                 │   ENGINE    │
│  └─────────────┘                 └─────────────┘                 └─────────────┘
│                                          │                                │
│                                          │                                │
│  ┌─────────────┐    HTTP/REST    ┌─────────────┐    HTTP/REST    ┌─────────────┐
│  │   TERMINAL  │◄──────────────►│   NEWS      │◄──────────────►│   MARKET    │
│  │  (CLI)      │                 │    BOT      │                 │    DATA     │
│  └─────────────┘                 └─────────────┘                 └─────────────┘
│                                          │                                │
│                                          │                                │
│  ┌─────────────┐    Database     ┌─────────────┐    Cache       ┌─────────────┐
│  │   POSTGRES  │◄──────────────►│   REDIS     │◄──────────────►│   KAFKA     │
│  │   (Read)    │                 │   (Cache)   │                 │ (Messages)  │
│  └─────────────┘                 └─────────────┘                 └─────────────┘
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           EXTERNAL APIs                                    │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   PUBLIC    │  │   ALPACA    │  │   YAHOO     │  │   NEWS      │      │ │
│  │  │    API      │  │    API      │  │  FINANCE    │  │  SOURCES    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Development vs Production

### **Development Environment**

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  trading-bot-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app                    # Live code mounting
      - ./logs:/app/logs          # Persistent logs
      - ./data:/app/data          # Persistent data
    environment:
      - ENV=development
      - DEBUG=true
    depends_on:
      - postgres-dev
      - redis-dev

  postgres-dev:
    image: postgres:13
    environment:
      POSTGRES_DB: trading_dev
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis-dev:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

### **Production Environment**

```yaml
# docker-compose.yml (Production)
version: '3.8'
services:
  trading-service:
    build:
      context: ./services/trading-service
      dockerfile: Dockerfile
    deploy:
      replicas: 3
    environment:
      - ENV=production
      - DEBUG=false
    depends_on:
      - kafka
      - eventstore
      - postgres
      - redis

  news-service:
    build:
      context: ./services/news-service
      dockerfile: Dockerfile
    deploy:
      replicas: 2
    environment:
      - ENV=production
      - DEBUG=false

  api-gateway:
    build:
      context: ./services/gateway
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
```

## 🔧 Development Commands

### **Docker Development Workflow**

```bash
# Build and start development environment
make docker-dev-build    # Build development container
make docker-dev-up       # Start all development services
make docker-dev-down     # Stop all development services

# Development tools
make docker-dev-shell    # Access container shell
make docker-dev-logs     # View logs
make docker-dev-restart  # Restart services
make docker-dev-clean    # Clean up containers and volumes

# Testing in Docker
make docker-test         # Run tests in container
make docker-test-unit    # Run unit tests
make docker-test-integration  # Run integration tests

# Code quality in Docker
make docker-lint         # Run linting
make docker-format       # Format code
make docker-type-check   # Type checking
```

### **Local Development vs Docker**

```bash
# Local Development (without Docker)
make install             # Install dependencies locally
make run-api             # Run API server locally
make run-trader          # Run trading engine locally
make test                # Run tests locally

# Docker Development
make docker-dev-up       # Start Docker environment
make docker-dev-shell    # Access container
make docker-dev-logs     # View logs
```

## 📊 Monitoring & Debugging

### **Development Monitoring**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT MONITORING                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   DOCKER    │  │   LOGS      │  │   METRICS   │  │   DEBUG     │          │
│  │   DESKTOP   │  │   VIEWER    │  │   (Port)    │  │   TOOLS     │          │
│  │             │  │             │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                 │                 │                 │                │
│         └─────────────────┼─────────────────┼─────────────────┘                │
│                           │                 │                                  │
│  ┌─────────────────────────┼─────────────────┼────────────────────────────────┐ │
│  │                    CONTAINER MONITORING                                   │ │ │
│  │                                                                           │ │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │ │
│  │  │   CPU       │  │   MEMORY    │  │   NETWORK   │  │   DISK      │    │ │ │
│  │  │   USAGE     │  │   USAGE     │  │   TRAFFIC   │  │   USAGE     │    │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │ │
└───────────────────────────────────────────────────────────────────────────────────┘ │
```

## 🔄 Development Lifecycle

### **Complete Development Workflow**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. SETUP                   2. DEVELOPMENT          3. TESTING                │
│  ┌─────────────┐           ┌─────────────┐         ┌─────────────┐            │
│  │   Clone     │──────────►│   Code      │────────►│   Unit      │            │
│  │   Repo      │           │   Changes   │         │   Tests     │            │
│  └─────────────┘           └─────────────┘         └─────────────┘            │
│                                                                                 │
│  4. BUILD                   5. DEPLOY              6. MONITOR                 │
│  ┌─────────────┐           ┌─────────────┐         ┌─────────────┐            │
│  │   Docker    │──────────►│   Dev       │────────►│   Logs      │            │
│  │   Build     │           │   Env       │         │   Metrics   │            │
│  └─────────────┘           └─────────────┘         └─────────────┘            │
│                                                                                 │
│  7. INTEGRATION            8. PRODUCTION          9. MAINTENANCE              │
│  ┌─────────────┐           ┌─────────────┐         ┌─────────────┐            │
│  │   Tests     │──────────►│   Deploy    │────────►│   Updates   │            │
│  │   (Docker)  │           │   (K8s)     │         │   Monitoring│            │
│  └─────────────┘           └─────────────┘         └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 Key Benefits of Docker in Development

### **1. Consistency**
- Same environment across all developers
- No "works on my machine" issues
- Reproducible builds

### **2. Isolation**
- Services don't interfere with each other
- Easy to reset and restart
- Clean development environment

### **3. Scalability**
- Easy to add new services
- Simple to scale individual components
- Microservices architecture support

### **4. Portability**
- Works on any OS with Docker
- Easy deployment to different environments
- Version control for infrastructure

### **5. Development Speed**
- Fast container startup
- Live code mounting for instant changes
- Integrated development tools

## 🚀 Current System Configuration (July 2025)

### **📡 Port Configuration & Service Mapping**

| Service | External Port | Internal Port | Status | Recent Changes |
|---------|---------------|---------------|---------|----------------|
| Performance Dashboard | 11000 | 80 | ✅ Running | Registry fix |
| Trading Dashboard | 11001 | 8000 | ✅ Running | Registry fix |
| Health Dashboard | 11002 | 80 | ✅ Running | Registry fix |
| **RSS Dashboard** | **11003** | **80** | **✅ Running** | **NEW** |
| Backtest Request | 11031 | 80 | ✅ Running | Registry fix |
| **LLM Proxy** | **12001** | **11434** | **✅ Running** | **NEW** |

### **🔧 Infrastructure Services**

| Service | Port | Status | Notes |
|---------|------|---------|-------|
| Docker Registry | 32000 | ✅ Running | NodePort (Fixed) |
| RabbitMQ | 5672 | ✅ Running | Message Queue |
| PostgreSQL | 5432 | ✅ Running | Database |
| Redis | 6379 | ✅ Running | Cache |

### **🎯 Recent Architecture Updates**

#### **✅ July 2025 Changes**

1. **🔧 Registry Port Configuration Fix**
   - **Problem**: Docker registry accessible on port 32000 but build scripts used port 5000
   - **Solution**: Updated all build/push commands to use `localhost:32000`
   - **Impact**: All Docker builds now work correctly

2. **📰 RSS Dashboard Addition**
   - **New Service**: Complete RSS dashboard for trading recommendations
   - **Features**: Real-time recommendations, multiple feed types, auto-refresh
   - **URL**: `http://localhost:11003/`

3. **🤖 LLM Proxy Integration**
   - **New Service**: LLM Proxy for external access to Ollama
   - **Port**: `localhost:12001`
   - **Integration**: Connects to internal Ollama LLM service

4. **🔄 Port Forwarding Stability**
   - **Improvement**: Robust port forwarding with auto-restart
   - **Features**: Auto-restart on failure, proactive monitoring
   - **Result**: All dashboards now accessible

### **📊 Health Check Endpoints**

All services now have working health endpoints:
- `http://localhost:11000/health` - Performance Dashboard
- `http://localhost:11001/health` - Trading Dashboard  
- `http://localhost:11002/health` - Health Dashboard
- `http://localhost:11003/health` - RSS Dashboard
- `http://localhost:12001/health` - LLM Proxy

### **🔍 Registry Health**
- Registry Catalog: `http://localhost:32000/v2/_catalog`
- Registry Status: `kubectl get svc registry -n default`

This architecture provides a robust foundation for developing, testing, and deploying your algorithmic trading system with full Docker integration throughout the development lifecycle. 