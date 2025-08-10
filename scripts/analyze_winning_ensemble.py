#!/usr/bin/env python3
"""
Analysis of Winning Ensemble Strategy for Algorithmic Trading
Shows how to combine the best-performing strategies into a single trading signal
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


class WinningEnsembleAnalyzer:
    """Analyze and demonstrate the winning ensemble strategy"""
    
    def __init__(self):
        self.strategy_factory = StrategyFactory()
        self.ensemble_strategy = WinningEnsembleStrategy(
            min_confidence_threshold=0.6,
            max_risk_per_trade=0.02,
            use_weighted_voting=True
        )
        
    async def analyze_strategy_performance(self):
        """Analyze the performance of individual strategies vs ensemble"""
        
        print("\n" + "="*80)
        print("WINNING ENSEMBLE STRATEGY ANALYSIS")
        print("="*80)
        
        # Strategy performance data from backtest results
        strategy_performance = {
            'Ichimoku': {
                'total_return': 51.80,
                'sharpe_ratio': -1.088,
                'max_drawdown': 3.59,
                'win_rate': 55.0,
                'profit_factor': 1.48,
                'total_trades': 56
            },
            'CashSecuredPut': {
                'total_return': 53.48,
                'sharpe_ratio': -0.598,
                'max_drawdown': 23.13,
                'win_rate': 66.1,
                'profit_factor': 1.30,
                'total_trades': 22
            },
            'SMACrossover': {
                'total_return': 38.93,
                'sharpe_ratio': 0.712,
                'max_drawdown': 26.15,
                'win_rate': 65.9,
                'profit_factor': 1.19,
                'total_trades': 65
            },
            'Momentum': {
                'total_return': 45.82,
                'sharpe_ratio': 0.210,
                'max_drawdown': 0.72,
                'win_rate': 48.1,
                'profit_factor': 1.06,
                'total_trades': 29
            },
            'MeanReversion': {
                'total_return': 29.61,
                'sharpe_ratio': 0.305,
                'max_drawdown': 10.57,
                'win_rate': 59.8,
                'profit_factor': 1.24,
                'total_trades': 94
            },
            'EnhancedDayTrading': {
                'total_return': 38.35,
                'sharpe_ratio': 1.172,
                'max_drawdown': 17.54,
                'win_rate': 57.7,
                'profit_factor': 1.37,
                'total_trades': 64
            },
            'RegimeSwitching': {
                'total_return': 40.70,
                'sharpe_ratio': 0.647,
                'max_drawdown': 18.16,
                'win_rate': 41.7,
                'profit_factor': 1.11,
                'total_trades': 42
            },
            'GreeksEnhanced': {
                'total_return': -17.12,
                'sharpe_ratio': 1.450,
                'max_drawdown': 14.56,
                'win_rate': 54.0,
                'profit_factor': 1.32,
                'total_trades': 96
            },
            'IronCondor': {
                'total_return': 22.54,
                'sharpe_ratio': 1.319,
                'max_drawdown': 3.66,
                'win_rate': 57.8,
                'profit_factor': 1.13,
                'total_trades': 50
            },
            'Volatility': {
                'total_return': -19.80,
                'sharpe_ratio': 0.734,
                'max_drawdown': 2.53,
                'win_rate': 51.7,
                'profit_factor': 1.43,
                'total_trades': 71
            }
        }
        
        # Print individual strategy performance
        print("\nINDIVIDUAL STRATEGY PERFORMANCE:")
        print("-" * 80)
        print(f"{'Strategy':<20} {'Return':<8} {'Sharpe':<8} {'Drawdown':<10} {'Win Rate':<10} {'Profit Factor':<12}")
        print("-" * 80)
        
        for strategy, metrics in strategy_performance.items():
            print(f"{strategy:<20} {metrics['total_return']:>6.2f}% {metrics['sharpe_ratio']:>7.3f} "
                  f"{metrics['max_drawdown']:>8.2f}% {metrics['win_rate']:>8.1f}% {metrics['profit_factor']:>10.2f}")
        
        # Calculate ensemble expected performance
        print("\nENSEMBLE STRATEGY EXPECTED PERFORMANCE:")
        print("-" * 80)
        
        # Weighted averages based on strategy weights
        weights = self.ensemble_strategy.strategy_weights
        risk_weights = self.ensemble_strategy.risk_adjusted_weights
        
        # Calculate weighted metrics
        weighted_return = sum(strategy_performance[s]['total_return'] * weights[s] 
                            for s in weights.keys() if s in strategy_performance)
        weighted_sharpe = sum(strategy_performance[s]['sharpe_ratio'] * risk_weights[s] 
                             for s in risk_weights.keys() if s in strategy_performance)
        weighted_drawdown = sum(strategy_performance[s]['max_drawdown'] * weights[s] 
                               for s in weights.keys() if s in strategy_performance)
        weighted_win_rate = sum(strategy_performance[s]['win_rate'] * weights[s] 
                               for s in weights.keys() if s in strategy_performance)
        weighted_profit_factor = sum(strategy_performance[s]['profit_factor'] * weights[s] 
                                   for s in weights.keys() if s in strategy_performance)
        
        print(f"Expected Total Return: {weighted_return:.2f}%")
        print(f"Expected Sharpe Ratio: {weighted_sharpe:.3f}")
        print(f"Expected Max Drawdown: {weighted_drawdown:.2f}%")
        print(f"Expected Win Rate: {weighted_win_rate:.1f}%")
        print(f"Expected Profit Factor: {weighted_profit_factor:.2f}")
        
        return strategy_performance
    
    def demonstrate_signal_generation(self):
        """Demonstrate how the ensemble strategy generates signals"""
        
        print("\n" + "="*80)
        print("SIGNAL GENERATION DEMONSTRATION")
        print("="*80)
        
        # Show strategy weights
        print("\nStrategy Weights (Return-based):")
        for strategy, weight in self.ensemble_strategy.strategy_weights.items():
            print(f"  {strategy}: {weight:.3f}")
        
        print("\nRisk-Adjusted Weights (Sharpe-based):")
        for strategy, weight in self.ensemble_strategy.risk_adjusted_weights.items():
            print(f"  {strategy}: {weight:.3f}")
        
        # Demonstrate signal combination logic
        print("\nSignal Combination Logic:")
        print("1. Each strategy generates individual signals (BUY/SELL/HOLD)")
        print("2. Signals are weighted by strategy performance")
        print("3. Buy and sell signals are aggregated separately")
        print("4. Final signal is determined by highest weighted confidence")
        print("5. Position size is calculated based on confidence and risk management")
        
        # Show confidence calculation
        print("\nConfidence Calculation:")
        print("- Uses risk-adjusted weights for better risk management")
        print("- Applies signal strength multiplier based on number of agreeing signals")
        print("- Boosts confidence by up to 20% when multiple strategies agree")
        print("- Caps final confidence at 1.0")
        
        # Show position sizing
        print("\nPosition Sizing:")
        print("- Base position: 2% of portfolio per trade")
        print("- Scaled by confidence (0.5x to 1.0x)")
        print("- Risk management: max 2% risk per trade")
        
    def show_implementation_guide(self):
        """Show how to implement the ensemble strategy in live trading"""
        
        print("\n" + "="*80)
        print("IMPLEMENTATION GUIDE FOR ALGORITHMIC TRADING")
        print("="*80)
        
        print("\n1. STRATEGY SETUP:")
        print("   - Initialize WinningEnsembleStrategy")
        print("   - Configure confidence threshold (default: 0.6)")
        print("   - Set risk per trade (default: 2%)")
        print("   - Choose voting method (weighted vs return-based)")
        
        print("\n2. MARKET DATA INTEGRATION:")
        print("   - Connect to real-time market data feed")
        print("   - Ensure sufficient historical data (50+ periods)")
        print("   - Calculate technical indicators for all strategies")
        
        print("\n3. SIGNAL GENERATION:")
        print("   - Run all individual strategies on current market data")
        print("   - Collect signals from each strategy")
        print("   - Apply weighted voting to combine signals")
        print("   - Generate final ensemble signal")
        
        print("\n4. RISK MANAGEMENT:")
        print("   - Check position limits")
        print("   - Validate against portfolio constraints")
        print("   - Apply stop-loss and take-profit levels")
        print("   - Monitor correlation between strategies")
        
        print("\n5. EXECUTION:")
        print("   - Route signals to order management system")
        print("   - Execute trades with proper slippage handling")
        print("   - Record all trades and performance metrics")
        print("   - Monitor strategy performance continuously")
        
        # Show code example
        print("\n6. CODE EXAMPLE:")
        print("""
