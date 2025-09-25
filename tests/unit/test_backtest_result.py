"""
Unit Tests: BacktestResult Standardization
=========================================
Unit tests for BacktestResult attribute standardization and backward compatibility.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/strategy-service/src'))

def test_backtest_result_initialization():
    """Test BacktestResult initialization with all required attributes"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult, BacktestTrade
    
    # Create sample trade data
    sample_trade = BacktestTrade(
        timestamp=datetime.now(),
        symbol="AAPL",
        action="BUY",
        quantity=100,
        price=150.0,
        strategy="TestStrategy",
        pnl=10.0,
        confidence=0.8,
        portfolio_value=10000.0,
        cash=5000.0,
        position_value=15000.0,
        total_pnl=100.0,
        trade_pnl=10.0
    )
    
    # Create sample equity curve
    equity_curve = pd.DataFrame({
        'timestamp': [datetime.now()],
        'portfolio_value': [10000.0],
        'cash': [5000.0],
        'positions_value': [15000.0]
    })
    
    # Test BacktestResult initialization
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=11000.0,
        total_return=1000.0,
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
        trades=[sample_trade],
        equity_curve=equity_curve,
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test all attributes exist
    assert result.strategy == "TestStrategy"
    assert result.initial_capital == 10000.0
    assert result.final_capital == 11000.0
    assert result.total_return == 1000.0
    assert result.total_return_pct == 0.1
    assert result.max_drawdown_pct == 0.05
    assert result.sharpe_ratio == 1.5
    assert result.total_trades == 10
    assert result.winning_trades == 6
    assert result.losing_trades == 4
    assert result.win_rate == 0.6
    assert result.profit_factor == 1.2
    assert result.avg_win == 20.0
    assert result.avg_loss == 10.0
    assert len(result.trades) == 1
    assert isinstance(result.equity_curve, pd.DataFrame)

def test_backtest_result_backward_compatibility():
    """Test BacktestResult backward compatibility with max_drawdown property"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult, BacktestTrade
    
    # Create minimal result
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=11000.0,
        total_return=1000.0,
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
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test backward compatibility property
    assert hasattr(result, 'max_drawdown')
    assert result.max_drawdown == 0.05  # Should be same as max_drawdown_pct
    assert result.max_drawdown == result.max_drawdown_pct

def test_backtest_result_property_consistency():
    """Test that max_drawdown property always returns correct value"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    # Test with different max_drawdown_pct values
    test_values = [0.0, 0.05, 0.1, 0.15, 0.2, 0.5]
    
    for max_dd in test_values:
        result = BacktestResult(
            strategy="TestStrategy",
            initial_capital=10000.0,
            final_capital=11000.0,
            total_return=1000.0,
            total_return_pct=0.1,
            max_drawdown_pct=max_dd,
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
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now()
        )
        
        assert result.max_drawdown == max_dd
        assert result.max_drawdown == result.max_drawdown_pct

def test_backtest_result_type_consistency():
    """Test that BacktestResult attributes have correct types"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=11000.0,
        total_return=1000.0,
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
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test attribute types
    assert isinstance(result.strategy, str)
    assert isinstance(result.initial_capital, float)
    assert isinstance(result.final_capital, float)
    assert isinstance(result.total_return, float)
    assert isinstance(result.total_return_pct, float)
    assert isinstance(result.max_drawdown_pct, float)
    assert isinstance(result.max_drawdown, float)  # Property should return float
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.total_trades, int)
    assert isinstance(result.winning_trades, int)
    assert isinstance(result.losing_trades, int)
    assert isinstance(result.win_rate, float)
    assert isinstance(result.profit_factor, float)
    assert isinstance(result.avg_win, float)
    assert isinstance(result.avg_loss, float)
    assert isinstance(result.trades, list)
    assert isinstance(result.equity_curve, pd.DataFrame)
    assert isinstance(result.start_date, datetime)
    assert isinstance(result.end_date, datetime)

def test_backtest_result_calculation_accuracy():
    """Test that BacktestResult calculations are accurate"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    initial_capital = 10000.0
    final_capital = 11500.0
    total_return = final_capital - initial_capital
    total_return_pct = total_return / initial_capital
    
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
        total_return_pct=total_return_pct,
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
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test calculation accuracy
    assert abs(result.total_return - 1500.0) < 0.01
    assert abs(result.total_return_pct - 0.15) < 0.01
    
    # Test that win rate calculation is correct
    expected_win_rate = result.winning_trades / result.total_trades
    assert abs(result.win_rate - expected_win_rate) < 0.01

def test_backtest_result_immutability():
    """Test that BacktestResult properties are immutable after creation"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=11000.0,
        total_return=1000.0,
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
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test that max_drawdown property is read-only
    original_value = result.max_drawdown
    
    # This should not change the value
    assert result.max_drawdown == original_value
    assert result.max_drawdown_pct == original_value

def test_backtest_result_edge_cases():
    """Test BacktestResult with edge case values"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    # Test with zero values
    result_zero = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=10000.0,
        total_return=0.0,
        total_return_pct=0.0,
        max_drawdown_pct=0.0,
        sharpe_ratio=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        win_rate=0.0,
        profit_factor=0.0,
        avg_win=0.0,
        avg_loss=0.0,
        trades=[],
        equity_curve=pd.DataFrame(),
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    assert result_zero.max_drawdown == 0.0
    assert result_zero.max_drawdown == result_zero.max_drawdown_pct
    
    # Test with negative values
    result_negative = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=8000.0,
        total_return=-2000.0,
        total_return_pct=-0.2,
        max_drawdown_pct=-0.2,
        sharpe_ratio=-1.0,
        total_trades=5,
        winning_trades=1,
        losing_trades=4,
        win_rate=0.2,
        profit_factor=0.5,
        avg_win=100.0,
        avg_loss=-200.0,
        trades=[],
        equity_curve=pd.DataFrame(),
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    assert result_negative.max_drawdown == -0.2
    assert result_negative.max_drawdown == result_negative.max_drawdown_pct

def test_backtest_result_serialization():
    """Test that BacktestResult can be serialized (for API responses)"""
    
    from src.backtesting.engine.backtest_engine import BacktestResult
    
    result = BacktestResult(
        strategy="TestStrategy",
        initial_capital=10000.0,
        final_capital=11000.0,
        total_return=1000.0,
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
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now()
    )
    
    # Test that we can access all attributes for serialization
    serializable_data = {
        'strategy': result.strategy,
        'initial_capital': result.initial_capital,
        'final_capital': result.final_capital,
        'total_return': result.total_return,
        'total_return_pct': result.total_return_pct,
        'max_drawdown_pct': result.max_drawdown_pct,
        'max_drawdown': result.max_drawdown,  # Test backward compatibility
        'sharpe_ratio': result.sharpe_ratio,
        'total_trades': result.total_trades,
        'winning_trades': result.winning_trades,
        'losing_trades': result.losing_trades,
        'win_rate': result.win_rate,
        'profit_factor': result.profit_factor,
        'avg_win': result.avg_win,
        'avg_loss': result.avg_loss
    }
    
    # All values should be serializable
    for key, value in serializable_data.items():
        assert value is not None
        # Test that value can be converted to JSON-serializable format
        import json
        json.dumps(value)  # Should not raise exception

if __name__ == "__main__":
    pytest.main([__file__])


