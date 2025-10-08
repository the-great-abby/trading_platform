#!/usr/bin/env python3
"""
Simple Comprehensive 2-Year Backtest with Detailed Trade Analysis
================================================================

This script runs a comprehensive backtest with detailed trade-by-trade analysis
using strategies that work locally without requiring Kubernetes services.

Uses Polygon API for reliable market data access.
Capital Allocation: 20% cash, 30% stocks, 50% options
Strategies: Market Regime, Ichimoku, Trailing Stop, Basic Options
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
from src.utils.trading_config import SYMBOLS, OPTIONS_SYMBOLS

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_comprehensive_backtest.log'),
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

class DetailedBacktestEngine(BacktestEngine):
    """
    Extended backtest engine with detailed trade logging and analysis
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
            'entry_reason': entry_reason,
            'confidence': confidence,
            'metadata': trade_signal.metadata if hasattr(trade_signal, 'metadata') else {}
        }
        self.trade_details.append(trade_detail)
        
        logger.info(f"📊 TRADE DETAIL: {trade_signal.action} {trade_signal.quantity} {trade_signal.symbol} @ ${trade_signal.price:.2f}")
        logger.info(f"   🎯 Strategy: {strategy_name}")
        logger.info(f"   📈 Reason: {entry_reason}")
        logger.info(f"   🎯 Confidence: {confidence:.2f}")
        logger.info("   " + "─" * 60)

async def run_simple_comprehensive_backtest():
    """Run a simple comprehensive backtest with detailed analysis"""
    
    logger.info("🚀 STARTING SIMPLE COMPREHENSIVE 2-YEAR BACKTEST WITH DETAILED ANALYSIS")
    logger.info("=" * 80)
    
    # Configuration
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    initial_capital = 100000  # $100k
    symbols = [
        # Core symbols for faster execution
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        'SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLV'
    ]
    
    # Strategy configuration - using strategies that work locally
    strategies_config = {
        # Core Strategies that work without external services
        'IchimokuStrategy': {
            'tenkan_period': 9,
            'kijun_period': 26,
            'senkou_b_period': 52,
            'displacement': 26,
            'min_confidence': 0.7
        },
        'RSIStrategy': {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'min_confidence': 0.6
        },
        'MACDStrategy': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'min_confidence': 0.6
        },
        'BollingerBandsStrategy': {
            'period': 20,
            'std_dev': 2,
            'min_confidence': 0.6
        },
        'SMACrossoverStrategy': {
            'short_period': 10,
            'long_period': 30,
            'min_confidence': 0.6
        },
        'TrailingStopStrategy': {
            'trailing_stop_pct': 0.05,
            'min_profit_pct': 0.02,
            'max_position_size': 0.15
        }
    }
    
    # Capital allocation
    capital_allocation = {
        'total_capital': initial_capital,
        'cash_reserve_pct': 0.20,  # 20% cash ($20k)
        'stock_allocation_pct': 0.30,  # 30% stocks ($30k)
        'options_allocation_pct': 0.50,  # 50% options ($50k)
        'max_position_size': 0.15,  # Max 15% per position
        'max_daily_risk': 0.02,  # Max 2% daily risk
        'max_drawdown': 0.10,  # Max 10% drawdown
    }
    
    logger.info(f"📅 Date Range: {start_date} to {end_date}")
    logger.info(f"💰 Initial Capital: ${initial_capital:,}")
    logger.info(f"📊 Capital Allocation: 20% cash, 30% stocks, 50% options")
    logger.info(f"🎯 Strategies: {len(strategies_config)}")
    logger.info(f"📈 Symbols: {len(symbols)}")
    logger.info(f"🔑 Using Polygon API for market data")
    logger.info("=" * 80)
    
    # Initialize detailed backtest engine
    engine = DetailedBacktestEngine(
        use_real_data=True,
        use_cache=False
    )
    engine.initial_capital = initial_capital
    
    # Discover and register strategies
    logger.info("🔍 Discovering strategies...")
    discover_strategies()
    registry = get_strategy_registry()
    
    logger.info(f"✅ Discovered {len(registry.get_all_strategies())} strategies")
    
    # Run backtest with detailed logging
    logger.info("🚀 Starting detailed backtest execution...")
    logger.info("=" * 80)
    
    try:
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategies=list(strategies_config.keys())
        )
        
        logger.info("=" * 80)
        logger.info("📊 COMPREHENSIVE BACKTEST RESULTS")
        logger.info("=" * 80)
        
        # Detailed results analysis
        total_trades = 0
        total_pnl = 0
        
        for strategy_name, result in results.items():
            trades = result.get('total_trades', 0)
            pnl = result.get('total_pnl', 0)
            total_trades += trades
            total_pnl += pnl
            
            logger.info(f"\n🎯 {strategy_name}")
            logger.info(f"   📊 Total Return: {result.get('total_return', 0):.2%}")
            logger.info(f"   📈 Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
            logger.info(f"   📉 Max Drawdown: {result.get('max_drawdown', 0):.2%}")
            logger.info(f"   🎯 Win Rate: {result.get('win_rate', 0):.2%}")
            logger.info(f"   📊 Total Trades: {trades}")
            logger.info(f"   💰 Final Value: ${result.get('final_value', 0):,.2f}")
            logger.info(f"   💵 Total P&L: ${pnl:,.2f}")
            
            # Show some trade examples if available
            if hasattr(result, 'trades') and len(result.trades) > 0:
                logger.info(f"   📋 Sample Trades:")
                for i, trade in enumerate(result.trades[:3]):  # Show first 3 trades
                    logger.info(f"      {i+1}. {trade.action} {trade.symbol} @ ${trade.price:.2f} (P&L: ${trade.pnl:.2f})")
        
        # Summary
        logger.info(f"\n📊 OVERALL SUMMARY:")
        logger.info(f"   🎯 Total Strategies: {len(results)}")
        logger.info(f"   📊 Total Trades: {total_trades}")
        logger.info(f"   💰 Combined P&L: ${total_pnl:,.2f}")
        
        # Save detailed results
        detailed_results = {
            'summary': results,
            'trade_details': engine.trade_details,
            'config': {
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'symbols': symbols,
                'strategies': strategies_config,
                'capital_allocation': capital_allocation
            }
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_comprehensive_backtest_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Detailed results saved to: {filename}")
        logger.info("=" * 80)
        logger.info("🎉 SIMPLE COMPREHENSIVE BACKTEST COMPLETED!")
        logger.info("=" * 80)
        
        # Show how to analyze results
        logger.info(f"\n📋 TO ANALYZE TRADE DETAILS:")
        logger.info(f"   python analyze_detailed_backtest_results.py {filename}")
        
        return detailed_results
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_simple_comprehensive_backtest())