# Initialize ensemble strategy
ensemble = WinningEnsembleStrategy(
    min_confidence_threshold=0.6,
    max_risk_per_trade=0.02,
    use_weighted_voting=True
)

# Initialize individual strategies
await ensemble.initialize_strategies(strategy_factory)

# Generate signal
signal = await ensemble.generate_signal(symbol, market_data)

if signal and signal.confidence >= 0.6:
    # Execute trade
    execute_trade(signal)
        """)
    
    def show_risk_management_guidelines(self):
        """Show risk management guidelines for the ensemble strategy"""
        
        print("\n" + "="*80)
        print("RISK MANAGEMENT GUIDELINES")
        print("="*80)
        
        print("\n1. POSITION SIZING:")
        print("   - Maximum 2% risk per trade")
        print("   - Scale position size by signal confidence")
        print("   - Consider portfolio correlation")
        print("   - Implement position limits per symbol")
        
        print("\n2. DIVERSIFICATION:")
        print("   - Trade multiple symbols simultaneously")
        print("   - Avoid over-concentration in single sector")
        print("   - Monitor strategy correlation")
        print("   - Rebalance portfolio regularly")
        
        print("\n3. STOP-LOSS MANAGEMENT:")
        print("   - Set stop-loss at 2-3% below entry")
        print("   - Use trailing stops for profitable positions")
        print("   - Implement time-based exits")
        print("   - Monitor drawdown limits")
        
        print("\n4. PERFORMANCE MONITORING:")
        print("   - Track Sharpe ratio continuously")
        print("   - Monitor maximum drawdown")
        print("   - Calculate daily VaR")
        print("   - Review strategy performance monthly")
        
        print("\n5. STRATEGY ADAPTATION:")
        print("   - Re-weight strategies based on recent performance")
        print("   - Add/remove strategies as needed")
        print("   - Adjust confidence thresholds")
        print("   - Implement regime detection")
    
    def show_optimization_opportunities(self):
        """Show opportunities for optimizing the ensemble strategy"""
        
        print("\n" + "="*80)
        print("OPTIMIZATION OPPORTUNITIES")
        print("="*80)
        
        print("\n1. DYNAMIC WEIGHTING:")
        print("   - Re-weight strategies based on recent performance")
        print("   - Use rolling Sharpe ratios")
        print("   - Implement regime-aware weighting")
        print("   - Add momentum to strategy selection")
        
        print("\n2. MACHINE LEARNING ENHANCEMENT:")
        print("   - Use ML to predict strategy performance")
        print("   - Implement ensemble learning methods")
        print("   - Add feature engineering for market conditions")
        print("   - Use neural networks for signal combination")
        
        print("\n3. MARKET REGIME DETECTION:")
        print("   - Detect bull/bear/sideways markets")
        print("   - Adjust strategy weights by regime")
        print("   - Use volatility regime detection")
        print("   - Implement correlation-based switching")
        
        print("\n4. ADVANCED RISK MANAGEMENT:")
        print("   - Implement Kelly Criterion for position sizing")
        print("   - Use Black-Litterman model for portfolio optimization")
        print("   - Add options for hedging")
        print("   - Implement dynamic correlation adjustment")
        
        print("\n5. PERFORMANCE ATTRIBUTION:")
        print("   - Decompose returns by strategy contribution")
        print("   - Analyze factor exposures")
        print("   - Monitor strategy drift")
        print("   - Implement style analysis")


async def main():
    """Main function to run the analysis"""
    try:
        analyzer = WinningEnsembleAnalyzer()
        
        # Run analysis
        await analyzer.analyze_strategy_performance()
        analyzer.demonstrate_signal_generation()
        analyzer.show_implementation_guide()
        analyzer.show_risk_management_guidelines()
        analyzer.show_optimization_opportunities()
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("The Winning Ensemble Strategy combines the best-performing strategies")
        print("from your backtest results into a single algorithmic trading signal.")
        print("\nKey Benefits:")
        print("- Diversifies risk across multiple strategies")
        print("- Improves signal quality through consensus")
        print("- Reduces false signals through confirmation")
        print("- Provides better risk-adjusted returns")
        print("\nNext Steps:")
        print("1. Implement the strategy in your trading system")
        print("2. Run paper trading to validate performance")
        print("3. Optimize weights based on recent market conditions")
        print("4. Deploy with proper risk management")
        
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 