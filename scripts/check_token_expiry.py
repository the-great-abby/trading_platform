import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from datetime import datetime

async def check():
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text('''
            SELECT token_expires_at,
                   EXTRACT(EPOCH FROM (token_expires_at - NOW())) / 3600 as hours_remaining
            FROM api_credentials
            WHERE account_id = '19c25392-8b61-4b71-a344-0eb04d275528'
            ORDER BY created_at DESC LIMIT 1
        '''))
        
        row = result.fetchone()
        if row:
            expires, hours = row
            print(f'Token expires: {expires}')
            if hours > 0:
                print(f'⏰ {hours:.1f} hours remaining')
            else:
                print(f'❌ EXPIRED {-hours:.1f} hours ago')

asyncio.run(check())
