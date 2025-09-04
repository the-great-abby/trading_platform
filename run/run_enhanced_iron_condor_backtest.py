#!/usr/bin/env python3
"""
Enhanced Iron Condor Backtest with Cache Integration
===================================================
Runs a comprehensive backtest using the enhanced Iron Condor strategy
that leverages the options data cache for better performance and accuracy.
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
from src.strategies.options.enhanced_iron_condor_strategy import EnhancedIronCondorStrategy
from src.utils.trading_config import BacktestConfig
from src.utils.enhanced_logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def run_enhanced_iron_condor_backtest():
    """Run enhanced Iron Condor backtest with cache integration"""
    
    logger.info("🚀 Starting Enhanced Iron Condor Backtest with Cache Integration")
    
    # Configuration
    config = BacktestConfig(
        start_date=date(2023, 1, 1),
        end_date=date(2024, 12, 31),
        initial_capital=1000000,  # $1M
        symbols=['SPY', 'QQQ', 'IWM', 'DIA', 'XLF'],  # Liquid ETFs with options
        strategies=['EnhancedIronCondor'],
        risk_management={
            'max_position_size': 0.05,  # 5% per position
            'max_portfolio_risk': 0.02,  # 2% max portfolio risk
            'stop_loss_pct': 0.02,  # 2% stop loss
            'take_profit_pct': 0.01,  # 1% take profit
        },
        data_providers=['polygon', 'cache'],  # Use cache as primary
        cache_only=True,  # Force cache-only mode
        enable_llm_evaluation=False,  # Disable LLM for speed
        parallel_execution=True,
        max_workers=4
    )
    
    # Initialize enhanced Iron Condor strategy
    iron_condor_strategy = EnhancedIronCondorStrategy(
        name="EnhancedIronCondor",
        days_to_expiration=45,
        profit_target_pct=0.5,
        stop_loss_pct=2.0,
        max_risk_per_trade=0.02,
        volatility_threshold=0.25,  # Lower threshold for more opportunities
        min_dte=30,
        max_dte=60,
        min_volume=5,  # Lower volume requirement
        min_open_interest=25,  # Lower OI requirement
        cache_lookback_days=30
    )
    
    # Initialize backtest engine
    engine = BacktestEngine(
        config=config,
        strategies={'EnhancedIronCondor': iron_condor_strategy}
    )
    
    logger.info("📊 Enhanced Iron Condor Strategy Configuration:")
    logger.info(f"   - Days to Expiration: {iron_condor_strategy.days_to_expiration}")
    logger.info(f"   - Volatility Threshold: {iron_condor_strategy.volatility_threshold}")
    logger.info(f"   - Min Volume: {iron_condor_strategy.min_volume}")
    logger.info(f"   - Min Open Interest: {iron_condor_strategy.min_open_interest}")
    logger.info(f"   - Cache Lookback: {iron_condor_strategy.cache_lookback_days} days")
    
    # Run backtest
    logger.info("🔄 Starting backtest execution...")
    results = await engine.run_backtest()
    
    if not results:
        logger.error("❌ Backtest failed to complete")
        return
    
    # Analyze results
    logger.info("📈 Analyzing backtest results...")
    
    # Extract key metrics
    total_trades = len(results.get('trades', []))
    winning_trades = len([t for t in results.get('trades', []) if t.get('pnl', 0) > 0])
    losing_trades = total_trades - winning_trades
    
    total_pnl = sum(t.get('pnl', 0) for t in results.get('trades', []))
    max_drawdown = results.get('max_drawdown', 0)
    sharpe_ratio = results.get('sharpe_ratio', 0)
    
    # Strategy-specific analysis
    iron_condor_trades = [t for t in results.get('trades', []) 
                         if t.get('strategy') == 'EnhancedIronCondor']
    
    logger.info("📊 Enhanced Iron Condor Backtest Results:")
    logger.info(f"   - Total Trades: {total_trades}")
    logger.info(f"   - Iron Condor Trades: {len(iron_condor_trades)}")
    logger.info(f"   - Winning Trades: {winning_trades} ({winning_trades/total_trades*100:.1f}%)")
    logger.info(f"   - Losing Trades: {losing_trades} ({losing_trades/total_trades*100:.1f}%)")
    logger.info(f"   - Total P&L: ${total_pnl:,.2f}")
    logger.info(f"   - Max Drawdown: {max_drawdown:.2f}%")
    logger.info(f"   - Sharpe Ratio: {sharpe_ratio:.3f}")
    
    # Cache performance analysis
    if hasattr(iron_condor_strategy, 'options_service'):
        cache_stats = iron_condor_strategy.options_service.get_cache_stats()
        logger.info("📊 Cache Performance:")
        logger.info(f"   - Cache Hit Rate: {cache_stats.get('hit_rate', 'N/A')}")
        logger.info(f"   - Total Requests: {cache_stats.get('total_requests', 0)}")
        logger.info(f"   - Cache Size: {cache_stats.get('cache_size', 0)} entries")
    
    # Detailed trade analysis
    if iron_condor_trades:
        avg_trade_pnl = sum(t.get('pnl', 0) for t in iron_condor_trades) / len(iron_condor_trades)
        max_trade_pnl = max(t.get('pnl', 0) for t in iron_condor_trades)
        min_trade_pnl = min(t.get('pnl', 0) for t in iron_condor_trades)
        
        logger.info("📊 Iron Condor Trade Analysis:")
        logger.info(f"   - Average Trade P&L: ${avg_trade_pnl:,.2f}")
        logger.info(f"   - Best Trade: ${max_trade_pnl:,.2f}")
        logger.info(f"   - Worst Trade: ${min_trade_pnl:,.2f}")
        
        # Analyze trade metadata
        successful_trades = [t for t in iron_condor_trades if t.get('pnl', 0) > 0]
        if successful_trades:
            avg_confidence = sum(t.get('metadata', {}).get('confidence', 0) for t in successful_trades) / len(successful_trades)
            avg_iv = sum(t.get('metadata', {}).get('metrics', {}).get('implied_volatility', 0) for t in successful_trades) / len(successful_trades)
            
            logger.info("📊 Successful Trades Analysis:")
            logger.info(f"   - Average Confidence: {avg_confidence:.3f}")
            logger.info(f"   - Average Implied Volatility: {avg_iv:.3f}")
    
    # Store results
    try:
        from src.services.database.backtest_results_service import BacktestResultsService
        results_service = BacktestResultsService()
        
        # Store backtest results
        result_id = results_service.store_backtest_result(
            strategy_name="EnhancedIronCondor",
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            final_capital=config.initial_capital + total_pnl,
            total_return=total_pnl / config.initial_capital,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            metadata={
                'cache_integration': True,
                'options_data_used': True,
                'strategy_config': iron_condor_strategy.get_strategy_info(),
                'cache_stats': cache_stats if hasattr(iron_condor_strategy, 'options_service') else {}
            }
        )
        
        logger.info(f"💾 Backtest results stored with ID: {result_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to store results: {e}")
    
    logger.info("✅ Enhanced Iron Condor Backtest completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_enhanced_iron_condor_backtest()) 