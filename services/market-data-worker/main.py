#!/usr/bin/env python3
"""
Market Data Worker Service
Periodically fetches fresh market data from Polygon and fills missing data gaps
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

# Add src to path for imports
sys.path.append('src')

from src.services.queue.rabbitmq_service import RabbitMQService, JobMessage
from src.services.market_data.market_data_provider import get_market_data_manager
from src.services.database.market_data_service import MarketDataService
from src.services.market_data.options_data_service import OptionsDataService
from src.utils.config import get_config
from src.utils.trading_config import get_symbols
from src.utils.advanced_cache_manager import AdvancedCacheManager
from config import get_worker_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigWrapper:
    """Simple wrapper to make dict config compatible with RabbitMQ service"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config_dict = config_dict
    
    def get(self, key: str, default=None):
        return self.config_dict.get(key, default)


@dataclass
class MarketDataJob:
    """Market data job structure"""
    job_id: str
    job_type: str  # 'fetch_ohlcv', 'fetch_options', 'fill_gaps', 'cleanup_cache'
    symbols: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    interval: str = '1d'
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'interval': self.interval,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketDataJob':
        """Create from dictionary"""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class MarketDataWorker:
    """Worker for periodic market data fetching and gap filling"""
    
    def __init__(self):
        self.config = get_worker_config()
        
        # Create a config wrapper for RabbitMQ service
        rabbitmq_config = ConfigWrapper({
            'RABBITMQ_URL': self.config.rabbitmq_url,
            'database_url': self.config.database_url,
            'log_level': self.config.log_level
        })
        
        self.rabbitmq = RabbitMQService(rabbitmq_config)
        
        # Initialize services
        self.market_data_manager = get_market_data_manager()
        self.market_data_service = MarketDataService(self.config.database_url)
        self.options_service = OptionsDataService()
        self.cache_manager = AdvancedCacheManager()
        
        # Worker configuration
        self.symbols = get_symbols()
        self.update_interval_minutes = self.config.update_interval_minutes
        self.gap_fill_days = self.config.gap_fill_days
        self.max_concurrent_jobs = self.config.max_concurrent_jobs
        
        # Statistics
        self.stats = {
            'jobs_processed': 0,
            'jobs_failed': 0,
            'data_points_fetched': 0,
            'gaps_filled': 0,
            'last_update': None
        }
        
        # Job queues
        self.job_queues = {
            'market_data_fetch': 'market_data_fetch_queue',
            'options_data_fetch': 'options_data_fetch_queue',
            'gap_fill': 'gap_fill_queue',
            'cache_cleanup': 'cache_cleanup_queue'
        }
        
        logger.info(f"Market Data Worker initialized with {len(self.symbols)} symbols")
        logger.info(f"Update interval: {self.update_interval_minutes} minutes")
        logger.info(f"Gap fill days: {self.gap_fill_days}")
    
    async def start(self):
        """Start the market data worker"""
        try:
            logger.info("🚀 Starting Market Data Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            logger.info("✅ Connected to RabbitMQ")
            
            # Register job handlers
            self._register_handlers()
            
            # Start consuming from all queues
            self.consumer_tasks = await self._start_consuming()
            
            # Start periodic data fetching as a separate task
            self.periodic_task = asyncio.create_task(self._start_periodic_fetching())
            
            # Keep the main task running
            await asyncio.gather(
                *self.consumer_tasks,
                self.periodic_task,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to start Market Data Worker: {e}")
            raise
    
    def _register_handlers(self):
        """Register job handlers"""
        self.rabbitmq.register_handler('fetch_ohlcv', self._handle_fetch_ohlcv)
        self.rabbitmq.register_handler('fetch_options', self._handle_fetch_options)
        self.rabbitmq.register_handler('fill_gaps', self._handle_fill_gaps)
        self.rabbitmq.register_handler('cleanup_cache', self._handle_cleanup_cache)
        logger.info("✅ Registered job handlers")
    
    async def _start_consuming(self):
        """Start consuming from all queues"""
        logger.info("🔄 Starting to consume from all queues...")
        
        # Start consuming from all queues concurrently
        # Use create_task to run them concurrently without waiting
        tasks = [
            asyncio.create_task(self.rabbitmq.start_worker(self.job_queues['market_data_fetch'], 'fetch_ohlcv')),
            asyncio.create_task(self.rabbitmq.start_worker(self.job_queues['options_data_fetch'], 'fetch_options')),
            asyncio.create_task(self.rabbitmq.start_worker(self.job_queues['gap_fill'], 'fill_gaps')),
            asyncio.create_task(self.rabbitmq.start_worker(self.job_queues['cache_cleanup'], 'cleanup_cache'))
        ]
        
        # Don't wait for the tasks to complete, just start them
        logger.info("✅ Started consuming from all queues")
        
        # Return the tasks so they can be managed if needed
        return tasks
    
    async def _start_periodic_fetching(self):
        """Start periodic data fetching"""
        logger.info(f"🔄 Starting periodic data fetching every {self.update_interval_minutes} minutes")
        
        while True:
            try:
                # Create and publish jobs
                await self._create_periodic_jobs()
                
                # Wait for next cycle
                await asyncio.sleep(self.update_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"❌ Error in periodic fetching: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _create_periodic_jobs(self):
        """Create and publish periodic jobs"""
        current_time = datetime.now()
        end_date = current_time.strftime('%Y-%m-%d')
        start_date = (current_time - timedelta(days=self.gap_fill_days)).strftime('%Y-%m-%d')
        
        # Create OHLCV fetch job
        ohlcv_job = MarketDataJob(
            job_id=f"ohlcv_fetch_{current_time.strftime('%Y%m%d_%H%M%S')}",
            job_type='fetch_ohlcv',
            symbols=self.symbols,
            start_date=start_date,
            end_date=end_date,
            interval='1d',
            priority=5
        )
        
        # Create options fetch job (for major symbols only)
        major_symbols = [s for s in self.symbols if s in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']]
        if major_symbols:
            options_job = MarketDataJob(
                job_id=f"options_fetch_{current_time.strftime('%Y%m%d_%H%M%S')}",
                job_type='fetch_options',
                symbols=major_symbols,
                start_date=start_date,
                end_date=end_date,
                priority=3
            )
            
            # Publish options job
            await self.rabbitmq.publish_job(
                JobMessage(
                    job_id=options_job.job_id,
                    job_type=options_job.job_type,
                    payload=options_job.to_dict(),
                    priority=options_job.priority
                ),
                self.job_queues['options_data_fetch']
            )
            logger.info(f"📤 Published options fetch job for {len(major_symbols)} symbols")
        
        # Publish OHLCV job
        await self.rabbitmq.publish_job(
            JobMessage(
                job_id=ohlcv_job.job_id,
                job_type=ohlcv_job.job_type,
                payload=ohlcv_job.to_dict(),
                priority=ohlcv_job.priority
            ),
            self.job_queues['market_data_fetch']
        )
        logger.info(f"📤 Published OHLCV fetch job for {len(self.symbols)} symbols")
        
        # Create gap fill job
        gap_job = MarketDataJob(
            job_id=f"gap_fill_{current_time.strftime('%Y%m%d_%H%M%S')}",
            job_type='fill_gaps',
            symbols=self.symbols,
            start_date=start_date,
            end_date=end_date,
            priority=7
        )
        
        await self.rabbitmq.publish_job(
            JobMessage(
                job_id=gap_job.job_id,
                job_type=gap_job.job_type,
                payload=gap_job.to_dict(),
                priority=gap_job.priority
            ),
            self.job_queues['gap_fill']
        )
        logger.info(f"📤 Published gap fill job for {len(self.symbols)} symbols")
    
    async def _handle_fetch_ohlcv(self, job: JobMessage) -> bool:
        """Handle OHLCV data fetching"""
        try:
            job_data = MarketDataJob.from_dict(job.payload)
            logger.info(f"📊 Processing OHLCV fetch job: {job_data.job_id}")
            
            successful_symbols = 0
            total_data_points = 0
            
            for symbol in job_data.symbols:
                try:
                    # Fetch data from Polygon
                    data = await self._fetch_ohlcv_data(
                        symbol, 
                        job_data.start_date, 
                        job_data.end_date, 
                        job_data.interval
                    )
                    
                    if data is not None and not data.empty:
                        # Store in database
                        success = self.market_data_service.store_historical_data(
                            symbol, data, 'polygon', job_data.interval
                        )
                        
                        if success:
                            successful_symbols += 1
                            total_data_points += len(data)
                            logger.info(f"✅ Stored {len(data)} data points for {symbol}")
                        else:
                            logger.warning(f"⚠️ Failed to store data for {symbol}")
                    else:
                        logger.warning(f"⚠️ No data returned for {symbol}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol}: {e}")
                    continue
            
            # Update statistics
            self.stats['jobs_processed'] += 1
            self.stats['data_points_fetched'] += total_data_points
            self.stats['last_update'] = datetime.now()
            
            logger.info(f"✅ OHLCV job completed: {successful_symbols}/{len(job_data.symbols)} symbols, {total_data_points} data points")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in OHLCV fetch handler: {e}")
            self.stats['jobs_failed'] += 1
            return False
    
    async def _handle_fetch_options(self, job: JobMessage) -> bool:
        """Handle options data fetching"""
        try:
            job_data = MarketDataJob.from_dict(job.payload)
            logger.info(f"📊 Processing options fetch job: {job_data.job_id}")
            
            successful_symbols = 0
            total_contracts = 0
            
            for symbol in job_data.symbols:
                try:
                    # Fetch options chain
                    contracts = self.options_service.get_options_chain(symbol)
                    
                    if contracts:
                        successful_symbols += 1
                        total_contracts += len(contracts)
                        logger.info(f"✅ Fetched {len(contracts)} contracts for {symbol}")
                    else:
                        logger.warning(f"⚠️ No options data for {symbol}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing options for {symbol}: {e}")
                    continue
            
            logger.info(f"✅ Options job completed: {successful_symbols}/{len(job_data.symbols)} symbols, {total_contracts} contracts")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in options fetch handler: {e}")
            self.stats['jobs_failed'] += 1
            return False
    
    async def _handle_fill_gaps(self, job: JobMessage) -> bool:
        """Handle data gap filling"""
        try:
            job_data = MarketDataJob.from_dict(job.payload)
            logger.info(f"🔍 Processing gap fill job: {job_data.job_id}")
            
            gaps_filled = 0
            total_gaps = 0
            
            for symbol in job_data.symbols:
                try:
                    # Find missing dates
                    start_date = datetime.strptime(job_data.start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(job_data.end_date, '%Y-%m-%d').date()
                    
                    missing_dates = self.market_data_service.get_missing_dates(
                        symbol, start_date, end_date, 'polygon', job_data.interval
                    )
                    
                    if missing_dates:
                        total_gaps += len(missing_dates)
                        logger.info(f"🔍 Found {len(missing_dates)} missing dates for {symbol}")
                        
                        # Fetch missing data
                        for missing_date in missing_dates:
                            try:
                                data = await self._fetch_ohlcv_data(
                                    symbol,
                                    missing_date.strftime('%Y-%m-%d'),
                                    missing_date.strftime('%Y-%m-%d'),
                                    job_data.interval
                                )
                                
                                if data is not None and not data.empty:
                                    success = self.market_data_service.store_historical_data(
                                        symbol, data, 'polygon', job_data.interval
                                    )
                                    
                                    if success:
                                        gaps_filled += 1
                                        logger.info(f"✅ Filled gap for {symbol} on {missing_date}")
                                    
                            except Exception as e:
                                logger.error(f"❌ Error filling gap for {symbol} on {missing_date}: {e}")
                                continue
                    else:
                        logger.info(f"✅ No gaps found for {symbol}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing gaps for {symbol}: {e}")
                    continue
            
            # Update statistics
            self.stats['gaps_filled'] += gaps_filled
            
            logger.info(f"✅ Gap fill job completed: {gaps_filled}/{total_gaps} gaps filled")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in gap fill handler: {e}")
            self.stats['jobs_failed'] += 1
            return False
    
    async def _handle_cleanup_cache(self, job: JobMessage) -> bool:
        """Handle cache cleanup"""
        try:
            logger.info("🧹 Processing cache cleanup job")
            
            # Cleanup old data (keep last 365 days)
            cleaned_count = self.market_data_service.cleanup_old_data(days_to_keep=365)
            
            # Cleanup cache manager
            self.cache_manager.cleanup_expired()
            
            logger.info(f"✅ Cache cleanup completed: {cleaned_count} old records removed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in cache cleanup handler: {e}")
            self.stats['jobs_failed'] += 1
            return False
    
    async def _fetch_ohlcv_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1d') -> Optional[Any]:
        """Fetch OHLCV data from Polygon"""
        try:
            # Use the market data manager to fetch data
            data = self.market_data_manager.get_historical_data(symbol, start_date, end_date, interval)
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching OHLCV data for {symbol}: {e}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            **self.stats,
            'symbols_count': len(self.symbols),
            'update_interval_minutes': self.update_interval_minutes,
            'gap_fill_days': self.gap_fill_days
        }
    
    async def stop(self):
        """Stop the worker"""
        logger.info("🛑 Stopping Market Data Worker...")
        await self.rabbitmq.disconnect()
        logger.info("✅ Market Data Worker stopped")


async def main():
    """Main entry point"""
    worker = MarketDataWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main()) 