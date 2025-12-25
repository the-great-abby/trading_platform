#!/usr/bin/env python3
"""
Makefile Parser for Variable Extraction
Parses Makefiles to extract variable definitions and identify variables used by targets.
"""

import os
import re
import subprocess
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VariableInfo:
    """Information about a Makefile variable"""
    name: str
    default_value: Optional[str]
    has_default: bool  # True if defined with ?=, False if defined with := or =
    is_required: bool  # True if no default and used in target
    description: Optional[str] = None  # From comments if available


@dataclass
class TargetVariables:
    """Variables used by a specific target"""
    target: str
    variables: Set[str]
    required_vars: List[VariableInfo]
    optional_vars: List[VariableInfo]
    all_vars: List[VariableInfo]


class MakefileParser:
    """Parser for extracting variables and target information from Makefiles"""
    
    # Regex patterns
    VAR_DEF_PATTERN = re.compile(r'^([A-Z_][A-Z0-9_]*)\s*([?:]?:?=)\s*(.*)$')
    VAR_REF_PATTERN = re.compile(r'\$\(([A-Z_][A-Z0-9_]*)\)')
    VAR_REF_SHELL_PATTERN = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')
    COMMENT_PATTERN = re.compile(r'^#+\s*(.+)$')
    TARGET_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+):')
    
    def __init__(self, makefile_path: str):
        """Initialize parser with Makefile path"""
        self.makefile_path = Path(makefile_path)
        if not self.makefile_path.exists():
            raise FileNotFoundError(f"Makefile not found: {makefile_path}")
        
        self.variables: Dict[str, VariableInfo] = {}
        self.targets: Dict[str, TargetVariables] = {}
        self._parse()
    
    def _parse(self):
        """Parse the Makefile"""
        with open(self.makefile_path, 'r') as f:
            lines = f.readlines()
        
        current_target = None
        target_lines = []
        last_comment = None
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for comment
            comment_match = self.COMMENT_PATTERN.match(line_stripped)
            if comment_match:
                last_comment = comment_match.group(1)
                continue
            
            # Check for variable definition
            var_match = self.VAR_DEF_PATTERN.match(line_stripped)
            if var_match:
                var_name = var_match.group(1)
                operator = var_match.group(2)
                value = var_match.group(3).strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Determine if it has a default (conditional assignment ?=)
                # := and = are immediate assignments (have values), ?= is conditional
                has_default = operator == '?='
                is_immediate = operator in (':=', '=')
                
                # Store variable info
                # If it's an immediate assignment (:= or =), treat it as having a default value
                effective_has_default = has_default or is_immediate
                effective_value = value if value else None
                
                self.variables[var_name] = VariableInfo(
                    name=var_name,
                    default_value=effective_value,
                    has_default=effective_has_default,
                    is_required=False,  # Will be determined later
                    description=last_comment if last_comment and 'variable' in last_comment.lower() else None
                )
                last_comment = None
                continue
            
            # Check for target
            target_match = self.TARGET_PATTERN.match(line_stripped)
            if target_match:
                # Save previous target
                if current_target and target_lines:
                    self._process_target(current_target, target_lines)
                
                current_target = target_match.group(1)
                target_lines = []
                continue
            
            # Collect target recipe lines (indented lines)
            if current_target and line.startswith('\t'):
                target_lines.append(line)
        
        # Process last target
        if current_target and target_lines:
            self._process_target(current_target, target_lines)
    
    def _process_target(self, target: str, lines: List[str]):
        """Process target lines to extract variable references"""
        all_var_refs = set()
        
        for line in lines:
            # Find $(VAR) references
            for match in self.VAR_REF_PATTERN.finditer(line):
                all_var_refs.add(match.group(1))
            
            # Find ${VAR} references (shell style)
            for match in self.VAR_REF_SHELL_PATTERN.finditer(line):
                all_var_refs.add(match.group(1))
        
        # Build variable info lists
        required_vars = []
        optional_vars = []
        all_vars_list = []
        
        for var_name in all_var_refs:
            if var_name in self.variables:
                var_info = self.variables[var_name]
                # Mark as required if no default or empty default
                if not var_info.has_default or (var_info.default_value is None or var_info.default_value == ''):
                    var_info.is_required = True
                    required_vars.append(var_info)
                else:
                    optional_vars.append(var_info)
                all_vars_list.append(var_info)
            else:
                # Variable used but not defined - assume required
                var_info = VariableInfo(
                    name=var_name,
                    default_value=None,
                    has_default=False,
                    is_required=True
                )
                required_vars.append(var_info)
                all_vars_list.append(var_info)
        
        self.targets[target] = TargetVariables(
            target=target,
            variables=all_var_refs,
            required_vars=sorted(required_vars, key=lambda v: v.name),
            optional_vars=sorted(optional_vars, key=lambda v: v.name),
            all_vars=sorted(all_vars_list, key=lambda v: v.name)
        )
    
    def get_target_variables(self, target: str) -> Optional[TargetVariables]:
        """Get variable information for a specific target"""
        return self.targets.get(target)
    
    def get_all_targets(self) -> List[str]:
        """Get list of all targets"""
        return list(self.targets.keys())
    
    def check_variable_status(self, var_name: str, env: Optional[Dict[str, str]] = None) -> Tuple[str, Optional[str]]:
        """
        Check variable status.
        Returns: (status, current_value)
        Status: 'set' | 'default' | 'missing' | 'empty'
        """
        if env is None:
            env = os.environ
        
        # Check environment first (environment takes precedence)
        if var_name in env:
            if env[var_name]:  # Non-empty value
                return ('set', env[var_name])
            else:  # Empty value in env (user explicitly set to empty)
                return ('empty', '')
        
        # Check Makefile definition
        if var_name in self.variables:
            var_info = self.variables[var_name]
            if var_info.has_default:
                if var_info.default_value:
                    return ('default', var_info.default_value)
                else:
                    # Has default but value is empty/None
                    return ('empty', None)
            else:
                # Defined but no default - check if set in env (already checked above)
                return ('missing', None)
        
        # Not defined in Makefile
        return ('missing', None)


def get_makefile_variables(makefile_path: str, target: str) -> Optional[TargetVariables]:
    """Convenience function to get variables for a target"""
    try:
        parser = MakefileParser(makefile_path)
        return parser.get_target_variables(target)
    except Exception as e:
        print(f"Error parsing Makefile: {e}")
        return None


if __name__ == "__main__":
    # Test the parser
    import sys
    if len(sys.argv) < 3:
        print("Usage: python makefile_parser.py <makefile> <target>")
        sys.exit(1)
    
    makefile = sys.argv[1]
    target = sys.argv[2]
    
    parser = MakefileParser(makefile)
    target_vars = parser.get_target_variables(target)
    
    if target_vars:
        print(f"\nVariables for target '{target}':")
        print(f"  Required: {[v.name for v in target_vars.required_vars]}")
        print(f"  Optional: {[v.name for v in target_vars.optional_vars]}")
        print(f"\nAll variables:")
        for var in target_vars.all_vars:
            status, value = parser.check_variable_status(var.name)
            default_str = f" (default: {var.default_value})" if var.has_default and var.default_value else ""
            print(f"  {var.name}: {status}{default_str}")
    else:
        print(f"Target '{target}' not found or has no variables")
        print(f"Available targets: {parser.get_all_targets()}")

