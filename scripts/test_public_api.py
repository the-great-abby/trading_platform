#!/usr/bin/env python3
"""
Test Public.com API Endpoints
============================

This script tests different Public.com API endpoints to find the correct one.
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

async def test_endpoint(base_url: str, access_token: str) -> bool:
    """Test a specific API endpoint"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
            
            # Test different endpoints
            endpoints = [
                "/accounts",
                "/user",
                "/profile", 
                "/me",
                "/trading/accounts",
                "/api/accounts",
                "/api/v1/accounts"
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    logger.info(f"Testing: {url}")
                    response = await client.get(url, headers=headers)
                    logger.info(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"  ✅ SUCCESS: {url}")
                        logger.info(f"  Response: {response.text[:200]}...")
                        return True
                    elif response.status_code == 401:
                        logger.info(f"  🔑 Authentication required: {url}")
                    elif response.status_code == 404:
                        logger.info(f"  ❌ Not found: {url}")
                    else:
                        logger.info(f"  ⚠️  Other status: {url} - {response.status_code}")
                        
                except Exception as e:
                    logger.info(f"  ❌ Error: {url} - {str(e)[:100]}")
            
            return False
            
    except Exception as e:
        logger.error(f"Error testing {base_url}: {e}")
        return False

async def main():
    """Main function to test Public.com API endpoints"""
    access_token = os.getenv('PUBLIC_API_KEY')
    if not access_token:
        logger.error("❌ PUBLIC_API_KEY not found in environment variables")
        return
    
    logger.info(f"🔑 Testing with token: {access_token[:8]}...")
    
    # Test different base URLs
    base_urls = [
        "https://public.com/api",
        "https://public.com/api/v1", 
        "https://api.public.com",
        "https://api.public.com/v1",
        "https://public.com/v1",
        "https://public.com",
        "https://trading.public.com/api",
        "https://trading.public.com/api/v1"
    ]
    
    success_found = False
    
    for base_url in base_urls:
        logger.info(f"\n🔍 Testing base URL: {base_url}")
        logger.info("-" * 50)
        
        if await test_endpoint(base_url, access_token):
            success_found = True
            logger.info(f"✅ Found working endpoint: {base_url}")
            break
    
    if not success_found:
        logger.error("❌ No working API endpoints found")
        logger.info("\n💡 Possible issues:")
        logger.info("  1. API key might be invalid or expired")
        logger.info("  2. API endpoints might have changed")
        logger.info("  3. Public.com might require different authentication")
        logger.info("  4. API might be in beta or restricted access")

if __name__ == "__main__":
    asyncio.run(main())











