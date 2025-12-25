# 🧙 Multi-Repository Wizard System Guide

**Last Updated**: December 4, 2025  
**Status**: ✅ Operational - Cross-repository command execution enabled!

---

## 🎯 Overview

The Trading System Wizard has been **enhanced to support multi-repository management**! You can now control services across multiple project repositories from a single unified interface.

### What's New?

- **Cross-Repository Commands**: Execute make commands in external repositories
- **Infrastructure Restoration**: Dedicated category for starting up all infrastructure components
- **Automatic Discovery**: Wizard automatically detects available external repositories
- **Unified Interface**: No need to `cd` between directories - manage everything from one place
- **Context-Aware**: Shows which repository each command targets

---

## 🏗️ Supported Repositories

The wizard can now manage these external repositories:

| Repository | Path | Description | Commands |
|------------|------|-------------|----------|
| **ollama_controller** | `/Users/abby/code/ollama_controller` | LLM queue management | Start/stop, port forwards, health checks |
| **database** | `/Users/abby/code/external_services/database` | PostgreSQL/TimescaleDB | Deploy, status, health checks |
| **rabbitmq** | `/Users/abby/code/external_services/rabbitmq` | Message broker | Deploy, status, logs, port forwards |
| **redis** | `/Users/abby/code/external_services/redis` | Cache service | Deploy, status, port forwards |
| **grafana** | `/Users/abby/code/external_services/grafana` | Monitoring dashboards | Deploy, status, port forwards |
| **registry** | `/Users/abby/code/external_services/registry` | Docker registry | Deploy, status |
| **system_mcp** | `/Users/abby/code/external_services/system_mcp` | System MCP integration | MCP commands |

---

## 🚀 Quick Start

### Launch the Enhanced Wizard

```bash
cd /Users/abby/code/trading
make wizard
# or
make wiz
```

### First Launch Experience

When you launch the wizard, you'll see:

```
======================================================================
🧙 Trading System Wizard
Interactive Command Menu
======================================================================

🌟 Multi-Repository Mode Enabled!

This wizard can now manage services across multiple repositories:

  ✅ ollama_controller      - Ollama Controller - LLM queue management system
  ✅ database               - PostgreSQL/TimescaleDB Infrastructure
  ✅ rabbitmq               - RabbitMQ Message Broker
  ✅ redis                  - Redis Cache Service
  ✅ grafana                - Grafana Monitoring Dashboards
  ✅ registry               - Docker Registry

Look for the 'Infrastructure Restoration' category!

Press Enter to start...
```

---

## 🔧 Infrastructure Restoration Category

The new **Infrastructure Restoration** category contains commands from all external repositories!

### Navigation Example:

```bash
make wizard
```

**Step 1: Select Category**
```
📋 Select a Category:

  1. AI Assistant (7 commands)
  2. Backtesting (3 commands)
  3. Build & Deploy (7 commands)
  4. Database (4 commands)
  5. Discord (3 commands)
  6. Infrastructure Restoration (30+ commands)  ← SELECT THIS!
  7. Kubernetes (8 commands)
  ...

Enter your choice: 6
```

**Step 2: View Available Commands**
```
📂 Category: Infrastructure Restoration

  1. ollama_controller:status
      → [ollama_controller] Show Ollama system status
  2. ollama_controller:hybrid-start
      → [ollama_controller] Start Ollama hybrid system
  3. ollama_controller:hybrid-stop
      → [ollama_controller] Stop Ollama hybrid system
  4. ollama_controller:pf-start
      → [ollama_controller] Start Ollama port forwards
  5. database:deploy
      → [database] Deploy all databases
  6. database:status
      → [database] Show database status
  7. database:health-check
      → [database] Check database health
  8. rabbitmq:deploy
      → [rabbitmq] Deploy RabbitMQ
  9. rabbitmq:status
      → [rabbitmq] Show RabbitMQ status
  10. redis:deploy
       → [redis] Deploy Redis
  ...

Enter your choice: _
```

---

## 📖 Recommended Restoration Workflow

Use this sequence to restore the entire system from scratch:

### Phase 1: Core Infrastructure (External Services)

1. **Deploy Databases**
   ```
   Wizard → Infrastructure Restoration → database:deploy
   Wizard → Infrastructure Restoration → database:health-check
   ```

2. **Deploy RabbitMQ**
   ```
   Wizard → Infrastructure Restoration → rabbitmq:deploy
   Wizard → Infrastructure Restoration → rabbitmq:status
   ```

3. **Deploy Redis**
   ```
   Wizard → Infrastructure Restoration → redis:deploy
   Wizard → Infrastructure Restoration → redis:status
   ```

