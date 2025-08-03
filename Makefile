# Trading Platform Service Management
# Easy commands to start/stop services in optimized configuration

.PHONY: help status start-all stop-all start-core stop-core start-heavy stop-heavy start-dashboards stop-dashboards start-workers stop-workers start-management stop-management scale-down scale-up logs data-fetch data-fetch-symbols data-fetch-period data-coverage data-status

# Default target
help:
	@echo "Trading Platform Service Management"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@echo "  status          - Show current pod status"
	@echo "  start-all       - Start all services"
	@echo "  stop-all        - Stop all services (scale to 0)"
	@echo "  start-core      - Start core services only"
	@echo "  stop-core       - Stop core services"
	@echo "  start-heavy     - Start heavy services (market-data, analytics)"
	@echo "  stop-heavy      - Stop heavy services"
	@echo "  start-dashboards - Start dashboard services"
	@echo "  stop-dashboards - Stop dashboard services"
	@echo "  start-workers   - Start worker services"
	@echo "  stop-workers    - Stop worker services"
	@echo "  start-management - Start management services"
	@echo "  stop-management - Stop management services"
	@echo "  scale-down      - Scale down to minimal configuration"
	@echo "  scale-up        - Scale up to full configuration"
	@echo "  logs <service>  - Show logs for a specific service"
	@echo "  port-forward    - Set up port forwarding for dashboards"
	@echo ""
	@echo "Port Watcher Commands:"
	@echo "  port-watcher-start     - Start comprehensive port watcher"
	@echo "  port-watcher-stop      - Stop port watcher and cleanup"
	@echo "  port-watcher-status    - Check watcher status and active ports"
	@echo "  port-watcher-logs      - View watcher logs"
	@echo "  port-watcher-restart   - Restart port watcher"
	@echo "  port-watcher-help      - Show port watcher help"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy-and-start       - Deploy, start services, and comprehensive port watcher"
	@echo "  deploy-and-port-forward - Deploy, start core services, and basic port forwarding"
	@echo "  deploy-and-tmux        - Deploy, start services, and tmux port forwarding"
	@echo "  deploy-only            - Deploy and start services only"
	@echo "  deploy-help            - Show deployment help"
	@echo ""
	@echo "Resource-Constrained Commands:"
	@echo "  deploy-constrained     - Deploy with resource constraints (1 pod each)"
	@echo "  deploy-constrained-and-start - Deploy, start, and comprehensive port watcher"
	@echo "  deploy-constrained-and-port-forward - Deploy, start core, and basic port forwarding"
	@echo "  start-constrained      - Start all services (1 pod each)"
	@echo "  constrained-help       - Show resource-constrained help"
	@echo ""
	@echo "Data Fetching Commands:"
	@echo "  data-fetch      - Fetch data for all symbols (last 30 days)"
	@echo "  data-fetch-symbols SYMBOLS='AAPL,MSFT,GOOGL' - Fetch data for specific symbols"
	@echo "  data-fetch-period START='2024-01-01' END='2024-12-31' - Fetch data for specific period"
	@echo "  data-coverage   - Show data coverage for all symbols"
	@echo "  data-status     - Show current data status"
	@echo ""
	@echo "VAPID Push Notification Commands:"
	@echo "  make vapid-*    - Use Makefile.vapid commands"
	@echo "  make vapid-help - Show VAPID help"
	@echo ""

# Show current status
status:
	@echo "=== Current Pod Status ==="
	kubectl get pods -n trading-system --sort-by=.metadata.name
	@echo ""
	@echo "=== Resource Usage ==="
	kubectl top pods -n trading-system --sort-by=memory | head -10
	@echo ""
	@echo "=== Node Resources ==="
	kubectl describe nodes | grep -A 5 "Allocated resources"

# Start all services
start-all:
	@echo "Starting all services..."
	kubectl scale deployment --all --replicas=2 -n trading-system
	@echo "All services started"

# Stop all services
stop-all:
	@echo "Stopping all services..."
	kubectl scale deployment --all --replicas=0 -n trading-system
	@echo "All services stopped"

