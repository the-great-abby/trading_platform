#!/usr/bin/env python3
"""
Fast Test Runner - Focuses on reliable tests that don't hang or take too long
"""

import subprocess
import sys
import os
from pathlib import Path

def run_fast_tests():
    """Run a subset of tests that are known to be fast and reliable"""
    
    # Tests to include (fast, reliable)
    include_patterns = [
        "tests/unit/test_*.py",
        "tests/test_quick_wins.py"
    ]
    
    # Tests to exclude (problematic, slow, or hanging)
    exclude_patterns = [
        "tests/skipped/",
        "tests/unit/test_market_data_provider.py",  # Network dependencies
        "tests/unit/test_greeks_enhanced_strategy.py",  # LLM dependencies
        "tests/unit/test_social_media_sentiment_strategy.py",  # Slow
        "tests/unit/test_strategy_optimizer.py",  # Slow
        "tests/unit/test_space_station_monitor.py",  # Time.sleep issues
        "tests/unit/test_options_data_service.py",  # External API calls
    ]
    
    # Build the pytest command
    cmd = [
        "python3", "-m", "pytest",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "--junitxml=test-results.xml",
        "--html=test-report.html",
        "--self-contained-html",
        "--disable-warnings",
        "--maxfail=10",  # Stop after 10 failures
        "-x",  # Stop on first failure
    ]
    
    # Add include patterns
    for pattern in include_patterns:
        cmd.append(pattern)
    
    # Add exclude patterns
    for pattern in exclude_patterns:
        cmd.append(f"--ignore={pattern}")
    
    print("🚀 Running Fast Tests...")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    
    try:
        result = subprocess.run(cmd, check=False, timeout=300)  # 5 minute timeout
        return result.returncode
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return 1
    except KeyboardInterrupt:
        print("❌ Tests interrupted by user")
        return 1

def run_coverage_report():
    """Generate a coverage report from existing .coverage file"""
    if not os.path.exists(".coverage"):
        print("❌ No .coverage file found")
        return 1
    
    cmd = ["coverage", "report", "--show-missing"]
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ Coverage not available. Install with: pip install coverage")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "coverage":
        exit(run_coverage_report())
    else:
        exit(run_fast_tests()) 