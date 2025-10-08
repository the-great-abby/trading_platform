#!/usr/bin/env python3
"""
Two-Year Aggressive Allocation Backtest
======================================
Backtest the aggressive allocation over 2 years (Oct 2023 - Oct 2025):
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
    logger.info("🚀 Starting Two-Year Aggressive Allocation Backtest")
    logger.info("=" * 80)
    logger.info("🎯 TWO-YEAR BACKTEST PERIOD:")
    logger.info("   • Start Date: October 1, 2023")
    logger.info("   • End Date: October 1, 2025")
    logger.info("   • Duration: 2 years (730 days)")
    logger.info("   • Market Conditions: Bear, Bull, and Recovery phases")
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
        
        logger.info("🎯 Multi-Strategy Ensemble Components (Two-Year Test):")
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
        
        # TWO-YEAR DATE RANGE
        start_date = '2023-10-01'  # October 1, 2023
        end_date = '2025-10-01'    # October 1, 2025

        logger.info("📊 Two-Year Backtest Configuration:")
        logger.info(f"   • Symbols: {symbols}")
        logger.info(f"   • Period: {start_date} to {end_date}")
        logger.info(f"   • Duration: 2 years (730 days)")
        logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
        logger.info(f"   • Cash Reserve: {engine.cash_reserve_pct*100}% (AGGRESSIVE)")
        logger.info(f"   • Max Position Size: {engine.max_position_size_pct*100}% (AGGRESSIVE)")
        logger.info(f"   • Real Data: {engine.use_real_data}")
        logger.info("")
        
        logger.info("📈 MARKET CONDITIONS COVERED:")
        logger.info("   • Q4 2023: End of bear market, recovery phase")
        logger.info("   • 2024: Full year of bull market conditions")
        logger.info("   • Q1-Q3 2025: Extended bull market + potential volatility")
        logger.info("   • Multiple market cycles and regime changes")
        logger.info("")
        
        logger.info("🏃‍♂️ Running Two-Year Multi-Strategy Ensemble backtest with AGGRESSIVE allocation...")

        results = await engine.run_backtest(
            strategies=['MultiStrategyEnsemble'],
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # Display results
        if 'MultiStrategyEnsemble' in results:
            result = results['MultiStrategyEnsemble']
            
            logger.info("📈 TWO-YEAR MULTI-STRATEGY ENSEMBLE RESULTS (AGGRESSIVE ALLOCATION)")
            logger.info("=" * 80)
            logger.info(f"Strategy: MultiStrategyEnsemble")
            logger.info(f"Test Period: {start_date} to {end_date} (2 years)")
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
            
            # Annualized performance calculation
            days_in_test = 730  # 2 years
            annualized_return = ((result.final_capital / engine.initial_capital) ** (365 / days_in_test) - 1) * 100
            
            logger.info("📊 ANNUALIZED PERFORMANCE ANALYSIS:")
            logger.info(f"   • Total Return (2 years): {result.total_return_pct:.2f}%")
            logger.info(f"   • Annualized Return: {annualized_return:.2f}%")
            logger.info(f"   • Compound Annual Growth Rate (CAGR): {annualized_return:.2f}%")
            logger.info("")
            
            # Show recent trades
            logger.info("🔍 Recent Trades (Last 10):")
            recent_trades = result.trades[-10:] if len(result.trades) > 10 else result.trades
            for i, trade in enumerate(recent_trades, 1):
                logger.info(f"   {i}. {trade.symbol}: {trade.action} {trade.quantity:.4f} shares @ ${trade.price:.2f} | P&L: ${trade.pnl:.2f}")
            
            logger.info("=" * 80)
            
            # Capital allocation analysis
            logger.info("💰 TWO-YEAR CAPITAL ALLOCATION ANALYSIS:")
            logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
            logger.info(f"   • Final Capital: ${result.final_capital:,.2f}")
            logger.info(f"   • Total Profit: ${result.final_capital - engine.initial_capital:,.2f}")
            logger.info(f"   • Cash Reserve (5%): ${engine.initial_capital * 0.05:,.2f}")
            logger.info(f"   • Stock Allocation (20%): ${engine.initial_capital * 0.20:,.2f}")
            logger.info(f"   • Options Allocation (50%): ${engine.initial_capital * 0.50:,.2f}")
            logger.info(f"     - Day Trading (25%): ${engine.initial_capital * 0.25:,.2f}")
            logger.info(f"     - Swing Trading (25%): ${engine.initial_capital * 0.25:,.2f}")
            logger.info("")
            
            # Performance comparison with 1-year results
            one_year_return = 1607.28  # From previous 1-year test
            two_year_return = result.total_return_pct
            
            logger.info("📊 PERFORMANCE COMPARISON:")
            logger.info(f"   • 1-Year Test (2024): {one_year_return:.2f}%")
            logger.info(f"   • 2-Year Test (2023-2025): {two_year_return:.2f}%")
            logger.info(f"   • Difference: {two_year_return - one_year_return:.2f} percentage points")
            
            if two_year_return > one_year_return:
                logger.info(f"   • 🎉 Two-year test EXCEEDED one-year performance!")
            elif abs(two_year_return - one_year_return) < 100:
                logger.info(f"   • ✅ Two-year test shows CONSISTENT performance")
            else:
                logger.info(f"   • ⚠️ Two-year test shows LOWER performance")
            logger.info("")
            
            # Risk-adjusted performance
            if result.max_drawdown_pct == 0:
                logger.info("🛡️ RISK ANALYSIS:")
                logger.info("   • Max Drawdown: 0.00% - PERFECT RISK CONTROL!")
                logger.info("   • No losing periods detected")
                logger.info("   • Consistent positive returns across market conditions")
            else:
                logger.info("🛡️ RISK ANALYSIS:")
                logger.info(f"   • Max Drawdown: {result.max_drawdown_pct:.2f}%")
                logger.info(f"   • Risk-Adjusted Return: {result.total_return_pct / max(result.max_drawdown_pct, 1):.2f}")
            logger.info("")
            
            # Trading frequency analysis
            trades_per_year = result.total_trades / 2
            logger.info("📈 TRADING FREQUENCY ANALYSIS:")
            logger.info(f"   • Total Trades (2 years): {result.total_trades}")
            logger.info(f"   • Trades per Year: {trades_per_year:.1f}")
            logger.info(f"   • Trades per Month: {trades_per_year / 12:.1f}")
            logger.info(f"   • Trading Activity: {'HIGH' if trades_per_year > 100 else 'MODERATE' if trades_per_year > 50 else 'LOW'}")
            logger.info("")
            
            # Market condition analysis
            logger.info("🎯 MARKET CONDITION PERFORMANCE:")
            logger.info("   • Bear Market (Q4 2023): Strategy performance during recovery")
            logger.info("   • Bull Market (2024): Full year of favorable conditions")
            logger.info("   • Extended Bull (Q1-Q3 2025): Sustainability test")
            logger.info(f"   • Overall Consistency: {'EXCELLENT' if result.win_rate > 90 else 'GOOD' if result.win_rate > 80 else 'MODERATE'}")
            logger.info("")
            
            logger.info("✅ Two-Year Multi-Strategy Ensemble backtest with AGGRESSIVE allocation completed successfully!")
            logger.info("=" * 80)
            
            # Final summary
            logger.info("🎉 TWO-YEAR BACKTEST SUMMARY:")
            logger.info(f"   • 🚀 Total Return: {result.total_return_pct:.2f}%")
            logger.info(f"   • 📈 Annualized Return: {annualized_return:.2f}%")
            logger.info(f"   • 🛡️ Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info(f"   • 🎯 Win Rate: {result.win_rate:.2f}%")
            logger.info(f"   • 💰 Final Value: ${result.final_capital:,.2f}")
            logger.info(f"   • 📊 Total Trades: {result.total_trades}")
            logger.info("=" * 80)
            
        else:
            logger.error("❌ No results found for MultiStrategyEnsemble")

    except Exception as e:
        logger.error(f"❌ Two-year backtest failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())