# Start core services (essential for basic functionality)
start-core:
	@echo "Starting core services..."
	kubectl scale deployment central-hub-dashboard --replicas=1 -n trading-system
	kubectl scale deployment trading-gateway --replicas=2 -n trading-system
	kubectl scale deployment health-dashboard --replicas=1 -n trading-system
	kubectl scale deployment postgres-dev --replicas=1 -n trading-system
	kubectl scale deployment rabbitmq --replicas=1 -n trading-system
	@echo "Core services started"

# Stop core services
stop-core:
	@echo "Stopping core services..."
	kubectl scale deployment central-hub-dashboard --replicas=0 -n trading-system
	kubectl scale deployment trading-gateway --replicas=0 -n trading-system
	kubectl scale deployment health-dashboard --replicas=0 -n trading-system
	@echo "Core services stopped"

# Start heavy services (market data and analytics)
start-heavy:
	@echo "Starting heavy services..."
	kubectl scale deployment market-data-service --replicas=1 -n trading-system
	kubectl scale deployment market-data-worker --replicas=1 -n trading-system
	kubectl scale deployment analytics-service --replicas=1 -n trading-system
	kubectl scale deployment analytics-worker --replicas=1 -n trading-system
	@echo "Heavy services started"

# Stop heavy services
stop-heavy:
	@echo "Stopping heavy services..."
	kubectl scale deployment market-data-service --replicas=0 -n trading-system
	kubectl scale deployment market-data-worker --replicas=0 -n trading-system
	kubectl scale deployment analytics-service --replicas=0 -n trading-system
	kubectl scale deployment analytics-worker --replicas=0 -n trading-system
	@echo "Heavy services stopped"

# Start dashboard services
start-dashboards:
	@echo "Starting dashboard services..."
	kubectl scale deployment trading-dashboard-service --replicas=1 -n trading-system
	kubectl scale deployment performance-dashboard --replicas=1 -n trading-system
	kubectl scale deployment rss-dashboard --replicas=1 -n trading-system
	kubectl scale deployment rss-feed-service --replicas=1 -n trading-system

# Stop dashboard services
stop-dashboards:
	@echo "Stopping dashboard services..."
	kubectl scale deployment trading-dashboard-service --replicas=0 -n trading-system
	kubectl scale deployment performance-dashboard --replicas=0 -n trading-system
	kubectl scale deployment rss-dashboard --replicas=0 -n trading-system
	kubectl scale deployment rss-feed-service --replicas=0 -n trading-system

# Start worker services
start-workers:
	@echo "Starting worker services..."
	kubectl scale deployment market-data-worker --replicas=1 -n trading-system
	kubectl scale deployment analytics-worker --replicas=1 -n trading-system
	kubectl scale deployment llm-worker --replicas=1 -n trading-system
	@echo "Worker services started"

# Stop worker services
stop-workers:
	@echo "Stopping worker services..."
	kubectl scale deployment market-data-worker --replicas=0 -n trading-system
	kubectl scale deployment analytics-worker --replicas=0 -n trading-system
	kubectl scale deployment llm-worker --replicas=0 -n trading-system
	@echo "Worker services stopped"

# Start management services
start-management:
	@echo "Starting management services..."
	kubectl scale deployment command-api --replicas=1 -n trading-system
	kubectl scale deployment query-api --replicas=1 -n trading-system
	kubectl scale deployment public-api --replicas=1 -n trading-system
	@echo "Management services started"

# Stop management services
stop-management:
	@echo "Stopping management services..."
	kubectl scale deployment command-api --replicas=0 -n trading-system
	kubectl scale deployment query-api --replicas=0 -n trading-system
	kubectl scale deployment public-api --replicas=0 -n trading-system
	@echo "Management services stopped"

# Scale down to minimal configuration
scale-down:
	@echo "Scaling down to minimal configuration..."
	kubectl scale deployment --all --replicas=0 -n trading-system
	kubectl scale deployment central-hub-dashboard --replicas=1 -n trading-system
	kubectl scale deployment trading-gateway --replicas=1 -n trading-system
	kubectl scale deployment health-dashboard --replicas=1 -n trading-system
	@echo "Scaled down to minimal configuration"

# Scale up to full configuration
scale-up:
	@echo "Scaling up to full configuration..."
	kubectl scale deployment --all --replicas=2 -n trading-system
	@echo "Scaled up to full configuration"

