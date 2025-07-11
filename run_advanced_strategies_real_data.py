#!/usr/bin/env python3
"""
Run Advanced Strategies Backtest with Real Market Data
Uses AI-enhanced strategies instead of basic strategies for better performance
"""

import os
import sys
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import traceback

print(f"🔍 DEBUG: ADVANCED STRATEGIES SCRIPT STARTED - {datetime.now()}")

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


async def run_advanced_strategies_backtest():
    """Run advanced strategies backtest with real market data"""
    
    print("🚀 ADVANCED STRATEGIES BACKTEST WITH REAL MARKET DATA")
    print("=" * 70)
    print("🤖 Using AI-Enhanced Strategies for Better Performance")
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
    
    # ADVANCED STRATEGIES - AI-Enhanced versions instead of basic
    advanced_strategies_to_test = [
        'RSI_AI_Enhanced',              # AI-enhanced RSI with sentiment analysis
        'BollingerBands_AI_Enhanced',   # AI-enhanced Bollinger Bands
        'MACD_AI_Enhanced',             # AI-enhanced MACD with momentum analysis
        'SMACrossover_AI_Enhanced',     # AI-enhanced SMA Crossover
        'News_Enhanced',                # Technical + News sentiment + AI
        'EnhancedEntryExit',            # Sophisticated entry-exit management
        'PortfolioStrategy'             # Multi-strategy confirmation
    ]
    
    # Basic strategies for comparison (showing the difference)
    basic_strategies_for_comparison = [
        'BollingerBandsStrategy',      # Basic version
        'RSIStrategy',                 # Basic version
        'MACDStrategy',                # Basic version
        'SMACrossoverStrategy'         # Basic version
    ]
    
    # Advanced portfolio combinations
    advanced_portfolio_combinations = [
        {
            'name': 'AI_Enhanced_Conservative',
            'description': 'AI-Enhanced RSI + Bollinger Bands',
            'strategies': ['RSI_AI_Enhanced', 'BollingerBands_AI_Enhanced']
        },
        {
            'name': 'AI_Enhanced_Balanced',
            'description': 'AI-Enhanced RSI + Bollinger Bands + MACD',
            'strategies': ['RSI_AI_Enhanced', 'BollingerBands_AI_Enhanced', 'MACD_AI_Enhanced']
        },
        {
            'name': 'AI_Enhanced_Aggressive',
            'description': 'All AI-Enhanced Strategies',
            'strategies': ['RSI_AI_Enhanced', 'BollingerBands_AI_Enhanced', 'MACD_AI_Enhanced', 'News_Enhanced']
        }
    ]
    
    print(f"📊 Advanced Backtest Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} stocks")
    print(f"   🤖 Advanced Strategies: {', '.join(advanced_strategies_to_test)}")
    print(f"   🗄️  Data Source: Real Market Data from Database")
    print(f"   🧠 AI Enhancement: ENABLED")
    print(f"   🎯 LLM Evaluation: ENABLED")
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
    
    # Run advanced strategies backtest
    print(f"\n🤖 RUNNING ADVANCED STRATEGIES BACKTEST")
    print("-" * 50)
    
    # Initialize backtest engine with real data, caching, and LLM evaluation
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    engine.use_llm_evaluation = True  # Enable LLM evaluation for advanced strategies
    
    # Run the advanced strategies backtest
    start_time = datetime.now()
    
    print(f"🔍 DEBUG: Running advanced strategies backtest...")
    advanced_results = await engine.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=advanced_strategies_to_test
    )
    print(f"🔍 DEBUG: Advanced strategies backtest completed")
    
    # Run basic strategies for comparison
    print(f"\n📊 RUNNING BASIC STRATEGIES FOR COMPARISON")
    print("-" * 50)
    
    engine_basic = BacktestEngine(use_real_data=True, use_cache=True)
    engine_basic.use_llm_evaluation = False  # No LLM for basic strategies
    
    basic_results = await engine_basic.run_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategies=basic_strategies_for_comparison
    )
    
    # Run advanced portfolio combinations
    print(f"\n📈 RUNNING ADVANCED PORTFOLIO COMBINATIONS")
    print("-" * 50)
    
    portfolio_results = await test_advanced_portfolio_combinations(
        engine, symbols, start_date, end_date, advanced_portfolio_combinations
    )
    
    # Generate comparison report
    print(f"\n📊 ADVANCED vs BASIC STRATEGIES COMPARISON")
    print("=" * 70)
    
    # Advanced Strategies Results
    print(f"\n🤖 AI-ENHANCED STRATEGIES PERFORMANCE:")
    print("-" * 50)
    
    advanced_total_return = 0
    advanced_strategy_count = 0
    
    if advanced_results:
        for strategy_name, result in advanced_results.items():
            if result and hasattr(result, 'total_return_pct'):
                return_pct = result.total_return_pct
                advanced_total_return += return_pct
                advanced_strategy_count += 1
                print(f"   {strategy_name}: {return_pct:.2f}%")
    
    if advanced_strategy_count > 0:
        advanced_avg_return = advanced_total_return / advanced_strategy_count
        print(f"\n   Average AI-Enhanced Return: {advanced_avg_return:.2f}%")
    
    # Basic Strategies Results
    print(f"\n📊 BASIC STRATEGIES PERFORMANCE:")
    print("-" * 50)
    
    basic_total_return = 0
    basic_strategy_count = 0
    
    if basic_results:
        for strategy_name, result in basic_results.items():
            if result and hasattr(result, 'total_return_pct'):
                return_pct = result.total_return_pct
                basic_total_return += return_pct
                basic_strategy_count += 1
                print(f"   {strategy_name}: {return_pct:.2f}%")
    
    if basic_strategy_count > 0:
        basic_avg_return = basic_total_return / basic_strategy_count
        print(f"\n   Average Basic Strategy Return: {basic_avg_return:.2f}%")
    
    # Performance Comparison
    print(f"\n📈 PERFORMANCE COMPARISON:")
    print("-" * 50)
    
    if advanced_strategy_count > 0 and basic_strategy_count > 0:
        improvement = advanced_avg_return - basic_avg_return
        improvement_pct = (improvement / abs(basic_avg_return)) * 100 if basic_avg_return != 0 else 0
        
        print(f"   AI-Enhanced vs Basic: {improvement:+.2f}% improvement")
        print(f"   Improvement Percentage: {improvement_pct:+.1f}%")
        
        if improvement > 0:
            print(f"   ✅ ADVANCED STRATEGIES OUTPERFORM BASIC STRATEGIES!")
        else:
            print(f"   ⚠️  Basic strategies still performing better")
    
    # Portfolio Results
    print(f"\n📊 ADVANCED PORTFOLIO COMBINATIONS:")
    print("-" * 50)
    
    if portfolio_results:
        for portfolio_result in portfolio_results:
            print(f"   {portfolio_result['name']}: {portfolio_result['total_return']:.2f}%")
    
    # Store results in database
    print(f"\n💾 STORING RESULTS IN DATABASE")
    print("-" * 50)
    
    database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
    
    if advanced_results:
        valid_results = {strategy: result for strategy, result in advanced_results.items() if result is not None}
        
        if valid_results:
            try:
                await engine.store_results(valid_results, symbols, start_date, end_date, database_only)
                print(f"✅ Advanced strategy results stored in database")
            except Exception as e:
                print(f"❌ Exception in store_results: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ No valid advanced results to store in database")
    else:
        print(f"❌ No advanced results to store in database")
    
    # Store basic results for comparison
    if basic_results:
        valid_basic_results = {strategy: result for strategy, result in basic_results.items() if result is not None}
        
        if valid_basic_results:
            try:
                await engine_basic.store_results(valid_basic_results, symbols, start_date, end_date, database_only)
                print(f"✅ Basic strategy results stored in database")
            except Exception as e:
                print(f"❌ Exception in store_results: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Store portfolio results
    if portfolio_results:
        for portfolio_result in portfolio_results:
            try:
                from src.backtesting.backtest_engine import BacktestResult, BacktestTrade
                portfolio_backtest_result = BacktestResult(
                    strategy=portfolio_result['name'],
                    initial_capital=100000.0,
                    final_capital=100000.0 * (1 + portfolio_result['total_return'] / 100),
                    total_return=portfolio_result['total_return'],
                    total_return_pct=portfolio_result['total_return'],
                    max_drawdown_pct=portfolio_result['max_drawdown'],
                    sharpe_ratio=portfolio_result.get('sharpe_ratio', 0.0),
                    total_trades=portfolio_result.get('total_trades', 0),
                    win_rate=portfolio_result.get('win_rate', 0.0),
                    profit_factor=portfolio_result.get('profit_factor', 0.0),
                    avg_win_pct=portfolio_result.get('avg_win_pct', 0.0),
                    avg_loss_pct=portfolio_result.get('avg_loss_pct', 0.0)
                )
                
                # Store portfolio result
                await engine.store_results({portfolio_result['name']: portfolio_backtest_result}, 
                                        symbols, start_date, end_date, database_only)
                print(f"✅ Portfolio result '{portfolio_result['name']}' stored in database")
            except Exception as e:
                print(f"❌ Exception storing portfolio result: {str(e)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n🎉 ADVANCED STRATEGIES BACKTEST COMPLETED!")
    print(f"⏱️  Duration: {duration}")
    print(f"📊 Advanced Strategies Tested: {len(advanced_strategies_to_test)}")
    print(f"📊 Basic Strategies Compared: {len(basic_strategies_for_comparison)}")
    print(f"📊 Portfolio Combinations: {len(advanced_portfolio_combinations)}")
    print("=" * 70)


async def test_advanced_portfolio_combinations(engine, symbols, start_date, end_date, portfolio_combinations):
    """Test advanced portfolio combinations"""
    
    portfolio_results = []
    
    for combo in portfolio_combinations:
        print(f"🎯 Testing portfolio: {combo['name']} - {combo['description']}")
        
        try:
            # Run backtest for this portfolio combination
            results = await engine.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                strategies=combo['strategies']
            )
            
            if results:
                # Calculate portfolio performance
                total_return = 0
                total_trades = 0
                strategy_count = 0
                
                for strategy_name, result in results.items():
                    if result and hasattr(result, 'total_return_pct'):
                        total_return += result.total_return_pct
                        total_trades += getattr(result, 'total_trades', 0)
                        strategy_count += 1
                
                if strategy_count > 0:
                    avg_return = total_return / strategy_count
                    portfolio_result = {
                        'name': combo['name'],
                        'description': combo['description'],
                        'total_return': avg_return,
                        'total_trades': total_trades,
                        'max_drawdown': 0.0,  # Simplified
                        'sharpe_ratio': 0.0,   # Simplified
                        'win_rate': 0.0,       # Simplified
                        'profit_factor': 0.0,  # Simplified
                        'avg_win_pct': 0.0,    # Simplified
                        'avg_loss_pct': 0.0    # Simplified
                    }
                    portfolio_results.append(portfolio_result)
                    print(f"   ✅ {combo['name']}: {avg_return:.2f}%")
                else:
                    print(f"   ❌ {combo['name']}: No valid results")
            else:
                print(f"   ❌ {combo['name']}: No results returned")
                
        except Exception as e:
            print(f"   ❌ {combo['name']}: Error - {str(e)}")
            continue
    
    return portfolio_results


async def main():
    """Run advanced strategies backtest"""
    try:
        await run_advanced_strategies_backtest()
    except Exception as e:
        print(f"❌ Error in advanced strategies backtest: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 