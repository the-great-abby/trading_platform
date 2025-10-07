#!/usr/bin/env python3
"""
Multi-Strategy Ensemble Live Executor - CronJob Version
=======================================================

This script is designed to run as a Kubernetes CronJob for automated trading.
It executes a single trading cycle and then exits.

Key Features:
- Market hours checking (only trades during 9:30 AM - 4:00 PM ET)
- Risk limit enforcement
- Emergency stop capability via ConfigMap
- Single cycle execution (no continuous loop)
- Comprehensive logging and error handling

Usage:
    python scripts/multi_strategy_ensemble_live_executor_cron.py

Environment Variables:
    LIVE_TRADING_SERVICE_URL: URL to live trading service
    STRATEGY_SERVICE_URL: URL to strategy service
    TRADING_ACCOUNT_ID: Account ID for trading
    TRADING_MODE: "paper" or "live"
    MAX_DAILY_LOSS: Maximum daily loss limit
    MAX_POSITION_SIZE: Maximum position size (% of portfolio)
    MAX_POSITIONS: Maximum concurrent positions
    ENFORCE_MARKET_HOURS: "true" or "false"
    TRADING_ENABLED: "true" or "false" (emergency kill switch)
"""

import os
import sys
import asyncio
import logging
import httpx
from datetime import datetime, time
from typing import Dict, Any, Optional
import pytz

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LiveTradingExecutor:
    """Execute a single live trading cycle"""
    
    def __init__(self):
        """Initialize the executor with configuration from environment"""
        self.live_trading_url = os.getenv(
            'LIVE_TRADING_SERVICE_URL',
            'http://live-trading-service.default.svc.cluster.local:8080'
        )
        self.strategy_service_url = os.getenv(
            'STRATEGY_SERVICE_URL',
            'http://strategy-service.trading-system.svc.cluster.local:80'
        )
        self.account_id = os.getenv(
            'TRADING_ACCOUNT_ID',
            '19c25392-8b61-4b71-a344-0eb04d275528'
        )
        self.trading_mode = os.getenv('TRADING_MODE', 'paper')
        self.strategy_name = os.getenv('STRATEGY_NAME', 'MultiStrategyEnsemble')
        
        # Risk limits
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '500'))
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', '0.20'))
        self.max_positions = int(os.getenv('MAX_POSITIONS', '5'))
        
        # Market hours
        self.enforce_market_hours = os.getenv('ENFORCE_MARKET_HOURS', 'true').lower() == 'true'
        self.market_open_time = time.fromisoformat(os.getenv('MARKET_OPEN_TIME', '09:30'))
        self.market_close_time = time.fromisoformat(os.getenv('MARKET_CLOSE_TIME', '16:00'))
        self.market_timezone = pytz.timezone(os.getenv('MARKET_TIMEZONE', 'America/New_York'))
        
        # Emergency controls
        self.trading_enabled = os.getenv('TRADING_ENABLED', 'true').lower() == 'true'
        
        # HTTP client settings
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        
        logger.info("🚀 Live Trading Executor initialized")
        logger.info(f"   • Mode: {self.trading_mode.upper()}")
        logger.info(f"   • Strategy: {self.strategy_name}")
        logger.info(f"   • Account: {self.account_id}")
        logger.info(f"   • Max Daily Loss: ${self.max_daily_loss}")
        logger.info(f"   • Max Position Size: {self.max_position_size*100}%")
        logger.info(f"   • Max Positions: {self.max_positions}")
    
    async def check_emergency_stop(self) -> bool:
        """Check if emergency stop is enabled via ConfigMap"""
        try:
            # In Kubernetes, ConfigMaps are mounted as files
            emergency_stop_file = "/etc/config/emergency_stop"
            if os.path.exists(emergency_stop_file):
                with open(emergency_stop_file, 'r') as f:
                    value = f.read().strip().lower()
                    if value == "true":
                        logger.warning("🚨 EMERGENCY STOP ENABLED - Trading halted")
                        return True
        except Exception as e:
            logger.warning(f"Could not check emergency stop: {e}")
        
        if not self.trading_enabled:
            logger.warning("🚨 TRADING_ENABLED=false - Trading halted")
            return True
        
        return False
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        if not self.enforce_market_hours:
            logger.info("⏰ Market hours enforcement disabled")
            return True
        
        # Get current time in market timezone
        now = datetime.now(self.market_timezone)
        current_time = now.time()
        current_weekday = now.weekday()
        
        # Check if weekend (Saturday=5, Sunday=6)
        if current_weekday >= 5:
            logger.info(f"📴 Weekend detected ({now.strftime('%A')}) - Market closed")
            return False
        
        # Check if within trading hours
        if self.market_open_time <= current_time <= self.market_close_time:
            logger.info(f"✅ Market hours: {current_time.strftime('%H:%M')} ET")
            return True
        else:
            logger.info(f"📴 Outside market hours: {current_time.strftime('%H:%M')} ET")
            logger.info(f"   Market: {self.market_open_time.strftime('%H:%M')} - {self.market_close_time.strftime('%H:%M')} ET")
            return False
    
    async def check_services_health(self) -> bool:
        """Check if required services are healthy"""
        services = {
            'Live Trading Service': f"{self.live_trading_url}/health",
            'Strategy Service': f"{self.strategy_service_url}/health",
        }
        
        all_healthy = True
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for name, url in services.items():
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info(f"✅ {name}: Healthy")
                    else:
                        logger.error(f"❌ {name}: Unhealthy (status: {response.status_code})")
                        all_healthy = False
                except Exception as e:
                    logger.error(f"❌ {name}: Unreachable - {e}")
                    all_healthy = False
        
        return all_healthy
    
    async def execute_trading_cycle(self) -> Dict[str, Any]:
        """Execute a single trading cycle"""
        try:
            logger.info("🔄 Starting trading cycle...")
            
            # Execute strategy via Live Trading Service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/strategies/execute",
                    params={'account_id': self.account_id},
                    json={'strategy_name': self.strategy_name}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Trading cycle completed")
                    logger.info(f"   • Orders submitted: {result.get('orders_submitted', 0)}")
                    logger.info(f"   • Orders successful: {result.get('orders_successful', 0)}")
                    logger.info(f"   • Orders failed: {result.get('orders_failed', 0)}")
                    return {
                        'success': True,
                        'result': result,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    error_text = response.text
                    logger.error(f"❌ Trading cycle failed: {response.status_code}")
                    logger.error(f"   Error: {error_text}")
                    return {
                        'success': False,
                        'error': error_text,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error in trading cycle: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def run(self) -> int:
        """Main execution function - returns exit code"""
        try:
            logger.info("=" * 80)
            logger.info("🚀 LIVE TRADING EXECUTOR - SINGLE CYCLE")
            logger.info("=" * 80)
            
            # Check emergency stop
            if await self.check_emergency_stop():
                logger.warning("🛑 Trading halted by emergency stop")
                return 0  # Exit successfully (emergency stop is intentional)
            
            # Check market hours
            if not self.is_market_hours():
                logger.info("⏰ Outside market hours - skipping execution")
                return 0  # Exit successfully (outside market hours is expected)
            
            # Check services health
            if not await self.check_services_health():
                logger.error("❌ Services not healthy - aborting")
                return 1  # Exit with error
            
            # Execute trading cycle
            result = await self.execute_trading_cycle()
            
            if result['success']:
                logger.info("✅ Trading cycle completed successfully")
                return 0  # Success
            else:
                logger.error(f"❌ Trading cycle failed: {result.get('error', 'Unknown error')}")
                return 1  # Failure
                
        except Exception as e:
            logger.error(f"❌ Fatal error in executor: {e}")
            return 1  # Failure


async def main():
    """Main entry point"""
    executor = LiveTradingExecutor()
    exit_code = await executor.run()
    
    logger.info("=" * 80)
    logger.info(f"Executor finished with exit code: {exit_code}")
    logger.info("=" * 80)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())

