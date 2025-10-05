#!/usr/bin/env python3
"""
Hybrid Strategy Test - Simulated 15-minute data for testing
This tests the hybrid strategy concept using daily data for both components
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the path
sys.path.append('src')

# Set up environment variables to disable AI services and enable real data
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'
os.environ['DISABLE_LLM_STRATEGIES'] = 'true'
os.environ['DISABLE_AI_STRATEGIES'] = 'true'
os.environ['ENABLE_LLM_EVALUATION'] = 'false'

# Enable real market data
os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
os.environ['DATABASE_ONLY'] = 'false'  # Use Polygon API for real data
os.environ['USE_MOCK_DATA'] = 'false'

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.advanced.hybrid_options_strategy import HybridOptionsStrategy

async def main():
    """Run hybrid strategy test with simulated 15-minute data"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Hybrid Strategy Test")
    logger.info("=" * 60)
    
    # Verify API key is loaded
    polygon_key = os.environ.get('POLYGON_API_KEY', 'NOT_SET')
    logger.info(f"🔑 Polygon API Key: {'✅ Loaded' if polygon_key != 'NOT_SET' and len(polygon_key) > 10 else '❌ Not loaded properly'}")
    logger.info(f"📊 Data Source: {'Real data via Polygon API' if polygon_key != 'NOT_SET' else 'Mock data'}")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    engine.initial_capital = 4000.0  # $4,000 starting capital
    
    # Test different hybrid configurations
    configurations = [
        {
            'name': 'Conservative Hybrid',
            'swing_pct': 0.95,
            'day_trading_pct': 0.05,
            'enable_day_trading': False  # Start with swing only
        },
        {
            'name': 'Balanced Hybrid', 
            'swing_pct': 0.90,
            'day_trading_pct': 0.10,
            'enable_day_trading': False  # Still swing only for now
        },
        {
            'name': 'Aggressive Hybrid',
            'swing_pct': 0.85,
            'day_trading_pct': 0.15,
            'enable_day_trading': False  # Still swing only for now
        }
    ]
    
    # Define symbols to test
    symbols = ['SPY', 'AAPL', 'NVDA']  # Start with fewer symbols for testing
    
    # Backtest configuration
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info(f"📊 Test Configuration:")
    logger.info(f"   Symbols: {', '.join(symbols)}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Capital: ${engine.initial_capital:,.2f}")
    logger.info(f"   Configurations: {len(configurations)}")
    logger.info("=" * 60)
    
    results = {}
    
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
            
            # Run the backtest
            backtest_results = await engine.run_backtest(
                strategies={'HybridOptionsStrategy': hybrid_strategy},
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get the result for our strategy
            result = backtest_results['HybridOptionsStrategy']
            results[config['name']] = result
            
            logger.info(f"✅ {config['name']} completed")
            logger.info(f"   Total Return: {result.total_return_pct:.2f}%")
            logger.info(f"   Final Value: ${result.final_capital:,.2f}")
            logger.info(f"   Total Trades: {result.total_trades}")
            logger.info(f"   Win Rate: {result.win_rate:.2f}%")
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ {config['name']} failed: {e}")
            continue
    
    # Compare results
    logger.info("📈 HYBRID STRATEGY COMPARISON")
    logger.info("=" * 60)
    
    if results:
        # Find best performing configuration
        best_config = max(results.items(), key=lambda x: x[1].total_return_pct)
        
        logger.info(f"🏆 Best Performance: {best_config[0]}")
        logger.info(f"   Return: {best_config[1].total_return_pct:.2f}%")
        logger.info(f"   Trades: {best_config[1].total_trades}")
        logger.info(f"   Win Rate: {best_config[1].win_rate:.2f}%")
        logger.info("")
        
        # Compare all configurations
        logger.info("📊 All Configurations:")
        for name, result in results.items():
            logger.info(f"   {name}:")
            logger.info(f"     Return: {result.total_return_pct:.2f}%")
            logger.info(f"     Trades: {result.total_trades}")
            logger.info(f"     Win Rate: {result.win_rate:.2f}%")
            logger.info(f"     Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info("")
        
        # Compare with baseline (pure swing trading)
        baseline_return = 313.56  # Our previous best
        logger.info(f"🔄 Comparison with Baseline (Pure Swing):")
        logger.info(f"   Baseline Return: {baseline_return:.2f}%")
        
        for name, result in results.items():
            improvement = result.total_return_pct - baseline_return
            logger.info(f"   {name}: {result.total_return_pct:.2f}% ({improvement:+.2f}%)")
        
        logger.info("=" * 60)
        logger.info("✅ Hybrid strategy test completed!")
        
        # Recommendations
        logger.info(f"\n💡 Recommendations:")
        if best_config[1].total_return_pct > baseline_return:
            logger.info(f"   ✅ {best_config[0]} outperforms baseline by {best_config[1].total_return_pct - baseline_return:.2f}%")
        else:
            logger.info(f"   ⚠️ All configurations underperformed baseline")
        
        logger.info(f"   🎯 Next step: Enable day trading component with real 15-minute data")
        logger.info(f"   📊 Current: Testing allocation splits with swing trading only")
        
    else:
        logger.error("❌ No successful backtests completed")

if __name__ == "__main__":
    asyncio.run(main())

