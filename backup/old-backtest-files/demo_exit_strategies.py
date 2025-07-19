#!/usr/bin/env python3
"""
Demo Exit Strategies
===================
Demonstrates the enhanced exit strategies and their impact on trading performance.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from src.strategies.enhanced_entry_exit_strategy import EnhancedEntryExitStrategy
from src.strategies.exit_strategies import (
    FibonacciExitStrategy,
    MultiSignalExitStrategy,
    DynamicStopLossStrategy,
    TimeBasedExitStrategy,
    EnhancedExitManager
)
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class ExitStrategiesDemo:
    """Demo class for exit strategies"""
    
    def __init__(self):
        self.strategies = {}
        self.market_data = {}
        
    def generate_sample_market_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Generate sample market data for testing"""
        logger.info(f"📊 Generating sample market data for {symbol}...")
        
        # Generate realistic price data with trends and volatility
        np.random.seed(hash(symbol) % 1000)
        
        base_price = 100 + np.random.uniform(0, 200)
        dates = pd.date_range(datetime.now() - timedelta(days=days), periods=days, freq='D')
        
        # Create price series with trends and volatility
        prices = [base_price]
        volumes = [1000000]
        
        for i in range(1, days):
            # Add trend and volatility
            trend = np.random.uniform(-0.02, 0.03)  # -2% to +3% daily
            volatility = np.random.uniform(0.01, 0.04)  # 1-4% volatility
            
            # Price movement
            price_change = np.random.normal(trend, volatility)
            new_price = prices[-1] * (1 + price_change)
            prices.append(new_price)
            
            # Volume (correlated with price movement)
            volume_change = np.random.normal(0, 0.3)
            new_volume = max(100000, volumes[-1] * (1 + volume_change))
            volumes.append(new_volume)
        
        # Create OHLC data
        data = []
        for i in range(len(prices)):
            open_price = prices[i] * (1 + np.random.uniform(-0.01, 0.01))
            high_price = max(open_price, prices[i]) * (1 + abs(np.random.uniform(0, 0.02)))
            low_price = min(open_price, prices[i]) * (1 - abs(np.random.uniform(0, 0.02)))
            close_price = prices[i]
            
            data.append({
                'Date': dates[i],
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volumes[i]
            })
        
        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        
        logger.info(f"✅ Generated {len(df)} data points for {symbol}")
        return df
    
    async def demo_fibonacci_exit_strategy(self):
        """Demo Fibonacci exit strategy"""
        logger.info("🔢 Demo: Fibonacci Exit Strategy")
        
        symbol = "AAPL"
        data = self.generate_sample_market_data(symbol)
        
        strategy = FibonacciExitStrategy()
        
        # Simulate a long position
        entry_price = 150.0
        swing_high = 160.0
        swing_low = 140.0
        position_type = "LONG"
        
        # Calculate Fibonacci targets
        targets = strategy.calculate_fibonacci_targets(entry_price, swing_high, swing_low, position_type)
        
        logger.info(f"Fibonacci targets for {symbol}:")
        for target_name, target_price in targets.items():
            logger.info(f"  {target_name}: ${target_price:.2f}")
        
        # Test exit signals at different prices
        test_prices = [155, 165, 175, 185, 195]
        
        for price in test_prices:
            exit_signal = strategy.get_exit_signal(price, entry_price, targets, position_type)
            if exit_signal:
                logger.info(f"Exit signal at ${price}: {exit_signal.reason.value} "
                           f"(confidence: {exit_signal.confidence:.2f})")
    
    async def demo_multi_signal_exit_strategy(self):
        """Demo multi-signal exit strategy"""
        logger.info("📊 Demo: Multi-Signal Exit Strategy")
        
        symbol = "MSFT"
        data = self.generate_sample_market_data(symbol)
        
        strategy = MultiSignalExitStrategy()
        
        # Test exit signals for different scenarios
        scenarios = [
            {"position_type": "LONG", "description": "Overbought RSI + Bearish MACD"},
            {"position_type": "SHORT", "description": "Oversold RSI + Bullish MACD"},
            {"position_type": "LONG", "description": "Volume spike + Price decline"}
        ]
        
        for scenario in scenarios:
            logger.info(f"Testing scenario: {scenario['description']}")
            
            # Modify data to create specific conditions
            test_data = data.copy()
            if scenario['position_type'] == "LONG":
                # Create overbought conditions
                test_data.loc[test_data.index[-1], 'Close'] = test_data['Close'].iloc[-2] * 1.05
                test_data.loc[test_data.index[-1], 'Volume'] = test_data['Volume'].iloc[-2] * 2.5
            
            entry_price = test_data['Close'].iloc[-10]  # Entry 10 days ago
            
            exit_signal = strategy.get_exit_signal(test_data, scenario['position_type'], entry_price)
            
            if exit_signal:
                logger.info(f"  Exit signal: {exit_signal.action} at ${exit_signal.price:.2f} "
                           f"(confidence: {exit_signal.confidence:.2f})")
                logger.info(f"  Reason: {exit_signal.reason.value}")
            else:
                logger.info("  No exit signal generated")
    
    async def demo_dynamic_stop_loss_strategy(self):
        """Demo dynamic stop-loss strategy"""
        logger.info("🛡️ Demo: Dynamic Stop-Loss Strategy")
        
        symbol = "GOOGL"
        data = self.generate_sample_market_data(symbol)
        
        strategy = DynamicStopLossStrategy(atr_period=14, atr_multiplier=2.0)
        
        # Calculate ATR
        atr = strategy.calculate_atr(data)
        current_atr = atr.iloc[-1]
        
        logger.info(f"Current ATR: {current_atr:.4f}")
        
        # Test for long and short positions
        entry_price = data['Close'].iloc[-1]
        
        for position_type in ["LONG", "SHORT"]:
            stop_loss = strategy.calculate_stop_loss(entry_price, position_type, current_atr)
            
            logger.info(f"{position_type} position:")
            logger.info(f"  Entry price: ${entry_price:.2f}")
            logger.info(f"  Stop loss: ${stop_loss:.2f}")
            logger.info(f"  Distance: {abs(entry_price - stop_loss) / entry_price * 100:.2f}%")
            
            # Test stop-loss hit
            test_price = stop_loss * (0.99 if position_type == "LONG" else 1.01)
            exit_signal = strategy.get_exit_signal(test_price, stop_loss, position_type)
            
            if exit_signal:
                logger.info(f"  Stop-loss triggered at ${test_price:.2f}")
    
    async def demo_time_based_exit_strategy(self):
        """Demo time-based exit strategy"""
        logger.info("⏰ Demo: Time-Based Exit Strategy")
        
        strategy = TimeBasedExitStrategy(
            max_holding_days=30,
            min_holding_days=1,
            profit_time_decay=True
        )
        
        # Test different holding periods
        entry_date = datetime.now() - timedelta(days=20)
        entry_price = 100.0
        
        test_scenarios = [
            {"current_date": datetime.now(), "current_price": 110.0, "position_type": "LONG", "description": "Profitable position after 20 days"},
            {"current_date": datetime.now(), "current_price": 90.0, "position_type": "LONG", "description": "Losing position after 20 days"},
            {"current_date": datetime.now() + timedelta(days=15), "current_price": 105.0, "position_type": "LONG", "description": "Position at max holding period"}
        ]
        
        for scenario in test_scenarios:
            logger.info(f"Testing: {scenario['description']}")
            
            exit_signal = strategy.get_exit_signal(
                entry_date,
                scenario['current_date'],
                scenario['current_price'],
                entry_price,
                scenario['position_type']
            )
            
            if exit_signal:
                holding_days = (scenario['current_date'] - entry_date).days
                logger.info(f"  Exit signal: {exit_signal.action} after {holding_days} days")
                logger.info(f"  Reason: {exit_signal.reason.value}")
                logger.info(f"  Confidence: {exit_signal.confidence:.2f}")
            else:
                holding_days = (scenario['current_date'] - entry_date).days
                logger.info(f"  No exit signal after {holding_days} days")
    
    async def demo_enhanced_exit_manager(self):
        """Demo the comprehensive exit manager"""
        logger.info("🎯 Demo: Enhanced Exit Manager")
        
        symbol = "TSLA"
        data = self.generate_sample_market_data(symbol)
        
        manager = EnhancedExitManager()
        
        # Simulate a position
        entry_price = 200.0
        entry_date = datetime.now() - timedelta(days=10)
        position_type = "LONG"
        swing_high = 220.0
        swing_low = 180.0
        
        # Test exit signal
        exit_signal = manager.get_exit_signal(
            data=data,
            entry_price=entry_price,
            entry_date=entry_date,
            position_type=position_type,
            swing_high=swing_high,
            swing_low=swing_low
        )
        
        if exit_signal:
            logger.info(f"Exit signal generated:")
            logger.info(f"  Action: {exit_signal.action}")
            logger.info(f"  Price: ${exit_signal.price:.2f}")
            logger.info(f"  Reason: {exit_signal.reason.value}")
            logger.info(f"  Confidence: {exit_signal.confidence:.2f}")
            
            if exit_signal.metadata:
                logger.info(f"  Metadata: {exit_signal.metadata}")
        else:
            logger.info("No exit signal generated")
        
        # Get exit targets
        targets = manager.get_exit_targets(entry_price, swing_high, swing_low, position_type)
        
        logger.info(f"Exit targets for {symbol}:")
        for target_name, target_price in targets.items():
            logger.info(f"  {target_name}: ${target_price:.2f}")
    
    async def demo_enhanced_entry_exit_strategy(self):
        """Demo the complete enhanced entry-exit strategy"""
        logger.info("🚀 Demo: Enhanced Entry-Exit Strategy")
        
        symbol = "NVDA"
        data = self.generate_sample_market_data(symbol)
        
        strategy = EnhancedEntryExitStrategy(
            entry_confidence_threshold=0.5,
            exit_confidence_threshold=0.4
        )
        
        # Generate signals over time
        signals = []
        for i in range(20, len(data)):
            current_data = data.iloc[:i+1]
            signal = await strategy.generate_signal(symbol, current_data)
            
            if signal:
                signals.append(signal)
                logger.info(f"Signal {len(signals)}: {signal.action} at ${signal.price:.2f} "
                           f"(confidence: {signal.confidence:.2f})")
                
                if signal.metadata.get('signal_type') == 'entry':
                    logger.info(f"  Entry signals: {signal.metadata.get('entry_signals', [])}")
                    logger.info(f"  Exit targets: {len(signal.metadata.get('exit_targets', {}))} targets")
                elif signal.metadata.get('signal_type') == 'exit':
                    logger.info(f"  Exit reason: {signal.metadata.get('exit_reason', 'unknown')}")
                    logger.info(f"  P&L: ${signal.metadata.get('pnl', 0):.2f}")
        
        logger.info(f"Generated {len(signals)} total signals")
        
        # Get strategy summary
        strategy_info = strategy.get_strategy_info()
        logger.info(f"Strategy info: {strategy_info}")
        
        position_summary = strategy.get_position_summary()
        logger.info(f"Position summary: {position_summary}")
    
    async def run_all_demos(self):
        """Run all exit strategy demos"""
        logger.info("🎯 Starting Exit Strategies Demo")
        
        # Run individual demos
        await self.demo_fibonacci_exit_strategy()
        await self.demo_multi_signal_exit_strategy()
        await self.demo_dynamic_stop_loss_strategy()
        await self.demo_time_based_exit_strategy()
        await self.demo_enhanced_exit_manager()
        await self.demo_enhanced_entry_exit_strategy()
        
        logger.info("✅ Exit Strategies Demo completed!")

async def main():
    """Main demo function"""
    demo = ExitStrategiesDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 