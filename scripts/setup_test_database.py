#!/usr/bin/env python3
"""
Setup test database for CQRS testing
Creates separate test database and tables
"""

import asyncio
import asyncpg
import logging
from src.config.test_config import get_test_database_url, get_test_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_test_database():
    """Setup test database with required tables"""
    
    # Connect to main database to create test database
    main_db_url = get_test_database_url().replace('/trading_bot_test', '/trading_bot')
    
    try:
        # Connect to main database
        conn = await asyncpg.connect(main_db_url)
        
        # Create test database if it doesn't exist
        await conn.execute("""
            CREATE DATABASE trading_bot_test 
            WITH TEMPLATE trading_bot
        """)
        logger.info("✅ Test database created successfully")
        
        await conn.close()
        
        # Connect to test database
        test_conn = await asyncpg.connect(get_test_database_url())
        
        # Create test-specific tables
        await test_conn.execute("""
            -- Test portfolio read model
            CREATE TABLE IF NOT EXISTS test_portfolio_read_model (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                account_id VARCHAR(255) NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                current_price DECIMAL(15,4) NOT NULL,
                unrealized_pnl DECIMAL(15,4) DEFAULT 0,
                realized_pnl DECIMAL(15,4) DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, account_id, symbol)
            );
        """)
        
        await test_conn.execute("""
            -- Test market data read model
            CREATE TABLE IF NOT EXISTS test_market_data_read_model (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) PRIMARY KEY,
                current_price DECIMAL(15,4) NOT NULL,
                price_change DECIMAL(15,4) DEFAULT 0,
                price_change_pct DECIMAL(8,4) DEFAULT 0,
                volume BIGINT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await test_conn.execute("""
            -- Test events table
            CREATE TABLE IF NOT EXISTS test_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(255) UNIQUE NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                aggregate_id VARCHAR(255) NOT NULL,
                event_data JSONB NOT NULL,
                version INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await test_conn.execute("""
            -- Test analytics read model
            CREATE TABLE IF NOT EXISTS test_analytics_read_model (
                id SERIAL PRIMARY KEY,
                strategy_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                total_return DECIMAL(15,4) DEFAULT 0,
                sharpe_ratio DECIMAL(8,4) DEFAULT 0,
                max_drawdown DECIMAL(8,4) DEFAULT 0,
                win_rate DECIMAL(8,4) DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(strategy_id, user_id)
            );
        """)
        
        # Create indexes for performance
        await test_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_portfolio_user_account 
            ON test_portfolio_read_model(user_id, account_id);
        """)
        
        await test_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_events_aggregate 
            ON test_events(aggregate_id, version);
        """)
        
        await test_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_events_type 
            ON test_events(event_type, timestamp);
        """)
        
        logger.info("✅ Test tables created successfully")
        
        await test_conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error setting up test database: {e}")
        raise

async def cleanup_test_database():
    """Clean up test database"""
    try:
        conn = await asyncpg.connect(get_test_database_url())
        
        # Clear test data
        await conn.execute("DELETE FROM test_portfolio_read_model;")
        await conn.execute("DELETE FROM test_market_data_read_model;")
        await conn.execute("DELETE FROM test_events;")
        await conn.execute("DELETE FROM test_analytics_read_model;")
        
        logger.info("✅ Test database cleaned up")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up test database: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        asyncio.run(cleanup_test_database())
    else:
        asyncio.run(setup_test_database())
