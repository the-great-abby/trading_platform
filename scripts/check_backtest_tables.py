#!/usr/bin/env python3
"""
Check if backtest tables exist in the database
"""

from sqlalchemy import create_engine, text

def check_backtest_tables():
    """Check if backtest tables exist"""
    try:
        engine = create_engine('postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot')
        with engine.connect() as conn:
            # Check all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            all_tables = [row[0] for row in result]
            print('All tables found:', all_tables)
            
            # Check backtest tables specifically
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'backtest_%'
            """))
            backtest_tables = [row[0] for row in result]
            print('Backtest tables found:', backtest_tables if backtest_tables else 'None')
            return backtest_tables
    except Exception as e:
        print(f'Error checking tables: {e}')
        return []

if __name__ == "__main__":
    check_backtest_tables() 