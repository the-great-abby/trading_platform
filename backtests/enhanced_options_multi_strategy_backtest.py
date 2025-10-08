#!/usr/bin/env python3
"""
Enhanced Options-Enabled Multi-Strategy Backtest
===============================================
Tests the new multi-strategy approach that includes:

1. Multiple Entry Strategies:
   - AdaptiveSectorWaveStrategy (Elliott Wave-based)
   - IchimokuStrategy (high-performing: 51.8% return)
   - OptionsWheelStrategy (income generation)

2. Options Trading Capabilities:
   - Iron Condor (income generation)
   - Cash Secured Puts (stock acquisition + income)
   - Covered Calls (income on owned stocks)

3. Dynamic Asset Allocation:
   - 60% stocks, 30% options, 10% cash reserve
   - Market condition-based allocation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set Polygon API key from Kubernetes secret
POLYGON_API_KEY = "PwSQb2yBh2aYqEs0lZIqnTX_nT2b7CHr"
os.environ['POLYGON_API_KEY'] = POLYGON_API_KEY

# Set required database URL for market data manager (use same as focused backtest)
os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5432/trading_db'
os.environ['DATABASE_ONLY'] = 'false'  # Allow API fallback

# Disable AI services to speed up backtest
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.enhanced_options_multi_strategy import EnhancedOptionsMultiStrategy
from src.strategies.strategy_registry import discover_strategies, get_strategy_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockTradeEvaluator:
    """Mock trade evaluator that bypasses all AI functionality"""
    
    async def evaluate_trade_signal(self, signal, market_data, strategy_name):
        """Always approve trades without AI evaluation"""
        return {
            'approved': True,
            'confidence': 0.8,  # High confidence for mock
            'reasoning': 'AI services disabled - auto-approved',
            'risk_score': 0.3,  # Low risk score
            'evaluation_time': 0.001  # Very fast mock evaluation
        }
    
    def get_performance_report(self):
        """Return proper performance report structure"""
        return {
            'evaluations_summary': {
                'total_signals': 0,
                'approved_signals': 0,
                'rejected_signals': 0,
                'avg_confidence': 0.8,
                'avg_risk_score': 0.3
            },
            'performance_metrics': {
                'total_evaluation_time': 0.001,
                'avg_evaluation_time': 0.001,
                'evaluation_success_rate': 1.0
            }
        }


class EnhancedOptionsBacktestEngine(BacktestEngine):
    """Enhanced backtest engine with options trading capabilities"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trade_evaluator = MockTradeEvaluator()
        self.trade_details = []
    
    def log_trade_details(self, symbol: str, action: str, price: float, quantity: float, 
                        pnl: float = 0.0, reason: str = "", strategy: str = ""):
        """Log detailed trade information"""
        trade_detail = {
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'pnl': pnl,
            'reason': reason,
            'strategy': strategy,
            'timestamp': datetime.now()
        }
        self.trade_details.append(trade_detail)
        
        logger.info(f"📝 TRADE: {symbol} {action} {quantity:.3f} @ ${price:.2f} | P&L: ${pnl:.2f} | {reason}")


