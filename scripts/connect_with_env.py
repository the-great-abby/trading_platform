#!/usr/bin/env python3
"""
Connect to Public.com using Environment Variables
===============================================

This script connects to Public.com using the PUBLIC_API_KEY from your .env file.
"""

import asyncio
import json
import logging
import httpx
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PublicComConnector:
    """Connect to Public.com API using environment variables"""
    
    def __init__(self, live_trading_url: str = "http://localhost:11120"):
        self.live_trading_url = live_trading_url
        self.timeout = 30
        
        logger.info(f"🔗 Public.com Connector initialized: {live_trading_url}")
    
    async def check_service_health(self) -> bool:
        """Check if live trading service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Live trading service is healthy: {health_data}")
                    return True
                else:
                    logger.error(f"❌ Live trading service health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error checking live trading service health: {e}")
            return False
    
    async def connect_to_public(self, secret_key: str, account_name: str = "Live Trading Account") -> Dict[str, Any]:
        """Connect to Public.com API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/auth/public-connect",
                    json={
                        "secret_key": secret_key,
                        "account_name": account_name,
                        "account_type": "CASH",
                        "validity_minutes": 1440  # 24 hours
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Connected to Public.com successfully!")
                    logger.info(f"📊 Account: {result.get('account_name', 'Unknown')}")
                    logger.info(f"🆔 Account ID: {result.get('account_id', 'Unknown')}")
                    return result
                else:
                    error_detail = response.text
                    logger.error(f"❌ Failed to connect to Public.com: {response.status_code}")
                    logger.error(f"📝 Error details: {error_detail}")
                    return {"success": False, "error": error_detail}
        except Exception as e:
            logger.error(f"❌ Error connecting to Public.com: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_accounts(self) -> Dict[str, Any]:
        """Get connected accounts"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/api/v1/accounts")
                
                if response.status_code == 200:
                    accounts_data = response.json()
                    logger.info(f"📊 Found {accounts_data.get('total_count', 0)} connected accounts")
                    return accounts_data
                else:
                    logger.error(f"❌ Failed to get accounts: {response.status_code} - {response.text}")
                    return {"accounts": [], "total_count": 0}
        except Exception as e:
            logger.error(f"❌ Error getting accounts: {e}")
            return {"accounts": [], "total_count": 0}

async def main():
    """Main function to connect to Public.com"""
    try:
        # Get secret key from environment
        secret_key = os.getenv('PUBLIC_API_SECRET')
        if not secret_key:
            logger.error("❌ PUBLIC_API_SECRET not found in environment variables")
            logger.error("💡 Make sure your .env file contains PUBLIC_API_SECRET")
            return 1
        
        logger.info(f"🔑 Found PUBLIC_API_SECRET: {secret_key[:8]}...")
        
        # Initialize connector
        connector = PublicComConnector()
        
        # Check service health
        logger.info("🔍 Checking live trading service health...")
        if not await connector.check_service_health():
            logger.error("❌ Live trading service is not healthy. Exiting.")
            return 1
        
        # Check for existing accounts
        logger.info("📊 Checking for existing accounts...")
        accounts_data = await connector.get_accounts()
        
        if accounts_data.get("total_count", 0) > 0:
            logger.info("✅ You already have connected accounts!")
            for account in accounts_data.get("accounts", []):
                logger.info(f"  - {account.get('account_name', 'Unknown')} ({account.get('account_id', 'Unknown')})")
            
            logger.info("🎉 You're all set! You can now configure trading strategies.")
            return 0
        
        # Connect to Public.com
        logger.info("🔗 Connecting to Public.com...")
        result = await connector.connect_to_public(secret_key)
        
        if result.get("success", True):  # Default to True if no success field
            logger.info("🎉 Successfully connected to Public.com!")
            logger.info("📚 Next steps:")
            logger.info("  1. Configure strategies: python scripts/setup_live_trading_strategies.py")
            logger.info("  2. Monitor trading: http://localhost:11120/docs")
            logger.info("  3. Check account balance: curl -s http://localhost:11120/api/v1/accounts")
            return 0
        else:
            logger.error("❌ Failed to connect to Public.com")
            logger.error(f"📝 Error: {result.get('error', 'Unknown error')}")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Error in Public.com connection: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
