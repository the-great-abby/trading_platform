# Wizard Quick Reference Card 🧙

## Launch
```bash
make wizard    # Full command
make wiz       # Quick shortcut
```

## Navigation
| Key | Action |
|-----|--------|
| `1-12` | Select category |
| `1-n` | Select command |
| `0` | Back / Exit |
| `Ctrl+C` | Interrupt |

## Categories

| # | Category | Commands | Description |
|---|----------|----------|-------------|
| 1 | Quick Status | 5 | Fast status checks |
| 2 | Service Management | 8 | Service operations |
| 3 | Port Forwarding | 7 | Port management |
| 4 | Kubernetes | 8 | K8s operations |
| 5 | Build & Deploy | 7 | Build/deploy services |
| 6 | Trading Operations | 6 | Trading management |
| 7 | Backtesting | 3 | Backtest operations |
| 8 | Testing | 4 | Test execution |
| 9 | Database | 4 | DB operations |
| 10 | AI Assistant | 7 | AI development help |
| 11 | Discord | 3 | Discord integration |
| 12 | MCP Service | 3 | MCP management |

## Common Workflows

### Quick Status Check
```
wizard → 1 (Quick Status) → 1 (status)
```

### Start Services
```
wizard → 2 (Service Management) → 1 (services-start)
```

### Port Forward Setup
```
wizard → 3 (Port Forwarding) → 1 (port-start)
```

### Deploy Service
```
wizard → 5 (Build & Deploy) → [select build] → [select deploy]
```

## Utilities
```bash
make wizard-help      # Full help
make wizard-test      # Test installation
make wizard-info      # Statistics
```

## Color Legend
🟢 Green - Success, headers
🟡 Yellow - Descriptions
🔵 Blue - Commands
🔴 Red - Exit, errors
🟣 Magenta - Back navigation
🔷 Cyan - Categories

---
**Total: 65 commands across 12 categories**









