#!/usr/bin/env python3
"""
Enhanced Multi-Strategy Backtest
===============================
Tests the new multi-strategy approach that combines:
- AdaptiveSectorWaveStrategy for entry signals
- Multiple exit strategies to let winners run longer
- Better risk management through combined signals
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

# Disable AI services to speed up backtest
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.enhanced_multi_strategy import EnhancedMultiStrategy
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
                'approval_rate': 100.0,
                'accuracy': 100.0,
                'average_confidence': 0.8,
                'average_response_time': 0.001
            },
            'llm_performance': {
                'total_signals': 0,
                'approved_signals': 0,
                'rejected_signals': 0,
                'approval_rate': 100.0,
                'average_response_time': 0.001
            }
        }
    
    def update_performance(self, *args, **kwargs):
        """No-op performance update"""
        pass


class EnhancedBacktestEngine(BacktestEngine):
    """Enhanced backtest engine with AI services disabled"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace trade evaluator with mock to disable AI completely
        self.trade_evaluator = MockTradeEvaluator()


async def run_enhanced_multi_strategy_backtest():
    """Run backtest with enhanced multi-strategy approach"""
    
    logger.info("🚀 Starting Enhanced Multi-Strategy Backtest")
    logger.info("=" * 60)
    
    # Initialize enhanced backtest engine (AI services disabled)
    engine = EnhancedBacktestEngine(use_real_data=True, use_cache=True)
    engine.initial_capital = 4000.0  # $4,000 account
    
    # Discover strategies
    discover_strategies()
    registry = get_strategy_registry()
    
    # Define symbols to test (focused set)
    symbols = ['SPY', 'QQQ', 'AAPL']
    
    # Date range for backtest
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    logger.info(f"📊 Testing symbols: {', '.join(symbols)}")
    logger.info(f"📅 Date range: {start_date} to {end_date}")
    logger.info(f"💰 Initial capital: ${engine.initial_capital:,.2f}")
    
    # Create enhanced multi-strategy
    strategy = EnhancedMultiStrategy(
        # Entry parameters
        entry_confidence_threshold=0.5,
        
        # Exit parameters
        momentum_exit_threshold=0.02,
        volatility_exit_threshold=0.03,
        
        # Position management
        max_position_duration_days=30,
        min_profit_target=0.05,  # 5% profit target
        max_loss_stop=0.03,      # 3% stop loss
        
        # Risk management
        max_concurrent_positions=3,
        position_size_pct=0.05   # 5% of available cash per trade
    )
    
    logger.info("🎯 Strategy Configuration:")
    logger.info(f"   Entry confidence threshold: {strategy.entry_confidence_threshold}")
    logger.info(f"   Max position duration: {strategy.max_position_duration_days} days")
    logger.info(f"   Profit target: {strategy.min_profit_target:.1%}")
    logger.info(f"   Stop loss: {strategy.max_loss_stop:.1%}")
    logger.info(f"   Max concurrent positions: {strategy.max_concurrent_positions}")
    logger.info(f"   Position size: {strategy.position_size_pct:.1%}")
    
    # Run backtest
    start_time = datetime.now()
    
    try:
        results = await engine.run_backtest(
            strategies={'EnhancedMultiStrategy': strategy},
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Backtest completed in {duration:.1f} seconds")
        
        # Display results
        if results and 'EnhancedMultiStrategy' in results:
            result = results['EnhancedMultiStrategy']
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("📊 ENHANCED MULTI-STRATEGY RESULTS")
            logger.info("=" * 60)
            logger.info("")
            logger.info(f"🎯 Strategy: {result.strategy}")
            logger.info(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
            logger.info(f"💰 Final Capital: ${result.final_capital:,.2f}")
            logger.info(f"📈 Total Return: ${result.total_return:,.2f}")
            logger.info(f"📊 Total Return %: {result.total_return_pct:.2f}%")
            logger.info(f"📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
            logger.info(f"📊 Sharpe Ratio: {result.sharpe_ratio:.3f}")
            logger.info("")
            logger.info("📋 TRADE STATISTICS:")
            logger.info(f"   Total Trades: {result.total_trades}")
            logger.info(f"   Winning Trades: {result.winning_trades}")
            logger.info(f"   Losing Trades: {result.losing_trades}")
            logger.info(f"   Win Rate: {result.win_rate:.2%}")
            logger.info(f"   Profit Factor: {result.profit_factor:.3f}")
            logger.info(f"   Average Win: ${result.avg_win:.2f}")
            logger.info(f"   Average Loss: ${result.avg_loss:.2f}")
            logger.info("")
            
            # Analyze trade types
            if result.trades:
                entry_trades = [t for t in result.trades if t.action == 'BUY']
                exit_trades = [t for t in result.trades if t.action == 'SELL']
                
                logger.info("🔍 TRADE ANALYSIS:")
                logger.info(f"   Entry trades: {len(entry_trades)}")
                logger.info(f"   Exit trades: {len(exit_trades)}")
                
                # Analyze exit reasons
                exit_reasons = {}
                for trade in exit_trades:
                    if hasattr(trade, 'metadata') and trade.metadata:
                        reason = trade.metadata.get('exit_reason', 'UNKNOWN')
                        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
                
                if exit_reasons:
                    logger.info("   Exit reasons:")
                    for reason, count in exit_reasons.items():
                        logger.info(f"     {reason}: {count}")
            
            # Position summary
            position_summary = strategy.get_position_summary()
            logger.info("")
            logger.info("📊 POSITION SUMMARY:")
            logger.info(f"   Active positions: {position_summary['active_positions']}")
            logger.info(f"   Max concurrent: {position_summary['max_concurrent_positions']}")
            
        else:
            logger.error("❌ No results generated")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("")
    logger.info("🎉 Enhanced multi-strategy backtest completed!")


if __name__ == "__main__":
    asyncio.run(run_enhanced_multi_strategy_backtest())
