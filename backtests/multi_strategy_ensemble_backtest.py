#!/usr/bin/env python3
"""
Multi-Strategy Ensemble Backtest
===============================
Tests the Multi-Strategy Ensemble combining:
1. AdaptiveSectorWaveStrategy (128.79% return)
2. RegimeSwitchingStrategy (market timing)
3. EnhancedMultiStrategy (sector rotation)  
4. CrossSectionalMomentumStrategy (momentum)

Target: 313%+ return through strategy diversification
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run Multi-Strategy Ensemble backtest"""
    
    logger.info("🚀 Starting Multi-Strategy Ensemble Backtest")
    logger.info("=" * 60)
    
    # Set environment variables for real data
    os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
    os.environ['DATABASE_ONLY'] = 'false'
    os.environ['DISABLE_AI_SERVICES'] = 'true'
    os.environ['DISABLE_OLLAMA'] = 'true'
    os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'
    os.environ['ENABLE_LLM_EVALUATION'] = 'false'
    
    # Verify Polygon API key
    polygon_key = os.getenv('POLYGON_API_KEY')
    if polygon_key:
        logger.info(f"✅ Polygon API key loaded: {polygon_key[:8]}...")
    else:
        logger.warning("⚠️ No Polygon API key found - using mock data")
    
    try:
        # Import after environment setup
        from src.backtesting.engine.backtest_engine import BacktestEngine
        from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble
        
        # Initialize Multi-Strategy Ensemble
        ensemble_strategy = MultiStrategyEnsemble(
            adaptive_wave_weight=0.35,      # 35% - Elliott Wave + Options (128.79% return)
            regime_switching_weight=0.25,   # 25% - Market timing (516.9% target)
            enhanced_multi_weight=0.25,     # 25% - Sector rotation (468.2% target)
            momentum_weight=0.15,           # 15% - Cross-sectional momentum
            performance_window=50,
            rebalance_frequency=10,
            max_total_exposure=0.95,
            correlation_threshold=0.7
        )
        
        logger.info("🎯 Multi-Strategy Ensemble Components:")
        logger.info(f"   • AdaptiveSectorWaveStrategy: 35% (128.79% return)")
        logger.info(f"   • RegimeSwitchingStrategy: 25% (516.9% target)")
        logger.info(f"   • EnhancedMultiStrategy: 25% (468.2% target)")
        logger.info(f"   • CrossSectionalMomentumStrategy: 15%")
        logger.info(f"   • Target Combined Return: 313%+")
        
    # Initialize backtest engine with AGGRESSIVE optimization
    engine = BacktestEngine()
    engine.initial_capital = 4000.0  # $4,000 starting capital
    engine.use_real_data = True  # Use REAL market data from Polygon API
    
    # AGGRESSIVE CAPITAL ALLOCATION (NEW REQUESTED SPLIT)
    engine.cash_reserve_pct = 0.05  # 5% cash reserve (AGGRESSIVE)
    engine.max_position_size_pct = 0.20  # 20% max position size (more aggressive)
    
    # NEW AGGRESSIVE ALLOCATION SETTINGS
    engine.stock_allocation_pct = 0.20  # 20% stocks (reduced)
    engine.options_allocation_pct = 0.50  # 50% options (same)
    engine.options_day_trading_pct = 0.25  # 25% total for day trading (HUGE INCREASE)
    engine.options_swing_trading_pct = 0.25  # 25% total for swing trading (reduced)
    
    # Test symbols (including QQQ for more day trading opportunities)
    symbols = ['SPY', 'AAPL', 'NVDA', 'QQQ']
    
    # Backtest period (2024 data for complete options coverage)
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info("📊 Backtest Configuration (AGGRESSIVE ALLOCATION):")
    logger.info(f"   • Symbols: {symbols}")
    logger.info(f"   • Period: {start_date} to {end_date}")
    logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
    logger.info(f"   • Cash Reserve: {engine.cash_reserve_pct*100}% (AGGRESSIVE)")
    logger.info(f"   • Stock Allocation: {engine.stock_allocation_pct*100}%")
    logger.info(f"   • Options Allocation: {engine.options_allocation_pct*100}%")
    logger.info(f"     - Day Trading: {engine.options_day_trading_pct*100}% (HUGE INCREASE)")
    logger.info(f"     - Swing Trading: {engine.options_swing_trading_pct*100}%")
    logger.info(f"   • Max Position Size: {engine.max_position_size_pct*100}%")
    logger.info(f"   • Real Data: {engine.use_real_data}")
    
    # Run backtest
    logger.info("🏃‍♂️ Running Multi-Strategy Ensemble backtest with AGGRESSIVE allocation...")
    
    results = await engine.run_backtest(
        strategies=['MultiStrategyEnsemble'],
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    # Display results
    if 'MultiStrategyEnsemble' in results:
        result = results['MultiStrategyEnsemble']
        
        logger.info("📈 MULTI-STRATEGY ENSEMBLE RESULTS (AGGRESSIVE ALLOCATION)")
        logger.info("=" * 60)
        logger.info(f"Strategy: MultiStrategyEnsemble")
        logger.info(f"Total Return: {result.total_return_pct:.2f}%")
        logger.info(f"Final Value: ${result.final_capital:,.2f}")
        logger.info(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
        logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Win Rate: {result.win_rate:.2f}%")
        logger.info(f"Total Trades: {result.total_trades}")
        logger.info(f"Profitable Trades: {result.winning_trades}")
        logger.info(f"Losing Trades: {result.losing_trades}")
        logger.info("")
        logger.info("📊 Trade Summary:")
        logger.info(f"   Average Win: ${result.avg_win:.2f}")
        logger.info(f"   Average Loss: ${result.avg_loss:.2f}")
        logger.info("")
        
        # Show recent trades
        logger.info("🔍 Recent Trades (Last 10):")
        recent_trades = result.trades[-10:] if len(result.trades) > 10 else result.trades
        for i, trade in enumerate(recent_trades, 1):
            logger.info(f"   {i}. {trade.symbol}: {trade.action} {trade.quantity:.4f} shares @ ${trade.price:.2f} | P&L: ${trade.pnl:.2f}")
        
        logger.info("=" * 60)
        
        # Performance comparison
        logger.info("🔄 Performance vs Targets (AGGRESSIVE ALLOCATION):")
        logger.info(f"   • Target (313%+): 313.00%")
        logger.info(f"   • Current Result: {result.total_return_pct:.2f}%")
        gap = 313.0 - result.total_return_pct
        if gap > 0:
            logger.info(f"   • Gap to Target: -{gap:.2f} percentage points")
        else:
            logger.info(f"   • 🎉 EXCEEDED TARGET by {abs(gap):.2f} percentage points!")
        
        # Strategy component analysis
            logger.info("")
            logger.info("🎯 Strategy Component Analysis:")
            strategy_summary = ensemble_strategy.get_strategy_summary()
            for strategy_name, weight in strategy_summary['strategy_weights'].items():
                perf_data = strategy_summary['performance_history'][strategy_name]
                logger.info(f"   • {strategy_name}: {weight*100:.1f}% weight, {perf_data['recent_avg']:.3f} avg, {perf_data['win_rate']*100:.1f}% win rate")
            
            logger.info("")
            logger.info("✅ Multi-Strategy Ensemble backtest completed successfully!")
            
        else:
            logger.error("❌ No results found for MultiStrategyEnsemble")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
