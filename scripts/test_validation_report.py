#!/usr/bin/env python3
"""
Report generation test script for the validation framework
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.discovery.script_discovery import BacktestScriptDiscovery
from src.validation.reporting.report_generator import ReportGenerator


async def test_report_generation():
    """Test report generation for validation results"""
    try:
        print("🔍 Discovering scripts for report generation...")
        discovery = BacktestScriptDiscovery()
        scripts = discovery.discover_scripts()
        
        if not scripts:
            print("❌ No scripts found for report generation")
            return False
            
        print(f"📊 Found {len(scripts)} scripts")
        
        # Take a small sample for testing
        sample_size = min(10, len(scripts))
        sample_scripts = [s.id for s in scripts[:sample_size]]
        
        print(f"📋 Generating report for {sample_size} scripts...")
        reporter = ReportGenerator()
        
        report = await reporter.generate_report(
            script_ids=sample_scripts,
            report_type='summary'
        )
        
        print(f"✅ Sample report generated:")
        print(f"   Report ID: {report.report_id}")
        print(f"   Report type: {report.report_type}")
        print(f"   Total scripts: {len(sample_scripts)}")
        print(f"   Generated at: {report.generated_at}")
        
        if hasattr(report, 'summary'):
            summary = report.summary
            print(f"   Summary:")
            print(f"     - Total scripts: {summary.get('total_scripts', 'N/A')}")
            print(f"     - Successful: {summary.get('successful_scripts', 'N/A')}")
            print(f"     - Failed: {summary.get('failed_scripts', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_report_generation())
    sys.exit(0 if success else 1)