# Show logs for a specific service
logs:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make logs SERVICE=<service-name>"; \
		echo "Available services:"; \
		kubectl get deployments -n trading-system -o name | sed 's/deployment.apps\///'; \
	else \
		kubectl logs -f deployment/$(SERVICE) -n trading-system; \
	fi

# Port forwarding for dashboards
port-forward:
	@echo "Setting up port forwarding for dashboards..."
	@echo "Central Hub Dashboard: http://localhost:11001"
	@echo "Health Dashboard: http://localhost:11002"
	@echo "Trading Dashboard: http://localhost:11003"
	@echo "Performance Dashboard: http://localhost:11004"
	@echo "RSS Dashboard: http://localhost:11005"
	@echo "PostgreSQL Vector Storage: http://localhost:11006"
	@echo "AI Stock Dashboard: http://localhost:11007"
	@echo ""
	@echo "Press Ctrl+C to stop port forwarding"
	kubectl port-forward -n trading-system service/central-hub-dashboard 11001:80 & \
	kubectl port-forward -n trading-system service/health-dashboard 11002:80 & \
	kubectl port-forward -n trading-system service/trading-dashboard-service 11003:8000 & \
	kubectl port-forward -n trading-system service/performance-dashboard 11004:80 & \
	kubectl port-forward -n trading-system service/rss-dashboard 11005:80 & \
	kubectl port-forward -n trading-system service/postgres-vector-storage 11006:80 & \
	kubectl port-forward -n trading-system service/ai-stock-dashboard 11007:80 & \
	wait

# Data fetching commands (use Makefile.data instead)
data-fetch:
	@echo "Use: make -f Makefile.data fetch-recent"

data-fetch-symbols:
	@echo "Use: make -f Makefile.data fetch-symbols SYMBOLS='AAPL,MSFT,GOOGL'"

data-fetch-period:
	@echo "Use: make -f Makefile.data fetch-period START='2024-01-01' END='2024-12-31'"

data-coverage:
	@echo "Use: make -f Makefile.data coverage"

data-status:
	@echo "Use: make -f Makefile.data status"
	kubectl logs -n trading-system deployment/market-data-worker --tail=10

# Emergency stop (stop everything except core)
emergency-stop:
	@echo "EMERGENCY STOP - Stopping all non-core services..."
	$(MAKE) stop-heavy
	$(MAKE) stop-dashboards
	$(MAKE) stop-workers
	$(MAKE) stop-management
	@echo "Emergency stop complete. Only core services remain running." 

# AI Analysis Service
ai-analysis-build:
	@echo "🤖 Building AI Analysis Service..."
	cd services/ai-analysis-service && docker build -t localhost:32000/ai-analysis-service:latest .
	docker push localhost:32000/ai-analysis-service:latest

ai-analysis-deploy: ai-analysis-build
	@echo "🚀 Deploying AI Analysis Service..."
	kubectl apply -f k8s/trading-platform-comprehensive.yaml
	kubectl wait --for=condition=available --timeout=300s deployment/ai-analysis-service -n trading-system

ai-analysis-logs:
	kubectl logs -f deployment/ai-analysis-service -n trading-system

ai-analysis-test:
	@echo "🧪 Testing AI Analysis Service..."
	curl -X POST http://localhost:11085/api/analyze/symbol/AAPL -H "Content-Type: application/json" -d '{"include_news": true, "include_technical": true}'

ai-analysis-daily:
	@echo "📊 Getting Daily AI Recommendations..."
	curl http://localhost:11085/api/recommendations/daily

# Port Watcher Commands
port-watcher-start: ## Start comprehensive port watcher with monitoring and logging
	@echo "🚀 Starting Comprehensive Port Watcher..."
	@echo "📁 Log directory: port_watcher_logs/"
	@echo "📄 Main log: port_watcher.log"
	@echo ""
	./scripts/start_port_watcher.sh

port-watcher-stop: ## Stop port watcher and cleanup processes
	@echo "🛑 Stopping Port Watcher..."
	@pkill -f "port_watcher.py" || echo "No port watcher process found"
	@pkill -f "kubectl port-forward" || echo "No port forwarding processes found"
	@echo "✅ Port watcher stopped and processes cleaned up"

