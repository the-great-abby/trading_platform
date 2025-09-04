#!/bin/bash

# 🐍 Migration Virtual Environment Activation Script
# Activates the virtual environment for running migration scripts

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "migration-env" ]; then
    echo -e "${BLUE}Creating migration virtual environment...${NC}"
    python3 -m venv migration-env
    
    echo -e "${BLUE}Installing dependencies...${NC}"
    source migration-env/bin/activate
    pip install -r migration-requirements.txt
    echo -e "${GREEN}Virtual environment created and dependencies installed!${NC}"
else
    echo -e "${BLUE}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating migration virtual environment...${NC}"
source migration-env/bin/activate

# Verify activation
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✅ Virtual environment activated: $VIRTUAL_ENV${NC}"
    echo -e "${BLUE}Python: $(which python)${NC}"
    echo -e "${BLUE}Pip: $(which pip)${NC}"
    echo -e "${BLUE}Installed packages:${NC}"
    pip list | grep -E "(psycopg2|pyyaml|pandas|numpy)" || echo "No matching packages found"
    
    echo
    echo -e "${GREEN}🚀 Ready to run migration scripts!${NC}"
    echo -e "${BLUE}Example commands:${NC}"
    echo "  python3 ./scripts/migrate-data-to-external.py --test-connections"
    echo "  python3 ./scripts/update-service-configs.py --dry-run"
    echo "  ./scripts/execute-migration.sh migrate-all"
else
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

