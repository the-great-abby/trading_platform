#!/usr/bin/env python3
"""
Script to run strategy tests via the Strategy Testing Framework API
"""

import asyncio
import logging
import sys
import time
import httpx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:11003/api/v1/testing"

async def test_api_connection():
    """Test if the API is running and accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ API is running - Status: {data.get('status')}")
                return True
            else:
                logger.error(f"❌ API returned status code: {response.status_code}")
                return False
    except httpx.ConnectError:
        logger.error("❌ Cannot connect to API. Is the server running on port 11003?")
        logger.info("💡 Start the server with: python run_testing_framework.py")
        return False
    except Exception as e:
        logger.error(f"❌ Error connecting to API: {e}")
        return False

async def get_available_strategies():
    """Get list of available strategies from the API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/strategies")
            if response.status_code == 200:
                data = response.json()
                strategies = [s["name"] for s in data.get("strategies", [])]
                logger.info(f"📋 Found {len(strategies)} strategies: {', '.join(strategies)}")
                return strategies
            else:
                logger.error(f"❌ Failed to get strategies: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"❌ Error getting strategies: {e}")
        return []

async def test_strategy_validation(strategy_name):
    """Test strategy validation via API"""
    try:
        payload = {
            "strategy_name": strategy_name,
            "config": {
                "lookback_periods": 50,
                "confidence_threshold": 0.8
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/strategies/validate",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("validation_result", {})
                status = result.get("test_status", "unknown")
                duration = result.get("test_duration_seconds", 0)
                
                logger.info(f"✅ {strategy_name} validation: {status} ({duration:.3f}s)")
                return {
                    "strategy": strategy_name,
                    "status": status,
                    "duration": duration,
                    "success": True
                }
            else:
                logger.error(f"❌ {strategy_name} validation failed: {response.status_code}")
                return {
                    "strategy": strategy_name,
                    "status": "failed",
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"❌ Error testing {strategy_name}: {e}")
        return {
            "strategy": strategy_name,
            "status": "error",
            "success": False,
            "error": str(e)
        }

async def test_signal_generation(strategy_name):
    """Test signal generation via API"""
    try:
        payload = {
            "strategy_name": strategy_name,
            "symbol": "AAPL",
            "test_config": {
                "confidence_threshold": 0.8
            },
            "mock_data": {
                "symbol": "AAPL",
                "timeframe": "1d",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
                "market_regime": "bull",
                "price_data": [
                    {
                        "timestamp": "2024-01-01T00:00:00Z",
                        "open": 150.0,
                        "high": 155.0,
                        "low": 149.0,
                        "close": 154.0,
                        "volume": 100000,
                        "symbol": "AAPL"
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/signals/test",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("validation_result", {})
                score = result.get("validation_score", 0)
                signals = result.get("signals_generated", 0)
                
                logger.info(f"📡 {strategy_name} signals: {signals} signals, {score}% score")
                return {
                    "strategy": strategy_name,
                    "signals_generated": signals,
                    "validation_score": score,
                    "success": True
                }
            else:
                logger.error(f"❌ {strategy_name} signal test failed: {response.status_code}")
                return {
                    "strategy": strategy_name,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"❌ Error testing {strategy_name} signals: {e}")
        return {
            "strategy": strategy_name,
            "success": False,
            "error": str(e)
        }

async def run_comprehensive_api_tests():
    """Run comprehensive tests via the API"""
    logger.info("🧪 Starting comprehensive API-based strategy testing...")
    
    # Test API connection
    if not await test_api_connection():
        return False
    
    # Get available strategies
    strategies = await get_available_strategies()
    if not strategies:
        logger.error("❌ No strategies available for testing")
        return False
    
    results = []
    
    for strategy_name in strategies:
        logger.info(f"\n🔍 Testing {strategy_name}...")
        
        # Test strategy validation
        validation_result = await test_strategy_validation(strategy_name)
        
        # Test signal generation
        signal_result = await test_signal_generation(strategy_name)
        
        # Compile results
        strategy_result = {
            "strategy": strategy_name,
            "validation": validation_result,
            "signals": signal_result,
            "overall_success": validation_result.get("success", False) and signal_result.get("success", False)
        }
        
        results.append(strategy_result)
        
        # Log summary
        status = "✅ PASSED" if strategy_result["overall_success"] else "❌ FAILED"
        logger.info(f"📋 {strategy_name}: {status}")
    
    return results

def print_api_test_summary(results):
    """Print summary of API test results"""
    logger.info("\n" + "="*60)
    logger.info("📊 API STRATEGY TESTING SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for r in results if r.get("overall_success"))
    failed = len(results) - passed
    total = len(results)
    
    logger.info(f"Total Strategies Tested: {total}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    logger.info("\n📋 Detailed Results:")
    for result in results:
        status_emoji = "✅" if result.get("overall_success") else "❌"
        logger.info(f"{status_emoji} {result['strategy']}")
    
    return passed == total

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting API-based Strategy Testing Suite...")
        start_time = time.time()
        
        # Run comprehensive tests
        results = await run_comprehensive_api_tests()
        
        if results is False:
            logger.error("❌ API testing failed - check server connection")
            sys.exit(1)
        
        # Print summary
        all_passed = print_api_test_summary(results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n⏱️  Total test duration: {duration:.2f} seconds")
        
        if all_passed:
            logger.info("🎉 All API-based strategy tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some API-based strategy tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Fatal error during API testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())













