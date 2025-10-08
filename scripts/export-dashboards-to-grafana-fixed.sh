#!/bin/bash

# Export Trading System Dashboards to Grafana (Fixed Version)
# Handles both dashboard JSON formats

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

echo -e "${BLUE}🚀 Trading System Dashboard Exporter (Fixed)${NC}"
echo -e "${YELLOW}===========================================${NC}"
echo ""
echo "Target Grafana: ${GRAFANA_URL}"
echo "Dashboard Directory: ${DASHBOARD_DIR}"
echo ""

# Test Grafana connection
echo -e "${YELLOW}Testing Grafana connection...${NC}"
if ! curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Grafana at ${GRAFANA_URL}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Connected to Grafana${NC}"
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
    
    # Check if dashboard JSON already has "dashboard" wrapper
    if echo "${dashboard_json}" | jq -e '.dashboard' > /dev/null 2>&1; then
        # Already has wrapper, just add overwrite
        import_payload=$(echo "${dashboard_json}" | jq '. + {"overwrite": true}')
    else
        # Check if it has a title
        title=$(echo "${dashboard_json}" | jq -r '.title // empty' 2>/dev/null)
        if [ -z "${title}" ]; then
            echo -e "${YELLOW}  ⚠️  Skipped (no title found)${NC}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            echo ""
            continue
        fi
        
        # Wrap in dashboard object
        import_payload=$(cat <<EOF
{
  "dashboard": ${dashboard_json},
  "overwrite": true
}
EOF
)
    fi
    
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
    else
        echo -e "${RED}  ❌ Failed${NC}"
        error_msg=$(echo "${response}" | jq -r '.message // "Unknown error"' 2>/dev/null || echo "Unknown error")
        echo -e "  ${RED}Error: ${error_msg}${NC}"
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

# List successfully imported dashboards
if [ ${SUCCESS_COUNT} -gt 0 ]; then
    echo -e "${YELLOW}Successfully Imported Dashboards:${NC}"
    curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_URL}/api/search?type=dash-db&limit=100" | \
        jq -r '.[] | "  • \(.title) - \(.url)"' 2>/dev/null | head -20
fi
echo ""

