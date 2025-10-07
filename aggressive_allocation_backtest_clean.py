#!/usr/bin/env python3
"""
Multi-Strategy Ensemble Backtest with AGGRESSIVE Capital Allocation
=================================================================
Backtest with the new aggressive allocation:
- 5% cash reserve (AGGRESSIVE)
- 20% stocks (reduced)
- 50% options (same)
- 25% day trading (HUGE INCREASE from 5%)
- 25% swing trading (reduced from 45%)
"""

import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting Multi-Strategy Ensemble Backtest with AGGRESSIVE Capital Allocation")
    logger.info("=" * 80)
    logger.info("🎯 AGGRESSIVE CAPITAL ALLOCATION:")
    logger.info("   • Cash Reserve: 5% (AGGRESSIVE)")
    logger.info("   • Stocks: 20% (reduced)")
    logger.info("   • Options: 50% (same)")
    logger.info("     - Day Trading: 25% (HUGE INCREASE from 5%)")
    logger.info("     - Swing Trading: 25% (reduced from 45%)")
    logger.info("=" * 80)

    # Load Polygon API key from environment
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    if polygon_api_key:
        logger.info("✅ Polygon API key loaded: %s...", polygon_api_key[:8])
    else:
        logger.error("❌ POLYGON_API_KEY not found in .env file. Please set it.")
        return

    # Disable LLM evaluation for backtesting
    os.environ['ENABLE_LLM_EVALUATION'] = 'false'
    os.environ['DISABLE_AI_SERVICES'] = 'true'
    os.environ['DISABLE_OLLAMA'] = 'true'
    os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'

    # Set up database connection for real data
    os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
    os.environ['DATABASE_ONLY'] = 'false' # Ensure real data is fetched if not in DB

    try:
        # Import after setting up environment
        from src.backtesting.engine.backtest_engine import BacktestEngine, BacktestResult
        from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble

        # Initialize the Multi-Strategy Ensemble with AGGRESSIVE allocation
        ensemble_strategy = MultiStrategyEnsemble(
            strategy_weights={
                'adaptive_wave': 0.35,      # 35% - Elliott Wave + Options
                'regime_switching': 0.25,   # 25% - Market timing
                'enhanced_multi': 0.25,     # 25% - Sector rotation
                'momentum': 0.15            # 15% - Cross-sectional momentum
            },
            min_signal_confidence=0.3,  # LOWERED for more trades
            min_strategies_for_entry=1, # LOWERED for more trades
        )
        
        logger.info("🎯 Multi-Strategy Ensemble Components (AGGRESSIVE):")
        logger.info(f"   • AdaptiveSectorWaveStrategy: 35% (Elliott Wave + Options)")
        logger.info(f"   • RegimeSwitchingStrategy: 25% (Market timing)")
        logger.info(f"   • EnhancedMultiStrategy: 25% (Sector rotation)")
        logger.info(f"   • CrossSectionalMomentumStrategy: 15% (Momentum)")
        logger.info(f"   • Min Signal Confidence: 0.3 (LOWERED for more trades)")
        logger.info(f"   • Min Strategies for Entry: 1 (LOWERED for more trades)")
        logger.info("")
        
        # Initialize backtest engine with AGGRESSIVE CAPITAL ALLOCATION
        engine = BacktestEngine()
        engine.initial_capital = 4000.0  # $4,000 starting capital
        
        # AGGRESSIVE CAPITAL ALLOCATION SETTINGS
        engine.cash_reserve_pct = 0.05  # 5% cash reserve (AGGRESSIVE)
        engine.max_position_size_pct = 0.20  # 20% max position size (more aggressive)
        
        engine.use_real_data = True  # Use REAL market data from Polygon API
        
        # Test symbols (including more for day trading)
        symbols = ['SPY', 'AAPL', 'NVDA', 'QQQ']  # Added QQQ for more day trading opportunities
        
        # Date range for backtest (2024 data)
        start_date = '2024-01-01'
        end_date = '2024-12-31'

        logger.info("📊 Backtest Configuration (AGGRESSIVE ALLOCATION):")
        logger.info(f"   • Symbols: {symbols}")
        logger.info(f"   • Period: {start_date} to {end_date}")
        logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
        logger.info(f"   • Cash Reserve: {engine.cash_reserve_pct*100}% (AGGRESSIVE)")
        logger.info(f"   • Max Position Size: {engine.max_position_size_pct*100}% (AGGRESSIVE)")
        logger.info(f"   • Real Data: {engine.use_real_data}")
        logger.info("")
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
            logger.info("=" * 80)
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
            
            logger.info("=" * 80)
            
            # Capital allocation analysis
            logger.info("💰 AGGRESSIVE CAPITAL ALLOCATION ANALYSIS:")
            logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
            logger.info(f"   • Cash Reserve (5%): ${engine.initial_capital * 0.05:,.2f}")
            logger.info(f"   • Stock Allocation (20%): ${engine.initial_capital * 0.20:,.2f}")
            logger.info(f"   • Options Allocation (50%): ${engine.initial_capital * 0.50:,.2f}")
            logger.info(f"     - Day Trading (25%): ${engine.initial_capital * 0.25:,.2f}")
            logger.info(f"     - Swing Trading (25%): ${engine.initial_capital * 0.25:,.2f}")
            logger.info("")
            
            # Performance comparison
            logger.info("📊 PERFORMANCE COMPARISON:")
            logger.info(f"   • Previous Conservative (1,139.36%): 1,139.36%")
            logger.info(f"   • Current Aggressive Result: {result.total_return_pct:.2f}%")
            if result.total_return_pct >= 1139.36:
                logger.info(f"   • 🎉 EXCEEDED CONSERVATIVE PERFORMANCE by {result.total_return_pct - 1139.36:.2f} percentage points!")
            else:
                logger.info(f"   • ⚠️ Below conservative performance by {1139.36 - result.total_return_pct:.2f} percentage points.")
            logger.info("")
            
            logger.info("🎯 AGGRESSIVE ALLOCATION IMPACT ANALYSIS:")
            logger.info("   • Cash Reserve: 5% (vs 20% previously) - Much more aggressive")
            logger.info("   • Stock Allocation: 20% (vs 30% previously) - Reduced")
            logger.info("   • Options Allocation: 50% (vs 50% previously) - Same")
            logger.info("   • Day Trading: 25% (vs 5% previously) - HUGE INCREASE")
            logger.info("   • Swing Trading: 25% (vs 45% previously) - Reduced")
            logger.info("")
            
            # Day trading analysis
            day_trading_capital = engine.initial_capital * 0.25
            logger.info("📈 DAY TRADING ANALYSIS:")
            logger.info(f"   • Day Trading Capital: ${day_trading_capital:,.2f}")
            logger.info(f"   • Previous Day Trading Capital: ${engine.initial_capital * 0.05:,.2f}")
            logger.info(f"   • Increase in Day Trading Capital: ${day_trading_capital - (engine.initial_capital * 0.05):,.2f}")
            logger.info(f"   • Day Trading Capital Multiplier: {day_trading_capital / (engine.initial_capital * 0.05):.1f}x")
            logger.info("")
            
            logger.info("✅ Multi-Strategy Ensemble backtest with AGGRESSIVE allocation completed successfully!")
        else:
            logger.error("❌ No results found for MultiStrategyEnsemble")

    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())









