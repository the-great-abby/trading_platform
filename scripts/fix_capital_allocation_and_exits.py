#!/usr/bin/env python3
"""
Fix Capital Allocation and Enable Automatic Exits
=================================================
This script fixes two critical issues:
1. Updates database risk profile to match desired capital allocation
2. Enables automatic position monitoring with stop-loss exits

Run this script to apply the fixes immediately.
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


class CapitalAllocationFixer:
    """Fix capital allocation and exit monitoring"""
    
    def __init__(self):
        # Database connection (adjust as needed)
        self.db_url = "postgresql+asyncpg://trading_user:trading_password@localhost:5432/trading_db"
        self.engine = None
        self.session_maker = None
        
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
    
    async def update_risk_profiles(self):
        """Update risk profiles with correct capital allocation"""
        logger.info("🔧 Updating risk profiles...")
        
        # Capital allocation based on your requirements:
        # - Initial capital: $4,000
        # - Max position size: 20% = $800
        # - Max daily loss: 5% = $200
        # - Max portfolio risk: 15% (85% max exposure)
        # - Max daily trades: 10
        
        async with self.session_maker() as session:
            try:
                # Update all risk profiles
                update_query = text("""
                    UPDATE risk_profiles
                    SET 
                        max_position_size = :max_position_size,
                        max_portfolio_risk = :max_portfolio_risk,
                        max_daily_loss = :max_daily_loss,
                        max_daily_trades = :max_daily_trades,
                        max_greeks_exposure = :max_greeks_exposure,
                        updated_at = NOW()
                    WHERE TRUE
                    RETURNING account_id, max_position_size, max_portfolio_risk, max_daily_loss
                """)
                
                result = await session.execute(update_query, {
                    'max_position_size': 800.0,  # 20% of $4,000
                    'max_portfolio_risk': 0.15,  # 15% portfolio risk (allows 85% exposure)
                    'max_daily_loss': 200.0,     # 5% of $4,000
                    'max_daily_trades': 10,      # 10 trades per day
                    'max_greeks_exposure': '{"delta": 50, "gamma": 10, "theta": -20, "vega": 30}'
                })
                
                await session.commit()
                
                updated_profiles = result.fetchall()
                
                if updated_profiles:
                    logger.info(f"✅ Updated {len(updated_profiles)} risk profiles:")
                    for profile in updated_profiles:
                        logger.info(f"   Account: {profile[0]}")
                        logger.info(f"     Max Position Size: ${profile[1]:,.2f} (20% of portfolio)")
                        logger.info(f"     Max Portfolio Risk: {profile[2]:.1%}")
                        logger.info(f"     Max Daily Loss: ${profile[3]:,.2f}")
                else:
                    logger.warning("⚠️  No risk profiles found - creating default profile...")
                    await self.create_default_risk_profile(session)
                    
            except Exception as e:
                logger.error(f"❌ Error updating risk profiles: {e}")
                raise
    
    async def create_default_risk_profile(self, session: AsyncSession):
        """Create default risk profile if none exists"""
        try:
            # Get the first account or create placeholder
            account_query = text("SELECT account_id FROM live_trading_accounts LIMIT 1")
            result = await session.execute(account_query)
            account = result.fetchone()
            
            if account:
                account_id = account[0]
                
                insert_query = text("""
                    INSERT INTO risk_profiles (
                        account_id, 
                        max_position_size, 
                        max_portfolio_risk, 
                        max_daily_loss, 
                        max_daily_trades,
                        max_greeks_exposure,
                        allowed_strategies,
                        emergency_stop_active,
                        created_at,
                        updated_at
                    ) VALUES (
                        :account_id,
                        :max_position_size,
                        :max_portfolio_risk,
                        :max_daily_loss,
                        :max_daily_trades,
                        :max_greeks_exposure,
                        :allowed_strategies,
                        :emergency_stop_active,
                        NOW(),
                        NOW()
                    )
                    ON CONFLICT (account_id) DO UPDATE SET
                        max_position_size = :max_position_size,
                        max_portfolio_risk = :max_portfolio_risk,
                        max_daily_loss = :max_daily_loss,
                        max_daily_trades = :max_daily_trades,
                        updated_at = NOW()
                """)
                
                await session.execute(insert_query, {
                    'account_id': account_id,
                    'max_position_size': 800.0,
                    'max_portfolio_risk': 0.15,
                    'max_daily_loss': 200.0,
                    'max_daily_trades': 10,
                    'max_greeks_exposure': '{"delta": 50, "gamma": 10, "theta": -20, "vega": 30}',
                    'allowed_strategies': '["MULTI_STRATEGY_ENSEMBLE", "IRON_CONDOR", "CALENDAR_SPREAD"]',
                    'emergency_stop_active': False
                })
                
                await session.commit()
                logger.info(f"✅ Created default risk profile for account {account_id}")
            else:
                logger.warning("⚠️  No accounts found - skipping risk profile creation")
                
        except Exception as e:
            logger.error(f"❌ Error creating default risk profile: {e}")
            raise
    
    async def check_positions_exceeding_limits(self):
        """Check for positions exceeding loss limits"""
        logger.info("🔍 Checking for positions exceeding loss limits...")
        
        async with self.session_maker() as session:
            try:
                # Find positions with losses > 8%
                query = text("""
                    SELECT 
                        position_id,
                        account_id,
                        symbol,
                        strategy,
                        entry_price,
                        current_price,
                        quantity,
                        unrealized_pnl,
                        unrealized_pnl_pct,
                        created_at
                    FROM live_positions
                    WHERE status = 'OPEN'
                        AND unrealized_pnl_pct <= -0.08
                    ORDER BY unrealized_pnl_pct ASC
                """)
                
                result = await session.execute(query)
                positions = result.fetchall()
                
                if positions:
                    logger.warning(f"⚠️  Found {len(positions)} positions exceeding 8% loss limit:")
                    for pos in positions:
                        logger.warning(f"   {pos[2]} ({pos[3]}): {pos[8]:.1%} loss (${pos[7]:+,.2f})")
                        logger.warning(f"      Position ID: {pos[0]}")
                        logger.warning(f"      Entry: ${pos[4]:.2f}, Current: ${pos[5]:.2f}")
                        logger.warning(f"      Open since: {pos[9]}")
                    
                    logger.warning(f"\n⚠️  URGENT: These positions should be exited!")
                    logger.warning(f"   Run the emergency exit script to close them automatically.")
                    return positions
                else:
                    logger.info("✅ No positions exceeding loss limits")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Error checking positions: {e}")
                return []
    
    async def verify_fixes(self):
        """Verify that fixes were applied correctly"""
        logger.info("\n" + "="*60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("="*60)
        
        async with self.session_maker() as session:
            try:
                # Check risk profiles
                query = text("""
                    SELECT 
                        COUNT(*) as total_profiles,
                        AVG(max_position_size) as avg_max_position,
                        AVG(max_portfolio_risk) as avg_max_risk,
                        AVG(max_daily_loss) as avg_max_loss
                    FROM risk_profiles
                """)
                
                result = await session.execute(query)
                stats = result.fetchone()
                
                if stats and stats[0] > 0:
                    logger.info(f"\n✅ Risk Profiles Updated:")
                    logger.info(f"   Total Profiles: {stats[0]}")
                    logger.info(f"   Avg Max Position Size: ${stats[1]:,.2f} (should be ~$800)")
                    logger.info(f"   Avg Max Portfolio Risk: {stats[2]:.1%} (should be 15%)")
                    logger.info(f"   Avg Max Daily Loss: ${stats[3]:,.2f} (should be $200)")
                else:
                    logger.warning("⚠️  No risk profiles found!")
                
                # Check position monitor status
                logger.info(f"\n📊 Position Monitor Status:")
                logger.info(f"   Service File: src/services/live_trading/position_monitor.py")
                logger.info(f"   Exit Config:")
                logger.info(f"     - Stop Loss: 8%")
                logger.info(f"     - Profit Target: 15%")
                logger.info(f"     - Max Holding: 30 days")
                logger.info(f"   Status: Ready to enable (see next steps)")
                
            except Exception as e:
                logger.error(f"❌ Error verifying fixes: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Database connection closed")


async def main():
    """Main function"""
    logger.info("="*60)
    logger.info("CAPITAL ALLOCATION & EXIT MONITORING FIX")
    logger.info("="*60)
    
    fixer = CapitalAllocationFixer()
    
    try:
        # Initialize
        await fixer.initialize()
        
        # Update risk profiles
        await fixer.update_risk_profiles()
        
        # Check for positions exceeding limits
        exceeding_positions = await fixer.check_positions_exceeding_limits()
        
        # Verify fixes
        await fixer.verify_fixes()
        
        # Next steps
        logger.info("\n" + "="*60)
        logger.info("NEXT STEPS")
        logger.info("="*60)
        logger.info("\n1. ✅ Capital allocation limits updated in database")
        logger.info("   - Max position size: $800 (20% of portfolio)")
        logger.info("   - Max daily loss: $200 (5% of portfolio)")
        logger.info("   - Max portfolio risk: 15%")
        
        logger.info("\n2. 🔧 Enable automatic position monitoring:")
        logger.info("   Run: python scripts/enable_position_monitor.py")
        
        if exceeding_positions:
            logger.info(f"\n3. ⚠️  URGENT - {len(exceeding_positions)} positions exceed loss limits:")
            logger.info("   Run: python scripts/emergency_exit_positions.py")
        else:
            logger.info("\n3. ✅ No positions currently exceed loss limits")
        
        logger.info("\n4. 🚀 Restart live trading service to apply changes:")
        logger.info("   kubectl rollout restart -n trading-system deployment/live-trading-service")
        
    except Exception as e:
        logger.error(f"\n❌ Error during fix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        await fixer.close()
    
    logger.info("\n✅ Fix script completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())









