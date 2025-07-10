#!/usr/bin/env python3
"""
Demo Advanced Exit Strategies
============================
Demonstrates the new advanced exit strategies:
- Momentum-based exits
- Volatility-based exits
- Correlation-based exits
- Machine learning exits
- Options-based exits
- Market regime exits
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.strategies.advanced_exit_strategies import (
    MomentumExitStrategy,
    VolatilityExitStrategy,
    CorrelationExitStrategy,
    MachineLearningExitStrategy,
    OptionsBasedExitStrategy,
    MarketRegimeExitStrategy
)
from src.strategies.exit_strategies import ExitSignal, ExitReason
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

def generate_sample_data(symbol: str = "AAPL", days: int = 100) -> pd.DataFrame:
    """Generate sample market data for testing"""
    np.random.seed(42)
    
    # Generate realistic price data
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='D')
    
    # Start with a base price
    base_price = 150.0
    
    # Generate price movements with trend and volatility
    returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # Add some trend
        trend = 0.0005 if i < len(dates) // 2 else -0.0003
        new_price = prices[-1] * (1 + returns[i] + trend)
        prices.append(max(new_price, 1.0))  # Ensure positive prices
    
    # Create DataFrame
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    # Ensure High >= Close >= Low
    data['High'] = data[['High', 'Close']].max(axis=1)
    data['Low'] = data[['Low', 'Close']].min(axis=1)
    
    return data.set_index('Date')

def generate_market_data() -> pd.DataFrame:
    """Generate sample market index data"""
    np.random.seed(123)
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=100), 
                         end=datetime.now(), freq='D')
    
    base_price = 3000.0
    returns = np.random.normal(0.0008, 0.015, len(dates))
    prices = [base_price]
    
    for i in range(1, len(dates)):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1.0))
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': np.random.randint(5000000, 50000000, len(dates))
    }).set_index('Date')

def generate_options_data() -> dict:
    """Generate sample options market data"""
    return {
        'put_call_ratio': np.random.uniform(0.8, 2.0),
        'implied_volatility': np.random.uniform(0.2, 0.6),
        'options_volume_ratio': np.random.uniform(0.5, 3.0)
    }

def demo_momentum_exit_strategy():
    """Demo momentum-based exit strategy"""
    print("\n" + "="*60)
    print("MOMENTUM EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data
    data = generate_sample_data("AAPL", 100)
    
    # Initialize strategy
    strategy = MomentumExitStrategy(
        momentum_period=10,
        trend_period=20,
        momentum_threshold=0.02,
        trend_strength_threshold=0.05
    )
    
    # Test exit signals
    entry_price = data['Close'].iloc[20]
    position_type = "LONG"
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    print(f"Data Points: {len(data)}")
    
    # Test multiple points
    exit_signals = []
    for i in range(30, len(data)):
        test_data = data.iloc[:i+1]
        signal = strategy.get_exit_signal(test_data, position_type, entry_price)
        if signal:
            exit_signals.append({
                'date': test_data.index[-1],
                'price': signal.price,
                'confidence': signal.confidence,
                'reason': signal.reason.value,
                'metadata': signal.metadata
            })
    
    print(f"\nExit Signals Found: {len(exit_signals)}")
    for i, signal in enumerate(exit_signals[:5]):  # Show first 5
        print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
        print(f"     Price: ${signal['price']:.2f}")
        print(f"     Confidence: {signal['confidence']:.2f}")
        print(f"     Reason: {signal['reason']}")
        if 'momentum' in signal['metadata']:
            print(f"     Momentum: {signal['metadata']['momentum']:.4f}")
        print()

def demo_volatility_exit_strategy():
    """Demo volatility-based exit strategy"""
    print("\n" + "="*60)
    print("VOLATILITY EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data with varying volatility
    data = generate_sample_data("TSLA", 100)
    
    # Add volatility spikes
    volatility_spikes = [40, 60, 80]
    for spike in volatility_spikes:
        if spike < len(data):
            # Create volatility spike
            data.iloc[spike, data.columns.get_loc('Close')] *= 1.1
    
    # Initialize strategy
    strategy = VolatilityExitStrategy(
        volatility_period=20,
        volatility_threshold=0.03,
        regime_change_threshold=0.5
    )
    
    # Test exit signals
    entry_price = data['Close'].iloc[20]
    position_type = "LONG"
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    print(f"Volatility Spikes Added: {volatility_spikes}")
    
    # Test multiple points
    exit_signals = []
    for i in range(30, len(data)):
        test_data = data.iloc[:i+1]
        signal = strategy.get_exit_signal(test_data, position_type, entry_price)
        if signal:
            exit_signals.append({
                'date': test_data.index[-1],
                'price': signal.price,
                'confidence': signal.confidence,
                'reason': signal.reason.value,
                'metadata': signal.metadata
            })
    
    print(f"\nExit Signals Found: {len(exit_signals)}")
    for i, signal in enumerate(exit_signals[:5]):
        print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
        print(f"     Price: ${signal['price']:.2f}")
        print(f"     Confidence: {signal['confidence']:.2f}")
        print(f"     Reason: {signal['reason']}")
        if 'volatility_regime_change' in signal['metadata']:
            print(f"     Regime Change: {signal['metadata']['volatility_regime_change']}")
        print()

def demo_correlation_exit_strategy():
    """Demo correlation-based exit strategy"""
    print("\n" + "="*60)
    print("CORRELATION EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data
    stock_data = generate_sample_data("AAPL", 100)
    market_data = generate_market_data()
    
    # Align data
    common_dates = stock_data.index.intersection(market_data.index)
    stock_data = stock_data.loc[common_dates]
    market_data = market_data.loc[common_dates]
    
    # Initialize strategy
    strategy = CorrelationExitStrategy(
        correlation_period=30,
        correlation_threshold=0.7,
        correlation_break_threshold=0.3
    )
    
    # Test exit signals
    entry_price = stock_data['Close'].iloc[20]
    position_type = "LONG"
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    print(f"Data Points: {len(stock_data)}")
    
    # Test multiple points
    exit_signals = []
    for i in range(40, len(stock_data)):
        test_stock_data = stock_data.iloc[:i+1]
        test_market_data = market_data.iloc[:i+1]
        signal = strategy.get_exit_signal(test_stock_data, test_market_data, position_type, entry_price)
        if signal:
            exit_signals.append({
                'date': test_stock_data.index[-1],
                'price': signal.price,
                'confidence': signal.confidence,
                'reason': signal.reason.value,
                'metadata': signal.metadata
            })
    
    print(f"\nExit Signals Found: {len(exit_signals)}")
    for i, signal in enumerate(exit_signals[:5]):
        print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
        print(f"     Price: ${signal['price']:.2f}")
        print(f"     Confidence: {signal['confidence']:.2f}")
        print(f"     Reason: {signal['reason']}")
        if 'correlation' in signal['metadata']:
            print(f"     Correlation: {signal['metadata']['correlation']:.4f}")
        print()

def demo_ml_exit_strategy():
    """Demo machine learning exit strategy"""
    print("\n" + "="*60)
    print("MACHINE LEARNING EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data
    data = generate_sample_data("NVDA", 100)
    
    # Initialize strategy
    strategy = MachineLearningExitStrategy(
        lookback_period=60,
        retrain_frequency=30
    )
    
    # Create synthetic training data
    historical_data = []
    for i in range(60, len(data) - 10):
        window_data = data.iloc[i-60:i+1]
        
        # Simple rule: exit if price drops more than 5% from entry
        entry_price = window_data['Close'].iloc[0]
        current_price = window_data['Close'].iloc[-1]
        should_exit = (current_price - entry_price) / entry_price < -0.05
        
        historical_data.append((window_data, should_exit))
    
    # Train model
    print("Training ML model...")
    strategy.train_model(historical_data)
    
    if strategy.model is not None:
        print("Model trained successfully!")
        
        # Test exit signals
        entry_price = data['Close'].iloc[80]
        position_type = "LONG"
        
        print(f"Entry Price: ${entry_price:.2f}")
        print(f"Position Type: {position_type}")
        
        # Test multiple points
        exit_signals = []
        for i in range(85, len(data)):
            test_data = data.iloc[:i+1]
            signal = strategy.get_exit_signal(test_data, position_type, entry_price)
            if signal:
                exit_signals.append({
                    'date': test_data.index[-1],
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'reason': signal.reason.value,
                    'metadata': signal.metadata
                })
        
        print(f"\nExit Signals Found: {len(exit_signals)}")
        for i, signal in enumerate(exit_signals[:5]):
            print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
            print(f"     Price: ${signal['price']:.2f}")
            print(f"     Confidence: {signal['confidence']:.2f}")
            print(f"     Reason: {signal['reason']}")
            if 'ml_exit_probability' in signal['metadata']:
                print(f"     ML Probability: {signal['metadata']['ml_exit_probability']:.4f}")
            print()
    else:
        print("Failed to train model - insufficient data")

def demo_options_exit_strategy():
    """Demo options-based exit strategy"""
    print("\n" + "="*60)
    print("OPTIONS-BASED EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data
    data = generate_sample_data("SPY", 100)
    
    # Initialize strategy
    strategy = OptionsBasedExitStrategy(
        put_call_ratio_threshold=1.5,
        implied_volatility_threshold=0.4,
        options_volume_threshold=2.0
    )
    
    # Test exit signals
    entry_price = data['Close'].iloc[20]
    position_type = "LONG"
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    
    # Test multiple points with different options scenarios
    exit_signals = []
    scenarios = [
        {'put_call_ratio': 1.8, 'implied_volatility': 0.5, 'options_volume_ratio': 2.5},
        {'put_call_ratio': 0.8, 'implied_volatility': 0.6, 'options_volume_ratio': 3.0},
        {'put_call_ratio': 1.2, 'implied_volatility': 0.3, 'options_volume_ratio': 2.8}
    ]
    
    for i in range(30, len(data), 20):  # Test every 20th point
        test_data = data.iloc[:i+1]
        options_data = scenarios[i % len(scenarios)]
        
        signal = strategy.get_exit_signal(test_data, options_data, position_type, entry_price)
        if signal:
            exit_signals.append({
                'date': test_data.index[-1],
                'price': signal.price,
                'confidence': signal.confidence,
                'reason': signal.reason.value,
                'metadata': signal.metadata
            })
    
    print(f"\nExit Signals Found: {len(exit_signals)}")
    for i, signal in enumerate(exit_signals[:5]):
        print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
        print(f"     Price: ${signal['price']:.2f}")
        print(f"     Confidence: {signal['confidence']:.2f}")
        print(f"     Reason: {signal['reason']}")
        if 'options_signals' in signal['metadata']:
            print(f"     Options Signals: {len(signal['metadata']['options_signals'])}")
        print()

def demo_market_regime_exit_strategy():
    """Demo market regime exit strategy"""
    print("\n" + "="*60)
    print("MARKET REGIME EXIT STRATEGY DEMO")
    print("="*60)
    
    # Generate sample data with different regimes
    data = generate_sample_data("QQQ", 100)
    
    # Add regime changes
    # High volatility period
    data.iloc[30:50, data.columns.get_loc('Close')] *= 1.05
    # Trending down period
    data.iloc[60:80, data.columns.get_loc('Close')] *= 0.95
    
    # Initialize strategy
    strategy = MarketRegimeExitStrategy(
        regime_period=50,
        volatility_threshold=0.03,
        trend_threshold=0.02
    )
    
    # Test exit signals
    entry_price = data['Close'].iloc[20]
    position_type = "LONG"
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    
    # Test multiple points
    exit_signals = []
    for i in range(30, len(data)):
        test_data = data.iloc[:i+1]
        signal = strategy.get_exit_signal(test_data, position_type, entry_price)
        if signal:
            exit_signals.append({
                'date': test_data.index[-1],
                'price': signal.price,
                'confidence': signal.confidence,
                'reason': signal.reason.value,
                'metadata': signal.metadata
            })
    
    print(f"\nExit Signals Found: {len(exit_signals)}")
    for i, signal in enumerate(exit_signals[:5]):
        print(f"  {i+1}. Date: {signal['date'].strftime('%Y-%m-%d')}")
        print(f"     Price: ${signal['price']:.2f}")
        print(f"     Confidence: {signal['confidence']:.2f}")
        print(f"     Reason: {signal['reason']}")
        if 'market_regime' in signal['metadata']:
            print(f"     Market Regime: {signal['metadata']['market_regime']}")
        print()

def compare_exit_strategies():
    """Compare performance of different exit strategies"""
    print("\n" + "="*60)
    print("EXIT STRATEGIES COMPARISON")
    print("="*60)
    
    # Generate sample data
    data = generate_sample_data("AAPL", 100)
    entry_price = data['Close'].iloc[20]
    position_type = "LONG"
    
    # Initialize all strategies
    strategies = {
        "Momentum": MomentumExitStrategy(),
        "Volatility": VolatilityExitStrategy(),
        "Market Regime": MarketRegimeExitStrategy()
    }
    
    # Test each strategy
    results = {}
    for name, strategy in strategies.items():
        exit_signals = []
        for i in range(30, len(data)):
            test_data = data.iloc[:i+1]
            signal = strategy.get_exit_signal(test_data, position_type, entry_price)
            if signal:
                exit_signals.append({
                    'date': test_data.index[-1],
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'reason': signal.reason.value
                })
        
        results[name] = {
            'signals_count': len(exit_signals),
            'avg_confidence': np.mean([s['confidence'] for s in exit_signals]) if exit_signals else 0,
            'first_signal_date': exit_signals[0]['date'] if exit_signals else None,
            'avg_price': np.mean([s['price'] for s in exit_signals]) if exit_signals else 0
        }
    
    # Display comparison
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Position Type: {position_type}")
    print(f"Data Points: {len(data)}")
    print()
    
    print(f"{'Strategy':<15} {'Signals':<8} {'Avg Conf':<10} {'First Signal':<15} {'Avg Exit Price':<15}")
    print("-" * 70)
    
    for name, result in results.items():
        print(f"{name:<15} {result['signals_count']:<8} {result['avg_confidence']:<10.3f} "
              f"{result['first_signal_date'].strftime('%Y-%m-%d') if result['first_signal_date'] else 'None':<15} "
              f"${result['avg_price']:<14.2f}")

def main():
    """Run all exit strategy demos"""
    print("ADVANCED EXIT STRATEGIES DEMO")
    print("="*60)
    print("This demo showcases the new advanced exit strategies:")
    print("- Momentum-based exits")
    print("- Volatility-based exits") 
    print("- Correlation-based exits")
    print("- Machine learning exits")
    print("- Options-based exits")
    print("- Market regime exits")
    print()
    
    try:
        # Run individual demos
        demo_momentum_exit_strategy()
        demo_volatility_exit_strategy()
        demo_correlation_exit_strategy()
        demo_ml_exit_strategy()
        demo_options_exit_strategy()
        demo_market_regime_exit_strategy()
        
        # Compare strategies
        compare_exit_strategies()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nKey Benefits of Advanced Exit Strategies:")
        print("1. Momentum-based: Captures trend reversals early")
        print("2. Volatility-based: Manages risk during market stress")
        print("3. Correlation-based: Exits when stock behavior changes")
        print("4. ML-based: Learns from historical patterns")
        print("5. Options-based: Uses derivatives market signals")
        print("6. Market regime: Adapts to changing market conditions")
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 