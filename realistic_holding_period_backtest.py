#!/usr/bin/env python3
"""
Realistic Holding Period Backtest
Tests the MultiStrategyEnsemble with proper time-based exits
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# Disable LLM evaluation for backtesting BEFORE any imports
os.environ['ENABLE_LLM_EVALUATION'] = 'false'

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.backtesting.engine.backtest_engine import BacktestEngine, BacktestResult
from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble
from src.strategies.strategy_registry import StrategyRegistry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_realistic_backtest():
    """Run backtest with realistic holding periods"""
    
    logger.info("🚀 Starting Realistic Holding Period Backtest...")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Configure for realistic trading
    engine.initial_capital = 4000.0
    engine.cash_reserve_pct = 0.05  # 5% cash reserve
    engine.max_position_size_pct = 0.20  # 20% max position size
    engine.stock_allocation_pct = 0.20  # 20% stocks
    engine.options_allocation_pct = 0.75  # 75% options
    engine.options_day_trading_pct = 0.25  # 25% day trading
    engine.options_swing_trading_pct = 0.50  # 50% swing trading
    
    # Use real data
    engine.use_real_data = True
    
    # Symbols to test
    symbols = ['SPY', 'AAPL', 'NVDA']
    
    # Date range for 2024
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info(f"📊 Backtest Configuration:")
    logger.info(f"   Capital: ${engine.initial_capital:,.2f}")
    logger.info(f"   Cash Reserve: {engine.cash_reserve_pct:.1%}")
    logger.info(f"   Max Position: {engine.max_position_size_pct:.1%}")
    logger.info(f"   Stock Allocation: {engine.stock_allocation_pct:.1%}")
    logger.info(f"   Options Allocation: {engine.options_allocation_pct:.1%}")
    logger.info(f"   Day Trading: {engine.options_day_trading_pct:.1%}")
    logger.info(f"   Swing Trading: {engine.options_swing_trading_pct:.1%}")
    logger.info(f"   Symbols: {', '.join(symbols)}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Real Data: {engine.use_real_data}")
    
    # Run backtest
    logger.info("🎯 Running backtest...")
    result = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=['MultiStrategyEnsemble']
    )
    
    # Display results
    logger.info("📈 BACKTEST RESULTS:")
    logger.info(f"   Result Type: {type(result)}")
    
    if isinstance(result, dict):
        logger.info(f"   Result Keys: {list(result.keys())}")
        
        # Handle nested results structure
        strategy_result = result.get('MultiStrategyEnsemble', {})
        if isinstance(strategy_result, list) and len(strategy_result) > 0:
            strategy_result = strategy_result[0]
        
        initial_capital = strategy_result.get('initial_capital', 4000) if hasattr(strategy_result, 'get') else getattr(strategy_result, 'initial_capital', 4000)
        final_capital = strategy_result.get('final_capital', initial_capital) if hasattr(strategy_result, 'get') else getattr(strategy_result, 'final_capital', initial_capital)
        total_trades = len(strategy_result.get('trades', [])) if hasattr(strategy_result, 'get') else getattr(strategy_result, 'total_trades', 0)
        
        logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"   Final Capital: ${final_capital:,.2f}")
        logger.info(f"   Total Return: {((final_capital - initial_capital) / initial_capital):.2%}")
        logger.info(f"   Total Trades: {total_trades}")
        
        # Calculate win rate from trades (match BacktestEngine logic - only count SELL trades)
        trades = strategy_result.get('trades', []) if hasattr(strategy_result, 'get') else getattr(strategy_result, 'trades', [])
        if trades:
            # Only count SELL trades for win rate (matching BacktestEngine logic)
            sell_trades = [trade for trade in trades if getattr(trade, 'action', '') == 'SELL']
            winning_trades = sum(1 for trade in sell_trades if getattr(trade, 'pnl', 0) > 0)
            win_rate = winning_trades / len(sell_trades) if sell_trades else 0
            logger.info(f"   Win Rate: {win_rate:.2%} (based on {len(sell_trades)} SELL trades)")
        
        logger.info(f"   Max Drawdown: {getattr(strategy_result, 'max_drawdown', 0):.2%}")
        logger.info(f"   Sharpe Ratio: {getattr(strategy_result, 'sharpe_ratio', 0):.2f}")
    else:
        logger.info(f"   Initial Capital: ${result.initial_capital:,.2f}")
        logger.info(f"   Final Capital: ${result.final_capital:,.2f}")
        logger.info(f"   Total Return: {result.total_return:.2%}")
        logger.info(f"   Annualized Return: {result.annualized_return:.2%}")
        logger.info(f"   Total Trades: {result.total_trades}")
        logger.info(f"   Win Rate: {result.win_rate:.2%}")
        logger.info(f"   Max Drawdown: {result.max_drawdown:.2%}")
        logger.info(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    # Strategy performance breakdown
    if hasattr(result, 'strategy_performance') and result.strategy_performance:
        logger.info("🎯 Strategy Performance:")
        for strategy_name, perf in result.strategy_performance.items():
            logger.info(f"   {strategy_name}:")
            logger.info(f"     Trades: {perf.get('total_trades', 0)}")
            logger.info(f"     Win Rate: {perf.get('win_rate', 0):.2%}")
            logger.info(f"     Return: {perf.get('total_return', 0):.2%}")
    
    # Trade analysis
    if hasattr(result, 'trades') and result.trades:
        logger.info("📊 Trade Analysis:")
        
        # Calculate average holding period
        holding_periods = []
        for trade in result.trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                entry = trade['entry_date']
                exit = trade['exit_date']
                if isinstance(entry, str):
                    from datetime import datetime
                    entry = datetime.strptime(entry, '%Y-%m-%d')
                if isinstance(exit, str):
                    from datetime import datetime
                    exit = datetime.strptime(exit, '%Y-%m-%d')
                holding_periods.append((exit - entry).days)
        
        if holding_periods:
            avg_holding = sum(holding_periods) / len(holding_periods)
            max_holding = max(holding_periods)
            min_holding = min(holding_periods)
            
            logger.info(f"   Average Holding Period: {avg_holding:.1f} days")
            logger.info(f"   Max Holding Period: {max_holding} days")
            logger.info(f"   Min Holding Period: {min_holding} days")
            
            # Show distribution
            short_term = sum(1 for h in holding_periods if h <= 7)
            medium_term = sum(1 for h in holding_periods if 7 < h <= 21)
            long_term = sum(1 for h in holding_periods if h > 21)
            
            logger.info(f"   Short-term (≤7 days): {short_term} trades ({short_term/len(holding_periods):.1%})")
            logger.info(f"   Medium-term (8-21 days): {medium_term} trades ({medium_term/len(holding_periods):.1%})")
            logger.info(f"   Long-term (>21 days): {long_term} trades ({long_term/len(holding_periods):.1%})")
    
    logger.info("✅ Backtest completed successfully!")
    return result

if __name__ == "__main__":
    asyncio.run(run_realistic_backtest())