port-watcher-status: ## Check port watcher status and active port forwards
	@echo "📊 Port Watcher Status:"
	@echo ""
	@if pgrep -f "port_watcher.py" > /dev/null; then \
		echo "✅ Port Watcher is running (PID: $(pgrep -f 'port_watcher.py'))"; \
	else \
		echo "❌ Port Watcher is not running"; \
	fi
	@echo ""
	@echo "🔍 Active Port Forwards:"
	@if pgrep -f "kubectl port-forward" > /dev/null; then \
		ps aux | grep "kubectl port-forward" | grep -v grep || echo "No active port forwards"; \
	else \
		echo "No active port forwards found"; \
	fi

port-watcher-logs: ## View port watcher logs
	@echo "📄 Port Watcher Logs:"
	@echo ""
	@if [ -f "port_watcher.log" ]; then \
		echo "📋 Main watcher log (last 20 lines):"; \
		tail -20 port_watcher.log; \
	else \
		echo "❌ No main watcher log found"; \
	fi
	@echo ""
	@if [ -d "port_watcher_logs" ]; then \
		echo "📁 Individual service logs:"; \
		ls -la port_watcher_logs/ | head -10; \
	else \
		echo "❌ No port watcher logs directory found"; \
	fi

port-watcher-restart: ## Restart port watcher
	@echo "🔄 Restarting Port Watcher..."
	$(MAKE) port-watcher-stop
	@echo ""
	$(MAKE) port-watcher-start

port-watcher-help: ## Show port watcher help
	@echo "📋 Port Watcher Commands:"
	@echo ""
	@echo "  make port-watcher-start     - Start comprehensive port watcher"
	@echo "  make port-watcher-stop      - Stop port watcher and cleanup"
	@echo "  make port-watcher-status    - Check watcher status and active ports"
	@echo "  make port-watcher-logs      - View watcher logs"
	@echo "  make port-watcher-restart   - Restart port watcher"
	@echo "  make port-watcher-help      - Show this help"
	@echo ""
	@echo "📊 Monitored Services (30+ services on ports 11101-11134):"
	@echo "   • Core Monitoring: Grafana, Prometheus, Infrastructure Metrics"
	@echo "   • Core Trading: Strategy, Trading, Order, Portfolio, Risk, Market Data"
	@echo "   • AI & Analytics: AI Analysis, AI Dashboard, LLM, Analytics"
	@echo "   • Dashboards: Health, Performance, Central Hub, RSS, Trading"
	@echo "   • Backtesting: Backtest API, Backtest Request Service"
	@echo "   • Data & Processing: Data Processing, Market Data Worker, Postgres Vector"
	@echo "   • Management: Strategy, Order, Signal, Risk Management"
	@echo "   • Additional: Notification, Public API, Report Viewer, RSS Feed, Trading Core/Ultra"
	@echo ""
	@echo "📝 Logs saved to: port_watcher_logs/ directory"

# Include VAPID Makefile
include Makefile.vapid

# Include Kubernetes Makefile
include Makefile.kubernetes

# Comprehensive Deployment Commands
deploy-and-start: ## Deploy all services, start them, and begin port forwarding
	@echo "🚀 Comprehensive Deployment Process"
	@echo "=================================="
	@echo ""
	@echo "📦 Step 1: Deploying services to Kubernetes..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting all services..."
	$(MAKE) start-all
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment --all -n trading-system
	@echo ""
	@echo "🔗 Step 3: Starting comprehensive port watcher..."
	@echo "📊 This will monitor all 30+ services and create logs for troubleshooting"
	@echo "📁 Logs will be saved to: port_watcher_logs/"
	@echo ""
	$(MAKE) port-watcher-start

deploy-and-port-forward: ## Deploy services and start basic port forwarding
	@echo "🚀 Quick Deployment with Port Forwarding"
	@echo "======================================="
	@echo ""
	@echo "📦 Step 1: Deploying services..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting core services..."
	$(MAKE) start-core
	@echo ""
	@echo "⏳ Waiting for core services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment/central-hub-dashboard -n trading-system
	@kubectl wait --for=condition=available --timeout=300s deployment/health-dashboard -n trading-system
	@echo ""
	@echo "🔗 Step 3: Starting basic port forwarding..."
	$(MAKE) port-forward

