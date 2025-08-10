#!/usr/bin/env python3
"""
Script to create LLM queues in RabbitMQ using aio_pika
"""

import asyncio
import aio_pika
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_llm_queues():
    """Create LLM queues in RabbitMQ"""
    try:
        # Use the same RabbitMQ URL as the existing service
        rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://trading:trading_pass@rabbitmq:5672/trading_vhost')
        
        logger.info(f"Connecting to RabbitMQ at {rabbitmq_url}")
        
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        
        # LLM queue names (same as in the service)
        llm_queues = [
            'llm.sentiment',
            'llm.signal', 
            'llm.risk',
            'llm.market',
            'llm.custom',
            'llm.results'
        ]
        
        # Create queues
        for queue_name in llm_queues:
            try:
                queue = await channel.declare_queue(queue_name, durable=True)
                logger.info(f"Created queue: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to create queue {queue_name}: {e}")
        
        await connection.close()
        logger.info("LLM queues created successfully")
        
    except Exception as e:
        logger.error(f"Error creating LLM queues: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_llm_queues()) 