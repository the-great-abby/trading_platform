#!/usr/bin/env python3
"""
Simple LLM Proxy Integration Test
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_proxy_direct():
    """Test direct proxy communication"""
    print("🔍 Testing direct proxy communication...")
    
    async with aiohttp.ClientSession() as session:
        # Test the proxy directly
        payload = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hello, this is a test message",
            "callback_url": "http://localhost:8080/test-callback"
        }
        
        try:
            async with session.post(
                "http://localhost:8081/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Proxy response: {data}")
                    return data.get('request_id')
                else:
                    error_text = await response.text()
                    print(f"❌ Proxy error: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Proxy connection error: {e}")
            return None


async def test_service_integration():
    """Test service integration"""
    print("\n🔍 Testing service integration...")
    
    async with aiohttp.ClientSession() as session:
        # Test the service
        payload = {
            "operation": "sentiment",
            "data": {
                "text": "Apple reported strong earnings today"
            },
            "model": "gpt-3.5-turbo",
            "proxy_callback": {
                "success_url": "http://localhost:8080/test-callback",
                "timeout_seconds": 30,
                "metadata": {"test": True}
            }
        }
        
        try:
            async with session.post(
                "http://localhost:8008/api/v1/llm",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Service response: {data}")
                    return data.get('success', False)
                else:
                    error_text = await response.text()
                    print(f"❌ Service error: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Service connection error: {e}")
            return False


async def main():
    """Main test function"""
    print("🚀 Simple LLM Proxy Integration Test")
    print("=" * 50)
    
    # Test proxy directly
    request_id = await test_proxy_direct()
    
    if request_id:
        print(f"✅ Proxy test successful - Request ID: {request_id}")
        
        # Wait a moment and check status
        await asyncio.sleep(2)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"http://localhost:8081/api/status/{request_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        print(f"📊 Request status: {status_data.get('status')}")
                        print(f"   Processing time: {status_data.get('processing_time')}s")
                        print(f"   Error: {status_data.get('error')}")
                    else:
                        print(f"❌ Status check failed: {response.status}")
            except Exception as e:
                print(f"❌ Status check error: {e}")
    else:
        print("❌ Proxy test failed")
    
    # Test service integration
    service_success = await test_service_integration()
    
    if service_success:
        print("✅ Service integration test successful")
    else:
        print("❌ Service integration test failed")
    
    print("\n📝 Summary:")
    print("- Proxy direct test:", "✅ PASS" if request_id else "❌ FAIL")
    print("- Service integration test:", "✅ PASS" if service_success else "❌ FAIL")


if __name__ == "__main__":
    asyncio.run(main()) 