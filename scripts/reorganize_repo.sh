#!/bin/bash

# Repository Reorganization Script
# This script helps reorganize the Space Trading Station repository

set -e

echo "🚀 Space Trading Station - Repository Reorganization"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        echo -e "${GREEN}Creating directory: $1${NC}"
        mkdir -p "$1"
    fi
}

# Function to move file with backup
move_file() {
    local src="$1"
    local dest="$2"
    
    if [ -f "$src" ]; then
        echo -e "${BLUE}Moving: $src → $dest${NC}"
        mkdir -p "$(dirname "$dest")"
        mv "$src" "$dest"
    else
        echo -e "${YELLOW}Warning: Source file not found: $src${NC}"
    fi
}

# Function to create README for directory
create_readme() {
    local dir="$1"
    local title="$2"
    local description="$3"
    
    if [ ! -f "$dir/README.md" ]; then
        echo -e "${GREEN}Creating README for: $dir${NC}"
        cat > "$dir/README.md" << EOF
# $title

$description

## Contents

This directory contains:

$(find "$dir" -maxdepth 1 -type f -name "*.py" -o -name "*.sh" -o -name "*.md" | sed 's|.*/||' | sort | sed 's/^/- /')

## Usage

See the main [README.md](../../README.md) for usage instructions.
EOF
    fi
}

echo -e "${GREEN}Phase 1: Creating new directory structure...${NC}"

# Create main directories
create_dir "demos"
create_dir "demos/monitor"
create_dir "demos/api"
create_dir "demos/backtest"
create_dir "demos/strategies"

create_dir "analysis"
create_dir "analysis/performance"
create_dir "analysis/backtest"

create_dir "tools"
create_dir "tools/data"
create_dir "tools/testing"
create_dir "tools/debugging"

create_dir "config"

create_dir "docker"
create_dir "docker/development"
create_dir "docker/services"

create_dir "scripts/deploy"
create_dir "scripts/setup"
create_dir "scripts/maintenance"
create_dir "scripts/cli"

create_dir "docs/guides"
create_dir "docs/guides/architecture"
create_dir "docs/guides/deployment"
create_dir "docs/guides/development"
create_dir "docs/guides/monitoring"
create_dir "docs/guides/strategies"
create_dir "docs/guides/news"
create_dir "docs/guides/data"
create_dir "docs/api"
create_dir "docs/tutorials"
create_dir "docs/reference"

echo -e "${GREEN}Phase 2: Moving demo files...${NC}"

# Move demo files
move_file "demo_monitor.py" "demos/monitor/demo_monitor.py"
move_file "demo_monitor_with_api.py" "demos/monitor/demo_monitor_with_api.py"
move_file "space_station_monitor.py" "demos/monitor/space_station_monitor.py"

move_file "demo_backtest_api.py" "demos/api/demo_backtest_api.py"

move_file "demo_news_backtest.py" "demos/backtest/demo_news_backtest.py"
move_file "demo_llm_trading_strategy.py" "demos/backtest/demo_llm_trading_strategy.py"
move_file "demo_all_ai_strategies.py" "demos/backtest/demo_all_ai_strategies.py"

echo -e "${GREEN}Phase 3: Moving analysis files...${NC}"

# Move analysis files
move_file "analyze_portfolio_performance.py" "analysis/performance/analyze_portfolio_performance.py"
move_file "analyze_real_portfolio_performance.py" "analysis/performance/analyze_real_portfolio_performance.py"
move_file "analyze_fixed_portfolio_performance.py" "analysis/performance/analyze_fixed_portfolio_performance.py"

move_file "run_comprehensive_historical_backtest.py" "analysis/backtest/run_comprehensive_historical_backtest.py"
move_file "run_historical_greeks_backtest.py" "analysis/backtest/run_historical_greeks_backtest.py"
move_file "run_greeks_comprehensive_backtest.py" "analysis/backtest/run_greeks_comprehensive_backtest.py"
move_file "run_news_enhanced_backtest.py" "analysis/backtest/run_news_enhanced_backtest.py"
move_file "run_portfolio_backtest.py" "analysis/backtest/run_portfolio_backtest.py"
move_file "run_backtest_with_real_data.py" "analysis/backtest/run_backtest_with_real_data.py"

echo -e "${GREEN}Phase 4: Moving tool files...${NC}"

# Move tool files
move_file "scan_backtest_data.py" "tools/data/scan_backtest_data.py"
move_file "populate_2year_data.py" "tools/data/populate_2year_data.py"
move_file "populate_2year_data_simple.py" "tools/data/populate_2year_data_simple.py"
move_file "store_2year_data.py" "tools/data/store_2year_data.py"
move_file "fetch_and_store_polygon_data.py" "tools/data/fetch_and_store_polygon_data.py"
move_file "build_backtest_data.py" "tools/data/build_backtest_data.py"

