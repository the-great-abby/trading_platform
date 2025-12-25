#!/usr/bin/env python3
"""
Multi-Repository Wizard Configuration
Defines external repositories and their available commands for the wizard system.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ExternalRepo:
    """Represents an external repository that the wizard can manage"""
    name: str
    path: str
    description: str
    makefile: str = "Makefile"
    
    def exists(self) -> bool:
        """Check if the repository exists on the filesystem"""
        return os.path.exists(self.path)
    
    def get_full_path(self) -> str:
        """Get the absolute path to the repository"""
        return os.path.abspath(os.path.expanduser(self.path))


@dataclass
class ExternalCommand:
    """Represents a command from an external repository"""
    name: str
    description: str
    category: str
    repo: ExternalRepo
    makefile: str = "Makefile"
    
    @property
    def full_path(self) -> str:
        """Get full path to the repository"""
        return self.repo.get_full_path()


# Define external repositories
EXTERNAL_REPOS = {
    'ollama_controller': ExternalRepo(
        name='ollama_controller',
        path='/Users/abby/code/ollama_controller',
        description='Ollama Controller - LLM queue management system',
        makefile='Makefile'
    ),
    'database': ExternalRepo(
        name='database',
        path='/Users/abby/code/external_services/database',
        description='PostgreSQL/TimescaleDB Infrastructure',
        makefile='Makefile'
    ),
    'rabbitmq': ExternalRepo(
        name='rabbitmq',
        path='/Users/abby/code/external_services/rabbitmq',
        description='RabbitMQ Message Broker',
        makefile='Makefile'
    ),
    'redis': ExternalRepo(
        name='redis',
        path='/Users/abby/code/external_services/redis',
        description='Redis Cache Service',
        makefile='Makefile'
    ),
    'grafana': ExternalRepo(
        name='grafana',
        path='/Users/abby/code/external_services/grafana',
        description='Grafana Monitoring Dashboards',
        makefile='Makefile'
    ),
    'registry': ExternalRepo(
        name='registry',
        path='/Users/abby/code/external_services/registry',
        description='Docker Registry',
        makefile='Makefile'
    ),
    'system_mcp': ExternalRepo(
        name='system_mcp',
        path='/Users/abby/code/external_services/system_mcp',
        description='System MCP Integration',
        makefile='Makefile'
    ),
}


def get_external_commands() -> List[ExternalCommand]:
    """
    Get all external commands from configured repositories.
    Returns commands only from repositories that exist on the filesystem.
    """
    commands = []
    
    # Ollama Controller Commands
    if EXTERNAL_REPOS['ollama_controller'].exists():
        repo = EXTERNAL_REPOS['ollama_controller']
        commands.extend([
            # Infrastructure Restoration
            ExternalCommand("status", "Show Ollama system status", "Infrastructure Restoration", repo),
            ExternalCommand("hybrid-start", "Start Ollama hybrid system", "Infrastructure Restoration", repo),
            ExternalCommand("hybrid-stop", "Stop Ollama hybrid system", "Infrastructure Restoration", repo),
            ExternalCommand("hybrid-status", "Check Ollama hybrid status", "Infrastructure Restoration", repo),
            
            # Port Forwarding
            ExternalCommand("pf-start", "Start Ollama port forwards", "Infrastructure Restoration", repo),
            ExternalCommand("pf-stop", "Stop Ollama port forwards", "Infrastructure Restoration", repo),
            ExternalCommand("pf-status", "Show Ollama port forward status", "Infrastructure Restoration", repo),
            ExternalCommand("pf-check", "Health check Ollama port forwards", "Infrastructure Restoration", repo),
            ExternalCommand("pf-auto-restart", "Auto-restart Ollama port forwards", "Infrastructure Restoration", repo),
            
            # Development
            ExternalCommand("dev", "Start Ollama development services", "Infrastructure Restoration", repo),
            ExternalCommand("dev-workflow", "Complete Ollama dev setup", "Infrastructure Restoration", repo),
            
            # Deployment
            ExternalCommand("deploy", "Deploy Ollama services", "Infrastructure Restoration", repo),
            ExternalCommand("health-check", "Run Ollama health checks", "Infrastructure Restoration", repo),
        ])
    
    # Database Commands
    if EXTERNAL_REPOS['database'].exists():
        repo = EXTERNAL_REPOS['database']
        commands.extend([
            ExternalCommand("status", "Show database status", "Infrastructure Restoration", repo),
            ExternalCommand("deploy", "Deploy all databases", "Infrastructure Restoration", repo),
            ExternalCommand("start", "Start database services", "Infrastructure Restoration", repo),
            ExternalCommand("stop", "Stop database services", "Infrastructure Restoration", repo),
            ExternalCommand("health-check", "Check database health", "Infrastructure Restoration", repo),
            ExternalCommand("port-forward", "Start database port forwards", "Infrastructure Restoration", repo),
            ExternalCommand("logs", "Show database logs", "Infrastructure Restoration", repo),
        ])
    
    # RabbitMQ Commands
    if EXTERNAL_REPOS['rabbitmq'].exists():
        repo = EXTERNAL_REPOS['rabbitmq']
        commands.extend([
            ExternalCommand("deploy", "Deploy RabbitMQ", "Infrastructure Restoration", repo),
            ExternalCommand("status", "Show RabbitMQ status", "Infrastructure Restoration", repo),
            ExternalCommand("logs", "Show RabbitMQ logs", "Infrastructure Restoration", repo),
            ExternalCommand("port-forward", "Start RabbitMQ port forward", "Infrastructure Restoration", repo),
            ExternalCommand("delete", "Delete RabbitMQ deployment", "Infrastructure Restoration", repo),
        ])
    
    # Redis Commands
    if EXTERNAL_REPOS['redis'].exists():
        repo = EXTERNAL_REPOS['redis']
        commands.extend([
            ExternalCommand("deploy", "Deploy Redis", "Infrastructure Restoration", repo),
            ExternalCommand("status", "Show Redis status", "Infrastructure Restoration", repo),
            ExternalCommand("logs", "Show Redis logs", "Infrastructure Restoration", repo),
            ExternalCommand("port-forward", "Start Redis port forward", "Infrastructure Restoration", repo),
            ExternalCommand("delete", "Delete Redis deployment", "Infrastructure Restoration", repo),
        ])
    
    # Grafana Commands
    if EXTERNAL_REPOS['grafana'].exists():
        repo = EXTERNAL_REPOS['grafana']
        commands.extend([
            ExternalCommand("deploy", "Deploy Grafana", "Infrastructure Restoration", repo),
            ExternalCommand("status", "Show Grafana status", "Infrastructure Restoration", repo),
            ExternalCommand("port-forward", "Start Grafana port forward", "Infrastructure Restoration", repo),
        ])
    
    # Registry Commands
    if EXTERNAL_REPOS['registry'].exists():
        repo = EXTERNAL_REPOS['registry']
        commands.extend([
            ExternalCommand("deploy", "Deploy Docker Registry", "Infrastructure Restoration", repo),
            ExternalCommand("status", "Show Registry status", "Infrastructure Restoration", repo),
        ])
    
    return commands


def get_available_repos() -> Dict[str, ExternalRepo]:
    """Get only the repositories that exist on the filesystem"""
    return {name: repo for name, repo in EXTERNAL_REPOS.items() if repo.exists()}


def get_restoration_workflow_commands() -> List[Dict[str, str]]:
    """
    Get recommended restoration workflow as an ordered list.
    Returns a list of dicts with 'repo', 'command', and 'description' keys.
    """
    workflow = []
    
    # Step 1: Database
    if EXTERNAL_REPOS['database'].exists():
        workflow.append({
            'repo': 'database',
            'command': 'deploy',
            'description': '1. Deploy PostgreSQL/TimescaleDB databases',
            'category': 'Infrastructure Restoration'
        })
        workflow.append({
            'repo': 'database',
            'command': 'health-check',
            'description': '2. Verify database health',
            'category': 'Infrastructure Restoration'
        })
    
    # Step 2: RabbitMQ
    if EXTERNAL_REPOS['rabbitmq'].exists():
        workflow.append({
            'repo': 'rabbitmq',
            'command': 'deploy',
            'description': '3. Deploy RabbitMQ message broker',
            'category': 'Infrastructure Restoration'
        })
        workflow.append({
            'repo': 'rabbitmq',
            'command': 'status',
            'description': '4. Verify RabbitMQ is running',
            'category': 'Infrastructure Restoration'
        })
    
    # Step 3: Redis
    if EXTERNAL_REPOS['redis'].exists():
        workflow.append({
            'repo': 'redis',
            'command': 'deploy',
            'description': '5. Deploy Redis cache',
            'category': 'Infrastructure Restoration'
        })
        workflow.append({
            'repo': 'redis',
            'command': 'status',
            'description': '6. Verify Redis is running',
            'category': 'Infrastructure Restoration'
        })
    
    # Step 4: Ollama Controller
    if EXTERNAL_REPOS['ollama_controller'].exists():
        workflow.append({
            'repo': 'ollama_controller',
            'command': 'hybrid-start',
            'description': '7. Start Ollama controller system',
            'category': 'Infrastructure Restoration'
        })
        workflow.append({
            'repo': 'ollama_controller',
            'command': 'pf-start',
            'description': '8. Start Ollama port forwards',
            'category': 'Infrastructure Restoration'
        })
        workflow.append({
            'repo': 'ollama_controller',
            'command': 'health-check',
            'description': '9. Verify Ollama health',
            'category': 'Infrastructure Restoration'
        })
    
    # Step 5: Trading System (local commands)
    workflow.extend([
        {
            'repo': 'trading',
            'command': 'services-start',
            'description': '10. Start trading system services',
            'category': 'Infrastructure Restoration'
        },
        {
            'repo': 'trading',
            'command': 'port-start',
            'description': '11. Start trading port forwards',
            'category': 'Infrastructure Restoration'
        },
        {
            'repo': 'trading',
            'command': 'status',
            'description': '12. Verify trading system status',
            'category': 'Infrastructure Restoration'
        },
    ])
    
    return workflow


# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_repo_status():
    """Print status of all configured external repositories"""
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
    print(f"{Colors.BOLD}External Repository Status{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
    
    for name, repo in EXTERNAL_REPOS.items():
        status = f"{Colors.GREEN}✅ Available{Colors.NC}" if repo.exists() else f"{Colors.RED}❌ Not Found{Colors.NC}"
        print(f"  {Colors.BOLD}{name:20}{Colors.NC} {status}")
        if repo.exists():
            print(f"    {Colors.CYAN}→{Colors.NC} {repo.description}")
            print(f"    {Colors.YELLOW}Path:{Colors.NC} {repo.path}")
        print()


def get_restoration_guide() -> str:
    """Get a formatted restoration guide"""
    guide = f"""
{Colors.CYAN}{'='*70}{Colors.NC}
{Colors.BOLD}{Colors.GREEN}🔧 System Restoration Wizard Guide{Colors.NC}
{Colors.CYAN}{'='*70}{Colors.NC}

