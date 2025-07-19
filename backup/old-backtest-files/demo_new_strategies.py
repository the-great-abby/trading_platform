#!/usr/bin/env python3
"""
Demo New Trading Strategies
===========================
Demonstrates the new trading strategies implemented for the trading bot.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict

from src.strategies import (
    PairsTradingStrategy,
    VWAPStrategy, 
    CrossSectionalMomentumStrategy,
    MLEnsembleStrategy,
    KalmanFilterStrategy
)
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class NewStrategiesDemo:
    """Demo class for new trading strategies"""
    
    def __init__(self):
        self.strategies = {}
        self.market_data = {}
        
    async def initialize_strategies(self):
        """Initialize all new strategies"""
        logger.info("🚀 Initializing new trading strategies...")
        
        # Initialize strategies
        self.strategies = {
            'pairs_trading': PairsTradingStrategy(
                correlation_threshold=0.8,
                z_score_threshold=2.0
            ),
            'vwap': VWAPStrategy(
                vwap_period=20,
                volume_threshold=1.5
            ),
            'cross_sectional_momentum': CrossSectionalMomentumStrategy(
                lookback_period=60,
                top_percentile=0.2,
                bottom_percentile=0.2
            ),
            'ml_ensemble': MLEnsembleStrategy(
                lookback_period=60,
                prediction_horizon=5,
                min_confidence=0.6
            ),
            'kalman_filter': KalmanFilterStrategy(
                lookback_period=50,
                prediction_threshold=0.02
            )
        }
        
        logger.info(f"✅ Initialized {len(self.strategies)} new strategies")
    
    def generate_sample_market_data(self, symbols: List[str], days: int = 100) -> Dict[str, pd.DataFrame]:
        """Generate sample market data for testing"""
        logger.info(f"📊 Generating sample market data for {len(symbols)} symbols...")
        
        market_data = {}
        base_date = datetime.now() - timedelta(days=days)
        
        for symbol in symbols:
            # Generate realistic price data
            np.random.seed(hash(symbol) % 1000)  # Consistent seed per symbol
            
            # Base price
            base_price = 100 + np.random.uniform(0, 200)
            
            # Generate price series with trend and noise
            trend = np.random.uniform(-0.001, 0.002)  # Daily trend
            volatility = np.random.uniform(0.01, 0.03)  # Daily volatility
            
            prices = [base_price]
            volumes = [1000000]
            
            for i in range(1, days):
                # Price movement
                daily_return = np.random.normal(trend, volatility)
                new_price = prices[-1] * (1 + daily_return)
                prices.append(new_price)
                
                # Volume (correlated with price movement)
                volume_change = np.random.normal(0, 0.3)
                new_volume = max(100000, volumes[-1] * (1 + volume_change))
                volumes.append(new_volume)
            
            # Create DataFrame
            dates = pd.date_range(base_date, periods=days, freq='D')
            df = pd.DataFrame({
                'Date': dates,
                'Open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
                'High': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in prices],
                'Low': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in prices],
                'Close': prices,
                'Volume': volumes
            })
            
            df.set_index('Date', inplace=True)
            market_data[symbol] = df
        
        logger.info(f"✅ Generated market data for {len(market_data)} symbols")
        return market_data
    
    async def demo_pairs_trading(self):
        """Demo pairs trading strategy"""
        logger.info("🔄 Demo: Pairs Trading Strategy")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
        market_data = self.generate_sample_market_data(symbols)
        
        strategy = self.strategies['pairs_trading']
        
        # Find correlated pairs
        pairs = strategy.find_correlated_pairs(symbols, market_data)
        logger.info(f"Found {len(pairs)} correlated pairs: {pairs}")
        
        # Generate signals for each pair
        for pair in pairs[:3]:  # Test first 3 pairs
            symbol1, symbol2 = pair
            signal = await strategy.generate_signal(symbol1, market_data[symbol1], market_data)
            
            if signal:
                logger.info(f"Pairs signal: {signal.symbol} {signal.action} "
                           f"(confidence: {signal.confidence:.3f})")
                logger.info(f"Pair details: {signal.metadata}")
    
    async def demo_vwap_strategy(self):
        """Demo VWAP strategy"""
        logger.info("📈 Demo: VWAP Strategy")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        market_data = self.generate_sample_market_data(symbols)
        
        strategy = self.strategies['vwap']
        
        for symbol in symbols:
            signal = await strategy.generate_signal(symbol, market_data[symbol])
            
            if signal:
                logger.info(f"VWAP signal: {signal.symbol} {signal.action} "
                           f"(confidence: {signal.confidence:.3f})")
                logger.info(f"VWAP details: {signal.metadata}")
    
    async def demo_cross_sectional_momentum(self):
        """Demo cross-sectional momentum strategy"""
        logger.info("📊 Demo: Cross-Sectional Momentum Strategy")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
        market_data = self.generate_sample_market_data(symbols)
        
        strategy = self.strategies['cross_sectional_momentum']
        
        # Generate signals for all symbols
        signals = []
        for symbol in symbols:
            signal = await strategy.generate_signal(symbol, market_data[symbol], market_data)
            if signal:
                signals.append(signal)
        
        logger.info(f"Generated {len(signals)} cross-sectional momentum signals")
        
        # Show rankings
        rankings = strategy.get_momentum_rankings()
        logger.info(f"Top performers: {rankings['top_performers']}")
        logger.info(f"Bottom performers: {rankings['bottom_performers']}")
    
    async def demo_ml_ensemble(self):
        """Demo ML ensemble strategy"""
        logger.info("🤖 Demo: ML Ensemble Strategy")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        market_data = self.generate_sample_market_data(symbols, days=200)  # More data for ML
        
        strategy = self.strategies['ml_ensemble']
        
        # Train models first
        await strategy.train_models(market_data)
        
        # Generate signals
        for symbol in symbols:
            signal = await strategy.generate_signal(symbol, market_data[symbol], market_data)
            
            if signal:
                logger.info(f"ML Ensemble signal: {signal.symbol} {signal.action} "
                           f"(confidence: {signal.confidence:.3f})")
                logger.info(f"Model performance: {signal.metadata['model_performance']}")
    
    async def demo_kalman_filter(self):
        """Demo Kalman filter strategy"""
        logger.info("🔍 Demo: Kalman Filter Strategy")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        market_data = self.generate_sample_market_data(symbols)
        
        strategy = self.strategies['kalman_filter']
        
        for symbol in symbols:
            signal = await strategy.generate_signal(symbol, market_data[symbol])
            
            if signal:
                logger.info(f"Kalman Filter signal: {signal.symbol} {signal.action} "
                           f"(confidence: {signal.confidence:.3f})")
                
                # Get filter stats
                stats = strategy.get_filter_stats(symbol)
                logger.info(f"Filter stats: {stats}")
    
    async def demo_strategy_comparison(self):
        """Compare all strategies on same data"""
        logger.info("⚖️ Demo: Strategy Comparison")
        
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        market_data = self.generate_sample_market_data(symbols)
        
        comparison_results = {}
        
        for strategy_name, strategy in self.strategies.items():
            logger.info(f"Testing {strategy_name}...")
            signals = []
            
            for symbol in symbols:
                signal = await strategy.generate_signal(symbol, market_data[symbol], market_data)
                if signal:
                    signals.append(signal)
            
            comparison_results[strategy_name] = {
                'signal_count': len(signals),
                'avg_confidence': np.mean([s.confidence for s in signals]) if signals else 0,
                'buy_signals': len([s for s in signals if s.action == 'BUY']),
                'sell_signals': len([s for s in signals if s.action == 'SELL'])
            }
        
        # Display comparison
        logger.info("Strategy Comparison Results:")
        for strategy_name, results in comparison_results.items():
            logger.info(f"{strategy_name}:")
            logger.info(f"  Signals: {results['signal_count']}")
            logger.info(f"  Avg Confidence: {results['avg_confidence']:.3f}")
            logger.info(f"  Buy/Sell: {results['buy_signals']}/{results['sell_signals']}")
    
    async def run_all_demos(self):
        """Run all strategy demos"""
        logger.info("🎯 Starting New Trading Strategies Demo")
        
        await self.initialize_strategies()
        
        # Run individual demos
        await self.demo_pairs_trading()
        await self.demo_vwap_strategy()
        await self.demo_cross_sectional_momentum()
        await self.demo_ml_ensemble()
        await self.demo_kalman_filter()
        
        # Run comparison
        await self.demo_strategy_comparison()
        
        logger.info("✅ New Trading Strategies Demo completed!")

async def main():
    """Main demo function"""
    demo = NewStrategiesDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 