move_file "test_database_storage.py" "tools/testing/test_database_storage.py"
move_file "test_llm_analysis.py" "tools/testing/test_llm_analysis.py"
move_file "test_import.py" "tools/testing/test_import.py"
move_file "test_db_connection.py" "tools/testing/test_db_connection.py"
move_file "test_historical_greeks_direct.py" "tools/testing/test_historical_greeks_direct.py"
move_file "test_polygon_options_access.py" "tools/testing/test_polygon_options_access.py"
move_file "verify_ollama_model.py" "tools/testing/verify_ollama_model.py"

move_file "debug_config.py" "tools/debugging/debug_config.py"
move_file "fix_llm_column.py" "tools/debugging/fix_llm_column.py"
move_file "logging_config.py" "tools/debugging/logging_config.py"

echo -e "${GREEN}Phase 5: Moving configuration files...${NC}"

# Move config files
move_file "config.env.example" "config/config.env.example"
move_file "alembic.ini" "config/alembic.ini"
move_file "pytest.ini" "config/pytest.ini"
move_file ".dockerignore" "config/.dockerignore"
move_file ".pre-commit-config.yaml" "config/.pre-commit-config.yaml"

echo -e "${GREEN}Phase 6: Moving Docker files...${NC}"

# Move Docker files
move_file "Dockerfile.dev" "docker/development/Dockerfile.dev"
move_file "Dockerfile.k8s" "docker/development/Dockerfile.k8s"
move_file "Dockerfile.quick-wins" "docker/development/Dockerfile.quick-wins"

move_file "docker-compose.yml" "docker/docker-compose.yml"
move_file "docker-compose.dev.yml" "docker/docker-compose.dev.yml"
move_file "docker-compose.quick-wins.yml" "docker/docker-compose.quick-wins.yml"
move_file "docker-compose.registry.yml" "docker/docker-compose.registry.yml"

echo -e "${GREEN}Phase 7: Moving script files...${NC}"

# Move script files
move_file "deploy-all-services.sh" "scripts/deploy/deploy-all-services.sh"
move_file "deploy-health-dashboard.sh" "scripts/deploy/deploy-health-dashboard.sh"
move_file "deploy.sh" "scripts/deploy/deploy.sh"

move_file "setup_polygon_secret.sh" "scripts/setup/setup_polygon_secret.sh"
move_file "quick-start.sh" "scripts/setup/quick-start.sh"
move_file "quick-start-secure.sh" "scripts/setup/quick-start-secure.sh"

move_file "fix_k8s_containers.sh" "scripts/maintenance/fix_k8s_containers.sh"
move_file "create_services.py" "scripts/maintenance/create_services.py"

move_file "backtest_cli.py" "scripts/cli/backtest_cli.py"
move_file "trading_cli.py" "scripts/cli/trading_cli.py"
move_file "kube_backtest_cli.py" "scripts/cli/kube_backtest_cli.py"
move_file "log_manager.py" "scripts/cli/log_manager.py"
move_file "replay_events.py" "scripts/cli/replay_events.py"

echo -e "${GREEN}Phase 8: Moving documentation files...${NC}"

# Move documentation files
move_file "AI_ENHANCED_STRATEGIES_GUIDE.md" "docs/guides/strategies/AI_ENHANCED_STRATEGIES_GUIDE.md"

move_file "MONITOR_API_GUIDE.md" "docs/guides/monitoring/MONITOR_API_GUIDE.md"
move_file "MONITOR_API_CHECKLIST.md" "docs/guides/monitoring/MONITOR_API_CHECKLIST.md"
move_file "QUICK_REFERENCE.md" "docs/guides/monitoring/QUICK_REFERENCE.md"

move_file "ARCHITECTURE_DIAGRAM.md" "docs/guides/architecture/ARCHITECTURE_DIAGRAM.md"
move_file "SPACE_STATION_ARCHITECTURE_DIAGRAMS.md" "docs/guides/architecture/SPACE_STATION_ARCHITECTURE_DIAGRAMS.md"
move_file "architecture.md" "docs/guides/architecture/architecture.md"

move_file "DEPLOYMENT.md" "docs/guides/deployment/DEPLOYMENT.md"
move_file "KUBERNETES_FIRST_GUIDE.md" "docs/guides/deployment/KUBERNETES_FIRST_GUIDE.md"
move_file "CONTAINER_FIRST_GUIDE.md" "docs/guides/deployment/CONTAINER_FIRST_GUIDE.md"
move_file "LOCAL_REGISTRY_GUIDE.md" "docs/guides/deployment/LOCAL_REGISTRY_GUIDE.md"
move_file "SECURE_ARCHITECTURE_GUIDE.md" "docs/guides/deployment/SECURE_ARCHITECTURE_GUIDE.md"

