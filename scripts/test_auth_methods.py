#!/usr/bin/env python3
"""
Test Different Authentication Methods for Public.com API
======================================================

Test various authentication methods to find the correct one.
"""

import asyncio
import httpx
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_auth_methods():
    """Test different authentication methods"""
    access_token = os.getenv('PUBLIC_API_KEY')
    if not access_token:
        logger.error("❌ PUBLIC_API_KEY not found in environment variables")
        return False
    
    logger.info(f"🔑 Testing with token: {access_token[:8]}...")
    
    base_url = "https://public.com/api/v1"
    endpoint = "/accounts"
    
    # Test different authentication methods
    auth_methods = [
        {
            "name": "Bearer Token (current)",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
        },
        {
            "name": "API Key Header",
            "headers": {
                "X-API-Key": access_token,
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
        },
        {
            "name": "Authorization Header (no Bearer)",
            "headers": {
                "Authorization": access_token,
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
        },
        {
            "name": "API Key Query Parameter",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            },
            "params": {"api_key": access_token}
        },
        {
            "name": "Token Query Parameter",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            },
            "params": {"token": access_token}
        }
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for method in auth_methods:
                logger.info(f"\n🔍 Testing: {method['name']}")
                
                try:
                    # Prepare request
                    url = f"{base_url}{endpoint}"
                    headers = method["headers"]
                    params = method.get("params", {})
                    
                    response = await client.get(url, headers=headers, params=params)
                    
                    logger.info(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info("✅ SUCCESS! Found working authentication method")
                        logger.info(f"  Method: {method['name']}")
                        logger.info(f"  Response: {response.text[:200]}...")
                        return True
                    elif response.status_code == 401:
                        logger.info("🔑 Authentication required - method might be correct but token invalid")
                    elif response.status_code == 403:
                        logger.info("🚫 Access forbidden - method might be correct but insufficient permissions")
                    elif response.status_code == 404:
                        logger.info("❌ Not found - method or endpoint incorrect")
                    else:
                        logger.info(f"⚠️  Unexpected status: {response.status_code}")
                    
                    # Show response headers for debugging
                    if response.status_code in [401, 403]:
                        logger.info(f"  Response headers: {dict(response.headers)}")
                        logger.info(f"  Response body: {response.text[:200]}...")
                        
                except Exception as e:
                    logger.error(f"  ❌ Error: {e}")
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing authentication methods: {e}")
        return False

async def test_different_endpoints():
    """Test different possible endpoints"""
    access_token = os.getenv('PUBLIC_API_KEY')
    if not access_token:
        return False
    
    base_url = "https://public.com/api/v1"
    
    # Test different possible endpoints
    endpoints = [
        "/accounts",
        "/account", 
        "/user/accounts",
        "/me/accounts",
        "/profile",
        "/user",
        "/me",
        "/portfolio",
        "/positions"
    ]
    
    logger.info(f"\n🔍 Testing different endpoints...")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
            
            for endpoint in endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    logger.info(f"  Testing: {url}")
                    
                    response = await client.get(url, headers=headers)
                    logger.info(f"    Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"✅ SUCCESS! Found working endpoint: {endpoint}")
                        logger.info(f"    Response: {response.text[:200]}...")
                        return True
                    elif response.status_code == 401:
                        logger.info(f"    🔑 Auth required: {endpoint}")
                    elif response.status_code == 403:
                        logger.info(f"    🚫 Forbidden: {endpoint}")
                    elif response.status_code == 404:
                        logger.info(f"    ❌ Not found: {endpoint}")
                    else:
                        logger.info(f"    ⚠️  Status {response.status_code}: {endpoint}")
                        
                except Exception as e:
                    logger.info(f"    ❌ Error: {endpoint} - {e}")
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing endpoints: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔍 Testing Public.com API authentication methods...")
    logger.info("📚 Testing various authentication approaches")
    
    # Test authentication methods
    auth_success = await test_auth_methods()
    
    if not auth_success:
        # Test different endpoints
        endpoint_success = await test_different_endpoints()
        
        if not endpoint_success:
            logger.info("\n❌ No working authentication method or endpoint found")
            logger.info("💡 Possible issues:")
            logger.info("  1. API key might be invalid or expired")
            logger.info("  2. API key might not have required permissions")
            logger.info("  3. API might require different authentication")
            logger.info("  4. API endpoints might be different than expected")
            logger.info("  5. API might be in beta or restricted access")
            logger.info("\n🔗 Check your API key at: https://public.com/public-api")
        else:
            logger.info("🎉 Found working endpoint!")
    else:
        logger.info("🎉 Found working authentication method!")

if __name__ == "__main__":
    asyncio.run(main())


