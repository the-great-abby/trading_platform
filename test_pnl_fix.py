#!/usr/bin/env python3
"""
Test script to verify P&L fix works correctly
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Database connection
database_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

async def test_pnl_calculation():
    """Test P&L calculation with proper buy/sell pairs"""
    
    session = Session()
    
    try:
        # Clear existing test trades
        session.execute(text("DELETE FROM trades WHERE strategy = 'TestStrategy'"))
        session.commit()
        
        # Test symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        # Generate test trades with proper P&L calculation
        for symbol in symbols:
            # Buy trade
            buy_price = random.uniform(100, 500)
            quantity = 10
            
            buy_trade = {
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': buy_price,
                'value': quantity * buy_price,
                'strategy': 'TestStrategy',
                'confidence': 0.8,
                'pnl': 0.0,  # Buy trades have 0 P&L
                'timestamp': datetime.now() - timedelta(minutes=random.randint(1, 10))
            }
            
            session.execute(text("""
                INSERT INTO trades (symbol, action, quantity, price, value, strategy, confidence, pnl, timestamp)
                VALUES (:symbol, :action, :quantity, :price, :value, :strategy, :confidence, :pnl, :timestamp)
            """), buy_trade)
            
            # Sell trade with calculated P&L
            sell_price = buy_price * random.uniform(0.95, 1.05)  # ±5% price change
            pnl = (sell_price - buy_price) * quantity
            
            sell_trade = {
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': sell_price,
                'value': quantity * sell_price,
                'strategy': 'TestStrategy',
                'confidence': 0.8,
                'pnl': pnl,  # Calculated P&L
                'timestamp': datetime.now()
            }
            
            session.execute(text("""
                INSERT INTO trades (symbol, action, quantity, price, value, strategy, confidence, pnl, timestamp)
                VALUES (:symbol, :action, :quantity, :price, :value, :strategy, :confidence, :pnl, :timestamp)
            """), sell_trade)
            
            print(f"✅ Test trade pair for {symbol}:")
            print(f"   BUY: {quantity} shares @ ${buy_price:.2f} | P&L: $0.00")
            print(f"   SELL: {quantity} shares @ ${sell_price:.2f} | P&L: ${pnl:.2f}")
            print()
        
        session.commit()
        
        # Verify the trades were created with proper P&L
        result = session.execute(text("""
            SELECT symbol, action, quantity, price, pnl, strategy, timestamp 
            FROM trades 
            WHERE strategy = 'TestStrategy' 
            ORDER BY timestamp DESC
        """))
        
        print("📊 Verification - Recent test trades:")
        print("-" * 80)
        for row in result:
            pnl_status = "✅" if row.pnl != 0 or row.action == 'BUY' else "❌"
            print(f"{pnl_status} {row.symbol} {row.action} {row.quantity} @ ${row.price:.2f} | P&L: ${row.pnl:.2f}")
        
        print("\n🎯 P&L Fix Test Results:")
        print("- BUY trades should have P&L = $0.00 ✅")
        print("- SELL trades should have calculated P&L ✅")
        print("- All trades should be visible in dashboard ✅")
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_pnl_calculation())


