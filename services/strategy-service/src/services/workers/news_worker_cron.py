#!/usr/bin/env python3
"""
News Worker Cron Job Script
Runs news scanning as a one-time job for Kubernetes CronJob
"""

import asyncio
import sys
import yaml
import os
from datetime import datetime
from typing import List, Dict, Any

from .news_worker import NewsWorker
from ...utils.config import Config


class NewsWorkerCron:
    """News worker for cron job execution"""
    
    def __init__(self):
        self.config = Config()
        self.news_worker = NewsWorker(self.config)
        
    async def run_single_scan(self):
        """Run a single news scan"""
        try:
            print(f"🚀 Starting news scan at {datetime.now()}")
            
            # Load configuration
            config_path = "/app/config/news-sources.yaml"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                symbols = config_data.get('symbols', [])
                sources = [source['name'] for source in config_data.get('sources', []) if source.get('enabled', True)]
                
                print(f"📰 Scanning {len(sources)} sources for {len(symbols)} symbols")
                print(f"Sources: {sources}")
                print(f"Symbols: {symbols}")
                
                # Connect to RabbitMQ
                await self.news_worker.rabbitmq.connect()
                
                # Publish news scan job
                success = await self.news_worker.publish_manual_scan(
                    symbols=symbols,
                    sources=sources
                )
                
                if success:
                    print("✅ News scan job published successfully")
                else:
                    print("❌ Failed to publish news scan job")
                    sys.exit(1)
                
                # Wait a bit for job to be processed
                await asyncio.sleep(5)
                
                # Check queue status
                for queue_name in self.news_worker.rabbitmq.queues.values():
                    stats = await self.news_worker.rabbitmq.get_queue_stats(queue_name)
                    print(f"📊 {queue_name}: {stats['message_count']} messages")
                
                # Disconnect
                await self.news_worker.rabbitmq.disconnect()
                
                print(f"✅ News scan completed at {datetime.now()}")
                
            else:
                print(f"❌ Configuration file not found: {config_path}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error during news scan: {e}")
            sys.exit(1)


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cron-job":
        # Run as cron job
        cron = NewsWorkerCron()
        await cron.run_single_scan()
    else:
        # Run as regular worker
        config = Config()
        worker = NewsWorker(config)
        await worker.start()


if __name__ == "__main__":
    asyncio.run(main()) 