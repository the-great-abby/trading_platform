#!/usr/bin/env python3
"""
Public.com Token Refresh Script
Refreshes the expired access token using your Public.com secret key
"""

import requests
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PublicTokenRefresher:
    def __init__(self):
        self.live_trading_url = "http://localhost:11120"
        self.account_id = "25cad391-6f18-44a5-9d1d-9caa73d99593"  # Updated after system restoration
        
        # Load environment variables
        load_dotenv()
        self.public_api_secret = os.getenv('PUBLIC_API_SECRET')
    
    def check_current_status(self):
        """Check current authentication status"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/auth/status/{self.account_id}", timeout=10)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"📊 Current Status:")
                logger.info(f"   • Account: {status.get('account_name', 'Unknown')}")
                logger.info(f"   • Authenticated: {'✅ Yes' if status.get('is_authenticated') else '❌ No'}")
                logger.info(f"   • Expires At: {status.get('expires_at', 'Unknown')}")
                logger.info(f"   • Last Used: {status.get('last_used', 'Unknown')}")
                return status
            else:
                logger.error(f"❌ Failed to get status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to check status: {e}")
            return None
    
    def refresh_access_token(self, secret_key, account_name="Live Trading Account"):
        """Refresh the access token using Public.com secret key"""
        try:
            logger.info("🔄 Refreshing access token...")
            
            # Prepare the request
            auth_data = {
                "secret_key": secret_key,
                "account_name": account_name,
                "account_type": "CASH",
                "validity_minutes": 1440  # 24 hours
            }
            
            # Make the request
            response = requests.post(
                f"{self.live_trading_url}/api/v1/auth/public-connect",
                json=auth_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Access token refreshed successfully!")
                logger.info(f"   • Credential ID: {result.get('credential_id', 'Unknown')}")
                logger.info(f"   • Account ID: {result.get('account_id', 'Unknown')}")
                logger.info(f"   • Status: {result.get('status', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Failed to refresh token: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to refresh token: {e}")
            return False
    
    def test_account_balance(self):
        """Test if account balance can now be retrieved"""
        try:
            logger.info("🔍 Testing account balance retrieval...")
            response = requests.get(f"{self.live_trading_url}/api/v1/accounts/{self.account_id}/balance", timeout=10)
            
            if response.status_code == 200:
                balance = response.json()
                logger.info("✅ Account balance retrieved successfully!")
                logger.info(f"   • Cash Balance: ${balance.get('cash_balance', 0):,.2f}")
                logger.info(f"   • Equity: ${balance.get('equity', 0):,.2f}")
                logger.info(f"   • Buying Power: ${balance.get('buying_power', 0):,.2f}")
                return True
            else:
                logger.error(f"❌ Still can't get balance: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to test balance: {e}")
            return False
    
    def run_token_refresh(self, secret_key=None):
        """Run the complete token refresh process"""
        logger.info("🚀 Starting Public.com token refresh process...")
        
        # Check current status
        logger.info("📊 Checking current authentication status...")
        status = self.check_current_status()
        
        if not status:
            logger.error("❌ Could not check current status")
            return False
        
        # Get secret key from .env file, command line argument, or user input
        if not secret_key:
            if self.public_api_secret:
                secret_key = self.public_api_secret
                logger.info("🔑 Using PUBLIC_API_SECRET from .env file")
            else:
                logger.info("🔑 No PUBLIC_API_SECRET found in .env file")
                logger.info("   (This is the secret key from your Public.com account settings)")
                logger.info("   (It's different from the access token - it's used to generate access tokens)")
                
                try:
                    secret_key = input("Enter your Public.com secret key: ").strip()
                except EOFError:
                    logger.error("❌ No secret key provided (non-interactive environment)")
                    logger.info("💡 Usage: python3 refresh_public_token.py <your_secret_key>")
                    return False
        
        if not secret_key:
            logger.error("❌ No secret key provided")
            return False
        
        # Refresh the token
        if self.refresh_access_token(secret_key):
            # Test if it works
            logger.info("🧪 Testing the refreshed token...")
            if self.test_account_balance():
                logger.info("🎉 Token refresh successful! Live trading is now ready.")
                return True
            else:
                logger.error("❌ Token refresh failed - still can't access account")
                return False
        else:
            logger.error("❌ Token refresh failed")
            return False

def main():
    """Main execution function"""
    import sys
    
    refresher = PublicTokenRefresher()
    
    print("""
================================================================================
🔑 PUBLIC.COM TOKEN REFRESH
================================================================================

This script will help you refresh your expired Public.com access token.

📋 What you need:
   • Your Public.com secret key (from account settings)
   • This is NOT the access token - it's the secret key used to generate tokens

🔍 Current Issue:
   • Your access token expired on 2025-09-28
   • The system can't retrieve account balance or place trades
   • All strategies are configured and ready - just need fresh credentials

================================================================================
""")
    
    # Check if secret key provided as command line argument
    secret_key = None
    if len(sys.argv) > 1:
        secret_key = sys.argv[1]
        logger.info(f"🔑 Using secret key from command line argument")
    
    if refresher.run_token_refresh(secret_key):
        print("\n🎉 SUCCESS!")
        print("📈 Your live trading system is now ready to trade")
        print("🔍 Run the monitoring script to verify everything is working")
    else:
        print("\n❌ FAILED!")
        print("🔧 Please check your Public.com secret key and try again")
        print("💡 Usage: python3 refresh_public_token.py <your_secret_key>")

if __name__ == "__main__":
    main()
