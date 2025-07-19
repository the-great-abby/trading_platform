#!/usr/bin/env python3
"""
Run Backtest with Real Market Data
Uses the historical data we just captured in the database
"""

import os
import sys
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import traceback

print(f"🔍 DEBUG: SCRIPT STARTED - {datetime.now()}")

# Add src to path
sys.path.append('src')

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.results_exporter import BacktestResultsExporter
from src.services.database.market_data_service import MarketDataDatabaseService, MarketDataService
from src.services.database.backtest_results_service import BacktestResultsService
from src.services.backtest.backtest_data_scanner import BacktestDataScanner
from src.utils.config import get_config
from src.utils.trading_config import get_symbols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_comprehensive_backtest():
    """Run comprehensive backtest with real market data"""
    
    print("🚀 COMPREHENSIVE BACKTEST WITH REAL MARKET DATA")
    print("=" * 70)
    
    # Configuration
    initial_capital = 100000.0  # $100,000 starting capital
    
    # Use the data we just captured (extended date range)
    start_date = "2023-07-06"  # Our data starts from this date
    end_date = "2025-07-03"    # Use consistent end date for all symbols
    
    # Symbols we have data for (from our recent data capture)
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',  # Tech stocks
        'JPM', 'GS', 'PFE', 'MRK', 'UNH',          # Finance & Healthcare
        'SPY', 'VTI'                               # ETFs
    ]
    
    # Test multiple strategies including portfolio combinations
    strategies_to_test = [
        'BollingerBandsStrategy',      # Best performer: +131.77%
        'RSIStrategy',                 # Good performer: +44.92%
        'MeanReversionStrategy',       # Best new strategy: -10.46%
        'MomentumStrategy',            # New: -67.47%
        'VolatilityBreakoutStrategy',  # New: -43.20%
        'NewsEnhancedStrategy',        # Poor: -101.09%
        'MACDStrategy',                # Poor: -78.68%
        'SMACrossoverStrategy'         # Worst: -93.02%
    ]
    
    # Portfolio combinations to test
    portfolio_combinations = [
        {
            'name': 'Conservative_Combo',
            'description': 'Bollinger Bands + RSI (Best performers)',
            'strategies': ['BollingerBandsStrategy', 'RSIStrategy']
        },
        {
            'name': 'Balanced_Combo', 
            'description': 'Bollinger Bands + RSI + Mean Reversion',
            'strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MeanReversionStrategy']
        },
        {
            'name': 'Risk_Averse_Combo',
            'description': 'Only Bollinger Bands (Most conservative)',
            'strategies': ['BollingerBandsStrategy']
        }
    ]
    
    print(f"📊 Backtest Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} stocks")
    print(f"   🎯 Strategies: {', '.join(strategies_to_test)}")
    print(f"   🗄️  Data Source: Real Market Data from Database")
    print()
    
    # Check database coverage first
    print("🔍 CHECKING DATABASE COVERAGE")
    print("-" * 40)
    
    db_service = MarketDataDatabaseService()
    coverage = {}
    
    for symbol in symbols:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        data = db_service.get_historical_data(symbol, start_dt, end_dt)
        if data is not None:
            coverage[symbol] = len(data)
            print(f"   ✅ {symbol}: {len(data)} records")
        else:
            coverage[symbol] = 0
            print(f"   ❌ {symbol}: No data found")
    
    available_symbols = [s for s, count in coverage.items() if count > 0]
    print(f"\n📊 Available symbols with data: {len(available_symbols)}/{len(symbols)}")
    
    if len(available_symbols) == 0:
        print("❌ No data available for backtesting!")
        return
    
    # Run backtest with available symbols
    print(f"\n🏃 RUNNING BACKTEST WITH {len(available_symbols)} SYMBOLS")
    print("-" * 50)
    
    # Initialize backtest engine with real data and caching
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Run the backtest
    start_time = datetime.now()
    
    # Run individual strategy backtests
    print(f"🔍 DEBUG: About to call engine.run_backtest...")
    results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=strategies_to_test
    )
    print(f"🔍 DEBUG: engine.run_backtest completed, results = {results}")
    
    # Debug logging
    print(f"🔍 DEBUG: Results type: {type(results)}")
    print(f"🔍 DEBUG: Results content: {results}")
    if results:
        print(f"🔍 DEBUG: Results keys: {list(results.keys())}")
        print(f"🔍 DEBUG: Results values: {list(results.values())}")
        for key, value in results.items():
            print(f"🔍 DEBUG: {key} = {type(value)}: {value}")
    else:
        print(f"🔍 DEBUG: Results is empty or None")
    
    # Run portfolio combination backtests
    portfolio_results = await test_portfolio_combinations(
        engine, symbols, start_date, end_date, portfolio_combinations
    )
    
    # Store results in database
    print(f"🔍 DEBUG: ENTERING STORAGE SECTION")
    database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
    print(f"🔍 DEBUG: database_only = {database_only}")
    print(f"🔍 DEBUG: About to store results: {results is not None}")
    print(f"🔍 DEBUG: Results type: {type(results)}")
    print(f"🔍 DEBUG: Results content: {results}")
    
    if results:
        print(f"🔍 DEBUG: Results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
        print(f"🔍 DEBUG: Results values: {list(results.values()) if isinstance(results, dict) else 'Not a dict'}")
        
        # Filter out None results and create proper format for store_results
        valid_results = {strategy: result for strategy, result in results.items() if result is not None}
        print(f"🔍 DEBUG: valid_results count: {len(valid_results)}")
        print(f"🔍 DEBUG: valid_results keys: {list(valid_results.keys())}")
        
        if valid_results:
            print(f"🔍 DEBUG: About to call engine.store_results with {len(valid_results)} results")
            try:
                await engine.store_results(valid_results, symbols, start_date, end_date, database_only)
                print(f"✅ Individual strategy results stored in database")
            except Exception as e:
                print(f"❌ Exception in store_results: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ No valid results to store in database")
    else:
        print(f"❌ No results to store in database")
    
    # Store portfolio results in database
    if portfolio_results:
        for portfolio_result in portfolio_results:
            # Create a simplified result object for portfolio combinations
            from src.backtesting.backtest_engine import BacktestResult, BacktestTrade
            portfolio_backtest_result = BacktestResult(
                strategy=portfolio_result['name'],
                initial_capital=100000.0,
                final_capital=100000.0 * (1 + portfolio_result['total_return'] / 100),
                total_return=portfolio_result['total_return'],
                total_return_pct=portfolio_result['total_return'],
                max_drawdown_pct=portfolio_result['max_drawdown'],
                sharpe_ratio=portfolio_result['sharpe_ratio'],
                total_trades=portfolio_result['total_trades'],
                winning_trades=int(portfolio_result['total_trades'] * portfolio_result['win_rate']),
                losing_trades=int(portfolio_result['total_trades'] * (1 - portfolio_result['win_rate'])),
                win_rate=portfolio_result['win_rate'],
                profit_factor=portfolio_result.get('profit_factor', 1.0),
                avg_win=portfolio_result.get('avg_win', 0.0),
                avg_loss=portfolio_result.get('avg_loss', 0.0),
                trades=[],  # Portfolio results don't have individual trades
                equity_curve=pd.DataFrame(),  # Portfolio results don't have equity curve
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d")
            )
            
            # Store portfolio result
            run_id = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{portfolio_result['name']}"
            service = BacktestResultsService()
            
            # Convert BacktestResult to dictionary format
            portfolio_result_dict = {
                'initial_capital': portfolio_backtest_result.initial_capital,
                'final_capital': portfolio_backtest_result.final_capital,
                'total_return': portfolio_backtest_result.total_return,
                'total_return_pct': portfolio_backtest_result.total_return_pct,
                'max_drawdown_pct': portfolio_backtest_result.max_drawdown_pct,
                'sharpe_ratio': portfolio_backtest_result.sharpe_ratio,
                'total_trades': portfolio_backtest_result.total_trades,
                'winning_trades': portfolio_backtest_result.winning_trades,
                'losing_trades': portfolio_backtest_result.losing_trades,
                'win_rate': portfolio_backtest_result.win_rate,
                'profit_factor': portfolio_backtest_result.profit_factor,
                'avg_win': portfolio_backtest_result.avg_win,
                'avg_loss': portfolio_backtest_result.avg_loss,
                'trades': [],
                'equity_curve': portfolio_backtest_result.equity_curve
            }
            
            success = service.store_backtest_results(
                run_id=run_id,
                strategy_name=portfolio_result['name'],
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                result=portfolio_result_dict,
                database_only=database_only,
                data_provider="portfolio_combination"
            )
            
            if success:
                print(f"✅ Portfolio result '{portfolio_result['name']}' stored in database")
            else:
                print(f"❌ Failed to store portfolio result '{portfolio_result['name']}'")
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Display individual strategy results
    print("\n" + "=" * 70)
    print("📊 INDIVIDUAL STRATEGY RESULTS")
    print("=" * 70)
    
    if results:
        # Sort by total return
        sorted_results = sorted(results.values(), key=lambda x: x.total_return_pct, reverse=True)
        
        print(f"{'Strategy':<25} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate %':<12} {'Max DD %':<10}")
        print("-" * 80)
        
        for result in sorted_results:
            print(f"{result.strategy:<25} {result.total_return_pct:>8.2f}% {result.sharpe_ratio:>6.2f} "
                  f"{result.total_trades:>6} {result.win_rate*100:>10.1f}% {result.max_drawdown_pct:>8.2f}%")
    else:
        print("❌ No individual strategy results to display")
    
    # Display portfolio combination results
    if portfolio_results:
        print("\n" + "=" * 70)
        print("📊 PORTFOLIO COMBINATION RESULTS")
        print("=" * 70)
        
        # Sort by total return
        portfolio_results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"{'Portfolio':<25} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate %':<12} {'Max DD %':<10}")
        print("-" * 80)
        
        for result in portfolio_results:
            print(f"{result['name']:<25} {result['total_return']:>8.2f}% {result['sharpe_ratio']:>6.2f} "
                  f"{result['total_trades']:>6} {result['win_rate']*100:>10.1f}% {result['max_drawdown']:>8.2f}%")
        
        # Best portfolio combination
        best_portfolio = portfolio_results[0]
        print(f"\n🏆 BEST PORTFOLIO COMBINATION: {best_portfolio['name']}")
        print(f"   📈 Average Return: {best_portfolio['total_return']:.2f}%")
        print(f"   📊 Average Sharpe Ratio: {best_portfolio['sharpe_ratio']:.2f}")
        print(f"   🔄 Total Trades: {best_portfolio['total_trades']}")
        print(f"   ✅ Average Win Rate: {best_portfolio['win_rate']*100:.1f}%")
        print(f"   📉 Average Max Drawdown: {best_portfolio['max_drawdown']:.2f}%")
        print(f"   🎯 Strategies: {', '.join(best_portfolio['strategies'])}")
        
        # Risk management recommendations
        print(f"\n🔒 RISK MANAGEMENT RECOMMENDATIONS:")
        print(f"   🎯 Use {best_portfolio['name']} as primary strategy combination")
        print(f"   📏 Position Size: 5-10% of portfolio per trade")
        print(f"   🛑 Stop Loss: 3-5% per position")
        print(f"   🎯 Take Profit: 10-15% per position")
        print(f"   📊 Diversify across multiple symbols")
        print(f"   ⏰ Monitor and rebalance monthly")
    
    print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
    print(f"✅ Backtest completed successfully!")
    print(f"🎯 Database data coverage: {len(symbols)}/{len(symbols)} symbols")
    print(f"📈 Total strategies tested: {len(strategies_to_test)}")
    print(f"🎯 Portfolio combinations tested: {len(portfolio_combinations)}")
    
    print(f"🔍 DEBUG: SCRIPT COMPLETED SUCCESSFULLY - {datetime.now()}")


