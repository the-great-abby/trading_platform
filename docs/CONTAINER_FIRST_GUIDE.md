# Container-First Development Guide

## 🎯 Cursor Rules

This project uses Cursor rules located in `.cursor/rules/` to enforce container-first development:

- **`container-first.md`** - Core container-first development principles
- **`python-execution.md`** - Specific Python execution patterns and examples
- **`security.md`** - Security guidelines and best practices

These rules ensure consistent development practices across the team.

## 🐳 Overview

This project follows a **container-first development approach** where all Python code execution, package management, and testing happens inside Docker containers. This ensures:

- **Consistent environments** across all developers
- **Isolation** from host system dependencies
- **Reproducible builds** and deployments
- **Security** by not executing code directly on the host

## 🚫 Forbidden Commands

**NEVER** run these commands directly on your host system:

```bash
# ❌ DON'T DO THIS
python src/main.py
python3 test_script.py
pip install yfinance
pip3 install -r requirements.txt
```

## ✅ Allowed Commands

**ALWAYS** use these container-based commands:

```bash
# ✅ DO THIS INSTEAD
docker-compose exec trading-service python src/main.py
docker-compose run --rm trading-cli python test_script.py
docker-compose exec trading-service pip install yfinance
docker-compose run --rm trading-cli pip install -r requirements.txt
```

## 🛠️ Quick Start

### 1. Start the Development Environment

```bash
# Start all services
make docker-up

# Or start with build
make docker-up-build
```

### 2. Run Python Scripts

```bash
# Run a Python script in the trading service
docker-compose exec trading-service python src/main.py

# Run a script in a temporary container
docker-compose run --rm trading-cli python test_script.py

# Use the interactive script
./run_container_test.sh
```

### 3. Install Packages

```bash
# Install a package in the trading service
docker-compose exec trading-service pip install yfinance

# Install in a temporary container
docker-compose run --rm trading-cli pip install yfinance
```

### 4. Run Tests

```bash
# Run all tests
make test

# Run specific test file
docker-compose run --rm trading-cli python -m pytest tests/test_strategies.py -v

# Run with coverage
make test-coverage
```

## 📋 Available Services

| Service | Purpose | Python Access |
|---------|---------|---------------|
| `trading-service` | Main trading bot | `docker-compose exec trading-service python` |
| `market-data-service` | Market data provider | `docker-compose exec market-data-service python` |
| `portfolio-service` | Portfolio management | `docker-compose exec portfolio-service python` |
| `strategy-service` | Trading strategies | `docker-compose exec strategy-service python` |
| `analytics-service` | Data analysis | `docker-compose exec analytics-service python` |
| `trading-cli` | CLI and testing | `docker-compose run --rm trading-cli python` |
| `postgres-dev` | Development database | `docker-compose exec postgres-dev psql` |
| `redis-dev` | Development cache | `docker-compose exec redis-dev redis-cli` |

## 🔧 Common Commands

### Python Execution

```bash
# Run script in specific service
docker-compose exec <service> python <script>

# Run script in temporary container
docker-compose run --rm trading-cli python <script>

# Open Python shell
docker-compose exec <service> python

# Run with environment variables
docker-compose run --rm -e API_KEY=your_key trading-cli python <script>
```

### Package Management

```bash
# Install package in service
docker-compose exec <service> pip install <package>

# Install from requirements
docker-compose exec <service> pip install -r requirements.txt

# Update requirements and rebuild
docker-compose build --no-cache <service>
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
docker-compose run --rm trading-cli python -m pytest tests/test_file.py

# Run with specific markers
docker-compose run --rm trading-cli python -m pytest -m "slow"

# Run with coverage
make test-coverage
```

### Database Operations

```bash
# Connect to database
docker-compose exec postgres-dev psql -U trading_user -d trading_bot

# Run migrations
docker-compose exec trading-service alembic upgrade head

# Backup database
docker-compose exec postgres-dev pg_dump -U trading_user trading_bot > backup.sql
```

### Logging and Monitoring

```bash
# View service logs
docker-compose logs <service>

# Follow logs in real-time
docker-compose logs -f <service>

# View all logs
docker-compose logs

# Access Grafana (if running)
open http://localhost:3000
```

## 🧪 Testing the Cached Market Data System

The project includes a database-backed market data caching system. To test it:

```bash
# Run the container test script
./run_container_test.sh

# Or run directly
docker-compose run --rm trading-cli python test_cached_market_data_container.py

# Test with specific service
docker-compose exec trading-service python test_cached_market_data_container.py
```

## 📊 Makefile Commands

The project includes a comprehensive Makefile with container-based commands:

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

# Database
make db-migrate         # Run database migrations
make db-backup          # Backup databases
make db-restore         # Restore databases

# Kubernetes (for production)
make k8s-deploy         # Deploy to Kubernetes
make k8s-delete         # Delete Kubernetes deployment
```

## 🔒 Security Benefits

### 1. Code Isolation
- No Python code runs directly on your host system
- All dependencies are contained within Docker images
- Prevents conflicts with system Python installations

### 2. Environment Consistency
- All developers use identical environments
- No "works on my machine" issues
- Reproducible builds and deployments

### 3. Dependency Management
- All packages are installed in containers
- No pollution of host system
- Easy to update and manage dependencies

### 4. Access Control
- Containers run with limited permissions
- Network access is controlled
- File system access is restricted

## 🚀 Production Deployment

For production, the same container-first approach is used:

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Deploy to Kubernetes
make k8s-deploy

# Monitor deployment
make k8s-pods
make k8s-logs
```

## 🐛 Troubleshooting

### Common Issues

1. **Container not starting**
   ```bash
   # Check logs
   docker-compose logs <service>
   
   # Rebuild container
   docker-compose build --no-cache <service>
   ```

2. **Import errors**
   ```bash
   # Install missing package
   docker-compose exec <service> pip install <package>
   
   # Rebuild with new requirements
   docker-compose build <service>
   ```

3. **Database connection issues**
   ```bash
   # Check database status
   docker-compose ps postgres-dev
   
   # Check database logs
   docker-compose logs postgres-dev
   ```

4. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   
   # Rebuild containers
   docker-compose build --no-cache
   ```

### Getting Help

1. Check the logs: `docker-compose logs <service>`
2. Check container status: `docker-compose ps`
3. Check the Makefile help: `make help`
4. Review the `.cursorrules` file for guidelines

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python in Docker](https://docs.docker.com/language/python/)
- [Project Architecture](ARCHITECTURE.md)
- [Quick Wins Guide](QUICK_WINS_SUMMARY.md)

---

**Remember**: Always use containers for Python execution. This ensures consistency, security, and reproducibility across all development environments. 