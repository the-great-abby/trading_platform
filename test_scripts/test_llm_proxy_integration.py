#!/usr/bin/env python3
"""
Test script to verify LLM proxy integration
Tests the connection between the LLM service and the proxy at http://localhost:8081/
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProxyTester:
    def __init__(self, proxy_url: str = "http://localhost:8081"):
        self.proxy_url = proxy_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_proxy_connectivity(self) -> bool:
        """Test basic connectivity to the LLM proxy"""
        try:
            logger.info(f"🔍 Testing connectivity to LLM proxy at {self.proxy_url}")
            
            if self.session is None:
                logger.error("❌ Session not initialized")
                return False
                
            async with self.session.get(f"{self.proxy_url}/") as response:
                if response.status == 200:
                    logger.info("✅ Proxy connectivity test passed")
                    return True
                else:
                    logger.error(f"❌ Proxy connectivity test failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Proxy connectivity test error: {e}")
            return False
    
    async def test_proxy_endpoints(self) -> Dict[str, bool]:
        """Test available proxy endpoints"""
        endpoints = {
            'root': '/',
            'health': '/health',
            'openapi': '/openapi.json',
            'docs': '/docs',
            'generate': '/api/generate',
            'chat': '/api/chat'
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                logger.info(f"🔍 Testing endpoint: {endpoint}")
                if self.session is None:
                    results[name] = False
                    logger.error(f"   {name}: ❌ Session not initialized")
                    continue
                    
                async with self.session.get(f"{self.proxy_url}{endpoint}") as response:
                    results[name] = response.status == 200
                    logger.info(f"   {name}: {'✅' if results[name] else '❌'} (HTTP {response.status})")
            except Exception as e:
                results[name] = False
                logger.error(f"   {name}: ❌ Error - {e}")
        
        return results
    
    async def test_proxy_generate_request(self) -> bool:
        """Test a simple generate request to the proxy"""
        try:
            logger.info("🔍 Testing proxy generate request")
            
            if self.session is None:
                logger.error("❌ Session not initialized")
                return False
            
            payload = {
                "model": "gpt-3.5-turbo",
                "prompt": "Hello, this is a test message. Please respond with 'Test successful'.",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 50
                }
            }
            
            async with self.session.post(
                f"{self.proxy_url}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    logger.info("✅ Proxy generate request successful")
                    logger.info(f"   Response: {response_data.get('response', 'No response')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Proxy generate request failed: HTTP {response.status}")
                    logger.error(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Proxy generate request error: {e}")
            return False
    
    async def test_proxy_callback_support(self) -> bool:
        """Test proxy callback URL support"""
        try:
            logger.info("🔍 Testing proxy callback URL support")
            
            if self.session is None:
                logger.error("❌ Session not initialized")
                return False
            
            payload = {
                "model": "gpt-3.5-turbo",
                "prompt": "Test callback support",
                "stream": False,
                "callback_url": "http://localhost:8080/callback/success",
                "timeout_url": "http://localhost:8080/callback/timeout",
                "callback_headers": {
                    "X-Request-ID": "test-123",
                    "X-Source": "trading-platform"
                },
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 50
                }
            }
            
            async with self.session.post(
                f"{self.proxy_url}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    logger.info("✅ Proxy callback support test successful")
                    logger.info(f"   Response: {response_data}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Proxy callback support test failed: HTTP {response.status}")
                    logger.error(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Proxy callback support test error: {e}")
            return False

async def test_llm_service_integration():
    """Test the LLM service integration with the proxy"""
    try:
        logger.info("🤖 Testing LLM Service Integration")
        logger.info("=" * 50)
        
        # Import LLM service components
        from src.services.llm_service.llm_client import LLMClient, LLMRequest, LLMResponse, LLMError, LLMTaskType
        from src.services.llm_service.service import LLMService
        from src.utils.trading_config import get_trading_config
        
        # Get configuration
        config = get_trading_config()
        logger.info(f"📋 LLM Service Config: {config.get('llm_service', {})}")
        
        # Test LLM client
        logger.info("\n🔧 Testing LLM Client")
        client = LLMClient(
            base_url="http://localhost:8081",
            timeout=30,
            max_retries=3
        )
        
        # Test health check
        is_healthy = await client.health_check()
        logger.info(f"   Health Check: {'✅' if is_healthy else '❌'}")
        
        if is_healthy:
            # Test a simple request
            request = LLMRequest(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, this is a test from the trading platform."}],
                task_type=LLMTaskType.SENTIMENT_ANALYSIS
            )
            
            logger.info("   Testing LLM request...")
            response = await client.generate(request)
            
            if isinstance(response, LLMResponse):
                logger.info("✅ LLM client test successful")
                logger.info(f"   Response: {response.content[:100]}...")
            elif isinstance(response, LLMError):
                logger.error(f"❌ LLM client test failed: {response.error_message}")
            else:
                logger.error(f"❌ LLM client test failed: Unknown response type")
        
        await client.disconnect()
        
        # Test LLM service
        logger.info("\n🔧 Testing LLM Service")
        service = LLMService(config)
        await service.initialize()
        
        # Test service health
        health = await service.get_health()
        logger.info(f"   Service Health: {health}")
        
        await service.shutdown()
        
        logger.info("\n✅ LLM Service Integration Test Complete")
        
    except Exception as e:
        logger.error(f"❌ LLM Service Integration Test Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    logger.info("🚀 Starting LLM Proxy Integration Tests")
    logger.info("=" * 60)
    
    # Test proxy directly
    async with LLMProxyTester() as tester:
        # Test basic connectivity
        connectivity_ok = await tester.test_proxy_connectivity()
        
        if connectivity_ok:
            # Test endpoints
            logger.info("\n🔍 Testing Proxy Endpoints")
            endpoint_results = await tester.test_proxy_endpoints()
            
            # Test generate request
            logger.info("\n🔍 Testing Proxy Generate Request")
            generate_ok = await tester.test_proxy_generate_request()
            
            # Test callback support
            logger.info("\n🔍 Testing Proxy Callback Support")
            callback_ok = await tester.test_proxy_callback_support()
            
            # Summary
            logger.info("\n📊 Test Summary")
            logger.info("=" * 30)
            logger.info(f"Connectivity: {'✅' if connectivity_ok else '❌'}")
            logger.info(f"Generate Request: {'✅' if generate_ok else '❌'}")
            logger.info(f"Callback Support: {'✅' if callback_ok else '❌'}")
            
            # Test LLM service integration
            if connectivity_ok and generate_ok:
                await test_llm_service_integration()
            else:
                logger.warning("⚠️  Skipping LLM service integration test due to proxy issues")
        else:
            logger.error("❌ Cannot proceed with tests - proxy not accessible")
    
    logger.info("\n🏁 Test Suite Complete")

if __name__ == "__main__":
    asyncio.run(main()) 