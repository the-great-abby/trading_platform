#!/usr/bin/env python3
"""
Options vs Traditional Strategies Test - Compare options strategies with traditional strategies
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

def calculate_cash_secured_put_signals(data: pd.DataFrame) -> List[str]:
    """Calculate cash-secured put strategy signals (simplified)"""
    signals = []
    close = data['Close']
    
    # Calculate volatility for premium estimation
    returns = close.pct_change().dropna()
    volatility = returns.rolling(20).std()
    
    # Calculate moving averages for trend analysis
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    
    for i in range(50, len(data)):  # Need 50 days for calculation
        current_price = close.iloc[i]
        current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        
        # Cash-secured put strategy logic
        # Sell puts when: price is above SMA20, low volatility, and price is near support
        
        # Check if price is above 20-day SMA (uptrend)
        price_above_sma20 = current_price > sma_20.iloc[i]
        
        # Check if volatility is low (good for selling premium)
        low_volatility = current_vol < 0.025  # 2.5% daily volatility
        
        # Check if price is near support (20-day SMA)
        near_support = abs(current_price - sma_20.iloc[i]) / sma_20.iloc[i] < 0.03  # Within 3%
        
        # Cash-secured put signal: sell puts when conditions are favorable
        if price_above_sma20 and low_volatility and near_support:
            signals.append('SELL_PUT')  # Sell cash-secured put
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_covered_call_signals(data: pd.DataFrame) -> List[str]:
    """Calculate covered call strategy signals (simplified)"""
    signals = []
    close = data['Close']
    
    # Calculate volatility for premium estimation
    returns = close.pct_change().dropna()
    volatility = returns.rolling(20).std()
    
    # Calculate moving averages
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    
    for i in range(50, len(data)):
        current_price = close.iloc[i]
        current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        
        # Covered call strategy logic
        # Sell calls when: price is above SMA20, moderate volatility, and price is near resistance
        
        # Check if price is above 20-day SMA (uptrend)
        price_above_sma20 = current_price > sma_20.iloc[i]
        
        # Check if volatility is moderate (good for selling premium)
        moderate_volatility = 0.015 < current_vol < 0.035  # 1.5-3.5% daily volatility
        
        # Check if price is near resistance (50-day SMA)
        near_resistance = abs(current_price - sma_50.iloc[i]) / sma_50.iloc[i] < 0.05  # Within 5%
        
        # Covered call signal: sell calls when conditions are favorable
        if price_above_sma20 and moderate_volatility and near_resistance:
            signals.append('SELL_CALL')  # Sell covered call
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_iron_condor_signals(data: pd.DataFrame) -> List[str]:
    """Calculate iron condor strategy signals (simplified)"""
    signals = []
    close = data['Close']
    
    # Calculate volatility for premium estimation
    returns = close.pct_change().dropna()
    volatility = returns.rolling(20).std()
    
    # Calculate Bollinger Bands for range identification
    sma_20 = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = sma_20 + (bb_std * 2)
    bb_lower = sma_20 - (bb_std * 2)
    
    for i in range(50, len(data)):
        current_price = close.iloc[i]
        current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        
        # Iron condor strategy logic
        # Sell iron condor when: low volatility, price in middle of range, stable trend
        
        # Check if volatility is low (good for selling premium)
        low_volatility = current_vol < 0.02  # 2% daily volatility
        
        # Check if price is in middle of Bollinger Bands (range-bound)
        price_in_range = bb_lower.iloc[i] < current_price < bb_upper.iloc[i]
        price_middle = abs(current_price - sma_20.iloc[i]) / sma_20.iloc[i] < 0.02  # Within 2% of SMA
        
        # Iron condor signal: sell when range-bound and low volatility
        if low_volatility and price_in_range and price_middle:
            signals.append('SELL_IRON_CONDOR')  # Sell iron condor
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_straddle_signals(data: pd.DataFrame) -> List[str]:
    """Calculate long straddle strategy signals (simplified)"""
    signals = []
    close = data['Close']
    
    # Calculate volatility for premium estimation
    returns = close.pct_change().dropna()
    volatility = returns.rolling(20).std()
    
    # Calculate RSI for overbought/oversold conditions
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    for i in range(50, len(data)):
        current_price = close.iloc[i]
        current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        current_rsi = rsi.iloc[i] if not pd.isna(rsi.iloc[i]) else 50
        
        # Long straddle strategy logic
        # Buy straddle when: low volatility, price consolidation, expecting breakout
        
        # Check if volatility is low (good for buying cheap options)
        low_volatility = current_vol < 0.02  # 2% daily volatility
        
        # Check if price is consolidating (RSI near 50)
        price_consolidating = 40 < current_rsi < 60
        
        # Check if recent price action is tight (low range)
        recent_range = (close.iloc[i-10:i+1].max() - close.iloc[i-10:i+1].min()) / close.iloc[i-10:i+1].mean()
        tight_range = recent_range < 0.05  # 5% range over 10 days
        
        # Long straddle signal: buy when expecting volatility expansion
        if low_volatility and price_consolidating and tight_range:
            signals.append('BUY_STRADDLE')  # Buy long straddle
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_traditional_strategies(data: pd.DataFrame) -> Dict[str, List[str]]:
    """Calculate traditional strategies for comparison"""
    strategies = {}
    
    # RSI Strategy
    signals = []
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    for i in range(len(data)):
        if rsi.iloc[i] < 30:
            signals.append('BUY')
        elif rsi.iloc[i] > 70:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    strategies['RSI'] = signals
    
    # Mean Reversion Strategy
    signals = []
    sma_20 = data['Close'].rolling(20).mean()
    
    for i in range(20, len(data)):
        deviation = (data['Close'].iloc[i] - sma_20.iloc[i]) / sma_20.iloc[i]
        if deviation < -0.05:  # 5% below SMA
            signals.append('BUY')
        elif deviation > 0.05:  # 5% above SMA
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    strategies['Mean Reversion'] = ['HOLD'] * 20 + signals
    
    # Bollinger Bands Strategy
    signals = []
    sma_20 = data['Close'].rolling(20).mean()
    bb_std = data['Close'].rolling(20).std()
    bb_upper = sma_20 + (bb_std * 2)
    bb_lower = sma_20 - (bb_std * 2)
    
    for i in range(20, len(data)):
        if data['Close'].iloc[i] <= bb_lower.iloc[i]:
            signals.append('BUY')
        elif data['Close'].iloc[i] >= bb_upper.iloc[i]:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    strategies['Bollinger Bands'] = ['HOLD'] * 20 + signals
    
    return strategies

def backtest_options_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Backtest options strategy with simplified P&L calculation"""
    if len(signals) != len(data):
        return {'error': 'Signal length mismatch'}
    
    capital = initial_capital
    position = 0
    trades = []
    
    for i, (date, row) in enumerate(data.iterrows()):
        signal = signals[i]
        price = row['Close']
        
        # Simplified options P&L calculation
        if signal == 'SELL_PUT':  # Cash-secured put
            if position == 0:  # No current position
                # Sell put at 2% out-of-the-money, collect premium
                strike_price = price * 0.98  # 2% OTM
                premium = price * 0.02  # 2% premium (simplified)
                
                # Set aside cash for potential assignment
                required_cash = strike_price * 100  # 100 shares per contract
                if required_cash <= capital * 0.8:  # Use 80% of capital
                    position = 1  # 1 put contract
                    capital += premium * 100  # Collect premium
                    trades.append({
                        'date': date, 
                        'action': 'SELL_PUT', 
                        'strike': strike_price, 
                        'premium': premium,
                        'contracts': 1
                    })
        
        elif signal == 'SELL_CALL':  # Covered call
            if position == 0:  # No current position
                # Sell call at 5% out-of-the-money, collect premium
                strike_price = price * 1.05  # 5% OTM
                premium = price * 0.015  # 1.5% premium (simplified)
                
                # Need to own 100 shares (simplified - assume we can buy them)
                shares_cost = price * 100
                if shares_cost <= capital * 0.8:  # Use 80% of capital
                    position = 1  # 1 call contract
                    capital -= shares_cost  # Buy shares
                    capital += premium * 100  # Collect premium
                    trades.append({
                        'date': date, 
                        'action': 'SELL_CALL', 
                        'strike': strike_price, 
                        'premium': premium,
                        'contracts': 1,
                        'shares_cost': shares_cost
                    })
        
        elif signal == 'SELL_IRON_CONDOR':  # Iron condor
            if position == 0:  # No current position
                # Sell iron condor, collect net premium
                net_premium = price * 0.01  # 1% net premium (simplified)
                
                # Iron condor has defined risk
                max_risk = price * 0.05  # 5% max risk
                if max_risk <= capital * 0.1:  # Use 10% of capital for margin
                    position = 1  # 1 iron condor
                    capital += net_premium * 100  # Collect net premium
                    trades.append({
                        'date': date, 
                        'action': 'SELL_IRON_CONDOR', 
                        'net_premium': net_premium,
                        'max_risk': max_risk,
                        'contracts': 1
                    })
        
        elif signal == 'BUY_STRADDLE':  # Long straddle
            if position == 0:  # No current position
                # Buy straddle, pay premium
                premium = price * 0.03  # 3% premium (simplified)
                
                if premium * 100 <= capital * 0.1:  # Use 10% of capital
                    position = 1  # 1 straddle
                    capital -= premium * 100  # Pay premium
                    trades.append({
                        'date': date, 
                        'action': 'BUY_STRADDLE', 
                        'premium': premium,
                        'contracts': 1
                    })
        
        # Close positions after 30 days (simplified)
        if position > 0 and len(trades) > 0:
            days_held = (date - trades[-1]['date']).days
            if days_held >= 30:  # Close after 30 days
                if trades[-1]['action'] in ['SELL_PUT', 'SELL_CALL', 'SELL_IRON_CONDOR']:
                    # Options expired worthless or closed for profit
                    pnl = trades[-1].get('premium', trades[-1].get('net_premium', 0)) * 100
                    capital += pnl
                elif trades[-1]['action'] == 'BUY_STRADDLE':
                    # Straddle expired worthless
                    pnl = -trades[-1]['premium'] * 100
                    capital += pnl
                
                position = 0
    
    # Calculate metrics
    total_return = (capital - initial_capital) / initial_capital * 100
    total_trades = len(trades)
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades,
        'trades': trades
    }

