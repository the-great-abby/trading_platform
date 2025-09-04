#!/usr/bin/env python3
"""
Single Options Strategy Backtest
===============================
Runs a backtest for a single options strategy with configurable parameters.
Useful for testing and tuning individual options strategies.
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger

# Setup logging
logger = get_trading_logger()
logger = logging.getLogger(__name__)

async def run_single_options_strategy_backtest(strategy_name: str, 
                                              symbols: List[str] = None,
                                              start_date: str = "2023-01-01",
                                              end_date: str = "2024-12-31",
                                              initial_capital: float = 1000000):
    """Run backtest for a single options strategy"""
    
    if symbols is None:
        symbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'XLF']
    
    logger.info(f"🚀 Starting Single Options Strategy Backtest: {strategy_name}")
    logger.info(f"📊 Configuration:")
    logger.info(f"   Strategy: {strategy_name}")
    logger.info(f"   Symbols: {', '.join(symbols)}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Run backtest
    try:
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=[strategy_name]
        )
        
        if results and strategy_name in results:
            result = results[strategy_name]
            
            logger.info(f"📈 {strategy_name} Results:")
            logger.info(f"   Total Return: {result.total_return_pct:.2f}%")
            logger.info(f"   Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
            logger.info(f"   Total Trades: {result.total_trades}")
            logger.info(f"   Winning Trades: {result.winning_trades}")
            logger.info(f"   Losing Trades: {result.losing_trades}")
            logger.info(f"   Win Rate: {result.win_rate*100:.1f}%")
            logger.info(f"   Profit Factor: {result.profit_factor:.2f}")
            logger.info(f"   Avg Win: ${result.avg_win:,.2f}")
            logger.info(f"   Avg Loss: ${result.avg_loss:,.2f}")
            
            # Store results
            await engine.store_results(
                results=results,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                database_only=True,
                backtest_name=f"single_options_{strategy_name.lower()}"
            )
            
            logger.info("✅ Single options strategy backtest completed successfully!")
            return result
            
        else:
            logger.error(f"❌ No results returned for {strategy_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error running {strategy_name}: {e}")
        return None

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Run single options strategy backtest')
    parser.add_argument('strategy', help='Name of the options strategy to test')
    parser.add_argument('--symbols', nargs='+', default=['SPY', 'QQQ', 'IWM', 'DIA', 'XLF'],
                       help='List of symbols to test (default: SPY QQQ IWM DIA XLF)')
    parser.add_argument('--start-date', default='2023-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=1000000, help='Initial capital (default: 1000000)')
    
    args = parser.parse_args()
    
    # Available options strategies
    available_strategies = [
        'EnhancedIronCondor', 'IronCondor', 'GreeksEnhanced',
        'CashSecuredPut', 'CoveredCall', 'CalendarSpread',
        'ButterflySpread', 'VolatilityStrategy', 'EarningsStrategy'
    ]
    
    if args.strategy not in available_strategies:
        logger.error(f"❌ Invalid strategy: {args.strategy}")
        logger.info(f"Available strategies: {', '.join(available_strategies)}")
        return
    
    asyncio.run(run_single_options_strategy_backtest(
        strategy_name=args.strategy,
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.capital
    ))

if __name__ == "__main__":
    main() 