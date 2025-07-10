#!/usr/bin/env python3
"""
Portfolio Strategy Backtest - Tests multi-strategy combinations with risk management
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import logging
from typing import Dict, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.portfolio_strategy import PortfolioStrategy
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.services.database.market_data_service import MarketDataService
from src.utils.config import get_config
from src.utils.trading_config import get_symbols


async def run_portfolio_backtest():
    """Run portfolio backtest with real market data"""
    config = get_config()
    
    # Initialize services
    market_data_service = MarketDataService(config.database_url)
    
    # Use centralized symbol list
    symbols = get_symbols()
    
    # Calculate date range (1 year ago to today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"📊 Running portfolio backtest for {len(symbols)} symbols")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    print("🚀 PORTFOLIO STRATEGY BACKTEST WITH RISK MANAGEMENT")
    print("=" * 70)
    
    # Configuration
    initial_capital = 100000.0
    
    print(f"📊 Test Configuration:")
    print(f"   💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"   📅 Test Period: {start_date} to {end_date}")
    print(f"   📈 Symbols: {len(symbols)} stocks")
    print(f"   🗄️  Data Source: Real Market Data from Database")
    print()
    
    # Initialize backtest engine
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    
    # Define portfolio configurations
    portfolio_configs = [
        {
            'name': 'Conservative_Portfolio',
            'description': 'Bollinger Bands + RSI with Mean Reversion confirmation',
            'primary_strategies': ['BollingerBandsStrategy', 'RSIStrategy'],
            'confirmation_strategies': ['MeanReversionStrategy'],
            'min_confirmations': 1,
            'risk_per_trade': 0.015,  # 1.5% risk
            'max_position_size': 0.08,  # 8% max position
            'stop_loss_pct': 0.04,  # 4% stop loss
            'take_profit_pct': 0.12,  # 12% take profit
            'volatility_threshold': 0.025  # 2.5% volatility threshold
        },
        {
            'name': 'Balanced_Portfolio',
            'description': 'Bollinger Bands + RSI + Momentum with Mean Reversion confirmation',
            'primary_strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MomentumStrategy'],
            'confirmation_strategies': ['MeanReversionStrategy'],
            'min_confirmations': 1,
            'risk_per_trade': 0.02,  # 2% risk
            'max_position_size': 0.1,  # 10% max position
            'stop_loss_pct': 0.05,  # 5% stop loss
            'take_profit_pct': 0.15,  # 15% take profit
            'volatility_threshold': 0.03  # 3% volatility threshold
        },
        {
            'name': 'Aggressive_Portfolio',
            'description': 'All strategies with strict confirmation requirements',
            'primary_strategies': ['BollingerBandsStrategy', 'RSIStrategy', 'MomentumStrategy'],
            'confirmation_strategies': ['MeanReversionStrategy', 'VolatilityBreakoutStrategy'],
            'min_confirmations': 2,
            'risk_per_trade': 0.025,  # 2.5% risk
            'max_position_size': 0.12,  # 12% max position
            'stop_loss_pct': 0.06,  # 6% stop loss
            'take_profit_pct': 0.18,  # 18% take profit
            'volatility_threshold': 0.035  # 3.5% volatility threshold
        },
        {
            'name': 'Risk_Averse_Portfolio',
            'description': 'Conservative with strict risk management',
            'primary_strategies': ['BollingerBandsStrategy'],
            'confirmation_strategies': ['RSIStrategy', 'MeanReversionStrategy'],
            'min_confirmations': 2,
            'risk_per_trade': 0.01,  # 1% risk
            'max_position_size': 0.05,  # 5% max position
            'stop_loss_pct': 0.03,  # 3% stop loss
            'take_profit_pct': 0.10,  # 10% take profit
            'volatility_threshold': 0.02  # 2% volatility threshold
        }
    ]
    
    # Strategy class mapping
    strategy_classes = {
        'BollingerBandsStrategy': BollingerBandsStrategy,
        'RSIStrategy': RSIStrategy,
        'MeanReversionStrategy': MeanReversionStrategy,
        'MomentumStrategy': MomentumStrategy,
        'VolatilityBreakoutStrategy': VolatilityBreakoutStrategy
    }
    
    results = []
    
    print("🏃 RUNNING PORTFOLIO BACKTESTS")
    print("-" * 50)
    
    for config in portfolio_configs:
        print(f"\n📊 Testing: {config['name']}")
        print(f"   📝 {config['description']}")
        print(f"   🎯 Primary: {', '.join(config['primary_strategies'])}")
        print(f"   ✅ Confirmation: {', '.join(config['confirmation_strategies'])}")
        print(f"   🔒 Risk per trade: {config['risk_per_trade']*100:.1f}%")
        print(f"   📏 Max position: {config['max_position_size']*100:.1f}%")
        
        try:
            # Create portfolio strategy
            portfolio = PortfolioStrategy(
                primary_strategies=config['primary_strategies'],
                confirmation_strategies=config['confirmation_strategies'],
                min_confirmations=config['min_confirmations'],
                risk_per_trade=config['risk_per_trade'],
                max_position_size=config['max_position_size'],
                stop_loss_pct=config['stop_loss_pct'],
                take_profit_pct=config['take_profit_pct'],
                volatility_threshold=config['volatility_threshold']
            )
            
            # Initialize strategies
            await portfolio.initialize_strategies(strategy_classes)
            
            # Run backtest
            result = await engine._run_strategy_backtest(config['name'], 
                                                       await engine._get_market_data(symbols, start_date, end_date))
            
            if result:
                results.append({
                    'config': config,
                    'result': result
                })
                
                print(f"   ✅ Return: {result.total_return_pct:.2f}%")
                print(f"   📊 Sharpe: {result.sharpe_ratio:.2f}")
                print(f"   🔄 Trades: {result.total_trades}")
                print(f"   🎯 Win Rate: {result.win_rate*100:.1f}%")
                print(f"   📉 Max DD: {result.max_drawdown_pct:.2f}%")
            else:
                print(f"   ❌ Failed to run backtest")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue
    
    # Display results summary
    print("\n" + "=" * 70)
    print("📊 PORTFOLIO STRATEGY RESULTS SUMMARY")
    print("=" * 70)
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['result'].total_return_pct, reverse=True)
        
        print(f"{'Portfolio':<25} {'Return %':<10} {'Sharpe':<8} {'Trades':<8} {'Win Rate %':<12} {'Max DD %':<10}")
        print("-" * 80)
        
        for item in results:
            config = item['config']
            result = item['result']
            
            print(f"{config['name']:<25} {result.total_return_pct:>8.2f}% {result.sharpe_ratio:>6.2f} "
                  f"{result.total_trades:>6} {result.win_rate*100:>10.1f}% {result.max_drawdown_pct:>8.2f}%")
        
        # Best performing portfolio
        best = results[0]
        print(f"\n🏆 BEST PERFORMING PORTFOLIO: {best['config']['name']}")
        print(f"   📈 Return: {best['result'].total_return_pct:.2f}%")
        print(f"   📊 Sharpe Ratio: {best['result'].sharpe_ratio:.2f}")
        print(f"   🔄 Total Trades: {best['result'].total_trades}")
        print(f"   ✅ Win Rate: {best['result'].win_rate*100:.1f}%")
        print(f"   📉 Max Drawdown: {best['result'].max_drawdown_pct:.2f}%")
        print(f"   💰 Final Capital: ${best['result'].final_capital:,.2f}")
        
        # Risk management analysis
        print(f"\n🔒 RISK MANAGEMENT ANALYSIS")
        print(f"   🎯 Risk per Trade: {best['config']['risk_per_trade']*100:.1f}%")
        print(f"   📏 Max Position Size: {best['config']['max_position_size']*100:.1f}%")
        print(f"   🛑 Stop Loss: {best['config']['stop_loss_pct']*100:.1f}%")
        print(f"   🎯 Take Profit: {best['config']['take_profit_pct']*100:.1f}%")
        print(f"   📊 Volatility Threshold: {best['config']['volatility_threshold']*100:.1f}%")
        
        # Strategy combination analysis
        print(f"\n🎯 STRATEGY COMBINATION ANALYSIS")
        print(f"   🚀 Primary Strategies: {', '.join(best['config']['primary_strategies'])}")
        print(f"   ✅ Confirmation Strategies: {', '.join(best['config']['confirmation_strategies'])}")
        print(f"   🔍 Min Confirmations Required: {best['config']['min_confirmations']}")
        
    else:
        print("❌ No successful backtest results")
    
    print(f"\n✅ Portfolio backtest completed!")
    print(f"📈 Total portfolios tested: {len(portfolio_configs)}")
    print(f"🎯 Successful backtests: {len(results)}")


if __name__ == "__main__":
    asyncio.run(run_portfolio_backtest()) 