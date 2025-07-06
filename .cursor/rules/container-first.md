# Container-First Development Rules

## 🐳 Container-First Development
- NEVER execute `python`, `python3`, `pip`, or `pip3` directly on the host
- **PREFER** Kubernetes for development over Docker Compose
- **USE** `kubectl` commands for development workflows
- **FALLBACK** to Docker Compose when Kubernetes is unavailable
- ALWAYS use containers for Python execution and package management

## ✅ Allowed Commands
- `docker-compose up` - Start services
- `docker-compose down` - Stop services
- `docker-compose exec <service> python <script>` - Run Python in container
- `docker-compose exec <service> pip install <package>` - Install packages in container
- `docker run --rm -v $(pwd):/app -w /app python:3.11 python <script>` - Run Python in temporary container
- `make` commands - Use Makefile targets that handle container execution

## ❌ Forbidden Commands
- `python <script>` - Use container instead
- `python3 <script>` - Use container instead
- `pip install <package>` - Use container instead
- `pip3 install <package>` - Use container instead

## 🛠️ Development Workflow
1. Use `make dev` to start development environment
2. Use `make test` to run tests in containers
3. Use `make install` to install dependencies in containers
4. Use `docker-compose exec <service> python <script>` for script execution

## 🐳 Container Services Available
- `trading-service` - Main trading bot service
- `market-data-service` - Market data provider
- `portfolio-service` - Portfolio management
- `strategy-service` - Trading strategies
- `analytics-service` - Data analysis
- `postgres-dev` - Development database
- `redis-dev` - Development cache
- `quick-wins-demo` - Quick wins demonstration

## 📝 Examples

### ✅ CORRECT:
```bash
# Run Python script in trading service
docker-compose exec trading-service python src/main.py

# Install package in market data service
docker-compose exec market-data-service pip install yfinance

# Run tests in container
make test

# Start development environment
make dev
```

### ❌ FORBIDDEN:
```bash
# Don't run Python directly on host
python src/main.py

# Don't install packages directly on host
pip install yfinance

# Don't use python3 directly
python3 test_script.py
```

## 🔧 Environment Variables
- Always use `.env` files for configuration
- Use `docker-compose` environment variable injection
- Never hardcode database URLs or API keys

## 🗄️ Database Operations
- Use `docker-compose exec postgres-dev psql -U trading_user -d trading_bot` for database access
- Use Alembic migrations in containers: `docker-compose exec trading-service alembic upgrade head`

## 🧪 Testing
- Run tests in containers: `make test`
- Use pytest in containers: `docker-compose exec trading-service pytest`
- Never run tests directly on host

## 📦 Package Management
- Add dependencies to `requirements.txt`
- Install in containers: `docker-compose exec trading-service pip install -r requirements.txt`
- Use `docker-compose build` to rebuild containers with new dependencies

## 📊 Logging and Monitoring
- Use container logs: `docker-compose logs <service>`
- Use `docker-compose logs -f <service>` for real-time logs
- Access Grafana at `http://localhost:3000` for monitoring

## ⚡ Quick Commands Reference
```bash
# Development
make dev                    # Start development environment
make test                   # Run tests
make install                # Install dependencies
make clean                  # Clean up containers

# Services
docker-compose up           # Start all services
docker-compose down         # Stop all services
docker-compose logs <svc>   # View service logs

# Python execution
docker-compose exec trading-service python <script>
docker-compose exec market-data-service python <script>
docker-compose exec quick-wins-demo python <script>

# Database
docker-compose exec postgres-dev psql -U trading_user -d trading_bot
docker-compose exec trading-service alembic upgrade head
```

## 🔒 Security Notes
- Never commit `.env` files with secrets
- Use Docker secrets for production
- Always run as non-root user in containers
- Use multi-stage builds for production images 