"""
News Scanning Worker - Processes news scanning jobs from RabbitMQ
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from ..queue.rabbitmq_service import JobMessage, RabbitMQService
from ..news.news_scanner import NewsScanner
from ...utils.config import Config


class NewsWorker:
    """Worker for processing news scanning jobs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rabbitmq = RabbitMQService(config)
        self.news_scanner = NewsScanner(config)
        self.is_running = False
        
    async def start(self):
        """Start the news worker"""
        try:
            logger.info("Starting News Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register job handlers
            self.rabbitmq.register_handler('news_scan', self._handle_news_scan)
            self.rabbitmq.register_handler('sentiment_analysis', self._handle_sentiment_analysis)
            
            # Start consuming from news scan queue
            self.is_running = True
            await self.rabbitmq.start_worker(
                queue_name=self.rabbitmq.queues['news_scan'],
                job_type='news_scan'
            )
            
        except Exception as e:
            logger.error(f"Failed to start News Worker: {e}")
            raise
    
    async def stop(self):
        """Stop the news worker"""
        self.is_running = False
        await self.rabbitmq.disconnect()
        logger.info("News Worker stopped")
    
    async def _handle_news_scan(self, job: JobMessage):
        """Handle news scanning job"""
        try:
            logger.info(f"Processing news scan job: {job.job_id}")
            
            # Extract job parameters
            symbols = job.payload.get('symbols', [])
            sources = job.payload.get('sources', ['reuters', 'bloomberg', 'cnbc'])
            scan_interval = job.payload.get('scan_interval', 300)  # 5 minutes
            
            # Perform news scan
            news_events = await self.news_scanner.scan_news_sources(symbols, sources)
            
            logger.info(f"Found {len(news_events)} news events")
            
            # For each news event, create a sentiment analysis job
            for event in news_events:
                sentiment_job = JobMessage(
                    job_id=str(uuid.uuid4()),
                    job_type='sentiment_analysis',
                    payload={
                        'news_event': {
                            'title': event.title,
                            'content': event.content,
                            'source': event.source,
                            'url': event.url,
                            'published_at': event.published_at.isoformat(),
                            'affected_symbols': event.affected_symbols,
                            'event_type': event.event_type
                        },
                        'original_job_id': job.job_id
                    },
                    priority=job.priority
                )
                
                # Publish sentiment analysis job
                await self.rabbitmq.publish_job(
                    sentiment_job,
                    self.rabbitmq.queues['sentiment_analysis']
                )
            
            # Schedule next scan
            await self._schedule_next_scan(symbols, sources, scan_interval)
            
            logger.info(f"Completed news scan job: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error processing news scan job {job.job_id}: {e}")
            raise
    
    async def _handle_sentiment_analysis(self, job: JobMessage):
        """Handle sentiment analysis job"""
        try:
            logger.info(f"Processing sentiment analysis job: {job.job_id}")
            
            # Extract news event
            news_event_data = job.payload['news_event']
            
            # Analyze sentiment
            sentiment_score = self.news_scanner._calculate_sentiment(news_event_data['title'])
            impact_score = self.news_scanner._calculate_impact(
                news_event_data['title'],
                news_event_data['event_type'],
                news_event_data['affected_symbols']
            )
            
            # Create trading signal if threshold met
            if abs(sentiment_score) > 0.3 and impact_score > 0.5:
                signal_job = JobMessage(
                    job_id=str(uuid.uuid4()),
                    job_type='trading_signal',
                    payload={
                        'symbols': news_event_data['affected_symbols'],
                        'sentiment_score': sentiment_score,
                        'impact_score': impact_score,
                        'news_event': news_event_data,
                        'signal_type': 'news_driven',
                        'confidence': abs(sentiment_score) * impact_score
                    },
                    priority=job.priority + 1  # Higher priority for trading signals
                )
                
                # Publish trading signal job
                await self.rabbitmq.publish_job(
                    signal_job,
                    self.rabbitmq.queues['trading_signal']
                )
                
                logger.info(f"Generated trading signal for {news_event_data['affected_symbols']}")
            
            logger.info(f"Completed sentiment analysis job: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error processing sentiment analysis job {job.job_id}: {e}")
            raise
    
    async def _schedule_next_scan(self, symbols: list, sources: list, interval: int):
        """Schedule the next news scan"""
        try:
            next_scan_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='news_scan',
                payload={
                    'symbols': symbols,
                    'sources': sources,
                    'scan_interval': interval
                },
                priority=0
            )
            
            # Schedule job to run after interval
            await asyncio.sleep(interval)
            await self.rabbitmq.publish_job(
                next_scan_job,
                self.rabbitmq.queues['news_scan']
            )
            
            logger.info(f"Scheduled next news scan in {interval} seconds")
            
        except Exception as e:
            logger.error(f"Failed to schedule next scan: {e}")
    
    async def publish_manual_scan(self, symbols: list, sources: list = None):
        """Publish a manual news scan job"""
        try:
            if sources is None:
                sources = ['reuters', 'bloomberg', 'cnbc']
            
            scan_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='news_scan',
                payload={
                    'symbols': symbols,
                    'sources': sources,
                    'manual': True
                },
                priority=5  # Higher priority for manual scans
            )
            
            success = await self.rabbitmq.publish_job(
                scan_job,
                self.rabbitmq.queues['news_scan']
            )
            
            if success:
                logger.info(f"Published manual news scan for symbols: {symbols}")
            else:
                logger.error("Failed to publish manual news scan")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing manual scan: {e}")
            return False 