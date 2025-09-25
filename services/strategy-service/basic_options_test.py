#!/usr/bin/env python3
"""
Basic Options Strategies Test - Simple comparison without complex indexing
"""

import sys
import os
import asyncio
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.append('/app/src')

from src.services.database.market_data_service import MarketDataDatabaseService

def calculate_basic_options_strategies(data: pd.DataFrame) -> Dict[str, List[str]]:
    """Calculate basic options strategies with safe indexing"""
    strategies = {}
    close = data['Close']
    
    # Calculate indicators
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    volatility = close.pct_change().rolling(20).std()
    
    # Cash Secured Put Strategy
    signals = []
    for i in range(len(data)):
        if i < 50:  # Need 50 days for calculation
            signals.append('HOLD')
        else:
            try:
                current_price = close.iloc[i]
                current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
                
                # Sell puts when: price above SMA20, low volatility
                price_above_sma20 = current_price > sma_20.iloc[i]
                low_volatility = current_vol < 0.025
                
                if price_above_sma20 and low_volatility:
                    signals.append('SELL_PUT')
                else:
                    signals.append('HOLD')
            except (IndexError, KeyError):
                signals.append('HOLD')
    
    strategies['Cash Secured Put'] = signals
    
    # Covered Call Strategy
    signals = []
    for i in range(len(data)):
        if i < 50:
            signals.append('HOLD')
        else:
            try:
                current_price = close.iloc[i]
                current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
                
                # Sell calls when: price above SMA20, moderate volatility
                price_above_sma20 = current_price > sma_20.iloc[i]
                moderate_volatility = 0.015 < current_vol < 0.035
                
                if price_above_sma20 and moderate_volatility:
                    signals.append('SELL_CALL')
                else:
                    signals.append('HOLD')
            except (IndexError, KeyError):
                signals.append('HOLD')
    
    strategies['Covered Call'] = signals
    
    return strategies

def calculate_basic_traditional_strategies(data: pd.DataFrame) -> Dict[str, List[str]]:
    """Calculate basic traditional strategies"""
    strategies = {}
    close = data['Close']
    
    # RSI Strategy
    signals = []
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    for i in range(len(data)):
        try:
            if rsi.iloc[i] < 30:
                signals.append('BUY')
            elif rsi.iloc[i] > 70:
                signals.append('SELL')
            else:
                signals.append('HOLD')
        except (IndexError, KeyError):
            signals.append('HOLD')
    
    strategies['RSI'] = signals
    
    # Mean Reversion Strategy
    signals = []
    sma_20 = close.rolling(20).mean()
    
    for i in range(len(data)):
        if i < 20:
            signals.append('HOLD')
        else:
            try:
                deviation = (close.iloc[i] - sma_20.iloc[i]) / sma_20.iloc[i]
                if deviation < -0.05:
                    signals.append('BUY')
                elif deviation > 0.05:
                    signals.append('SELL')
                else:
                    signals.append('HOLD')
            except (IndexError, KeyError):
                signals.append('HOLD')
    
    strategies['Mean Reversion'] = signals
    
    return strategies

def backtest_basic_options_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Backtest basic options strategy"""
    if len(signals) != len(data):
        return {'error': 'Signal length mismatch'}
    
    capital = initial_capital
    position = 0
    trades = []
    
    for i, (date, row) in enumerate(data.iterrows()):
        signal = signals[i]
        price = row['Close']
        
        # Simplified options P&L calculation
        if signal == 'SELL_PUT' and position == 0:
            # Sell put, collect premium
            premium = price * 0.02  # 2% premium
            capital += premium * 100
            position = 1
            trades.append({'date': date, 'action': 'SELL_PUT', 'premium': premium})
        
        elif signal == 'SELL_CALL' and position == 0:
            # Sell call, collect premium (assume we own shares)
            premium = price * 0.015  # 1.5% premium
            capital += premium * 100
            position = 1
            trades.append({'date': date, 'action': 'SELL_CALL', 'premium': premium})
        
        # Close positions after 30 days
        if position > 0 and len(trades) > 0:
            days_held = (date - trades[-1]['date']).days
            if days_held >= 30:
                # Options expired worthless (simplified)
                pnl = trades[-1]['premium'] * 100
                capital += pnl
                position = 0
    
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len(trades)
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades
    }

def backtest_basic_traditional_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Backtest basic traditional strategy"""
    if len(signals) != len(data):
        return {'error': 'Signal length mismatch'}
    
    capital = initial_capital
    position = 0
    trades = []
    
    for i, (date, row) in enumerate(data.iterrows()):
        signal = signals[i]
        price = row['Close']
        
        if signal == 'BUY' and position == 0:
            shares = int(capital / price)
            if shares > 0:
                position = shares
                capital -= shares * price
                trades.append({'date': date, 'action': 'BUY', 'price': price, 'shares': shares})
        
        elif signal == 'SELL' and position > 0:
            capital += position * price
            trades.append({'date': date, 'action': 'SELL', 'price': price, 'shares': position})
            position = 0
    
    # Close any remaining position
    if position > 0:
        final_price = data['Close'].iloc[-1]
        capital += position * final_price
        trades.append({'date': data.index[-1], 'action': 'SELL', 'price': final_price, 'shares': position})
        position = 0
    
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len([t for t in trades if t['action'] == 'SELL'])
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades
    }

