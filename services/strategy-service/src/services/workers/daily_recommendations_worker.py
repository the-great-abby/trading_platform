"""
Daily Recommendations Worker - Generates daily trading recommendations and updates RSS feed
"""

import asyncio
import uuid
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from loguru import logger

from ..queue.rabbitmq_service import JobMessage, RabbitMQService
from ...utils.config import Config
from ...utils.trading_config import get_symbols


class DailyRecommendationsWorker:
    """Worker for generating daily trading recommendations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rabbitmq = RabbitMQService(config)
        self.is_running = False
        
        # Service URLs
        self.strategy_service_url = config.get('STRATEGY_SERVICE_URL', 'http://strategy-service:8000')
        self.rss_service_url = config.get('RSS_SERVICE_URL', 'http://rss-feed-service:8084')
        
        # Job handlers
        self.job_handlers = {
            'daily_recommendations': self._handle_daily_recommendations,
            'symbol_recommendations': self._handle_symbol_recommendations,
            'rss_update': self._handle_rss_update
        }
        
    async def start(self):
        """Start the worker"""
        try:
            logger.info("🚀 Starting Daily Recommendations Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register job handlers
            for job_type, handler in self.job_handlers.items():
                self.rabbitmq.register_job_handler(job_type, handler)
            
            # Start consuming jobs
            await self.rabbitmq.start_consuming()
            
            self.is_running = True
            logger.info("✅ Daily Recommendations Worker started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Daily Recommendations Worker: {e}")
            raise
    
    async def stop(self):
        """Stop the worker"""
        self.is_running = False
        await self.rabbitmq.disconnect()
        logger.info("🛑 Daily Recommendations Worker stopped")
    
    async def _handle_daily_recommendations(self, job: JobMessage):
        """Handle daily recommendations generation job"""
        try:
            logger.info(f"📊 Processing daily recommendations job: {job.job_id}")
            
            # Extract job parameters
            symbols = job.payload.get('symbols', [])
            include_ai = job.payload.get('include_ai_analysis', True)
            include_news = job.payload.get('include_news_sentiment', True)
            include_risk = job.payload.get('include_risk_assessment', True)
            strategies = job.payload.get('strategies', [
                'rsi_strategy', 'macd_strategy', 'bollinger_bands_strategy', 
                'news_enhanced_strategy', 'sma_crossover_strategy'
            ])
            
            # Use default symbols if none provided
            if not symbols:
                symbols = get_symbols()[:20]  # Top 20 symbols
            
            logger.info(f"📈 Generating recommendations for {len(symbols)} symbols")
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                symbols=symbols,
                include_ai=include_ai,
                include_news=include_news,
                include_risk=include_risk,
                strategies=strategies
            )
            
            # Store recommendations
            await self._store_recommendations(recommendations)
            
            # Trigger RSS feed update
            await self._trigger_rss_update(recommendations)
            
            # Send completion notification
            await self._send_completion_notification(job.job_id, recommendations)
            
            logger.info(f"✅ Daily recommendations completed: {len(recommendations)} recommendations generated")
            
        except Exception as e:
            logger.error(f"❌ Error processing daily recommendations job {job.job_id}: {e}")
            raise
    
    async def _handle_symbol_recommendations(self, job: JobMessage):
        """Handle single symbol recommendations job"""
        try:
            logger.info(f"📊 Processing symbol recommendations job: {job.job_id}")
            
            # Extract job parameters
            symbol = job.payload.get('symbol')
            if not symbol:
                raise ValueError("Symbol is required for symbol recommendations job")
            
            # Generate recommendation for single symbol
            recommendations = await self._generate_recommendations(
                symbols=[symbol],
                include_ai=job.payload.get('include_ai_analysis', True),
                include_news=job.payload.get('include_news_sentiment', True),
                include_risk=job.payload.get('include_risk_assessment', True),
                strategies=job.payload.get('strategies', [
                    'rsi_strategy', 'macd_strategy', 'bollinger_bands_strategy'
                ])
            )
            
            # Store recommendation
            await self._store_recommendations(recommendations)
            
            logger.info(f"✅ Symbol recommendation completed for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error processing symbol recommendations job {job.job_id}: {e}")
            raise
    
    async def _handle_rss_update(self, job: JobMessage):
        """Handle RSS feed update job"""
        try:
            logger.info(f"📊 Processing RSS update job: {job.job_id}")
            
            # Trigger RSS feed regeneration
            await self._trigger_rss_update()
            
            logger.info("✅ RSS feed update completed")
            
        except Exception as e:
            logger.error(f"❌ Error processing RSS update job {job.job_id}: {e}")
            raise
    
    async def _generate_recommendations(self, symbols: List[str], include_ai: bool = True, 
                                      include_news: bool = True, include_risk: bool = True,
                                      strategies: List[str] = None) -> List[Dict[str, Any]]:
        """Generate recommendations for symbols"""
        recommendations = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for symbol in symbols:
                try:
                    # Get recommendation from strategy service
                    response = await client.post(
                        f"{self.strategy_service_url}/recommendations/stock",
                        json={
                            "symbol": symbol,
                            "include_ai_analysis": include_ai,
                            "include_news_sentiment": include_news,
                            "include_risk_assessment": include_risk,
                            "strategies": strategies or [
                                'rsi_strategy', 'macd_strategy', 'bollinger_bands_strategy'
                            ]
                        }
                    )
                    
                    if response.status_code == 200:
                        recommendation = response.json()
                        recommendation['generated_at'] = datetime.now().isoformat()
                        recommendation['job_id'] = str(uuid.uuid4())
                        recommendations.append(recommendation)
                        
                        logger.info(f"✅ Generated recommendation for {symbol}: {recommendation['overall_recommendation']}")
                    else:
                        logger.warning(f"⚠️ Failed to get recommendation for {symbol}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating recommendation for {symbol}: {e}")
                    continue
        
        return recommendations
    
    async def _store_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Store recommendations in database"""
        try:
            # TODO: Implement database storage
            # For now, just log the recommendations
            logger.info(f"💾 Storing {len(recommendations)} recommendations")
            
            for rec in recommendations:
                logger.info(f"  - {rec['symbol']}: {rec['overall_recommendation']} ({rec['confidence']:.1%})")
                
        except Exception as e:
            logger.error(f"❌ Error storing recommendations: {e}")
    
    async def _trigger_rss_update(self, recommendations: List[Dict[str, Any]] = None):
        """Trigger RSS feed update"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Trigger RSS feed regeneration
                response = await client.get(f"{self.rss_service_url}/rss/daily-recommendations")
                
                if response.status_code == 200:
                    logger.info("✅ RSS feed updated successfully")
                else:
                    logger.warning(f"⚠️ Failed to update RSS feed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Error triggering RSS update: {e}")
    
    async def _send_completion_notification(self, job_id: str, recommendations: List[Dict[str, Any]]):
        """Send completion notification"""
        try:
            # Create notification job
            notification_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='notification',
                payload={
                    'notification_type': 'daily_recommendations_complete',
                    'job_id': job_id,
                    'recommendations_count': len(recommendations),
                    'timestamp': datetime.now().isoformat(),
                    'summary': {
                        'buy_signals': len([r for r in recommendations if r['overall_recommendation'] == 'BUY']),
                        'sell_signals': len([r for r in recommendations if r['overall_recommendation'] == 'SELL']),
                        'hold_signals': len([r for r in recommendations if r['overall_recommendation'] == 'HOLD'])
                    }
                },
                priority=5
            )
            
            # Publish notification job
            await self.rabbitmq.publish_job(
                notification_job,
                self.rabbitmq.queues.get('notification', 'notification_queue')
            )
            
            logger.info("📧 Completion notification sent")
            
        except Exception as e:
            logger.error(f"❌ Error sending completion notification: {e}")
    
    async def publish_daily_recommendations_job(self, symbols: List[str] = None, 
                                              include_ai: bool = True, 
                                              include_news: bool = True,
                                              include_risk: bool = True) -> bool:
        """Publish daily recommendations job to RabbitMQ"""
        try:
            job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='daily_recommendations',
                payload={
                    'symbols': symbols,
                    'include_ai_analysis': include_ai,
                    'include_news_sentiment': include_news,
                    'include_risk_assessment': include_risk,
                    'strategies': [
                        'rsi_strategy', 'macd_strategy', 'bollinger_bands_strategy',
                        'news_enhanced_strategy', 'sma_crossover_strategy'
                    ]
                },
                priority=8  # High priority
            )
            
            await self.rabbitmq.publish_job(
                job,
                self.rabbitmq.queues.get('daily_recommendations', 'daily_recommendations_queue')
            )
            
            logger.info(f"✅ Daily recommendations job published: {job.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish daily recommendations job: {e}")
            return False


async def main():
    """Main function"""
    config = Config()
    worker = DailyRecommendationsWorker(config)
    
    try:
        await worker.start()
        
        # Keep running
        while worker.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main()) 