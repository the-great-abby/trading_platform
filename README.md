# Trading Platform

Automated algorithmic trading system with backtesting, live trading, portfolio management, and AI-powered market analysis.

## 🏗️ Architecture

This is a Kubernetes-native trading platform that combines multiple strategies (Elliott Wave, Sector Rotation, Options Trading, Volatility Trading) with real-time market data and AI-driven decision making.

**Key Features:**
- ✅ Real market data backtesting with Polygon API
- ✅ Monte Carlo simulations for strategy validation
- ✅ Live trading with Public.com integration
- ✅ Options trading strategies (Iron Condor, Straddles, etc.)
- ✅ AI-powered sentiment analysis and market regime detection
- ✅ Risk management and portfolio optimization
- ✅ Comprehensive monitoring with Grafana/Prometheus

## 📁 Project Structure

```
trading/
├── src/                   # Core application code
│   ├── backtesting/      # Backtest engine and strategies
│   ├── strategies/       # Trading strategy implementations
│   ├── services/         # Microservices (AI, market data, etc.)
│   └── utils/            # Shared utilities and configurations
├── backtests/            # Real market data backtest scripts
├── simulations/          # Monte Carlo simulation scripts
├── tests/                # Automated test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── contract/        # Contract tests
├── scripts/              # Utility and operational scripts
│   ├── analysis/        # Results analysis tools
│   ├── monitoring/      # System and trade monitors
│   ├── deployment/      # Deployment automation
│   ├── utilities/       # Helper scripts
│   └── strategies/      # Strategy management
├── results/              # Backtest and simulation outputs
├── config/               # Configuration files
│   ├── strategies/      # Strategy configurations
│   ├── services/        # Service configurations
│   └── requirements/    # Python dependencies
├── docs/                 # Documentation
├── k8s/                  # Kubernetes manifests
├── deploy/               # Deployment configurations
└── services/             # Microservice implementations
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Kubernetes cluster (local or cloud)
- Polygon API key (for market data)

### Local Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd trading

# 2. Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp config.env.example .env
# Edit .env with your API keys

# 5. Run tests
make test-run
```

### Run a Backtest

```bash
# Run a simple backtest
python backtests/clean_backtest.py

# Run a simulation (faster, statistical)
python simulations/realistic_trading_simulation.py

# View results
make -f Makefile.backtesting results
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Port forward to access services
make port-forward-all

# Check status
make service-status
```

## 📊 Common Commands

### Testing
```bash
make test-run              # Run all tests
make test-unit             # Run unit tests only
make test-integration      # Run integration tests
make test-coverage         # Run tests with coverage report
```

### Backtesting
```bash
make -f Makefile.backtesting dashboard  # Open web dashboard
make -f Makefile.backtesting results    # View recent results
make -f Makefile.backtesting clean      # Clean old results
```

### Live Trading
```bash
make live-trading-service-status      # Check service status
make live-trading-refresh-token       # Refresh API token
make live-trading-monitor             # Monitor live trades
make live-trading-orders              # View active orders
```

### Docker Cleanup
```bash
make docker-prune          # Clean unused containers/images (keeps volumes)
make docker-prune-all      # Aggressive cleanup (keeps volumes)
make docker-stats          # Show Docker disk usage
```

### Services
```bash
make service-status        # Check all services
make port-forward-all      # Forward all service ports
make port-forward-stop     # Stop all port forwards
```

## 📚 Documentation

### Getting Started
- [Quick Reference](docs/QUICK_REFERENCE.md) - Common tasks and commands
- [File Organization Guide](docs/FILE_ORGANIZATION_GUIDE.md) - Project structure explained
- [Backtesting Guide](docs/BACKTESTING_GUIDE.md) - How to run backtests

### Trading Strategies
- [Available Strategies](docs/AVAILABLE_STRATEGIES.md) - Strategy catalog
- [Strategy Guide](docs/ALL_STRATEGIES_GUIDE.md) - Detailed strategy documentation
- [Options Strategies](docs/OPTIONS_STRATEGIES_GUIDE.md) - Options trading guide

