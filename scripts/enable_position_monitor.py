#!/usr/bin/env python3
"""
Enable Automatic Position Monitoring
====================================
This script enables the position monitor service to automatically
check positions and trigger exits when stop-loss or other exit
conditions are met.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def enable_position_monitor():
    """Enable and start the position monitor service"""
    logger.info("="*60)
    logger.info("ENABLING POSITION MONITOR SERVICE")
    logger.info("="*60)
    
    try:
        # Import the position monitor
        from src.services.live_trading.position_monitor import position_monitor
        
        logger.info("\n✅ Position Monitor Service Loaded")
        logger.info(f"   Monitoring interval: {position_monitor.monitoring_interval} seconds")
        logger.info(f"   Exit Configuration:")
        logger.info(f"     - Stop Loss: {position_monitor.exit_config['stop_loss_pct']:.1%}")
        logger.info(f"     - Profit Target: {position_monitor.exit_config['profit_target_pct']:.1%}")
        logger.info(f"     - Max Holding Days: {position_monitor.exit_config['max_holding_days']}")
        logger.info(f"     - Min Holding Hours: {position_monitor.exit_config['min_holding_hours']}")
        
        # Start monitoring
        logger.info("\n🚀 Starting position monitoring...")
        logger.info("   Press Ctrl+C to stop")
        
        # Run the monitor
        await position_monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("\n\n⏸️  Stopping position monitor...")
        await position_monitor.stop_monitoring()
        logger.info("✅ Position monitor stopped")
    except Exception as e:
        logger.error(f"\n❌ Error enabling position monitor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


async def main():
    """Main function"""
    logger.info("\n📋 This script will enable continuous position monitoring")
    logger.info("   Positions will be checked every 5 minutes for exit conditions:")
    logger.info("   - Stop loss: 8% loss")
    logger.info("   - Profit target: 15% gain")
    logger.info("   - Max holding: 30 days")
    logger.info("   - Min holding: 4 hours")
    
    logger.info("\n⚠️  NOTE: For production use, this should run as a")
    logger.info("   background service or Kubernetes cron job.")
    
    logger.info("\n" + "="*60)
    input("Press Enter to start monitoring (Ctrl+C to stop)...")
    
    await enable_position_monitor()


if __name__ == "__main__":
    asyncio.run(main())









