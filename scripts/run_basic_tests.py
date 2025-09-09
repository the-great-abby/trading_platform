#!/usr/bin/env python3
"""
Basic Test Runner - Runs only the tests that should work
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_basic_tests():
    """Run basic CQRS tests that should always work"""
    logger.info("🧪 Running Basic CQRS Tests")
    
    try:
        result = subprocess.run([
            "pytest", 
            "tests/cqrs/test_basic.py", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, check=True)
        
        logger.info("✅ Basic tests passed!")
        logger.info(f"Output: {result.stdout}")
        return 0
        
    except subprocess.CalledProcessError as e:
        logger.error("❌ Basic tests failed!")
        logger.error(f"Error: {e.stderr}")
        logger.error(f"Output: {e.stdout}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(run_basic_tests())
