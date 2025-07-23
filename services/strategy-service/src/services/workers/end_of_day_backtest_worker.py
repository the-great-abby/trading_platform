#!/usr/bin/env python3
"""
End of Day Backtest Worker - Runs daily backtests after market close
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from loguru import logger

from ..queue.rabbitmq_service import JobMessage, RabbitMQService
from ...utils.config import Config
from ...utils.trading_config import get_symbols
from ...backtesting.engine.backtest_engine import BacktestEngine


class EndOfDayBacktestWorker:
    """Worker for running end-of-day backtests"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rabbitmq = RabbitMQService(config)
        self.is_running = False
        
        # Configuration
        self.symbols = os.getenv('BACKTEST_SYMBOLS', 'AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA').split(',')
        self.strategies = os.getenv('BACKTEST_STRATEGIES', 'RSIStrategy,MACDStrategy,BollingerBandsStrategy').split(',')
        self.period_days = int(os.getenv('BACKTEST_PERIOD_DAYS', '365'))
        self.initial_capital = float(os.getenv('BACKTEST_INITIAL_CAPITAL', '1000'))
        
        # Job handlers
        self.job_handlers = {
            'end_of_day_backtest': self._handle_end_of_day_backtest,
            'daily_performance_analysis': self._handle_daily_performance_analysis
        }
        
    async def start(self):
        """Start the worker"""
        try:
            logger.info("🚀 Starting End of Day Backtest Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register job handlers
            for job_type, handler in self.job_handlers.items():
                self.rabbitmq.register_job_handler(job_type, handler)
            
            # Start consuming jobs
            await self.rabbitmq.start_consuming()
            
            self.is_running = True
            logger.info("✅ End of Day Backtest Worker started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start End of Day Backtest Worker: {e}")
            raise
    
    async def stop(self):
        """Stop the worker"""
        self.is_running = False
        await self.rabbitmq.disconnect()
        logger.info("🛑 End of Day Backtest Worker stopped")
    
    async def _handle_end_of_day_backtest(self, job: JobMessage):
        """Handle end-of-day backtest job"""
        try:
            logger.info(f"📊 Processing end-of-day backtest job: {job.job_id}")
            
            # Extract job parameters
            symbols = job.payload.get('symbols', self.symbols)
            strategies = job.payload.get('strategies', self.strategies)
            period_days = job.payload.get('period_days', self.period_days)
            initial_capital = job.payload.get('initial_capital', self.initial_capital)
            
            # Calculate date range (last N days)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            
            logger.info(f"📈 Running end-of-day backtest:")
            logger.info(f"   Period: {start_date} to {end_date}")
            logger.info(f"   Symbols: {len(symbols)} stocks")
            logger.info(f"   Strategies: {', '.join(strategies)}")
            logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
            
            # Initialize backtest engine
            engine = BacktestEngine(
                use_real_data=True,
                use_cache=True
            )
            
            # Run backtest
            results = await engine.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                strategies=strategies
            )
            
            # Store results
            await self._store_backtest_results(results, job.job_id)
            
            # Generate performance report
            await self._generate_performance_report(results, job.job_id)
            
            logger.info("✅ End-of-day backtest completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error processing end-of-day backtest job {job.job_id}: {e}")
            raise
    
    async def _handle_daily_performance_analysis(self, job: JobMessage):
        """Handle daily performance analysis job"""
        try:
            logger.info(f"📊 Processing daily performance analysis job: {job.job_id}")
            
            # Analyze today's performance
            await self._analyze_daily_performance()
            
            logger.info("✅ Daily performance analysis completed")
            
        except Exception as e:
            logger.error(f"❌ Error processing daily performance analysis job {job.job_id}: {e}")
            raise
    
    async def _store_backtest_results(self, results: Dict[str, Any], job_id: str):
        """Store backtest results in database"""
        try:
            logger.info(f"💾 Storing backtest results for job {job_id}")
            
            # TODO: Implement database storage
            # For now, just log the results
            for strategy_name, result in results.items():
                if result:
                    logger.info(f"  {strategy_name}: {getattr(result, 'total_return_pct', 0):.2f}% return")
                else:
                    logger.info(f"  {strategy_name}: No result")
                    
        except Exception as e:
            logger.error(f"❌ Error storing backtest results: {e}")
    
    async def _generate_performance_report(self, results: Dict[str, Any], job_id: str):
        """Generate performance report"""
        try:
            logger.info(f"📊 Generating performance report for job {job_id}")
            
            # Calculate summary statistics
            total_strategies = len(results)
            successful_strategies = sum(1 for r in results.values() if r is not None)
            
            if successful_strategies > 0:
                returns = [getattr(r, 'total_return_pct', 0) for r in results.values() if r is not None]
                avg_return = sum(returns) / len(returns)
                best_strategy = max(results.items(), key=lambda x: getattr(x[1], 'total_return_pct', 0) if x[1] else 0)
                
                logger.info(f"📈 Performance Summary:")
                logger.info(f"   Successful strategies: {successful_strategies}/{total_strategies}")
                logger.info(f"   Average return: {avg_return:.2f}%")
                logger.info(f"   Best strategy: {best_strategy[0]} ({getattr(best_strategy[1], 'total_return_pct', 0):.2f}%)")
            else:
                logger.warning("⚠️ No successful strategies in this backtest")
                
        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")
    
    async def _analyze_daily_performance(self):
        """Analyze daily performance metrics"""
        try:
            logger.info("📊 Analyzing daily performance metrics...")
            
            # TODO: Implement daily performance analysis
            # - Compare today's performance vs historical averages
            # - Identify underperforming strategies
            # - Generate recommendations for tomorrow
            
            logger.info("✅ Daily performance analysis completed")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing daily performance: {e}")
    
    async def publish_end_of_day_backtest_job(self, symbols: List[str] = None, 
                                            strategies: List[str] = None,
                                            period_days: int = None) -> bool:
        """Publish end-of-day backtest job to RabbitMQ"""
        try:
            job = JobMessage(
                job_id=f"eod_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                job_type='end_of_day_backtest',
                payload={
                    'symbols': symbols or self.symbols,
                    'strategies': strategies or self.strategies,
                    'period_days': period_days or self.period_days,
                    'initial_capital': self.initial_capital
                },
                priority=7  # High priority
            )
            
            await self.rabbitmq.publish_job(
                job,
                self.rabbitmq.queues.get('end_of_day_backtest', 'end_of_day_backtest_queue')
            )
            
            logger.info(f"✅ End-of-day backtest job published: {job.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish end-of-day backtest job: {e}")
            return False