async def basic_options_test():
    """Compare basic options strategies with traditional strategies"""
    
    print("🚀 BASIC OPTIONS vs TRADITIONAL STRATEGIES TEST")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: $2,000")
    print(f"📊 Testing BASIC OPTIONS vs TRADITIONAL strategies")
    
    # Initialize database service
    print("\n🔧 Connecting to database...")
    db_service = MarketDataDatabaseService()
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    
    results = []
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        # Get data for this symbol (2 years)
        data = db_service.get_historical_data(symbol, '2022-09-19', '2024-09-19')
        
        if data is None or data.empty:
            print(f"   ❌ No data for {symbol}")
            continue
            
        print(f"   ✅ Loaded {len(data)} records")
        
        # Remove NaN values
        data = data.dropna()
        print(f"   📈 Valid data: {len(data)} records")
        
        # Test options strategies
        print(f"   🎯 Testing OPTIONS strategies...")
        options_strategies = calculate_basic_options_strategies(data)
        
        for strategy_name, signals in options_strategies.items():
            try:
                result = backtest_basic_options_strategy(data, signals, f"{strategy_name} ({symbol})", 2000.0)
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ {strategy_name}: {result['total_return']:.2f}%, Trades: {result['total_trades']}")
                else:
                    print(f"      ❌ {strategy_name}: Error")
                    
            except Exception as e:
                print(f"      ❌ {strategy_name}: {e}")
        
        # Test traditional strategies
        print(f"   📈 Testing TRADITIONAL strategies...")
        traditional_strategies = calculate_basic_traditional_strategies(data)
        
        for strategy_name, signals in traditional_strategies.items():
            try:
                result = backtest_basic_traditional_strategy(data, signals, f"{strategy_name} ({symbol})", 2000.0)
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ {strategy_name}: {result['total_return']:.2f}%, Trades: {result['total_trades']}")
                else:
                    print(f"      ❌ {strategy_name}: Error")
                    
            except Exception as e:
                print(f"      ❌ {strategy_name}: {e}")
    
    # Display results
    print("\n" + "=" * 90)
    print("📊 BASIC OPTIONS vs TRADITIONAL STRATEGIES RESULTS")
    print("=" * 90)
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"\n{'Rank':<4} {'Strategy':<25} {'Symbol':<8} {'Return %':<10} {'Capital':<12} {'Trades':<8} {'Type':<12}")
        print("-" * 90)
        
        for i, result in enumerate(results, 1):
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            # Determine strategy type
            strategy_type = "OPTIONS" if any(x in strategy_name for x in ['Put', 'Call']) else "TRADITIONAL"
            
            print(f"{i:<4} {strategy_name:<25} {symbol:<8} {result['total_return']:<10} ${result['final_capital']:<12} {result['total_trades']:<8} {strategy_type:<12}")
        
        # Separate options and traditional results
        options_results = [r for r in results if any(x in r['strategy'] for x in ['Put', 'Call'])]
        traditional_results = [r for r in results if not any(x in r['strategy'] for x in ['Put', 'Call'])]
        
        print(f"\n🎯 TOP 3 OPTIONS STRATEGIES:")
        print("-" * 50)
        for i, result in enumerate(options_results[:3], 1):
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            print(f"{i}. {strategy_name} on {symbol}: {result['total_return']:.2f}%")
        
        print(f"\n📈 TOP 3 TRADITIONAL STRATEGIES:")
        print("-" * 50)
        for i, result in enumerate(traditional_results[:3], 1):
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            print(f"{i}. {strategy_name} on {symbol}: {result['total_return']:.2f}%")
        
        # Calculate averages
        options_avg = sum(r['total_return'] for r in options_results) / len(options_results) if options_results else 0
        traditional_avg = sum(r['total_return'] for r in traditional_results) / len(traditional_results) if traditional_results else 0
        
        print(f"\n📊 AVERAGE PERFORMANCE:")
        print(f"   Options Strategies: {options_avg:.2f}%")
        print(f"   Traditional Strategies: {traditional_avg:.2f}%")
        
        if options_avg > traditional_avg:
            print(f"\n🏆 VERDICT: OPTIONS strategies outperform traditional strategies by {options_avg - traditional_avg:.2f}%!")
        else:
            print(f"\n📉 VERDICT: Traditional strategies outperform options strategies by {traditional_avg - options_avg:.2f}%")
    
    print(f"\n✅ Basic options vs traditional test complete!")

if __name__ == "__main__":
    asyncio.run(basic_options_test())


