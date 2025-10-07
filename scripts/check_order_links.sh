#!/bin/bash
# Check how orders are linked in the database
# Shows the relationship between internal trades and Public.com orders

set -e

echo "🔗 Order Linkage Check"
echo "====================="
echo ""

# Get the live-trading-service pod
POD=$(kubectl get pods -n default -l app=live-trading-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
    echo "❌ Error: Live trading service pod not found"
    exit 1
fi

echo "📊 Recent Orders with Linkage Information"
echo "------------------------------------------"
echo ""

# Execute Python script in the pod to query the database
kubectl exec -n default "$POD" -- python3 -c "
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import os

async def check_orders():
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://admin:password@localhost:5432/trading')
    
    # Create async engine
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Query recent trades with all linkage fields
        query = text('''
            SELECT 
                trade_id,
                symbol,
                action,
                quantity,
                status,
                public_order_id,
                price,
                created_at,
                filled_at,
                account_id
            FROM live_trades 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        result = await session.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print('No orders found in database')
            return
        
        print('Recent Orders:')
        print('=' * 120)
        print(f\"{'Trade ID':<38} {'Symbol':<8} {'Action':<6} {'Qty':<5} {'Status':<12} {'Public Order ID':<38}\")
        print('-' * 120)
        
        for row in rows:
            trade_id = str(row[0])[:36] if row[0] else 'N/A'
            symbol = row[1] or 'N/A'
            action = row[2] or 'N/A'
            quantity = str(row[3]) if row[3] else '0'
            status = row[4] or 'N/A'
            public_order_id = str(row[5])[:36] if row[5] else 'N/A'
            
            print(f\"{trade_id:<38} {symbol:<8} {action:<6} {quantity:<5} {status:<12} {public_order_id:<38}\")
        
        print('-' * 120)
        print()
        
        # Show linkage explanation
        print('🔗 Linkage Explanation:')
        print('-' * 120)
        print('trade_id         = Internal UUID (unique identifier in our database)')
        print('public_order_id  = Order ID from Public.com (links to their system)')
        print('account_id       = Your trading account (links trades to account)')
        print('symbol           = Stock symbol (groups trades by asset)')
        print('status           = Current order status (tracks lifecycle)')
        print()
        
        # Show pending orders specifically
        pending_query = text('''
            SELECT COUNT(*) as pending_count
            FROM live_trades 
            WHERE status = 'PENDING'
        ''')
        
        pending_result = await session.execute(pending_query)
        pending_count = pending_result.scalar()
        
        if pending_count > 0:
            print(f'⚠️  {pending_count} pending orders waiting for Public.com to fill')
            print()
            
            # Show pending order details
            pending_details = text('''
                SELECT 
                    symbol,
                    action,
                    quantity,
                    public_order_id,
                    created_at
                FROM live_trades 
                WHERE status = 'PENDING'
                ORDER BY created_at DESC
            ''')
            
            details_result = await session.execute(pending_details)
            pending_rows = details_result.fetchall()
            
            print('Pending Orders Details:')
            print(f\"{'Symbol':<8} {'Action':<6} {'Qty':<5} {'Public Order ID':<38} {'Created At':<30}\")
            print('-' * 90)
            
            for row in pending_rows:
                symbol = row[0] or 'N/A'
                action = row[1] or 'N/A'
                quantity = str(row[2]) if row[2] else '0'
                public_order_id = str(row[3])[:36] if row[3] else 'N/A'
                created_at = str(row[4]) if row[4] else 'N/A'
                
                print(f\"{symbol:<8} {action:<6} {quantity:<5} {public_order_id:<38} {created_at:<30}\")
            
            print()
        
        # Show filled orders today
        filled_query = text('''
            SELECT COUNT(*) as filled_count
            FROM live_trades 
            WHERE status = 'FILLED' 
            AND filled_at::date = CURRENT_DATE
        ''')
        
        filled_result = await session.execute(filled_query)
        filled_count = filled_result.scalar()
        
        if filled_count > 0:
            print(f'✅ {filled_count} orders filled today')
            print()

# Run the async function
asyncio.run(check_orders())
" 2>/dev/null || echo "❌ Error querying database"

echo ""
echo "📋 How the Linkage Works:"
echo "-------------------------"
echo ""
echo "1. When you submit an order:"
echo "   - System creates a 'trade' record with a unique 'trade_id' (UUID)"
echo "   - Order is sent to Public.com with a 'orderId' (also UUID)"
echo "   - Public.com's 'orderId' is stored as 'public_order_id' in our database"
echo ""
echo "2. This creates the link:"
echo "   - trade_id (internal) ←→ public_order_id (Public.com)"
echo "   - Both are UUIDs, both are unique"
echo ""
echo "3. When syncing:"
echo "   - System queries our database for trades with status = 'PENDING'"
echo "   - For each trade, it queries Public.com using 'public_order_id'"
echo "   - Public.com returns the current status"
echo "   - System updates our database using 'trade_id'"
echo ""
echo "4. The full chain:"
echo "   ┌─────────────────┐"
echo "   │ Our Database    │"
echo "   │  trade_id       │ ←── Our internal ID"
echo "   │  public_order_id│ ←── Links to Public.com"
echo "   │  symbol         │"
echo "   │  status         │ ←── Updated by sync worker"
echo "   └─────────────────┘"
echo "           ↕"
echo "   ┌─────────────────┐"
echo "   │ Public.com      │"
echo "   │  orderId        │ ←── Same as our public_order_id"
echo "   │  status         │ ←── Source of truth for order status"
echo "   │  filledPrice    │ ←── Copied to our database when filled"
echo "   └─────────────────┘"
echo ""
echo "To manually check links:"
echo "  kubectl logs -n default -l app=order-sync-worker --tail=20"
echo ""

