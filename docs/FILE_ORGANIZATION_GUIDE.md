# File Organization Guide

This document describes the reorganized file structure of the trading system.

## Overview

The codebase has been organized into logical directories to improve discoverability and maintainability.

## Directory Structure

```
trading/
├── simulations/        # Monte Carlo simulations for strategy testing
├── backtests/         # Real market data backtests
├── results/           # Backtest and simulation output files
├── tests/             # All test files
├── scripts/           # Utility and operational scripts
│   ├── analysis/      # Analysis and comparison scripts
│   └── monitoring/    # System and trading monitors
├── docs/              # All documentation
├── examples/          # Demo and example files
├── config/            # Configuration files
├── logs/              # Log files
├── src/               # Core application code
├── k8s/               # Kubernetes configurations
└── deploy/            # Deployment files
```

## Directory Purposes

### `simulations/`
**Purpose**: Monte Carlo simulations for quick strategy validation

**Contains**:
- Statistical trading simulations
- Options strategy simulations (Iron Condor, Butterfly Spread)
- Strategy comparison simulations

**When to use**: Quick "what if" testing before building full strategies

**See**: `simulations/README.md` for details

### `backtests/`
**Purpose**: Historical market data validation of trading strategies

**Contains**:
- Strategy-specific backtests
- Allocation backtests
- Comprehensive system backtests
- Platform-specific backtests (Public.com, etc.)

**When to use**: Validate strategies with real market data

**See**: `backtests/README.md` and `docs/BACKTESTING_GUIDE.md`

### `results/`
**Purpose**: Store output from backtests and simulations

**Contains**:
- JSON result files with timestamps
- Performance metrics
- Trade details

**Cleanup**: Consider removing results older than 30 days

**See**: `results/README.md`

### `tests/`
**Purpose**: All automated tests for the system

**Contains**:
- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`)
- Contract tests (`tests/contract/`)
- Strategy validation tests (`tests/strategy_validation/`)
- Live trading tests (`tests/live_trading/`)

**Run tests**: `pytest tests/` or specific test files

### `scripts/`
**Purpose**: Utility scripts for operations, analysis, and monitoring

**Subdirectories**:
- `analysis/` - Analyze backtest results, compare strategies, optimize allocations
- `monitoring/` - Monitor live trading, system health, strategy performance

**Contains**:
- Deployment scripts (`activate_*.py`, `deploy_*.py`)
- Strategy scripts (`automated_strategy_selector.py`)
- Utility scripts (`refresh_public_token.py`, `update_order_helper.py`)
- Shell scripts (`*.sh`)
- Run scripts (`run_*.py`)

### `examples/`
**Purpose**: Demo files and examples for learning

**Contains**:
- Demo scripts showing how to use various features
- Example implementations
- Tutorial code

### `docs/`
**Purpose**: All documentation and guides

**Contains**:
- Architecture documentation
- Setup guides
- API references
- Strategy guides
- Deployment guides
- Troubleshooting docs

**Organization**: Documentation is organized by topic with descriptive names

### `config/`
**Purpose**: Configuration files for the system

**Contains**:
- Strategy configs (`*_config.json`)
- Automation configs (`strategy_automation_config.yaml`)
- Dashboard imports
- Environment examples (`config.env.example`)

### `logs/`
**Purpose**: Log files from various services

**Contains**:
- Application logs
- Port monitor logs
- Service-specific logs

**Cleanup**: Logs can be rotated or removed periodically

### `src/`
**Purpose**: Core application code

**Contains**:
- Services
- Models
- Utilities
- Trading strategies
- API implementations

**Note**: This is the main codebase - don't move files from here

## File Types and Locations

| File Type | Location | Example |
|-----------|----------|---------|
| Simulations | `simulations/` | `realistic_trading_simulation.py` |
| Backtests | `backtests/` | `clean_backtest.py` |
| Tests | `tests/` | `test_backtest_engine.py` |
| Analysis | `scripts/analysis/` | `analyze_optimization_results.py` |
| Monitors | `scripts/monitoring/` | `live_trading_monitor.py` |
| Demos | `examples/` | `elliott_wave_service_demo.py` |
| Docs | `docs/` | `BACKTESTING_GUIDE.md` |
| Results | `results/` | `backtest_20250929_065505.json` |
| Configs | `config/` | `strategy_optimization_config.json` |
| Logs | `logs/` | `comprehensive_backtest.log` |
| Scripts | `scripts/` | `run_automated_backtest_now.py` |

## What Stays in Root

The following files appropriately remain in the root directory:
- `docker-compose*.yml` - Docker compositions
- `Dockerfile.*` - Docker build files
- `Makefile*` - Build and automation targets
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Pytest configuration
- `requirements*.txt` - Python dependencies
- `alembic.ini` - Database migration config
- `.pre-commit-config.yaml` - Pre-commit hooks
- `GitVersion.yml` - Semantic versioning config
- Configuration dotfiles moved to `config/` (`.portfolio-lint-config.py`, etc.)

## Migration Notes

### Updated Imports

Some files may need import path updates. If you encounter import errors:

```python
# Before
from analyze_results import analyze

# After
from scripts.analysis.analyze_results import analyze
```

### Script Execution

Scripts can now be run from their new locations:

```bash
# Run simulation
python simulations/realistic_trading_simulation.py

# Run backtest
python backtests/clean_backtest.py

# Run analysis
python scripts/analysis/compare_strategies.py

# Run monitor
python scripts/monitoring/live_trading_monitor.py
```

### Makefile Targets

Makefile targets have been updated to reference new locations. Use make targets when available:

```bash
make -f makefiles/Makefile.backtesting run-backtest
make -f makefiles/Makefile.live-trading monitor
```

## Benefits of Reorganization

1. **Discoverability**: Files are easier to find in logical groupings
2. **Maintainability**: Separation of concerns is clear
3. **Onboarding**: New developers can understand structure quickly
4. **Cleanup**: Easier to identify and remove old/unused files
5. **Testing**: Clear separation between tests and implementation
6. **Documentation**: All docs in one place

## Finding Files

If you're looking for a specific file:

```bash
# Search for a file by name
find . -name "filename.py"

# Search for files containing text
grep -r "search term" --include="*.py"

# List files in a category
ls -la simulations/
ls -la backtests/
```

## See Also

- `simulations/README.md` - Simulation guide
- `backtests/README.md` - Backtest guide
- `results/README.md` - Results guide
- `scripts/analysis/README.md` - Analysis scripts guide
- `scripts/monitoring/README.md` - Monitoring scripts guide
- `docs/QUICK_REFERENCE.md` - Quick reference for common tasks

