#!/usr/bin/env python3
"""
Emergency Position Exit Script
==============================
This script immediately exits any positions that exceed the loss limit (8%).
Use this for emergency situations where positions need to be closed immediately.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmergencyExitService:
    """Emergency exit service for positions exceeding limits"""
    
    def __init__(self):
        # Database connection
        self.db_url = "postgresql+asyncpg://trading_user:trading_password@localhost:5432/trading_db"
        self.engine = None
        self.session_maker = None
        self.stop_loss_threshold = -0.08  # 8% loss
        
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_maker = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("✅ Database connection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def find_positions_exceeding_limits(self):
        """Find all positions exceeding loss limits"""
        async with self.session_maker() as session:
            try:
                query = text("""
                    SELECT 
                        p.position_id,
                        p.account_id,
                        p.symbol,
                        p.strategy,
                        p.entry_price,
                        p.current_price,
                        p.quantity,
                        p.unrealized_pnl,
                        p.unrealized_pnl_pct,
                        p.created_at,
                        a.public_account_id
                    FROM live_positions p
                    LEFT JOIN live_trading_accounts a ON p.account_id = a.account_id
                    WHERE p.status = 'OPEN'
                        AND p.unrealized_pnl_pct <= :loss_threshold
                    ORDER BY p.unrealized_pnl_pct ASC
                """)
                
                result = await session.execute(query, {
                    'loss_threshold': self.stop_loss_threshold
                })
                positions = result.fetchall()
                
                return positions
                
            except Exception as e:
                logger.error(f"❌ Error finding positions: {e}")
                return []
    
    async def create_exit_trade(self, position, session: AsyncSession):
        """Create exit trade for a position"""
        try:
            position_id, account_id, symbol, strategy, entry_price, current_price, quantity, unrealized_pnl, unrealized_pnl_pct, created_at, public_account_id = position
            
            # Create exit trade record
            trade_query = text("""
                INSERT INTO live_trades (
                    account_id,
                    symbol,
                    strategy,
                    action,
                    quantity,
                    premium,
                    total_amount,
                    status,
                    exit_reason,
                    notes,
                    created_at
                ) VALUES (
                    :account_id,
                    :symbol,
                    :strategy,
                    'SELL',
                    :quantity,
                    :premium,
                    :total_amount,
                    'PENDING',
                    'emergency_stop_loss',
                    :notes,
                    NOW()
                )
                RETURNING trade_id
            """)
            
            notes = f"Emergency exit: {unrealized_pnl_pct:.1%} loss exceeded {self.stop_loss_threshold:.1%} threshold"
            
            result = await session.execute(trade_query, {
                'account_id': account_id,
                'symbol': symbol,
                'strategy': strategy,
                'quantity': quantity,
                'premium': current_price,
                'total_amount': current_price * quantity,
                'notes': notes
            })
            
            trade_id = result.fetchone()[0]
            
            # Update position status
            position_query = text("""
                UPDATE live_positions
                SET 
                    status = 'CLOSED',
                    exit_price = :exit_price,
                    exit_time = NOW(),
                    exit_reason = 'emergency_stop_loss',
                    updated_at = NOW()
                WHERE position_id = :position_id
            """)
            
            await session.execute(position_query, {
                'position_id': position_id,
                'exit_price': current_price
            })
            
            await session.commit()
            
            logger.info(f"✅ Created emergency exit for {symbol}:")
            logger.info(f"   Trade ID: {trade_id}")
            logger.info(f"   Position ID: {position_id}")
            logger.info(f"   Loss: {unrealized_pnl_pct:.1%} (${unrealized_pnl:+,.2f})")
            logger.info(f"   Exit Price: ${current_price:.2f}")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"❌ Error creating exit trade: {e}")
            await session.rollback()
            raise
    
    async def execute_emergency_exits(self, dry_run=True):
        """Execute emergency exits for all positions exceeding limits"""
        logger.info("🚨 EMERGENCY EXIT EXECUTION")
        logger.info("="*60)
        
        # Find positions
        positions = await self.find_positions_exceeding_limits()
        
        if not positions:
            logger.info("✅ No positions exceed loss limits")
            return []
        
        logger.info(f"\n⚠️  Found {len(positions)} positions exceeding {self.stop_loss_threshold:.1%} loss:")
        logger.info("")
        
        for i, pos in enumerate(positions, 1):
            position_id, account_id, symbol, strategy, entry_price, current_price, quantity, unrealized_pnl, unrealized_pnl_pct, created_at, public_account_id = pos
            
            logger.info(f"{i}. {symbol} ({strategy})")
            logger.info(f"   Loss: {unrealized_pnl_pct:.1%} (${unrealized_pnl:+,.2f})")
            logger.info(f"   Entry: ${entry_price:.2f} → Current: ${current_price:.2f}")
            logger.info(f"   Quantity: {quantity}")
            logger.info(f"   Held since: {created_at}")
            logger.info("")
        
        if dry_run:
            logger.warning("🔍 DRY RUN MODE - No trades will be executed")
            logger.warning("   Run with --execute flag to actually close positions")
            return []
        
        # Confirm execution
        logger.warning("\n⚠️  WARNING: This will create SELL orders for all positions above!")
        response = input("\nType 'CONFIRM' to proceed with emergency exits: ")
        
        if response.strip() != 'CONFIRM':
            logger.info("❌ Emergency exit cancelled")
            return []
        
        # Execute exits
        logger.info("\n🚀 Executing emergency exits...")
        executed_trades = []
        
        async with self.session_maker() as session:
            for pos in positions:
                try:
                    trade_id = await self.create_exit_trade(pos, session)
                    executed_trades.append({
                        'trade_id': trade_id,
                        'symbol': pos[2],
                        'loss_pct': pos[8],
                        'loss_amount': pos[7]
                    })
                except Exception as e:
                    logger.error(f"❌ Failed to exit {pos[2]}: {e}")
        
        return executed_trades
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Database connection closed")


async def main():
    """Main function"""
    # Check for execute flag
    dry_run = '--execute' not in sys.argv
    
    logger.info("="*60)
    logger.info("EMERGENCY POSITION EXIT")
    logger.info("="*60)
    
    if dry_run:
        logger.info("\n🔍 Running in DRY RUN mode")
        logger.info("   Use --execute flag to actually close positions")
    else:
        logger.warning("\n⚠️  LIVE EXECUTION MODE")
        logger.warning("   Positions will be ACTUALLY closed!")
    
    service = EmergencyExitService()
    
    try:
        await service.initialize()
        
        executed_trades = await service.execute_emergency_exits(dry_run=dry_run)
        
        if executed_trades and not dry_run:
            logger.info("\n" + "="*60)
            logger.info("EMERGENCY EXITS EXECUTED")
            logger.info("="*60)
            logger.info(f"\n✅ Successfully created {len(executed_trades)} exit trades:")
            
            total_loss = sum(t['loss_amount'] for t in executed_trades)
            
            for trade in executed_trades:
                logger.info(f"   {trade['symbol']}: Trade ID {trade['trade_id']}")
                logger.info(f"      Loss: {trade['loss_pct']:.1%} (${trade['loss_amount']:+,.2f})")
            
            logger.info(f"\n   Total Losses Stopped: ${total_loss:+,.2f}")
            logger.info("\n⚠️  NOTE: Orders are PENDING - they need to be submitted to Public.com")
            logger.info("   Check the live trading dashboard for order status")
        
    except Exception as e:
        logger.error(f"\n❌ Error during emergency exit: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())









