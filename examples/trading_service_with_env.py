#!/usr/bin/env python3
"""
Trading Service with Environment Variable Loading
===============================================

This example shows how to integrate environment variable loading
into your trading service.
"""

import os
import sys
import logging
from pathlib import Path

# Add the services directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'live-trading-service'))

from env_loader import load_trading_env, get_public_api_config, get_database_config, get_trading_config, validate_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function demonstrating environment variable usage"""
    print("🔧 Trading Service with Environment Variables")
    print("=" * 50)
    
    # Load environment variables
    print("1️⃣ Loading environment variables...")
    if not load_trading_env():
        print("❌ Failed to load environment variables")
        return 1
    
    # Validate required variables
    print("\n2️⃣ Validating required variables...")
    if not validate_env():
        print("❌ Environment validation failed")
        return 1
    
    # Get configurations
    print("\n3️⃣ Getting configurations...")
    
    try:
        # Public.com API configuration
        api_config = get_public_api_config()
        print("✅ Public.com API Config:")
        for key, value in api_config.items():
            if 'key' in key.lower():
                display_value = value[:8] + '...' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"  {key}: {display_value}")
        
        # Database configuration
        db_config = get_database_config()
        print("\n✅ Database Config:")
        for key, value in db_config.items():
            # Mask sensitive parts of URLs
            if 'password' in value.lower():
                masked_value = value.split('@')[0].split(':')[0] + ':***@' + value.split('@')[1]
            else:
                masked_value = value
            print(f"  {key}: {masked_value}")
        
        # Trading configuration
        trading_config = get_trading_config()
        print("\n✅ Trading Config:")
        for key, value in trading_config.items():
            print(f"  {key}: {value}")
        
        print("\n🎉 Environment variables loaded successfully!")
        print("💡 You can now use these configurations in your trading service.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting configurations: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)





















