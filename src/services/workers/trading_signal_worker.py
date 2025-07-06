"""
Trading Signal Worker - Processes trading signal jobs from RabbitMQ
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from ..queue.rabbitmq_service import JobMessage, RabbitMQService
from ...strategies.news_enhanced_strategy import NewsEnhancedStrategy
from ...strategies.sma_crossover import SMACrossoverStrategy
from ...strategies.rsi_strategy import RSIStrategy
from ...strategies.macd_strategy import MACDStrategy
from ...strategies.bollinger_bands_strategy import BollingerBandsStrategy
from ...core.types import TradeSignal
from ...utils.config import Config


class TradingSignalWorker:
    """Worker for processing trading signal jobs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rabbitmq = RabbitMQService(config)
        self.is_running = False
        
        # Initialize strategies
        self.strategies = {
            'news_enhanced': NewsEnhancedStrategy(),
            'sma_crossover': SMACrossoverStrategy(),
            'rsi': RSIStrategy(),
            'macd': MACDStrategy(),
            'bollinger_bands': BollingerBandsStrategy()
        }
        
    async def start(self):
        """Start the trading signal worker"""
        try:
            print("Starting Trading Signal Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register job handlers
            self.rabbitmq.register_handler('trading_signal', self._handle_trading_signal)
            self.rabbitmq.register_handler('backtest', self._handle_backtest)
            
            # Start consuming from trading signal queue
            self.is_running = True
            await self.rabbitmq.start_worker(
                queue_name=self.rabbitmq.queues['trading_signal'],
                job_type='trading_signal'
            )
            
        except Exception as e:
            print(f"Failed to start Trading Signal Worker: {e}")
            raise
    
    async def stop(self):
        """Stop the trading signal worker"""
        self.is_running = False
        await self.rabbitmq.disconnect()
        print("Trading Signal Worker stopped")
    
    async def _handle_trading_signal(self, job: JobMessage):
        """Handle trading signal job"""
        try:
            print(f"Processing trading signal job: {job.job_id}")
            
            # Extract job parameters
            signal_type = job.payload.get('signal_type', 'news_driven')
            symbols = job.payload.get('symbols', [])
            strategy_name = job.payload.get('strategy', 'news_enhanced')
            
            if signal_type == 'news_driven':
                await self._process_news_driven_signal(job)
            elif signal_type == 'technical':
                await self._process_technical_signal(job)
            elif signal_type == 'combined':
                await self._process_combined_signal(job)
            
            print(f"Completed trading signal job: {job.job_id}")
            
        except Exception as e:
            print(f"Error processing trading signal job {job.job_id}: {e}")
            raise
    
    async def _process_news_driven_signal(self, job: JobMessage):
        """Process news-driven trading signal"""
        try:
            # Extract news data
            news_event = job.payload.get('news_event', {})
            sentiment_score = job.payload.get('sentiment_score', 0)
            impact_score = job.payload.get('impact_score', 0)
            symbols = job.payload.get('symbols', [])
            
            print(f"Processing news-driven signal for {symbols}")
            print(f"Sentiment: {sentiment_score}, Impact: {impact_score}")
            
            # Generate trading signal based on news
            if sentiment_score > 0.3 and impact_score > 0.5:
                signal = TradeSignal(
                    symbol=symbols[0] if symbols else 'UNKNOWN',
                    action='BUY',
                    price=0.0,  # Will be filled by market data
                    quantity=100,
                    strategy='news_enhanced',
                    confidence=abs(sentiment_score) * impact_score,
                    metadata={
                        'news_event': news_event,
                        'sentiment_score': sentiment_score,
                        'impact_score': impact_score,
                        'signal_type': 'news_driven'
                    }
                )
                
                # Publish to portfolio update queue
                await self._publish_portfolio_update(signal, job)
                
            elif sentiment_score < -0.3 and impact_score > 0.5:
                signal = TradeSignal(
                    symbol=symbols[0] if symbols else 'UNKNOWN',
                    action='SELL',
                    price=0.0,
                    quantity=100,
                    strategy='news_enhanced',
                    confidence=abs(sentiment_score) * impact_score,
                    metadata={
                        'news_event': news_event,
                        'sentiment_score': sentiment_score,
                        'impact_score': impact_score,
                        'signal_type': 'news_driven'
                    }
                )
                
                # Publish to portfolio update queue
                await self._publish_portfolio_update(signal, job)
            
        except Exception as e:
            print(f"Error processing news-driven signal: {e}")
            raise
    
    async def _process_technical_signal(self, job: JobMessage):
        """Process technical trading signal"""
        try:
            # Extract technical data
            symbol = job.payload.get('symbol', 'UNKNOWN')
            strategy_name = job.payload.get('strategy', 'sma_crossover')
            market_data = job.payload.get('market_data', {})
            
            print(f"Processing technical signal for {symbol} using {strategy_name}")
            
            # Get strategy
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                print(f"Strategy {strategy_name} not found")
                return
            
            # Convert market data to DataFrame
            if market_data:
                data = pd.DataFrame(market_data)
                
                # Generate signal
                signal = await strategy.generate_signal(symbol, data)
                
                if signal:
                    # Publish to portfolio update queue
                    await self._publish_portfolio_update(signal, job)
            
        except Exception as e:
            print(f"Error processing technical signal: {e}")
            raise
    
    async def _process_combined_signal(self, job: JobMessage):
        """Process combined news + technical signal"""
        try:
            # Extract combined data
            symbol = job.payload.get('symbol', 'UNKNOWN')
            news_data = job.payload.get('news_data', {})
            technical_data = job.payload.get('technical_data', {})
            
            print(f"Processing combined signal for {symbol}")
            
            # Use news-enhanced strategy
            strategy = self.strategies['news_enhanced']
            
            # Convert technical data to DataFrame
            if technical_data:
                data = pd.DataFrame(technical_data)
                
                # Generate combined signal
                signal = await strategy.generate_signal(symbol, data)
                
                if signal:
                    # Add news metadata
                    signal.metadata.update({
                        'news_data': news_data,
                        'signal_type': 'combined'
                    })
                    
                    # Publish to portfolio update queue
                    await self._publish_portfolio_update(signal, job)
            
        except Exception as e:
            print(f"Error processing combined signal: {e}")
            raise
    
    async def _handle_backtest(self, job: JobMessage):
        """Handle backtest job"""
        try:
            print(f"Processing backtest job: {job.job_id}")
            
            # Extract backtest parameters
            symbols = job.payload.get('symbols', [])
            strategies = job.payload.get('strategies', ['sma_crossover', 'rsi', 'macd'])
            start_date = job.payload.get('start_date', '2020-01-01')
            end_date = job.payload.get('end_date', '2025-07-02')
            
            print(f"Running backtest for {symbols} with strategies {strategies}")
            
            # This would integrate with the backtest engine
            # For now, just log the parameters
            print(f"Backtest parameters: {symbols}, {strategies}, {start_date} to {end_date}")
            
            print(f"Completed backtest job: {job.job_id}")
            
        except Exception as e:
            print(f"Error processing backtest job {job.job_id}: {e}")
            raise
    
    async def _publish_portfolio_update(self, signal: TradeSignal, original_job: JobMessage):
        """Publish portfolio update job"""
        try:
            portfolio_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='portfolio_update',
                payload={
                    'signal': {
                        'symbol': signal.symbol,
                        'action': signal.action,
                        'price': signal.price,
                        'quantity': signal.quantity,
                        'strategy': signal.strategy,
                        'confidence': signal.confidence,
                        'metadata': signal.metadata
                    },
                    'original_job_id': original_job.job_id
                },
                priority=original_job.priority + 2  # Highest priority for portfolio updates
            )
            
            # Publish to portfolio update queue
            await self.rabbitmq.publish_job(
                portfolio_job,
                self.rabbitmq.queues['portfolio_update']
            )
            
            print(f"Published portfolio update for {signal.symbol} {signal.action}")
            
        except Exception as e:
            print(f"Error publishing portfolio update: {e}")
    
    async def publish_manual_signal(self, symbol: str, strategy: str, market_data: Dict = None):
        """Publish a manual trading signal job"""
        try:
            signal_job = JobMessage(
                job_id=str(uuid.uuid4()),
                job_type='trading_signal',
                payload={
                    'symbol': symbol,
                    'strategy': strategy,
                    'market_data': market_data or {},
                    'signal_type': 'technical',
                    'manual': True
                },
                priority=5
            )
            
            success = await self.rabbitmq.publish_job(
                signal_job,
                self.rabbitmq.queues['trading_signal']
            )
            
            if success:
                print(f"Published manual trading signal for {symbol} using {strategy}")
            else:
                print("Failed to publish manual trading signal")
            
            return success
            
        except Exception as e:
            print(f"Error publishing manual signal: {e}")
            return False 