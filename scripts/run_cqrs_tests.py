#!/usr/bin/env python3
"""
CQRS Test Runner
Runs CQRS tests with proper setup and teardown
"""

import asyncio
import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command: list, cwd: str = None) -> int:
    """Run a command and return exit code"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"✅ Command succeeded: {' '.join(command)}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Command failed: {' '.join(command)}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        if e.stdout:
            logger.error(f"Output: {e.stdout}")
        return e.returncode

def setup_test_environment():
    """Setup test environment"""
    logger.info("🔧 Setting up test environment...")
    
    # Set test environment variables
    os.environ.update({
        'TEST_DB_HOST': 'localhost',
        'TEST_DB_PORT': '5433',
        'TEST_DB_NAME': 'trading_bot_test',
        'TEST_DB_USER': 'trading_user',
        'TEST_DB_PASSWORD': 'trading_pass',
        'TEST_REDIS_HOST': 'localhost',
        'TEST_REDIS_PORT': '6380',
        'TEST_REDIS_DB': '1',
        'TEST_RABBITMQ_HOST': 'localhost',
        'TEST_RABBITMQ_PORT': '5673',
        'TEST_RABBITMQ_USER': 'trading',
        'TEST_RABBITMQ_PASSWORD': 'trading_pass',
        'TEST_RABBITMQ_VHOST': 'trading_vhost_test'
    })
    
    logger.info("✅ Test environment variables set")

def run_tests():
    """Run CQRS tests"""
    logger.info("🧪 Running CQRS tests...")
    
    total_failures = 0
    
    # Run basic tests first (these should always work)
    logger.info("Running basic CQRS tests...")
    basic_result = run_command([
        "pytest", 
        "tests/cqrs/test_basic.py", 
        "-v", 
        "--tb=short"
    ])
    total_failures += basic_result
    
    # Run unit tests (may fail if CQRS modules don't exist yet)
    logger.info("Running unit tests...")
    unit_result = run_command([
        "pytest", 
        "tests/cqrs/test_query_services.py", 
        "tests/cqrs/test_command_services.py", 
        "-v", 
        "--tb=short"
    ])
    total_failures += unit_result
    
    # Run integration tests (may fail if CQRS modules don't exist yet)
    logger.info("Running integration tests...")
    integration_result = run_command([
        "pytest", 
        "tests/cqrs/test_integration.py", 
        "-v", 
        "--tb=short"
    ])
    total_failures += integration_result
    
    # Run performance tests (if any exist)
    logger.info("Running performance tests...")
    performance_result = run_command([
        "pytest", 
        "tests/cqrs/", 
        "-k", "performance", 
        "-v", 
        "--tb=short"
    ])
    total_failures += performance_result
    
    # Run all tests with coverage
    logger.info("Running all tests with coverage...")
    coverage_result = run_command([
        "pytest", 
        "tests/cqrs/", 
        "--cov=src", 
        "--cov-report=html", 
        "--cov-report=term-missing"
    ])
    total_failures += coverage_result
    
    return total_failures

def main():
    """Main test runner"""
    logger.info("🚀 Starting CQRS Test Suite")
    
    # Setup environment
    setup_test_environment()
    
    # Run tests
    exit_code = run_tests()
    
    if exit_code == 0:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed!")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
