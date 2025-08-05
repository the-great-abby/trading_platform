# 🚀 Space Trading Station - CQRS & Microservices

A comprehensive algorithmic trading system built with CQRS (Command Query Responsibility Segregation) architecture, featuring backtesting, real-time market data, and Kubernetes deployment. Welcome to Mission Control!

## 🏗️ Space Station Architecture

- **CQRS Pattern**: Separate command and query models for optimal performance
- **Microservices**: Containerized services for scalability
- **Event Sourcing**: Complete audit trail of all trading events
- **Kubernetes Native**: Production-ready deployment
- **Multi-Strategy Backtesting**: Comprehensive strategy evaluation
- **AI Navigation Systems**: LLM-enhanced trading strategies

## 📁 Mission Control Structure

```
├── Makefile                 # Mission Control Center (use Makefile.new for modular approach)
├── Makefile.backtest       # Orbital Backtesting operations and results management
├── Makefile.kubernetes     # Space Station deployment and management
├── Makefile.docker         # Development environment operations
├── Makefile.database       # Data management operations
├── src/                    # Source code
│   ├── api/               # REST API endpoints
│   ├── backtesting/       # Backtesting engine
│   ├── core/              # Core trading logic
│   ├── cqrs/              # CQRS implementation
│   ├── models/            # Data models
│   ├── services/          # Business services
│   ├── strategies/        # Trading strategies
│   └── utils/             # Utilities
├── k8s/                   # Kubernetes manifests
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## 🚀 Launch Sequence (Quick Start)

### Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- Python 3.8+
- API keys for market data providers

### AI Assistant

This Space Trading Station is powered by **ORION** - your AI co-pilot for Mission Control operations. All AI Navigation Systems and Space Station modules are configured through `src/utils/space_station_config.py`.

### 1. Setup Mission Control Environment

```bash
# Copy environment template
cp config.env.example .env

# Edit .env with your API credentials
# Required: POLYGON_API_KEY, ALPHA_VANTAGE_API_KEY
```

### 2. Initialize Space Station

```bash
# Using modular Makefiles (recommended)
make -f Makefile.new dev-start

# Or using the old monolithic Makefile
make docker-dev
```

### 3. Launch Orbital Backtests

```bash
# List available backtest runs
make -f Makefile.backtest backtest-list

# Run a new backtest
make -f Makefile.backtest backtest-run

# View results
make -f Makefile.backtest backtest-view-results
```

## 📋 Mission Control System (Modular Makefile System)

We've organized the Makefile into focused, manageable modules to eliminate conflicts and improve maintainability.

## 🚀 Real-Time Monitor ↔ API Architecture

The Space Trading Station includes a real-time performance monitor that runs on your host and connects to the backtest API running in Kubernetes.

### Quick Monitor Setup
```bash
# Deploy the backtest API
./scripts/deploy-backtest-api.sh

# Port forward the API (keep running)
kubectl port-forward svc/backtest-api 10001:10001 -n trading-system

# Run the monitor with real data
make monitor-demo-api
```

### Documentation
- [📖 Complete Guide](docs/MONITOR_API_GUIDE.md) - Detailed architecture and setup
- [⚡ Quick Reference](docs/QUICK_REFERENCE.md) - One-page cheat sheet  
- [✅ Setup Checklist](docs/MONITOR_API_CHECKLIST.md) - Step-by-step checklist
- [🎯 Unified Dashboards](docs/UNIFIED_DASHBOARDS_GUIDE.md) - Unified dashboard management system

### Architecture
```
Your Host ←→ Port Forward ←→ Kubernetes API ←→ Database
Monitor    ←→ localhost:10001 ←→ backtest-api ←→ PostgreSQL
```

### Available Mission Control Modules

| Makefile | Purpose | Usage |
|----------|---------|-------|
| `Makefile.new` | Main Mission Control | `make -f Makefile.new <target>` |
| `Makefile.backtest` | Orbital Backtesting | `make -f Makefile.backtest <target>` |
| `Makefile.kubernetes` | Space Station deployment | `make -f Makefile.kubernetes <target>` |
| `Makefile.trading-platform` | Unified Dashboard Management | `make -f Makefile.trading-platform <target>` |
| `Makefile.docker` | Development environment | `make -f Makefile.docker <target>` |
| `Makefile.database` | Data management | `make -f Makefile.database <target>` |

### Common Mission Operations

#### Development
```bash
# Start development environment
make -f Makefile.new dev-start

# Check system status
make -f Makefile.new status

# View logs
make -f Makefile.docker dev-logs
```

#### Orbital Backtesting
```bash
# List backtest results
make -f Makefile.backtest backtest-list

# Run comprehensive backtest
make -f Makefile.backtest backtest-run

# Compare strategies
make -f Makefile.backtest backtest-compare

# View specific run details
make -f Makefile.backtest backtest-show RUN_ID=backtest_20250705_123456_BollingerBandsStrategy
```

#### Space Station Operations
```bash
# Deploy to Kubernetes
make -f Makefile.new kube-deploy

# Check pod status
make -f Makefile.kubernetes kube-status

# View logs
make -f Makefile.kubernetes kube-logs

# Port forward services
make -f Makefile.kubernetes kube-postgres-port
```

#### Data Management
```bash
# Initialize database
make -f Makefile.database db-init

# Fetch satellite data (market data)
make -f Makefile.new data-fetch

# Check database health
make -f Makefile.database db-health

