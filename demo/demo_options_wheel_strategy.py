#!/usr/bin/env python3
"""
Options Wheel Strategy Demo
==========================
Demonstrates the options wheel strategy implementation with realistic market simulation.

The options wheel strategy combines:
1. Cash-secured put selling for income and stock acquisition
2. Covered call selling for additional income on owned positions

This demo shows:
- Strategy initialization and configuration
- Market condition analysis
- Signal generation for both put and call phases
- Wheel state management
- Performance tracking
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies.options.options_wheel_strategy import OptionsWheelStrategy, WheelPhase
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_trading_logger()

class OptionsWheelDemo:
    """
    Demo class for the Options Wheel Strategy
    """
    
    def __init__(self):
        self.strategy = OptionsWheelStrategy(
            # Put Phase Configuration
            put_days_to_expiration=30,
            put_profit_target_pct=0.7,
            put_stop_loss_pct=1.5,
            put_min_delta=-0.7,
            put_max_delta=-0.3,
            put_min_premium_pct=0.015,
            
            # Call Phase Configuration
            call_days_to_expiration=30,
            call_profit_target_pct=0.7,
            call_stop_loss_pct=1.5,
            call_min_delta=0.3,
            call_max_delta=0.7,
            call_min_premium_pct=0.02,
            
            # General Configuration
            max_risk_per_trade=0.02,
            max_cash_utilization=0.8,
            min_dte=21,
            max_dte=45,
            
            # Wheel-specific Configuration
            max_wheel_cycles=5,
            min_cycle_interval_days=7,
            assignment_buffer_days=3,
            
            # Stock Selection Criteria
            min_stock_price=50.0,
            max_stock_price=500.0,
            min_volume=1000000,
            min_options_volume=100
        )
        
        # Demo symbols
        self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        # Demo results
        self.demo_results = []
    
    def generate_sample_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Generate sample market data for demo"""
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        # Generate price data
        base_price = np.random.uniform(100, 300)
        returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate dates
        end_date = datetime.now()
        dates = [end_date - timedelta(days=i) for i in range(days, 0, -1)]
        
        # Create DataFrame
        data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, days),
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices]
        })
        
        # Add technical indicators
        data['sma_20'] = data['close'].rolling(20).mean()
        data['sma_50'] = data['close'].rolling(50).mean()
        
        # RSI calculation
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        data['bb_middle'] = data['close'].rolling(20).mean()
        bb_std = data['close'].rolling(20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        
        return data
    
    async def run_wheel_demo(self):
        """Run the options wheel strategy demo"""
        logger.info("🎯 Starting Options Wheel Strategy Demo")
        logger.info("=" * 50)
        
        # Display strategy configuration
        self.display_strategy_config()
        
        # Test each symbol
        for symbol in self.symbols:
            logger.info(f"\n📊 Testing {symbol}")
            logger.info("-" * 30)
            
            # Generate sample data
            data = self.generate_sample_data(symbol)
            
            # Test eligibility
            current_price = data['close'].iloc[-1]
            volume = data['volume'].iloc[-1]
            
            is_eligible = self.strategy.is_eligible_for_wheel(
                symbol, current_price, volume, 1000
            )
            
            logger.info(f"Eligibility: {'✅ Eligible' if is_eligible else '❌ Not Eligible'}")
            logger.info(f"Current Price: ${current_price:.2f}")
            logger.info(f"Volume: {volume:,}")
            
            if not is_eligible:
                continue
            
            # Calculate scores
            technical_score = self.strategy.calculate_technical_score(data)
            volatility_score = self.strategy.calculate_volatility_score(data)
            momentum_score = self.strategy.calculate_momentum_score(data)
            
            logger.info(f"Technical Score: {technical_score:.3f}")
            logger.info(f"Volatility Score: {volatility_score:.3f}")
            logger.info(f"Momentum Score: {momentum_score:.3f}")
            
            # Generate signal
            signal = await self.strategy.generate_signal(symbol, data)
            
            if signal:
                logger.info(f"🎯 Signal Generated: {signal.action}")
                logger.info(f"   Strike: ${signal.price:.2f}")
                logger.info(f"   Confidence: {signal.confidence:.3f}")
                logger.info(f"   Phase: {signal.metadata.get('phase', 'unknown')}")
                logger.info(f"   Expected Premium: ${signal.metadata.get('expected_premium', 0):.2f}")
                
                # Store result
                self.demo_results.append({
                    'symbol': symbol,
                    'signal': signal,
                    'technical_score': technical_score,
                    'volatility_score': volatility_score,
                    'momentum_score': momentum_score,
                    'current_price': current_price
                })
            else:
                logger.info("❌ No signal generated")
        
        # Display summary
        self.display_demo_summary()
        
        # Test wheel state management
        self.test_wheel_state_management()
    
    def display_strategy_config(self):
        """Display strategy configuration"""
        logger.info("⚙️  Strategy Configuration:")
        logger.info(f"   Put Phase - DTE: {self.strategy.put_days_to_expiration}, "
                   f"Delta Range: {self.strategy.put_min_delta} to {self.strategy.put_max_delta}")
        logger.info(f"   Call Phase - DTE: {self.strategy.call_days_to_expiration}, "
                   f"Delta Range: {self.strategy.call_min_delta} to {self.strategy.call_max_delta}")
        logger.info(f"   Max Risk per Trade: {self.strategy.max_risk_per_trade:.1%}")
        logger.info(f"   Max Cash Utilization: {self.strategy.max_cash_utilization:.1%}")
        logger.info(f"   Max Wheel Cycles: {self.strategy.max_wheel_cycles}")
        logger.info(f"   Min Cycle Interval: {self.strategy.min_cycle_interval_days} days")
    
    def display_demo_summary(self):
        """Display demo summary"""
        logger.info("\n📈 Demo Summary")
        logger.info("=" * 30)
        
        total_signals = len(self.demo_results)
        put_signals = sum(1 for r in self.demo_results 
                         if r['signal'].metadata.get('phase') == 'put_phase')
        call_signals = sum(1 for r in self.demo_results 
                          if r['signal'].metadata.get('phase') == 'call_phase')
        
        logger.info(f"Total Signals Generated: {total_signals}")
        logger.info(f"Put Phase Signals: {put_signals}")
        logger.info(f"Call Phase Signals: {call_signals}")
        
        if self.demo_results:
            avg_confidence = np.mean([r['signal'].confidence for r in self.demo_results])
            avg_technical = np.mean([r['technical_score'] for r in self.demo_results])
            avg_volatility = np.mean([r['volatility_score'] for r in self.demo_results])
            avg_momentum = np.mean([r['momentum_score'] for r in self.demo_results])
            
            logger.info(f"Average Confidence: {avg_confidence:.3f}")
            logger.info(f"Average Technical Score: {avg_technical:.3f}")
            logger.info(f"Average Volatility Score: {avg_volatility:.3f}")
            logger.info(f"Average Momentum Score: {avg_momentum:.3f}")
            
            # Show top performers
            sorted_results = sorted(self.demo_results, 
                                  key=lambda x: x['signal'].confidence, 
                                  reverse=True)
            
            logger.info("\n🏆 Top Performing Signals:")
            for i, result in enumerate(sorted_results[:3], 1):
                signal = result['signal']
                logger.info(f"   {i}. {result['symbol']}: {signal.action} @ ${signal.price:.2f} "
                           f"(Confidence: {signal.confidence:.3f})")
    
    def test_wheel_state_management(self):
        """Test wheel state management functionality"""
        logger.info("\n🔄 Testing Wheel State Management")
        logger.info("-" * 35)
        
        # Test put assignment
        test_symbol = "AAPL"
        logger.info(f"Testing put assignment for {test_symbol}")
        
        # Simulate put assignment
        self.strategy.handle_assignment(test_symbol, 150.0, 100)
        
        position = self.strategy.get_wheel_position(test_symbol)
        logger.info(f"Shares owned: {position['shares_owned']}")
        logger.info(f"Average cost: ${position['average_cost']:.2f}")
        logger.info(f"Phase: {position['phase']}")
        
        # Test call assignment
        logger.info(f"Testing call assignment for {test_symbol}")
        self.strategy.handle_call_assignment(test_symbol, 160.0, 100)
        
        position = self.strategy.get_wheel_position(test_symbol)
        logger.info(f"Shares remaining: {position['shares_owned']}")
        logger.info(f"Total income: ${position['total_income']:.2f}")
        logger.info(f"Cycles completed: {position['cycles_completed']}")
        logger.info(f"Phase: {position['phase']}")
        
        # Display strategy info
        strategy_info = self.strategy.get_strategy_info()
        logger.info(f"\n📊 Strategy Info:")
        logger.info(f"   Active Wheels: {strategy_info['active_wheels']}")
        logger.info(f"   Total Cycles: {strategy_info['total_cycles']}")
        logger.info(f"   Total Income: ${strategy_info['total_income']:.2f}")
        logger.info(f"   Phase Distribution: {strategy_info['phase_distribution']}")

async def main():
    """Main demo function"""
    demo = OptionsWheelDemo()
    await demo.run_wheel_demo()
    
    logger.info("\n✅ Options Wheel Strategy Demo Complete!")
    logger.info("The strategy is ready for integration into your trading system.")

if __name__ == "__main__":
    asyncio.run(main())


