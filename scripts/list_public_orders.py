#!/usr/bin/env python3
"""
List recent orders from Public.com API to find order IDs
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os
import sys
sys.path.insert(0, '/app/src')

from services.live_trading.models import LiveTradingAccount, APICredentials
from services.live_trading.public_api_client import PublicAPIClient, PublicAPIConfig

async def list_orders():
    account_id = os.getenv('ACCOUNT_ID', '19c25392-8b61-4b71-a344-0eb04d275528')
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
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
        
        if not public_account_id:
            print("❌ Public account ID not found")
            return
        
        # Initialize Public.com API client
        config = PublicAPIConfig()
        config.access_token = credentials.access_token
        config.secret_key = credentials.api_secret if hasattr(credentials, 'api_secret') else ""
        
        public_client = PublicAPIClient(config)
        
        try:
            # Try to get account info first (this should work)
            print(f"🔍 Fetching orders from Public.com account: {public_account_id}")
            print()
            
            # Try the orders endpoint
            response = await public_client.client.get(
                f"/trading/{public_account_id}/orders",
                headers={
                    "Authorization": f"Bearer {config.access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                orders = response.json()
                
                if isinstance(orders, list):
                    print(f"📋 Found {len(orders)} orders:")
                    print()
                    print(f"{'Order ID':<38} {'Symbol':<8} {'Side':<6} {'Qty':<5} {'Status':<12} {'Price':<10} {'Time':<25}")
                    print("-" * 120)
                    
                    for order in orders[:20]:  # Show last 20 orders
                        order_id = order.get('orderId', 'N/A')
                        symbol = order.get('symbol', 'N/A')
                        side = order.get('side', 'N/A')
                        qty = order.get('quantity', 'N/A')
                        status = order.get('status', 'N/A')
                        price = order.get('averagePrice') or order.get('limitPrice', 'N/A')
                        created = order.get('createdAt', 'N/A')[:25] if order.get('createdAt') else 'N/A'
                        
                        print(f"{order_id:<38} {symbol:<8} {side:<6} {qty:<5} {status:<12} {price:<10} {created:<25}")
                else:
                    print(f"Unexpected response format: {orders}")
            else:
                print(f"❌ API returned status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await public_client.close()

asyncio.run(list_orders())

