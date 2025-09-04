#!/bin/bash

# 🚀 Migration Wrapper Script
# Ensures virtual environment is activated before running migration commands

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "migration-env" ]; then
    echo -e "${YELLOW}⚠️ Migration virtual environment not found.${NC}"
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv migration-env
    
    echo -e "${BLUE}Installing dependencies...${NC}"
    source migration-env/bin/activate
    pip install -r migration-requirements.txt
    echo -e "${GREEN}✅ Virtual environment created and dependencies installed!${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}🐍 Activating migration virtual environment...${NC}"
source migration-env/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated: $VIRTUAL_ENV${NC}"

# Pass all arguments to the migration script
echo -e "${BLUE}🚀 Running migration command: $@${NC}"
./scripts/execute-migration.sh "$@"

