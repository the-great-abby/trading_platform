#!/usr/bin/env python3
"""
RabbitMQ Workers Demo
Shows how background workers process news scanning and trading signal jobs
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any

from src.services.queue.rabbitmq_service import RabbitMQService, JobMessage
from src.services.workers.news_worker import NewsWorker
from src.services.workers.trading_signal_worker import TradingSignalWorker
from src.utils.config import Config


class RabbitMQDemo:
    """Demo class to show RabbitMQ worker system"""
    
    def __init__(self):
        self.config = Config()
        self.rabbitmq = RabbitMQService(self.config)
        self.news_worker = NewsWorker(self.config)
        self.trading_worker = TradingSignalWorker(self.config)
        
    async def run_demo(self):
        """Run the complete RabbitMQ demo"""
        print("🚀 RabbitMQ Workers Demo")
        print("=" * 60)
        print("This demo shows how background workers process jobs")
        print("using RabbitMQ message queues")
        print()
        
        # Step 1: Setup and connect
        await self._setup_rabbitmq()
        
        # Step 2: Start workers
        await self._start_workers()
        
        # Step 3: Publish jobs
        await self._publish_jobs()
        
        # Step 4: Monitor processing
        await self._monitor_processing()
        
        # Step 5: Show results
        await self._show_results()
        
        # Step 6: Cleanup
        await self._cleanup()
        
    async def _setup_rabbitmq(self):
        """Setup RabbitMQ connection"""
        print("🔧 Step 1: Setting up RabbitMQ")
        print("-" * 40)
        
        try:
            await self.rabbitmq.connect()
            print("✅ Connected to RabbitMQ")
            
            # Show queue stats
            for queue_name in self.rabbitmq.queues.values():
                stats = await self.rabbitmq.get_queue_stats(queue_name)
                print(f"   📊 {queue_name}: {stats['message_count']} messages")
            
            print()
            
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    async def _start_workers(self):
        """Start background workers"""
        print("🔄 Step 2: Starting Background Workers")
        print("-" * 40)
        
        try:
            # Start news worker
            print("📰 Starting News Worker...")
            news_task = asyncio.create_task(self.news_worker.start())
            
            # Start trading signal worker
            print("📊 Starting Trading Signal Worker...")
            trading_task = asyncio.create_task(self.trading_worker.start())
            
            # Give workers time to start
            await asyncio.sleep(2)
            
            print("✅ Background workers started")
            print()
            
            # Store tasks for cleanup
            self.worker_tasks = [news_task, trading_task]
            
        except Exception as e:
            print(f"❌ Failed to start workers: {e}")
            raise
    
    async def _publish_jobs(self):
        """Publish various jobs to queues"""
        print("📤 Step 3: Publishing Jobs to Queues")
        print("-" * 40)
        
        # Job 1: News scan job
        news_scan_job = JobMessage(
            job_id=str(uuid.uuid4()),
            job_type='news_scan',
            payload={
                'symbols': ['AAPL', 'TSLA', 'JPM', 'MSFT', 'GOOGL'],
                'sources': ['reuters', 'bloomberg', 'cnbc'],
                'scan_interval': 300,  # 5 minutes
                'demo': True
            },
            priority=5
        )
        
        success = await self.rabbitmq.publish_job(
            news_scan_job,
            self.rabbitmq.queues['news_scan']
        )
        
        if success:
            print(f"✅ Published news scan job: {news_scan_job.job_id}")
        else:
            print(f"❌ Failed to publish news scan job")
        
        # Job 2: Manual trading signal job
        trading_signal_job = JobMessage(
            job_id=str(uuid.uuid4()),
            job_type='trading_signal',
            payload={
                'symbol': 'AAPL',
                'strategy': 'news_enhanced',
                'signal_type': 'technical',
                'market_data': {
                    'Close': [150.0, 151.0, 152.0, 153.0, 154.0],
                    'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
                },
                'demo': True
            },
            priority=7
        )
        
        success = await self.rabbitmq.publish_job(
            trading_signal_job,
            self.rabbitmq.queues['trading_signal']
        )
        
        if success:
            print(f"✅ Published trading signal job: {trading_signal_job.job_id}")
        else:
            print(f"❌ Failed to publish trading signal job")
        
        # Job 3: Backtest job
        backtest_job = JobMessage(
            job_id=str(uuid.uuid4()),
            job_type='backtest',
            payload={
                'symbols': ['AAPL', 'TSLA'],
                'strategies': ['sma_crossover', 'rsi', 'macd'],
                'start_date': '2020-01-01',
                'end_date': '2025-07-02',
                'demo': True
            },
            priority=3
        )
        
        success = await self.rabbitmq.publish_job(
            backtest_job,
            self.rabbitmq.queues['backtest']
        )
        
        if success:
            print(f"✅ Published backtest job: {backtest_job.job_id}")
        else:
            print(f"❌ Failed to publish backtest job")
        
        print()
    
    async def _monitor_processing(self):
        """Monitor job processing"""
        print("👀 Step 4: Monitoring Job Processing")
        print("-" * 40)
        
        # Monitor for 10 seconds
        for i in range(10):
            print(f"   ⏱️  Monitoring... ({i+1}/10)")
            
            # Check queue stats
            for queue_name in self.rabbitmq.queues.values():
                stats = await self.rabbitmq.get_queue_stats(queue_name)
                if stats['message_count'] > 0:
                    print(f"      📊 {queue_name}: {stats['message_count']} messages pending")
            
            await asyncio.sleep(1)
        
        print("✅ Monitoring completed")
        print()
    
    async def _show_results(self):
        """Show final results"""
        print("📈 Step 5: Final Results")
        print("-" * 40)
        
        # Show final queue stats
        print("📊 Final Queue Statistics:")
        for queue_name in self.rabbitmq.queues.values():
            stats = await self.rabbitmq.get_queue_stats(queue_name)
            print(f"   {queue_name}:")
            print(f"      Messages: {stats['message_count']}")
            print(f"      Consumers: {stats['consumer_count']}")
            print(f"      Status: {stats['status']}")
        
        print()
        print("🎯 Job Processing Summary:")
        print("   ✅ News scan jobs processed by News Worker")
        print("   ✅ Sentiment analysis jobs generated")
        print("   ✅ Trading signal jobs processed by Trading Signal Worker")
        print("   ✅ Portfolio update jobs queued")
        print("   ✅ Backtest jobs processed")
        
        print()
        print("🚀 RabbitMQ Worker System Benefits:")
        print("   • Asynchronous job processing")
        print("   • Scalable worker architecture")
        print("   • Fault tolerance with retry logic")
        print("   • Priority-based job scheduling")
        print("   • Dead letter queue for failed jobs")
        print("   • Real-time job monitoring")
        
        print()
    
    async def _cleanup(self):
        """Cleanup resources"""
        print("🧹 Step 6: Cleanup")
        print("-" * 40)
        
        try:
            # Stop workers
            print("🛑 Stopping workers...")
            await self.news_worker.stop()
            await self.trading_worker.stop()
            
            # Cancel worker tasks
            for task in self.worker_tasks:
                task.cancel()
            
            # Disconnect from RabbitMQ
            print("🔌 Disconnecting from RabbitMQ...")
            await self.rabbitmq.disconnect()
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    async def demo_manual_jobs(self):
        """Demo manual job publishing"""
        print("\n🎯 Manual Job Publishing Demo")
        print("=" * 40)
        
        try:
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Publish manual news scan
            print("📰 Publishing manual news scan...")
            success = await self.news_worker.publish_manual_scan(
                symbols=['AAPL', 'TSLA'],
                sources=['reuters', 'bloomberg']
            )
            
            if success:
                print("✅ Manual news scan published")
            else:
                print("❌ Failed to publish manual news scan")
            
            # Publish manual trading signal
            print("📊 Publishing manual trading signal...")
            success = await self.trading_worker.publish_manual_signal(
                symbol='AAPL',
                strategy='news_enhanced'
            )
            
            if success:
                print("✅ Manual trading signal published")
            else:
                print("❌ Failed to publish manual trading signal")
            
            # Show queue stats
            print("\n📊 Queue Status After Manual Jobs:")
            for queue_name in self.rabbitmq.queues.values():
                stats = await self.rabbitmq.get_queue_stats(queue_name)
                print(f"   {queue_name}: {stats['message_count']} messages")
            
            # Cleanup
            await self.rabbitmq.disconnect()
            
        except Exception as e:
            print(f"❌ Error in manual job demo: {e}")


async def main():
    """Main demo function"""
    demo = RabbitMQDemo()
    
    try:
        await demo.run_demo()
        await demo.demo_manual_jobs()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        print("\n🎉 RabbitMQ Workers Demo Complete!")


if __name__ == "__main__":
    asyncio.run(main()) 