This wizard can now manage services across multiple repositories!

{Colors.BOLD}Available External Services:{Colors.NC}
"""
    
    for name, repo in get_available_repos().items():
        guide += f"\n  {Colors.GREEN}✅ {name:20}{Colors.NC} - {repo.description}"
    
    guide += f"""

{Colors.BOLD}Recommended Restoration Flow:{Colors.NC}

Use the {Colors.CYAN}Infrastructure Restoration{Colors.NC} category in the wizard to:

  1. {Colors.YELLOW}Start Infrastructure{Colors.NC}
     - Deploy databases (PostgreSQL/TimescaleDB)
     - Deploy message broker (RabbitMQ)
     - Deploy cache (Redis)
     - Start Ollama controller

  2. {Colors.YELLOW}Verify Health{Colors.NC}
     - Check database connections
     - Verify RabbitMQ is accepting connections
     - Test Redis connectivity
     - Confirm Ollama is responding

  3. {Colors.YELLOW}Start Trading Services{Colors.NC}
     - Fix service configurations (use restoration guide)
     - Start trading system services
     - Setup port forwards

  4. {Colors.YELLOW}Final Verification{Colors.NC}
     - Run health checks
     - Test service endpoints
     - Verify port forwards

{Colors.BOLD}Quick Commands:{Colors.NC}

  {Colors.CYAN}make wizard{Colors.NC} or {Colors.CYAN}make wiz{Colors.NC}
    → Launch the wizard
    → Select {Colors.YELLOW}"Infrastructure Restoration"{Colors.NC} category
    → Follow the prompts

{Colors.CYAN}{'='*70}{Colors.NC}
"""
    return guide


if __name__ == "__main__":
    # When run directly, show repository status
    print_repo_status()
    print(get_restoration_guide())








