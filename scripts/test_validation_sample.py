#!/usr/bin/env python3
"""
Sample validation test script for the validation framework
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.execution.script_executor import ScriptExecutor


async def test_sample_validation():
    """Test sample validation of a backtest script"""
    try:
        print("🔍 Discovering scripts...")
        discovery = BacktestScriptDiscovery()
        scripts = discovery.discover_scripts()
        
        if not scripts:
            print("❌ No scripts found for validation")
            return False
            
        print(f"📊 Found {len(scripts)} scripts")
        
        print("🧪 Testing sample validation...")
        executor = ScriptExecutor()
        
        # Try to validate the first script
        first_script = scripts[0]
        print(f"   Testing: {first_script.name}")
        
        result = await executor.execute_script_async(first_script)
        print(f"✅ Sample validation completed: {result.status}")
        
        if result.stderr:
            print(f"   Error: {result.stderr}")
        else:
            print(f"   Execution time: {result.duration_seconds:.2f}s")
            if result.performance_metrics:
                print(f"   Total return: {result.performance_metrics.total_return_pct:.2f}%")
            
        return True
        
    except Exception as e:
        print(f"❌ Sample validation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sample_validation())
    sys.exit(0 if success else 1)
