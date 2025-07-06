# Cursor Rules Summary

## 📁 Rules Structure

The project now uses the proper Cursor rules structure in `.cursor/rules/`:

```
.cursor/
└── rules/
    ├── container-first.md      # Core container-first principles
    ├── python-execution.md     # Python execution patterns
    └── security.md            # Security guidelines
```

## 🎯 Rule Files

### 1. `container-first.md`
- **Purpose**: Core container-first development principles
- **Content**: 
  - Allowed vs. forbidden commands
  - Container services available
  - Development workflow
  - Quick command reference

### 2. `python-execution.md`
- **Purpose**: Specific Python execution patterns
- **Content**:
  - Container Python execution patterns
  - Service-specific commands
  - Common use cases
  - Error handling

### 3. `security.md`
- **Purpose**: Security guidelines and best practices
- **Content**:
  - Container security principles
  - Environment variable management
  - Database security
  - Network security
  - Incident response

## 🚫 Forbidden Commands

**NEVER** run these on the host:
```bash
python src/main.py
python3 test_script.py
pip install yfinance
pip3 install -r requirements.txt
```

## ✅ Allowed Commands

**ALWAYS** use containers:
```bash
# Run Python scripts
docker-compose exec trading-service python src/main.py
docker-compose run --rm trading-cli python test_script.py

# Install packages
docker-compose exec trading-service pip install yfinance
docker-compose run --rm trading-cli pip install -r requirements.txt

# Run tests
make test
docker-compose run --rm trading-cli python -m pytest tests/
```

## 🛠️ Quick Start

1. **Start environment**:
   ```bash
   make docker-up
   ```

2. **Run Python scripts**:
   ```bash
   docker-compose exec trading-service python src/main.py
   ```

3. **Install packages**:
   ```bash
   docker-compose exec trading-service pip install yfinance
   ```

4. **Run tests**:
   ```bash
   make test
   ```

5. **Use interactive script**:
   ```bash
   ./run_container_test.sh
   ```

## 🔧 Available Services

| Service | Purpose | Command |
|---------|---------|---------|
| `trading-service` | Main trading bot | `docker-compose exec trading-service python` |
| `market-data-service` | Market data | `docker-compose exec market-data-service python` |
| `portfolio-service` | Portfolio management | `docker-compose exec portfolio-service python` |
| `strategy-service` | Trading strategies | `docker-compose exec strategy-service python` |
| `analytics-service` | Data analysis | `docker-compose exec analytics-service python` |
| `trading-cli` | CLI and testing | `docker-compose run --rm trading-cli python` |

## 🧪 Testing the Cached Market Data System

```bash
# Interactive testing
./run_container_test.sh

# Direct testing
docker-compose run --rm trading-cli python test_cached_market_data_container.py

# Service-specific testing
docker-compose exec trading-service python test_cached_market_data_container.py
```

## 📋 Makefile Commands

```bash
# Development
make setup-dev          # Set up development environment
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-restart     # Restart all services

# Testing
make test               # Run all tests
make test-unit          # Run unit tests only
make test-integration   # Run integration tests only
make test-coverage      # Run tests with coverage

# Code Quality
make lint               # Run linting checks
make format             # Format code
make type-check         # Run type checking
```

## 🔒 Security Benefits

1. **Code Isolation**: No Python code runs on host system
2. **Environment Consistency**: All developers use identical environments
3. **Dependency Management**: All packages installed in containers
4. **Access Control**: Containers run with limited permissions
5. **Network Security**: Controlled network access through Docker

## 📚 Additional Resources

- [Container First Guide](CONTAINER_FIRST_GUIDE.md) - Comprehensive development guide
- [Quick Wins Summary](QUICK_WINS_SUMMARY.md) - Performance improvements
- [Architecture Guide](ARCHITECTURE.md) - System architecture overview

---

**Remember**: Always use containers for Python execution. This ensures consistency, security, and reproducibility across all development environments. 