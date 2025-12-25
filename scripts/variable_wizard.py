#!/usr/bin/env python3
"""
Variable Wizard - Interactive variable prompt system for Makefile targets
Walks users through providing values for missing/unset variables before executing targets.
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional, Tuple

# Import parser - handle both direct execution and module import
try:
    from makefile_parser import MakefileParser, TargetVariables, VariableInfo
except ImportError:
    # If running as script, add scripts directory to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    from makefile_parser import MakefileParser, TargetVariables, VariableInfo


class Colors:
    """ANSI color codes"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class VariableWizard:
    """Interactive wizard for prompting Makefile variables"""
    
    def __init__(self, makefile_path: str, target: str):
        """Initialize wizard with Makefile path and target"""
        self.makefile_path = makefile_path
        self.target = target
        self.parser = MakefileParser(makefile_path)
        self.target_vars = self.parser.get_target_variables(target)
        self.user_vars: Dict[str, str] = {}
    
    def check_all_variables(self) -> Tuple[List[VariableInfo], List[VariableInfo], List[VariableInfo]]:
        """
        Check status of all variables for the target.
        Returns: (missing_vars, empty_vars, default_vars)
        """
        if not self.target_vars:
            return [], [], []
        
        missing = []
        empty = []
        defaults = []
        
        for var_info in self.target_vars.all_vars:
            status, value = self.parser.check_variable_status(var_info.name)
            
            if status == 'missing':
                missing.append(var_info)
            elif status == 'empty':
                empty.append(var_info)
            elif status == 'default':
                defaults.append(var_info)
        
        return missing, empty, defaults
    
    def print_variable_status(self, missing: List[VariableInfo], empty: List[VariableInfo], 
                             defaults: List[VariableInfo]):
        """Print summary of variable status"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.GREEN}📋 Variable Status for target '{self.target}'{Colors.NC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
        
        if missing:
            print(f"{Colors.RED}❌ Missing Variables (Required):{Colors.NC}")
            for var in missing:
                desc = f" - {var.description}" if var.description else ""
                print(f"  {Colors.RED}•{Colors.NC} {Colors.BOLD}{var.name}{Colors.NC}{desc}")
            print()
        
        if empty:
            print(f"{Colors.YELLOW}⚠️  Empty Variables (Should be set):{Colors.NC}")
            for var in empty:
                desc = f" - {var.description}" if var.description else ""
                print(f"  {Colors.YELLOW}•{Colors.NC} {Colors.BOLD}{var.name}{Colors.NC}{desc}")
            print()
        
        if defaults:
            print(f"{Colors.GREEN}✅ Variables with Defaults:{Colors.NC}")
            for var in defaults:
                status, value = self.parser.check_variable_status(var.name)
                desc = f" - {var.description}" if var.description else ""
                print(f"  {Colors.GREEN}•{Colors.NC} {Colors.BOLD}{var.name}{Colors.NC} = {Colors.CYAN}{value}{Colors.NC}{desc}")
            print()
        
        if not missing and not empty:
            print(f"{Colors.GREEN}✅ All variables are set or have defaults!{Colors.NC}\n")
    
    def prompt_variable(self, var_info: VariableInfo) -> Optional[str]:
        """Prompt user for a variable value"""
        status, current_value = self.parser.check_variable_status(var_info.name)
        
        # Build prompt
        prompt_parts = [f"{Colors.BOLD}{var_info.name}{Colors.NC}"]
        
        if var_info.description:
            prompt_parts.append(f"{Colors.CYAN}({var_info.description}){Colors.NC}")
        
        if status == 'default' and current_value:
            prompt_parts.append(f"{Colors.YELLOW}[default: {current_value}]{Colors.NC}")
        elif status == 'empty':
            prompt_parts.append(f"{Colors.YELLOW}[empty, recommended to set]{Colors.NC}")
        elif current_value:
            prompt_parts.append(f"{Colors.GREEN}[current: {current_value}]{Colors.NC}")
        
        prompt = " ".join(prompt_parts) + f": {Colors.GREEN}"
        
        try:
            value = input(prompt + Colors.NC).strip()
            
            # Use default if empty and default exists
            if not value and status == 'default' and current_value:
                print(f"{Colors.CYAN}Using default: {current_value}{Colors.NC}")
                return current_value
            
            # Allow empty for optional variables
            if not value and var_info.has_default:
                return value if value != '' else None
            
            return value if value else None
            
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Colors.YELLOW}Input cancelled.{Colors.NC}")
            return None
    
    def prompt_all_variables(self, missing: List[VariableInfo], empty: List[VariableInfo]) -> Dict[str, str]:
        """Prompt for all missing and empty variables"""
        vars_to_prompt = missing + empty
        if not vars_to_prompt:
            return {}
        
        print(f"{Colors.BOLD}{Colors.BLUE}🔧 Please provide values for the following variables:{Colors.NC}\n")
        
        provided_vars = {}
        for var_info in vars_to_prompt:
            value = self.prompt_variable(var_info)
            if value is not None:
                provided_vars[var_info.name] = value
            elif var_info.is_required:
                # Required variable was not provided
                print(f"{Colors.RED}❌ Required variable {var_info.name} not provided. Aborting.{Colors.NC}")
                return None
        
        return provided_vars
    
    def build_make_command(self, user_vars: Dict[str, str]) -> List[str]:
        """Build the make command with all variables"""
        cmd = ["make", "-f", self.makefile_path, self.target]
        
        # Add user-provided variables
        for var_name, var_value in user_vars.items():
            if var_value:  # Only add non-empty values
                cmd.append(f"{var_name}={var_value}")
        
        return cmd
    
    def execute(self, interactive: bool = True, skip_prompts: bool = False) -> int:
        """
        Execute the wizard and optionally run the make command.
        Returns: exit code (0 on success, non-zero on failure/abort)
        """
        if not self.target_vars:
            print(f"{Colors.YELLOW}⚠️  Target '{self.target}' not found or has no variable dependencies.{Colors.NC}")
            if not skip_prompts:
                # Just run the command without variable checking
                cmd = ["make", "-f", self.makefile_path, self.target]
                return subprocess.run(cmd, cwd=os.getcwd()).returncode
            return 0
        
        # Check variable status
        missing, empty, defaults = self.check_all_variables()
        
        # Show status
        self.print_variable_status(missing, empty, defaults)
        
        # If skip_prompts, just show status and return
        if skip_prompts:
            return 0
        
        # Prompt for variables if interactive
        if interactive and (missing or empty):
            user_vars = self.prompt_all_variables(missing, empty)
            if user_vars is None:
                return 1  # User aborted
            self.user_vars = user_vars
        else:
            self.user_vars = {}
        
        # Build and execute command
        if interactive:
            cmd = self.build_make_command(self.user_vars)
            
            print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
            print(f"{Colors.GREEN}🚀 Executing command:{Colors.NC}")
            print(f"{Colors.BOLD}{' '.join(cmd)}{Colors.NC}")
            print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
            
            try:
                result = subprocess.run(cmd, cwd=os.getcwd())
                return result.returncode
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Command interrupted.{Colors.NC}")
                return 130
        
        return 0


def main():
    """Main entry point for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive variable wizard for Makefile targets"
    )
    parser.add_argument("makefile", help="Path to Makefile")
    parser.add_argument("target", help="Makefile target name")
    parser.add_argument("--no-interactive", action="store_true", 
                       help="Only show variable status, don't prompt or execute")
    parser.add_argument("--skip-execution", action="store_true",
                       help="Prompt for variables but don't execute the command")
    
    args = parser.parse_args()
    
    wizard = VariableWizard(args.makefile, args.target)
    interactive = not args.no_interactive
    skip_exec = args.skip_execution
    
    if skip_exec:
        exit_code = wizard.execute(interactive=interactive, skip_prompts=False)
        # Don't execute, just return after prompting
        sys.exit(0 if exit_code == 0 else 1)
    else:
        exit_code = wizard.execute(interactive=interactive, skip_prompts=args.no_interactive)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

