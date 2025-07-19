#!/usr/bin/env python3
"""
Create backtest tables in the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.backtest_results import Base
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def create_backtest_tables():
    """Create backtest tables"""
    try:
        engine = create_engine(
            'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot',
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30
        )
        Base.metadata.create_all(bind=engine)
        print('Backtest tables created successfully!')
        return True
    except Exception as e:
        print(f'Error creating tables: {e}')
        return False

if __name__ == "__main__":
    create_backtest_tables() 