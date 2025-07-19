#!/usr/bin/env python3
"""
Daily Recommendations Cron Job Script
Runs daily recommendations generation as a one-time job for Kubernetes CronJob
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

from .daily_recommendations_worker import DailyRecommendationsWorker
from ...utils.config import Config
from ...utils.trading_config import get_symbols


class DailyRecommendationsCron:
    """Daily recommendations cron job executor"""
    
    def __init__(self):
        self.config = Config()
        self.worker = DailyRecommendationsWorker(self.config)
        
    async def run_daily_recommendations(self):
        """Run daily recommendations generation"""
        try:
            print(f"🚀 Starting daily recommendations generation at {datetime.now()}")
            
            # Get symbols to analyze
            symbols = get_symbols()[:20]  # Top 20 symbols
            
            print(f"📈 Generating recommendations for {len(symbols)} symbols")
            print(f"Symbols: {symbols}")
            
            # Connect to RabbitMQ
            await self.worker.rabbitmq.connect()
            
            # Publish daily recommendations job
            success = await self.worker.publish_daily_recommendations_job(
                symbols=symbols,
                include_ai=True,
                include_news=True,
                include_risk=True
            )
            
            if success:
                print("✅ Daily recommendations job published successfully")
                print("📊 Job will be processed by the Daily Recommendations Worker")
                print("📰 RSS feed will be updated automatically")
            else:
                print("❌ Failed to publish daily recommendations job")
                sys.exit(1)
            
            # Wait a bit for job to be processed
            await asyncio.sleep(5)
            
            print("✅ Daily recommendations cron job completed successfully")
            
        except Exception as e:
            print(f"❌ Error in daily recommendations cron job: {e}")
            sys.exit(1)
        finally:
            await self.worker.rabbitmq.disconnect()


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cron-job":
        # Run as cron job
        cron = DailyRecommendationsCron()
        await cron.run_daily_recommendations()
    else:
        # Run as regular worker
        config = Config()
        worker = DailyRecommendationsWorker(config)
        await worker.start()


if __name__ == "__main__":
    asyncio.run(main()) 