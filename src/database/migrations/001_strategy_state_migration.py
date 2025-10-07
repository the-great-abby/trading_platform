#!/usr/bin/env python3
"""
Strategy State Database Migration
Creates tables for strategy state management
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.database import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def run_migration():
    """Run the strategy state migration"""
    logger.info("🚀 Running strategy state migration...")
    
    try:
        async with engine.begin() as conn:
            # Read and execute schema
            schema_path = Path(__file__).parent / "strategy_state_schema.sql"
            schema_sql = schema_path.read_text()
            
            await conn.execute(text(schema_sql))
            
        logger.info("✅ Strategy state migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Strategy state migration failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(run_migration())
