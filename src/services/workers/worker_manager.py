"""
Worker Manager - Coordinates all background workers
"""

import asyncio
import signal
import sys
from typing import Dict, List
from loguru import logger

from .news_worker import NewsWorker
from .trading_signal_worker import TradingSignalWorker
from ...utils.config import Config


class WorkerManager:
    """Manages all background workers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.workers: Dict[str, any] = {}
        self.is_running = False
        
        # Initialize workers
        self.workers['news'] = NewsWorker(config)
        self.workers['trading_signal'] = TradingSignalWorker(config)
        
    async def start_all(self):
        """Start all workers"""
        try:
            logger.info("Starting Worker Manager...")
            
            # Start all workers concurrently
            tasks = []
            for name, worker in self.workers.items():
                logger.info(f"Starting {name} worker...")
                task = asyncio.create_task(worker.start())
                tasks.append(task)
            
            # Wait for all workers to start
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.is_running = True
            logger.info("All workers started successfully")
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in Worker Manager: {e}")
            raise
    
    async def stop_all(self):
        """Stop all workers"""
        try:
            logger.info("Stopping Worker Manager...")
            self.is_running = False
            
            # Stop all workers
            for name, worker in self.workers.items():
                logger.info(f"Stopping {name} worker...")
                await worker.stop()
            
            logger.info("All workers stopped")
            
        except Exception as e:
            logger.error(f"Error stopping workers: {e}")
    
    async def start_worker(self, worker_name: str):
        """Start a specific worker"""
        if worker_name in self.workers:
            await self.workers[worker_name].start()
            logger.info(f"Started {worker_name} worker")
        else:
            logger.error(f"Worker {worker_name} not found")
    
    async def stop_worker(self, worker_name: str):
        """Stop a specific worker"""
        if worker_name in self.workers:
            await self.workers[worker_name].stop()
            logger.info(f"Stopped {worker_name} worker")
        else:
            logger.error(f"Worker {worker_name} not found")
    
    def get_worker_status(self) -> Dict[str, bool]:
        """Get status of all workers"""
        return {
            name: worker.is_running 
            for name, worker in self.workers.items()
        }
    
    async def health_check(self) -> Dict[str, any]:
        """Perform health check on all workers"""
        status = {}
        for name, worker in self.workers.items():
            try:
                # Check if worker is running
                status[name] = {
                    'running': worker.is_running,
                    'healthy': True  # Add more health checks as needed
                }
            except Exception as e:
                status[name] = {
                    'running': False,
                    'healthy': False,
                    'error': str(e)
                }
        return status


async def main():
    """Main function to run the worker manager"""
    # Load configuration
    config = Config()
    
    # Create worker manager
    manager = WorkerManager(config)
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(manager.stop_all())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all workers
        await manager.start_all()
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.stop_all()


if __name__ == "__main__":
    asyncio.run(main()) 