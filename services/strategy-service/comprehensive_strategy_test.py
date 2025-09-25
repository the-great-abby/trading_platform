#!/usr/bin/env python3
"""
Comprehensive Strategy Test - All strategies with $2,000 account
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

def calculate_macd_signals(data: pd.DataFrame) -> List[str]:
    """Calculate MACD signals"""
    signals = []
    
    if 'MACD' not in data.columns or 'MACD_Signal' not in data.columns:
        return ['HOLD'] * len(data)
    
    macd = data['MACD']
    macd_signal = data['MACD_Signal']
    
    for i in range(1, len(data)):
        # Bullish crossover: MACD crosses above signal
        if (macd.iloc[i] > macd_signal.iloc[i] and 
            macd.iloc[i-1] <= macd_signal.iloc[i-1]):
            signals.append('BUY')
        # Bearish crossover: MACD crosses below signal
        elif (macd.iloc[i] < macd_signal.iloc[i] and 
              macd.iloc[i-1] >= macd_signal.iloc[i-1]):
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_bollinger_bands_signals(data: pd.DataFrame) -> List[str]:
    """Calculate Bollinger Bands mean reversion signals"""
    signals = []
    
    if 'BB_Upper' not in data.columns or 'BB_Lower' not in data.columns:
        return ['HOLD'] * len(data)
    
    close = data['Close']
    bb_upper = data['BB_Upper']
    bb_lower = data['BB_Lower']
    
    for i in range(len(data)):
        if close.iloc[i] <= bb_lower.iloc[i]:  # Price touches lower band
            signals.append('BUY')
        elif close.iloc[i] >= bb_upper.iloc[i]:  # Price touches upper band
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_mean_reversion_signals(data: pd.DataFrame) -> List[str]:
    """Calculate mean reversion signals based on price vs SMA"""
    signals = []
    close = data['Close']
    sma_20 = data['SMA_20']
    
    for i in range(len(data)):
        deviation = (close.iloc[i] - sma_20.iloc[i]) / sma_20.iloc[i]
        
        if deviation < -0.05:  # 5% below SMA
            signals.append('BUY')
        elif deviation > 0.05:  # 5% above SMA
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_volatility_breakout_signals(data: pd.DataFrame) -> List[str]:
    """Calculate volatility breakout signals"""
    signals = []
    close = data['Close']
    
    for i in range(20, len(data)):  # Need 20 days for volatility calculation
        # Calculate 20-day volatility
        returns = close.iloc[i-19:i+1].pct_change().dropna()
        volatility = returns.std()
        
        # Current return
        current_return = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
        
        # Breakout if current return > 2 * volatility
        if current_return > 2 * volatility:
            signals.append('BUY')
        elif current_return < -2 * volatility:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    # Fill first 20 with HOLD
    return ['HOLD'] * 20 + signals

def calculate_ichimoku_signals(data: pd.DataFrame) -> List[str]:
    """Calculate Ichimoku signals (simplified)"""
    signals = []
    
    if 'SMA_20' not in data.columns or 'SMA_50' not in data.columns:
        return ['HOLD'] * len(data)
    
    close = data['Close']
    sma_20 = data['SMA_20']
    sma_50 = data['SMA_50']
    
    for i in range(len(data)):
        # Simplified Ichimoku: price above both SMAs = bullish
        if close.iloc[i] > sma_20.iloc[i] and close.iloc[i] > sma_50.iloc[i]:
            signals.append('BUY')
        # Price below both SMAs = bearish
        elif close.iloc[i] < sma_20.iloc[i] and close.iloc[i] < sma_50.iloc[i]:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals

def calculate_regime_switching_signals(data: pd.DataFrame) -> List[str]:
    """Calculate regime switching signals (simplified)"""
    signals = []
    close = data['Close']
    
    for i in range(50, len(data)):  # Need 50 days for regime detection
        # Calculate 50-day trend
        long_trend = (close.iloc[i] - close.iloc[i-49]) / close.iloc[i-49]
        # Calculate 20-day trend
        short_trend = (close.iloc[i] - close.iloc[i-19]) / close.iloc[i-19]
        
        # Bullish regime: both trends positive
        if long_trend > 0.02 and short_trend > 0.01:
            signals.append('BUY')
        # Bearish regime: both trends negative
        elif long_trend < -0.02 and short_trend < -0.01:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def backtest_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Simple backtest for a strategy with $2,000 initial capital"""
    if len(signals) != len(data):
        return {'error': 'Signal length mismatch'}
    
    capital = initial_capital
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
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len([t for t in trades if t['action'] == 'SELL'])
    
    # Calculate win rate
    winning_trades = 0
    for i in range(1, len(trades), 2):
        if i < len(trades):
            buy_trade = trades[i-1]
            sell_trade = trades[i]
            if sell_trade['price'] > buy_trade['price']:
                winning_trades += 1
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate max drawdown
    portfolio_values = []
    temp_capital = initial_capital
    temp_position = 0
    
    for i, (date, row) in enumerate(data.iterrows()):
        if i < len(signals):
            signal = signals[i]
            price = row['Close']
            
            if signal == 'BUY' and temp_position == 0:
                shares = int(temp_capital / price)
                if shares > 0:
                    temp_position = shares
                    temp_capital -= shares * price
            
            elif signal == 'SELL' and temp_position > 0:
                temp_capital += temp_position * price
                temp_position = 0
        
        portfolio_value = temp_capital + (temp_position * price)
        portfolio_values.append(portfolio_value)
    
    if portfolio_values:
        peak = portfolio_values[0]
        max_drawdown = 0
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    else:
        max_drawdown = 0
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'max_drawdown': round(max_drawdown, 2),
        'trades': trades
    }

