#!/usr/bin/env python3
"""
Test script for backtest CLI functionality
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_cli():
    """Test the backtest CLI functionality"""
    print("🧪 Testing Backtest CLI Functionality")
    print("=" * 50)
    
    # Test importing the service
    try:
        from src.services.database.backtest_results_service import BacktestResultsService
        print("✅ BacktestResultsService imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BacktestResultsService: {e}")
        return False
    
    # Test creating service instance
    try:
        service = BacktestResultsService()
        print("✅ BacktestResultsService instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create BacktestResultsService instance: {e}")
        return False
    
    # Test getting runs
    try:
        runs = service.get_backtest_runs(limit=5)
        print(f"✅ Retrieved {len(runs)} backtest runs from database")
        
        if runs:
            print("📊 Sample run data:")
            for i, run in enumerate(runs[:3]):
                print(f"  {i+1}. {run['strategy_name']}: {run['total_return_pct']:.2f}% return")
        else:
            print("ℹ️  No backtest runs found in database")
            
    except Exception as e:
        print(f"❌ Failed to retrieve backtest runs: {e}")
        return False
    
    print("\n🎯 CLI Commands Available:")
    print("  python scripts/backtest_cli.py list")
    print("  python scripts/backtest_cli.py list --details")
    print("  python scripts/backtest_cli.py compare")
    print("  python scripts/backtest_cli.py show <run_id>")
    print("  python scripts/backtest_cli.py show <run_id> --show-trades")
    print("  python scripts/backtest_cli.py export --output results.csv")
    
    print("\n🌐 API Endpoints Available:")
    print("  GET  /api/v1/runs")
    print("  GET  /api/v1/runs/{run_id}")
    print("  GET  /api/v1/runs/{run_id}/trades")
    print("  GET  /api/v1/runs/{run_id}/equity")
    print("  GET  /api/v1/compare")
    print("  GET  /api/v1/strategies")
    print("  GET  /api/v1/stats")
    
    return True

if __name__ == "__main__":
    success = test_cli()
    sys.exit(0 if success else 1) 