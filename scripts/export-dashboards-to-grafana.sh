#!/bin/bash

# Export Trading System Dashboards to Grafana
# Target: http://localhost:14000/dashboards

set -e

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:14000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
DASHBOARD_DIR="./monitoring/grafana/dashboards"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Trading System Dashboard Exporter${NC}"
echo -e "${YELLOW}====================================${NC}"
echo ""
echo "Target Grafana: ${GRAFANA_URL}"
echo "Dashboard Directory: ${DASHBOARD_DIR}"
echo ""

# Test Grafana connection
echo -e "${YELLOW}Testing Grafana connection...${NC}"
if ! curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Grafana at ${GRAFANA_URL}${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if Grafana is running: curl ${GRAFANA_URL}/api/health"
    echo "  2. Verify credentials (default: admin/admin)"
    echo "  3. Try port forwarding: kubectl port-forward svc/grafana 14000:3000 -n trading-system"
    exit 1
fi

echo -e "${GREEN}✅ Connected to Grafana${NC}"
echo ""

# Create folder for trading dashboards
echo -e "${YELLOW}Creating 'Trading System' folder...${NC}"
FOLDER_RESPONSE=$(curl -s -X POST \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Trading System"}' \
  "${GRAFANA_URL}/api/folders" 2>&1)

FOLDER_UID=$(echo "${FOLDER_RESPONSE}" | grep -o '"uid":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "${FOLDER_UID}" ]; then
    echo -e "${GREEN}✅ Folder created with UID: ${FOLDER_UID}${NC}"
else
    echo -e "${YELLOW}⚠️  Folder might already exist, continuing...${NC}"
    # Try to get existing folder
    FOLDER_UID=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_URL}/api/folders" | \
        grep -o '"uid":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

echo ""

# Count dashboards
TOTAL_DASHBOARDS=$(ls -1 ${DASHBOARD_DIR}/*.json 2>/dev/null | wc -l | tr -d ' ')
echo -e "${BLUE}Found ${TOTAL_DASHBOARDS} dashboards to import${NC}"
echo ""

# Import dashboards
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

for dashboard_file in ${DASHBOARD_DIR}/*.json; do
    if [ ! -f "${dashboard_file}" ]; then
        continue
    fi
    
    dashboard_name=$(basename "${dashboard_file}" .json)
    echo -e "${YELLOW}Importing: ${dashboard_name}${NC}"
    
    # Read dashboard JSON
    dashboard_json=$(cat "${dashboard_file}")
    
    # Create import payload
    import_payload=$(cat <<EOF
{
  "dashboard": ${dashboard_json},
  "folderId": 0,
  "overwrite": true
}
EOF
)
    
    # Import dashboard
    response=$(curl -s -X POST \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -H "Content-Type: application/json" \
        -d "${import_payload}" \
        "${GRAFANA_URL}/api/dashboards/db" 2>&1)
    
    # Check result
    if echo "${response}" | grep -q '"status":"success"'; then
        dashboard_url=$(echo "${response}" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}  ✅ Imported successfully${NC}"
        echo -e "  ${BLUE}URL: ${GRAFANA_URL}${dashboard_url}${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    elif echo "${response}" | grep -q '"message":"Dashboard not found"'; then
        echo -e "${YELLOW}  ⚠️  Skipped (invalid format)${NC}"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    else
        echo -e "${RED}  ❌ Failed${NC}"
        echo -e "  ${RED}Error: ${response}${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}📊 Import Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Success: ${SUCCESS_COUNT}${NC}"
echo -e "${YELLOW}⚠️  Skipped: ${SKIPPED_COUNT}${NC}"
echo -e "${RED}❌ Failed: ${FAILED_COUNT}${NC}"
echo -e "${BLUE}📊 Total: ${TOTAL_DASHBOARDS}${NC}"
echo ""
echo -e "${GREEN}🎉 Done! View your dashboards at:${NC}"
echo -e "${BLUE}${GRAFANA_URL}/dashboards${NC}"
echo ""

# List key dashboards
echo -e "${YELLOW}Key Dashboards:${NC}"
echo "  • Trading System Overview"
echo "  • Strategy Performance"
echo "  • Order Execution"
echo "  • Risk Management"
echo "  • Market Data"
echo "  • System Infrastructure"
echo ""

