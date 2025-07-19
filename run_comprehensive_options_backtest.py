#!/usr/bin/env python3
"""
Comprehensive Options Strategies Backtest
========================================
Runs a comprehensive backtest using all available options strategies
with cache integration for better performance and accuracy.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.enhanced_logging import get_trading_logger

# Setup logging
logger = get_trading_logger()
logger = logging.getLogger(__name__)

async def run_comprehensive_options_backtest():
    """Run comprehensive options strategies backtest with cache integration"""
    
    logger.info("🚀 Starting Comprehensive Options Strategies Backtest")
    
    # Configuration
    initial_capital = 1000000  # $1M
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    # Options-focused symbols (liquid ETFs with good options chains)
    symbols = [
        'SPY',   # S&P 500 ETF
        'QQQ',   # Nasdaq 100 ETF
        'IWM',   # Russell 2000 ETF
        'DIA',   # Dow Jones ETF
        'XLF',   # Financial Sector ETF
        'XLE',   # Energy Sector ETF
        'XLK',   # Technology Sector ETF
        'XLV',   # Healthcare Sector ETF
        'XLI',   # Industrial Sector ETF
        'XLP'    # Consumer Staples ETF
    ]
    
    # All available options strategies
    options_strategies = [
        'EnhancedIronCondor',    # Enhanced Iron Condor with cache
        'IronCondor',            # Basic Iron Condor
        'GreeksEnhanced',        # Greeks-based strategy
        'CashSecuredPut',        # Cash Secured Put
        'CoveredCall',           # Covered Call
        'CalendarSpread',        # Calendar Spread
        'ButterflySpread',       # Butterfly Spread
        'VolatilityStrategy',    # Volatility-based strategy
        'EarningsStrategy'       # Earnings-based strategy
    ]
    
    # Risk management settings for options
    risk_settings = {
        'max_position_size': 0.05,  # 5% per position
        'max_portfolio_risk': 0.02,  # 2% max portfolio risk
        'stop_loss_pct': 0.02,  # 2% stop loss
        'take_profit_pct': 0.01,  # 1% take profit
    }
    
    logger.info("📊 Options Backtest Configuration:")
    logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"   Test Period: {start_date} to {end_date}")
    logger.info(f"   Symbols: {len(symbols)} ETFs with options")
    logger.info(f"   Strategies: {len(options_strategies)} options strategies")
    logger.info(f"   Data Source: Cached Options Data")
    
    # Initialize backtest engine with cache
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Run backtests for each options strategy
    results = {}
    for strategy_name in options_strategies:
        logger.info(f"🏃 Running backtest for {strategy_name} strategy...")
        
        try:
            strategy_results = await engine.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                strategies=[strategy_name]
            )
            
            if strategy_results and strategy_name in strategy_results:
                results[strategy_name] = strategy_results[strategy_name]
                logger.info(f"✅ {strategy_name} completed successfully")
            else:
                logger.warning(f"⚠️  {strategy_name} returned no results")
                
        except Exception as e:
            logger.error(f"❌ Error running {strategy_name}: {e}")
            continue
    
    # Analyze and compare results
    logger.info("📈 Analyzing options strategies results...")
    
    strategy_performance = {}
    for strategy_name, result in results.items():
        if result:
            performance = {
                'total_return_pct': result.total_return_pct,
                'max_drawdown_pct': result.max_drawdown_pct,
                'sharpe_ratio': result.sharpe_ratio,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'avg_win': result.avg_win,
                'avg_loss': result.avg_loss
            }
            strategy_performance[strategy_name] = performance
    
    # Sort strategies by total return
    sorted_strategies = sorted(
        strategy_performance.items(),
        key=lambda x: x[1]['total_return_pct'],
        reverse=True
    )
    
    logger.info("🏆 Options Strategies Performance Ranking:")
    logger.info("=" * 80)
    logger.info(f"{'Strategy':<20} {'Return %':<10} {'Drawdown %':<12} {'Sharpe':<8} {'Trades':<8} {'Win Rate %':<12}")
    logger.info("-" * 80)
    
    for strategy_name, perf in sorted_strategies:
        logger.info(f"{strategy_name:<20} {perf['total_return_pct']:>8.2f}% {perf['max_drawdown_pct']:>10.2f}% "
                   f"{perf['sharpe_ratio']:>6.2f} {perf['total_trades']:>6} {perf['win_rate']*100:>10.1f}%")
    
    # Detailed analysis for top performers
    logger.info("\n📊 Top 3 Performing Options Strategies:")
    for i, (strategy_name, perf) in enumerate(sorted_strategies[:3], 1):
        logger.info(f"\n{i}. {strategy_name}:")
        logger.info(f"   Total Return: {perf['total_return_pct']:.2f}%")
        logger.info(f"   Max Drawdown: {perf['max_drawdown_pct']:.2f}%")
        logger.info(f"   Sharpe Ratio: {perf['sharpe_ratio']:.3f}")
        logger.info(f"   Total Trades: {perf['total_trades']}")
        logger.info(f"   Win Rate: {perf['win_rate']*100:.1f}%")
        logger.info(f"   Profit Factor: {perf['profit_factor']:.2f}")
        logger.info(f"   Avg Win: ${perf['avg_win']:,.2f}")
        logger.info(f"   Avg Loss: ${perf['avg_loss']:,.2f}")
    
    # Store results
    try:
        await engine.store_results(
            results=results,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            database_only=True,
            backtest_name="comprehensive_options_strategies"
        )
        logger.info("💾 Backtest results stored successfully")
    except Exception as e:
        logger.error(f"❌ Failed to store results: {e}")
    
    # Cache performance analysis
    if hasattr(engine, 'market_data_manager') and hasattr(engine.market_data_manager, 'get_stats'):
        try:
            cache_stats = engine.market_data_manager.get_stats()
            logger.info("\n📊 Cache Performance:")
            logger.info(f"   Cache Hit Rate: {cache_stats.get('cache_hit_rate', 0):.1f}%")
            logger.info(f"   API Calls Saved: {cache_stats.get('cache_hits', 0)}")
            logger.info(f"   Total API Calls: {cache_stats.get('api_calls', 0)}")
        except Exception as e:
            logger.warning(f"⚠️  Could not retrieve cache stats: {e}")
    
    logger.info("✅ Comprehensive Options Strategies Backtest completed successfully!")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_options_backtest()) 