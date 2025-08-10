#!/usr/bin/env python3
"""
Local Testing Script for Winning Ensemble Strategy
This script tests the winning ensemble strategy locally without requiring the full Kubernetes infrastructure.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.winning_ensemble_strategy import WinningEnsembleStrategy
from strategies.strategy_factory import StrategyFactory
from core.types import TradeSignal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockMarketData:
    """Mock market data for testing"""
    
    def __init__(self):
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample market data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        
        # Generate realistic price data
        np.random.seed(42)  # For reproducible results
        base_price = 100
        returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0.01, 0.02))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0.01, 0.02))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        })
        
        # Calculate technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['RSI'] = self._calculate_rsi(data['Close'])
        data['MACD'] = self._calculate_macd(data['Close'])
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = self._calculate_bollinger_bands(data['Close'])
        
        return data
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    def get_data(self, symbol: str, start_date: str = None, end_date: str = None):
        """Get market data for a symbol"""
        data = self.sample_data.copy()
        
        if start_date:
            data = data[data['Date'] >= start_date]
        if end_date:
            data = data[data['Date'] <= end_date]
        
        return data


class LocalWinningEnsembleTester:
    """Local tester for the winning ensemble strategy"""
    
    def __init__(self):
        self.ensemble_strategy = WinningEnsembleStrategy(
            min_confidence_threshold=0.6,
            max_risk_per_trade=0.02,
            use_weighted_voting=True
        )
        self.strategy_factory = StrategyFactory()
        self.market_data = MockMarketData()
        
    async def test_strategy_performance(self):
        """Test the strategy performance with mock data"""
        print("\n" + "="*80)
        print("WINNING ENSEMBLE STRATEGY LOCAL TESTING")
        print("="*80)
        
        # Test with different symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        results = []
        
        for symbol in symbols:
            print(f"\nTesting {symbol}...")
            
            # Get mock data
            data = self.market_data.get_data(symbol, '2023-01-01', '2024-12-31')
            
            if len(data) < 50:
                print(f"Insufficient data for {symbol}")
                continue
            
            # Test signal generation
            signals = []
            for i in range(50, len(data), 5):  # Test every 5th day
                test_data = data.iloc[:i+1]
                
                try:
                    signal = await self.ensemble_strategy.generate_signal(
                        symbol=symbol,
                        data=test_data
                    )
                    
                    if signal:
                        signals.append({
                            'date': test_data.iloc[-1]['Date'],
                            'symbol': symbol,
                            'action': signal.action,
                            'confidence': signal.confidence,
                            'price': signal.price,
                            'quantity': signal.quantity
                        })
                        
                except Exception as e:
                    logger.warning(f"Error generating signal for {symbol}: {e}")
                    continue
            
            if signals:
                results.append({
                    'symbol': symbol,
                    'total_signals': len(signals),
                    'buy_signals': len([s for s in signals if s['action'] == 'BUY']),
                    'sell_signals': len([s for s in signals if s['action'] == 'SELL']),
                    'avg_confidence': np.mean([s['confidence'] for s in signals]),
                    'signals': signals
                })
                
                print(f"  Generated {len(signals)} signals")
                print(f"  Average confidence: {np.mean([s['confidence'] for s in signals]):.3f}")
            else:
                print(f"  No signals generated")
        
        return results
    
    def analyze_results(self, results):
        """Analyze the test results"""
        print("\n" + "="*80)
        print("TEST RESULTS ANALYSIS")
        print("="*80)
        
        if not results:
            print("No results to analyze")
            return
        
        # Overall statistics
        total_signals = sum(r['total_signals'] for r in results)
        total_buy = sum(r['buy_signals'] for r in results)
        total_sell = sum(r['sell_signals'] for r in results)
        avg_confidence = np.mean([r['avg_confidence'] for r in results])
        
        print(f"\nOverall Statistics:")
        print(f"  Total Signals: {total_signals}")
        print(f"  Buy Signals: {total_buy}")
        print(f"  Sell Signals: {total_sell}")
        print(f"  Average Confidence: {avg_confidence:.3f}")
        
        # Per-symbol analysis
        print(f"\nPer-Symbol Analysis:")
        print(f"{'Symbol':<10} {'Signals':<8} {'Buy':<6} {'Sell':<6} {'Avg Conf':<10}")
        print("-" * 50)
        
        for result in results:
            print(f"{result['symbol']:<10} {result['total_signals']:<8} "
                  f"{result['buy_signals']:<6} {result['sell_signals']:<6} "
                  f"{result['avg_confidence']:<10.3f}")
        
        # Strategy performance summary
        print(f"\nStrategy Performance Summary:")
        performance = self.ensemble_strategy.get_strategy_performance_summary()
        
        for key, value in performance.items():
            if key not in ['strategy_weights', 'risk_adjusted_weights']:
                print(f"  {key}: {value}")
        
        # Show strategy weights
        print(f"\nStrategy Weights (Return-based):")
        for strategy, weight in self.ensemble_strategy.strategy_weights.items():
            print(f"  {strategy}: {weight:.3f}")
        
        print(f"\nRisk-Adjusted Weights (Sharpe-based):")
        for strategy, weight in self.ensemble_strategy.risk_adjusted_weights.items():
            print(f"  {strategy}: {weight:.3f}")
    
    async def demonstrate_signal_generation(self):
        """Demonstrate signal generation process"""
        print("\n" + "="*80)
        print("SIGNAL GENERATION DEMONSTRATION")
        print("="*80)
        
        # Get sample data
        data = self.market_data.get_data('AAPL', '2024-01-01', '2024-12-31')
        
        if len(data) < 100:
            print("Insufficient data for demonstration")
            return
        
        # Show the signal generation process
        print(f"\nTesting signal generation with {len(data)} data points...")
        
        # Test a few specific dates
        test_dates = [50, 100, 150, 200, 250]
        
        for i, date_idx in enumerate(test_dates):
            if date_idx >= len(data):
                continue
                
            test_data = data.iloc[:date_idx+1]
            current_date = test_data.iloc[-1]['Date']
            current_price = test_data.iloc[-1]['Close']
            
            print(f"\nTest {i+1}: {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")
            
            try:
                signal = await self.ensemble_strategy.generate_signal(
                    symbol='AAPL',
                    data=test_data
                )
                
                if signal:
                    print(f"  Signal: {signal.action}")
                    print(f"  Confidence: {signal.confidence:.3f}")
                    print(f"  Quantity: {signal.quantity:.2f}")
                    print(f"  Price: ${signal.price:.2f}")
                    
                    # Show metadata if available
                    if hasattr(signal, 'metadata') and signal.metadata:
                        print(f"  Buy Confidence: {signal.metadata.get('buy_confidence', 'N/A'):.3f}")
                        print(f"  Sell Confidence: {signal.metadata.get('sell_confidence', 'N/A'):.3f}")
                        print(f"  Strategy Contributions: {len(signal.metadata.get('strategy_contributions', []))}")
                else:
                    print(f"  No signal generated (confidence below threshold)")
                    
            except Exception as e:
                print(f"  Error: {e}")


async def main():
    """Main function to run the local testing"""
    try:
        tester = LocalWinningEnsembleTester()
        
        # Test strategy performance
        print("Testing strategy performance...")
        results = await tester.test_strategy_performance()
        
        # Analyze results
        tester.analyze_results(results)
        
        # Demonstrate signal generation
        await tester.demonstrate_signal_generation()
        
        print("\n" + "="*80)
        print("LOCAL TESTING COMPLETE")
        print("="*80)
        print("The winning ensemble strategy has been tested locally with mock data.")
        print("This demonstrates the strategy's signal generation capabilities without")
        print("requiring the full Kubernetes infrastructure.")
        print("\nNext steps:")
        print("1. Deploy to Kubernetes when resources are available")
        print("2. Test with real market data")
        print("3. Implement in live trading system")
        
    except Exception as e:
        logger.error(f"Error in local testing: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 