deploy-and-tmux: ## Deploy services and start tmux-based port forwarding
	@echo "🚀 Deployment with Tmux Port Forwarding"
	@echo "======================================"
	@echo ""
	@echo "📦 Step 1: Deploying services..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting services..."
	$(MAKE) start-all
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment --all -n trading-system
	@echo ""
	@echo "🔗 Step 3: Starting tmux port forwarding session..."
	$(MAKE) k8s-port-forward-start

deploy-only: ## Deploy services only (no port forwarding)
	@echo "📦 Deploying Services Only"
	@echo "========================="
	@echo ""
	@echo "📦 Step 1: Deploying services to Kubernetes..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting all services..."
	$(MAKE) start-all
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment --all -n trading-system
	@echo ""
	@echo "✅ Deployment complete!"
	@echo "💡 To start port forwarding, run:"
	@echo "   • make port-watcher-start (comprehensive monitoring)"
	@echo "   • make k8s-port-forward-start (tmux-based)"
	@echo "   • make port-forward (basic)"

deploy-help: ## Show deployment help
	@echo "📋 Deployment Commands:"
	@echo ""
	@echo "  make deploy-and-start        - Deploy, start services, and run comprehensive port watcher"
	@echo "  make deploy-and-port-forward - Deploy, start core services, and basic port forwarding"
	@echo "  make deploy-and-tmux         - Deploy, start services, and tmux port forwarding"
	@echo "  make deploy-only             - Deploy and start services only (no port forwarding)"
	@echo "  make deploy-help             - Show this help"
	@echo ""
	@echo "📊 Port Forwarding Options:"
	@echo "   • Comprehensive Port Watcher (30+ services, automatic logging)"
	@echo "   • Tmux-based Port Forwarding (6 services, separate windows)"
	@echo "   • Basic Port Forwarding (7 services, background processes)"
	@echo ""
	@echo "🔍 Monitoring:"
	@echo "   • make port-watcher-status  - Check port watcher status"
	@echo "   • make port-watcher-logs    - View port watcher logs"
	@echo "   • make status               - Show service status"

# Resource-Constrained Deployment Commands (1 pod per service)
deploy-constrained: ## Deploy with resource constraints (1 pod per service)
	@echo "📦 Resource-Constrained Deployment"
	@echo "=================================="
	@echo ""
	@echo "📦 Step 1: Deploying services to Kubernetes..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting services with resource constraints (1 pod each)..."
	$(MAKE) start-constrained
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment --all -n trading-system
	@echo ""
	@echo "✅ Resource-constrained deployment complete!"
	@echo "💡 To start port forwarding, run:"
	@echo "   • make port-watcher-start (comprehensive monitoring)"
	@echo "   • make k8s-port-forward-start (tmux-based)"
	@echo "   • make port-forward (basic)"

deploy-constrained-and-start: ## Deploy with constraints and start comprehensive port watcher
	@echo "🚀 Resource-Constrained Deployment with Port Watcher"
	@echo "=================================================="
	@echo ""
	@echo "📦 Step 1: Deploying services to Kubernetes..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting services with resource constraints (1 pod each)..."
	$(MAKE) start-constrained
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment --all -n trading-system
	@echo ""
	@echo "🔗 Step 3: Starting comprehensive port watcher..."
	@echo "📊 This will monitor all 30+ services and create logs for troubleshooting"
	@echo "📁 Logs will be saved to: port_watcher_logs/"
	@echo ""
	$(MAKE) port-watcher-start

deploy-constrained-and-port-forward: ## Deploy with constraints and basic port forwarding
	@echo "🚀 Resource-Constrained Deployment with Port Forwarding"
	@echo "====================================================="
	@echo ""
	@echo "📦 Step 1: Deploying services..."
	$(MAKE) -f Makefile.trading-platform deploy-platform
	@echo ""
	@echo "⚡ Step 2: Starting core services with constraints (1 pod each)..."
	$(MAKE) start-constrained-core
	@echo ""
	@echo "⏳ Waiting for core services to be ready..."
	@kubectl wait --for=condition=available --timeout=300s deployment/central-hub-dashboard -n trading-system
	@kubectl wait --for=condition=available --timeout=300s deployment/health-dashboard -n trading-system
	@echo ""
	@echo "🔗 Step 3: Starting basic port forwarding..."
	$(MAKE) port-forward