4. **Start Ollama Controller**
   ```
   Wizard → Infrastructure Restoration → ollama_controller:hybrid-start
   Wizard → Infrastructure Restoration → ollama_controller:pf-start
   Wizard → Infrastructure Restoration → ollama_controller:health-check
   ```

### Phase 2: Trading System Services

5. **Fix Service Configurations**
   - Follow the `SERVICE_RESTORATION_GUIDE.md`
   - Fix market-data-service database URL
   - Fix rss-feed-service RabbitMQ URL

6. **Start Trading Services**
   ```
   Wizard → Service Management → services-start
   ```

7. **Setup Port Forwards**
   ```
   Wizard → Port Forwarding → port-start
   ```

8. **Verify System**
   ```
   Wizard → Quick Status → status
   ```

---

## 🎨 Command Format

External repository commands follow this format in the wizard:

```
repository_name:command_name
```

Examples:
- `ollama_controller:status` - Run `make status` in ollama_controller repo
- `database:deploy` - Run `make deploy` in database repo
- `rabbitmq:port-forward` - Run `make port-forward` in rabbitmq repo

---

## 🔍 How It Works

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Trading System Wizard                    │
│         (scripts/wizard.py)                      │
└──────────────────┬──────────────────────────────┘
                   │
                   ├─── Local Commands (trading repo)
                   │    ├─ Quick Status
                   │    ├─ Service Management
                   │    ├─ Port Forwarding
                   │    └─ Kubernetes
                   │
                   └─── External Commands (other repos)
                        ├─ wizard_config.py
                        │   ├─ EXTERNAL_REPOS
                        │   └─ get_external_commands()
                        │
                        └─ Infrastructure Restoration
                            ├─ ollama_controller/*
                            ├─ database/*
                            ├─ rabbitmq/*
                            ├─ redis/*
                            └─ grafana/*
```

### Execution Flow

1. **User selects command** from wizard menu
2. **Wizard detects** if it's an external command (has repository prefix)
3. **Changes directory** to the external repository path
4. **Executes make command** with appropriate Makefile
5. **Returns to wizard** menu after completion

---

## 🛠️ Configuration

### Adding New Repositories

Edit `/Users/abby/code/trading/scripts/wizard_config.py`:

```python
EXTERNAL_REPOS = {
    'my_new_repo': ExternalRepo(
        name='my_new_repo',
        path='/Users/abby/code/my_new_repo',
        description='My New Repository Description',
        makefile='Makefile'
    ),
}
```

### Adding New Commands

In `wizard_config.py`, add to `get_external_commands()`:

```python
if EXTERNAL_REPOS['my_new_repo'].exists():
    repo = EXTERNAL_REPOS['my_new_repo']
    commands.extend([
        ExternalCommand(
            "start", 
            "Start my service", 
            "Infrastructure Restoration", 
            repo
        ),
        ExternalCommand(
            "stop", 
            "Stop my service", 
            "Infrastructure Restoration", 
            repo
        ),
    ])
```

---

## 🎯 Use Cases

### Use Case 1: System Recovery After Restart

**Scenario**: Your Mac restarted and all services are down.

**Solution**:
```bash
make wizard
→ Infrastructure Restoration
  → database:deploy
  → rabbitmq:deploy
  → redis:deploy
  → ollama_controller:hybrid-start
  → ollama_controller:pf-start
→ Service Management
  → services-start
→ Port Forwarding
  → port-start
→ Quick Status
  → status
```

**Time**: 5-10 minutes (mostly waiting for services to start)

---

### Use Case 2: Troubleshooting Infrastructure

**Scenario**: Services are failing, need to check infrastructure health.

**Solution**:
```bash
make wizard
→ Infrastructure Restoration
  → database:health-check
  → rabbitmq:status
  → redis:status
  → ollama_controller:health-check
→ Kubernetes
  → k8s-events (check for errors)
  → k8s-logs (view service logs)
```

---

### Use Case 3: Selective Service Restart

**Scenario**: Only Ollama is having issues, everything else is fine.

**Solution**:
```bash
make wizard
→ Infrastructure Restoration
  → ollama_controller:hybrid-stop
  → ollama_controller:hybrid-start
  → ollama_controller:pf-start
  → ollama_controller:health-check
```

---

## 💡 Pro Tips

### 1. Check Repository Availability

Before using the wizard, check which repos are available:

```bash
cd /Users/abby/code/trading
python3 scripts/wizard_config.py
```

This shows which external repositories the wizard can find.

### 2. Use Descriptive Names

When you see `[repository_name]` in the description, it tells you which repo the command targets:

```
[ollama_controller] Start Ollama hybrid system
[database] Check database health
[rabbitmq] Deploy RabbitMQ
```

### 3. Chain Commands

The wizard returns to the menu after each command, so you can chain multiple commands:

```
1. database:deploy
2. Wait for completion
3. database:health-check
4. Verify success
5. Continue with next service
```

### 4. Use Infrastructure Restoration for Setup

The **Infrastructure Restoration** category is your one-stop-shop for getting all external services running!

### 5. Combine with Local Commands

After infrastructure is up, use local categories:
- **Service Management** for trading services
- **Port Forwarding** for local access
- **Quick Status** for health checks

---

## 🚨 Troubleshooting

### Problem: "Repository not found"

**Cause**: External repository doesn't exist at the configured path.

**Solution**:
1. Check if the repo exists: `ls /Users/abby/code/ollama_controller`
2. Update path in `wizard_config.py` if location changed
3. Re-run wizard

---

### Problem: "Make command failed"

**Cause**: The Makefile doesn't have that target, or prerequisites aren't met.

**Solution**:
1. Navigate to the repo manually: `cd /Users/abby/code/[repo_name]`
2. Run `make help` to see available commands
3. Try running the command directly to see the error
4. Fix the issue in that repository

---

### Problem: "External commands not showing up"

**Cause**: `wizard_config.py` import failed.

**Solution**:
1. Check file exists: `ls scripts/wizard_config.py`
2. Check file is executable: `chmod +x scripts/wizard_config.py`
3. Test import: `python3 -c "from scripts.wizard_config import get_external_commands"`
4. Re-launch wizard

---

## 📊 Command Categories

The wizard now has these categories:

| Category | Local/External | Command Count | Purpose |
|----------|----------------|---------------|---------|
| Quick Status | Local | 5 | Fast status checks |
| Service Management | Local | 8 | K8s service control |
| Port Forwarding | Local | 7 | kubectl port-forward |
| Kubernetes | Local | 8 | K8s operations |
| **Infrastructure Restoration** | **External** | **30+** | **Cross-repo infrastructure** |
| Build & Deploy | Local | 7 | Docker build/deploy |
| Trading Operations | Local | 6 | Trading start/stop |
| Backtesting | Local | 3 | Backtest execution |
| Testing | Local | 4 | Test execution |
| Database | Local | 4 | Database migrations |
| AI Assistant | Local | 7 | AI-powered tools |
| Discord | Local | 3 | Discord integration |
| MCP Service | Local | 3 | MCP operations |

---

## 🎓 Advanced Features

### Custom Restoration Workflows

You can create custom restoration sequences by editing `wizard_config.py`:

```python
def get_restoration_workflow_commands() -> List[Dict[str, str]]:
    """Define your custom restoration sequence"""
    return [
        {
            'repo': 'database',
            'command': 'deploy',
            'description': '1. Deploy databases',
            'category': 'Infrastructure Restoration'
        },
        # ... add more steps
    ]
```

### Repository Health Checks

Run quick health checks across all repos:

```bash
make wizard
→ Infrastructure Restoration
  → database:health-check
  → rabbitmq:status
  → redis:status
  → ollama_controller:health-check
```

### Batch Operations

Though not automated yet, you can mentally batch operations:

**Morning Startup Sequence**:
1. Infrastructure Restoration → database:deploy
2. Infrastructure Restoration → rabbitmq:deploy
3. Infrastructure Restoration → redis:deploy
4. Infrastructure Restoration → ollama_controller:hybrid-start
5. Service Management → services-start
6. Port Forwarding → port-start

---

## 🔗 Related Documentation

- **Original Wizard Guide**: `docs/wizard-system.md`
- **Wizard Quick Reference**: `md/wizard-quick-reference.md`
- **Service Restoration Guide**: `docs/SERVICE_RESTORATION_GUIDE.md`
- **Wizard Configuration**: `scripts/wizard_config.py`
- **Main Wizard Script**: `scripts/wizard.py`

---

## 🎉 Summary

The multi-repository wizard system gives you:

✅ **Unified Control** - Manage all services from one interface  
✅ **Cross-Repository** - Execute commands in any configured repo  
✅ **Infrastructure Restoration** - Dedicated category for system recovery  
✅ **Automatic Discovery** - Detects available external repositories  
✅ **Context-Aware** - Shows which repo each command targets  
✅ **Easy to Extend** - Add new repos and commands via configuration  

**The wizard is now your complete system management tool!** 🧙✨

---

**Questions?**

The wizard system is self-documenting. Just run:
```bash
make wizard
```

And explore the **Infrastructure Restoration** category!








