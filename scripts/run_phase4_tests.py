#!/usr/bin/env python3
"""
Phase 4 Test Runner
Runs all Phase 4 API integration tests
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command: list, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED (exit code: {e.returncode})")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Phase 4 API Integration Test Runner")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test configuration
    test_env = "test-env"
    test_dir = "tests/cqrs"
    
    # Check if test environment exists
    if not Path(test_env).exists():
        print(f"❌ Test environment '{test_env}' not found!")
        print("Please run: python scripts/setup_test_env.sh")
        sys.exit(1)
    
    # Activate test environment and run tests
    python_cmd = f"{test_env}/bin/python"
    
    # Test categories
    test_categories = [
        {
            "name": "API Integration Tests",
            "file": "test_api_integration.py",
            "description": "FastAPI endpoints, WebSocket connections, and API validation"
        },
        {
            "name": "API Models Tests", 
            "file": "test_api_models.py",
            "description": "Pydantic models, request/response schemas, and validation"
        },
        {
            "name": "API Middleware Tests",
            "file": "test_api_middleware.py", 
            "description": "Authentication, rate limiting, logging, and error handling middleware"
        },
        {
            "name": "API Configuration Tests",
            "file": "test_api_config.py",
            "description": "Configuration management, environment variables, and deployment settings"
        }
    ]
    
    # Run each test category
    results = []
    for category in test_categories:
        test_file = f"{test_dir}/{category['file']}"
        
        if not Path(test_file).exists():
            print(f"⚠️  Test file {test_file} not found, skipping...")
            continue
        
        print(f"\n🧪 {category['name']}")
        print(f"📝 {category['description']}")
        
        # Run the test file
        success = run_command(
            [python_cmd, "-m", "pytest", test_file, "-v", "--tb=short"],
            f"Running {category['file']}"
        )
        
        results.append({
            "category": category['name'],
            "file": category['file'],
            "success": success
        })
    
    # Run all Phase 4 tests together
    print(f"\n🧪 All Phase 4 Tests")
    print(f"📝 Running all API integration tests together")
    
    all_tests_success = run_command(
        [python_cmd, "-m", "pytest", test_dir, "-k", "api", "-v", "--tb=short"],
        "Running all Phase 4 tests"
    )
    
    results.append({
        "category": "All Phase 4 Tests",
        "file": "All API tests",
        "success": all_tests_success
    })
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 PHASE 4 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} {result['category']}")
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 4 tests passed!")
        print("✅ API integration tests are ready for implementation")
        return 0
    else:
        print("⚠️  Some Phase 4 tests failed!")
        print("🔧 Please fix the failing tests before implementing Phase 4")
        return 1

if __name__ == "__main__":
    sys.exit(main())
