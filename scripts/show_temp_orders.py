#!/usr/bin/env python3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

async def show():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(text(
            "SELECT symbol, quantity, public_order_id, created_at FROM live_trades WHERE public_order_id LIKE 'TEMP_%' ORDER BY created_at DESC"
        ))
        rows = result.fetchall()
        print('Symbol | Qty | TEMP ID                        | Created At')
        print('-' * 80)
        for row in rows:
            print(f'{row[0]:<6} | {row[1]:<3} | {row[2]:<30} | {str(row[3])[:19]}')

asyncio.run(show())

