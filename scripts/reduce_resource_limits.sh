#!/bin/bash

# Script to reduce resource limits for all services to prevent over-allocation
# This should help resolve network connectivity issues under resource constraints

echo "Reducing resource limits for all services..."

# Function to patch deployment with reduced resources
patch_deployment() {
    local deployment=$1
    local cpu_request=$2
    local mem_request=$3
    local cpu_limit=$4
    local mem_limit=$5
    
    echo "Patching $deployment with CPU: ${cpu_request}->${cpu_limit}, Memory: ${mem_request}->${mem_limit}"
    
    kubectl patch deployment $deployment -n trading-system -p "{
        \"spec\": {
            \"template\": {
                \"spec\": {
                    \"containers\": [{
                        \"name\": \"$deployment\",
                        \"resources\": {
                            \"requests\": {
                                \"cpu\": \"${cpu_request}\",
                                \"memory\": \"${mem_request}\"
                            },
                            \"limits\": {
                                \"cpu\": \"${cpu_limit}\",
                                \"memory\": \"${mem_limit}\"
                            }
                        }
                    }]
                }
            }
        }
    }"
}

# Critical services - very conservative limits
patch_deployment "ai-stock-dashboard" "50m" "64Mi" "100m" "128Mi"
patch_deployment "llm-service" "100m" "128Mi" "200m" "256Mi"
patch_deployment "llm-proxy" "50m" "64Mi" "100m" "128Mi"
patch_deployment "llm-worker" "50m" "64Mi" "100m" "128Mi"
patch_deployment "backtest-api" "100m" "128Mi" "200m" "256Mi"
patch_deployment "analytics-service" "25m" "32Mi" "50m" "64Mi"

# Data services - moderate limits
patch_deployment "market-data-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "market-data-worker" "50m" "64Mi" "100m" "128Mi"
patch_deployment "rss-feed-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "data-analysis-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "data-processing-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "data-transformation-pipeline" "50m" "64Mi" "100m" "128Mi"

# Database services - conservative but adequate
patch_deployment "postgres-dev" "100m" "128Mi" "200m" "256Mi"
patch_deployment "timescaledb" "100m" "128Mi" "200m" "256Mi"
patch_deployment "postgres-vector-storage" "50m" "64Mi" "100m" "128Mi"

# Dashboard services - minimal resources
patch_deployment "unified-analytics-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "unified-news-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "unified-trading-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "trading-dashboard-service" "25m" "32Mi" "50m" "64Mi"
patch_deployment "performance-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "health-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "data-pipeline-dashboard" "25m" "32Mi" "50m" "64Mi"
patch_deployment "rss-dashboard" "25m" "32Mi" "50m" "64Mi"

# API services - moderate limits
patch_deployment "backtest-request-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "public-api" "50m" "64Mi" "100m" "128Mi"
patch_deployment "order-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "portfolio-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "risk-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "strategy-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "trading-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "trading-ultra-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "notification-service" "50m" "64Mi" "100m" "128Mi"
patch_deployment "report-viewer-service" "50m" "64Mi" "100m" "128Mi"

# Infrastructure services - minimal but functional
patch_deployment "rabbitmq" "50m" "64Mi" "100m" "128Mi"
patch_deployment "redis" "25m" "32Mi" "50m" "64Mi"
patch_deployment "redis-dev" "25m" "32Mi" "50m" "64Mi"
patch_deployment "prometheus" "50m" "64Mi" "100m" "128Mi"
patch_deployment "grafana" "25m" "32Mi" "50m" "64Mi"

# AI services - moderate limits
patch_deployment "ai-analysis-service" "25m" "32Mi" "50m" "64Mi"

echo "Resource limits reduced. Waiting for pods to restart..."
sleep 10

echo "Current resource usage:"
kubectl top nodes
echo ""
echo "Pod status:"
kubectl get pods -n trading-system --no-headers | wc -l
echo "pods total" 