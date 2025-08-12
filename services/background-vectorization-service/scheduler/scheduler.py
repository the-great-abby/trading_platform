"""
Vectorization Scheduler
Handles periodic tasks and job scheduling for the background vectorization service.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database.manager import DatabaseManager
from vectorizer.market_data_vectorizer import MarketDataVectorizer
from vectorizer.news_vectorizer import NewsVectorizer
from vectorizer.earnings_vectorizer import EarningsVectorizer

logger = logging.getLogger(__name__)

class VectorizationScheduler:
    """Scheduler for managing periodic vectorization tasks."""
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 market_data_vectorizer: MarketDataVectorizer,
                 news_vectorizer: NewsVectorizer,
                 earnings_vectorizer: EarningsVectorizer):
        self.db_manager = db_manager
        self.market_data_vectorizer = market_data_vectorizer
        self.news_vectorizer = news_vectorizer
        self.earnings_vectorizer = earnings_vectorizer
        
        # Scheduling configuration
        self.market_data_interval = 3600  # 1 hour
        self.news_interval = 1800  # 30 minutes
        self.earnings_interval = 7200  # 2 hours
        
        # Task tracking
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting Vectorization Scheduler...")
        self.is_running = True
        
        # Start periodic tasks
        self.scheduled_tasks['market_data'] = asyncio.create_task(
            self._schedule_market_data_vectorization()
        )
        self.scheduled_tasks['news'] = asyncio.create_task(
            self._schedule_news_vectorization()
        )
        self.scheduled_tasks['earnings'] = asyncio.create_task(
            self._schedule_earnings_vectorization()
        )
        
        logger.info("Vectorization Scheduler started successfully")
        
    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
            
        logger.info("Stopping Vectorization Scheduler...")
        self.is_running = False
        
        # Cancel all scheduled tasks
        for task_name, task in self.scheduled_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            logger.info(f"Cancelled {task_name} task")
            
        self.scheduled_tasks.clear()
        logger.info("Vectorization Scheduler stopped")
        
    async def _schedule_market_data_vectorization(self):
        """Schedule periodic market data vectorization."""
        while self.is_running:
            try:
                logger.info("Running scheduled market data vectorization...")
                await self._vectorize_new_market_data()
                logger.info("Scheduled market data vectorization completed")
            except Exception as e:
                logger.error(f"Error in scheduled market data vectorization: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.market_data_interval)
            
    async def _schedule_news_vectorization(self):
        """Schedule periodic news vectorization."""
        while self.is_running:
            try:
                logger.info("Running scheduled news vectorization...")
                await self._vectorize_new_news()
                logger.info("Scheduled news vectorization completed")
            except Exception as e:
                logger.error(f"Error in scheduled news vectorization: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.news_interval)
            
    async def _schedule_earnings_vectorization(self):
        """Schedule periodic earnings vectorization."""
        while self.is_running:
            try:
                logger.info("Running scheduled earnings vectorization...")
                await self._vectorize_new_earnings()
                logger.info("Scheduled earnings vectorization completed")
            except Exception as e:
                logger.error(f"Error in scheduled earnings vectorization: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.earnings_interval)
            
    async def _vectorize_new_market_data(self):
        """Vectorize new market data that hasn't been processed yet."""
        try:
            # Get symbols with unvectorized market data
            symbols = await self._get_unvectorized_market_data_symbols()
            
            if not symbols:
                logger.info("No new market data to vectorize")
                return
                
            logger.info(f"Found {len(symbols)} symbols with new market data to vectorize")
            
            # Process in batches to avoid overwhelming the system
            batch_size = 5
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {batch}")
                
                # Use the vectorizer to process each symbol
                results = await self.market_data_vectorizer.batch_vectorize_market_data(batch)
                
                # Log results
                successful = sum(1 for success in results.values() if success)
                logger.info(f"Batch completed: {successful}/{len(batch)} symbols vectorized successfully")
                
                # Small delay between batches
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in market data vectorization: {e}")
            raise
            
    async def _vectorize_new_news(self):
        """Vectorize new news articles that haven't been processed yet."""
        try:
            # Get unvectorized news IDs
            news_ids = await self.news_vectorizer.get_unvectorized_news(limit=50)
            
            if not news_ids:
                logger.info("No new news articles to vectorize")
                return
                
            logger.info(f"Found {len(news_ids)} news articles to vectorize")
            
            # Process in smaller batches for news (more complex processing)
            batch_size = 10
            for i in range(0, len(news_ids), batch_size):
                batch = news_ids[i:i + batch_size]
                logger.info(f"Processing news batch {i//batch_size + 1}: {len(batch)} articles")
                
                # Process each news article
                for news_id in batch:
                    try:
                        # Create a job for this news article
                        from main import VectorizationJob
                        job = VectorizationJob(
                            job_id=f"news_{news_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                            data_type="news",
                            data={"id": news_id},
                            priority=2
                        )
                        
                        # Process directly (bypass queue for scheduled tasks)
                        success = await self.news_vectorizer.vectorize_news_data(job)
                        if success:
                            logger.info(f"Successfully vectorized news article {news_id}")
                        else:
                            logger.warning(f"Failed to vectorize news article {news_id}")
                            
                    except Exception as e:
                        logger.error(f"Error vectorizing news article {news_id}: {e}")
                
                # Small delay between batches
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in news vectorization: {e}")
            raise
            
    async def _vectorize_new_earnings(self):
        """Vectorize new earnings reports that haven't been processed yet."""
        try:
            # Get unvectorized earnings IDs
            earnings_ids = await self.earnings_vectorizer.get_unvectorized_earnings(limit=20)
            
            if not earnings_ids:
                logger.info("No new earnings reports to vectorize")
                return
                
            logger.info(f"Found {len(earnings_ids)} earnings reports to vectorize")
            
            # Process earnings reports (usually fewer, more complex)
            for earnings_id in earnings_ids:
                try:
                    # Create a job for this earnings report
                    from main import VectorizationJob
                    job = VectorizationJob(
                        job_id=f"earnings_{earnings_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        data_type="earnings",
                        data={"id": earnings_id},
                        priority=3
                    )
                    
                    # Process directly
                    success = await self.earnings_vectorizer.vectorize_earnings_data(job)
                    if success:
                        logger.info(f"Successfully vectorized earnings report {earnings_id}")
                    else:
                        logger.warning(f"Failed to vectorize earnings report {earnings_id}")
                        
                except Exception as e:
                    logger.error(f"Error vectorizing earnings report {earnings_id}: {e}")
                
                # Small delay between earnings reports
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in earnings vectorization: {e}")
            raise
            
    async def _get_unvectorized_market_data_symbols(self) -> List[str]:
        """Get list of symbols with unvectorized market data."""
        try:
            # Query to find symbols with recent market data that hasn't been vectorized
            # Check against vector_embeddings table to see what's already been processed
            # Use correct table name 'historical_prices'
            query = """
            SELECT DISTINCT h.symbol
            FROM historical_prices h
            LEFT JOIN vector_embeddings v ON v.metadata_json->>'symbol' = h.symbol 
                AND v.vector_type = 'market_data'
                AND v.created_at >= h.date
            WHERE h.date >= NOW() - INTERVAL '7 days'
                AND v.id IS NULL
            ORDER BY h.symbol
            LIMIT 100
            """
            
            conn = await self.db_manager.pool.acquire()
            try:
                rows = await conn.fetch(query)
                return [row['symbol'] for row in rows]
            finally:
                await self.db_manager.pool.release(conn)
                
        except Exception as e:
            logger.error(f"Error getting unvectorized market data symbols: {e}")
            return []
            
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "scheduled_tasks": {
                name: {
                    "status": "running" if not task.done() else "completed",
                    "exception": str(task.exception()) if task.done() and task.exception() else None
                }
                for name, task in self.scheduled_tasks.items()
            },
            "intervals": {
                "market_data": self.market_data_interval,
                "news": self.news_interval,
                "earnings": self.earnings_interval
            },
            "last_run": {
                "market_data": "N/A",  # Could track this if needed
                "news": "N/A",
                "earnings": "N/A"
            }
        }
