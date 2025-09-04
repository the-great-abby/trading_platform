#!/usr/bin/env python3
"""
Script to create order management queues in RabbitMQ
"""

import asyncio
import aio_pika
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_order_queues():
    """Create order management queues in RabbitMQ"""
    try:
        # Use the correct RabbitMQ URL with trading user and vhost
        rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://trading:trading_pass@localhost:11143/trading_vhost')
        
        logger.info(f"Connecting to RabbitMQ at {rabbitmq_url}")
        
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        
        # Order management queue names
        order_queues = [
            'order.created',
            'order.submitted',
            'order.executed',
            'order.cancelled',
            'order.rejected',
            'order.expired',
            'order.validation',
            'order.routing',
            'order.risk_check',
            'order.compliance',
            'order.analytics',
            'order.heartbeat',
            'order.alerts',
            'order.escalation',
            'order.external_sync',
            'order.reconciliation'
        ]
        
        # Create queues
        for queue_name in order_queues:
            try:
                queue = await channel.declare_queue(queue_name, durable=True)
                logger.info(f"Created queue: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to create queue {queue_name}: {e}")
        
        await connection.close()
        logger.info("Order management queues created successfully")
        
    except Exception as e:
        logger.error(f"Error creating order queues: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_order_queues())

