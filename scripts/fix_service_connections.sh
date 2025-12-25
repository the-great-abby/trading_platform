#!/bin/bash
# Fix Service Connection Issues
# Automatically fixes database and RabbitMQ connection URLs in Kubernetes deployments

set -e

echo "🔧 Service Connection Fixer"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fix 1: market-data-service database connection
echo -e "${CYAN}Fix 1: Updating market-data-service database connection...${NC}"

kubectl patch deployment market-data-service -n trading-system --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/env",
    "value": [
      {
        "name": "DATABASE_URL",
        "value": "postgresql://postgres:password@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot"
      },
      {
        "name": "REDIS_URL",
        "value": "redis://redis.redis.svc.cluster.local:6379"
      },
      {
        "name": "LOG_LEVEL",
        "value": "INFO"
      },
      {
        "name": "ENVIRONMENT",
        "value": "production"
      },
      {
        "name": "PORT",
        "value": "8000"
      },
      {
        "name": "POLYGON_API_KEY",
        "valueFrom": {
          "secretKeyRef": {
            "name": "trading-secrets",
            "key": "polygon_api_key"
          }
        }
      },
      {
        "name": "ALPHA_VANTAGE_API_KEY",
        "valueFrom": {
          "secretKeyRef": {
            "name": "trading-secrets",
            "key": "alpha_vantage_api_key"
          }
        }
      },
      {
        "name": "IEX_CLOUD_API_KEY",
        "valueFrom": {
          "secretKeyRef": {
            "name": "trading-secrets",
            "key": "iex-cloud-api-key",
            "optional": true
          }
        }
      }
    ]
  }
]'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ market-data-service database connection updated${NC}"
else
    echo -e "${RED}❌ Failed to update market-data-service${NC}"
    exit 1
fi

echo ""

# Fix 2: rss-feed-service RabbitMQ connection
echo -e "${CYAN}Fix 2: Updating rss-feed-service RabbitMQ connection...${NC}"

kubectl patch deployment rss-feed-service -n trading-system --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/env",
    "value": [
      {
        "name": "STRATEGY_SERVICE_URL",
        "value": "http://strategy-service:80"
      },
      {
        "name": "DATABASE_URL",
        "value": "postgresql://postgres:password@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot"
      },
      {
        "name": "RABBITMQ_URL",
        "value": "amqp://guest:guest@rabbitmq.rabbitmq-system.svc.cluster.local:5672/"
      },
      {
        "name": "LOG_LEVEL",
        "value": "INFO"
      },
      {
        "name": "POLYGON_API_KEY",
        "valueFrom": {
          "secretKeyRef": {
            "name": "trading-secrets",
            "key": "polygon_api_key"
          }
        }
      }
    ]
  }
]'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ rss-feed-service RabbitMQ connection updated${NC}"
else
    echo -e "${RED}❌ Failed to update rss-feed-service${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All service connections fixed!${NC}"
echo ""
echo -e "${YELLOW}Waiting for pods to restart...${NC}"
echo ""

# Wait for pods to restart
kubectl wait --for=condition=ready pod -l app=market-data-service -n trading-system --timeout=120s 2>/dev/null || echo "Note: market-data-service may take longer to become ready"
kubectl wait --for=condition=ready pod -l app=rss-feed-service -n trading-system --timeout=120s 2>/dev/null || echo "Note: rss-feed-service may take longer to become ready"

echo ""
echo -e "${CYAN}Checking pod status...${NC}"
kubectl get pods -n trading-system | grep -E "(market-data-service|rss-feed-service)"

echo ""
echo -e "${GREEN}🎉 Service restoration complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Verify services are running: ${CYAN}kubectl get pods -n trading-system${NC}"
echo "  2. Check logs: ${CYAN}kubectl logs -n trading-system deployment/market-data-service${NC}"
echo "  3. Use wizard for full system status: ${CYAN}make wizard${NC}"
echo ""








