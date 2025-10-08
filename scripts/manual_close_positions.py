#!/usr/bin/env python3
"""
Manual Position Closer

Manually closes positions when the sync workers can't detect sold positions.
Useful when positions are sold outside market hours or when Public.com API fails.
"""

import asyncio
import asyncpg
import sys
from datetime import datetime

# Database connection
DB_HOST = "localhost"
DB_PORT = 5434  # Local port-forward to postgres
DB_USER = "trading_user"
DB_PASS = "trading_password"
DB_NAME = "trading_db"


async def close_position(symbol: str, account_id: str):
    """Close a position manually by marking it as CLOSED."""
    
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    
    try:
        # Get the current position
        position = await conn.fetchrow(
            """
            SELECT position_id, symbol, quantity, average_price, status
            FROM live_trading_positions
            WHERE symbol = $1 AND account_id = $2 AND status = 'OPEN'
            """,
            symbol, account_id
        )
        
        if not position:
            print(f"❌ No open position found for {symbol}")
            return False
        
        print(f"\n📊 Current Position:")
        print(f"   Symbol: {position['symbol']}")
        print(f"   Quantity: {position['quantity']}")
        print(f"   Avg Price: ${position['average_price']:.2f}")
        print(f"   Status: {position['status']}")
        
        # Ask for confirmation
        confirm = input(f"\n❓ Close this position? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return False
        
        # Get current price (optional, or use average price)
        close_price_input = input(f"💰 Enter close price (press Enter to use avg price ${position['average_price']:.2f}): ")
        if close_price_input.strip():
            close_price = float(close_price_input)
        else:
            close_price = position['average_price']
        
        # Calculate P&L
        quantity = position['quantity']
        entry_value = position['average_price'] * quantity
        exit_value = close_price * quantity
        realized_pnl = exit_value - entry_value
        
        print(f"\n💵 Position P&L:")
        print(f"   Entry: ${entry_value:.2f} ({quantity} @ ${position['average_price']:.2f})")
        print(f"   Exit:  ${exit_value:.2f} ({quantity} @ ${close_price:.2f})")
        print(f"   P&L:   ${realized_pnl:+.2f}")
        
        # Update the position
        await conn.execute(
            """
            UPDATE live_trading_positions
            SET status = 'CLOSED',
                current_price = $1,
                realized_pnl = $2,
                total_pnl = $2,
                closed_at = $3,
                updated_at = $3
            WHERE position_id = $4
            """,
            close_price,
            realized_pnl,
            datetime.utcnow(),
            position['position_id']
        )
        
        print(f"\n✅ Position {symbol} closed successfully!")
        print(f"   Position ID: {position['position_id']}")
        print(f"   Realized P&L: ${realized_pnl:+.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error closing position: {e}")
        return False
    finally:
        await conn.close()


async def main():
    """Main function."""
    
    account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
    
    print("🔄 Manual Position Closer")
    print("=" * 50)
    
    # Get symbols to close
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
    else:
        symbols_input = input("Enter symbol(s) to close (comma-separated): ")
        symbols = [s.strip().upper() for s in symbols_input.split(',')]
    
    print(f"\n📋 Positions to close: {', '.join(symbols)}")
    
    # Close each position
    for symbol in symbols:
        await close_position(symbol, account_id)
        print()


if __name__ == "__main__":
    asyncio.run(main())

