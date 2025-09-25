#!/usr/bin/env python3
"""
Fast Strategy Comparison - Direct database approach
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

def calculate_sma_crossover_signals(data: pd.DataFrame) -> List[str]:
    """Calculate SMA crossover signals"""
    signals = []
    sma_20 = data['SMA_20']
    sma_50 = data['SMA_50']
    
    for i in range(1, len(data)):
        # Bullish crossover: SMA_20 crosses above SMA_50
        if (sma_20.iloc[i] > sma_50.iloc[i] and 
            sma_20.iloc[i-1] <= sma_50.iloc[i-1]):
            signals.append('BUY')
        # Bearish crossover: SMA_20 crosses below SMA_50
        elif (sma_20.iloc[i] < sma_50.iloc[i] and 
              sma_20.iloc[i-1] >= sma_50.iloc[i-1]):
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_rsi_signals(data: pd.DataFrame) -> List[str]:
    """Calculate RSI signals"""
    signals = []
    rsi = data['RSI']
    
    for i in range(len(data)):
        if rsi.iloc[i] < 30:  # Oversold
            signals.append('BUY')
        elif rsi.iloc[i] > 70:  # Overbought
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_momentum_signals(data: pd.DataFrame) -> List[str]:
    """Calculate momentum signals"""
    signals = []
    close = data['Close']
    
    for i in range(10, len(data)):  # Need 10 days for momentum
        momentum_10 = (close.iloc[i] - close.iloc[i-10]) / close.iloc[i-10]
        
        if momentum_10 > 0.02:  # 2% momentum
            signals.append('BUY')
        elif momentum_10 < -0.02:  # -2% momentum
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    # Fill first 10 with HOLD
    return ['HOLD'] * 10 + signals

def backtest_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str) -> Dict:
    """Simple backtest for a strategy"""
    if len(signals) != len(data):
        return {'error': 'Signal length mismatch'}
    
    capital = 1000.0
    position = 0
    trades = []
    
    for i, (date, row) in enumerate(data.iterrows()):
        signal = signals[i]
        price = row['Close']
        
        if signal == 'BUY' and position == 0:
            # Buy
            shares = int(capital / price)
            if shares > 0:
                position = shares
                capital -= shares * price
                trades.append({'date': date, 'action': 'BUY', 'price': price, 'shares': shares})
        
        elif signal == 'SELL' and position > 0:
            # Sell
            capital += position * price
            trades.append({'date': date, 'action': 'SELL', 'price': price, 'shares': position})
            position = 0
    
    # Close any remaining position
    if position > 0:
        final_price = data['Close'].iloc[-1]
        capital += position * final_price
        trades.append({'date': data.index[-1], 'action': 'SELL', 'price': final_price, 'shares': position})
        position = 0
    
    # Calculate metrics
    total_return = (capital - 1000) / 1000 * 100
    total_trades = len([t for t in trades if t['action'] == 'SELL'])
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades,
        'trades': trades
    }

async def fast_strategy_comparison():
    """Fast strategy comparison using direct database access"""
    
    print("🚀 FAST STRATEGY COMPARISON")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize database service
    print("\n🔧 Connecting to database...")
    db_service = MarketDataDatabaseService()
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    strategies = {
        'SMA Crossover': calculate_sma_crossover_signals,
        'RSI': calculate_rsi_signals,
        'Momentum': calculate_momentum_signals
    }
    
    results = []
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        # Get data for this symbol
        data = db_service.get_historical_data(symbol, '2023-11-28', '2024-09-19')
        
        if data is None or data.empty:
            print(f"   ❌ No data for {symbol}")
            continue
            
        print(f"   ✅ Loaded {len(data)} records")
        
        # Add technical indicators if not present
        if 'SMA_20' not in data.columns:
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        if 'RSI' not in data.columns:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
        
        # Remove NaN values
        data = data.dropna()
        print(f"   📈 Valid data: {len(data)} records")
        
        # Test each strategy
        for strategy_name, signal_func in strategies.items():
            print(f"   🔍 Testing {strategy_name}...")
            
            try:
                signals = signal_func(data)
                result = backtest_strategy(data, signals, f"{strategy_name} ({symbol})")
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ Return: {result['total_return']:.2f}%, Trades: {result['total_trades']}")
                else:
                    print(f"      ❌ Error: {result['error']}")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    # Display results
    print("\n" + "=" * 80)
    print("📈 STRATEGY COMPARISON RESULTS")
    print("=" * 80)
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"{'Strategy':<25} {'Symbol':<8} {'Return %':<10} {'Capital':<10} {'Trades':<8}")
        print("-" * 70)
        
        for result in results:
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            print(f"{strategy_name:<25} {symbol:<8} {result['total_return']:<10} ${result['final_capital']:<10} {result['total_trades']:<8}")
        
        # Find best performers
        print(f"\n🏆 TOP PERFORMERS:")
        print(f"🥇 Best Overall: {results[0]['strategy']} ({results[0]['total_return']:.2f}%)")
        
        # Group by strategy type
        strategy_performance = {}
        for result in results:
            strategy_name = result['strategy'].split(' (')[0]
            if strategy_name not in strategy_performance:
                strategy_performance[strategy_name] = []
            strategy_performance[strategy_name].append(result['total_return'])
        
        print(f"\n📊 Average Performance by Strategy:")
        for strategy_name, returns in strategy_performance.items():
            avg_return = sum(returns) / len(returns)
            print(f"   {strategy_name}: {avg_return:.2f}% (tested on {len(returns)} symbols)")
    
    print(f"\n✅ Fast comparison complete!")

if __name__ == "__main__":
    asyncio.run(fast_strategy_comparison())


