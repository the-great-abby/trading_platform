#!/usr/bin/env python3
"""
Trading System Setup Wizard - Interactive Installation of External Services

This wizard helps you install all necessary external service repositories
needed for the trading system to function properly.

It:
1. Identifies which services are required for the trading system
2. Checks which services are already installed
3. Extracts SSH connection info from existing .git/config files
4. Prompts you to install missing services
5. Clones missing repositories using SSH
"""

import os
import sys
import subprocess
import configparser
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

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
class ExternalService:
    """Represents an external service repository"""
    name: str
    description: str
    required: bool  # True for critical services, False for optional
    git_url: Optional[str] = None  # Will be extracted from .git/config if installed
    installed: bool = False
    install_path: Optional[str] = None


class SetupWizard:
    """Interactive setup wizard for external services"""
    
    # Define services needed for trading system
    # Mapping: service_name -> (description, required, expected_repo_name)
    TRADING_SYSTEM_SERVICES = {
        "database": ("PostgreSQL/TimescaleDB database infrastructure", True, "postgres_databases"),
        "rabbitmq": ("RabbitMQ message queue service", True, "message_queue"),
        "redis": ("Redis cache and session storage", True, "redis"),
        "registry": ("Docker registry for container images", True, "registry"),
        "playwright": ("Playwright testing framework (optional)", False, "playwright"),
        "grafana": ("Grafana monitoring dashboards (optional)", False, "grafana"),
    }
    
    def __init__(self, external_services_dir: str = None):
        """
        Initialize the setup wizard.
        
        Args:
            external_services_dir: Path to external_services directory
                                  Defaults to ../external_services from script location
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        trading_root = os.path.dirname(script_dir)
        
        if external_services_dir is None:
            # Assume external_services is sibling to trading directory
            code_dir = os.path.dirname(trading_root)
            external_services_dir = os.path.join(code_dir, "external_services")
        
        self.external_services_dir = Path(external_services_dir)
        self.services: Dict[str, ExternalService] = {}
        self._load_service_status()
    
    def _load_service_status(self):
        """Load status of all services - check what's installed and extract git URLs"""
        # First, infer the git URL pattern from an existing service
        git_url_pattern = self._infer_git_url_pattern()
        
        for service_name, (description, required, repo_name) in self.TRADING_SYSTEM_SERVICES.items():
            service_path = self.external_services_dir / service_name
            
            # Check if service is installed
            installed = service_path.exists() and service_path.is_dir()
            git_url = None
            
            if installed:
                # Try to extract git URL from .git/config
                git_config_path = service_path / ".git" / "config"
                if git_config_path.exists():
                    git_url = self._extract_git_url(str(git_config_path))
                
                # If we couldn't extract it, infer it
                if not git_url and git_url_pattern:
                    repo_to_use = repo_name if repo_name else service_name
                    git_url = git_url_pattern.format(repo_to_use)
            else:
                # Infer URL for missing services
                if git_url_pattern:
                    repo_to_use = repo_name if repo_name else service_name
                    git_url = git_url_pattern.format(repo_to_use)
            
            self.services[service_name] = ExternalService(
                name=service_name,
                description=description,
                required=required,
                git_url=git_url,
                installed=installed,
                install_path=str(service_path) if installed else None
            )
    
    def _infer_git_url_pattern(self) -> Optional[str]:
        """
        Infer the git URL pattern from existing services.
        Returns format string like "git@github.com:the-great-abby/{}.git"
        """
        # Check a few services that are likely to be installed
        check_services = ["database", "rabbitmq", "grafana"]
        
        for service_name in check_services:
            service_path = self.external_services_dir / service_name
            git_config_path = service_path / ".git" / "config"
            
            if git_config_path.exists():
                git_url = self._extract_git_url(str(git_config_path))
                if git_url:
                    # Extract pattern: git@github.com:user/repo.git -> git@github.com:user/{}.git
                    # Try to find the user/org part
                    if "github.com:" in git_url:
                        parts = git_url.split("github.com:")
                        if len(parts) == 2:
                            repo_part = parts[1].replace(".git", "")
                            # Extract user/org (everything before the last /)
                            if "/" in repo_part:
                                repo_parts = repo_part.split("/")
                                if len(repo_parts) >= 2:
                                    user_part = "/".join(repo_parts[:-1])
                                    return f"git@github.com:{user_part}/{{}}.git"
        
        return None
    
    def _extract_git_url(self, git_config_path: str) -> Optional[str]:
        """Extract git remote URL from .git/config file"""
        try:
            # Use a more lenient config parser that allows duplicate keys
            config = configparser.ConfigParser(allow_no_value=True, strict=False)
            config.read(git_config_path)
            
            if 'remote "origin"' in config:
                url = config['remote "origin"'].get('url')
                return url
        except Exception as e:
            # Fallback: try reading the file directly
            try:
                with open(git_config_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('url ='):
                            url = line.split('=', 1)[1].strip()
                            return url
            except Exception:
                pass  # If both methods fail, return None
        
        return None
    
    def print_header(self):
        """Print wizard header"""
        self.clear_screen()
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.GREEN}🧙 Trading System Setup Wizard{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
        print(f"{Colors.YELLOW}This wizard will help you install external service repositories")
        print(f"needed for the trading system to run properly.{Colors.NC}\n")
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_service_status(self):
        """Print status of all services"""
        print(f"{Colors.BOLD}{Colors.CYAN}External Service Status:{Colors.NC}\n")
        
        required_services = [s for s in self.services.values() if s.required]
        optional_services = [s for s in self.services.values() if not s.required]
        
        print(f"{Colors.BOLD}Required Services:{Colors.NC}")
        for service in required_services:
            status_icon = "✅" if service.installed else "❌"
            status_text = f"{Colors.GREEN}Installed{Colors.NC}" if service.installed else f"{Colors.RED}Not Installed{Colors.NC}"
            print(f"  {status_icon} {Colors.BOLD}{service.name}{Colors.NC}")
            print(f"      {service.description}")
            print(f"      Status: {status_text}")
            if service.git_url:
                print(f"      Git URL: {Colors.CYAN}{service.git_url}{Colors.NC}")
            print()
        
        if optional_services:
            print(f"{Colors.BOLD}Optional Services:{Colors.NC}")
            for service in optional_services:
                status_icon = "✅" if service.installed else "⚪"
                status_text = f"{Colors.GREEN}Installed{Colors.NC}" if service.installed else f"{Colors.YELLOW}Not Installed (Optional){Colors.NC}"
                print(f"  {status_icon} {Colors.BOLD}{service.name}{Colors.NC}")
                print(f"      {service.description}")
                print(f"      Status: {status_text}")
                if service.git_url:
                    print(f"      Git URL: {Colors.CYAN}{service.git_url}{Colors.NC}")
                print()
    
    def get_missing_required_services(self) -> List[ExternalService]:
        """Get list of required services that are not installed"""
        return [s for s in self.services.values() if s.required and not s.installed]
    
    def get_missing_optional_services(self) -> List[ExternalService]:
        """Get list of optional services that are not installed"""
        return [s for s in self.services.values() if not s.required and not s.installed]
    
    def install_service(self, service: ExternalService) -> bool:
        """
        Install a service by cloning its git repository.
        
        Returns:
            True if installation was successful, False otherwise
        """
        if not service.git_url:
            print(f"{Colors.RED}Error: No git URL available for {service.name}{Colors.NC}")
            return False
        
        if service.installed:
            print(f"{Colors.YELLOW}Service {service.name} is already installed at {service.install_path}{Colors.NC}")
            return True
        
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}Installing: {service.name}{Colors.NC}")
        print(f"Description: {service.description}")
        print(f"Git URL: {Colors.CYAN}{service.git_url}{Colors.NC}")
        print(f"Install Path: {Colors.CYAN}{self.external_services_dir / service.name}{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
        
        # Ensure external_services directory exists
        self.external_services_dir.mkdir(parents=True, exist_ok=True)
        
        # Clone the repository
        install_path = self.external_services_dir / service.name
        try:
            result = subprocess.run(
                ["git", "clone", service.git_url, str(install_path)],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"{Colors.GREEN}✅ Successfully installed {service.name}!{Colors.NC}\n")
            
            # Update service status
            service.installed = True
            service.install_path = str(install_path)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Failed to install {service.name}{Colors.NC}")
            print(f"Error: {e.stderr}")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ Unexpected error installing {service.name}: {e}{Colors.NC}")
            return False
    
    def interactive_install(self):
        """Interactive installation process"""
        self.print_header()
        self.print_service_status()
        
        missing_required = self.get_missing_required_services()
        missing_optional = self.get_missing_optional_services()
        
        if not missing_required and not missing_optional:
            print(f"{Colors.GREEN}✅ All services are already installed!{Colors.NC}\n")
            return
        
        # Install required services
        if missing_required:
            print(f"{Colors.BOLD}{Colors.YELLOW}Required services that need installation:{Colors.NC}")
            for i, service in enumerate(missing_required, 1):
                print(f"  {i}. {service.name} - {service.description}")
            print()
            
            response = input(f"{Colors.GREEN}Install all required services? (y/n): {Colors.NC}").strip().lower()
            
            if response in ['y', 'yes']:
                print()
                for service in missing_required:
                    if not self.install_service(service):
                        print(f"{Colors.RED}Failed to install {service.name}. Continue? (y/n): {Colors.NC}")
                        cont = input().strip().lower()
                        if cont not in ['y', 'yes']:
                            break
                    print()  # Blank line between installations
            else:
                # Install individually
                for service in missing_required:
                    response = input(f"{Colors.GREEN}Install {service.name}? (y/n): {Colors.NC}").strip().lower()
                    if response in ['y', 'yes']:
                        self.install_service(service)
                        print()
        
        # Install optional services
        if missing_optional:
            print(f"{Colors.BOLD}{Colors.YELLOW}Optional services available for installation:{Colors.NC}")
            for i, service in enumerate(missing_optional, 1):
                print(f"  {i}. {service.name} - {service.description}")
            print()
            
            response = input(f"{Colors.GREEN}Install optional services? (y/n): {Colors.NC}").strip().lower()
            
            if response in ['y', 'yes']:
                for service in missing_optional:
                    response = input(f"{Colors.GREEN}Install {service.name}? (y/n): {Colors.NC}").strip().lower()
                    if response in ['y', 'yes']:
                        self.install_service(service)
                        print()
        
        # Final status
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}Installation Summary:{Colors.NC}\n")
        self.print_service_status()
        print(f"{Colors.GREEN}Setup complete!{Colors.NC}\n")
    
    def run(self):
        """Run the setup wizard"""
        try:
            self.interactive_install()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Setup wizard interrupted by user.{Colors.NC}")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.NC}")
            sys.exit(1)


def main():
    """Main entry point"""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()

