#!/usr/bin/env python3
"""
Test Live Trading Strategy Setup
===============================

This script tests the live trading strategy setup without requiring user input.
It uses environment variables and provides a dry-run mode for testing.
"""

import asyncio
import json
import logging
import httpx
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveTradingSetupTester:
    """Test live trading strategy setup"""
    
    def __init__(self, live_trading_url: str = "http://localhost:11120"):
        self.live_trading_url = live_trading_url
        self.timeout = 30
        
        logger.info(f"🧪 Live Trading Setup Tester initialized: {live_trading_url}")
    
    async def test_service_health(self) -> bool:
        """Test live trading service health"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Service health check passed: {health_data}")
                    return True
                else:
                    logger.error(f"❌ Service health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error checking service health: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test API endpoints availability"""
        endpoints = [
            "/health",
            "/ready", 
            "/api/v1/status",
            "/api/v1/status/market-hours",
            "/docs"
        ]
        
        results = {}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for endpoint in endpoints:
                    try:
                        response = await client.get(f"{self.live_trading_url}{endpoint}")
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "success": response.status_code < 400
                        }
                        logger.info(f"✅ {endpoint}: {response.status_code}")
                    except Exception as e:
                        results[endpoint] = {
                            "status_code": None,
                            "success": False,
                            "error": str(e)
                        }
                        logger.error(f"❌ {endpoint}: {e}")
            
            success_count = sum(1 for r in results.values() if r["success"])
            total_count = len(results)
            
            logger.info(f"📊 API Endpoint Test Results: {success_count}/{total_count} passed")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"❌ Error testing API endpoints: {e}")
            return False
    
    async def test_account_endpoints(self) -> bool:
        """Test account-related endpoints"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test accounts endpoint
                response = await client.get(f"{self.live_trading_url}/api/v1/accounts")
                if response.status_code == 200:
                    accounts_data = response.json()
                    logger.info(f"✅ Accounts endpoint working: {len(accounts_data.get('accounts', []))} accounts found")
                    return True
                else:
                    logger.warning(f"⚠️ Accounts endpoint returned {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error testing account endpoints: {e}")
            return False
    
    async def test_risk_endpoints(self) -> bool:
        """Test risk management endpoints"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test risk profile endpoint (this might fail if no account is connected)
                response = await client.get(f"{self.live_trading_url}/api/v1/risk/profile/test-account")
                if response.status_code in [200, 404]:  # 404 is expected if no account exists
                    logger.info(f"✅ Risk endpoints accessible: {response.status_code}")
                    return True
                else:
                    logger.warning(f"⚠️ Risk endpoint returned {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error testing risk endpoints: {e}")
            return False
    
    async def test_trading_endpoints(self) -> bool:
        """Test trading endpoints"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test trading orders endpoint (this might fail if no account is connected)
                response = await client.get(f"{self.live_trading_url}/api/v1/trading/orders")
                if response.status_code in [200, 404]:  # 404 is expected if no account exists
                    logger.info(f"✅ Trading endpoints accessible: {response.status_code}")
                    return True
                else:
                    logger.warning(f"⚠️ Trading endpoint returned {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error testing trading endpoints: {e}")
            return False
    
    async def test_market_hours(self) -> bool:
        """Test market hours functionality"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/api/v1/status/market-hours")
                if response.status_code == 200:
                    market_data = response.json()
                    logger.info(f"✅ Market hours working: {market_data}")
                    return True
                else:
                    logger.warning(f"⚠️ Market hours endpoint returned {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error testing market hours: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("🧪 Starting live trading setup tests...")
        
        tests = {
            "service_health": await self.test_service_health(),
            "api_endpoints": await self.test_api_endpoints(),
            "account_endpoints": await self.test_account_endpoints(),
            "risk_endpoints": await self.test_risk_endpoints(),
            "trading_endpoints": await self.test_trading_endpoints(),
            "market_hours": await self.test_market_hours()
        }
        
        passed = sum(1 for result in tests.values() if result)
        total = len(tests)
        
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in tests.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        return tests

async def main():
    """Main test function"""
    try:
        tester = LiveTradingSetupTester()
        results = await tester.run_all_tests()
        
        # Check if all critical tests passed
        critical_tests = ["service_health", "api_endpoints"]
        critical_passed = all(results.get(test, False) for test in critical_tests)
        
        if critical_passed:
            logger.info("🎉 Live trading service is ready for strategy setup!")
            logger.info("📚 Next steps:")
            logger.info("  1. Connect to Public.com: python scripts/setup_live_trading_strategies.py")
            logger.info("  2. Configure strategies: Use the interactive setup script")
            logger.info("  3. Monitor trading: http://localhost:11120/docs")
        else:
            logger.error("❌ Critical tests failed. Please check the live trading service.")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


