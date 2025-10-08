#!/usr/bin/env python3
"""
Test Paper Trading Backtest
Verify that trades are occurring at realistic intervals
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.backtest_config import BacktestConfig, RiskProfile, load_config_from_env

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run a realistic backtest to verify trading behavior"""
    try:
        logger.info("🚀 Starting Paper Trading Backtest Verification")
        logger.info("=" * 80)
        
        # Use a short test period to see trading frequency
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Test with a few stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Test with simple strategies
        strategies = ['RSIStrategy', 'MACDStrategy', 'BollingerBandsStrategy']
        
        logger.info(f"📊 Test Configuration:")
        logger.info(f"   Period: {start_date} to {end_date} (90 days)")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Strategies: {strategies}")
        logger.info(f"   Initial Capital: $4,000 (paper trading amount)")
        logger.info("")
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        # Run backtest
        logger.info("🔄 Running backtest...")
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=strategies
        )
        
        # Analyze results
        logger.info("")
        logger.info("=" * 80)
        logger.info("📈 BACKTEST RESULTS - Trading Frequency Analysis")
        logger.info("=" * 80)
        
        if not results:
            logger.error("❌ No results returned")
            return
        
        for strategy_name, result in results.items():
            if result:
                logger.info(f"\n{strategy_name} Strategy:")
                logger.info(f"  Total Trades: {result.total_trades}")
                logger.info(f"  Total Days: 90")
                logger.info(f"  Trades per Day: {result.total_trades / 90:.2f}")
                logger.info(f"  Winning Trades: {result.winning_trades}")
                logger.info(f"  Losing Trades: {result.losing_trades}")
                logger.info(f"  Win Rate: {result.win_rate * 100:.1f}%")
                logger.info(f"  Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
                logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
                logger.info(f"  Max Drawdown: {result.max_drawdown_pct:.2f}%")
                
                # Show trade timing
                if result.trades:
                    logger.info(f"\n  Recent Trades (last 5):")
                    for trade in result.trades[-5:]:
                        logger.info(f"    {trade.timestamp} - {trade.action} {trade.quantity} {trade.symbol} @ ${trade.price:.2f}")
                    
                    # Calculate average days between trades
                    if len(result.trades) > 1:
                        trade_dates = [t.timestamp for t in result.trades]
                        time_diffs = [(trade_dates[i+1] - trade_dates[i]).total_seconds() / 86400 
                                     for i in range(len(trade_dates)-1)]
                        avg_days_between_trades = sum(time_diffs) / len(time_diffs) if time_diffs else 0
                        logger.info(f"\n  Average Days Between Trades: {avg_days_between_trades:.2f}")
            else:
                logger.warning(f"\n{strategy_name} Strategy: No results")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📝 ANALYSIS:")
        logger.info("=" * 80)
        logger.info("In a realistic backtest, trades occur when:")
        logger.info("  1. Strategy conditions are met (e.g., RSI oversold/overbought)")
        logger.info("  2. Market conditions are favorable")
        logger.info("  3. Risk management allows the trade")
        logger.info("")
        logger.info("Expected Behavior:")
        logger.info("  - Trades should occur every few days, not every 60 seconds")
        logger.info("  - Trading frequency: ~0.5-3 trades per day on average")
        logger.info("  - Paper trading config says max 6 trades per day")
        logger.info("")
        logger.info("🔍 If you saw trades occurring every 60 seconds, that's from the")
        logger.info("   paper trading SIMULATION script (setup_paper_trading.py),")
        logger.info("   which generates random trades for testing purposes.")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
