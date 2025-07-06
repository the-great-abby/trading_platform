"""
Main entry point for the algorithmic trading bot
"""

import asyncio
import signal
import sys
from loguru import logger

from .core.trading_engine import TradingEngine, TradingMode
from .strategies.sma_crossover import SMACrossoverStrategy
from .strategies.rsi_strategy import RSIStrategy
from .utils.config import Config


class AlgoTrader:
    """Main trading bot application"""
    
    def __init__(self):
        self.config = Config()
        self.engine = TradingEngine(self.config)
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration"""
        logger.remove()  # Remove default handler
        logger.add(
            self.config.log_file,
            level=self.config.log_level,
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="{time:HH:mm:ss} | {level} | {message}"
        )
    
    def setup_strategies(self):
        """Setup and register trading strategies"""
        # SMA Crossover Strategy
        sma_strategy = SMACrossoverStrategy(short_window=20, long_window=50)
        self.engine.register_strategy("AAPL", sma_strategy)
        
        # RSI Strategy
        rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        self.engine.register_strategy("MSFT", rsi_strategy)
        
        logger.info(f"Registered {len(self.engine.strategies)} strategies")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the trading bot"""
        try:
            # Setup components
            self.setup_logging()
            self.setup_strategies()
            self.setup_signal_handlers()
            
            # Validate configuration
            if not self.config.validate():
                logger.warning("Configuration validation failed, but continuing...")
            
            # Set trading mode
            self.engine.set_mode(TradingMode.PAPER)
            
            logger.info("Starting AlgoTrader...")
            logger.info(f"Initial capital: ${self.config.initial_capital:,.2f}")
            logger.info(f"Trading mode: {self.engine.mode.value}")
            
            self.running = True
            
            # Start the trading engine
            await self.engine.start()
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        if self.engine.is_running:
            await self.engine.stop()
        logger.info("AlgoTrader stopped")


async def main():
    """Main function"""
    trader = AlgoTrader()
    await trader.run()


if __name__ == "__main__":
    asyncio.run(main()) 