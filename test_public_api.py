#!/usr/bin/env python3
"""
Test script for Public API integration
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.public_data import PublicDataProvider
from src.utils.config import Config

async def test_public_api():
    """Test Public API connection and basic functionality"""
    print("🧪 Testing Public API Integration...")
    
    # Load configuration
    load_dotenv()
    config = Config()
    
    # Check if Public credentials are configured
    if not config.public_username or not config.public_password:
        print("❌ Public API credentials not configured!")
        print("Please set PUBLIC_USERNAME and PUBLIC_PASSWORD in your .env file")
        return False
    
    try:
        # Initialize Public API provider
        provider = PublicDataProvider(config)
        
        # Test connection
        print("🔌 Connecting to Public API...")
        await provider.connect()
        print("✅ Connected successfully!")
        
        # Test getting accounts
        print("📊 Getting accounts...")
        accounts = await provider.get_accounts()
        print(f"✅ Found {len(accounts)} accounts")
        
        if accounts:
            account_id = accounts[0].get('id')
            print(f"📈 Getting portfolio for account {account_id}...")
            portfolio = await provider.get_account_portfolio(account_id)
            print(f"✅ Portfolio retrieved: {portfolio.get('total_value', 'N/A')}")
        
        # Test getting quotes
        print("📈 Getting quotes for AAPL and TSLA...")
        quotes = await provider.get_latest_data(['AAPL', 'TSLA'])
        print(f"✅ Retrieved quotes for {len(quotes)} symbols")
        
        for symbol, data in quotes.items():
            if not data.empty:
                price = data['Close'].iloc[-1]
                print(f"   {symbol}: ${price:.2f}")
        
        # Test getting instruments
        print("🔍 Getting available instruments...")
        instruments = await provider.get_instruments()
        print(f"✅ Found {len(instruments)} instruments")
        
        # Disconnect
        await provider.disconnect()
        print("✅ Disconnected successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Public API: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_public_api()
    
    if success:
        print("\n🎉 Public API integration test passed!")
        print("You can now use Public API with your trading bot.")
    else:
        print("\n💥 Public API integration test failed!")
        print("Please check your credentials and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 