# Central Hub Dashboard Guide

## Overview

The **Central Hub Dashboard** is your main navigation center for the entire Space Trading Station. It provides a unified interface to access all services, dashboards, and tools in your trading system.

## 🚀 Quick Start

### 1. Build and Deploy
```bash
# Build and deploy the central hub
make build-hub

# Or manually:
./scripts/build_central_hub.sh
```

### 2. Access the Hub
```bash
# Start port-forward to access the hub
make central-hub

# Then open: http://localhost:11080
```

## 📊 Available Services

The Central Hub provides access to all your trading system services:

### Core Trading
- **📊 Trading Dashboard** - Main trading interface with portfolio, trades, and positions
- **🧪 Backtest API** - Backtest request form and results

### Analytics
- **📋 Backtest Reports** - HTML reports and analysis from backtest runs
- **📊 Analytics Service** - Advanced analytics and data processing
- **📈 Performance Dashboard** - Trading performance metrics and analytics

### Monitoring
- **🏥 Health Dashboard** - System health monitoring and service status
- **📡 RSS Feed Dashboard** - Real-time RSS feed monitoring and alerts

### API & Integration
- **🌐 API Gateway** - Central API gateway and service documentation

## 🎯 Key Features

### Real-time Status Monitoring
- **Service Health Checks** - Automatic monitoring of all services
- **Status Indicators** - Visual indicators showing online/offline status
- **Response Time Tracking** - Monitor service performance

### Quick Actions
- **One-Click Access** - Direct links to all services
- **Quick Launch Buttons** - Most commonly used services
- **Auto-refresh** - Dashboard updates every 30 seconds

### Service Categories
- **Organized Layout** - Services grouped by category
- **Visual Design** - Color-coded service cards
- **Responsive Design** - Works on desktop and mobile

## 🔧 Configuration

### Environment Variables
The central hub uses these environment variables to connect to services:

```bash
TRADING_DASHBOARD_URL=http://trading-dashboard-service:80
HEALTH_DASHBOARD_URL=http://health-dashboard:80
PERFORMANCE_DASHBOARD_URL=http://performance-dashboard:80
RSS_DASHBOARD_URL=http://rss-dashboard:80
GATEWAY_URL=http://trading-gateway:80
BACKTEST_API_URL=http://backtest-api:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8000
```

### Service Definitions
Services are defined in the `SERVICES` dictionary in `main.py`:

```python
SERVICES = {
    "trading": {
        "name": "📊 Trading Dashboard",
        "description": "Main trading interface with portfolio, trades, and positions",
        "url": config.TRADING_DASHBOARD_URL,
        "category": "Core Trading",
        "icon": "📈",
        "color": "#2E86AB"
    },
    # ... more services
}
```

## 📋 API Endpoints

### Main Dashboard
- `GET /` - Main hub dashboard page
- `GET /health` - Health check endpoint

### Service Status
- `GET /api/services` - Get all services with their status

Example response:
```json
{
  "services": {
    "trading": {
      "name": "📊 Trading Dashboard",
      "description": "Main trading interface...",
      "url": "http://trading-dashboard-service:80",
      "category": "Core Trading",
      "icon": "📈",
      "color": "#2E86AB",
      "status": {
        "id": "trading",
        "status": "online",
        "response_time": 0.123,
        "last_check": "2024-01-15T10:30:00"
      }
    }
  },
  "total": 8,
  "online": 7,
  "offline": 1
}
```

## 🛠️ Development

### Local Development
```bash
# Run locally
cd services/central-hub-dashboard
python main.py

# Access at: http://localhost:11080
# For production port-forward: http://localhost:11080
```

### Adding New Services
1. Add service definition to `SERVICES` dictionary
2. Add environment variable for service URL
3. Update Kubernetes deployment with new environment variable
4. Rebuild and redeploy

### Customizing the UI
- **CSS Styles** - Modify the embedded CSS in `main.py`
- **Service Cards** - Update the card template in `_generate_category_sections()`
- **Quick Actions** - Add new action buttons to the quick actions section

## 🔍 Troubleshooting

### Service Not Showing
- Check if service is deployed in Kubernetes
- Verify environment variables are set correctly
- Check service health endpoint is responding

### Status Check Failures
- Verify network connectivity between services
- Check service URLs are correct
- Ensure services have `/health` endpoints

### Port Forward Issues
```bash
# Check if port is already in use
lsof -i :11080

# Use different port in 11000-11999 range
kubectl port-forward service/central-hub-dashboard 11081:80 -n trading-system
```

## 📈 Monitoring

### Health Checks
The hub performs health checks on all services:
- **Timeout**: 5 seconds per service
- **Frequency**: Every page load
- **Endpoint**: `/health` on each service

### Status Tracking
- **Online**: Service responds with 200 OK
- **Offline**: Service unreachable or returns error
- **Response Time**: Tracked for performance monitoring

## 🚀 Deployment

### Kubernetes Deployment
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/trading-platform-comprehensive.yaml

# Check deployment status
kubectl get pods -n trading-system -l app=central-hub-dashboard

# View logs
kubectl logs -f deployment/central-hub-dashboard -n trading-system
```

### Docker Build
```bash
# Build image
docker build -t localhost:32000/central-hub-dashboard:latest services/central-hub-dashboard/

# Push to registry
docker push localhost:32000/central-hub-dashboard:latest
```

## 🎯 Best Practices

### Service Organization
- **Group Related Services** - Use categories to organize services
- **Clear Descriptions** - Provide helpful descriptions for each service
- **Consistent Icons** - Use appropriate icons for visual recognition

### Performance
- **Async Health Checks** - Perform health checks asynchronously
- **Caching** - Consider caching service status for better performance
- **Error Handling** - Gracefully handle service failures

### User Experience
- **Quick Access** - Provide direct links to most-used services
- **Status Visibility** - Clear indication of service availability
- **Responsive Design** - Ensure mobile compatibility

## 🔗 Integration

### With Existing Dashboards
The central hub integrates with all your existing dashboards:
- **Trading Dashboard** - Portfolio and trading data
- **Health Dashboard** - System monitoring
- **Performance Dashboard** - Analytics and metrics
- **RSS Dashboard** - Feed monitoring

### With Reports System
- **Direct Access** - Link to backtest reports
- **Status Monitoring** - Check report generation status
- **Quick Navigation** - Easy access to latest reports

## 📚 Related Documentation

- [Trading Dashboard Guide](TRADING_DASHBOARD_GUIDE.md)
- [HTML Reports Guide](HTML_REPORT_GUIDE.md)
- [Kubernetes Deployment Guide](KUBERNETES_DEPLOYMENT_GUIDE.md)
- [Service Architecture Guide](SERVICE_ARCHITECTURE_GUIDE.md)

---

**🎉 The Central Hub Dashboard provides a unified interface to navigate your entire trading system!** 