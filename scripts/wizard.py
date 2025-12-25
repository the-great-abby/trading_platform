#!/usr/bin/env python3
"""
Trading System Wizard - Interactive TUI for Makefile Commands
A wizard system that allows users to navigate and execute Makefile commands
by selecting numbered options from categorized menus.

Now supports multi-repository management for infrastructure restoration!
"""

import os
import sys
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

# Import variable wizard - handle import path
try:
    from variable_wizard import VariableWizard
    VARIABLE_WIZARD_AVAILABLE = True
except ImportError:
    # Try adding scripts directory to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    try:
        from variable_wizard import VariableWizard
        VARIABLE_WIZARD_AVAILABLE = True
    except ImportError:
        VARIABLE_WIZARD_AVAILABLE = False

# Import external repo configuration
try:
    from wizard_config import (
        get_external_commands, 
        get_available_repos, 
        get_restoration_guide,
        ExternalCommand
    )
    EXTERNAL_REPOS_AVAILABLE = True
except ImportError:
    EXTERNAL_REPOS_AVAILABLE = False
    ExternalCommand = None

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


@dataclass
class Command:
    """Represents a Makefile command"""
    name: str
    description: str
    category: str
    makefile: str = "Makefile"


class WizardMenu:
    """Main wizard menu system"""
    
    def __init__(self):
        self.commands = self._load_commands()
        self.categories = self._organize_by_category()
        self.current_repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def _load_commands(self) -> List[Command]:
        """Load all available commands from Makefiles"""
        commands = []
        
        # System Control - Quick access to essential operations
        commands.extend([
            Command("services-start", "🚀 Start all services (bring everything up)", "System Control", "makefiles/Makefile.services"),
            Command("services-stop", "🛑 Stop all services (shut everything down)", "System Control", "makefiles/Makefile.services"),
            Command("services-restart", "🔄 Restore all services (restart everything)", "System Control", "makefiles/Makefile.services"),
            Command("port-start", "🔌 Start all port forwards", "System Control", "makefiles/Makefile.port-forward"),
            Command("port-stop", "🔌 Stop all port forwards", "System Control", "makefiles/Makefile.port-forward"),
            Command("services-status", "📊 Show system status", "System Control", "makefiles/Makefile.services"),
        ])
        
        # Core Quick Commands
        commands.extend([
            Command("status", "Quick project status", "Quick Status", "makefiles/Makefile.simple"),
            Command("sync", "Team sync", "Quick Status", "makefiles/Makefile.simple"),
            Command("critical", "Testing priorities", "Quick Status", "makefiles/Makefile.simple"),
            Command("simple-startup", "Startup checklist", "Quick Status", "makefiles/Makefile.simple"),
            Command("simple-progress", "Progress tracking", "Quick Status", "makefiles/Makefile.simple"),
        ])
        
        # Service Management
        commands.extend([
            Command("services-start", "Start all essential services", "Service Management", "makefiles/Makefile.services"),
            Command("services-stop", "Stop all services", "Service Management", "makefiles/Makefile.services"),
            Command("services-status", "Show service status", "Service Management", "makefiles/Makefile.services"),
            Command("services-restart", "Restart all services", "Service Management", "makefiles/Makefile.services"),
            Command("services-start-dashboards", "Start dashboard services", "Service Management", "makefiles/Makefile.services"),
            Command("services-start-trading", "Start trading services", "Service Management", "makefiles/Makefile.services"),
            Command("services-start-analytics", "Start analytics services", "Service Management", "makefiles/Makefile.services"),
            Command("services-core-status", "Show core services status", "Service Management", "makefiles/Makefile.services"),
        ])
        
        # Port Forwarding
        commands.extend([
            Command("port-start", "Start all port forwards", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-stop", "Stop all port forwards", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-status", "Show port forwarding status", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-check", "Check if essential ports are responding", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-restart", "Restart all port forwards", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-health-check", "Check health of all forwarded ports", "Port Forwarding", "makefiles/Makefile.port-forward"),
            Command("port-start-dashboards", "Start dashboard port forwards", "Port Forwarding", "makefiles/Makefile.port-forward"),
        ])
        
        # Kubernetes
        commands.extend([
            Command("k8s-status", "Show cluster status", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-logs", "Show service logs", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-pods", "Show pods", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-deployments", "Show deployments", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-events", "Show events", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-top", "Show resource usage", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-restart", "Restart services", "Kubernetes", "makefiles/Makefile.kubernetes"),
            Command("k8s-secrets", "Show secrets", "Kubernetes", "makefiles/Makefile.kubernetes"),
        ])
        
        # Build & Deploy
        commands.extend([
            Command("build", "Build all services", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("deploy", "Deploy all services", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("build-mcp", "Build MCP service", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("deploy-mcp", "Deploy MCP service", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("build-trading", "Build trading service", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("deploy-trading", "Deploy trading service", "Build & Deploy", "makefiles/Makefile.versioning"),
            Command("version", "Check current semantic version", "Build & Deploy", "makefiles/Makefile.versioning"),
        ])
        
        # Trading Operations
        commands.extend([
            Command("live-trading-start", "Start live trading", "Trading Operations", "makefiles/Makefile.live-trading"),
            Command("live-trading-stop", "Stop live trading", "Trading Operations", "makefiles/Makefile.live-trading"),
            Command("live-trading-status", "Check live trading status", "Trading Operations", "makefiles/Makefile.live-trading"),
            Command("paper-trading-start", "Start paper trading", "Trading Operations", "makefiles/Makefile.paper-trading"),
            Command("paper-trading-stop", "Stop paper trading", "Trading Operations", "makefiles/Makefile.paper-trading"),
            Command("paper-trading-status", "Check paper trading status", "Trading Operations", "makefiles/Makefile.paper-trading"),
        ])
        
        # Backtesting
        commands.extend([
            Command("backtest-run", "Run backtest", "Backtesting", "makefiles/Makefile.backtest"),
            Command("backtest-results", "Show backtest results", "Backtesting", "makefiles/Makefile.backtest"),
            Command("backtest-clean", "Clean backtest data", "Backtesting", "makefiles/Makefile.backtest"),
        ])
        
        # Testing
        commands.extend([
            Command("test", "Run all tests", "Testing", "makefiles/Makefile.test"),
            Command("test-unit", "Run unit tests", "Testing", "makefiles/Makefile.test"),
            Command("test-integration", "Run integration tests", "Testing", "makefiles/Makefile.test"),
            Command("test-priority", "Test priority", "Testing", "makefiles/Makefile.simple"),
        ])
        
        # Database
        commands.extend([
            Command("db-migrate", "Run database migrations", "Database", "makefiles/Makefile.database"),
            Command("db-status", "Show database status", "Database", "makefiles/Makefile.database"),
            Command("db-reset", "Reset database", "Database", "makefiles/Makefile.database"),
            Command("db-backup", "Backup database", "Database", "makefiles/Makefile.database"),
        ])
        
        # AI Development Assistant
        commands.extend([
            Command("simple-ai-review", "AI code review", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-refactor", "AI refactoring", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-test", "AI test generation", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-docs", "AI documentation", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-optimize", "AI performance optimization", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-security", "AI security review", "AI Assistant", "makefiles/Makefile.simple"),
            Command("simple-ai-debug", "AI debugging", "AI Assistant", "makefiles/Makefile.simple"),
        ])
        
        # Discord Integration
        commands.extend([
            Command("discord-setup", "Set up Discord webhook", "Discord", "makefiles/Makefile.simple"),
            Command("discord-test", "Test Discord notifications", "Discord", "makefiles/Makefile.simple"),
            Command("discord-status", "Check Discord webhook status", "Discord", "makefiles/Makefile.simple"),
        ])
        
        # MCP (Model Context Protocol)
        commands.extend([
            Command("mcp-start", "Start MCP service", "MCP Service", "makefiles/Makefile.mcp"),
            Command("mcp-stop", "Stop MCP service", "MCP Service", "makefiles/Makefile.mcp"),
            Command("mcp-status", "Check MCP service status", "MCP Service", "makefiles/Makefile.mcp"),
        ])
        
        # Load external repository commands if available
        if EXTERNAL_REPOS_AVAILABLE:
            try:
                external_commands = get_external_commands()
                # Convert ExternalCommand to Command objects
                for ext_cmd in external_commands:
                    # Create a wrapper command that includes repo information
                    cmd = Command(
                        name=f"{ext_cmd.repo.name}:{ext_cmd.name}",
                        description=f"[{ext_cmd.repo.name}] {ext_cmd.description}",
                        category=ext_cmd.category,
                        makefile=ext_cmd.makefile
                    )
                    # Store the external command for execution
                    if not hasattr(cmd, '_external_cmd'):
                        cmd._external_cmd = ext_cmd
                    commands.append(cmd)
            except Exception as e:
                print(f"Warning: Could not load external commands: {e}")
        
        return commands
    
    def _organize_by_category(self) -> Dict[str, List[Command]]:
        """Organize commands by category"""
        categories = {}
        for cmd in self.commands:
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)
        
        # Sort categories, but put System Control first
        sorted_cats = dict(sorted(categories.items()))
        if "System Control" in sorted_cats:
            # Move System Control to the front
            system_control = sorted_cats.pop("System Control")
            return {"System Control": system_control, **sorted_cats}
        return sorted_cats
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        """Print the wizard header"""
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.GREEN}🧙 Trading System Wizard{Colors.NC}")
        print(f"{Colors.YELLOW}Interactive Command Menu{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
        print()
    
    def print_category_menu(self):
        """Print the main category menu"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.GREEN}📋 Select a Category:{Colors.NC}\n")
        
        for idx, category in enumerate(self.categories.keys(), 1):
            cmd_count = len(self.categories[category])
            print(f"  {Colors.BOLD}{idx}.{Colors.NC} {Colors.CYAN}{category}{Colors.NC} {Colors.YELLOW}({cmd_count} commands){Colors.NC}")
        
        print(f"\n  {Colors.BOLD}0.{Colors.NC} {Colors.RED}🚪 Exit Wizard (Shut Down){Colors.NC}")
        print()
    
    def print_command_menu(self, category: str):
        """Print the command menu for a specific category"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.GREEN}📂 Category: {Colors.BOLD}{category}{Colors.NC}\n")
        
        commands = self.categories[category]
        for idx, cmd in enumerate(commands, 1):
            print(f"  {Colors.BOLD}{idx}.{Colors.NC} {Colors.BLUE}{cmd.name}{Colors.NC}")
            print(f"      {Colors.YELLOW}→{Colors.NC} {cmd.description}")
        
        print(f"\n  {Colors.BOLD}0.{Colors.NC} {Colors.MAGENTA}← Back to Categories{Colors.NC}")
        print()
    
    def show_startup_info(self):
        """Show startup information about multi-repo capabilities"""
        self.clear_screen()
        self.print_header()
        
        if EXTERNAL_REPOS_AVAILABLE:
            try:
                available_repos = get_available_repos()
                if available_repos:
                    print(f"{Colors.GREEN}🌟 Multi-Repository Mode Enabled!{Colors.NC}\n")
                    print(f"{Colors.YELLOW}This wizard can now manage services across multiple repositories:{Colors.NC}\n")
                    
                    for name, repo in available_repos.items():
                        print(f"  {Colors.GREEN}✅ {name:20}{Colors.NC} - {repo.description}")
                    
                    print(f"\n{Colors.CYAN}Look for the 'Infrastructure Restoration' category!{Colors.NC}\n")
                else:
                    print(f"{Colors.YELLOW}Multi-repo support enabled, but no external repos found.{Colors.NC}\n")
            except Exception as e:
                print(f"{Colors.YELLOW}Note: External repo support available but not configured.{Colors.NC}\n")
        
        input(f"{Colors.GREEN}Press Enter to start...{Colors.NC}")
    
    def get_user_choice(self, max_choice: int) -> int:
        """Get user's menu choice"""
        while True:
            try:
                choice = input(f"{Colors.GREEN}Enter your choice (0-{max_choice}): {Colors.NC}")
                choice = int(choice)
                if 0 <= choice <= max_choice:
                    return choice
                else:
                    print(f"{Colors.RED}Invalid choice. Please enter a number between 0 and {max_choice}.{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.NC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Wizard interrupted.{Colors.NC}")
                sys.exit(0)
    
    def execute_command(self, command: Command):
        """Execute the selected make command"""
        self.clear_screen()
        self.print_header()
        
        # Check if this is an external command
        is_external = hasattr(command, '_external_cmd')
        
        if is_external:
            ext_cmd = command._external_cmd
            display_name = f"{ext_cmd.repo.name}:{ext_cmd.name}"
            repo_path = ext_cmd.full_path
            makefile_path = ext_cmd.makefile
            actual_command = ext_cmd.name
            
            print(f"{Colors.GREEN}🚀 Executing: {Colors.BOLD}{display_name}{Colors.NC}")
            print(f"{Colors.YELLOW}Description: {ext_cmd.description}{Colors.NC}")
            print(f"{Colors.MAGENTA}Repository: {ext_cmd.repo.description}{Colors.NC}")
            print(f"{Colors.CYAN}Path: {repo_path}{Colors.NC}")
        else:
            display_name = command.name
            repo_path = self.current_repo_path
            makefile_path = command.makefile
            actual_command = command.name
            
            print(f"{Colors.GREEN}🚀 Executing: {Colors.BOLD}{command.name}{Colors.NC}")
            print(f"{Colors.YELLOW}Description: {command.description}{Colors.NC}")
        
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
        
        try:
            # Use variable wizard if available
            user_vars = {}
            cmd = None
            if VARIABLE_WIZARD_AVAILABLE and not is_external:
                try:
                    # Get absolute path to makefile
                    if os.path.isabs(makefile_path):
                        abs_makefile_path = makefile_path
                    else:
                        abs_makefile_path = os.path.abspath(os.path.join(repo_path, makefile_path))
                    
                    wizard = VariableWizard(abs_makefile_path, actual_command)
                    
                    # Check variable status and prompt
                    missing, empty, defaults = wizard.check_all_variables()
                    
                    if missing or empty:
                        # Show status
                        wizard.print_variable_status(missing, empty, defaults)
                        
                        # Prompt for variables
                        user_vars = wizard.prompt_all_variables(missing, empty)
                        if user_vars is None:
                            print(f"\n{Colors.YELLOW}Command cancelled.{Colors.NC}")
                            print()
                            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                            return
                    
                    # Build command with variables
                    wizard.user_vars = user_vars  # Store vars in wizard
                    cmd = wizard.build_make_command(user_vars)
                    
                except Exception as e:
                    # If variable wizard fails, fall back to direct execution
                    print(f"{Colors.YELLOW}⚠️  Variable wizard unavailable: {e}{Colors.NC}")
                    import traceback
                    if os.getenv('DEBUG'):
                        traceback.print_exc()
                    print(f"{Colors.CYAN}Executing command directly...{Colors.NC}\n")
                    cmd = None  # Will be set below
            
            # Fallback to direct command if wizard wasn't used
            if cmd is None:
                cmd = ["make", "-f", makefile_path, actual_command]
            
            # Execute the make command in the appropriate directory
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                check=False
            )
            
            print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Command completed successfully!{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Command failed with exit code {result.returncode}{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error executing command: {e}{Colors.NC}")
        
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
    
    def run(self):
        """Run the wizard main loop"""
        # Show startup info on first run
        self.show_startup_info()
        
        while True:
            # Show category menu
            self.print_category_menu()
            category_choice = self.get_user_choice(len(self.categories))
            
            if category_choice == 0:
                self.clear_screen()
                print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
                print(f"{Colors.GREEN}👋 Thanks for using the Trading System Wizard!{Colors.NC}")
                print(f"{Colors.YELLOW}Wizard shutdown complete.{Colors.NC}")
                print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
                sys.exit(0)
            
            # Get selected category
            category = list(self.categories.keys())[category_choice - 1]
            
            while True:
                # Show command menu
                self.print_command_menu(category)
                command_choice = self.get_user_choice(len(self.categories[category]))
                
                if command_choice == 0:
                    break  # Back to category menu
                
                # Execute selected command
                command = self.categories[category][command_choice - 1]
                self.execute_command(command)


def main():
    """Main entry point"""
    wizard = WizardMenu()
    wizard.run()


if __name__ == "__main__":
    main()


