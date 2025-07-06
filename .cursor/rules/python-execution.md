# Python Execution Rules

## 🚫 Never Execute Python on Host
- **NEVER** use `python` or `python3` directly on the host system
- **NEVER** use `pip` or `pip3` directly on the host system
- **PREFER** Kubernetes for Python execution
- **FALLBACK** to Docker Compose when Kubernetes is unavailable
- **ALWAYS** use containers for Python execution

## ✅ Container Python Execution Patterns

### Running Scripts (Kubernetes Preferred)
```bash
# ✅ PREFERRED - Run in Kubernetes pod
kubectl exec -it deployment/trading-service -- python src/main.py
kubectl exec -it deployment/market-data-service -- python scripts/fetch_data.py

# ✅ PREFERRED - Run in temporary Kubernetes pod
kubectl run python-test --rm -it --image=python:3.11 -- python test_script.py
kubectl exec -it deployment/trading-service -- python -m pytest tests/

# ✅ PREFERRED - Use Makefile k8s targets
make k8s-test
make k8s-logs
```

### Running Scripts (Docker Compose Fallback)
```bash
# ✅ FALLBACK - Run in specific service
docker-compose exec trading-service python src/main.py
docker-compose exec market-data-service python scripts/fetch_data.py

# ✅ FALLBACK - Run in temporary container
docker-compose run --rm trading-cli python test_script.py
docker-compose run --rm trading-cli python -m pytest tests/

# ✅ FALLBACK - Use Makefile targets
make test
make python-run SCRIPT=src/main.py
```

### Installing Packages
```bash
# ✅ Correct - Install in service
docker-compose exec trading-service pip install yfinance
docker-compose exec market-data-service pip install pandas

# ✅ Correct - Install in temporary container
docker-compose run --rm trading-cli pip install -r requirements.txt
docker-compose run --rm trading-cli pip install pytest

# ✅ Correct - Use Makefile targets
make install
make python-install PACKAGE=yfinance
```

### Interactive Python
```bash
# ✅ Correct - Python shell in container
docker-compose exec trading-service python
docker-compose run --rm trading-cli python

# ✅ Correct - IPython in container
docker-compose exec trading-service ipython
docker-compose run --rm trading-cli ipython
```

## ❌ Forbidden Patterns

### Direct Host Execution
```bash
# ❌ WRONG - Don't do this
python src/main.py
python3 test_script.py
pip install yfinance
pip3 install -r requirements.txt
```

### Host Python Shell
```bash
# ❌ WRONG - Don't do this
python
python3
ipython
```

## 🔧 Service-Specific Commands

### Trading Service
```bash
docker-compose exec trading-service python src/main.py
docker-compose exec trading-service pip install <package>
docker-compose exec trading-service python -m pytest tests/
```

### Market Data Service
```bash
docker-compose exec market-data-service python scripts/fetch_data.py
docker-compose exec market-data-service pip install yfinance
docker-compose exec market-data-service python -c "import yfinance; print('OK')"
```

### CLI/Testing Container
```bash
docker-compose run --rm trading-cli python test_script.py
docker-compose run --rm trading-cli pip install pytest
docker-compose run --rm trading-cli python -m pytest tests/ -v
```

## 📋 Common Use Cases

### Running Tests
```bash
# All tests
make test

# Specific test file
docker-compose run --rm trading-cli python -m pytest tests/test_strategies.py

# With coverage
make test-coverage

# Specific service tests
docker-compose exec trading-service python -m pytest tests/unit/
```

### Running Scripts
```bash
# Main application
docker-compose exec trading-service python src/main.py

# Data fetching
docker-compose exec market-data-service python scripts/fetch_market_data.py

# Backtesting
docker-compose exec trading-service python scripts/run_backtest.py

# Quick test
docker-compose run --rm trading-cli python test_cached_market_data_container.py
```

### Package Management
```bash
# Install from requirements
docker-compose exec trading-service pip install -r requirements.txt

# Install new package
docker-compose exec trading-service pip install new_package

# Update requirements
docker-compose exec trading-service pip freeze > requirements.txt

# Rebuild with new dependencies
docker-compose build trading-service
```

## 🎯 Best Practices

1. **Always use containers** for Python execution
2. **Use specific services** when possible (trading-service, market-data-service)
3. **Use temporary containers** for one-off scripts (trading-cli)
4. **Use Makefile targets** for common operations
5. **Check service availability** before executing commands
6. **Use proper environment variables** in containers
7. **Monitor container logs** for debugging

## 🚨 Error Handling

### Service Not Running
```bash
# Check if service is running
docker-compose ps

# Start service if needed
docker-compose up -d trading-service

# Then run command
docker-compose exec trading-service python script.py
```

### Container Build Issues
```bash
# Rebuild container
docker-compose build --no-cache trading-service

# Rebuild all containers
docker-compose build --no-cache

# Check build logs
docker-compose build trading-service
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Rebuild containers
docker-compose build --no-cache
``` 