move_file "DEVELOPMENT_RULES.md" "docs/guides/development/DEVELOPMENT_RULES.md"
move_file "MAKEFILE_MODULAR_GUIDE.md" "docs/guides/development/MAKEFILE_MODULAR_GUIDE.md"
move_file "MAKEFILE_REFERENCE.md" "docs/guides/development/MAKEFILE_REFERENCE.md"
move_file "CURSOR_RULES_SUMMARY.md" "docs/guides/development/CURSOR_RULES_SUMMARY.md"

move_file "NEWS_AI_GUIDE.md" "docs/guides/news/NEWS_AI_GUIDE.md"
move_file "NEWS_BOT_GUIDE.md" "docs/guides/news/NEWS_BOT_GUIDE.md"
move_file "HISTORICAL_NEWS_GUIDE.md" "docs/guides/news/HISTORICAL_NEWS_GUIDE.md"
move_file "KUBERNETES_NEWS_DEPLOYMENT.md" "docs/guides/news/KUBERNETES_NEWS_DEPLOYMENT.md"
move_file "NEWS_TRADING_IMPACT_DIAGRAM.md" "docs/guides/news/NEWS_TRADING_IMPACT_DIAGRAM.md"

move_file "MARKET_DATA_GUIDE.md" "docs/guides/data/MARKET_DATA_GUIDE.md"
move_file "YAHOO_FINANCE_GUIDE.md" "docs/guides/data/YAHOO_FINANCE_GUIDE.md"
move_file "RABBITMQ_WORKERS_GUIDE.md" "docs/guides/data/RABBITMQ_WORKERS_GUIDE.md"
move_file "EVENT_REPLAY_GUIDE.md" "docs/guides/data/EVENT_REPLAY_GUIDE.md"

move_file "QUICKSTART.md" "docs/reference/QUICKSTART.md"
move_file "QUICK_WINS_SUMMARY.md" "docs/reference/QUICK_WINS_SUMMARY.md"
move_file "TODO.md" "docs/reference/TODO.md"

echo -e "${GREEN}Phase 9: Creating README files...${NC}"

# Create README files for new directories
create_readme "demos" "Demos & Examples" "Interactive demonstrations of the Space Trading Station features."
create_readme "demos/monitor" "Monitor Demos" "Real-time monitoring and dashboard demonstrations."
create_readme "demos/api" "API Demos" "Backtest API and service demonstrations."
create_readme "demos/backtest" "Backtest Demos" "Backtesting strategy demonstrations."
create_readme "demos/strategies" "Strategy Demos" "Trading strategy demonstrations."

create_readme "analysis" "Analysis Tools" "Performance analysis and backtesting tools."
create_readme "analysis/performance" "Performance Analysis" "Portfolio and performance analysis scripts."
create_readme "analysis/backtest" "Backtest Analysis" "Backtesting and strategy analysis scripts."

create_readme "tools" "Development Tools" "Utilities and tools for development and debugging."
create_readme "tools/data" "Data Tools" "Data processing and management tools."
create_readme "tools/testing" "Testing Tools" "Testing and verification tools."
create_readme "tools/debugging" "Debugging Tools" "Debugging and troubleshooting tools."

create_readme "scripts" "Scripts" "Deployment, setup, and maintenance scripts."
create_readme "scripts/deploy" "Deployment Scripts" "Scripts for deploying services and applications."
create_readme "scripts/setup" "Setup Scripts" "Scripts for initial setup and configuration."
create_readme "scripts/maintenance" "Maintenance Scripts" "Scripts for system maintenance and fixes."
create_readme "scripts/cli" "CLI Tools" "Command-line interface tools."

create_readme "config" "Configuration" "Configuration files and templates."

create_readme "docker" "Docker" "Docker configuration and container definitions."

echo -e "${GREEN}Phase 10: Updating .gitignore...${NC}"

# Update .gitignore to include new directories
if ! grep -q "backups/" .gitignore; then
    echo "" >> .gitignore
    echo "# Reorganized directories" >> .gitignore
    echo "backups/" >> .gitignore
fi

echo -e "${GREEN}✅ Repository reorganization complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review the new structure"
echo "2. Update import paths in Python files"
echo "3. Update Makefile paths"
echo "4. Test that everything still works"
echo "5. Update documentation references"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- Check for any broken import paths"
echo "- Update any hardcoded file paths"
echo "- Test the demos and tools"
echo "- Update CI/CD pipeline if needed"
echo ""
echo "This is ORION, Mission Control. Repository reorganization complete! 🚀" 