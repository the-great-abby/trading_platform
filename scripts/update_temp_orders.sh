#!/bin/bash
# Update TEMP order IDs with real Public.com order IDs
# Use this when you know the real order ID from Public.com

set -e

echo "🔗 Update TEMP Orders with Real Public.com Order IDs"
echo "===================================================="
echo ""

# Get the live-trading-service pod
POD=$(kubectl get pods -n default -l app=live-trading-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
    echo "❌ Error: Live trading service pod not found"
    exit 1
fi

echo "📋 Current TEMP Orders:"
echo ""

kubectl exec -n default "$POD" -- python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import os

async def show_temp_orders():
    db_url = os.getenv('DATABASE_URL')
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        query = text('''
            SELECT 
                trade_id,
                symbol,
                action,
                quantity,
                public_order_id,
                created_at,
                status
            FROM live_trades 
            WHERE public_order_id LIKE 'TEMP_%'
            ORDER BY created_at DESC
        ''')
        
        result = await session.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print('No TEMP orders found')
            return
        
        print('TEMP Orders in Database:')
        print('=' * 100)
        print(f\"{'#':<3} {'Symbol':<8} {'Qty':<5} {'TEMP ID':<30} {'Created At':<25}\")
        print('-' * 100)
        
        for idx, row in enumerate(rows, 1):
            trade_id = str(row[0])
            symbol = row[1]
            quantity = row[3]
            temp_id = row[4]
            created_at = str(row[5])[:19] if row[5] else 'N/A'
            
            print(f\"{idx:<3} {symbol:<8} {quantity:<5} {temp_id:<30} {created_at:<25}\")

asyncio.run(show_temp_orders())
"

echo ""
echo "📝 How to Update:"
echo "-----------------"
echo ""
echo "To update a TEMP order with the real Public.com order ID:"
echo ""
echo "1. Check your Public.com app for the filled orders"
echo "2. Find the order ID (UUID format)"
echo "3. Match it to the symbol and time above"
echo "4. Run the update command below"
echo ""
echo "Update Command Template:"
echo "------------------------"
echo ""
echo 'kubectl exec -n default '"$POD"' -- python3 -c "'
echo '  import asyncio'
echo '  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession'
echo '  from sqlalchemy.orm import sessionmaker'
echo '  from sqlalchemy import text'
echo '  from decimal import Decimal'
echo '  from datetime import datetime'
echo '  import os'
echo '  '
echo '  async def update_order():'
echo '      db_url = os.getenv(\"DATABASE_URL\")'
echo '      engine = create_async_engine(db_url, echo=False)'
echo '      async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)'
echo '      '
echo '      async with async_session() as session:'
echo '          # Update TEMP order with real info'
echo '          query = text(\"\"\"'
echo '              UPDATE live_trades'
echo '              SET '
echo '                  public_order_id = :real_order_id,'
echo '                  status = :status,'
echo '                  price = :price,'
echo '                  filled_quantity = :quantity,'
echo '                  remaining_quantity = 0,'
echo '                  filled_at = :filled_at'
echo '              WHERE public_order_id = :temp_order_id'
echo '          \"\"\")'
echo '          '
echo '          await session.execute(query, {'
echo '              \"temp_order_id\": \"TEMP_1759862702.040189\",  # Replace with TEMP ID from table above'
echo '              \"real_order_id\": \"your-real-uuid-here\",     # Replace with real Public.com order ID'
echo '              \"status\": \"FILLED\",'
echo '              \"price\": 450.25,                              # Replace with actual fill price'
echo '              \"quantity\": 1,'
echo '              \"filled_at\": datetime.utcnow()'
echo '          })'
echo '          await session.commit()'
echo '          print(\"✅ Order updated successfully\")'
echo '  '
echo '  asyncio.run(update_order())'
echo '"'
echo ""
echo "📱 Easier Method - Use the Interactive Script:"
echo "----------------------------------------------"
echo ""
echo "For each TEMP order, you'll be prompted to enter the real order ID:"
echo ""
echo "  chmod +x scripts/link_filled_orders.py"
echo "  kubectl exec -it $POD -- python3 /app/scripts/link_filled_orders.py"
echo ""
echo "Or run it directly in the pod:"
echo ""
echo "  kubectl exec -it $POD -- bash"
echo "  # Then inside the pod:"
echo "  python3 << 'EOF'"
echo "import asyncio"
echo "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession"
echo "from sqlalchemy.orm import sessionmaker"
echo "from sqlalchemy import text"
echo "from decimal import Decimal"
echo "import os"
echo ""
echo "async def quick_update(temp_id, real_id, price):"
echo "    db_url = os.getenv('DATABASE_URL')"
echo "    engine = create_async_engine(db_url, echo=False)"
echo "    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)"
echo "    async with async_session() as session:"
echo "        query = text('''UPDATE live_trades SET "
echo "            public_order_id = :real_id, "
echo "            status = 'FILLED', "
echo "            price = :price, "
echo "            filled_quantity = quantity, "
echo "            remaining_quantity = 0, "
echo "            filled_at = NOW() "
echo "            WHERE public_order_id = :temp_id''')"
echo "        await session.execute(query, {'temp_id': temp_id, 'real_id': real_id, 'price': Decimal(str(price))})"
echo "        await session.commit()"
echo "        print(f'✅ Updated {temp_id} → {real_id}')"
echo ""
echo "# Example usage - UPDATE THESE VALUES:"
echo "asyncio.run(quick_update("
echo "    'TEMP_1759862702.040189',    # TEMP ID from table"
echo "    'abc12345-...',               # Real Public.com order ID"
echo "    450.25                        # Fill price"
echo "))"
echo "EOF"
echo ""

