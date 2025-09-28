#!/usr/bin/env python3
"""
Test Public.com Authentication Flow
==================================

Test the new two-step authentication flow with Public.com API.
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

async def test_public_auth_flow():
    """Test the complete Public.com authentication flow"""
    secret_key = os.getenv('PUBLIC_API_SECRET')
    if not secret_key:
        logger.error("❌ PUBLIC_API_SECRET not found in environment variables")
        logger.error("💡 Add PUBLIC_API_SECRET to your .env file")
        return False
    
    logger.info(f"🔑 Testing with secret key: {secret_key[:8]}...")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: Generate access token
            logger.info("🔐 Step 1: Generating access token...")
            auth_response = await client.post(
                "https://api.public.com/userapiauthservice/personal/access-tokens",
                json={
                    "validityInMinutes": 1440,  # 24 hours
                    "secret": secret_key
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "LiveTradingService/1.0.0"
                }
            )
            
            logger.info(f"  Auth Status: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                access_token = token_data.get("accessToken")
                
                if access_token:
                    logger.info("✅ Step 1 SUCCESS: Access token generated")
                    logger.info(f"  Token: {access_token[:20]}...")
                    
                    # Step 2: Use access token to get account info
                    logger.info("🔐 Step 2: Testing API access...")
                    api_response = await client.get(
                        "https://api.public.com/userapigateway/trading/account",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                            "User-Agent": "LiveTradingService/1.0.0"
                        }
                    )
                    
                    logger.info(f"  API Status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        account_data = api_response.json()
                        logger.info("✅ Step 2 SUCCESS: API access working")
                        logger.info(f"  Account data: {account_data}")
                        return True
                    else:
                        logger.error(f"❌ Step 2 FAILED: {api_response.status_code}")
                        logger.error(f"  Response: {api_response.text}")
                        return False
                else:
                    logger.error("❌ Step 1 FAILED: No access token in response")
                    logger.error(f"  Response: {auth_response.text}")
                    return False
            else:
                logger.error(f"❌ Step 1 FAILED: {auth_response.status_code}")
                logger.error(f"  Response: {auth_response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing authentication flow: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔍 Testing Public.com two-step authentication flow...")
    logger.info("📚 Step 1: Generate access token with secret key")
    logger.info("📚 Step 2: Use access token for API requests")
    
    success = await test_public_auth_flow()
    
    if success:
        logger.info("🎉 Public.com authentication flow is working!")
        logger.info("💡 Your live trading service can now connect to Public.com")
    else:
        logger.info("❌ Public.com authentication flow failed")
        logger.info("💡 Check your PUBLIC_API_SECRET in the .env file")
        logger.info("🔗 Get your secret key from: https://public.com/public-api")

if __name__ == "__main__":
    asyncio.run(main())


