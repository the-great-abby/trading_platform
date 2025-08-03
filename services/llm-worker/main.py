"""
LLM Worker for Background Processing
Processes LLM tasks from RabbitMQ queues
"""

import asyncio
import json
import logging
from typing import Dict, Any
import os
import sys

# Add the parent directory to the path to import from src
sys.path.append("/app/src")

from src.services.llm_service.llm_client import LLMClient, LLMRequest, LLMTaskType
from src.services.queue.rabbitmq_service import RabbitMQService
from src.utils.trading_config import get_trading_config
from src.utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMWorker:
    """LLM worker for background processing"""
    
    def __init__(self):
        self.config = get_trading_config()
        
        # LLM client
        llm_config = self.config.get('llm_service', {})
        self.llm_client = LLMClient(
            base_url=llm_config.get('base_url', 'http://localhost:12001'),
            api_key=llm_config.get('api_key'),
            timeout=llm_config.get('timeout', 30),
            max_retries=llm_config.get('max_retries', 3)
        )
        
        # RabbitMQ service
        config = get_config()
        self.rabbitmq = RabbitMQService(config)
        
        # Worker state
        self.is_running = False
        self.processed_tasks = 0
        self.failed_tasks = 0
        
        logger.info("LLM Worker initialized")
    
    async def start(self):
        """Start the LLM worker"""
        try:
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Start consuming messages
            self.is_running = True
            logger.info("LLM Worker started")
            
            # Start consuming from different queues
            await asyncio.gather(
                self._consume_sentiment_tasks(),
                self._consume_signal_tasks(),
                self._consume_risk_tasks(),
                self._consume_market_tasks(),
                self._consume_custom_tasks()
            )
            
        except Exception as e:
            logger.error(f"Error starting LLM worker: {e}")
            raise
    
    async def stop(self):
        """Stop the LLM worker"""
        self.is_running = False
        await self.llm_client.disconnect()
        await self.rabbitmq.disconnect()
        logger.info("LLM Worker stopped")
    
    async def _consume_sentiment_tasks(self):
        """Consume sentiment analysis tasks"""
        async def callback(message):
            try:
                data = json.loads(message.body.decode())
                logger.info(f"Processing sentiment task: {data.get('task_id', 'unknown')}")
                
                # Create LLM request
                request = LLMRequest(
                    model=data.get('model', 'gpt-3.5-turbo'),
                    messages=[
                        {"role": "system", "content": "You are a financial sentiment analysis expert."},
                        {"role": "user", "content": f"Analyze sentiment: {data.get('text', '')}"}
                    ],
                    task_type=LLMTaskType.SENTIMENT_ANALYSIS,
                    temperature=0.3,
                    max_tokens=500,
                    metadata=data.get('metadata', {})
                )
                
                # Process request
                response = await self.llm_client.generate(request)
                
                # Publish result
                result_data = {
                    'task_id': data.get('task_id'),
                    'task_type': 'sentiment_analysis',
                    'success': hasattr(response, 'content'),
                    'result': response.content if hasattr(response, 'content') else str(response),
                    'metadata': data.get('metadata', {})
                }
                
                # Create job message for result
                from src.services.queue.rabbitmq_service import JobMessage
                job = JobMessage(
                    job_id=f"result_{data.get('task_id', 'unknown')}",
                    job_type='llm_result',
                    payload=result_data
                )
                await self.rabbitmq.publish_job(job, 'llm.results')
                self.processed_tasks += 1
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing sentiment task: {e}")
                await self._handle_error(message, data.get('task_id', 'unknown'), str(e))
                self.failed_tasks += 1
        
        await self.rabbitmq.consume_queue('sentiment_analysis_queue', callback)
    
    async def _consume_signal_tasks(self):
        """Consume trading signal tasks"""
        async def callback(message):
            try:
                data = json.loads(message.body.decode())
                logger.info(f"Processing signal task: {data.get('task_id', 'unknown')}")
                
                # Create LLM request for signal generation
                market_data = data.get('market_data', {})
                news_data = data.get('news_data', [])
                technical_indicators = data.get('technical_indicators', {})
                
                request = LLMRequest(
                    model=data.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are an expert trading analyst."},
                        {"role": "user", "content": f"Generate trading signal for {market_data.get('symbol', 'Unknown')} based on market data, news, and technical indicators."}
                    ],
                    task_type=LLMTaskType.SIGNAL_GENERATION,
                    temperature=0.2,
                    max_tokens=800,
                    metadata={
                        'symbol': market_data.get('symbol'),
                        'data_sources': ['market_data', 'news', 'technical']
                    }
                )
                
                # Process request
                response = await self.llm_client.generate(request)
                
                # Publish result
                result_data = {
                    'task_id': data.get('task_id'),
                    'task_type': 'signal_generation',
                    'success': hasattr(response, 'content'),
                    'result': response.content if hasattr(response, 'content') else str(response),
                    'symbol': market_data.get('symbol'),
                    'metadata': data.get('metadata', {})
                }
                
                # Create job message for result
                job = JobMessage(
                    job_id=f"result_{data.get('task_id', 'unknown')}",
                    job_type='llm_result',
                    payload=result_data
                )
                await self.rabbitmq.publish_job(job, 'llm.results')
                self.processed_tasks += 1
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing signal task: {e}")
                await self._handle_error(message, data.get('task_id', 'unknown'), str(e))
                self.failed_tasks += 1
        
        await self.rabbitmq.consume_queue('trading_signal_queue', callback)
    
    async def _consume_risk_tasks(self):
        """Consume risk assessment tasks"""
        async def callback(message):
            try:
                data = json.loads(message.body.decode())
                logger.info(f"Processing risk task: {data.get('task_id', 'unknown')}")
                
                # Create LLM request for risk assessment
                portfolio_data = data.get('portfolio_data', {})
                market_conditions = data.get('market_conditions', {})
                
                request = LLMRequest(
                    model=data.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are a risk management expert."},
                        {"role": "user", "content": f"Assess portfolio risk based on portfolio data and market conditions."}
                    ],
                    task_type=LLMTaskType.RISK_ASSESSMENT,
                    temperature=0.1,
                    max_tokens=1000,
                    metadata={'portfolio_size': len(portfolio_data.get('positions', []))}
                )
                
                # Process request
                response = await self.llm_client.generate(request)
                
                # Publish result
                result_data = {
                    'task_id': data.get('task_id'),
                    'task_type': 'risk_assessment',
                    'success': hasattr(response, 'content'),
                    'result': response.content if hasattr(response, 'content') else str(response),
                    'metadata': data.get('metadata', {})
                }
                
                # Create job message for result
                job = JobMessage(
                    job_id=f"result_{data.get('task_id', 'unknown')}",
                    job_type='llm_result',
                    payload=result_data
                )
                await self.rabbitmq.publish_job(job, 'llm.results')
                self.processed_tasks += 1
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing risk task: {e}")
                await self._handle_error(message, data.get('task_id', 'unknown'), str(e))
                self.failed_tasks += 1
        
        await self.rabbitmq.consume_queue('risk_check_queue', callback)
    
    async def _consume_market_tasks(self):
        """Consume market analysis tasks"""
        async def callback(message):
            try:
                data = json.loads(message.body.decode())
                logger.info(f"Processing market task: {data.get('task_id', 'unknown')}")
                
                # Create LLM request for market analysis
                market_data = data.get('market_data', {})
                timeframe = data.get('timeframe', '1d')
                
                request = LLMRequest(
                    model=data.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are a market analysis expert."},
                        {"role": "user", "content": f"Analyze market conditions for timeframe: {timeframe}"}
                    ],
                    task_type=LLMTaskType.MARKET_ANALYSIS,
                    temperature=0.3,
                    max_tokens=800,
                    metadata={'timeframe': timeframe}
                )
                
                # Process request
                response = await self.llm_client.generate(request)
                
                # Publish result
                result_data = {
                    'task_id': data.get('task_id'),
                    'task_type': 'market_analysis',
                    'success': hasattr(response, 'content'),
                    'result': response.content if hasattr(response, 'content') else str(response),
                    'timeframe': timeframe,
                    'metadata': data.get('metadata', {})
                }
                
                # Create job message for result
                job = JobMessage(
                    job_id=f"result_{data.get('task_id', 'unknown')}",
                    job_type='llm_result',
                    payload=result_data
                )
                await self.rabbitmq.publish_job(job, 'llm.results')
                self.processed_tasks += 1
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing market task: {e}")
                await self._handle_error(message, data.get('task_id', 'unknown'), str(e))
                self.failed_tasks += 1
        
        await self.rabbitmq.consume_queue('market_data_fetch_queue', callback)
    
    async def _consume_custom_tasks(self):
        """Consume custom LLM tasks"""
        async def callback(message):
            try:
                data = json.loads(message.body.decode())
                logger.info(f"Processing custom task: {data.get('task_id', 'unknown')}")
                
                # Create LLM request
                request = LLMRequest(
                    model=data.get('model', 'gpt-3.5-turbo'),
                    messages=data.get('messages', []),
                    task_type=LLMTaskType(data.get('task_type', 'custom')),
                    temperature=data.get('temperature', 0.7),
                    max_tokens=data.get('max_tokens', 1000),
                    metadata=data.get('metadata', {})
                )
                
                # Process request
                response = await self.llm_client.generate(request)
                
                # Publish result
                result_data = {
                    'task_id': data.get('task_id'),
                    'task_type': 'custom',
                    'success': hasattr(response, 'content'),
                    'result': response.content if hasattr(response, 'content') else str(response),
                    'metadata': data.get('metadata', {})
                }
                
                # Create job message for result
                job = JobMessage(
                    job_id=f"result_{data.get('task_id', 'unknown')}",
                    job_type='llm_result',
                    payload=result_data
                )
                await self.rabbitmq.publish_job(job, 'llm.results')
                self.processed_tasks += 1
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(f"Error processing custom task: {e}")
                await self._handle_error(message, data.get('task_id', 'unknown'), str(e))
                self.failed_tasks += 1
        
        await self.rabbitmq.consume_queue('notification_queue', callback)
    
    async def _handle_error(self, message, task_id: str, error: str):
        """Handle task processing errors"""
        try:
            error_data = {
                'task_id': task_id,
                'error': error,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # Create job message for error
            from src.services.queue.rabbitmq_service import JobMessage
            job = JobMessage(
                job_id=f"error_{task_id}",
                job_type='llm_error',
                payload=error_data
            )
            await self.rabbitmq.publish_job(job, 'llm.errors')
            await message.ack()
            
        except Exception as e:
            logger.error(f"Error handling error: {e}")
            await message.nack()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            'processed_tasks': self.processed_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': (self.processed_tasks - self.failed_tasks) / max(self.processed_tasks, 1) * 100,
            'is_running': self.is_running
        }


async def main():
    """Main function"""
    worker = LLMWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main()) 