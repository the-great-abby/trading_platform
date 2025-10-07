#!/usr/bin/env python3
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from decimal import Decimal
import os

async def update(temp_id, real_id, price):
    engine = create_async_engine(os.getenv('DATABASE_URL'))
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
        '''), {
            'temp_id': temp_id,
            'real_id': real_id,
            'price': Decimal(str(price))
        })
        await session.commit()
        print(f'✅ Order updated successfully: {temp_id} → {real_id} at ${price}')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python3 update_temp_order.py <TEMP_ID> <REAL_ID> <PRICE>")
        sys.exit(1)
    
    asyncio.run(update(sys.argv[1], sys.argv[2], sys.argv[3]))

