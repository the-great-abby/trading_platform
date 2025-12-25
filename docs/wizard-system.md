# Trading System Wizard 🧙

An interactive TUI (Text User Interface) wizard system for navigating and executing Makefile commands through a numbered menu interface.

## Overview

The Trading System Wizard simplifies complex Makefile navigation by providing:
- **Categorized command menu** - Commands organized by function
- **Number-based selection** - No need to remember command names
- **Interactive navigation** - Easy browsing through categories
- **Direct execution** - Run commands straight from the menu
- **Color-coded interface** - Beautiful, easy-to-read output

## Quick Start

### Launch the Wizard

```bash
# Full command
make wizard

# Or use the shortcut
make wiz
```

### Navigation

1. **Select a category** by entering its number (1-12)
2. **Select a command** by entering its number
3. **Go back** by entering 0
4. **Exit** by entering 0 from the main menu
5. **Interrupt** anytime with Ctrl+C

## Available Categories

The wizard organizes **65 commands** across **12 categories**:

### 1. Quick Status (5 commands)
Fast status checks and team syncs
- Quick project status
- Team sync
- Testing priorities
- Startup checklist
- Progress tracking

### 2. Service Management (8 commands)
Start, stop, and manage Kubernetes services
- Start/stop all services
- Service status
- Start specific service types (dashboards, trading, analytics)
- Core services status

### 3. Port Forwarding (7 commands)
Manage kubectl port forwards
- Start/stop all port forwards
- Port forwarding status
- Health checks
- Category-specific port forwards

### 4. Kubernetes (8 commands)
Kubernetes cluster operations
- Cluster status
- View logs
- Pod management
- Deployments
- Events and resource usage

### 5. Build & Deploy (7 commands)
Build and deploy services with semantic versioning
- Build all services
- Deploy all services
- Service-specific builds (MCP, trading)
- Version management

### 6. Trading Operations (6 commands)
Live and paper trading management
- Start/stop live trading
- Start/stop paper trading
- Trading status checks

### 7. Backtesting (3 commands)
Run and analyze backtests
- Run backtests
- View results
- Clean backtest data

### 8. Testing (4 commands)
Execute various test suites
- Run all tests
- Unit tests
- Integration tests
- Test priorities

### 9. Database (4 commands)
Database operations and migrations
- Run migrations
- Database status
- Reset database
- Backup database

### 10. AI Assistant (7 commands)
AI-powered development assistance
- Code review
- Refactoring
- Test generation
- Documentation
- Performance optimization
- Security review
- Debugging

### 11. Discord (3 commands)
Discord integration management
- Set up webhook
- Test notifications
- Check status

### 12. MCP Service (3 commands)
Model Context Protocol service management
- Start/stop MCP service
- Check status

## Example Workflow

### Check System Status

```
1. Launch wizard: make wizard
2. Select "1" for Quick Status
3. Select "1" for status
4. View system status
5. Press Enter to return
6. Select "0" to go back
7. Select "0" to exit
```

### Start Port Forwarding

```
1. Launch wizard: make wizard
2. Select "3" for Port Forwarding
3. Select "1" for port-start
4. Watch port forwards start
5. Press Enter to return
```

### Deploy a Service

```
1. Launch wizard: make wizard
2. Select "5" for Build & Deploy
3. Select "3" for build-mcp (or desired service)
4. Wait for build to complete
5. Select "4" for deploy-mcp
6. Service deployed!
```

## Features

### Color-Coded Interface

- 🟢 **Green**: Headers and success messages
- 🟡 **Yellow**: Descriptions and warnings
- 🔵 **Blue**: Command names
- 🔴 **Red**: Errors and exit options
- 🟣 **Magenta**: Back navigation
- 🔷 **Cyan**: Categories and highlights

### Smart Organization

Commands are automatically categorized based on their function, making it easy to find what you need without memorizing command names.

### Safe Execution

- Clear indication of what command is running
- Shows command description before execution
- Displays exit code after completion
- Easy return to menu after execution

## Technical Details

### Architecture

```
scripts/wizard.py           - Main wizard implementation
makefiles/Makefile.wizard   - Wizard Makefile targets
Makefile                    - Includes wizard system
```

### Command Definition

Commands are defined with:
- **name**: The make target name
- **description**: Human-readable description
- **category**: Category for organization
- **makefile**: Path to the Makefile containing the target

### Adding New Commands

Edit `scripts/wizard.py` and add to the `_load_commands()` method:

```python
commands.extend([
    Command("my-command", "Description", "Category", "makefiles/Makefile.xyz"),
])
```

## Utilities

### Test Installation

```bash
make wizard-test
```

Verifies:
- Python installation
- Wizard script presence
- File permissions

### View Information

```bash
make wizard-info
```

Shows:
- Version information
- Command statistics
- Category breakdown

### Get Help

```bash
make wizard-help
```

Displays:
- Usage instructions
- Features list
- Navigation guide
- Category overview

## Why Use the Wizard?

### Before (Traditional Makefile)
```bash
# Need to remember exact command names
make services-start-dashboards
make port-start-analytics
make k8s-pods
# Easy to mistype or forget options
```

### After (Wizard System)
```bash
# Just launch and select by number
make wizard
> 1  # Select category
> 3  # Select command
# Done! No memorization needed
```

## Benefits

✅ **No memorization** - Browse commands visually
✅ **Fewer typos** - Just enter numbers
✅ **Better discovery** - See all available commands
✅ **Faster workflow** - Quick navigation
✅ **Beginner friendly** - Self-documenting interface
✅ **Power user ready** - Quick number selection

## Integration with Existing Workflow

The wizard complements existing Makefile usage:

- **Use the wizard** when exploring or learning
- **Use direct make commands** when you know exactly what you want
- **Both work together** - No conflicts

Example:
```bash
# Interactive exploration
make wizard

# Direct execution when you know what you want
make status
make port-start
```

## Shortcuts

- `make wizard` - Full command
- `make wiz` - Quick shortcut
- Ctrl+C - Interrupt anytime
- 0 - Go back or exit

## Future Enhancements

Potential additions:
- [ ] Search/filter commands
- [ ] Command favorites
- [ ] Recent commands history
- [ ] Parameter input for commands that need them
- [ ] Batch command execution
- [ ] Custom command aliases
- [ ] Configuration file support

## Troubleshooting

### Wizard won't start
```bash
# Check installation
make wizard-test

# Verify Python version
python3 --version  # Should be 3.6+
```

### Commands not executing
```bash
# Verify you're in the project root
pwd  # Should show /Users/abby/code/trading

# Check Makefile structure
make help
```

### Screen display issues
```bash
# Try clearing the screen
clear

# Check terminal size
echo $COLUMNS $LINES  # Should be at least 80x24
```

## Contributing

To add new categories or commands:

1. Edit `scripts/wizard.py`
2. Add commands to `_load_commands()`
3. Test with `make wizard-test`
4. Update this documentation

## Support

For issues or questions:
1. Check `make wizard-help`
2. Review this documentation
3. Check Makefile comments
4. Ask Orion (AI assistant) for help

---

**Happy wizarding! 🧙✨**









