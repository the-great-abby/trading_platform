import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from decimal import Decimal
import os

async def update_order(temp_id, real_id, price):
    """Update a TEMP order with real Public.com order ID and fill info."""
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await session.execute(text('''
            UPDATE live_trades SET 
                public_order_id = :real_id, 
                status = 'FILLED', 
                price = :price, 
                filled_quantity = quantity, 
                remaining_quantity = 0, 
                filled_at = NOW() 
            WHERE public_order_id = :temp_id
        '''), {'temp_id': temp_id, 'real_id': real_id, 'price': Decimal(str(price))})
        await session.commit()
        print(f'✅ Updated {temp_id} → {real_id} at ${price}')

# Instructions
print("""
🔗 Order Update Helper
======================

Your TEMP orders to update:
1. QQQ  (TEMP_1759864502.388342) - Created: 2025-10-07 19:15:02
2. MSFT (TEMP_1759864501.847982) - Created: 2025-10-07 19:15:01
3. QQQ  (TEMP_1759862702.040189) - Created: 2025-10-07 18:45:02
4. MSFT (TEMP_1759862701.230061) - Created: 2025-10-07 18:45:01
5. QQQ  (TEMP_1759862685.796322) - Created: 2025-10-07 18:44:45
6. AAPL (TEMP_1759862685.233462) - Created: 2025-10-07 18:44:45
7. MSFT (TEMP_1759862684.536224) - Created: 2025-10-07 18:44:44

For each order, run:
asyncio.run(update_order('TEMP_ID', 'REAL_ORDER_ID', PRICE))

Examples:
---------
asyncio.run(update_order('TEMP_1759862702.040189', 'abc12345-1234-5678-9012-123456789012', 450.25))
asyncio.run(update_order('TEMP_1759862701.230061', 'def67890-1234-5678-9012-123456789012', 415.30))

Now ready to update orders!
""")

