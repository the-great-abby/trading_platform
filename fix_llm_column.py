#!/usr/bin/env python3
"""
Script to fix the llm_approved column size in the backtest_trades table
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def main():
    # Get database connection details
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('DATABASE_URL not found')
        exit(1)

    # Parse connection string
    # postgresql://user:pass@host:port/dbname
    parts = db_url.replace('postgresql://', '').split('@')
    user_pass = parts[0].split(':')
    host_port_db = parts[1].split('/')
    host_port = host_port_db[0].split(':')

    user = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    database = host_port_db[1]

    print(f'Connecting to {host}:{port}/{database} as {user}')

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create cursor
        cur = conn.cursor()
        
        # Check current column type
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'backtest_trades' AND column_name = 'llm_approved'
        """)
        
        result = cur.fetchone()
        if result:
            print(f'Current llm_approved column: {result}')
            
            # Update column size
            cur.execute('ALTER TABLE backtest_trades ALTER COLUMN llm_approved TYPE VARCHAR(10)')
            print('✅ Successfully updated llm_approved column size to VARCHAR(10)')
            
            # Verify the change
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'backtest_trades' AND column_name = 'llm_approved'
            """)
            
            result = cur.fetchone()
            print(f'Updated llm_approved column: {result}')
        else:
            print('❌ llm_approved column not found')
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        exit(1)

if __name__ == "__main__":
    main() 