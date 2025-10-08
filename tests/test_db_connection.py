#!/usr/bin/env python3
"""Test database connection and table creation"""

import asyncio
import os
import sys
sys.path.append('.')

async def test_db_connection():
    """Test database connection and table creation"""
    try:
        from src.services.database import initialize_database
        
        # Get database URL from environment or use default
        database_url = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")
        
        print(f"Connecting to database: {database_url.split('@')[-1]}")
        db_manager = await initialize_database(database_url)
        print("✅ Database connection successful")
        
        # Test a simple query
        result = await db_manager.fetchrow("SELECT 1 as test")
        print(f"✅ Simple query test: {result}")
        
        # Test table creation
        print("Testing table creation...")
        await db_manager.execute("""
            CREATE TABLE IF NOT EXISTS test_orders (
                order_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        print("✅ Test table creation successful")
        
        # Test insert
        await db_manager.execute("""
            INSERT INTO test_orders (order_id, user_id, created_at) 
            VALUES ($1, $2, $3)
        """, "test_001", "test_user", "2025-01-01 00:00:00")
        print("✅ Test insert successful")
        
        # Test select
        result = await db_manager.fetchrow("SELECT * FROM test_orders WHERE order_id = $1", "test_001")
        print(f"✅ Test select successful: {result}")
        
        # Cleanup
        await db_manager.execute("DROP TABLE test_orders")
        print("✅ Test cleanup successful")
        
        await db_manager.close()
        print("✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_connection())