### Operations
- [Live Trading Setup](docs/LIVE_TRADING_SETUP.md) - Production setup
- [Kubernetes Guide](docs/KUBERNETES_FIRST_GUIDE.md) - K8s deployment
- [Monitoring Guide](docs/OBSERVABILITY_GUIDE.md) - Observability and alerts

### Development
- [Makefile Reference](docs/MAKEFILE_REFERENCE.md) - All make targets
- [Testing Guide](docs/KUBERNETES_TESTING_GUIDE.md) - Testing strategies
- [Architecture](docs/ARCHITECTURE_DIAGRAM.md) - System architecture

## 🎯 Strategy Overview

### Stock Strategies
- **Sector Rotation** - Momentum-based sector switching
- **Elliott Wave** - Impulse and corrective wave detection
- **Volatility Trading** - VIX-based volatility capture
- **Market Regime Detection** - Bull/bear/volatile market adaptation

### Options Strategies
- **Iron Condor** - Range-bound profit generation
- **Straddle/Strangle** - Volatility plays
- **Calendar Spread** - Time decay capture
- **Butterfly Spread** - Limited risk/reward

### AI-Enhanced
- **Sentiment Analysis** - News and social media sentiment
- **LLM-Based Analysis** - GPT-powered market insights
- **Adaptive Sector Wave** - Multi-strategy auto-switching

## 🔧 Configuration

### Environment Variables

Key environment variables (see `config.env.example`):
```bash
# Market Data
POLYGON_API_KEY=your_key_here
PUBLIC_API_SECRET=your_secret_here

# Database
DATABASE_URL=postgresql://...

# Trading
TRADING_MODE=paper  # or 'live'
ACCOUNT_SIZE=1000
```

### Trading Configuration

Central config in `src/utils/trading_config.py`:
- Symbol lists
- Risk parameters
- Strategy allocations
- Position sizing rules

## 📈 Monitoring

### Access Dashboards

```bash
# Grafana (monitoring)
open http://localhost:11003

# Trading Dashboard
open http://localhost:11114

# Backtest Dashboard
make -f Makefile.backtesting dashboard
```

### Logs

```bash
# Service logs
kubectl logs -f deployment/live-trading-service

# Backtest logs
ls logs/

# Monitor logs
make live-trading-service-logs
```

## 🧪 Testing

### Run Tests

```bash
# All tests
make test-run

# Specific test suites
make test-unit
make test-integration
pytest tests/unit/test_specific.py

# With coverage
make test-coverage
```

### Validation

```bash
# Validate system
make validate-system

# Validate Kubernetes configs
make validate-k8s
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `make test-run`
4. Update documentation
5. Submit a pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write docstrings for public functions
- Add tests for new features

## 📊 Performance

### Backtest Results

See `results/` directory for detailed backtest outputs.

Recent performance (example):
- **Annual Return**: 8-12%
- **Sharpe Ratio**: 1.5-2.0
- **Max Drawdown**: <15%
- **Win Rate**: 55-65%

## 🔐 Security

- API keys stored in Kubernetes secrets
- Encrypted credentials in database
- No hardcoded secrets in code
- Environment-based configuration

## 📞 Support

- **Documentation**: See `docs/` directory
- **Issues**: Use GitHub issues
- **Questions**: Check existing documentation first

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- Polygon.io for market data
- Public.com for trading API
- OpenAI for LLM capabilities

---

**Quick Links:**
- [File Organization](docs/FILE_ORGANIZATION_GUIDE.md)
- [Quick Reference](docs/QUICK_REFERENCE.md)
- [Backtesting](docs/BACKTESTING_GUIDE.md)
- [Live Trading](docs/LIVE_TRADING_SETUP.md)
- [Makefile Reference](docs/MAKEFILE_REFERENCE.md)

