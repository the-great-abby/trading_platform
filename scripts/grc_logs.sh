#!/bin/bash
# Trading System Log Colorizer using grc
# Usage: ./scripts/grc_logs.sh <command>

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if grc is installed
if ! command -v grc &> /dev/null; then
    echo -e "${RED}Error: grc is not installed. Please install it with: brew install grc${NC}"
    exit 1
fi

# Check if custom config exists
CONFIG_FILE="$HOME/.grc/trading-logs.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Warning: Custom grc config not found at $CONFIG_FILE${NC}"
    echo -e "${BLUE}Using default grc configuration...${NC}"
    CONFIG_FILE=""
fi

# Function to show usage
show_usage() {
    echo -e "${GREEN}Trading System Log Colorizer${NC}"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Examples:"
    echo "  $0 'tail -f logs/trading_system.log'"
    echo "  $0 'kubectl logs -f pod/trading-service'"
    echo "  $0 'docker logs -f container_name'"
    echo "  $0 'cat logs/errors.log'"
    echo ""
    echo "Or pipe output:"
    echo "  tail -f logs/trading_system.log | $0"
    echo ""
}

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Execute command with grc
if [ -n "$CONFIG_FILE" ]; then
    echo -e "${GREEN}🎨 Using custom trading logs colorizer...${NC}"
    grc -c "$CONFIG_FILE" "$@"
else
    echo -e "${BLUE}🎨 Using default grc colorizer...${NC}"
    grc "$@"
fi 