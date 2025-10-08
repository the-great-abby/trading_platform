#!/usr/bin/env python3
"""
Example: Elliott Wave Service Backtesting from Kubernetes

This example shows how to use the Elliott Wave service for backtesting
when running within the Kubernetes cluster.
"""

import sys
import os
sys.path.append('src')

import asyncio
import logging
from datetime import datetime, timedelta

# Import the backtest engine
from src.backtesting.engine.backtest_engine import BacktestEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_kubernetes_elliott_wave_backtest():
    """Run backtest using Elliott Wave service from within Kubernetes"""
    
    print("🎯 KUBERNETES ELLIOTT WAVE SERVICE BACKTESTING EXAMPLE")
    print("=" * 70)
    print("📊 Configuration:")
    print(f"   💰 Initial Capital: $4,000")
    print(f"   📈 Service URL: http://elliott-wave-service.trading-system.svc.cluster.local:8000")
    print(f"   📊 Symbols: SPY, QQQ")
    print(f"   📅 Period: 2023-01-01 to 2023-12-31")
    print(f"   🛑 Features: Real Elliott Wave Service, Internal Kubernetes Address")
    print()
    
    # Create engine with real data
    engine = BacktestEngine(use_real_data=True, use_cache=True)
    engine.initial_capital = 4000.0
    
    # Use service-based strategies that call the Elliott Wave service
    # These strategies use the internal Kubernetes service address
    kubernetes_strategies = [
        'ServiceBasedElliottWaveImpulseStrategy',     # Uses real Elliott Wave service
        'ServiceBasedElliottWaveCorrectiveStrategy',  # Uses real Elliott Wave service
        'CalendarSpreadStrategy',                     # Keep existing strategies
        'VolatilityStrategy'                          # Keep existing strategies
    ]
    
    print("🚀 Running backtest with Kubernetes Elliott Wave service...")
    print("📅 Period: 1 year (2023) - shorter period for testing")
    print("📊 Strategies: Service-Based Elliott Wave + Options Strategies")
    print("🛑 Features: Real Elliott Wave Service, Internal Kubernetes Address")
    print()
    
    try:
        results = await engine.run_backtest(
            symbols=['SPY', 'QQQ'],  # Fewer symbols for testing
            start_date='2023-01-01',
            end_date='2023-12-31',
            strategies=kubernetes_strategies
        )
        
        print('✅ Backtest completed successfully!')
        print()
        
        # Display results
        total_final_capital = 0
        total_initial_capital = 0
        total_trades = 0
        total_winning_trades = 0
        
        print('📊 KUBERNETES ELLIOTT WAVE SERVICE BACKTEST RESULTS')
        print('=' * 60)
        
        for strategy_name, result in results.items():
            print(f'📈 {strategy_name}:')
            print(f'   💰 Initial Capital: ${result.initial_capital:,.2f}')
            print(f'   💰 Final Capital: ${result.final_capital:,.2f}')
            print(f'   📊 Total Return: {result.total_return_pct:.2%}')
            print(f'   ⚠️  Max Drawdown: {result.max_drawdown_pct:.2%}')
            print(f'   📊 Sharpe Ratio: {result.sharpe_ratio:.2f}')
            print(f'   🎯 Win Rate: {result.win_rate:.2%}')
            print(f'   📊 Total Trades: {result.total_trades}')
            print(f'   ✅ Winning Trades: {result.winning_trades}')
            print(f'   ❌ Losing Trades: {result.losing_trades}')
            print(f'   💰 Avg Win: ${result.avg_win:.2f}')
            print(f'   💸 Avg Loss: ${result.avg_loss:.2f}')
            print(f'   📊 Profit Factor: {result.profit_factor:.2f}')
            print()
            
            total_final_capital += result.final_capital
            total_initial_capital += result.initial_capital
            total_trades += result.total_trades
            total_winning_trades += result.winning_trades
        
        # Overall portfolio performance
        print('📊 OVERALL PORTFOLIO PERFORMANCE')
        print('=' * 40)
        overall_return = ((total_final_capital - total_initial_capital) / total_initial_capital) * 100
        overall_win_rate = (total_winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        print(f'💰 Total Initial Capital: ${total_initial_capital:,.2f}')
        print(f'💰 Total Final Capital: ${total_final_capital:,.2f}')
        print(f'📈 Overall Return: {overall_return:.2f}%')
        print(f'📈 Annualized Return: {overall_return:.2f}%')
        print(f'🎯 Overall Win Rate: {overall_win_rate:.2f}%')
        print(f'📊 Total Trades: {total_trades}')
        print()
        
        # Analysis of service-based strategies
        print('🔧 KUBERNETES ELLIOTT WAVE SERVICE ANALYSIS')
        print('=' * 60)
        
        impulse_result = results.get('ServiceBasedElliottWaveImpulseStrategy')
        corrective_result = results.get('ServiceBasedElliottWaveCorrectiveStrategy')
        
        if impulse_result:
            print(f'📈 Service-Based Elliott Wave Impulse Strategy:')
            print(f'   📊 Total Trades: {impulse_result.total_trades}')
            print(f'   🎯 Win Rate: {impulse_result.win_rate:.2%}')
            print(f'   📊 Total Return: {impulse_result.total_return_pct:.2%}')
            print(f'   ⚠️  Max Drawdown: {impulse_result.max_drawdown_pct:.2%}')
            
            if impulse_result.total_trades > 0:
                print(f'   🎉 Strategy is generating trades using real Elliott Wave service!')
                if impulse_result.win_rate > 60:
                    print(f'   ✅ Win rate is good')
                else:
                    print(f'   ⚠️  Win rate could be improved')
                
                if impulse_result.total_return_pct > 0:
                    print(f'   🎉 Strategy is profitable!')
                elif impulse_result.total_return_pct > -10:
                    print(f'   ✅ Return is acceptable - small loss')
                else:
                    print(f'   ❌ Strategy needs improvement')
            else:
                print(f'   ❌ Strategy not generating trades')
        
        if corrective_result:
            print(f'📈 Service-Based Elliott Wave Corrective Strategy:')
            print(f'   📊 Total Trades: {corrective_result.total_trades}')
            print(f'   🎯 Win Rate: {corrective_result.win_rate:.2%}')
            print(f'   📊 Total Return: {corrective_result.total_return_pct:.2%}')
            print(f'   ⚠️  Max Drawdown: {corrective_result.max_drawdown_pct:.2%}')
            
            if corrective_result.total_trades > 0:
                print(f'   🎉 Strategy is generating trades using real Elliott Wave service!')
                if corrective_result.win_rate > 60:
                    print(f'   ✅ Win rate is good')
                else:
                    print(f'   ⚠️  Win rate could be improved')
                
                if corrective_result.total_return_pct > 0:
                    print(f'   🎉 Strategy is profitable!')
                elif corrective_result.total_return_pct > -10:
                    print(f'   ✅ Return is acceptable - small loss')
                else:
                    print(f'   ❌ Strategy needs improvement')
            else:
                print(f'   ❌ Strategy not generating trades')
        
        if overall_return > 0:
            print('   🎉 Portfolio is profitable!')
        elif overall_return > -10:
            print('   ✅ Portfolio performance is acceptable - small loss')
        else:
            print('   ❌ Portfolio needs improvement')
        
        if total_trades > 0:
            print('   ✅ Strategies are generating trades using real Elliott Wave service')
        else:
            print('   ❌ Strategies not generating trades')
        
        if overall_win_rate > 60:
            print('   ✅ Win rate is good')
        else:
            print('   ⚠️  Win rate could be improved')
        
        print()
        print('🎉 Kubernetes Elliott Wave service backtesting completed!')
        
        return results
        
    except Exception as e:
        print(f'❌ Backtest failed: {e}')
        import traceback
        traceback.print_exc()
        return None

async def test_individual_service_calls():
    """Test individual service calls to demonstrate usage"""
    
    print("🔍 TESTING INDIVIDUAL ELLIOTT WAVE SERVICE CALLS")
    print("=" * 60)
    
    import requests
    
    # Internal Kubernetes service address
    service_url = "http://elliott-wave-service.trading-system.svc.cluster.local:8000"
    
    # Test backtesting endpoint
    print("📅 Testing backtesting endpoint...")
    try:
        response = requests.get(
            f"{service_url}/elliott-wave/backtest/SPY",
            params={"historical_date": "2023-06-15", "timeframe": "1d"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("pattern_found", False):
            print(f"   ✅ Pattern found: {result.get('pattern_type', 'unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"   📈 Data points: {result.get('data_points', 0)}")
            print(f"   🌊 Swing points: {result.get('swing_points', 0)}")
        else:
            print(f"   ❌ No pattern: {result.get('message', 'No pattern')}")
        
        print(f"   ⏱️  Analysis time: {result.get('analysis_time', 0):.3f}s")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test live endpoint
    print("📅 Testing live endpoint...")
    try:
        response = requests.get(
            f"{service_url}/elliott-wave/analyze/AAPL",
            params={"timeframe": "1d"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("pattern_found", False):
            print(f"   ✅ Pattern found: {result.get('pattern_type', 'unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0.0):.2f}")
        else:
            print(f"   ❌ No pattern: {result.get('message', 'No pattern')}")
        
        print(f"   ⏱️  Analysis time: {result.get('analysis_time', 0):.3f}s")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def main():
    """Main function"""
    
    print("🚀 KUBERNETES ELLIOTT WAVE SERVICE BACKTESTING EXAMPLE")
    print("=" * 70)
    print()
    
    # Test individual service calls first
    await test_individual_service_calls()
    print()
    
    # Run the full backtest
    await run_kubernetes_elliott_wave_backtest()

if __name__ == "__main__":
    asyncio.run(main())
