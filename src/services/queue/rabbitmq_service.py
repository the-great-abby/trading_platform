"""
RabbitMQ Service for Background Job Processing
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode
from loguru import logger

from ...utils.config import Config


@dataclass
class JobMessage:
    """Job message structure"""
    job_id: str
    job_type: str
    payload: Dict[str, Any]
    priority: int = 0
    created_at: datetime = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobMessage':
        """Create from dictionary"""
        if isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class RabbitMQService:
    """RabbitMQ service for background job processing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connection = None
        self.channel = None
        self.exchange = None
        
        # Queue names
        self.queues = {
            'news_scan': 'news_scan_queue',
            'sentiment_analysis': 'sentiment_analysis_queue',
            'trading_signal': 'trading_signal_queue',
            'backtest': 'backtest_queue',
            'risk_check': 'risk_check_queue',
            'portfolio_update': 'portfolio_update_queue',
            'daily_recommendations': 'daily_recommendations_queue',
            'notification': 'notification_queue',
            'market_data_fetch': 'market_data_fetch_queue',
            'options_data_fetch': 'options_data_fetch_queue',
            'gap_fill': 'gap_fill_queue',
            'cache_cleanup': 'cache_cleanup_queue',
            # LLM-specific queues
            'llm_sentiment': 'llm.sentiment',
            'llm_signal': 'llm.signal',
            'llm_risk': 'llm.risk',
            'llm_market': 'llm.market',
            'llm_custom': 'llm.custom',
            'llm_results': 'llm.results'
        }
        
        # Job handlers
        self.job_handlers: Dict[str, Callable] = {}
        
        # Connection settings
        self.rabbitmq_url = config.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            logger.info("Connecting to RabbitMQ...")
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                'trading_jobs',
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queues
            for queue_name in self.queues.values():
                try:
                    queue = await self.channel.declare_queue(
                        queue_name,
                        durable=True,
                        arguments={
                            'x-message-ttl': 24 * 60 * 60 * 1000,  # 24 hours
                            'x-max-priority': 10
                        }
                    )
                except Exception as e:
                    # If queue already exists with different arguments, try to declare it passively
                    logger.warning(f"Failed to declare queue {queue_name} with arguments: {e}")
                    queue = await self.channel.declare_queue(
                        queue_name,
                        durable=True,
                        passive=True
                    )
                
                # Bind queue to exchange
                await queue.bind(self.exchange, routing_key=queue_name)
            
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    async def publish_job(self, job: JobMessage, queue_name: str) -> bool:
        """Publish a job to a specific queue"""
        try:
            if not self.channel:
                await self.connect()
            
            # Serialize job message
            message_body = json.dumps(job.to_dict()).encode()
            
            # Create message with properties
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=job.priority,
                headers={
                    'job_id': job.job_id,
                    'job_type': job.job_type,
                    'retry_count': job.retry_count
                }
            )
            
            # Publish to queue
            await self.exchange.publish(
                message,
                routing_key=queue_name
            )
            
            logger.info(f"Published job {job.job_id} to queue {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish job {job.job_id}: {e}")
            return False
    
    async def consume_queue(self, queue_name: str, handler: Callable, prefetch_count: int = 10):
        """Start consuming messages from a queue"""
        try:
            if not self.channel:
                await self.connect()
            
            # Set QoS
            await self.channel.set_qos(prefetch_count=prefetch_count)
            
            # Get queue - try passive first to avoid conflicts
            try:
                queue = await self.channel.declare_queue(queue_name, durable=True, passive=True)
            except Exception:
                # If passive declaration fails, try active declaration
                queue = await self.channel.declare_queue(queue_name, durable=True)
            
            logger.info(f"Starting to consume from queue: {queue_name}")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            # Parse job message
                            job_data = json.loads(message.body.decode())
                            job = JobMessage.from_dict(job_data)
                            
                            logger.info(f"Processing job {job.job_id} from {queue_name}")
                            
                            # Execute handler
                            await handler(job)
                            
                            logger.info(f"Successfully processed job {job.job_id}")
                            
                        except Exception as e:
                            logger.error(f"Error processing job {job.job_id}: {e}")
                            
                            # Handle retry logic
                            if job.retry_count < job.max_retries:
                                job.retry_count += 1
                                await asyncio.sleep(self.retry_delay)
                                await self.publish_job(job, queue_name)
                                logger.info(f"Retrying job {job.job_id} (attempt {job.retry_count})")
                            else:
                                logger.error(f"Job {job.job_id} failed after {job.max_retries} retries")
                                
                                # Publish to dead letter queue
                                await self._publish_to_dlq(job, queue_name, str(e))
                                
        except Exception as e:
            logger.error(f"Error consuming from queue {queue_name}: {e}")
            raise
    
    async def _publish_to_dlq(self, job: JobMessage, original_queue: str, error: str):
        """Publish failed job to dead letter queue"""
        try:
            dlq_name = f"{original_queue}_dlq"
            
            # Declare DLQ
            dlq = await self.channel.declare_queue(dlq_name, durable=True)
            
            # Add error information to job
            job.payload['error'] = error
            job.payload['failed_at'] = datetime.now().isoformat()
            job.payload['original_queue'] = original_queue
            
            # Publish to DLQ
            message_body = json.dumps(job.to_dict()).encode()
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await self.exchange.publish(message, routing_key=dlq_name)
            logger.info(f"Published failed job {job.job_id} to DLQ {dlq_name}")
            
        except Exception as e:
            logger.error(f"Failed to publish to DLQ: {e}")
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            if not self.channel:
                await self.connect()
            
            queue = await self.channel.declare_queue(queue_name, durable=True, passive=True)
            queue_info = queue.declaration_result
            
            return {
                'queue_name': queue_name,
                'message_count': queue_info.message_count,
                'consumer_count': queue_info.consumer_count,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return {
                'queue_name': queue_name,
                'message_count': 0,
                'consumer_count': 0,
                'status': 'error'
            }
    
    async def purge_queue(self, queue_name: str) -> bool:
        """Purge all messages from a queue"""
        try:
            if not self.channel:
                await self.connect()
            
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.purge()
            
            logger.info(f"Purged queue: {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return False
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler for a specific job type"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    async def start_worker(self, queue_name: str, job_type: str):
        """Start a worker for a specific queue and job type"""
        if job_type not in self.job_handlers:
            raise ValueError(f"No handler registered for job type: {job_type}")
        
        handler = self.job_handlers[job_type]
        await self.consume_queue(queue_name, handler)
    
    async def health_check(self) -> bool:
        """Check if RabbitMQ connection is healthy"""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            
            # Try to declare a test queue
            test_queue = await self.channel.declare_queue('health_check', durable=False)
            await test_queue.delete()
            
            return True
            
        except Exception:
            return False 