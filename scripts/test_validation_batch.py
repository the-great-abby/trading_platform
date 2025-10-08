#!/usr/bin/env python3
"""
Batch validation test script for the validation framework
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.execution.batch_validator import BatchValidator


async def test_batch_validation():
    """Test batch validation of backtest scripts"""
    try:
        print("🔍 Discovering scripts for batch validation...")
        discovery = BacktestScriptDiscovery()
        scripts = discovery.discover_scripts()
        
        if not scripts:
            print("❌ No scripts found for batch validation")
            return False
            
        print(f"📊 Found {len(scripts)} scripts")
        
        # Take a small sample for testing
        sample_size = min(5, len(scripts))
        sample_scripts = [s.id for s in scripts[:sample_size]]
        
        print(f"🧪 Running batch validation on {sample_size} scripts...")
        batch = BatchValidator()
        
        results = await batch.validate_batch(
            script_ids=sample_scripts, 
            max_concurrent=2
        )
        
        successful = sum(1 for r in results if r.get('status') == 'PASSED')
        failed = len(results) - successful
        
        print(f"✅ Batch validation completed:")
        print(f"   Total: {len(results)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        # Show some results
        for i, result in enumerate(results[:3]):
            status = result.get('status', 'UNKNOWN')
            script_id = result.get('script_id', 'unknown')
            print(f"   {i+1}. {script_id}: {status}")
            
        return True
        
    except Exception as e:
        print(f"❌ Batch validation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_batch_validation())
    sys.exit(0 if success else 1)













