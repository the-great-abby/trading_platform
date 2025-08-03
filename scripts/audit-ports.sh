#!/bin/bash

# Trading System Port Audit Script
# Ensures all services use ports in the 11000-11999 range

set -e

NAMESPACE="trading-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Trading System Port Audit${NC}"
echo -e "${YELLOW}Checking for services outside 11000-11999 range...${NC}"
echo ""

# Get all services and their ports
SERVICES=$(kubectl get services -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.ports[0].port}{"\n"}{end}')

VIOLATIONS=0
COMPLIANT=0

echo -e "${BLUE}📊 Service Port Analysis:${NC}"
echo ""

while IFS=$'\t' read -r service port; do
    if [[ -n "$service" && -n "$port" ]]; then
        if [[ "$port" -ge 11000 && "$port" -le 11999 ]]; then
            echo -e "  ${GREEN}✅ $service: $port${NC}"
            ((COMPLIANT++))
        else
            echo -e "  ${RED}❌ $service: $port (VIOLATION)${NC}"
            ((VIOLATIONS++))
        fi
    fi
done <<< "$SERVICES"

echo ""
echo -e "${BLUE}📈 Summary:${NC}"
echo -e "  ${GREEN}Compliant services: $COMPLIANT${NC}"
echo -e "  ${RED}Violations: $VIOLATIONS${NC}"

if [[ $VIOLATIONS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All services are compliant with port range 11000-11999!${NC}"
    exit 0
else
    echo -e "${RED}🚨 Found $VIOLATIONS service(s) using ports outside 11000-11999 range${NC}"
    echo -e "${YELLOW}Please fix these violations to ensure consistent port allocation${NC}"
    exit 1
fi 