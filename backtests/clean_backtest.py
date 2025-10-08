#!/usr/bin/env python3
"""
Clean AdaptiveSectorWaveStrategy Backtest
Simplified logging and cleaner output
"""

import os
import asyncio
import logging
from datetime import datetime

# Set up environment
os.environ['POLYGON_API_KEY'] = 'vV3WBYZ1fLYcNYKIeH5jVyYfOzOjZRYM'
os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
os.environ['DATABASE_ONLY'] = 'false'
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'
os.environ['DISABLE_LLM_STRATEGIES'] = 'true'
os.environ['DISABLE_AI_STRATEGIES'] = 'true'
os.environ['ENABLE_LLM_EVALUATION'] = 'false'

# Import after env setup
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
from src.strategies.strategy_registry import StrategyRegistry

# Configure minimal logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(levelname)s: %(message)s'
)

async def run_clean_backtest():
    """Run a clean adaptive sector wave backtest"""
    
    # Initialize backtest engine
    engine = BacktestEngine()
    engine.initial_capital = 4000.0
    
    # Initialize strategy
    strategy = AdaptiveSectorWaveStrategy(
        elliott_wave_min_confidence=0.05,  # Allow lower confidence patterns
        ichimoku_min_confidence=0.05,     # Allow lower confidence patterns
        lookback_period=50
    )
    
    # Register strategy manually to avoid discovery issues
    engine.strategy_registry = StrategyRegistry()
    engine.strategy_registry.strategies = {'AdaptiveSectorsWave': strategy}
    
    # Symbols to test - only those with proven Elliott Wave performance
    # Based on best_symbols from the strategy: SPY, QQQ, IWM, AAPL, GOOGL, AMZN, META, NVDA, TSLA, AMD
    symbols = ['SPY', 'AAPL', 'NVDA']  # Top performers across different pattern types
    
    # Date range for backtest (2024 for better options data coverage)
    start_date = '2024-01-01'
    end_date = '2024-06-30'  # Shorter period for faster testing
    
    print("🔄 Running Clean Adaptive Sector Wave Backtest")
    print(f"📅 Date Range: {start_date} to {end_date}")
    print(f"💰 Initial Capital: ${engine.initial_capital:,.2f}")
    print(f"📊 Symbols: {', '.join(symbols)}")
    print("=" * 60)
    
    try:
        start_time = datetime.now()
        
        # Run backtest
        results = await engine.run_backtest(
            strategies={'AdaptiveSectorWaveStrategy': strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Display clean results
        if results and 'AdaptiveSectorWaveStrategy' in results:
            result = results['AdaptiveSectorWaveStrategy']
            
            print("\n" + "=" * 60)
            print("🎯 BACKTEST RESULTS")
            print("=" * 60)
            print(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
            print(f"💰 Final Capital: ${result.final_capital:,.2f}")
            print(f"📈 Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
            print(f"📊 Total Trades: {result.total_trades}")
            print(f"🎯 Win Rate: {result.win_rate:.2%}")
            print(f"📈 Profit Factor: {result.profit_factor:.3f}")
            print(f"📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
            print(f"⏱️ Execution Time: {execution_time:.1f} seconds")
            
            # Show trade details if we have trades
            if result.trades:
                print(f"\n📋 TRADE SUMMARY:")
                profit_trades = [t for t in result.trades if t.pnl > 0]
                loss_trades = [t for t in result.trades if t.pnl < 0]
                print(f"  ✅ Profitable trades: {len(profit_trades)}")
                print(f"  ❌ Loss trades: {len(loss_trades)}")
                
                if profit_trades:
                    avg_profit = sum(t.pnl for t in profit_trades) / len(profit_trades)
                    print(f"  💰 Average Profit: ${avg_profit:.2f}")
                
                if loss_trades:
                    avg_loss = sum(t.pnl for t in loss_trades) / len(loss_trades)
                    print(f"  📉 Average Loss: ${avg_loss:.2f}")
                
                print(f"\n📋 Recent Trades:")
                for i, trade in enumerate(result.trades[-5:], 1):  # Show last 5 trades
                    action_emoji = "🟢" if trade.action == "BUY" else "🔴"
                    print(f"  {action_emoji} {trade.action} {trade.symbol} @ ${trade.price:.2f} "
                          f"({trade.quantity:.4f} shares) - P&L: ${trade.pnl:.2f}")
            else:
                print("\n❌ No trades executed")
                
        print(f"\n✅ Backtest completed in {execution_time:.1f}s!")
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_clean_backtest())
