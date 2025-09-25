"""
Working Options Backtest Script
==============================
Comprehensive backtest script for options strategies with proper error handling and fallback mechanisms.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

# Add src to path for imports
sys.path.append('/app/src')
sys.path.append('/app')

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.services.mock_options_data_service import MockOptionsDataService
from src.utils.error_handler import ErrorHandler, log_backtest_progress

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INITIAL_CAPITAL = 2000.0
SYMBOLS = ["AAPL", "MSFT", "AMD", "PYPL", "INTC"]
STRATEGIES = ["IronCondor", "ButterflySpread", "CalendarSpread"]
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"

async def run_comprehensive_backtest():
    """Run comprehensive backtest with options strategies"""
    
    logger.info("🚀 Starting comprehensive options backtest")
    logger.info(f"📊 Testing {len(STRATEGIES)} strategies on {len(SYMBOLS)} symbols")
    logger.info(f"💰 Initial Capital: ${INITIAL_CAPITAL}")
    logger.info(f"📅 Date Range: {START_DATE} to {END_DATE}")
    
    # Initialize services
    error_handler = ErrorHandler()
    mock_options_service = MockOptionsDataService()
    
    # Initialize backtest engine with mock data
    engine = BacktestEngine(use_real_data=False, use_cache=False)
    
    # Set up options service for strategies
    engine.options_service = mock_options_service
    
    all_results = []
    total_tests = len(STRATEGIES) * len(SYMBOLS)
    completed_tests = 0
    
    try:
        for symbol in SYMBOLS:
            logger.info(f"\n📈 Testing {symbol}...")
            
            for strategy in STRATEGIES:
                try:
                    log_backtest_progress(
                        "starting_strategy",
                        {"symbol": symbol, "strategy": strategy, "completed": completed_tests, "total": total_tests}
                    )
                    
                    # Run backtest for single strategy
                    result = await engine.run_backtest(
                        symbols=[symbol],
                        start_date=START_DATE,
                        end_date=END_DATE,
                        strategies=[strategy]
                    )
                    
                    if result and strategy in result:
                        strategy_result = result[strategy]
                        if strategy_result:
                            # Calculate performance metrics
                            final_value = INITIAL_CAPITAL * (1 + strategy_result.total_return)
                            
                            result_data = {
                                'symbol': symbol,
                                'strategy': strategy,
                                'total_return': strategy_result.total_return,
                                'total_return_pct': strategy_result.total_return_pct,
                                'sharpe_ratio': strategy_result.sharpe_ratio,
                                'max_drawdown_pct': strategy_result.max_drawdown_pct,
                                'max_drawdown': strategy_result.max_drawdown,  # Use backward compatibility
                                'win_rate': strategy_result.win_rate,
                                'total_trades': strategy_result.total_trades,
                                'profit_factor': strategy_result.profit_factor,
                                'final_value': final_value,
                                'initial_capital': INITIAL_CAPITAL
                            }
                            
                            all_results.append(result_data)
                            
                            logger.info(f"  ✅ {strategy}: {strategy_result.total_return:.2%} return, "
                                       f"{strategy_result.sharpe_ratio:.2f} Sharpe, "
                                       f"{strategy_result.total_trades} trades")
                        else:
                            logger.warning(f"  ❌ {strategy}: No results")
                    else:
                        logger.warning(f"  ❌ {strategy}: Failed to get results")
                        
                except Exception as e:
                    logger.error(f"  ❌ {strategy}: Error - {e}")
                    error_handler.handle_error(e, {
                        "symbol": symbol,
                        "strategy": strategy,
                        "context": "backtest_execution"
                    })
                
                completed_tests += 1
                
                # Progress update every 5 tests
                if completed_tests % 5 == 0:
                    log_backtest_progress(
                        "progress_update",
                        {"completed": completed_tests, "total": total_tests, "percentage": (completed_tests/total_tests)*100}
                    )
                    logger.info(f"🔄 Progress: {completed_tests}/{total_tests} tests completed ({(completed_tests/total_tests)*100:.1f}%)")
        
        logger.info(f"\n✅ Completed all {total_tests} tests")
        
        # Analyze results
        if all_results:
            await analyze_results(all_results)
        else:
            logger.warning("No results to analyze")
            
    except Exception as e:
        logger.error(f"❌ Critical error in backtest: {e}")
        error_handler.handle_error(e, {"context": "comprehensive_backtest"})

async def analyze_results(results):
    """Analyze and rank backtest results"""
    
    logger.info("\n📊 BACKTEST RESULTS ANALYSIS")
    logger.info("=" * 60)
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    
    # Sort by total return
    df_sorted = df.sort_values('total_return', ascending=False)
    
    logger.info(f"\n🏆 TOP 10 PERFORMING COMBINATIONS:")
    logger.info("-" * 60)
    
    for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        logger.info(f"{i:2d}. {row['strategy']:15} on {row['symbol']:5} | "
                   f"Return: {row['total_return']:7.2%} | "
                   f"Sharpe: {row['sharpe_ratio']:5.2f} | "
                   f"Trades: {row['total_trades']:3d}")
    
    # Strategy performance summary
    logger.info(f"\n📈 STRATEGY PERFORMANCE SUMMARY:")
    logger.info("-" * 60)
    
    strategy_stats = df.groupby('strategy').agg({
        'total_return': ['mean', 'std', 'count'],
        'sharpe_ratio': 'mean',
        'max_drawdown_pct': 'mean',
        'total_trades': 'mean'
    }).round(4)
    
    for strategy in STRATEGIES:
        if strategy in strategy_stats.index:
            stats = strategy_stats.loc[strategy]
            avg_return = stats[('total_return', 'mean')]
            avg_sharpe = stats[('sharpe_ratio', 'mean')]
            avg_drawdown = stats[('max_drawdown_pct', 'mean')]
            avg_trades = stats[('total_trades', 'mean')]
            count = stats[('total_return', 'count')]
            
            logger.info(f"{strategy:15} | "
                       f"Avg Return: {avg_return:7.2%} | "
                       f"Avg Sharpe: {avg_sharpe:5.2f} | "
                       f"Avg DD: {avg_drawdown:6.2%} | "
                       f"Avg Trades: {avg_trades:5.1f} | "
                       f"Count: {count:2d}")
    
    # Symbol performance summary
    logger.info(f"\n📊 SYMBOL PERFORMANCE SUMMARY:")
    logger.info("-" * 60)
    
    symbol_stats = df.groupby('symbol').agg({
        'total_return': ['mean', 'std'],
        'sharpe_ratio': 'mean',
        'total_trades': 'mean'
    }).round(4)
    
    for symbol in SYMBOLS:
        if symbol in symbol_stats.index:
            stats = symbol_stats.loc[symbol]
            avg_return = stats[('total_return', 'mean')]
            avg_sharpe = stats[('sharpe_ratio', 'mean')]
            avg_trades = stats[('total_trades', 'mean')]
            
            logger.info(f"{symbol:5} | "
                       f"Avg Return: {avg_return:7.2%} | "
                       f"Avg Sharpe: {avg_sharpe:5.2f} | "
                       f"Avg Trades: {avg_trades:5.1f}")
    
    # Best overall performance
    best_result = df_sorted.iloc[0]
    logger.info(f"\n🎯 BEST OVERALL PERFORMANCE:")
    logger.info("-" * 60)
    logger.info(f"Strategy: {best_result['strategy']}")
    logger.info(f"Symbol: {best_result['symbol']}")
    logger.info(f"Total Return: {best_result['total_return']:.2%}")
    logger.info(f"Final Value: ${best_result['final_value']:.2f}")
    logger.info(f"Sharpe Ratio: {best_result['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown: {best_result['max_drawdown_pct']:.2%}")
    logger.info(f"Total Trades: {best_result['total_trades']}")
    
    # Risk-adjusted performance
    logger.info(f"\n⚖️ RISK-ADJUSTED RANKING (Sharpe Ratio):")
    logger.info("-" * 60)
    
    df_sharpe = df.sort_values('sharpe_ratio', ascending=False)
    for i, (_, row) in enumerate(df_sharpe.head(5).iterrows(), 1):
        logger.info(f"{i}. {row['strategy']:15} on {row['symbol']:5} | "
                   f"Sharpe: {row['sharpe_ratio']:5.2f} | "
                   f"Return: {row['total_return']:7.2%}")
    
    logger.info("\n✅ Analysis complete!")

async def test_mock_options_service():
    """Test the mock options service"""
    
    logger.info("🧪 Testing Mock Options Data Service...")
    
    try:
        service = MockOptionsDataService()
        
        # Test basic functionality
        options = service.get_liquid_options("AAPL", min_volume=10)
        logger.info(f"✅ Generated {len(options)} options for AAPL")
        
        # Test historical data
        hist_options = service.get_liquid_options_with_historical_support(
            "AAPL", min_volume=10, historical_date="2023-06-15"
        )
        logger.info(f"✅ Generated {len(hist_options)} historical options for AAPL")
        
        # Test service status
        status = service.get_service_status()
        logger.info(f"✅ Service status: {status}")
        
    except Exception as e:
        logger.error(f"❌ Mock options service test failed: {e}")

if __name__ == "__main__":
    async def main():
        # Test mock service first
        await test_mock_options_service()
        
        # Run comprehensive backtest
        await run_comprehensive_backtest()
    
    asyncio.run(main())


