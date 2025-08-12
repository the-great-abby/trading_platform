#!/usr/bin/env python3
"""
Populate Symbols Database from Central List
This script populates the popular_symbols table with the complete central symbol list
from src/utils/trading_config.py, making the Symbol Management interface the source of truth.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.append('src')

from src.utils.trading_config import get_symbols, OPTIONS_SYMBOLS

# Database connection
DATABASE_URL = "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot"

# Symbol categories and descriptions
SYMBOL_INFO = {
    # Major Tech Stocks
    'AAPL': {'category': 'Technology', 'description': 'Apple Inc.'},
    'MSFT': {'category': 'Technology', 'description': 'Microsoft Corporation'},
    'GOOGL': {'category': 'Technology', 'description': 'Alphabet Inc.'},
    'AMZN': {'category': 'Technology', 'description': 'Amazon.com Inc.'},
    'TSLA': {'category': 'Technology', 'description': 'Tesla Inc.'},
    'NVDA': {'category': 'Technology', 'description': 'NVIDIA Corporation'},
    'META': {'category': 'Technology', 'description': 'Meta Platforms Inc.'},
    'NFLX': {'category': 'Technology', 'description': 'Netflix Inc.'},
    'AMD': {'category': 'Technology', 'description': 'Advanced Micro Devices Inc.'},
    'INTC': {'category': 'Technology', 'description': 'Intel Corporation'},
    
    # Financial Sector
    'JPM': {'category': 'Finance', 'description': 'JPMorgan Chase & Co.'},
    'BAC': {'category': 'Finance', 'description': 'Bank of America Corporation'},
    'WFC': {'category': 'Finance', 'description': 'Wells Fargo & Company'},
    'GS': {'category': 'Finance', 'description': 'Goldman Sachs Group Inc.'},
    'MS': {'category': 'Finance', 'description': 'Morgan Stanley'},
    
    # Healthcare
    'JNJ': {'category': 'Healthcare', 'description': 'Johnson & Johnson'},
    'PFE': {'category': 'Healthcare', 'description': 'Pfizer Inc.'},
    'UNH': {'category': 'Healthcare', 'description': 'UnitedHealth Group Inc.'},
    
    # Consumer Discretionary
    'HD': {'category': 'Consumer Discretionary', 'description': 'Home Depot Inc.'},
    'DIS': {'category': 'Consumer Discretionary', 'description': 'Walt Disney Co.'},
    'V': {'category': 'Finance', 'description': 'Visa Inc.'},
    'MA': {'category': 'Finance', 'description': 'Mastercard Inc.'},
    'PYPL': {'category': 'Technology', 'description': 'PayPal Holdings Inc.'},
    'ADBE': {'category': 'Technology', 'description': 'Adobe Inc.'},
    'CRM': {'category': 'Technology', 'description': 'Salesforce Inc.'},
    'ORCL': {'category': 'Technology', 'description': 'Oracle Corporation'},
    'CSCO': {'category': 'Technology', 'description': 'Cisco Systems Inc.'},
    'QCOM': {'category': 'Technology', 'description': 'Qualcomm Incorporated'},
    'TXN': {'category': 'Technology', 'description': 'Texas Instruments Incorporated'},
    'AVGO': {'category': 'Technology', 'description': 'Broadcom Inc.'},
    
    # ETFs & Indexes
    'SPY': {'category': 'ETF', 'description': 'SPDR S&P 500 ETF Trust'},
    'QQQ': {'category': 'ETF', 'description': 'Invesco QQQ Trust'},
    'VTI': {'category': 'ETF', 'description': 'Vanguard Total Stock Market ETF'},
    'VOO': {'category': 'ETF', 'description': 'Vanguard S&P 500 ETF'},
    'VUG': {'category': 'ETF', 'description': 'Vanguard Growth ETF'},
    'XLK': {'category': 'ETF', 'description': 'Technology Select Sector SPDR Fund'},
    'XLF': {'category': 'ETF', 'description': 'Financial Select Sector SPDR Fund'},
    'XLE': {'category': 'ETF', 'description': 'Energy Select Sector SPDR Fund'},
    'XLV': {'category': 'ETF', 'description': 'Health Care Select Sector SPDR Fund'},
    'XLY': {'category': 'ETF', 'description': 'Consumer Discretionary Select Sector SPDR Fund'},
    'SMCI': {'category': 'Technology', 'description': 'Super Micro Computer Inc.'}
}

async def create_symbols_table(conn: asyncpg.Connection):
    """Create the popular_symbols table if it doesn't exist"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS popular_symbols (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) UNIQUE NOT NULL,
            description TEXT,
            category VARCHAR(50) DEFAULT 'stock',
            priority INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster lookups
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_popular_symbols_symbol ON popular_symbols(symbol)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_popular_symbols_active ON popular_symbols(active)
    """)
    
    print("✅ Symbols table created/verified")

async def populate_symbols(conn: asyncpg.Connection):
    """Populate the symbols table with the central list"""
    central_symbols = get_symbols()
    
    print(f"📊 Found {len(central_symbols)} symbols in central list")
    
    # Clear existing symbols (except TEST)
    await conn.execute("DELETE FROM popular_symbols WHERE symbol != 'TEST'")
    print("🗑️  Cleared existing symbols (kept TEST)")
    
    # Insert all symbols from central list
    for i, symbol in enumerate(central_symbols):
        symbol_info = SYMBOL_INFO.get(symbol, {
            'category': 'stock',
            'description': f'{symbol} Stock'
        })
        
        priority = i + 1  # Priority 1, 2, 3, etc.
        
        await conn.execute("""
            INSERT INTO popular_symbols (symbol, description, category, priority, active)
            VALUES ($1, $2, $3, $4, $5)
        """, symbol, symbol_info['description'], symbol_info['category'], priority, True)
        
        print(f"✅ Added {symbol} ({symbol_info['category']}) - Priority {priority}")
    
    print(f"🎉 Successfully populated {len(central_symbols)} symbols")

async def verify_population(conn: asyncpg.Connection):
    """Verify that all symbols were populated correctly"""
    result = await conn.fetch("SELECT COUNT(*) as count FROM popular_symbols WHERE active = true")
    active_count = result[0]['count']
    
    result = await conn.fetch("SELECT COUNT(*) as total FROM popular_symbols")
    total_count = result[0]['total']
    
    print(f"📊 Verification Results:")
    print(f"   Total symbols: {total_count}")
    print(f"   Active symbols: {active_count}")
    
    # Show sample symbols
    result = await conn.fetch("""
        SELECT symbol, description, category, priority, active 
        FROM popular_symbols 
        ORDER BY priority 
        LIMIT 10
    """)
    
    print(f"\n📋 Sample symbols:")
    for row in result:
        status = "✅" if row['active'] else "❌"
        print(f"   {status} {row['symbol']} - {row['description']} ({row['category']}) - Priority {row['priority']}")

async def main():
    """Main function"""
    print("🚀 Starting Symbol Database Population...")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Create table if needed
        await create_symbols_table(conn)
        
        # Populate symbols
        await populate_symbols(conn)
        
        # Verify population
        await verify_population(conn)
        
        print("\n🎉 Symbol database population completed successfully!")
        print("\n💡 Next steps:")
        print("   1. The Symbol Management interface now controls the central list")
        print("   2. Market data worker will use symbols from this database")
        print("   3. You can add/remove symbols through the web interface")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
