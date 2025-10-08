#!/bin/bash

# Configure Grafana Data Source for Prometheus
set -e

GRAFANA_URL="${GRAFANA_URL:-http://localhost:14000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📊 Configuring Grafana Data Source${NC}"
echo ""

# Check if data source already exists
echo "Checking for existing Prometheus data source..."
EXISTING_DS=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "${GRAFANA_URL}/api/datasources/name/Prometheus" 2>/dev/null)

if echo "${EXISTING_DS}" | grep -q '"id"'; then
    DS_ID=$(echo "${EXISTING_DS}" | jq -r '.id')
    echo -e "${YELLOW}Found existing data source (ID: ${DS_ID}), updating...${NC}"
    
    # Update existing data source
    curl -X PUT \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -H "Content-Type: application/json" \
        -d '{
            "id": '"${DS_ID}"',
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus.trading-system.svc.cluster.local:9090",
            "access": "proxy",
            "isDefault": true,
            "jsonData": {
                "httpMethod": "POST",
                "timeInterval": "15s"
            }
        }' \
        "${GRAFANA_URL}/api/datasources/${DS_ID}"
else
    echo -e "${YELLOW}Creating new Prometheus data source...${NC}"
    
    # Create new data source
    curl -X POST \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus.trading-system.svc.cluster.local:9090",
            "access": "proxy",
            "isDefault": true,
            "jsonData": {
                "httpMethod": "POST",
                "timeInterval": "15s"
            }
        }' \
        "${GRAFANA_URL}/api/datasources"
fi

echo ""
echo -e "${GREEN}✅ Data source configured!${NC}"
echo ""

# Test the connection
echo "Testing Prometheus connection..."
curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "${GRAFANA_URL}/api/datasources/proxy/1/api/v1/query?query=up" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Prometheus connection successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Connection test failed, but data source is configured.${NC}"
    echo "Prometheus may need a moment to start scraping metrics."
fi

echo ""
echo -e "${YELLOW}Prometheus URL:${NC} http://prometheus.trading-system.svc.cluster.local:9090"
echo -e "${YELLOW}Grafana URL:${NC} ${GRAFANA_URL}"
echo ""

