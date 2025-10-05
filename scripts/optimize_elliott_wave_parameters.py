#!/usr/bin/env python3
"""
Elliott Wave Strategy Parameter Optimization Script
Tests different parameter combinations to find optimal settings
"""

import requests
import json
import time
from typing import Dict, List, Tuple

def test_parameter_combination(
    confidence_threshold: float,
    lookback_period: int, 
    volatility_threshold: float,
    mean_reversion_threshold: float,
    strategy_name: str = "ElliottWaveCorrectiveStrategy"
) -> Dict:
    """Test a specific parameter combination"""
    
    # Update the strategy parameters in the container
    update_command = f"""
kubectl exec -n trading-system deployment/strategy-service -- python3 -c "
import sys
sys.path.append('/app')

# Force reload the module
import importlib
import src.strategies.enhanced_elliott_wave_strategies
importlib.reload(src.strategies.enhanced_elliott_wave_strategies)

from src.strategies.enhanced_elliott_wave_strategies import ElliottWaveCorrectiveStrategy

# Create strategy with custom parameters
strategy = ElliottWaveCorrectiveStrategy(
    confidence_threshold={confidence_threshold},
    lookback_period={lookback_period},
    volatility_threshold={volatility_threshold}
)

# Update the mean reversion threshold in the method
import inspect
lines = inspect.getsource(strategy.calculate_mean_reversion_signal).split('\\n')
for i, line in enumerate(lines):
    if 'deviation >' in line:
        lines[i] = f'        if deviation > {mean_reversion_threshold}:  # {mean_reversion_threshold*100:.1f}% above mean'
    elif 'deviation <' in line:
        lines[i] = f'        elif deviation < -{mean_reversion_threshold}:  # {mean_reversion_threshold*100:.1f}% below mean'

# Write the updated method back to the file
with open('/app/src/strategies/enhanced_elliott_wave_strategies.py', 'r') as f:
    content = f.read()

# Replace the method
import re
pattern = r'def calculate_mean_reversion_signal\(self, data: pd\.DataFrame\) -> Optional\[str\]:.*?(?=    async def|\Z)'
replacement = '\\n'.join(lines)
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('/app/src/strategies/enhanced_elliott_wave_strategies.py', 'w') as f:
    f.write(content)

print('Parameters updated successfully')
"
"""
    
    # Run the backtest
    backtest_request = {
        "symbols": ["AAPL"],
        "start_date": "2024-01-01", 
        "end_date": "2024-03-01",
        "initial_capital": 4000,
        "strategies": [strategy_name]
    }
    
    try:
        response = requests.post(
            "http://localhost:11080/api/backtest/run",
            json=backtest_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('results'):
                result = data['results'][0]
                return {
                    'success': True,
                    'total_return': result.get('total_return', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'win_rate': result.get('win_rate', 0),
                    'total_trades': result.get('total_trades', 0),
                    'profit_factor': result.get('profit_factor', 0),
                    'parameters': {
                        'confidence_threshold': confidence_threshold,
                        'lookback_period': lookback_period,
                        'volatility_threshold': volatility_threshold,
                        'mean_reversion_threshold': mean_reversion_threshold
                    }
                }
            else:
                return {'success': False, 'error': 'No results returned'}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def optimize_parameters():
    """Test different parameter combinations"""
    
    # Parameter ranges to test
    confidence_thresholds = [0.1, 0.15, 0.2, 0.25, 0.3]
    lookback_periods = [5, 7, 10, 14]
    volatility_thresholds = [0.005, 0.01, 0.015, 0.02]
    mean_reversion_thresholds = [0.005, 0.01, 0.015, 0.02]
    
    results = []
    total_combinations = len(confidence_thresholds) * len(lookback_periods) * len(volatility_thresholds) * len(mean_reversion_thresholds)
    current = 0
    
    print(f"Testing {total_combinations} parameter combinations...")
    
    for conf in confidence_thresholds:
        for lookback in lookback_periods:
            for vol in volatility_thresholds:
                for mean_rev in mean_reversion_thresholds:
                    current += 1
                    print(f"\\n[{current}/{total_combinations}] Testing: conf={conf}, lookback={lookback}, vol={vol}, mean_rev={mean_rev}")
                    
                    result = test_parameter_combination(conf, lookback, vol, mean_rev)
                    results.append(result)
                    
                    if result['success']:
                        print(f"✅ Success: {result['total_trades']} trades, {result['total_return']:.2%} return, {result['max_drawdown']:.2%} drawdown")
                    else:
                        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
                    time.sleep(1)  # Brief pause between tests
    
    # Analyze results
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        print("\\n❌ No successful parameter combinations found!")
        return
    
    print(f"\\n📊 ANALYSIS OF {len(successful_results)} SUCCESSFUL COMBINATIONS:")
    
    # Sort by different criteria
    by_return = sorted(successful_results, key=lambda x: x['total_return'], reverse=True)
    by_sharpe = sorted(successful_results, key=lambda x: x['sharpe_ratio'], reverse=True)
    by_trades = sorted(successful_results, key=lambda x: x['total_trades'], reverse=True)
    by_drawdown = sorted(successful_results, key=lambda x: x['max_drawdown'])
    
    print("\\n🏆 TOP 5 BY RETURN:")
    for i, result in enumerate(by_return[:5], 1):
        params = result['parameters']
        print(f"{i}. Return: {result['total_return']:.2%}, Trades: {result['total_trades']}, Drawdown: {result['max_drawdown']:.2%}")
        print(f"   Params: conf={params['confidence_threshold']}, lookback={params['lookback_period']}, vol={params['volatility_threshold']}, mean_rev={params['mean_reversion_threshold']}")
    
    print("\\n📈 TOP 5 BY SHARPE RATIO:")
    for i, result in enumerate(by_sharpe[:5], 1):
        params = result['parameters']
        print(f"{i}. Sharpe: {result['sharpe_ratio']:.3f}, Return: {result['total_return']:.2%}, Trades: {result['total_trades']}")
        print(f"   Params: conf={params['confidence_threshold']}, lookback={params['lookback_period']}, vol={params['volatility_threshold']}, mean_rev={params['mean_reversion_threshold']}")
    
    print("\\n🎯 TOP 5 BY TRADE COUNT:")
    for i, result in enumerate(by_trades[:5], 1):
        params = result['parameters']
        print(f"{i}. Trades: {result['total_trades']}, Return: {result['total_return']:.2%}, Drawdown: {result['max_drawdown']:.2%}")
        print(f"   Params: conf={params['confidence_threshold']}, lookback={params['lookback_period']}, vol={params['volatility_threshold']}, mean_rev={params['mean_reversion_threshold']}")
    
    print("\\n🛡️ TOP 5 BY LOWEST DRAWDOWN:")
    for i, result in enumerate(by_drawdown[:5], 1):
        params = result['parameters']
        print(f"{i}. Drawdown: {result['max_drawdown']:.2%}, Return: {result['total_return']:.2%}, Trades: {result['total_trades']}")
        print(f"   Params: conf={params['confidence_threshold']}, lookback={params['lookback_period']}, vol={params['volatility_threshold']}, mean_rev={params['mean_reversion_threshold']}")
    
    # Find balanced combination (good return, reasonable drawdown, decent trade count)
    balanced_results = [
        r for r in successful_results 
        if r['total_return'] > 0 and 
           r['max_drawdown'] < 0.5 and 
           r['total_trades'] >= 2 and
           r['sharpe_ratio'] > 0
    ]
    
    if balanced_results:
        best_balanced = max(balanced_results, key=lambda x: x['sharpe_ratio'])
        print(f"\\n🎯 RECOMMENDED BALANCED PARAMETERS:")
        params = best_balanced['parameters']
        print(f"Confidence Threshold: {params['confidence_threshold']}")
        print(f"Lookback Period: {params['lookback_period']}")
        print(f"Volatility Threshold: {params['volatility_threshold']}")
        print(f"Mean Reversion Threshold: {params['mean_reversion_threshold']}")
        print(f"Expected Performance: {best_balanced['total_return']:.2%} return, {best_balanced['max_drawdown']:.2%} drawdown, {best_balanced['total_trades']} trades")
    else:
        print("\\n⚠️ No balanced parameter combination found. Consider adjusting ranges.")

if __name__ == "__main__":
    optimize_parameters()

