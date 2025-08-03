"""
News Scanning Worker - Processes news scanning jobs from RabbitMQ
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any
from loguru import logger
import aiohttp
import json

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
        
        # LLM Proxy configuration
        self.llm_proxy_url = getattr(config, 'llm_proxy_url', 'http://llm-proxy:12001')
        self.enable_llm_analysis = getattr(config, 'enable_llm_analysis', True)
        self.llm_timeout = getattr(config, 'llm_timeout', 30)
        self.llm_max_retries = getattr(config, 'llm_max_retries', 3)
        
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
        """Handle sentiment analysis job using LLM Proxy"""
        try:
            logger.info(f"Processing sentiment analysis job: {job.job_id}")
            
            news_event = job.payload.get('news_event', {})
            
            if not self.enable_llm_analysis:
                logger.info("LLM analysis disabled, skipping sentiment analysis")
                return
            
            # Prepare text for sentiment analysis
            text = f"{news_event.get('title', '')} {news_event.get('content', '')}"
            context = f"Financial news from {news_event.get('source', 'unknown')} about {', '.join(news_event.get('affected_symbols', []))}"
            
            # Use LLM Proxy for sentiment analysis
            sentiment_result = await self._analyze_sentiment_with_llm_proxy(text, context)
            
            if sentiment_result:
                # Store sentiment analysis result
                await self._store_sentiment_result(news_event, sentiment_result)
                
                # Generate trading signal if sentiment is significant
                if self._should_generate_signal(sentiment_result):
                    signal = await self._generate_trading_signal(news_event, sentiment_result)
                    if signal:
                        await self._send_signal(signal)
            
            logger.info(f"Completed sentiment analysis job: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error processing sentiment analysis job {job.job_id}: {e}")
            raise
    
    async def _analyze_sentiment_with_llm_proxy(self, text: str, context: str) -> Dict[str, Any]:
        """Analyze sentiment using LLM Proxy"""
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare request for LLM Proxy
                llm_request = {
                    "operation": "sentiment",
                    "data": {
                        "text": text,
                        "context": context
                    },
                    "model": "gpt-3.5-turbo",
                    "priority": 2,
                    "use_cache": True
                }
                
                url = f"{self.llm_proxy_url}/api/v1/llm"
                async with session.post(url, json=llm_request, timeout=self.llm_timeout) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            return result.get('data', {})
                        else:
                            logger.error(f"LLM Proxy sentiment analysis failed: {result.get('error')}")
                            return None
                    else:
                        logger.error(f"LLM Proxy request failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling LLM Proxy for sentiment analysis: {e}")
            return None
    
    def _should_generate_signal(self, sentiment_result: Dict[str, Any]) -> bool:
        """Determine if sentiment warrants generating a trading signal"""
        try:
            sentiment_score = sentiment_result.get('sentiment_score', 0)
            confidence = sentiment_result.get('confidence', 0)
            
            # Generate signal if sentiment is significant and confidence is high
            return abs(sentiment_score) > 0.3 and confidence > 0.7
            
        except Exception as e:
            logger.error(f"Error checking signal generation criteria: {e}")
            return False
    
    async def _generate_trading_signal(self, news_event: Dict[str, Any], sentiment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on news and sentiment"""
        try:
            # Create trading signal
            signal = {
                'type': 'news_sentiment',
                'symbols': news_event.get('affected_symbols', []),
                'sentiment_score': sentiment_result.get('sentiment_score', 0),
                'confidence': sentiment_result.get('confidence', 0),
                'news_source': news_event.get('source'),
                'news_title': news_event.get('title'),
                'timestamp': datetime.now().isoformat(),
                'action': 'BUY' if sentiment_result.get('sentiment_score', 0) > 0.3 else 'SELL' if sentiment_result.get('sentiment_score', 0) < -0.3 else 'HOLD'
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {e}")
            return None
    
    async def _store_sentiment_result(self, news_event: Dict[str, Any], sentiment_result: Dict[str, Any]):
        """Store sentiment analysis result in database"""
        try:
            # Store in database (implementation depends on your database service)
            logger.info(f"Stored sentiment result for {news_event.get('title', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error storing sentiment result: {e}")
    
    async def _send_signal(self, signal: Dict[str, Any]):
        """Send trading signal to trading engine"""
        try:
            # Send to trading engine (implementation depends on your trading service)
            logger.info(f"Sent trading signal: {signal.get('action')} for {signal.get('symbols')}")
            
        except Exception as e:
            logger.error(f"Error sending trading signal: {e}")
    
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
    
    async def publish_manual_scan(self, symbols: list, sources: list) -> bool:
        """Publish a manual news scan job"""
        try:
            scan_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='news_scan',
                payload={
                    'symbols': symbols,
                    'sources': sources,
                    'scan_interval': 0  # No auto-scheduling for manual scans
                },
                priority=1
            )
            
            await self.rabbitmq.publish_job(
                scan_job,
                self.rabbitmq.queues['news_scan']
            )
            
            logger.info(f"Published manual news scan job for {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish manual scan job: {e}")
            return False 