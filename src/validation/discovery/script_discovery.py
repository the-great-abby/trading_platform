"""
Script discovery service for finding and cataloging backtest scripts

This service automatically discovers backtest scripts in the codebase using
multiple patterns and extracts metadata for validation.
"""

import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

from ..models.backtest_script import BacktestScript, ScriptType, ValidationStatus

logger = logging.getLogger(__name__)


class BacktestScriptDiscovery:
    """
    Service for discovering and cataloging backtest scripts in the codebase.
    """
    
    def __init__(self):
        self.discovered_scripts: Dict[str, BacktestScript] = {}
        self.discovery_patterns = [
            r".*backtest.*\.py$",
            r".*_backtest\.py$",
            r"test_.*backtest.*\.py$",
            r".*_strategy.*\.py$",
            r".*_simulation.*\.py$"
        ]
    
    def discover_scripts_in_directory(self, directory: Path) -> List[BacktestScript]:
        """
        Discover all backtest scripts in a directory.
        
        Args:
            directory: Directory to search for scripts
            
        Returns:
            List of discovered BacktestScript objects
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If path is not a directory
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        logger.info(f"Discovering backtest scripts in {directory}")
        
        discovered_scripts = []
        
        # Walk through directory recursively
        for file_path in directory.rglob("*.py"):
            if self._is_backtest_script(file_path):
                try:
                    script = self._extract_script_metadata(file_path)
                    if script:
                        discovered_scripts.append(script)
                        self.discovered_scripts[script.id] = script
                        logger.debug(f"Discovered script: {script.name} at {script.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to extract metadata from {file_path}: {e}")
        
        logger.info(f"Discovered {len(discovered_scripts)} backtest scripts")
        return discovered_scripts
    
    def discover_scripts(self, directory: Optional[Path] = None, 
                        script_type: Optional[ScriptType] = None,
                        status: Optional[ValidationStatus] = None,
                        name_pattern: Optional[str] = None) -> List[BacktestScript]:
        """
        Discover scripts with optional filtering.
        
        Args:
            directory: Directory to search (uses current directory if None)
            script_type: Filter by script type
            status: Filter by validation status
            name_pattern: Filter by name pattern
            
        Returns:
            List of filtered BacktestScript objects
        """
        if directory is None:
            directory = Path.cwd()
        
        # Get all scripts from directory
        scripts = self.discover_scripts_in_directory(directory)
        
        # Apply filters
        filtered_scripts = scripts
        
        if script_type:
            filtered_scripts = [s for s in filtered_scripts if s.script_type == script_type]
        
        if status:
            filtered_scripts = [s for s in filtered_scripts if s.validation_status == status]
        
        if name_pattern:
            pattern = re.compile(name_pattern, re.IGNORECASE)
            filtered_scripts = [s for s in filtered_scripts if pattern.search(s.name)]
        
        return filtered_scripts
    
    def _is_backtest_script(self, file_path: Path) -> bool:
        """
        Check if a file is a backtest script using multiple criteria.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            True if file appears to be a backtest script
        """
        # Check filename patterns
        filename = file_path.name
        for pattern in self.discovery_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        
        # Check file content for backtest indicators
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for backtest-related keywords
                backtest_keywords = [
                    'backtest', 'run_backtest', 'strategy', 'trading',
                    'portfolio', 'returns', 'sharpe', 'drawdown'
                ]
                
                content_lower = content.lower()
                keyword_count = sum(1 for keyword in backtest_keywords if keyword in content_lower)
                
                # If file contains multiple backtest keywords, likely a backtest script
                if keyword_count >= 2:
                    return True
                    
                # Check for function definitions with backtest in name
                if 'def ' in content and 'backtest' in content_lower:
                    return True
                    
        except Exception as e:
            logger.debug(f"Could not read file {file_path}: {e}")
        
        return False
    
    def _extract_script_metadata(self, file_path: Path) -> Optional[BacktestScript]:
        """
        Extract metadata from a backtest script file.
        
        Args:
            file_path: Path to the script file
            
        Returns:
            BacktestScript object with extracted metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to extract function and class information
            tree = ast.parse(content)
            
            # Extract function names
            function_names = []
            class_names = []
            docstring = ""
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_names.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    class_names.append(node.name)
                elif isinstance(node, ast.Module) and node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                        docstring = node.body[0].value.value
            
            # Determine script type
            script_type = self._classify_script_type(file_path, content, function_names, class_names)
            
            # Find main function
            main_function = self._find_main_function(function_names, content)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(content)
            
            # Create script object
            script = BacktestScript(
                name=self._generate_script_name(file_path),
                file_path=str(file_path.absolute()),
                function_name=main_function,
                class_name=class_names[0] if class_names else None,
                script_type=script_type,
                dependencies=dependencies,
                timeout_seconds=self._get_default_timeout(script_type)
            )
            
            return script
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return None
    
    def _classify_script_type(self, file_path: Path, content: str, 
                            function_names: List[str], class_names: List[str]) -> ScriptType:
        """
        Classify the script type based on content and structure.
        
        Args:
            file_path: Path to the script
            content: File content
            filename: List of function names
            class_names: List of class names
            
        Returns:
            ScriptType classification
        """
        content_lower = content.lower()
        filename_lower = file_path.name.lower()
        
        # Check for options-related content
        options_keywords = ['option', 'put', 'call', 'strike', 'greeks', 'iron condor', 'butterfly']
        if any(keyword in content_lower for keyword in options_keywords):
            return ScriptType.OPTIONS
        
        # Check for comprehensive/multi-strategy content
        comprehensive_keywords = ['comprehensive', 'multi', 'portfolio', 'allocation', 'ensemble']
        if any(keyword in content_lower for keyword in comprehensive_keywords):
            return ScriptType.COMPREHENSIVE
        
        # Check for multi-strategy content
        multi_strategy_keywords = ['strategy', 'strategies', 'multiple', 'combination']
        if any(keyword in content_lower for keyword in multi_strategy_keywords) and len(function_names) > 3:
            return ScriptType.MULTI_STRATEGY
        
        # Default to individual strategy
        return ScriptType.INDIVIDUAL_STRATEGY
    
    def _find_main_function(self, function_names: List[str], content: str) -> str:
        """
        Find the main function for script execution.
        
        Args:
            function_names: List of function names in the script
            content: File content
            
        Returns:
            Name of the main function
        """
        # Look for common backtest function names
        preferred_functions = [
            'run_backtest', 'execute_backtest', 'backtest', 'main',
            'run', 'execute', 'simulate', 'test_strategy'
        ]
        
        for func_name in preferred_functions:
            if func_name in function_names:
                return func_name
        
        # Look for functions with 'backtest' in the name
        for func_name in function_names:
            if 'backtest' in func_name.lower():
                return func_name
        
        # Look for functions with 'run' or 'execute' in the name
        for func_name in function_names:
            if 'run' in func_name.lower() or 'execute' in func_name.lower():
                return func_name
        
        # Return the first function if none of the above are found
        return function_names[0] if function_names else 'main'
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """
        Extract dependencies from script content.
        
        Args:
            content: File content
            
        Returns:
            List of dependency package names
        """
        dependencies = []
        
        # Common trading/finance packages
        common_packages = [
            'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn',
            'sklearn', 'tensorflow', 'torch', 'yfinance', 'alpha_vantage',
            'ccxt', 'backtrader', 'zipline', 'quantlib', 'pyfolio'
        ]
        
        content_lower = content.lower()
        
        for package in common_packages:
            if f'import {package}' in content_lower or f'from {package}' in content_lower:
                dependencies.append(package)
        
        return dependencies
    
    def _generate_script_name(self, file_path: Path) -> str:
        """
        Generate a script name from the file path.
        
        Args:
            file_path: Path to the script file
            
        Returns:
            Generated script name
        """
        # Remove .py extension
        name = file_path.stem
        
        # Remove common prefixes and suffixes
        name = re.sub(r'^(test_|_)', '', name)
        name = re.sub(r'(_backtest|_test|_script)$', '', name)
        
        # Convert to title case
        name = name.replace('_', ' ').replace('-', ' ').title()
        
        return name
    
    def _get_default_timeout(self, script_type: ScriptType) -> int:
        """
        Get default timeout for script type.
        
        Args:
            script_type: Type of script
            
        Returns:
            Timeout in seconds
        """
        timeouts = {
            ScriptType.INDIVIDUAL_STRATEGY: 300,  # 5 minutes
            ScriptType.MULTI_STRATEGY: 600,       # 10 minutes
            ScriptType.OPTIONS: 900,              # 15 minutes
            ScriptType.COMPREHENSIVE: 1800        # 30 minutes
        }
        return timeouts.get(script_type, 300)
    
    def get_script_by_id(self, script_id: str) -> Optional[BacktestScript]:
        """
        Get a script by its ID.
        
        Args:
            script_id: Script identifier
            
        Returns:
            BacktestScript object or None if not found
        """
        return self.discovered_scripts.get(script_id)
    
    def get_all_scripts(self) -> List[BacktestScript]:
        """
        Get all discovered scripts.
        
        Returns:
            List of all discovered scripts
        """
        return list(self.discovered_scripts.values())
    
    def refresh_script(self, script_id: str) -> Optional[BacktestScript]:
        """
        Refresh a script's metadata by re-reading the file.
        
        Args:
            script_id: Script identifier
            
        Returns:
            Updated BacktestScript object or None if not found
        """
        script = self.discovered_scripts.get(script_id)
        if not script:
            return None
        
        file_path = Path(script.file_path)
        if not file_path.exists():
            logger.warning(f"Script file no longer exists: {file_path}")
            return None
        
        # Re-extract metadata
        updated_script = self._extract_script_metadata(file_path)
        if updated_script:
            updated_script.id = script.id  # Preserve original ID
            updated_script.validation_status = script.validation_status  # Preserve status
            updated_script.last_validated_at = script.last_validated_at  # Preserve validation time
            self.discovered_scripts[script_id] = updated_script
            return updated_script
        
        return None











