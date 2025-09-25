#!/usr/bin/env python3
"""
Adaptive Strategies Test - Test self-adjusting strategies that adapt to market conditions
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

def calculate_adaptive_momentum_signals(data: pd.DataFrame) -> List[str]:
    """Calculate adaptive momentum signals that adjust to market conditions"""
    signals = []
    close = data['Close']
    
    # Calculate volatility and trend strength
    returns = close.pct_change().dropna()
    volatility = returns.rolling(20).std()
    
    # Trend strength calculation
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    
    for i in range(50, len(data)):  # Need 50 days for full calculation
        current_vol = volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        trend_strength = abs(sma_20.iloc[i] - sma_50.iloc[i]) / sma_50.iloc[i] if not pd.isna(sma_50.iloc[i]) else 0
        
        # Adaptive momentum calculation
        # High volatility: shorter lookback, higher threshold
        if current_vol > 0.03:  # High volatility
            lookback = 10
            threshold = 0.03
        elif current_vol < 0.015:  # Low volatility
            lookback = 30
            threshold = 0.015
        else:  # Normal volatility
            lookback = 20
            threshold = 0.02
        
        # Calculate momentum with adaptive parameters
        momentum = (close.iloc[i] - close.iloc[i-lookback]) / close.iloc[i-lookback]
        
        # Trend-aware signals
        if trend_strength > 0.05:  # Strong trend
            # In trending markets, use momentum
            if momentum > threshold:
                signals.append('BUY')
            elif momentum < -threshold:
                signals.append('SELL')
            else:
                signals.append('HOLD')
        else:  # Sideways market
            # In sideways markets, use mean reversion
            sma_current = sma_20.iloc[i]
            deviation = (close.iloc[i] - sma_current) / sma_current
            if deviation < -0.03:  # 3% below SMA
                signals.append('BUY')
            elif deviation > 0.03:  # 3% above SMA
                signals.append('SELL')
            else:
                signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_regime_switching_signals(data: pd.DataFrame) -> List[str]:
    """Calculate regime switching signals (enhanced version)"""
    signals = []
    close = data['Close']
    
    for i in range(100, len(data)):  # Need 100 days for regime detection
        # Calculate multiple indicators for regime detection
        sma_20 = close.iloc[i-19:i+1].mean()
        sma_50 = close.iloc[i-49:i+1].mean()
        sma_100 = close.iloc[i-99:i+1].mean()
        
        # Volatility regime
        returns = close.iloc[i-19:i+1].pct_change().dropna()
        volatility = returns.std()
        
        # Trend regime
        long_trend = (close.iloc[i] - close.iloc[i-99]) / close.iloc[i-99]
        medium_trend = (close.iloc[i] - close.iloc[i-49]) / close.iloc[i-49]
        short_trend = (close.iloc[i] - close.iloc[i-19]) / close.iloc[i-19]
        
        # Determine regime
        if volatility > 0.025:  # High volatility regime
            # Use shorter timeframes and smaller thresholds
            if short_trend > 0.02:
                signals.append('BUY')
            elif short_trend < -0.02:
                signals.append('SELL')
            else:
                signals.append('HOLD')
                
        elif long_trend > 0.05 and medium_trend > 0.02:  # Bull market regime
            # Use trend following
            if short_trend > 0.01:
                signals.append('BUY')
            elif short_trend < -0.01:
                signals.append('SELL')
            else:
                signals.append('HOLD')
                
        elif long_trend < -0.05 and medium_trend < -0.02:  # Bear market regime
            # Use mean reversion or short selling
            deviation = (close.iloc[i] - sma_20) / sma_20
            if deviation > 0.03:  # Bounce opportunity
                signals.append('SELL')
            elif deviation < -0.03:  # Oversold bounce
                signals.append('BUY')
            else:
                signals.append('HOLD')
                
        else:  # Sideways regime
            # Use range trading
            if close.iloc[i] < sma_20 * 0.98:  # 2% below SMA
                signals.append('BUY')
            elif close.iloc[i] > sma_20 * 1.02:  # 2% above SMA
                signals.append('SELL')
            else:
                signals.append('HOLD')
    
    # Fill first 100 with HOLD
    return ['HOLD'] * 100 + signals

def calculate_enhanced_day_trading_signals(data: pd.DataFrame) -> List[str]:
    """Calculate enhanced day trading signals with multiple confirmations"""
    signals = []
    close = data['Close']
    
    # Calculate indicators
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    
    # RSI calculation
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD calculation
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=9).mean()
    
    # Volume analysis (if available)
    volume = data['Volume'] if 'Volume' in data.columns else pd.Series([1000000] * len(data), index=data.index)
    avg_volume = volume.rolling(20).mean()
    
    for i in range(50, len(data)):  # Need 50 days for full calculation
        # Multiple confirmation signals
        price_above_sma20 = close.iloc[i] > sma_20.iloc[i]
        price_above_sma50 = close.iloc[i] > sma_50.iloc[i]
        rsi_oversold = rsi.iloc[i] < 30
        rsi_overbought = rsi.iloc[i] > 70
        macd_bullish = macd.iloc[i] > macd_signal.iloc[i]
        macd_bearish = macd.iloc[i] < macd_signal.iloc[i]
        volume_spike = volume.iloc[i] > avg_volume.iloc[i] * 1.5
        
        # Enhanced buy signal: Multiple confirmations
        if (price_above_sma20 and 
            macd_bullish and 
            (rsi_oversold or (rsi.iloc[i] > 50 and rsi.iloc[i] < 70)) and
            volume_spike):
            signals.append('BUY')
            
        # Enhanced sell signal: Multiple confirmations
        elif (macd_bearish and 
              (rsi_overbought or (rsi.iloc[i] < 50 and rsi.iloc[i] > 30))):
            signals.append('SELL')
            
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_neural_network_signals(data: pd.DataFrame) -> List[str]:
    """Calculate neural network inspired signals (simplified)"""
    signals = []
    close = data['Close']
    
    # Calculate multiple features
    sma_5 = close.rolling(5).mean()
    sma_10 = close.rolling(10).mean()
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    
    # Price momentum
    momentum_5 = close.pct_change(5)
    momentum_10 = close.pct_change(10)
    momentum_20 = close.pct_change(20)
    
    # Volatility
    volatility = close.pct_change().rolling(20).std()
    
    for i in range(50, len(data)):  # Need 50 days for calculation
        # Feature engineering (simplified neural network approach)
        features = {
            'price_vs_sma5': (close.iloc[i] - sma_5.iloc[i]) / sma_5.iloc[i],
            'price_vs_sma10': (close.iloc[i] - sma_10.iloc[i]) / sma_10.iloc[i],
            'price_vs_sma20': (close.iloc[i] - sma_20.iloc[i]) / sma_20.iloc[i],
            'price_vs_sma50': (close.iloc[i] - sma_50.iloc[i]) / sma_50.iloc[i],
            'momentum_5': momentum_5.iloc[i],
            'momentum_10': momentum_10.iloc[i],
            'momentum_20': momentum_20.iloc[i],
            'volatility': volatility.iloc[i] if not pd.isna(volatility.iloc[i]) else 0.02
        }
        
        # Simple neural network-like decision (weighted combination)
        buy_score = 0
        sell_score = 0
        
        # Price position weights
        if features['price_vs_sma5'] > 0:
            buy_score += 0.3
        else:
            sell_score += 0.3
            
        if features['price_vs_sma20'] > 0:
            buy_score += 0.4
        else:
            sell_score += 0.4
            
        # Momentum weights
        if features['momentum_5'] > 0.01:
            buy_score += 0.2
        elif features['momentum_5'] < -0.01:
            sell_score += 0.2
            
        if features['momentum_20'] > 0.02:
            buy_score += 0.3
        elif features['momentum_20'] < -0.02:
            sell_score += 0.3
            
        # Volatility adjustment
        if features['volatility'] > 0.03:  # High volatility - reduce confidence
            buy_score *= 0.7
            sell_score *= 0.7
        
        # Decision threshold
        if buy_score > 0.6:
            signals.append('BUY')
        elif sell_score > 0.6:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    # Fill first 50 with HOLD
    return ['HOLD'] * 50 + signals

def calculate_quantum_momentum_signals(data: pd.DataFrame) -> List[str]:
    """Calculate quantum momentum signals (advanced adaptive)"""
    signals = []
    close = data['Close']
    
    for i in range(100, len(data)):  # Need 100 days for quantum analysis
        # Quantum-inspired superposition of multiple timeframes
        timeframes = [5, 10, 20, 50]
        momentum_scores = []
        
        for tf in timeframes:
            if i >= tf:
                momentum = (close.iloc[i] - close.iloc[i-tf]) / close.iloc[i-tf]
                momentum_scores.append(momentum)
        
        # Quantum state calculation (weighted superposition)
        weights = [0.4, 0.3, 0.2, 0.1]  # Shorter timeframes get higher weight
        quantum_state = sum(w * m for w, m in zip(weights, momentum_scores))
        
        # Entanglement with volatility
        returns = close.iloc[i-19:i+1].pct_change().dropna()
        volatility = returns.std()
        
        # Quantum interference (volatility affects signal strength)
        if volatility > 0.025:  # High volatility - quantum decoherence
            threshold = 0.03
        else:  # Low volatility - quantum coherence
            threshold = 0.015
        
        # Quantum measurement (signal generation)
        if quantum_state > threshold:
            signals.append('BUY')
        elif quantum_state < -threshold:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    # Fill first 100 with HOLD
    return ['HOLD'] * 100 + signals

def backtest_strategy(data: pd.DataFrame, signals: List[str], strategy_name: str, initial_capital: float = 2000.0) -> Dict:
    """Enhanced backtest for adaptive strategies"""
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
    
    return {
        'strategy': strategy_name,
        'total_return': round(total_return, 2),
        'final_capital': round(capital, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'trades': trades
    }

async def adaptive_strategies_test():
    """Test adaptive strategies that self-adjust to market conditions"""
    
    print("🚀 ADAPTIVE STRATEGIES TEST")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Initial Capital: $2,000")
    print(f"🧠 Testing SELF-ADJUSTING strategies")
    
    # Initialize database service
    print("\n🔧 Connecting to database...")
    db_service = MarketDataDatabaseService()
    
    # Test symbols
    symbols = ['AMD', 'INTC', 'PYPL']
    
    # Adaptive strategies that adjust to market conditions
    adaptive_strategies = {
        'Adaptive Momentum': calculate_adaptive_momentum_signals,
        'Enhanced Regime Switching': calculate_regime_switching_signals,
        'Enhanced Day Trading': calculate_enhanced_day_trading_signals,
        'Neural Network': calculate_neural_network_signals,
        'Quantum Momentum': calculate_quantum_momentum_signals
    }
    
    results = []
    total_tests = len(symbols) * len(adaptive_strategies)
    current_test = 0
    
    print(f"\n📊 Testing {len(adaptive_strategies)} adaptive strategies on {len(symbols)} symbols")
    print(f"🎯 Total tests: {total_tests}")
    
    start_time = time.time()
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        # Get data for this symbol (2 years)
        data = db_service.get_historical_data(symbol, '2022-09-19', '2024-09-19')
        
        if data is None or data.empty:
            print(f"   ❌ No data for {symbol}")
            continue
            
        print(f"   ✅ Loaded {len(data)} records")
        
        # Add technical indicators if not present
        if 'SMA_20' not in data.columns:
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # Remove NaN values
        data = data.dropna()
        print(f"   📈 Valid data: {len(data)} records")
        
        # Test each adaptive strategy
        for strategy_name, signal_func in adaptive_strategies.items():
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
    print("🧠 ADAPTIVE STRATEGIES RESULTS (Self-Adjusting to Market Conditions)")
    print("=" * 90)
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"🎯 Tests completed: {len(results)}/{total_tests}")
    
    if results:
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print(f"\n{'Rank':<4} {'Strategy':<25} {'Symbol':<8} {'Return %':<10} {'Capital':<12} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 90)
        
        for i, result in enumerate(results, 1):
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            print(f"{i:<4} {strategy_name:<25} {symbol:<8} {result['total_return']:<10} ${result['final_capital']:<12} {result['total_trades']:<8} {result['win_rate']:<10}")
        
        # TOP 3 ADAPTIVE RESULTS
        print(f"\n🏆 TOP 3 ADAPTIVE STRATEGIES (Self-Adjusting):")
        print("=" * 70)
        
        for i in range(min(3, len(results))):
            result = results[i]
            strategy_parts = result['strategy'].split(' (')
            strategy_name = strategy_parts[0]
            symbol = strategy_parts[1].rstrip(')') if len(strategy_parts) > 1 else ''
            
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            print(f"{medal} #{i+1}: {strategy_name} on {symbol}")
            print(f"   💰 Return: {result['total_return']:.2f}% (${result['final_capital']:.2f} from $2,000)")
            print(f"   📊 Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%")
            print(f"   🧠 Adaptive Features: Adjusts parameters based on market conditions")
            print()
        
        # Strategy performance summary
        strategy_performance = {}
        for result in results:
            strategy_name = result['strategy'].split(' (')[0]
            if strategy_name not in strategy_performance:
                strategy_performance[strategy_name] = []
            strategy_performance[strategy_name].append(result['total_return'])
        
        print(f"📊 AVERAGE PERFORMANCE BY ADAPTIVE STRATEGY:")
        print("-" * 60)
        strategy_averages = []
        for strategy_name, returns in strategy_performance.items():
            avg_return = sum(returns) / len(returns)
            strategy_averages.append((strategy_name, avg_return))
        
        strategy_averages.sort(key=lambda x: x[1], reverse=True)
        
        for strategy_name, avg_return in strategy_averages:
            print(f"   {strategy_name:<25}: {avg_return:>8.2f}% average")
    
    print(f"\n✅ Adaptive strategies test complete!")

if __name__ == "__main__":
    asyncio.run(adaptive_strategies_test())


