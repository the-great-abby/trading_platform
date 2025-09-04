#!/usr/bin/env python3
"""
Test Database Storage - Verify backtest results storage is working
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.database.backtest_results_service import BacktestResultsService
from utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()


async def test_database_storage():
    """Test database storage functionality"""
    
    print("🧪 TESTING DATABASE STORAGE")
    print("=" * 50)
    
    try:
        # Initialize service
        service = BacktestResultsService()
        print("✅ BacktestResultsService initialized")
        
        # Test storing a sample backtest result
        test_run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_result = {
            'initial_capital': 100000.0,
            'final_capital': 105000.0,
            'total_return': 5000.0,
            'total_return_pct': 5.0,
            'max_drawdown_pct': -2.5,
            'sharpe_ratio': 1.2,
            'total_trades': 10,
            'winning_trades': 6,
            'losing_trades': 4,
            'win_rate': 0.6,
            'profit_factor': 1.5,
            'avg_win': 1000.0,
            'avg_loss': -500.0,
            'trades': [
                {
                    'timestamp': datetime.now(),
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'quantity': 100,
                    'price': 150.0,
                    'pnl': 500.0,
                    'confidence': 0.8,
                    'portfolio_value': 100000.0,
                    'cash': 85000.0,
                    'position_value': 15000.0,
                    'total_pnl': 500.0,
                    'trade_pnl': 500.0
                }
            ],
            'equity_curve': None
        }
        
        # Store the test result
        success = service.store_backtest_results(
            run_id=test_run_id,
            strategy_name="TestStrategy",
            symbols=["AAPL", "MSFT"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            result=test_result,
            database_only=False,
            data_provider="test"
        )
        
        if success:
            print(f"✅ Successfully stored test backtest result (run_id: {test_run_id})")
        else:
            print(f"❌ Failed to store test backtest result")
            return
        
        # Retrieve the stored result
        runs = service.get_backtest_runs(strategy_name="TestStrategy", limit=5)
        print(f"✅ Retrieved {len(runs)} backtest runs")
        
        if runs:
            latest_run = runs[0]
            print(f"📊 Latest run: {latest_run['run_id']}")
            print(f"   Strategy: {latest_run['strategy_name']}")
            print(f"   Return: {latest_run['total_return_pct']:.2f}%")
            print(f"   Trades: {latest_run['total_trades']}")
            print(f"   Win Rate: {latest_run['win_rate']:.2f}%")
        
        # Test retrieving trades
        trades = service.get_backtest_trades(test_run_id)
        print(f"✅ Retrieved {len(trades)} trades for test run")
        
        if trades:
            trade = trades[0]
            print(f"📈 Sample trade: {trade['symbol']} {trade['action']} {trade['quantity']} @ ${trade['price']:.2f}")
        
        print("\n🎉 Database storage test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database storage test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_database_storage()) 