class EndOfDayBacktestCron:
    """End-of-day backtest cron job executor"""
    
    def __init__(self):
        self.config = Config()
        self.worker = EndOfDayBacktestWorker(self.config)
        
    async def run_end_of_day_backtest(self):
        """Run end-of-day backtest"""
        try:
            print(f"🚀 Starting end-of-day backtest at {datetime.now()}")
            
            # Get symbols to analyze
            symbols = self.worker.symbols
            
            print(f"📈 Running backtest for {len(symbols)} symbols")
            print(f"Symbols: {symbols}")
            print(f"Strategies: {', '.join(self.worker.strategies)}")
            
            # Connect to RabbitMQ
            await self.worker.rabbitmq.connect()
            
            # Publish end-of-day backtest job
            success = await self.worker.publish_end_of_day_backtest_job(
                symbols=symbols,
                strategies=self.worker.strategies,
                period_days=self.worker.period_days
            )
            
            if success:
                print("✅ End-of-day backtest job published successfully")
                print("📊 Job will be processed by the End of Day Backtest Worker")
            else:
                print("❌ Failed to publish end-of-day backtest job")
                sys.exit(1)
            
            # Wait a bit for job to be processed
            await asyncio.sleep(5)
            
            print("✅ End-of-day backtest cron job completed successfully")
            
        except Exception as e:
            print(f"❌ Error in end-of-day backtest cron job: {e}")
            sys.exit(1)
        finally:
            await self.worker.rabbitmq.disconnect()


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cron-job":
        # Run as cron job
        cron = EndOfDayBacktestCron()
        await cron.run_end_of_day_backtest()
    else:
        # Run as regular worker
        config = Config()
        worker = EndOfDayBacktestWorker(config)
        await worker.start()


if __name__ == "__main__":
    asyncio.run(main()) 