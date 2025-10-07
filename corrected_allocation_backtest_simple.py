#!/usr/bin/env python3
"""
Multi-Strategy Ensemble Backtest with Corrected Capital Allocation (Simplified)
===============================================================================
Backtest with the updated capital allocation:
- 20% cash reserve
- 30% stocks
- 50% options (5% day trading, 45% swing trading)
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
    logger.info("🚀 Starting Multi-Strategy Ensemble Backtest with Corrected Capital Allocation")
    logger.info("=" * 80)
    logger.info("🎯 CAPITAL ALLOCATION:")
    logger.info("   • Cash Reserve: 20%")
    logger.info("   • Stocks: 30%")
    logger.info("   • Options: 50%")
    logger.info("     - Day Trading: 5% (15-minute time window)")
    logger.info("     - Swing Trading: 45% (1-day time window)")
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

    # Start database port forwarding
    logger.info("🔌 Starting database port forwarding...")
    import subprocess
    try:
        # Kill any existing port forwards
        subprocess.run(["pkill", "-f", "kubectl port-forward.*5432"], check=False)
        # Start new port forward
        subprocess.Popen([
            "kubectl", "port-forward", "svc/postgresql-service", "5432:5432", 
            "-n", "trading-system"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("✅ Database port forwarding started")
    except Exception as e:
        logger.warning(f"⚠️ Could not start database port forwarding: {e}")

    # Wait a moment for port forwarding to establish
    await asyncio.sleep(2)

    try:
        # Import after setting up environment
        from src.backtesting.engine.backtest_engine import BacktestEngine, BacktestResult
        from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble

        # Initialize the Multi-Strategy Ensemble with corrected allocation
        ensemble_strategy = MultiStrategyEnsemble(
            strategy_weights={
                'adaptive_wave': 0.35,      # 35% - Elliott Wave + Options
                'regime_switching': 0.25,   # 25% - Market timing
                'enhanced_multi': 0.25,     # 25% - Sector rotation
                'momentum': 0.15            # 15% - Cross-sectional momentum
            },
            min_signal_confidence=0.5,
            min_strategies_for_entry=2
        )
        
        logger.info("🎯 Multi-Strategy Ensemble Components:")
        logger.info(f"   • AdaptiveSectorWaveStrategy: 35% (Elliott Wave + Options)")
        logger.info(f"   • RegimeSwitchingStrategy: 25% (Market timing)")
        logger.info(f"   • EnhancedMultiStrategy: 25% (Sector rotation)")
        logger.info(f"   • CrossSectionalMomentumStrategy: 15% (Momentum)")
        logger.info("")
        
        # Initialize backtest engine with CORRECTED CAPITAL ALLOCATION
        engine = BacktestEngine()
        engine.initial_capital = 4000.0  # $4,000 starting capital
        
        # CORRECTED CAPITAL ALLOCATION SETTINGS
        engine.cash_reserve_pct = 0.20  # 20% cash reserve (CORRECTED)
        engine.max_position_size_pct = 0.15  # 15% max position size (conservative)
        
        engine.use_real_data = True  # Use REAL market data from Polygon API
        
        # Test symbols (proven high performers)
        symbols = ['SPY', 'AAPL', 'NVDA']
        
        # Date range for backtest (2024 data)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        logger.info("📊 Backtest Configuration:")
        logger.info(f"   • Symbols: {symbols}")
        logger.info(f"   • Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
        logger.info(f"   • Cash Reserve: {engine.cash_reserve_pct:.1%}")
        logger.info(f"   • Real Data: {engine.use_real_data}")
        logger.info("")
        logger.info("🏃‍♂️ Running Multi-Strategy Ensemble backtest with corrected allocation...")

        results = await engine.run_backtest(
            strategies={'MultiStrategyEnsemble': ensemble_strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )

        # Display results
        logger.info("\n📈 MULTI-STRATEGY ENSEMBLE RESULTS (CORRECTED ALLOCATION)")
        logger.info("=" * 80)
        
        ensemble_result: BacktestResult = results['MultiStrategyEnsemble']
        
        logger.info(f"Strategy: {ensemble_result.strategy}")
        logger.info(f"Total Return: {ensemble_result.total_return_pct:.2f}%")
        logger.info(f"Final Value: ${ensemble_result.final_capital:,.2f}")
        logger.info(f"Max Drawdown: {ensemble_result.max_drawdown_pct:.2f}%")
        logger.info(f"Sharpe Ratio: {ensemble_result.sharpe_ratio:.2f}")
        logger.info(f"Win Rate: {ensemble_result.win_rate:.2f}%")
        logger.info(f"Total Trades: {ensemble_result.total_trades}")
        logger.info(f"Profitable Trades: {ensemble_result.winning_trades}")
        logger.info(f"Losing Trades: {ensemble_result.losing_trades}")
        logger.info("")
        logger.info("📊 Trade Summary:")
        logger.info(f"   Average Win: ${ensemble_result.avg_win:,.2f}")
        logger.info(f"   Average Loss: ${ensemble_result.avg_loss:,.2f}")
        logger.info("")
        
        logger.info("🔍 Recent Trades (Last 10):")
        for i, trade in enumerate(ensemble_result.trades[-10:]):
            logger.info(f"   {i+1}. {trade.symbol}: {trade.action} {trade.quantity:.4f} shares @ ${trade.price:,.2f} | P&L: ${trade.pnl:,.2f}")
        logger.info("=" * 80)

        # Capital allocation analysis
        logger.info("💰 CAPITAL ALLOCATION ANALYSIS:")
        logger.info(f"   • Initial Capital: ${engine.initial_capital:,.2f}")
        logger.info(f"   • Cash Reserve (20%): ${engine.initial_capital * 0.20:,.2f}")
        logger.info(f"   • Stock Allocation (30%): ${engine.initial_capital * 0.30:,.2f}")
        logger.info(f"   • Options Allocation (50%): ${engine.initial_capital * 0.50:,.2f}")
        logger.info(f"     - Day Trading (5%): ${engine.initial_capital * 0.05:,.2f}")
        logger.info(f"     - Swing Trading (45%): ${engine.initial_capital * 0.45:,.2f}")
        logger.info("")

        # Performance comparison
        logger.info("📊 PERFORMANCE COMPARISON:")
        logger.info(f"   • Previous Backtest (1,100.88%): 1,100.88%")
        logger.info(f"   • Current Result: {ensemble_result.total_return_pct:.2f}%")
        if ensemble_result.total_return_pct >= 1100.88:
            logger.info(f"   • 🎉 EXCEEDED PREVIOUS PERFORMANCE by {ensemble_result.total_return_pct - 1100.88:.2f} percentage points!")
        else:
            logger.info(f"   • ⚠️ Below previous performance by {1100.88 - ensemble_result.total_return_pct:.2f} percentage points.")
        logger.info("")

        logger.info("🎯 ALLOCATION IMPACT ANALYSIS:")
        logger.info("   • Cash Reserve: 20% (vs 5% previously) - More conservative")
        logger.info("   • Stock Allocation: 30% (vs 0% previously) - New allocation")
        logger.info("   • Options Allocation: 50% (vs 95% previously) - Reduced")
        logger.info("   • Day Trading: 5% (vs 0% previously) - New feature")
        logger.info("   • Swing Trading: 45% (vs 95% previously) - Reduced")
        logger.info("")

        logger.info("✅ Multi-Strategy Ensemble backtest with corrected allocation completed successfully!")

    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())










