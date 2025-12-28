# Trading System Setup Wizard 🧙

The Setup Wizard helps you install all necessary external service repositories needed for the trading system to function properly.

## Quick Start

```bash
make setup-wizard
# or
make setup
```

## What It Does

The setup wizard:

1. **Identifies Required Services** - Determines which external services are needed for the trading system
2. **Checks Installation Status** - Checks which services are already installed in the `external_services/` directory
3. **Extracts Git URLs** - Reads SSH connection info from existing `.git/config` files
4. **Infers Missing URLs** - Intelligently infers git repository URLs for services that aren't installed yet
5. **Interactive Installation** - Prompts you to install missing services one by one
6. **Git Cloning** - Clones missing repositories using SSH authentication

## Services Managed

### Required Services
- **database** - PostgreSQL/TimescaleDB database infrastructure
- **rabbitmq** - RabbitMQ message queue service
- **redis** - Redis cache and session storage
- **registry** - Docker registry for container images

### Optional Services
- **playwright** - Playwright testing framework
- **grafana** - Grafana monitoring dashboards

## How It Works

1. The wizard scans the `../external_services/` directory (sibling to the trading directory)
2. For installed services, it reads `.git/config` to extract the SSH git URL
3. For missing services, it infers the URL pattern from existing services (e.g., `git@github.com:the-great-abby/{repo_name}.git`)
4. It displays the status of all services (installed/not installed)
5. You can choose to install all required services at once, or install them individually
6. Optional services are presented separately for your consideration

## Example Output

```
🧙 Trading System Setup Wizard
======================================================================

External Service Status:

Required Services:
  ✅ database
      PostgreSQL/TimescaleDB database infrastructure
      Status: Installed
      Git URL: git@github.com:the-great-abby/postgres_databases.git

  ❌ redis
      Redis cache and session storage
      Status: Not Installed
      Git URL: git@github.com:the-great-abby/redis.git

Install all required services? (y/n):
```

## Requirements

- Python 3.6+
- Git installed and configured
- SSH access to GitHub (or your git provider)
- `external_services/` directory should be a sibling to the `trading/` directory

## Integration

The setup wizard is integrated into the main Makefile:

- `make setup-wizard` - Run the setup wizard
- `make setup` - Shortcut for setup-wizard
- `make wizard-help` - Shows wizard system help (includes setup wizard)

## Notes

- The wizard assumes services are located in `../external_services/` relative to the trading directory
- SSH authentication is required for git cloning
- The wizard is safe to run multiple times - it won't re-install already installed services
- If a service installation fails, you can choose to continue with the remaining services