# Export data
make -f Makefile.database db-export-data SYMBOL=AAPL
```

## 🔧 Available Mission Commands

### Main Mission Control (`Makefile.new`)
```bash
make -f Makefile.new help              # Show main help
make -f Makefile.new help-backtest     # Show backtest commands
make -f Makefile.new help-kube         # Show Kubernetes commands
make -f Makefile.new help-docker       # Show Docker commands
make -f Makefile.new help-db           # Show database commands
make -f Makefile.new dev-start         # Start development environment
make -f Makefile.new kube-deploy       # Deploy to Kubernetes
make -f Makefile.new backtest-run      # Run backtests
make -f Makefile.new data-fetch        # Fetch satellite data
make -f Makefile.new status            # Show system status
make -f Makefile.new clean             # Clean up all resources
make -f Makefile.new version           # Show version information
make -f Makefile.new env-check         # Check environment configuration
```

### Orbital Backtesting (`Makefile.backtest`)
```bash
make -f Makefile.backtest help                    # Show backtest help
make -f Makefile.backtest backtest-list           # List backtest runs
make -f Makefile.backtest backtest-list-detailed  # List with details
make -f Makefile.backtest backtest-show           # Show specific run
make -f Makefile.backtest backtest-compare        # Compare strategies
make -f Makefile.backtest backtest-stats          # Show statistics
make -f Makefile.backtest backtest-run            # Run backtest
make -f Makefile.backtest backtest-quick          # Quick backtest
make -f Makefile.backtest kube-backtest-list      # K8s backtest list
make -f Makefile.backtest kube-backtest-show      # K8s backtest show
```

### Space Station Operations (`Makefile.kubernetes`)
```bash
make -f Makefile.kubernetes help              # Show K8s help
make -f Makefile.kubernetes kube-deploy-all   # Deploy all components
make -f Makefile.kubernetes kube-status       # Check pod status
make -f Makefile.kubernetes kube-jobs         # Check job status
make -f Makefile.kubernetes kube-logs         # View logs
make -f Makefile.kubernetes kube-postgres     # Deploy PostgreSQL
make -f Makefile.kubernetes kube-rabbitmq     # Deploy RabbitMQ
make -f Makefile.kubernetes kube-workers      # Deploy workers
make -f Makefile.kubernetes kube-clean        # Clean up resources
```

### Unified Dashboard Management (`Makefile.trading-platform`)
```bash
make -f Makefile.trading-platform help                    # Show trading platform help
make -f Makefile.trading-platform start-unified-dashboards    # Start unified dashboard services
make -f Makefile.trading-platform stop-unified-dashboards     # Stop unified dashboard services
make -f Makefile.trading-platform restart-unified-dashboards  # Restart unified dashboard services
make -f Makefile.trading-platform unified-dashboards          # Set up port forwarding for unified dashboards
```

**Unified Dashboard URLs:**
- **Analytics Dashboard**: http://localhost:11141 (consolidates AI stock, central hub, data pipeline)
- **News Dashboard**: http://localhost:11142 (consolidates RSS dashboard and feed service)
- **Trading Dashboard**: http://localhost:11143 (consolidates trading, performance, health dashboards)

### Development Environment (`Makefile.docker`)
```bash
make -f Makefile.docker help              # Show Docker help
make -f Makefile.docker docker-dev        # Start development environment
make -f Makefile.docker docker-test       # Run tests
```

## 🧪 Testing

```bash
# Run all tests
make -f Makefile.docker docker-test

# Run specific test file
make -f Makefile.docker python-test-file FILE=test_strategies.py

# Run backtest validation
make -f Makefile.backtest backtest-run
```

## 📊 Monitoring

```bash
# Check system health
make -f Makefile.new status

# View service logs
make -f Makefile.kubernetes kube-logs

# Port forward monitoring tools
make -f Makefile.kubernetes kube-rabbitmq-ui
```

## 🚀 Deployment

### Development
```bash
make -f Makefile.new dev-start
```

### Production (Kubernetes)
```bash
make -f Makefile.new kube-deploy
```

## 📈 Features

- **Multi-Strategy Backtesting**: Bollinger Bands, RSI, MACD, SMA Crossover, News Enhanced
- **Real-time Market Data**: Polygon, Alpha Vantage, Yahoo Finance
- **Event Sourcing**: Complete audit trail
- **CQRS Architecture**: Optimized for read/write operations
- **Kubernetes Native**: Scalable deployment
- **Database Persistence**: PostgreSQL with proper indexing
- **API Gateway**: RESTful endpoints
- **Health Monitoring**: Comprehensive health checks

## 🤝 Contributing

### Development Rules

**IMPORTANT**: Before contributing, please read our [Development Rules](./docs/DEVELOPMENT_RULES.md). 

**Key Requirements:**
- **User Stories First**: All new features must have user stories documented in `./docs/user_stories/`
- **Modular Design**: Follow the modular Makefile and architecture patterns
- **Documentation**: Include comprehensive documentation and examples
- **Testing**: Include unit and integration tests

### Contribution Process

1. **Create User Stories**: Document user stories in appropriate file under `./docs/user_stories/`
2. **Design Review**: Review user stories and technical approach
3. **Implementation**: Follow the development workflow in our rules
4. **Testing**: Ensure all acceptance criteria are met
5. **Documentation**: Update relevant documentation
6. **Submit PR**: Include references to user stories

### Quick Start for Contributors

```bash
# Review development rules
cat docs/DEVELOPMENT_RULES.md

# Check existing user stories
ls docs/user_stories/

# Start development environment
make -f Makefile.new dev-start
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in `./docs/`
2. Review user stories in `./docs/user_stories/`
3. Open an issue on GitHub

## 🔄 Migration from Old Makefile

If you're migrating from the old monolithic Makefile:

1. **Backup**: The old Makefile is saved as `Makefile.old`
2. **Use new structure**: Use `Makefile.new` as the main entry point
3. **Update scripts**: Update any scripts that reference specific Makefile targets
4. **Test**: Verify all workflows work with the new modular structure

The new structure eliminates the duplicate target warnings and provides better organization. 