async def comprehensive_strategy_test():
    """Comprehensive strategy test with $2,000 account"""
    
    print("🚀 COMPREHENSIVE STRATEGY TEST")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: $2,000")
    print(f"📈 Testing ALL available strategies")
    
    # Initialize database service
    print("\n🔧 Connecting to database...")
    db_service = MarketDataDatabaseService()
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    
    # ALL available strategies
    strategies = {
        'SMA Crossover': calculate_sma_crossover_signals,
        'RSI': calculate_rsi_signals,
        'Momentum': calculate_momentum_signals,
        'MACD': calculate_macd_signals,
        'Bollinger Bands': calculate_bollinger_bands_signals,
        'Mean Reversion': calculate_mean_reversion_signals,
        'Volatility Breakout': calculate_volatility_breakout_signals,
        'Ichimoku': calculate_ichimoku_signals,
        'Regime Switching': calculate_regime_switching_signals
    }
    
    results = []
    total_tests = len(symbols) * len(strategies)
    current_test = 0
    
    print(f"\n📊 Testing {len(strategies)} strategies on {len(symbols)} symbols")
    print(f"🎯 Total tests: {total_tests}")
    
    start_time = time.time()
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        # Get data for this symbol
        data = db_service.get_historical_data(symbol, '2022-09-19', '2024-09-19')  # 2 years
        
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
        
        if 'MACD' not in data.columns:
            exp1 = data['Close'].ewm(span=12).mean()
            exp2 = data['Close'].ewm(span=26).mean()
            data['MACD'] = exp1 - exp2
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        
        if 'BB_Upper' not in data.columns:
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
        
        # Remove NaN values
        data = data.dropna()
        print(f"   📈 Valid data: {len(data)} records")
        
        # Test each strategy
        for strategy_name, signal_func in strategies.items():
            current_test += 1
            progress = (current_test / total_tests) * 100
            print(f"   🔍 [{progress:.0f}%] Testing {strategy_name}...")
            
            try:
                signals = signal_func(data)
                result = backtest_strategy(data, signals, f"{strategy_name} ({symbol})", 2000.0)
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ Return: {result['total_return']:.2f}%, Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%")
                else:
                    print(f"      ❌ Error: {result['error']}")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    elapsed_time = time.time() - start_time
    
    # Display results
    print("\n" + "=" * 90)
    print("📈 COMPREHENSIVE STRATEGY RESULTS (2 Years, $2,000 Account)")
    print("=" * 90)
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"🎯 Tests completed: {len(results)}/{total_tests}")
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"\n{'Rank':<4} {'Strategy':<20} {'Symbol':<8} {'Return %':<10} {'Capital':<12} {'Trades':<8} {'Win Rate':<10} {'Max DD':<8}")
        print("-" * 90)
        
        for i, result in enumerate(results, 1):
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            print(f"{i:<4} {strategy_name:<20} {symbol:<8} {result['total_return']:<10} ${result['final_capital']:<12} {result['total_trades']:<8} {result['win_rate']:<10} {result['max_drawdown']:<8}")
        
        # TOP 3 RESULTS
        print(f"\n🏆 TOP 3 BEST PERFORMING STRATEGIES:")
        print("=" * 60)
        
        for i in range(min(3, len(results))):
            result = results[i]
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            print(f"{medal} #{i+1}: {strategy_name} on {symbol}")
            print(f"   💰 Return: {result['total_return']:.2f}% (${result['final_capital']:.2f} from $2,000)")
            print(f"   📊 Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%")
            print(f"   📉 Max Drawdown: {result['max_drawdown']:.2f}%")
            print()
        
        # Strategy performance summary
        strategy_performance = {}
        for result in results:
            strategy_name = result['strategy'].split(' (')[0]
            if strategy_name not in strategy_performance:
                strategy_performance[strategy_name] = []
            strategy_performance[strategy_name].append(result['total_return'])
        
        print(f"📊 AVERAGE PERFORMANCE BY STRATEGY:")
        print("-" * 50)
        strategy_averages = []
        for strategy_name, returns in strategy_performance.items():
            avg_return = sum(returns) / len(returns)
            strategy_averages.append((strategy_name, avg_return))
        
        strategy_averages.sort(key=lambda x: x[1], reverse=True)
        
        for strategy_name, avg_return in strategy_averages:
            print(f"   {strategy_name:<20}: {avg_return:>8.2f}% average")
    
    print(f"\n✅ Comprehensive test complete!")

if __name__ == "__main__":
    asyncio.run(comprehensive_strategy_test())


