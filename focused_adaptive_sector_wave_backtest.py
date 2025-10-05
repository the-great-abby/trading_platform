#!/usr/bin/env python3
"""
Focused Adaptive Sector Wave Backtest

This script runs a focused backtest using:
1. Limited stock universe: INTC, AMD, PYPL, AAPL, NFLX
2. AdaptiveSectorWave strategy with Elliott Wave service integration
3. Clean, fast execution without AI services
"""

import sys
import os
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Add src to path for imports
sys.path.append('src')

# Set Polygon API key from Kubernetes secret
POLYGON_API_KEY = "PwSQb2yBh2aYqEs0lZIqnTX_nT2b7CHr"
os.environ['POLYGON_API_KEY'] = POLYGON_API_KEY

# Disable AI services to speed up backtest
os.environ['DISABLE_AI_SERVICES'] = 'true'
os.environ['DISABLE_OLLAMA'] = 'true'
os.environ['DISABLE_TRADE_EVALUATOR'] = 'true'

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.strategy_registry import get_strategy_registry, discover_strategies

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('focused_adaptive_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockTradeEvaluator:
    """Mock trade evaluator that bypasses all AI functionality"""
    
    async def evaluate_trade_signal(self, signal, market_data, strategy_name):
        """Always approve trades without AI evaluation"""
        # Return the expected dictionary structure instead of just True
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
                'approval_rate': 100.0,  # 100% approval for mock
                'accuracy': 100.0,  # Add missing accuracy field
                'average_confidence': 0.8,  # Add missing average_confidence field
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

class FocusedBacktestEngine(BacktestEngine):
    """
    Focused backtest engine for Adaptive Sector Wave strategy
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trade_details = []
        # Replace trade evaluator with mock to disable AI completely
        self.trade_evaluator = MockTradeEvaluator()
        self.strategy_performance = {}
        
    def log_trade_details(self, trade_signal, entry_reason, confidence, strategy_name):
        """Log detailed trade information"""
        trade_detail = {
            'timestamp': datetime.now().isoformat(),
            'symbol': trade_signal.symbol,
            'action': trade_signal.action,
            'quantity': trade_signal.quantity,
            'price': trade_signal.price,
            'strategy': strategy_name,
            'confidence': confidence,
            'entry_reason': entry_reason,
            'pattern_type': trade_signal.metadata.get('pattern_type', 'N/A'),
            'direction': trade_signal.metadata.get('direction', 'N/A'),
            'strategy_type': trade_signal.metadata.get('strategy_type', 'N/A'),
            'elliott_wave_service': trade_signal.metadata.get('elliott_wave_service', False),
        }
        self.trade_details.append(trade_detail)
        logger.info(f"TRADE_DETAIL: {json.dumps(trade_detail)}")

async def run_focused_backtest():
    """Run focused backtest with Adaptive Sector Wave strategy"""
    
    logger.info("🚀 FOCUSED ADAPTIVE SECTOR WAVE BACKTEST")
    logger.info("=" * 60)
    logger.info("📊 Strategy: AdaptiveSectorWave with Elliott Wave Service")
    logger.info("📈 Symbols: INTC, AMD, PYPL, AAPL, NFLX")
    logger.info("🎯 Focus: High-performing stocks with Elliott Wave patterns")
    logger.info("=" * 60)
    
    # Initialize backtest engine
    engine = FocusedBacktestEngine(use_real_data=True, use_cache=True)
    engine.initial_capital = 4000.0  # $4k account with $800 cash reserve (20%)
    
    # Discover strategies
    discover_strategies()
    registry = get_strategy_registry()
    
    # Focused symbol universe - stocks that work well with Elliott Wave strategies
    symbols = ['SPY', 'QQQ', 'AAPL']  # Using symbols currently tracked by Elliott Wave service
    
    # Strategy configuration - only Adaptive Sector Wave
    strategies = ['AdaptiveSectorWaveStrategy']
    
    logger.info(f"📊 Running backtest with:")
    logger.info(f"   💰 Initial Capital: ${engine.initial_capital:,.2f}")
    logger.info(f"   📈 Symbols: {', '.join(symbols)}")
    logger.info(f"   🎯 Strategies: {', '.join(strategies)}")
    logger.info(f"   📅 Date Range: 2023-01-01 to 2023-12-31")
    logger.info("")
    
    # Run backtest
    start_time = datetime.now()
    
    try:
        results = await engine.run_backtest(
            symbols=symbols,
            start_date='2023-01-01',
            end_date='2023-12-31',
            strategies=strategies
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Backtest completed in {duration:.1f} seconds")
        
        # Analyze results
        logger.info("\n" + "=" * 60)
        logger.info("📊 FOCUSED BACKTEST RESULTS")
        logger.info("=" * 60)
        
        # Portfolio summary
        if 'PortfolioStrategy' in results:
            portfolio = results['PortfolioStrategy']
            logger.info(f"💰 Portfolio Performance:")
            logger.info(f"   📈 Total Return: {portfolio.get('total_return', 0):.2%}")
            logger.info(f"   📊 Sharpe Ratio: {portfolio.get('sharpe_ratio', 0):.3f}")
            logger.info(f"   📉 Max Drawdown: {portfolio.get('max_drawdown', 0):.2%}")
            logger.info(f"   🎯 Win Rate: {portfolio.get('win_rate', 0):.2%}")
            logger.info(f"   💵 Final Value: ${portfolio.get('final_value', 0):,.2f}")
            logger.info(f"   📊 Total Trades: {portfolio.get('total_trades', 0)}")
            logger.info(f"   ✅ Winning Trades: {portfolio.get('winning_trades', 0)}")
            logger.info(f"   ❌ Losing Trades: {portfolio.get('losing_trades', 0)}")
            logger.info(f"   💰 Profit Factor: {portfolio.get('profit_factor', 0):.3f}")
        
        # Individual strategy results
        for strategy_name, result in results.items():
            if strategy_name == 'PortfolioStrategy':
                continue
                
            logger.info(f"\n🎯 {strategy_name} Performance:")
            logger.info(f"   📈 Total Return: {result.total_return:.2%}")
            logger.info(f"   📊 Sharpe Ratio: {result.sharpe_ratio:.3f}")
            logger.info(f"   📉 Max Drawdown: {result.max_drawdown:.2%}")
            logger.info(f"   🎯 Win Rate: {result.win_rate:.2%}")
            logger.info(f"   📊 Total Trades: {result.total_trades}")
            logger.info(f"   💵 Final Value: ${result.final_capital:,.2f}")
        
        # Trade details analysis
        logger.info(f"\n📋 TRADE DETAILS ANALYSIS:")
        logger.info(f"   📊 Total Trades Logged: {len(engine.trade_details)}")
        
        if engine.trade_details:
            # Pattern type analysis
            pattern_types = {}
            strategy_types = {}
            symbols_traded = {}
            
            for trade in engine.trade_details:
                pattern = trade.get('pattern_type', 'unknown')
                strategy_type = trade.get('strategy_type', 'unknown')
                symbol = trade.get('symbol', 'unknown')
                
                pattern_types[pattern] = pattern_types.get(pattern, 0) + 1
                strategy_types[strategy_type] = strategy_types.get(strategy_type, 0) + 1
                symbols_traded[symbol] = symbols_traded.get(symbol, 0) + 1
            
            logger.info(f"   🎯 Pattern Types:")
            for pattern, count in pattern_types.items():
                logger.info(f"      📊 {pattern}: {count} trades")
            
            logger.info(f"   🎯 Strategy Types:")
            for strategy_type, count in strategy_types.items():
                logger.info(f"      📊 {strategy_type}: {count} trades")
            
            logger.info(f"   📈 Symbols Traded:")
            for symbol, count in symbols_traded.items():
                logger.info(f"      📊 {symbol}: {count} trades")
            
            # Save detailed trade log
            with open('focused_adaptive_trades.json', 'w') as f:
                json.dump(engine.trade_details, f, indent=2)
            logger.info(f"   💾 Detailed trades saved to: focused_adaptive_trades.json")
        
        logger.info(f"\n🎉 Focused backtest completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(run_focused_backtest())
