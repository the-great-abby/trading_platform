#!/usr/bin/env python3
"""
Simple Test for Winning Ensemble Strategy
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_winning_ensemble_availability():
    """Test if the winning ensemble strategy is available"""
    
    print("🚀 Testing Winning Ensemble Strategy Availability")
    print("=" * 50)
    
    # Test importing the strategy
    print("\n1. Testing import...")
    try:
        from strategies.winning_ensemble_strategy import WinningEnsembleStrategy
        print("✅ Successfully imported WinningEnsembleStrategy")
    except ImportError as e:
        print(f"❌ Failed to import WinningEnsembleStrategy: {e}")
        return False
    
    # Test creating the strategy
    print("\n2. Testing strategy creation...")
    try:
        strategy = WinningEnsembleStrategy()
        print("✅ Successfully created WinningEnsembleStrategy instance")
    except Exception as e:
        print(f"❌ Failed to create WinningEnsembleStrategy: {e}")
        return False
    
    # Test strategy properties
    print("\n3. Testing strategy properties...")
    try:
        print(f"✅ Strategy Name: {strategy.name}")
        print(f"✅ Min Confidence Threshold: {strategy.min_confidence_threshold}")
        print(f"✅ Max Risk Per Trade: {strategy.max_risk_per_trade}")
        print(f"✅ Use Weighted Voting: {strategy.use_weighted_voting}")
    except Exception as e:
        print(f"❌ Error accessing strategy properties: {e}")
        return False
    
    # Test strategy weights
    print("\n4. Testing strategy weights...")
    try:
        print("✅ Return-based Weights:")
        for name, weight in strategy.strategy_weights.items():
            print(f"   - {name}: {weight:.2f}")
        
        print("\n✅ Risk-adjusted Weights:")
        for name, weight in strategy.risk_adjusted_weights.items():
            print(f"   - {name}: {weight:.2f}")
    except Exception as e:
        print(f"❌ Error accessing strategy weights: {e}")
        return False
    
    # Test performance summary
    print("\n5. Testing performance summary...")
    try:
        performance = strategy.get_strategy_performance_summary()
        print("✅ Performance Summary:")
        print(f"   - Strategy Name: {performance['strategy_name']}")
        print(f"   - Expected Total Return: {performance['total_return']}%")
        print(f"   - Expected Sharpe Ratio: {performance['sharpe_ratio']}")
        print(f"   - Expected Max Drawdown: {performance['max_drawdown']}%")
        print(f"   - Expected Win Rate: {performance['win_rate']}%")
        print(f"   - Expected Profit Factor: {performance['profit_factor']}")
    except Exception as e:
        print(f"❌ Error getting performance summary: {e}")
        return False
    
    # Test strategy factory integration
    print("\n6. Testing strategy factory integration...")
    try:
        from strategies.strategy_factory import StrategyFactory
        factory = StrategyFactory()
        
        # Test if the strategy can be created through the factory
        ensemble_strategy = factory._create_strategy_by_name('WinningEnsembleStrategy')
        if ensemble_strategy:
            print("✅ Successfully created WinningEnsembleStrategy through factory")
        else:
            print("❌ Failed to create WinningEnsembleStrategy through factory")
            return False
    except Exception as e:
        print(f"❌ Error testing factory integration: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📋 Summary:")
    print("✅ Import: Working")
    print("✅ Creation: Working")
    print("✅ Properties: Working")
    print("✅ Weights: Working")
    print("✅ Performance Summary: Working")
    print("✅ Factory Integration: Working")
    
    print("\n🚀 The Winning Ensemble Strategy is ready for use!")
    print("📍 Location: src/strategies/winning_ensemble_strategy.py")
    print("🎯 Available in: Strategy Factory and Backtest Dashboard")
    
    return True


if __name__ == "__main__":
    success = test_winning_ensemble_availability()
    if success:
        print("\n✅ All integration tests passed successfully!")
    else:
        print("\n❌ Some integration tests failed.")
        sys.exit(1) 