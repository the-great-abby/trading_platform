#!/bin/bash

# 🔍 Trading System Observability Setup Script
# Deploys complete observability stack with distributed tracing

set -e

echo "🚀 Setting up Trading System Observability Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace trading-system &> /dev/null; then
    print_error "trading-system namespace does not exist. Please create it first."
    exit 1
fi

print_status "Starting observability stack deployment..."

# Step 1: Deploy Jaeger
print_status "Deploying Jaeger distributed tracing..."
kubectl apply -f monitoring/jaeger-deployment.yaml

# Wait for Jaeger to be ready
print_status "Waiting for Jaeger to be ready..."
kubectl wait --for=condition=ready pod -l app=jaeger -n trading-system --timeout=300s

if [ $? -eq 0 ]; then
    print_success "Jaeger deployed successfully"
else
    print_error "Jaeger deployment failed"
    exit 1
fi

# Step 2: Update Prometheus configuration to include tracing metrics
print_status "Updating Prometheus configuration..."
kubectl apply -f monitoring/monitoring-stack.yaml

# Step 3: Add the request tracing dashboard to Grafana
print_status "Adding request tracing dashboard to Grafana..."

# Create a temporary file with the dashboard
cat > /tmp/request-tracing-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Request Tracing & Bottleneck Analysis",
    "tags": ["trading-system", "observability", "tracing", "performance"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Flow Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "displayMode": "list",
              "orientation": "horizontal"
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Duration by Service",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))",
            "legendFormat": "95th percentile - {{service}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "drawStyle": "line",
              "lineInterpolation": "linear",
              "barAlignment": 0,
              "lineWidth": 1,
              "fillOpacity": 10,
              "gradientMode": "none",
              "spanNulls": false,
              "showPoints": "auto",
              "pointSize": 5,
              "stacking": {
                "mode": "none",
                "group": "A"
              },
              "axisLabel": "",
              "scaleDistribution": {
                "type": "linear"
              },
              "hideFrom": {
                "legend": false,
                "tooltip": false,
                "vis": false
              },
              "thresholds": {
                "steps": [
                  {
                    "color": "green",
                    "value": null
                  },
                  {
                    "color": "red",
                    "value": 80
                  }
                ],
                "mode": "absolute"
              },
              "unit": "s"
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {},
    "templating": {
      "list": []
    },
    "annotations": {
      "list": [
        {
          "builtIn": 1,
          "datasource": "-- Grafana --",
          "enable": true,
          "hide": true,
          "iconColor": "rgba(0, 211, 255, 1)",
          "name": "Annotations & Alerts",
          "type": "dashboard"
        }
      ]
    },
    "refresh": "5s",
    "schemaVersion": 27,
    "style": "dark",
    "tags": ["trading-system", "observability", "tracing"],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {},
    "timezone": "",
    "title": "Request Tracing & Bottleneck Analysis",
    "uid": "request-tracing-dashboard",
    "version": 1
  }
}
EOF

# Add the dashboard to the Grafana ConfigMap
kubectl patch configmap grafana-dashboards -n trading-system --patch-file /tmp/request-tracing-dashboard.json

# Clean up temporary file
rm /tmp/request-tracing-dashboard.json

# Step 4: Restart Grafana to pick up new dashboard
print_status "Restarting Grafana to load new dashboard..."
kubectl rollout restart deployment/grafana -n trading-system

# Wait for Grafana to be ready
print_status "Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n trading-system --timeout=300s

# Step 5: Set up port forwarding
print_status "Setting up port forwarding for observability tools..."

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Kill existing port forwards
print_status "Cleaning up existing port forwards..."
pkill -f "kubectl port-forward.*jaeger" || true
pkill -f "kubectl port-forward.*grafana" || true
pkill -f "kubectl port-forward.*prometheus" || true

sleep 2

# Start port forwarding
print_status "Starting port forwarding..."

# Jaeger UI
if ! check_port 16686; then
    kubectl port-forward service/jaeger 16686:16686 -n trading-system &
    print_success "Jaeger UI: http://localhost:16686"
else
    print_warning "Port 16686 is already in use. Jaeger UI may not be accessible."
fi

# Grafana
if ! check_port 11044; then
    kubectl port-forward service/grafana 11044:3000 -n trading-system &
    print_success "Grafana: http://localhost:11044 (admin/admin)"
else
    print_warning "Port 11044 is already in use. Grafana may not be accessible."
fi

# Prometheus
if ! check_port 11190; then
    kubectl port-forward service/prometheus 11190:11190 -n trading-system &
    print_success "Prometheus: http://localhost:11190"
else
    print_warning "Port 11190 is already in use. Prometheus may not be accessible."
fi

sleep 3

# Step 6: Verify services are running
print_status "Verifying observability services..."

# Check Jaeger
if kubectl get pods -n trading-system -l app=jaeger | grep -q "Running"; then
    print_success "Jaeger is running"
else
    print_error "Jaeger is not running properly"
fi

# Check Grafana
if kubectl get pods -n trading-system -l app=grafana | grep -q "Running"; then
    print_success "Grafana is running"
else
    print_error "Grafana is not running properly"
fi

# Check Prometheus
if kubectl get pods -n trading-system -l app=prometheus | grep -q "Running"; then
    print_success "Prometheus is running"
else
    print_error "Prometheus is not running properly"
fi

# Step 7: Test observability stack
print_status "Testing observability stack..."

# Test Jaeger health
if curl -s http://localhost:16686/api/services > /dev/null 2>&1; then
    print_success "Jaeger UI is accessible"
else
    print_warning "Jaeger UI may not be accessible yet. Wait a moment and try: http://localhost:16686"
fi

# Test Grafana health
if curl -s http://localhost:11044/api/health > /dev/null 2>&1; then
    print_success "Grafana is accessible"
else
    print_warning "Grafana may not be accessible yet. Wait a moment and try: http://localhost:11044"
fi

# Test Prometheus health
if curl -s http://localhost:11190/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus is accessible"
else
    print_warning "Prometheus may not be accessible yet. Wait a moment and try: http://localhost:11190"
fi

# Step 8: Display access information
echo ""
echo "🎉 Observability Stack Setup Complete!"
echo ""
echo "📊 Access URLs:"
echo "   Jaeger UI (Tracing):     http://localhost:16686"
echo "   Grafana (Dashboards):    http://localhost:11044 (admin/admin)"
echo "   Prometheus (Metrics):    http://localhost:11190"
echo ""
echo "🔍 Next Steps:"
echo "   1. Access Jaeger UI to view distributed traces"
echo "   2. Check Grafana for the 'Request Tracing & Bottleneck Analysis' dashboard"
echo "   3. Integrate tracing into your services using the provided utilities"
echo "   4. Monitor your system performance in real-time"
echo ""
echo "📚 Documentation:"
echo "   - Observability Guide: docs/OBSERVABILITY_GUIDE.md"
echo "   - Example Implementation: services/trading-service/main_with_tracing.py"
echo ""
echo "🛠️ To stop port forwarding:"
echo "   pkill -f 'kubectl port-forward'"
echo ""

print_success "Observability stack deployment completed successfully!"


