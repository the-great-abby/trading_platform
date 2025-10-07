#!/usr/bin/env python3
"""
Link filled orders from Public.com to TEMP orders in the database.

This script helps when:
1. Orders were submitted and got TEMP IDs
2. Public.com actually filled them
3. We need to update the database with the real order IDs and fill info
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'live-trading-service', 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from services.live_trading.models import LiveTrade, TradeStatus, LiveTradingAccount, APICredentials
from services.live_trading.public_api_client import PublicAPIClient, PublicAPIConfig


async def link_filled_orders(account_id: str, days_back: int = 1):
    """
    Link TEMP orders to filled orders from Public.com.
    
    Strategy:
    1. Get all TEMP orders from database
    2. Fetch recent filled orders from Public.com
    3. Match them by symbol, quantity, and approximate time
    4. Update database with real order IDs and fill info
    """
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://admin:password@localhost:5432/trading')
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"🔗 Linking TEMP orders to filled orders from Public.com")
        print(f"   Account: {account_id}")
        print(f"   Looking back: {days_back} days")
        print()
        
        # 1. Get TEMP orders from database
        temp_result = await session.execute(
            select(LiveTrade).where(
                LiveTrade.account_id == account_id,
                LiveTrade.public_order_id.like('TEMP_%')
            ).order_by(LiveTrade.created_at.desc())
        )
        temp_orders = temp_result.scalars().all()
        
        if not temp_orders:
            print("✅ No TEMP orders found in database")
            return
        
        print(f"📋 Found {len(temp_orders)} TEMP orders in database:")
        print(f"{'Symbol':<8} {'Qty':<5} {'Created At':<30} {'TEMP ID':<30}")
        print("-" * 80)
        for order in temp_orders:
            print(f"{order.symbol:<8} {order.quantity:<5} {order.created_at!s:<30} {order.public_order_id:<30}")
        print()
        
        # 2. Get Public.com credentials
        creds_result = await session.execute(
            select(APICredentials).where(
                APICredentials.account_id == account_id,
                APICredentials.is_active == True
            ).order_by(APICredentials.created_at.desc()).limit(1)
        )
        credentials = creds_result.scalar_one_or_none()
        
        if not credentials:
            print("❌ No active API credentials found")
            return
        
        # Get public_account_id
        acc_result = await session.execute(
            select(LiveTradingAccount.public_account_id).where(
                LiveTradingAccount.account_id == account_id
            ).limit(1)
        )
        public_account_id = acc_result.scalar_one_or_none()
        
        if not public_account_id:
            print("❌ Public account ID not found")
            return
        
        # 3. Initialize Public.com API client
        config = PublicAPIConfig()
        config.access_token = credentials.access_token
        config.secret_key = credentials.api_secret if hasattr(credentials, 'api_secret') else ""
        
        public_client = PublicAPIClient(config)
        
        # 4. Fetch recent filled orders from Public.com
        print(f"🔍 Fetching filled orders from Public.com account {public_account_id}...")
        
        try:
            # For now, we'll manually fetch orders
            # You'll need to implement get_recent_orders in PublicAPIClient
            # For this script, we'll use a simpler approach: check each TEMP order
            
            linked_count = 0
            
            for temp_order in temp_orders:
                print(f"\n🔍 Checking TEMP order: {temp_order.symbol} x{temp_order.quantity}")
                print(f"   Created: {temp_order.created_at}")
                print(f"   TEMP ID: {temp_order.public_order_id}")
                
                # Prompt user for the real Public.com order ID
                print(f"\n   💡 If you know the real Public.com order ID for this order, enter it now.")
                print(f"   💡 Check your Public.com app for {temp_order.symbol} filled around {temp_order.created_at}")
                print(f"   💡 Or press Enter to skip this order.")
                
                real_order_id = input(f"   Real order ID (or Enter to skip): ").strip()
                
                if not real_order_id:
                    print(f"   ⏭️  Skipped")
                    continue
                
                # Fetch order details from Public.com
                try:
                    order_status = await public_client.get_order_status(public_account_id, real_order_id)
                    
                    # Update the database record
                    temp_order.public_order_id = real_order_id
                    temp_order.status = TradeStatus.FILLED if order_status.get('status') == 'FILLED' else TradeStatus.PENDING
                    
                    if order_status.get('averagePrice'):
                        temp_order.price = Decimal(str(order_status['averagePrice']))
                    
                    if order_status.get('filledQuantity'):
                        temp_order.filled_quantity = int(float(order_status['filledQuantity']))
                        temp_order.remaining_quantity = temp_order.quantity - temp_order.filled_quantity
                    
                    if order_status.get('status') == 'FILLED':
                        temp_order.filled_at = datetime.utcnow()
                    
                    session.add(temp_order)
                    linked_count += 1
                    
                    print(f"   ✅ Linked! Status: {order_status.get('status')}, Price: ${temp_order.price}")
                    
                except Exception as e:
                    print(f"   ❌ Error fetching order {real_order_id}: {e}")
                    continue
            
            # Commit changes
            if linked_count > 0:
                await session.commit()
                print(f"\n✅ Successfully linked {linked_count} orders!")
            else:
                print(f"\n⚠️  No orders were linked")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await public_client.close()


async def list_public_orders(account_id: str, days_back: int = 1):
    """List recent orders from Public.com for reference."""
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://admin:password@localhost:5432/trading')
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get credentials
        creds_result = await session.execute(
            select(APICredentials).where(
                APICredentials.account_id == account_id,
                APICredentials.is_active == True
            ).order_by(APICredentials.created_at.desc()).limit(1)
        )
        credentials = creds_result.scalar_one_or_none()
        
        if not credentials:
            print("❌ No active API credentials found")
            return
        
        # Get public_account_id
        acc_result = await session.execute(
            select(LiveTradingAccount.public_account_id).where(
                LiveTradingAccount.account_id == account_id
            ).limit(1)
        )
        public_account_id = acc_result.scalar_one_or_none()
        
        # Initialize client
        config = PublicAPIConfig()
        config.access_token = credentials.access_token
        config.secret_key = credentials.api_secret if hasattr(credentials, 'api_secret') else ""
        
        public_client = PublicAPIClient(config)
        
        try:
            print(f"📋 Recent orders from Public.com account {public_account_id}:")
            print()
            print("NOTE: You'll need to check your Public.com app manually")
            print("      This script will help you link them to the TEMP orders")
            print()
            
        finally:
            await public_client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Link TEMP orders to filled Public.com orders')
    parser.add_argument('--account-id', 
                       default='19c25392-8b61-4b71-a344-0eb04d275528',
                       help='Internal account ID')
    parser.add_argument('--days', type=int, default=1,
                       help='How many days back to check')
    parser.add_argument('--list-public', action='store_true',
                       help='List orders from Public.com')
    
    args = parser.parse_args()
    
    if args.list_public:
        asyncio.run(list_public_orders(args.account_id, args.days))
    else:
        asyncio.run(link_filled_orders(args.account_id, args.days))

