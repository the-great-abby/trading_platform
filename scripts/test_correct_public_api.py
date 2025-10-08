#!/usr/bin/env python3
"""
Test Correct Public.com API Endpoints
====================================

Based on the official documentation, test the correct Public.com API endpoints.
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

async def test_public_api():
    """Test the correct Public.com API endpoints"""
    access_token = os.getenv('PUBLIC_API_KEY')
    if not access_token:
        logger.error("❌ PUBLIC_API_KEY not found in environment variables")
        return False
    
    logger.info(f"🔑 Testing with token: {access_token[:8]}...")
    
    # Correct base URL from official documentation
    base_url = "https://public.com/api/v1"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
            
            # Test the accounts endpoint (this is what your service calls)
            logger.info(f"🔍 Testing: {base_url}/accounts")
            response = await client.get(f"{base_url}/accounts", headers=headers)
            
            logger.info(f"  Status: {response.status_code}")
            logger.info(f"  Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info("✅ SUCCESS! Public.com API is working")
                logger.info(f"  Response: {response.text[:500]}...")
                return True
            elif response.status_code == 401:
                logger.error("❌ Authentication failed - check your API key")
                logger.error(f"  Response: {response.text}")
                return False
            elif response.status_code == 403:
                logger.error("❌ Access forbidden - API key may not have required permissions")
                logger.error(f"  Response: {response.text}")
                return False
            else:
                logger.error(f"❌ Unexpected status: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing Public.com API: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔍 Testing correct Public.com API endpoints...")
    logger.info("📚 Based on official documentation: https://public.com/api/v1")
    
    success = await test_public_api()
    
    if success:
        logger.info("🎉 Public.com API is working correctly!")
        logger.info("💡 The issue might be with your API key or permissions")
    else:
        logger.info("❌ Public.com API test failed")
        logger.info("💡 Check your API key and permissions at: https://public.com/public-api")

if __name__ == "__main__":
    asyncio.run(main())























