#!/usr/bin/env python3
"""
Migrate Symbols to TimescaleDB External
Moves popular_symbols to the main trading database (TimescaleDB external)
"""

import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_symbols_to_timescale():
    """Migrate popular_symbols to TimescaleDB external database"""
    
    # Source: Old TimescaleDB
    source_config = {
        "host": "localhost",
        "port": 11140,
        "database": "trading_bot",
        "user": "trading_user",
        "password": "trading_pass"
    }
    
    # Target: TimescaleDB External (main trading database)
    target_config = {
        "host": "localhost",
        "port": 11150,
        "database": "trading",
        "user": "postgres",
        "password": "postgres"
    }
    
    try:
        # Connect to source database
        logger.info("🔍 Connecting to source database...")
        source_conn = psycopg2.connect(**source_config)
        
        # Connect to target database
        logger.info("🔍 Connecting to TimescaleDB external...")
        target_conn = psycopg2.connect(**target_config)
        
        # Get data from source
        with source_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM popular_symbols")
            source_count = cur.fetchone()[0]
            logger.info(f"📊 Source database has {source_count} symbols")
            
            cur.execute("SELECT * FROM popular_symbols ORDER BY priority")
            symbols = cur.fetchall()
            logger.info(f"📋 Retrieved {len(symbols)} symbols from source")
        
        # Create table in target if it doesn't exist
        with target_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS popular_symbols (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    priority INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clear existing data
            cur.execute("DELETE FROM popular_symbols")
            logger.info("🧹 Cleared existing data from target table")
            
            # Insert all symbols
            for symbol in symbols:
                cur.execute("""
                    INSERT INTO popular_symbols (symbol, description, category, priority, active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, symbol[1:])  # Skip the id column
            
            target_conn.commit()
            logger.info(f"✅ Successfully migrated {len(symbols)} symbols to TimescaleDB external")
        
        # Verify migration
        with target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM popular_symbols")
            target_count = cur.fetchone()[0]
            logger.info(f"🔍 TimescaleDB external now has {target_count} symbols")
            
            if source_count == target_count:
                logger.info("🎉 Migration successful! All symbols restored to TimescaleDB external.")
            else:
                logger.warning(f"⚠️ Migration incomplete: {source_count} source vs {target_count} target")
        
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("🚀 Starting symbols migration to TimescaleDB external...")
    migrate_symbols_to_timescale()
    logger.info("✨ Migration complete!")
