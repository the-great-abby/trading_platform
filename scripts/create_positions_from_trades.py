#!/usr/bin/env python3
"""
Create positions from filled trades
This syncs your imported manual trades into the positions table
so the exit logic knows what you're holding
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime
import os
import sys
import uuid

async def create_positions():
    account_id = '19c25392-8b61-4b71-a344-0eb04d275528'
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("📊 Creating Positions from Filled Trades")
        print("=" * 60)
        print()
        
        # Get filled trades grouped by symbol
        result = await session.execute(text('''
            SELECT 
                symbol,
                SUM(quantity) as total_quantity,
                AVG(price) as avg_price,
                SUM(total_amount) as total_cost
            FROM live_trades
            WHERE account_id = :account_id
            AND status = 'FILLED'
            AND action = 'BUY'
            GROUP BY symbol
            ORDER BY symbol
        '''), {'account_id': account_id})
        
        positions = result.fetchall()
        
        for symbol, quantity, avg_price, total_cost in positions:
            # Check if position already exists
            existing = await session.execute(text('''
                SELECT position_id FROM live_positions
                WHERE account_id = :account_id AND symbol = :symbol
            '''), {'account_id': account_id, 'symbol': symbol})
            
            if existing.scalar_one_or_none():
                print(f"⏭️  {symbol}: Position already exists, skipping")
                continue
            
            # Create position
            position_id = str(uuid.uuid4())
            await session.execute(text('''
                INSERT INTO live_positions (
                    position_id,
                    account_id,
                    symbol,
                    strategy,
                    quantity,
                    average_price,
                    current_price,
                    unrealized_pnl,
                    realized_pnl,
                    status,
                    opened_at,
                    created_at,
                    updated_at
                ) VALUES (
                    :position_id,
                    :account_id,
                    :symbol,
                    'MULTI_STRATEGY_ENSEMBLE',
                    :quantity,
                    :avg_price,
                    :avg_price,
                    0,
                    0,
                    'OPEN',
                    NOW(),
                    NOW(),
                    NOW()
                )
            '''), {
                'position_id': position_id,
                'account_id': account_id,
                'symbol': symbol,
                'quantity': int(quantity),
                'avg_price': Decimal(str(avg_price))
            })
            
            print(f"✅ {symbol}: Created position - {int(quantity)} shares @ ${avg_price:.2f}")
        
        await session.commit()
        
        print()
        print("=" * 60)
        print("✅ Positions created successfully!")
        print()
        print("Your system can now track exits for:")
        for symbol, quantity, avg_price, total_cost in positions:
            print(f"  • {symbol}: {int(quantity)} shares @ ${avg_price:.2f}")

asyncio.run(create_positions())

