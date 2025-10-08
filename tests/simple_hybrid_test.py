#!/usr/bin/env python3
"""
Simple Hybrid Strategy Test
Tests the hybrid strategy concept directly without complex backtest engine
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.append('src')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_15min_data(symbol: str, days: int = 1) -> pd.DataFrame:
    """Create mock 15-minute data for testing"""
    
    # Create 15-minute timestamps for the specified days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Generate 15-minute intervals
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15min')
    
    # Generate realistic price data
    np.random.seed(hash(symbol) % 2**32)
    base_price = 400 + np.random.uniform(50, 100)  # SPY-like prices
    
    data = []
    current_price = base_price
    
    for timestamp in timestamps:
        # Generate OHLC data
        price_change = np.random.normal(0, 0.002)  # 0.2% volatility
        current_price *= (1 + price_change)
        
        # Generate OHLC from current price
        volatility = abs(np.random.normal(0, 0.001))
        high = current_price * (1 + volatility)
        low = current_price * (1 - volatility)
        open_price = current_price + np.random.normal(0, 0.0005)
        close_price = current_price
        
        volume = int(np.random.uniform(1000000, 5000000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close_price,
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=timestamps)
    return df

def create_mock_daily_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """Create mock daily data for testing"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate daily timestamps
    timestamps = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate realistic price data
    np.random.seed(hash(symbol) % 2**32)
    base_price = 400 + np.random.uniform(50, 100)
    
    data = []
    current_price = base_price
    
    for timestamp in timestamps:
        # Generate daily price movement
        price_change = np.random.normal(0, 0.02)  # 2% daily volatility
        current_price *= (1 + price_change)
        
        # Generate OHLC from current price
        volatility = abs(np.random.normal(0, 0.01))
        high = current_price * (1 + volatility)
        low = current_price * (1 - volatility)
        open_price = current_price + np.random.normal(0, 0.005)
        close_price = current_price
        
        volume = int(np.random.uniform(50000000, 150000000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close_price,
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=timestamps)
    return df

async def test_hybrid_strategy():
    """Test the hybrid strategy with mock data"""
    
    logger.info("🚀 Testing Hybrid Strategy with Mock Data")
    logger.info("=" * 60)
    
    try:
        # Import the hybrid strategy
        from strategies.advanced.hybrid_options_strategy import HybridOptionsStrategy
        
        # Test configurations
        configurations = [
            {
                'name': 'Conservative Hybrid (95% Swing, 5% Day)',
                'swing_pct': 0.95,
                'day_trading_pct': 0.05,
                'enable_day_trading': False  # Start with swing only
            },
            {
                'name': 'Balanced Hybrid (90% Swing, 10% Day)',
                'swing_pct': 0.90,
                'day_trading_pct': 0.10,
                'enable_day_trading': False  # Start with swing only
            },
            {
                'name': 'Aggressive Hybrid (85% Swing, 15% Day)',
                'swing_pct': 0.85,
                'day_trading_pct': 0.15,
                'enable_day_trading': False  # Start with swing only
            }
        ]
        
        # Create test data
        symbols = ['SPY', 'AAPL', 'NVDA']
        
        logger.info(f"📊 Creating mock data for {len(symbols)} symbols...")
        
        # Create daily data for swing trading
        daily_data = {}
        for symbol in symbols:
            daily_data[symbol] = create_mock_daily_data(symbol, days=365)
            logger.info(f"   ✅ {symbol}: {len(daily_data[symbol])} daily records")
        
        # Create 15-minute data for day trading
        minute_data = {}
        for symbol in symbols:
            minute_data[symbol] = create_mock_15min_data(symbol, days=1)
            logger.info(f"   ✅ {symbol}: {len(minute_data[symbol])} 15-minute records")
        
        logger.info("=" * 60)
        
        # Test each configuration
        for config in configurations:
            logger.info(f"🔄 Testing {config['name']}...")
            
            try:
                # Initialize hybrid strategy
                hybrid_strategy = HybridOptionsStrategy(
                    swing_allocation_pct=config['swing_pct'],
                    day_trading_allocation_pct=config['day_trading_pct'],
                    enable_swing_trading=True,
                    enable_day_trading=config['enable_day_trading']
                )
                
                # Test signal generation for each symbol
                total_signals = 0
                swing_signals = 0
                day_signals = 0
                
                for symbol in symbols:
                    # Test with daily data (swing trading)
                    daily_signal = await hybrid_strategy.generate_signal(symbol, daily_data[symbol])
                    if daily_signal:
                        total_signals += 1
                        swing_signals += 1
                        logger.info(f"   📈 {symbol} swing signal: {daily_signal.action} @ ${daily_signal.price:.2f}")
                    
                    # Test with 15-minute data (day trading) - if enabled
                    if config['enable_day_trading']:
                        minute_signal = await hybrid_strategy.generate_signal(symbol, minute_data[symbol])
                        if minute_signal:
                            total_signals += 1
                            day_signals += 1
                            logger.info(f"   ⚡ {symbol} day signal: {minute_signal.action} @ ${minute_signal.price:.2f}")
                
                logger.info(f"   ✅ {config['name']}: {total_signals} signals ({swing_signals} swing, {day_signals} day)")
                logger.info(f"      Allocation: {config['swing_pct']:.1%} swing, {config['day_trading_pct']:.1%} day")
                
                # Get strategy stats
                stats = hybrid_strategy.get_strategy_stats()
                logger.info(f"      Strategy Stats: {stats['strategy_name']}")
                
            except Exception as e:
                logger.error(f"   ❌ {config['name']} failed: {e}")
                import traceback
                traceback.print_exc()
            
            logger.info("")
        
        logger.info("=" * 60)
        logger.info("✅ Hybrid strategy test completed!")
        
        # Summary
        logger.info(f"\n💡 Summary:")
        logger.info(f"   📊 Tested {len(configurations)} hybrid configurations")
        logger.info(f"   🎯 Symbols tested: {', '.join(symbols)}")
        logger.info(f"   📈 Daily data: {len(daily_data['SPY'])} records per symbol")
        logger.info(f"   ⏰ 15-minute data: {len(minute_data['SPY'])} records per symbol")
        logger.info(f"   🔄 All configurations use swing trading only (day trading disabled)")
        logger.info(f"   🚀 Next step: Enable day trading with real 15-minute data")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hybrid_strategy())

