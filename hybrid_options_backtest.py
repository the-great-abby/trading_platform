#!/usr/bin/env python3
"""
Hybrid Options Strategy Backtest
Combining 90% Swing Trading + 10% Day Trading on 15-minute charts
"""

import os
import sys
import logging
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
    """Run hybrid options strategy backtest"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Hybrid Options Strategy Backtest")
    logger.info("=" * 60)
    
    # Verify API key is loaded
    polygon_key = os.environ.get('POLYGON_API_KEY', 'NOT_SET')
    logger.info(f"🔑 Polygon API Key: {'✅ Loaded' if polygon_key != 'NOT_SET' and len(polygon_key) > 10 else '❌ Not loaded properly'}")
    logger.info(f"📊 Data Source: {'Real data via Polygon API' if polygon_key != 'NOT_SET' else 'Mock data'}")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    engine.initial_capital = 4000.0  # $4,000 starting capital
    
    # Initialize hybrid strategy
    hybrid_strategy = HybridOptionsStrategy(
        swing_allocation_pct=0.90,      # 90% swing trading
        day_trading_allocation_pct=0.10, # 10% day trading
        enable_swing_trading=True,       # Enable swing trading
        enable_day_trading=True          # Enable day trading
    )
    
    # Define symbols to test (high-performing, liquid options assets)
    symbols = ['SPY', 'QQQ', 'AAPL', 'NVDA']  # Start with fewer symbols for testing
    
    # Backtest configuration
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info(f"📊 Backtest Configuration:")
    logger.info(f"   Strategy: HybridOptionsStrategy")
    logger.info(f"   Swing Trading: 90% allocation (daily charts)")
    logger.info(f"   Day Trading: 10% allocation (15-minute charts)")
    logger.info(f"   Symbols: {', '.join(symbols)}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Capital: ${engine.initial_capital:,.2f}")
    logger.info("=" * 60)
    
    try:
        # Run the backtest
        logger.info("🔄 Running hybrid backtest...")
        results = await engine.run_backtest(
            strategies={'HybridOptionsStrategy': hybrid_strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get the result for our strategy
        result = results['HybridOptionsStrategy']
        
        logger.info("📈 HYBRID BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Strategy: {result.strategy}")
        logger.info(f"Total Return: {result.total_return_pct:.2f}%")
        logger.info(f"Final Value: ${result.final_capital:,.2f}")
        logger.info(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
        logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Win Rate: {result.win_rate:.2f}%")
        logger.info(f"Total Trades: {result.total_trades}")
        logger.info(f"Profitable Trades: {result.winning_trades}")
        logger.info(f"Losing Trades: {result.losing_trades}")
        
        if result.trades:
            logger.info(f"\n📊 Trade Summary:")
            logger.info(f"   Average Win: ${result.avg_win:,.2f}")
            logger.info(f"   Average Loss: ${result.avg_loss:,.2f}")
            
            # Analyze trade types
            swing_trades = [t for t in result.trades if 'swing_trading' in t.metadata.get('strategy_component', '')]
            day_trades = [t for t in result.trades if 'day_trading' in t.metadata.get('strategy_component', '')]
            
            logger.info(f"\n🎯 Strategy Component Analysis:")
            logger.info(f"   Swing Trades: {len(swing_trades)} trades")
            logger.info(f"   Day Trades: {len(day_trades)} trades")
            
            if swing_trades:
                swing_pnl = sum(t.pnl for t in swing_trades)
                logger.info(f"   Swing Trading P&L: ${swing_pnl:,.2f}")
            
            if day_trades:
                day_pnl = sum(t.pnl for t in day_trades)
                logger.info(f"   Day Trading P&L: ${day_pnl:,.2f}")
            
            logger.info(f"\n🔍 Recent Trades (Last 10):")
            for i, trade in enumerate(result.trades[-10:]):
                component = trade.metadata.get('strategy_component', 'unknown')
                logger.info(f"   {i+1}. {trade.symbol}: {trade.action} {trade.quantity:.4f} shares @ ${trade.price:.2f} | P&L: ${trade.pnl:.2f} | {component}")
        
        # Strategy statistics
        strategy_stats = hybrid_strategy.get_strategy_stats()
        logger.info(f"\n📊 Strategy Statistics:")
        logger.info(f"   Swing Allocation: {strategy_stats['swing_allocation_pct']:.1%}")
        logger.info(f"   Day Trading Allocation: {strategy_stats['day_trading_allocation_pct']:.1%}")
        
        if 'day_trading' in strategy_stats:
            day_stats = strategy_stats['day_trading']
            logger.info(f"   Day Trading Active Positions: {day_stats['active_positions']}")
            logger.info(f"   Max Holding Periods: {day_stats['max_holding_periods']} (4 hours)")
            logger.info(f"   Profit Target: {day_stats['profit_target']:.1%}")
            logger.info(f"   Stop Loss: {day_stats['stop_loss']:.1%}")
        
        logger.info("=" * 60)
        logger.info("✅ Hybrid backtest completed successfully!")
        
        # Performance comparison
        logger.info(f"\n🔄 Performance Comparison:")
        logger.info(f"   Previous (Swing Only): 313.56% return, 31 trades")
        logger.info(f"   Current (Hybrid): {result.total_return_pct:.2f}% return, {result.total_trades} trades")
        
        improvement = result.total_return_pct - 313.56
        if improvement > 0:
            logger.info(f"   Improvement: +{improvement:.2f} percentage points")
        else:
            logger.info(f"   Change: {improvement:.2f} percentage points")
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

