#!/usr/bin/env python3
"""
Validate a specific backtest script by various targeting methods
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.execution.script_executor import ScriptExecutor


class ScriptValidator:
    """Helper class for validating specific backtest scripts"""
    
    def __init__(self):
        self.discovery = BacktestScriptDiscovery()
        self.executor = ScriptExecutor()
        self.scripts_data = None
    
    def load_scripts_data(self) -> List[Dict[str, Any]]:
        """Load scripts data from JSON file"""
        try:
            with open('validation_scripts.json', 'r') as f:
                data = json.load(f)
                return data.get('scripts', [])
        except FileNotFoundError:
            print("❌ validation_scripts.json not found. Run 'make validation-discover-json' first.")
            return []
    
    def find_script_by_name(self, name: str, partial: bool = True) -> Optional[Dict[str, Any]]:
        """Find a script by name (exact or partial match)"""
        scripts = self.load_scripts_data()
        if not scripts:
            return None
            
        for script in scripts:
            script_name = script.get('name', '').lower()
            search_name = name.lower()
            
            if partial:
                if search_name in script_name:
                    return script
            else:
                if script_name == search_name:
                    return script
        
        return None
    
    def find_script_by_path(self, path: str, partial: bool = True) -> Optional[Dict[str, Any]]:
        """Find a script by file path (exact or partial match)"""
        scripts = self.load_scripts_data()
        if not scripts:
            return None
            
        for script in scripts:
            script_path = script.get('file_path', '').lower()
            search_path = path.lower()
            
            if partial:
                if search_path in script_path:
                    return script
            else:
                if script_path == search_path:
                    return script
        
        return None
    
    def find_script_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Find a script by exact ID"""
        scripts = self.load_scripts_data()
        if not scripts:
            return None
            
        for script in scripts:
            if script.get('id') == script_id:
                return script
        
        return None
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """Search for scripts by name or path containing query"""
        scripts = self.load_scripts_data()
        if not scripts:
            return []
            
        query = query.lower()
        matches = []
        
        for script in scripts:
            name = script.get('name', '').lower()
            path = script.get('file_path', '').lower()
            
            if query in name or query in path:
                matches.append(script)
        
        return matches
    
    async def validate_script(self, script_data: Dict[str, Any]) -> bool:
        """Validate a specific script"""
        try:
            print(f"🧪 Validating script: {script_data['name']}")
            print(f"   Path: {script_data['file_path']}")
            print(f"   Type: {script_data['script_type']}")
            
            # Convert dict to BacktestScript object
            from src.validation.models.backtest_script import BacktestScript
            script = BacktestScript(**script_data)
            
            result = await self.executor.execute_script_async(script)
            
            print(f"✅ Validation completed: {result.status}")
            print(f"   Execution time: {result.duration_seconds:.2f}s")
            
            if result.stderr:
                print(f"   Error: {result.stderr}")
            
            if result.performance_metrics:
                metrics = result.performance_metrics
                print(f"   Performance:")
                print(f"     - Total return: {metrics.total_return_pct:.2f}%")
                print(f"     - Sharpe ratio: {metrics.sharpe_ratio:.2f}")
                print(f"     - Max drawdown: {metrics.max_drawdown_pct:.2f}%")
                print(f"     - Total trades: {metrics.total_trades}")
            
            return True
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def print_script_info(self, script: Dict[str, Any]):
        """Print detailed script information"""
        print(f"📋 Script Information:")
        print(f"   ID: {script['id']}")
        print(f"   Name: {script['name']}")
        print(f"   Path: {script['file_path']}")
        print(f"   Type: {script['script_type']}")
        print(f"   Function: {script['function_name']}")
        print(f"   Class: {script.get('class_name', 'N/A')}")
        print(f"   Timeout: {script['timeout_seconds']}s")
        print(f"   Status: {script['validation_status']}")


async def main():
    parser = argparse.ArgumentParser(description='Validate a specific backtest script')
    parser.add_argument('--name', '-n', help='Script name (exact or partial)')
    parser.add_argument('--path', '-p', help='Script file path (exact or partial)')
    parser.add_argument('--id', '-i', help='Script ID (exact)')
    parser.add_argument('--search', '-s', help='Search query (searches name and path)')
    parser.add_argument('--list', '-l', help='List scripts matching pattern')
    parser.add_argument('--exact', action='store_true', help='Use exact matching instead of partial')
    parser.add_argument('--info', action='store_true', help='Show script info without validating')
    
    args = parser.parse_args()
    
    validator = ScriptValidator()
    
    if args.list:
        print(f"🔍 Searching for scripts containing: '{args.list}'")
        matches = validator.search_scripts(args.list)
        
        if matches:
            print(f"Found {len(matches)} matching scripts:")
            for i, script in enumerate(matches[:10]):  # Show first 10
                print(f"  {i+1}. {script['name']} ({script['script_type']})")
                print(f"     ID: {script['id']}")
                print(f"     Path: {script['file_path']}")
                print()
            
            if len(matches) > 10:
                print(f"... and {len(matches) - 10} more scripts")
                
            print("To validate one of these scripts, use:")
            print(f"  python {__file__} --id <script_id>")
            print(f"  python {__file__} --name <exact_name>")
        else:
            print("❌ No scripts found matching the search query")
        
        return
    
    script_data = None
    
    if args.id:
        script_data = validator.find_script_by_id(args.id)
        if not script_data:
            print(f"❌ Script with ID '{args.id}' not found")
            return
    
    elif args.name:
        script_data = validator.find_script_by_name(args.name, partial=not args.exact)
        if not script_data:
            print(f"❌ Script with name '{args.name}' not found")
            # Show similar names
            similar = validator.search_scripts(args.name)
            if similar:
                print("Similar scripts found:")
                for script in similar[:5]:
                    print(f"  - {script['name']} (ID: {script['id']})")
            return
    
    elif args.path:
        script_data = validator.find_script_by_path(args.path, partial=not args.exact)
        if not script_data:
            print(f"❌ Script with path '{args.path}' not found")
            return
    
    elif args.search:
        matches = validator.search_scripts(args.search)
        if not matches:
            print(f"❌ No scripts found matching '{args.search}'")
            return
        elif len(matches) == 1:
            script_data = matches[0]
        else:
            print(f"Found {len(matches)} matching scripts:")
            for i, script in enumerate(matches):
                print(f"  {i+1}. {script['name']} (ID: {script['id']})")
            print(f"\nTo validate a specific script, use --id with one of the IDs above")
            return
    
    else:
        print("❌ Please specify a script to validate using --name, --path, --id, or --search")
        print("Use --help for more information")
        return
    
    if script_data:
        validator.print_script_info(script_data)
        
        if not args.info:
            print()
            success = await validator.validate_script(script_data)
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())