async def run_enhanced_options_multi_strategy_backtest():
    """Run the enhanced options-enabled multi-strategy backtest"""
    
    logger.info("🚀 Starting Enhanced Options Multi-Strategy Backtest")
    logger.info("=" * 60)
    
    # Initialize enhanced backtest engine (AI services disabled)
    engine = EnhancedOptionsBacktestEngine(use_real_data=True, use_cache=True)
    engine.initial_capital = 4000.0  # $4,000 account
    
    # Initialize enhanced options multi-strategy
    strategy = EnhancedOptionsMultiStrategy(
        enable_elliott_wave=True,  # Elliott Wave for entry signals
        enable_ichimoku=True,      # High-performing: 51.8% return
        enable_options_wheel=True,  # Enable options wheel for income generation
        stock_allocation_pct=0.30,  # 30% stocks
        options_allocation_pct=0.50,  # 50% options
        cash_reserve_pct=0.20,  # 20% cash reserve
        max_position_size_pct=0.15,  # 15% max per position
        profit_target_pct=0.08,  # 8% profit target
        stop_loss_pct=0.04,  # 4% stop loss
        max_concurrent_positions=5
    )
    
    # Define symbols to test (expanded set)
    symbols = ['SPY', 'QQQ', 'AAPL', 'AMD', 'INTC', 'PYPL', 'NFLX', 'NVDA', 'META', 'GOOG']
    
    # Date range for backtest (2024 for better options data coverage)
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    logger.info(f"📊 Testing symbols: {', '.join(symbols)}")
    logger.info(f"📅 Date range: {start_date} to {end_date}")
    logger.info(f"💰 Initial capital: ${engine.initial_capital:,.2f}")
    logger.info(f"🎯 Asset allocation: 30% stocks, 50% options, 20% cash")
    logger.info(f"📈 Strategies: Elliott Wave + Ichimoku + Options Wheel")
    
    # Run backtest
    start_time = datetime.now()
    
    try:
        results = await engine.run_backtest(
            strategies={'EnhancedOptionsMultiStrategy': strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("🎉 ENHANCED OPTIONS MULTI-STRATEGY BACKTEST COMPLETE!")
        logger.info("=" * 60)
        
        # Display results
        if results and 'EnhancedOptionsMultiStrategy' in results:
            result = results['EnhancedOptionsMultiStrategy']
            
            logger.info(f"📊 STRATEGY: {result.strategy}")
            logger.info(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
            logger.info(f"💰 Final Capital: ${result.final_capital:,.2f}")
            logger.info(f"📈 Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
            logger.info(f"📊 Total Trades: {result.total_trades}")
            logger.info(f"🎯 Win Rate: {result.win_rate:.2%}")
            logger.info(f"📈 Profit Factor: {result.profit_factor:.3f}")
            logger.info(f"📉 Max Drawdown: {result.max_drawdown:.2%}")
            logger.info(f"⏱️ Execution Time: {duration.total_seconds():.1f} seconds")
            
            # Display trade details
            if hasattr(engine, 'trade_details') and engine.trade_details:
                logger.info(f"📝 Trade Details: {len(engine.trade_details)} trades logged")
                
                # Show sample trades
                logger.info("🔍 Sample Trades:")
                for i, trade in enumerate(engine.trade_details[:10]):  # Show first 10 trades
                    logger.info(f"  {i+1}. {trade['symbol']} {trade['action']} {trade['quantity']:.3f} @ ${trade['price']:.2f} | P&L: ${trade['pnl']:.2f} | {trade['reason']}")
                
                if len(engine.trade_details) > 10:
                    logger.info(f"  ... and {len(engine.trade_details) - 10} more trades")
            
            # Strategy performance breakdown
            logger.info("📊 Strategy Performance Breakdown:")
            for strategy_name, perf in strategy.strategy_performance.items():
                if perf['trades'] > 0:
                    win_rate = perf['wins'] / perf['trades']
                    avg_return = perf['total_return'] / perf['trades']
                    logger.info(f"  {strategy_name}: {perf['trades']} trades, {win_rate:.1%} win rate, ${avg_return:.2f} avg return")
            
            # Compare with previous results
            logger.info("🔄 Comparison with Previous Results:")
            logger.info("  Previous (Stocks Only): -4.37% return, 39.6% win rate")
            logger.info(f"  Current (Stocks + Options): {result.total_return_pct:.2f}% return, {result.win_rate:.1%} win rate")
            
            improvement = result.total_return_pct - (-4.37)
            logger.info(f"  Improvement: {improvement:+.2f} percentage points")
            
        else:
            logger.error("❌ No results generated")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_enhanced_options_multi_strategy_backtest())
