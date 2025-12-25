#!/usr/bin/env python3
"""
Manual Options Exit Script
Directly submits exit orders to Public.com for options marked PENDING_CLOSE
"""

import sys
import asyncio
sys.path.insert(0, '/app')

from src.services.live_trading.public_api_client import PublicAPIClient, PublicAPIConfig
from src.services.live_trading.database import async_session_maker
from src.services.live_trading.models import LivePosition, PositionStatus
from sqlalchemy import select, and_
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACCOUNT_ID = "19c25392-8b61-4b71-a344-0eb04d275528"
PUBLIC_ACCOUNT_ID = "f86f1b83-b8ba-46dd-88e0-d1a7b41bc41d"  # Your Public.com account

async def parse_occ_symbol(symbol: str):
    """Parse OCC option symbol"""
    symbol_clean = symbol.replace("-OPTION", "")
    
    # Find the 6-digit date followed by C or P
    for i in range(len(symbol_clean) - 6):
        if symbol_clean[i:i+6].isdigit():
            if i + 6 < len(symbol_clean) and symbol_clean[i+6] in ['C', 'P']:
                date_str = symbol_clean[i:i+6]
                underlying = symbol_clean[:i]
                option_type = "CALL" if symbol_clean[i+6] == 'C' else "PUT"
                strike_str = symbol_clean[i+7:]
                
                year = 2000 + int(date_str[0:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                strike = float(strike_str) / 1000.0
                
                return {
                    "underlying": underlying,
                    "type": option_type,
                    "strike": strike,
                    "expiration": f"{year}-{month:02d}-{day:02d}",
                    "occ_symbol": symbol_clean
                }
    
    return None

async def submit_exit_orders():
    """Submit exit orders for PENDING_CLOSE positions"""
    
    # Get positions
    async with async_session_maker() as session:
        stmt = select(LivePosition).where(
            and_(
                LivePosition.account_id == ACCOUNT_ID,
                LivePosition.status == 'PENDING_CLOSE'
            )
        )
        result = await session.execute(stmt)
        positions = result.scalars().all()
        
        logger.info(f"Found {len(positions)} positions marked for exit")
        
        if not positions:
            logger.info("No positions to exit")
            return
        
        # Initialize Public API client
        client = PublicAPIClient()
        
        for pos in positions:
            logger.info(f"\n📤 Exiting {pos.symbol}")
            logger.info(f"   Quantity: {pos.quantity}")
            logger.info(f"   Entry: ${pos.average_price}, Current: ${pos.current_price}")
            logger.info(f"   P&L: ${pos.unrealized_pnl}")
            
            # Parse option details
            option_details = await parse_occ_symbol(pos.symbol)
            if not option_details:
                logger.error(f"   ❌ Could not parse option symbol")
                continue
            
            logger.info(f"   Option: {option_details['underlying']} {option_details['type']} ${option_details['strike']} exp {option_details['expiration']}")
            
            # Submit to Public.com
            try:
                order_data = {
                    "symbol": option_details['underlying'],
                    "side": "sell",
                    "quantity": pos.quantity,
                    "type": "market",
                    "time_in_force": "day"
                }
                
                response = await client.submit_order(PUBLIC_ACCOUNT_ID, order_data)
                logger.info(f"   ✅ Order submitted: {response}")
                
            except Exception as e:
                logger.error(f"   ❌ Failed to submit: {e}")

if __name__ == "__main__":
    asyncio.run(submit_exit_orders())






