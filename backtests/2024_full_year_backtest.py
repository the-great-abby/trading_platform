#!/usr/bin/env python3
"""
2024 Full Year Backtest Simulation
Using MultiStrategyEnsemble with current allocation settings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.engine.backtest_engine import BacktestEngine, BacktestResult
from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble
from src.strategies.strategy_registry import StrategyRegistry
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_2024_backtest():
    """Run a comprehensive 2024 backtest with current allocation settings"""
    
    print("🚀 Starting 2024 Full Year Backtest Simulation")
    print("=" * 60)
    
    # Initialize the backtest engine
    engine = BacktestEngine()
    
    # Configure engine settings for 2024
    engine.initial_capital = 4000.0
    engine.start_date = "2024-01-01"
    engine.end_date = "2024-12-31"
    
    # Current allocation settings (matching paper trading config)
    engine.cash_reserve_pct = 0.05      # 5% cash reserve
    engine.stock_allocation_pct = 0.20  # 20% stocks
    engine.options_allocation_pct = 0.75 # 75% options
    engine.options_day_trading_pct = 0.25 # 25% of options for day trading
    engine.options_swing_trading_pct = 0.50 # 50% of options for swing trading
    
    # Trading settings
    engine.max_position_size_pct = 0.20  # 20% max position size
    engine.use_real_data = True
    engine.trading_interval_minutes = 60  # 1-hour intervals
    
    # Symbols to trade (high performers from previous backtests)
    symbols = ['SPY', 'AAPL', 'NVDA', 'QQQ']
    
    print(f"📊 Configuration:")
    print(f"   Initial Capital: ${engine.initial_capital:,.0f}")
    print(f"   Date Range: {engine.start_date} to {engine.end_date}")
    print(f"   Cash Reserve: {engine.cash_reserve_pct*100:.0f}%")
    print(f"   Stocks: {engine.stock_allocation_pct*100:.0f}%")
    print(f"   Options: {engine.options_allocation_pct*100:.0f}%")
    print(f"   Day Trading: {engine.options_day_trading_pct*100:.0f}% of options")
    print(f"   Swing Trading: {engine.options_swing_trading_pct*100:.0f}% of options")
    print(f"   Max Position Size: {engine.max_position_size_pct*100:.0f}%")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Real Data: {engine.use_real_data}")
    print()
    
    # Register and initialize the strategy
    registry = StrategyRegistry()
    strategy = MultiStrategyEnsemble()
    
    print("🎯 Strategy: MultiStrategyEnsemble")
    print("   - Adaptive Sector Wave Strategy")
    print("   - Elliott Wave Analysis")
    print("   - Ichimoku Integration")
    print("   - Multi-signal confirmation")
    print()
    
    try:
        # Run the backtest
        print("⚡ Running backtest...")
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=engine.start_date,
            end_date=engine.end_date,
            strategies=['MultiStrategyEnsemble']
        )
        
        # Get the result for our strategy
        result = results.get('MultiStrategyEnsemble')
        if not result:
            print("❌ No results found for MultiStrategyEnsemble")
            return None
        
        # Display results
        print("\n" + "=" * 60)
        print("📈 BACKTEST RESULTS - 2024 FULL YEAR")
        print("=" * 60)
        
        print(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
        print(f"💰 Final Capital: ${result.final_capital:,.2f}")
        print(f"📊 Total Return: ${result.total_return:,.2f}")
        print(f"📊 Total Return %: {result.total_return_pct:.2f}%")
        print(f"📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
        print(f"📊 Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"📈 Total Trades: {result.total_trades}")
        print(f"📊 Winning Trades: {result.winning_trades}")
        print(f"📉 Losing Trades: {result.losing_trades}")
        
        # Calculate win rate
        win_rate = (result.winning_trades / result.total_trades * 100) if result.total_trades > 0 else 0
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print()
        
        # Trade breakdown by symbol
        if hasattr(result, 'symbol_performance') and result.symbol_performance:
            print("📊 Performance by Symbol:")
            for symbol, perf in result.symbol_performance.items():
                print(f"   {symbol}: {perf['return']*100:+.2f}% ({perf['trades']} trades)")
            print()
        
        # Strategy component analysis
        if hasattr(result, 'strategy_performance') and result.strategy_performance:
            print("🎯 Strategy Component Analysis:")
            for strategy_name, perf in result.strategy_performance.items():
                print(f"   {strategy_name}: {perf['return']*100:+.2f}% win rate")
            print()
        
        # Monthly breakdown
        if hasattr(result, 'monthly_returns') and result.monthly_returns:
            print("📅 Monthly Returns:")
            for month, ret in result.monthly_returns.items():
                print(f"   {month}: {ret*100:+.2f}%")
            print()
        
        print("✅ Backtest completed successfully!")
        
        return result
        
    except Exception as e:
        print(f"❌ Backtest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the backtest
    result = asyncio.run(run_2024_backtest())