def backtest_traditional_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Backtest traditional strategy"""
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
        'total_trades': total_trades,
        'trades': trades
    }

async def options_vs_traditional_test():
    """Compare options strategies with traditional strategies"""
    
    print("🚀 OPTIONS vs TRADITIONAL STRATEGIES TEST")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: $2,000")
    print(f"📊 Testing OPTIONS vs TRADITIONAL strategies")
    
    # Initialize database service
    print("\n🔧 Connecting to database...")
    db_service = MarketDataDatabaseService()
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    
    # Options strategies
    options_strategies = {
        'Cash Secured Put': calculate_cash_secured_put_signals,
        'Covered Call': calculate_covered_call_signals,
        'Iron Condor': calculate_iron_condor_signals,
        'Long Straddle': calculate_straddle_signals
    }
    
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
        for strategy_name, signal_func in options_strategies.items():
            try:
                signals = signal_func(data)
                result = backtest_options_strategy(data, signals, f"{strategy_name} ({symbol})", 2000.0)
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ {strategy_name}: {result['total_return']:.2f}%, Trades: {result['total_trades']}")
                else:
                    print(f"      ❌ {strategy_name}: Error")
                    
            except Exception as e:
                print(f"      ❌ {strategy_name}: {e}")
        
        # Test traditional strategies
        print(f"   📈 Testing TRADITIONAL strategies...")
        traditional_strategies = calculate_traditional_strategies(data)
        
        for strategy_name, signals in traditional_strategies.items():
            try:
                result = backtest_traditional_strategy(data, signals, f"{strategy_name} ({symbol})", 2000.0)
                
                if 'error' not in result:
                    results.append(result)
                    print(f"      ✅ {strategy_name}: {result['total_return']:.2f}%, Trades: {result['total_trades']}")
                else:
                    print(f"      ❌ {strategy_name}: Error")
                    
            except Exception as e:
                print(f"      ❌ {strategy_name}: {e}")
    
    # Display results
    print("\n" + "=" * 90)
    print("📊 OPTIONS vs TRADITIONAL STRATEGIES RESULTS")
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
            strategy_type = "OPTIONS" if any(x in strategy_name for x in ['Put', 'Call', 'Iron', 'Straddle']) else "TRADITIONAL"
            
            print(f"{i:<4} {strategy_name:<25} {symbol:<8} {result['total_return']:<10} ${result['final_capital']:<12} {result['total_trades']:<8} {strategy_type:<12}")
        
        # Separate options and traditional results
        options_results = [r for r in results if any(x in r['strategy'] for x in ['Put', 'Call', 'Iron', 'Straddle'])]
        traditional_results = [r for r in results if not any(x in r['strategy'] for x in ['Put', 'Call', 'Iron', 'Straddle'])]
        
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
    
    print(f"\n✅ Options vs Traditional test complete!")

if __name__ == "__main__":
    asyncio.run(options_vs_traditional_test())


