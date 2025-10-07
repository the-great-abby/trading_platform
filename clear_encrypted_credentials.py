#!/usr/bin/env python3
"""
Clear Encrypted Credentials Script
Clears existing encrypted credentials from the database to allow fresh authentication
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CredentialCleaner:
    def __init__(self):
        self.live_trading_url = "http://localhost:11120"
        self.account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
    
    def check_service_health(self):
        """Check if the live trading service is healthy"""
        try:
            response = requests.get(f"{self.live_trading_url}/health", timeout=5)
            response.raise_for_status()
            logger.info("✅ Live trading service is healthy")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Live trading service is not healthy: {e}")
            return False
    
    def clear_account_credentials(self):
        """Clear encrypted credentials for the account"""
        try:
            logger.info("🧹 Clearing encrypted credentials...")
            
            # Try to delete the account credentials
            response = requests.delete(
                f"{self.live_trading_url}/api/v1/auth/accounts/{self.account_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Account credentials cleared successfully")
                return True
            elif response.status_code == 404:
                logger.info("ℹ️  No existing credentials found (account not found)")
                return True
            else:
                logger.error(f"❌ Failed to clear credentials: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to clear credentials: {e}")
            return False
    
    def verify_credentials_cleared(self):
        """Verify that credentials have been cleared"""
        try:
            logger.info("🔍 Verifying credentials are cleared...")
            response = requests.get(f"{self.live_trading_url}/api/v1/auth/status/{self.account_id}", timeout=10)
            
            if response.status_code == 404:
                logger.info("✅ Credentials successfully cleared (account not found)")
                return True
            elif response.status_code == 200:
                data = response.json()
                if not data.get('is_authenticated', False):
                    logger.info("✅ Account exists but is not authenticated (credentials cleared)")
                    return True
                else:
                    logger.warning("⚠️  Account still appears to be authenticated")
                    return False
            else:
                logger.error(f"❌ Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to verify credentials: {e}")
            return False
    
    def run_cleanup(self):
        """Run the complete credential cleanup process"""
        logger.info("🧹 Starting credential cleanup process...")
        
        if not self.check_service_health():
            logger.error("❌ Service is not healthy. Aborting cleanup.")
            return False
        
        if self.clear_account_credentials():
            if self.verify_credentials_cleared():
                logger.info("🎉 Credential cleanup completed successfully!")
                logger.info("💡 You can now run the token refresh script to authenticate fresh")
                return True
            else:
                logger.error("❌ Credential cleanup verification failed")
                return False
        else:
            logger.error("❌ Credential cleanup failed")
            return False

def main():
    """Main execution function"""
    cleaner = CredentialCleaner()
    
    print("""
================================================================================
🧹 CREDENTIAL CLEANUP
================================================================================

This script will clear existing encrypted credentials that are causing
Fernet key validation errors.

🔍 Problem:
   • Existing credentials were encrypted with an invalid key
   • New encryption key can't decrypt old data
   • Need to clear old credentials to start fresh

✅ Solution:
   • Clear existing encrypted credentials
   • Allow fresh authentication with new encryption key
   • Enable token refresh to work properly

================================================================================
""")
    
    if cleaner.run_cleanup():
        print("\n🎉 SUCCESS!")
        print("🧹 Old credentials cleared successfully")
        print("🔄 Now run: python3 refresh_public_token.py")
    else:
        print("\n❌ FAILED!")
        print("🔧 Credential cleanup failed - check logs for details")

if __name__ == "__main__":
    main()


















