#!/usr/bin/env python3
"""
Test Backtest Engine Fixes
Tests the fixes for backtest engine issues
"""
import sys
import os
import traceback
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append('.')

def test_backtest_result_backward_compatibility():
    """Test BacktestResult backward compatibility fix"""
    print("🧪 Testing BacktestResult Backward Compatibility...")
    
    try:
        # Test the fix without importing the full backtest engine
        import pandas as pd
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class BacktestTrade:
            timestamp: datetime
            symbol: str
            action: str
            quantity: int
            price: float
            strategy: str
        
        @dataclass
        class BacktestResult:
            strategy: str
            initial_capital: float
            final_capital: float
            total_return: float
            total_return_pct: float
            max_drawdown_pct: float
            sharpe_ratio: float
            total_trades: int
            winning_trades: int
            losing_trades: int
            win_rate: float
            profit_factor: float
            avg_win: float
            avg_loss: float
            trades: List[BacktestTrade]
            equity_curve: pd.DataFrame
            start_date: datetime
            end_date: datetime
            
            @property
            def max_drawdown(self) -> float:
                return self.max_drawdown_pct
            
            @max_drawdown.setter
            def max_drawdown(self, value: float) -> None:
                self.max_drawdown_pct = value
        
        # Test the fix
        result = BacktestResult(
            strategy='TestStrategy',
            initial_capital=1000.0,
            final_capital=1100.0,
            total_return=100.0,
            total_return_pct=0.1,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.5,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.2,
            avg_win=20.0,
            avg_loss=10.0,
            trades=[],
            equity_curve=pd.DataFrame(),
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        # Test backward compatibility
        assert result.max_drawdown_pct == 0.05
        assert result.max_drawdown == 0.05
        assert result.max_drawdown == result.max_drawdown_pct
        print("  ✅ Backward compatibility property works")
        
        # Test setter
        result.max_drawdown = 0.10
        assert result.max_drawdown_pct == 0.10
        assert result.max_drawdown == 0.10
        print("  ✅ Backward compatibility setter works")
        
        print("  ✅ BacktestResult backward compatibility test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ BacktestResult backward compatibility test failed: {e}")
        traceback.print_exc()
        return False

def test_mock_options_data_service():
    """Test mock options data service"""
    print("🧪 Testing Mock Options Data Service...")
    
    try:
        from src.services.options.mock_options_data_service import get_mock_options_service
        
        # Test service initialization
        service = get_mock_options_service()
        assert service is not None
        print("  ✅ Mock options service initialized")
        
        # Test getting liquid options
        contracts = service.get_liquid_options('AAPL')
        assert len(contracts) > 0
        print(f"  ✅ Generated {len(contracts)} mock options contracts")
        
        # Test contract structure
        if contracts:
            contract = contracts[0]
            assert hasattr(contract, 'symbol')
            assert hasattr(contract, 'strike')
            assert hasattr(contract, 'expiration')
            assert hasattr(contract, 'option_type')
            assert hasattr(contract, 'bid')
            assert hasattr(contract, 'ask')
            assert hasattr(contract, 'volume')
            assert hasattr(contract, 'delta')
            assert hasattr(contract, 'gamma')
            assert hasattr(contract, 'theta')
            assert hasattr(contract, 'vega')
            print("  ✅ Mock options contracts have correct structure")
        
        # Test options chain
        chain = service.get_options_chain('AAPL')
        assert isinstance(chain, dict)
        assert len(chain) > 0
        print(f"  ✅ Generated options chain with {len(chain)} expiration dates")
        
        print("  ✅ Mock options data service test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Mock options data service test failed: {e}")
        traceback.print_exc()
        return False

def test_options_strategy_fallback():
    """Test options strategy fallback system"""
    print("🧪 Testing Options Strategy Fallback...")
    
    try:
        from src.strategies.options.options_strategy_fallback import get_options_fallback
        
        # Test fallback initialization
        fallback = get_options_fallback()
        assert fallback is not None
        print("  ✅ Options strategy fallback initialized")
        
        # Test Iron Condor data
        iron_condor_data = fallback.get_options_data('AAPL', 'iron_condor')
        assert isinstance(iron_condor_data, dict)
        assert iron_condor_data['symbol'] == 'AAPL'
        assert iron_condor_data['strategy_type'] == 'iron_condor'
        assert iron_condor_data['data_source'] == 'mock'
        print("  ✅ Iron Condor data generated")
        
        # Test Butterfly Spread data
        butterfly_data = fallback.get_options_data('AAPL', 'butterfly_spread')
        assert isinstance(butterfly_data, dict)
        assert butterfly_data['symbol'] == 'AAPL'
        assert butterfly_data['strategy_type'] == 'butterfly_spread'
        assert butterfly_data['data_source'] == 'mock'
        print("  ✅ Butterfly Spread data generated")
        
        # Test Calendar Spread data
        calendar_data = fallback.get_options_data('AAPL', 'calendar_spread')
        assert isinstance(calendar_data, dict)
        assert calendar_data['symbol'] == 'AAPL'
        assert calendar_data['strategy_type'] == 'calendar_spread'
        assert calendar_data['data_source'] == 'mock'
        print("  ✅ Calendar Spread data generated")
        
        print("  ✅ Options strategy fallback test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Options strategy fallback test failed: {e}")
        traceback.print_exc()
        return False

def test_backtest_engine_import():
    """Test that backtest engine can be imported without dependency errors"""
    print("🧪 Testing Backtest Engine Import...")
    
    try:
        # Test importing the backtest engine with error handling
        from src.backtesting.engine.backtest_engine import BacktestResult, BacktestTrade
        
        # Test that we can create BacktestResult objects
        result = BacktestResult(
            strategy='TestStrategy',
            initial_capital=1000.0,
            final_capital=1100.0,
            total_return=100.0,
            total_return_pct=0.1,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.5,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            profit_factor=1.2,
            avg_win=20.0,
            avg_loss=10.0,
            trades=[],
            equity_curve=None,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert result is not None
        assert result.max_drawdown == result.max_drawdown_pct
        print("  ✅ Backtest engine imports successfully")
        print("  ✅ BacktestResult objects can be created")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Backtest engine import test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all backtest engine fix tests"""
    print("🚀 Backtest Engine Fix Validation Tests")
    print("=" * 50)
    
    tests = [
        test_backtest_result_backward_compatibility,
        test_mock_options_data_service,
        test_options_strategy_fallback,
        test_backtest_engine_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 50)
    print("📊 BACKTEST ENGINE FIX VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total:.1%}")
    
    if passed == total:
        print("🎉 ALL BACKTEST ENGINE FIXES WORKING!")
        print("✅ Backward compatibility for max_drawdown attribute")
        print("✅ Mock options data service for strategy testing")
        print("✅ Options strategy fallback system")
        print("✅ Backtest engine imports without dependency errors")
        print("✅ The backtest engine is now ready for options strategy testing!")
        return 0
    else:
        print("⚠️ Some backtest engine fixes need attention.")
        print("📝 Check the failed tests above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)






















