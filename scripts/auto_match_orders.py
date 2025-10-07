#!/usr/bin/env python3
"""
Auto-match TEMP orders to Public.com orders by symbol, quantity, and time
Since Public.com doesn't show UUIDs in their app, we match by characteristics
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from decimal import Decimal
import os
import sys
sys.path.insert(0, '/app/src')

from services.live_trading.models import LiveTradingAccount, APICredentials, LiveTrade
from services.live_trading.public_api_client import PublicAPIClient, PublicAPIConfig

async def auto_match():
    account_id = os.getenv('ACCOUNT_ID', '19c25392-8b61-4b71-a344-0eb04d275528')
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🔗 Auto-Matching TEMP Orders")
        print("=" * 80)
        print()
        
        # Get TEMP orders
        temp_result = await session.execute(
            select(LiveTrade).where(
                LiveTrade.account_id == account_id,
                LiveTrade.public_order_id.like('TEMP_%')
            ).order_by(LiveTrade.created_at.desc())
        )
        temp_orders = list(temp_result.scalars().all())
        
        if not temp_orders:
            print("✅ No TEMP orders to match")
            return
        
        print(f"Found {len(temp_orders)} TEMP orders to match")
        print()
        
        # Get credentials
        creds_result = await session.execute(
            select(APICredentials).where(
                APICredentials.account_id == account_id,
                APICredentials.is_active == True
            ).order_by(APICredentials.created_at.desc()).limit(1)
        )
        credentials = creds_result.scalar_one_or_none()
        
        if not credentials:
            print("❌ No active API credentials - refresh token first:")
            print("   make -f Makefile.live-trading live-trading-refresh-token")
            return
        
        # Get public_account_id
        acc_result = await session.execute(
            select(LiveTradingAccount.public_account_id).where(
                LiveTradingAccount.account_id == account_id
            ).limit(1)
        )
        public_account_id = acc_result.scalar_one_or_none()
        
        # Initialize Public.com API client
        config = PublicAPIConfig()
        config.access_token = credentials.access_token
        config.secret_key = credentials.api_secret if hasattr(credentials, 'api_secret') else ""
        
        public_client = PublicAPIClient(config)
        
        try:
            # Get orders from Public.com
            response = await public_client.client.get(
                f"/trading/{public_account_id}/orders",
                headers={
                    "Authorization": f"Bearer {config.access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Public.com API error: {response.status_code}")
                print("   Try refreshing token: make -f Makefile.live-trading live-trading-refresh-token")
                return
            
            public_orders = response.json()
            
            if not isinstance(public_orders, list):
                print(f"❌ Unexpected response format")
                return
            
            print(f"Fetched {len(public_orders)} orders from Public.com")
            print()
            
            matched_count = 0
            
            for temp_order in temp_orders:
                print(f"🔍 Matching: {temp_order.symbol} x{temp_order.quantity} at {temp_order.created_at}")
                
                # Find matching Public.com order
                best_match = None
                
                for pub_order in public_orders:
                    # Match by symbol and quantity
                    if pub_order.get('symbol') != temp_order.symbol:
                        continue
                    if int(float(pub_order.get('quantity', 0))) != temp_order.quantity:
                        continue
                    
                    # Match by approximate time (within 5 minutes)
                    pub_time_str = pub_order.get('createdAt', '')
                    if pub_time_str:
                        try:
                            pub_time = datetime.fromisoformat(pub_time_str.replace('Z', '+00:00'))
                            time_diff = abs((pub_time - temp_order.created_at).total_seconds())
                            
                            if time_diff < 300:  # Within 5 minutes
                                best_match = pub_order
                                break
                        except:
                            pass
                
                if best_match:
                    order_id = best_match.get('orderId')
                    price = best_match.get('averagePrice') or best_match.get('limitPrice', 0)
                    status = best_match.get('status', 'FILLED')
                    
                    # Update the database
                    await session.execute(text('''
                        UPDATE live_trades SET 
                            public_order_id = :real_id,
                            status = :status,
                            price = :price,
                            filled_quantity = quantity,
                            remaining_quantity = 0,
                            filled_at = NOW()
                        WHERE public_order_id = :temp_id
                    '''), {
                        'temp_id': temp_order.public_order_id,
                        'real_id': order_id,
                        'status': status,
                        'price': Decimal(str(price)) if price else None
                    })
                    
                    matched_count += 1
                    print(f"   ✅ Matched to {order_id[:8]}... (${price})")
                else:
                    print(f"   ⚠️  No match found")
                
                print()
            
            await session.commit()
            
            print("=" * 80)
            print(f"✅ Auto-match complete: {matched_count}/{len(temp_orders)} matched")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await public_client.close()

asyncio.run(auto_match())