# Resource-Constrained Service Management (1 pod per service)
start-constrained: ## Start all services with resource constraints (1 pod each)
	@echo "⚡ Starting all services with resource constraints (1 pod each)..."
	kubectl scale deployment --all --replicas=1 -n trading-system
	@echo "✅ All services started with resource constraints"

start-constrained-core: ## Start core services with resource constraints (1 pod each)
	@echo "⚡ Starting core services with resource constraints (1 pod each)..."
	kubectl scale deployment central-hub-dashboard --replicas=1 -n trading-system
	kubectl scale deployment trading-gateway --replicas=1 -n trading-system
	kubectl scale deployment health-dashboard --replicas=1 -n trading-system
	kubectl scale deployment postgres-dev --replicas=1 -n trading-system
	kubectl scale deployment rabbitmq --replicas=1 -n trading-system
	@echo "✅ Core services started with resource constraints"

start-constrained-heavy: ## Start heavy services with resource constraints (1 pod each)
	@echo "⚡ Starting heavy services with resource constraints (1 pod each)..."
	kubectl scale deployment market-data-service --replicas=1 -n trading-system
	kubectl scale deployment market-data-worker --replicas=1 -n trading-system
	kubectl scale deployment analytics-service --replicas=1 -n trading-system
	kubectl scale deployment analytics-worker --replicas=1 -n trading-system
	@echo "✅ Heavy services started with resource constraints"

start-constrained-dashboards: ## Start dashboard services with resource constraints (1 pod each)
	@echo "⚡ Starting dashboard services with resource constraints (1 pod each)..."
	kubectl scale deployment trading-dashboard-service --replicas=1 -n trading-system
	kubectl scale deployment performance-dashboard --replicas=1 -n trading-system
	kubectl scale deployment rss-dashboard --replicas=1 -n trading-system
	kubectl scale deployment rss-feed-service --replicas=1 -n trading-system
	@echo "✅ Dashboard services started with resource constraints"

start-constrained-workers: ## Start worker services with resource constraints (1 pod each)
	@echo "⚡ Starting worker services with resource constraints (1 pod each)..."
	kubectl scale deployment market-data-worker --replicas=1 -n trading-system
	kubectl scale deployment analytics-worker --replicas=1 -n trading-system
	kubectl scale deployment llm-worker --replicas=1 -n trading-system
	@echo "✅ Worker services started with resource constraints"

start-constrained-management: ## Start management services with resource constraints (1 pod each)
	@echo "⚡ Starting management services with resource constraints (1 pod each)..."
	kubectl scale deployment command-api --replicas=1 -n trading-system
	kubectl scale deployment query-api --replicas=1 -n trading-system
	kubectl scale deployment public-api --replicas=1 -n trading-system
	@echo "✅ Management services started with resource constraints"

constrained-help: ## Show resource-constrained deployment help
	@echo "📋 Resource-Constrained Deployment Commands:"
	@echo ""
	@echo "🚀 Full Deployment:"
	@echo "  make deploy-constrained              - Deploy and start all services (1 pod each)"
	@echo "  make deploy-constrained-and-start   - Deploy, start, and comprehensive port watcher"
	@echo "  make deploy-constrained-and-port-forward - Deploy, start core, and basic port forwarding"
	@echo ""
	@echo "⚡ Service Management:"
	@echo "  make start-constrained              - Start all services (1 pod each)"
	@echo "  make start-constrained-core         - Start core services (1 pod each)"
	@echo "  make start-constrained-heavy        - Start heavy services (1 pod each)"
	@echo "  make start-constrained-dashboards   - Start dashboard services (1 pod each)"
	@echo "  make start-constrained-workers      - Start worker services (1 pod each)"
	@echo "  make start-constrained-management   - Start management services (1 pod each)"
	@echo ""
	@echo "📊 Resource Optimization:"
	@echo "  • CPU usage: ~40% reduction compared to 2 pods per service"
	@echo "  • Memory usage: ~35% reduction compared to 2 pods per service"
	@echo "  • Suitable for: Development, testing, resource-constrained environments"
	@echo ""
	@echo "⚠️  Trade-offs:"
	@echo "  • No high availability (single point of failure per service)"
	@echo "  • Reduced throughput under high load"
	@echo "  • Suitable for development and testing scenarios" 