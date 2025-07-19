#!/usr/bin/env python3
"""
Kubernetes LLM Proxy Integration Test
Tests the integration between the trading system and your LLM proxy in Kubernetes
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KubernetesLLMIntegrationTester:
    def __init__(self):
        self.llm_service_url = os.getenv('LLM_SERVICE_URL', 'http://localhost:8008')
        self.proxy_url = os.getenv('LLM_PROXY_URL', 'http://localhost:8081')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_llm_service_health(self) -> bool:
        """Test LLM service health endpoint"""
        try:
            logger.info(f"🔍 Testing LLM service health at {self.llm_service_url}/health")
            
            async with self.session.get(f"{self.llm_service_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info("✅ LLM service health check passed")
                    logger.info(f"   Status: {health_data.get('status', 'unknown')}")
                    logger.info(f"   Proxy Healthy: {health_data.get('llm_proxy_healthy', False)}")
                    return health_data.get('llm_proxy_healthy', False)
                else:
                    logger.error(f"❌ LLM service health check failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ LLM service health check error: {e}")
            return False
    
    async def test_sentiment_analysis(self) -> bool:
        """Test sentiment analysis through LLM service"""
        try:
            logger.info("🔍 Testing sentiment analysis through LLM service")
            
            payload = {
                "operation": "sentiment",
                "data": {
                    "text": "Apple reported strong Q4 earnings with 15% revenue growth, beating analyst expectations.",
                    "context": "Technology sector earnings season"
                },
                "model": "gpt-3.5-turbo",
                "proxy_callback": {
                    "success_url": "http://localhost:8080/callback/sentiment-success",
                    "timeout_url": "http://localhost:8080/callback/sentiment-timeout",
                    "timeout_seconds": 30,
                    "metadata": {"test": True, "operation": "sentiment"}
                },
                "priority": 3,
                "use_cache": False
            }
            
            async with self.session.post(f"{self.llm_service_url}/api/v1/llm", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    success = result.get('success', False)
                    logger.info(f"✅ Sentiment analysis test: {'PASSED' if success else 'FAILED'}")
                    if success:
                        logger.info(f"   Response: {result.get('data', 'No data')[:100]}...")
                    else:
                        logger.error(f"   Error: {result.get('error', 'Unknown error')}")
                    return success
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Sentiment analysis test failed: HTTP {response.status}")
                    logger.error(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Sentiment analysis test error: {e}")
            return False
    
    async def test_trading_signal_generation(self) -> bool:
        """Test trading signal generation through LLM service"""
        try:
            logger.info("🔍 Testing trading signal generation through LLM service")
            
            payload = {
                "operation": "signal",
                "data": {
                    "symbol": "AAPL",
                    "market_data": {
                        "price": 150.25,
                        "volume": 50000000,
                        "change_24h": 2.5,
                        "market_cap": 2500000000000
                    },
                    "news_data": [
                        {"title": "Apple beats earnings expectations", "sentiment": "positive"}
                    ],
                    "technical_indicators": {
                        "rsi": 65,
                        "macd": "bullish",
                        "sma_20": 148.50
                    }
                },
                "model": "gpt-4",
                "proxy_callback": {
                    "success_url": "http://localhost:8080/callback/signal-success",
                    "timeout_url": "http://localhost:8080/callback/signal-timeout",
                    "timeout_seconds": 45,
                    "metadata": {"test": True, "operation": "signal"}
                },
                "priority": 5,
                "use_cache": False
            }
            
            async with self.session.post(f"{self.llm_service_url}/api/v1/llm", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    success = result.get('success', False)
                    logger.info(f"✅ Trading signal test: {'PASSED' if success else 'FAILED'}")
                    if success:
                        logger.info(f"   Response: {result.get('data', 'No data')[:100]}...")
                    else:
                        logger.error(f"   Error: {result.get('error', 'Unknown error')}")
                    return success
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Trading signal test failed: HTTP {response.status}")
                    logger.error(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Trading signal test error: {e}")
            return False
    
    async def test_metrics_and_history(self) -> bool:
        """Test metrics and history endpoints"""
        try:
            logger.info("🔍 Testing metrics and history endpoints")
            
            # Test metrics
            async with self.session.get(f"{self.llm_service_url}/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    logger.info("✅ Metrics endpoint working")
                    
                    # Check callback metrics
                    callback_requests = metrics.get('service_metrics', {}).get('callback_requests', 0)
                    logger.info(f"   Callback Requests: {callback_requests}")
                    
                    # LLM metrics
                    llm_metrics = metrics.get('llm_metrics', {})
                    logger.info(f"   Total LLM Requests: {llm_metrics.get('total_requests', 0)}")
                    logger.info(f"   Successful Requests: {llm_metrics.get('successful_requests', 0)}")
                    logger.info(f"   Failed Requests: {llm_metrics.get('failed_requests', 0)}")
                else:
                    logger.error(f"❌ Metrics endpoint failed: HTTP {response.status}")
                    return False
            
            # Test history
            async with self.session.get(f"{self.llm_service_url}/history?limit=5") as response:
                if response.status == 200:
                    history = await response.json()
                    count = history.get('count', 0)
                    logger.info(f"✅ History endpoint working: {count} entries")
                else:
                    logger.error(f"❌ History endpoint failed: HTTP {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Metrics and history test error: {e}")
            return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Kubernetes LLM Integration Tests")
    logger.info("=" * 60)
    
    # Check environment
    logger.info("📋 Environment Configuration:")
    logger.info(f"   LLM Service URL: {os.getenv('LLM_SERVICE_URL', 'http://localhost:8008')}")
    logger.info(f"   LLM Proxy URL: {os.getenv('LLM_PROXY_URL', 'http://localhost:8081')}")
    
    # Test LLM service integration
    async with KubernetesLLMIntegrationTester() as tester:
        # Test service health
        health_ok = await tester.test_llm_service_health()
        
        if health_ok:
            # Test LLM operations
            logger.info("\n🧠 Testing LLM Operations...")
            sentiment_ok = await tester.test_sentiment_analysis()
            signal_ok = await tester.test_trading_signal_generation()
            
            # Test metrics and history
            metrics_ok = await tester.test_metrics_and_history()
            
            # Summary
            logger.info("\n📊 Test Summary")
            logger.info("=" * 30)
            logger.info(f"Service Health: {'✅' if health_ok else '❌'}")
            logger.info(f"Sentiment Analysis: {'✅' if sentiment_ok else '❌'}")
            logger.info(f"Trading Signal: {'✅' if signal_ok else '❌'}")
            logger.info(f"Metrics & History: {'✅' if metrics_ok else '❌'}")
            
            passed = sum([health_ok, sentiment_ok, signal_ok, metrics_ok])
            total = 4
            
            logger.info(f"\nOverall: {passed}/{total} tests passed")
            
            if passed == total:
                logger.info("🎉 All tests passed! Kubernetes integration is working correctly.")
            else:
                logger.warning("⚠️  Some tests failed. Check the details above.")
        else:
            logger.error("❌ Cannot proceed with tests - LLM service not healthy")
    
    logger.info("\n🏁 Kubernetes Integration Test Complete")

if __name__ == "__main__":
    asyncio.run(main()) 