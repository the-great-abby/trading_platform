"""
Contract Test: BacktestResult Attribute Consistency
=================================================
Tests that BacktestResult objects have consistent attribute naming.
This test will FAIL until T011 is implemented.
"""

import pytest
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

def test_backtest_result_attributes_exist():
    """Test that BacktestResult has all required attributes"""
    
    try:
        from src.backtesting.engine.backtest_engine import BacktestResult
    except ImportError:
        pytest.skip("BacktestResult not yet implemented")
    
    # Create a sample BacktestResult
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=1000.0,
        final_capital=1100.0,
        total_return=100.0,
        total_return_pct=0.1,
        max_drawdown_pct=0.05,  # This should be the correct attribute name
        sharpe_ratio=1.5,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=0.6,
        profit_factor=1.2,
        avg_win=20.0,
        avg_loss=10.0
    )
    
    # Test that all attributes exist and are accessible
    assert hasattr(result, 'strategy')
    assert hasattr(result, 'initial_capital')
    assert hasattr(result, 'final_capital')
    assert hasattr(result, 'total_return')
    assert hasattr(result, 'total_return_pct')
    assert hasattr(result, 'max_drawdown_pct')  # This is the correct attribute name
    assert hasattr(result, 'sharpe_ratio')
    assert hasattr(result, 'total_trades')
    assert hasattr(result, 'winning_trades')
    assert hasattr(result, 'losing_trades')
    assert hasattr(result, 'win_rate')
    assert hasattr(result, 'profit_factor')
    assert hasattr(result, 'avg_win')
    assert hasattr(result, 'avg_loss')

def test_backtest_result_attribute_consistency():
    """Test that scripts can access max_drawdown attribute consistently"""
    
    try:
        from src.backtesting.engine.backtest_engine import BacktestResult
    except ImportError:
        pytest.skip("BacktestResult not yet implemented")
    
    # Create a sample BacktestResult
    result = BacktestResult(
        strategy="TestStrategy",
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
        avg_loss=10.0
    )
    
    # Test that max_drawdown_pct is accessible (this should work)
    assert result.max_drawdown_pct == 0.05
    
    # Test that max_drawdown is also accessible (for backward compatibility)
    # This will FAIL until we implement the fix
    assert hasattr(result, 'max_drawdown')
    assert result.max_drawdown == 0.05  # Should be an alias to max_drawdown_pct

def test_backtest_result_type_consistency():
    """Test that BacktestResult attributes have correct types"""
    
    try:
        from src.backtesting.engine.backtest_engine import BacktestResult
    except ImportError:
        pytest.skip("BacktestResult not yet implemented")
    
    result = BacktestResult(
        strategy="TestStrategy",
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
        avg_loss=10.0
    )
    
    # Test attribute types
    assert isinstance(result.strategy, str)
    assert isinstance(result.initial_capital, float)
    assert isinstance(result.final_capital, float)
    assert isinstance(result.total_return, float)
    assert isinstance(result.total_return_pct, float)
    assert isinstance(result.max_drawdown_pct, float)
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.total_trades, int)
    assert isinstance(result.winning_trades, int)
    assert isinstance(result.losing_trades, int)
    assert isinstance(result.win_rate, float)
    assert isinstance(result.profit_factor, float)
    assert isinstance(result.avg_win, float)
    assert isinstance(result.avg_loss, float)

if __name__ == "__main__":
    pytest.main([__file__])


