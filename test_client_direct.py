#!/usr/bin/env python3
"""
Direct test of LLM client
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.llm_service.llm_client import LLMClient, LLMRequest, LLMTaskType, LLMModel, ProxyCallbackConfig


async def test_client_direct():
    """Test the LLM client directly"""
    print("🔍 Testing LLM client directly...")
    
    try:
        # Create client
        client = LLMClient(base_url="http://localhost:8081")
        
        # Test health check
        is_healthy = await client.health_check()
        print(f"✅ Health check: {is_healthy}")
        
        if not is_healthy:
            print("❌ Proxy is not healthy")
            return False
        
        # Create a simple request
        request = LLMRequest(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test"}
            ],
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            temperature=0.3,
            max_tokens=100,
            proxy_callback=ProxyCallbackConfig(
                success_url="http://localhost:8080/test-callback",
                timeout_seconds=30,
                metadata={"test": True}
            )
        )
        
        print(f"✅ Request created: {request.request_id}")
        
        # Generate response
        print("🔄 Generating response...")
        result = await client.generate(request, use_cache=False)
        
        print(f"✅ Result type: {type(result)}")
        print(f"✅ Result: {result}")
        
        if hasattr(result, 'request_id'):
            print(f"✅ Request ID: {result.request_id}")
        
        if hasattr(result, 'content'):
            print(f"✅ Content: {result.content}")
        
        if hasattr(result, 'error_message'):
            print(f"❌ Error: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 Direct LLM Client Test")
    print("=" * 40)
    
    success = await test_client_direct()
    
    if success:
        print("\n✅ Client test successful!")
    else:
        print("\n❌ Client test failed!")


if __name__ == "__main__":
    asyncio.run(main()) 