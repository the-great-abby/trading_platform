# Trading Platform Service Management
# Easy commands to start/stop services in optimized configuration

.PHONY: help status start-all stop-all start-core stop-core start-heavy stop-heavy start-dashboards stop-dashboards start-workers stop-workers start-management stop-management scale-down scale-up logs

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
	@echo "Dashboard services started"

# Stop dashboard services
stop-dashboards:
	@echo "Stopping dashboard services..."
	kubectl scale deployment trading-dashboard-service --replicas=0 -n trading-system
	kubectl scale deployment performance-dashboard --replicas=0 -n trading-system
	kubectl scale deployment rss-dashboard --replicas=0 -n trading-system
	kubectl scale deployment rss-feed-service --replicas=0 -n trading-system
	@echo "Dashboard services stopped"

# Start worker services
start-workers:
	@echo "Starting worker services..."
	kubectl scale deployment order-worker --replicas=1 -n trading-system
	kubectl scale deployment strategy-worker --replicas=1 -n trading-system
	kubectl scale deployment signal-worker --replicas=1 -n trading-system
	kubectl scale deployment risk-worker --replicas=1 -n trading-system
	kubectl scale deployment notification-worker --replicas=1 -n trading-system
	@echo "Worker services started"

# Stop worker services
stop-workers:
	@echo "Stopping worker services..."
	kubectl scale deployment order-worker --replicas=0 -n trading-system
	kubectl scale deployment strategy-worker --replicas=0 -n trading-system
	kubectl scale deployment signal-worker --replicas=0 -n trading-system
	kubectl scale deployment risk-worker --replicas=0 -n trading-system
	kubectl scale deployment notification-worker --replicas=0 -n trading-system
	@echo "Worker services stopped"

# Start management services
start-management:
	@echo "Starting management services..."
	kubectl scale deployment order-management-service --replicas=1 -n trading-system
	kubectl scale deployment strategy-management-service --replicas=1 -n trading-system
	kubectl scale deployment signal-management-service --replicas=1 -n trading-system
	kubectl scale deployment risk-management-service --replicas=1 -n trading-system
	@echo "Management services started"

# Stop management services
stop-management:
	@echo "Stopping management services..."
	kubectl scale deployment order-management-service --replicas=0 -n trading-system
	kubectl scale deployment strategy-management-service --replicas=0 -n trading-system
	kubectl scale deployment signal-management-service --replicas=0 -n trading-system
	kubectl scale deployment risk-management-service --replicas=0 -n trading-system
	@echo "Management services stopped"

# Scale down to minimal configuration (core + management only)
scale-down:
	@echo "Scaling down to minimal configuration..."
	$(MAKE) stop-heavy
	$(MAKE) stop-dashboards
	$(MAKE) stop-workers
	$(MAKE) start-core
	$(MAKE) start-management
	@echo "Minimal configuration active"

# Scale up to full configuration
scale-up:
	@echo "Scaling up to full configuration..."
	$(MAKE) start-all
	@echo "Full configuration active"

# Show logs for a specific service
logs:
	@if [ -z "$(service)" ]; then \
		echo "Usage: make logs service=<service-name>"; \
		echo "Example: make logs service=market-data-service"; \
		echo ""; \
		echo "Available services:"; \
		kubectl get deployments -n trading-system --no-headers | awk '{print $$1}'; \
	else \
		echo "Showing logs for $(service)..."; \
		kubectl logs -f deployment/$(service) -n trading-system; \
	fi

# Set up port forwarding for dashboards
port-forward:
	@echo "Setting up port forwarding..."
	@echo "Central Hub Dashboard: http://localhost:11080"
	@echo "Health Dashboard: http://localhost:11081"
	@echo "Trading Dashboard: http://localhost:11082"
	@echo ""
	@echo "Starting port forwarding (Ctrl+C to stop)..."
	kubectl port-forward service/central-hub-dashboard 11080:80 -n trading-system &
	kubectl port-forward service/health-dashboard 11081:80 -n trading-system &
	kubectl port-forward service/trading-dashboard-service 11082:80 -n trading-system &
	@echo "Port forwarding started. Access dashboards at the URLs above."

# Quick status check
quick-status:
	@echo "=== Quick Status Check ==="
	@echo "Core Services:"
	kubectl get pods -n trading-system -l app=central-hub-dashboard --no-headers | awk '{print "  " $$1 ": " $$3}'
	kubectl get pods -n trading-system -l app=trading-gateway --no-headers | awk '{print "  " $$1 ": " $$3}'
	@echo ""
	@echo "Management Services:"
	kubectl get pods -n trading-system -l app=order-management-service --no-headers | awk '{print "  " $$1 ": " $$3}'
	kubectl get pods -n trading-system -l app=strategy-management-service --no-headers | awk '{print "  " $$1 ": " $$3}'
	kubectl get pods -n trading-system -l app=signal-management-service --no-headers | awk '{print "  " $$1 ": " $$3}'
	kubectl get pods -n trading-system -l app=risk-management-service --no-headers | awk '{print "  " $$1 ": " $$3}'
	@echo ""
	@echo "Heavy Services:"
	kubectl get pods -n trading-system -l app=market-data-service --no-headers | awk '{print "  " $$1 ": " $$3}'
	kubectl get pods -n trading-system -l app=analytics-service --no-headers | awk '{print "  " $$1 ": " $$3}'

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