async def test_portfolio_combinations(engine, symbols, start_date, end_date, portfolio_combinations):
    """Test portfolio strategy combinations"""
    print("\n🎯 TESTING PORTFOLIO COMBINATIONS")
    print("-" * 50)
    
    portfolio_results = []
    
    for combo in portfolio_combinations:
        print(f"\n📊 Testing: {combo['name']}")
        print(f"   📝 {combo['description']}")
        print(f"   🎯 Strategies: {', '.join(combo['strategies'])}")
        
        try:
            # Run backtest for each strategy in the combination
            combo_results = []
            for strategy_name in combo['strategies']:
                result = await engine._run_strategy_backtest(strategy_name, 
                                                           await engine._get_market_data(symbols, start_date, end_date))
                if result:
                    combo_results.append(result)
            
            if combo_results:
                # Calculate combined metrics
                total_return = sum(r.total_return_pct for r in combo_results) / len(combo_results)
                total_trades = sum(r.total_trades for r in combo_results)
                avg_win_rate = sum(r.win_rate for r in combo_results) / len(combo_results)
                avg_sharpe = sum(r.sharpe_ratio for r in combo_results) / len(combo_results)
                avg_max_dd = sum(r.max_drawdown_pct for r in combo_results) / len(combo_results)
                
                portfolio_results.append({
                    'name': combo['name'],
                    'description': combo['description'],
                    'strategies': combo['strategies'],
                    'total_return': total_return,
                    'total_trades': total_trades,
                    'win_rate': avg_win_rate,
                    'sharpe_ratio': avg_sharpe,
                    'max_drawdown': avg_max_dd,
                    'individual_results': combo_results
                })
                
                print(f"   ✅ Avg Return: {total_return:.2f}%")
                print(f"   📊 Avg Sharpe: {avg_sharpe:.2f}")
                print(f"   🔄 Total Trades: {total_trades}")
                print(f"   🎯 Avg Win Rate: {avg_win_rate*100:.1f}%")
                print(f"   📉 Avg Max DD: {avg_max_dd:.2f}%")
            else:
                print(f"   ❌ No successful results")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue
    
    return portfolio_results


async def main():
    try:
        await run_comprehensive_backtest()
    except Exception as e:
        print("❌ Unhandled exception in main():", e)
        traceback.print_exc()
        logging.error("Unhandled exception in main(): %s", e)
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Unhandled exception at script level:", e)
        traceback.print_exc()
        logging.error("Unhandled exception at script level: %s", e)
        logging.error(traceback.format_exc()) 