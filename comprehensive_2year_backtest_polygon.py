#!/usr/bin/env python3
"""
Comprehensive 2-Year Backtest with Detailed Trade Analysis (Polygon API)
======================================================================

This script runs a comprehensive backtest with all the requested strategies
and provides detailed trade-by-trade analysis including:
- Entry reasons and confidence levels
- Exit reasons and timing
- Strategy performance breakdown
- Market regime analysis
- Elliott Wave pattern details
- Options strategy reasoning

Uses Polygon API for reliable market data access.
Capital Allocation: 20% cash, 30% stocks, 50% options
Strategies: Market Regime, Ichimoku, Elliott Wave, Trailing Stop, Options
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

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.strategy_registry import get_strategy_registry, discover_strategies
from src.utils.trading_config import SYMBOLS, OPTIONS_SYMBOLS

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_backtest_polygon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DetailedBacktestEngine(BacktestEngine):
    """
    Extended backtest engine with detailed trade logging and analysis
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trade_details = []
        self.strategy_performance = {}
        self.market_regime_history = []
        self.elliott_wave_patterns = []
        
    def log_trade_details(self, trade_signal, entry_reason, confidence, strategy_name, market_regime=None, elliott_pattern=None):
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
            'market_regime': market_regime,
            'elliott_pattern': elliott_pattern,
            'metadata': trade_signal.metadata if hasattr(trade_signal, 'metadata') else {}
        }
        self.trade_details.append(trade_detail)
        
        logger.info(f"📊 TRADE DETAIL: {trade_signal.action} {trade_signal.quantity} {trade_signal.symbol} @ ${trade_signal.price:.2f}")
        logger.info(f"   🎯 Strategy: {strategy_name}")
        logger.info(f"   📈 Reason: {entry_reason}")
        logger.info(f"   🎯 Confidence: {confidence:.2f}")
        logger.info(f"   🌊 Market Regime: {market_regime}")
        if elliott_pattern:
            logger.info(f"   🌊 Elliott Pattern: {elliott_pattern}")
        logger.info("   " + "─" * 60)
    
    def log_exit_details(self, trade_signal, exit_reason, pnl, strategy_name):
        """Log detailed exit information"""
        logger.info(f"🚪 EXIT DETAIL: {trade_signal.symbol} - {exit_reason}")
        logger.info(f"   💰 P&L: ${pnl:.2f}")
        logger.info(f"   📊 Strategy: {strategy_name}")
        logger.info("   " + "─" * 60)
    
    def log_market_regime_change(self, old_regime, new_regime, confidence, indicators):
        """Log market regime changes"""
        regime_change = {
            'timestamp': datetime.now().isoformat(),
            'old_regime': old_regime,
            'new_regime': new_regime,
            'confidence': confidence,
            'indicators': indicators
        }
        self.market_regime_history.append(regime_change)
        
        logger.info(f"🔄 MARKET REGIME CHANGE: {old_regime} → {new_regime}")
        logger.info(f"   🎯 Confidence: {confidence:.2f}")
        logger.info(f"   📊 Indicators: {indicators}")
        logger.info("   " + "─" * 60)
    
    def log_elliott_wave_pattern(self, symbol, pattern_type, confidence, target_price, invalidation_level):
        """Log Elliott Wave pattern detection"""
        pattern = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'pattern_type': pattern_type,
            'confidence': confidence,
            'target_price': target_price,
            'invalidation_level': invalidation_level
        }
        self.elliott_wave_patterns.append(pattern)
        
        logger.info(f"🌊 ELLIOTT WAVE PATTERN: {pattern_type} on {symbol}")
        logger.info(f"   🎯 Confidence: {confidence:.2f}")
        logger.info(f"   📈 Target: ${target_price:.2f}")
        logger.info(f"   🛑 Invalidation: ${invalidation_level:.2f}")
        logger.info("   " + "─" * 60)

async def run_comprehensive_backtest():
    """Run the comprehensive 2-year backtest with detailed analysis"""
    
    logger.info("🚀 STARTING COMPREHENSIVE 2-YEAR BACKTEST WITH DETAILED ANALYSIS (POLYGON API)")
    logger.info("=" * 80)
    
    # Configuration
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    initial_capital = 100000  # $100k
    symbols = [
        # Large Cap Tech (reduced set for faster execution)
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        
        # Financials
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',
        
        # Consumer
        'KO', 'PEP', 'WMT', 'PG', 'NKE',
        
        # ETFs for diversification
        'SPY', 'QQQ', 'IWM', 'DIA', 'XLF', 'XLK', 'XLE', 'XLV'
    ]
    
    # Strategy configuration with detailed parameters (reduced set for faster execution)
    strategies_config = {
        # Market Regime Strategies
        'MarketRegimeAdaptiveStrategy': {
            'regime_lookback': 50,
            'volatility_threshold': 0.2,
            'trend_threshold': 0.02,
            'regime_confidence_threshold': 0.6
        },
        'AdaptiveSectorWaveStrategy': {
            'sector_rotation_lookback': 60,
            'volatility_threshold': 0.25,
            'trend_threshold': 0.03,
            'confidence_threshold': 0.65
        },
        
        # Core Strategies
        'IchimokuStrategy': {
            'tenkan_period': 9,
            'kijun_period': 26,
            'senkou_b_period': 52,
            'displacement': 26,
            'min_confidence': 0.7
        },
        
        # Elliott Wave Strategies (Service-Based)
        'ServiceBasedElliottWaveImpulseStrategy': {
            'service_url': 'http://elliott-wave-service.trading-system.svc.cluster.local:8000',
            'confidence_threshold': 0.7,
            'timeframe': '1d'
        },
        'ServiceBasedElliottWaveCorrectiveStrategy': {
            'service_url': 'http://elliott-wave-service.trading-system.svc.cluster.local:8000',
            'confidence_threshold': 0.6,
            'timeframe': '1d'
        },
        
        # Advanced Risk Management
        'TrailingStopStrategy': {
            'trailing_stop_pct': 0.05,
            'min_profit_pct': 0.02,
            'max_position_size': 0.15
        },
        
        # Options Strategies
        'CalendarSpreadStrategy': {
            'min_dte': 30,
            'max_dte': 60,
            'strike_distance': 0.02,
            'max_position_size': 0.20
        },
        'ButterflySpreadStrategy': {
            'min_dte': 45,
            'max_dte': 90,
            'wing_width': 0.05,
            'max_position_size': 0.15
        },
        'IronCondorStrategy': {
            'min_dte': 30,
            'max_dte': 60,
            'wing_width': 0.10,
            'max_position_size': 0.25
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
        for strategy_name, result in results.items():
            logger.info(f"\n🎯 {strategy_name}")
            logger.info(f"   📊 Total Return: {result.get('total_return', 0):.2%}")
            logger.info(f"   📈 Sharpe Ratio: {result.get('sharpe_ratio', 0):.3f}")
            logger.info(f"   📉 Max Drawdown: {result.get('max_drawdown', 0):.2%}")
            logger.info(f"   🎯 Win Rate: {result.get('win_rate', 0):.2%}")
            logger.info(f"   📊 Total Trades: {result.get('total_trades', 0)}")
            logger.info(f"   💰 Final Value: ${result.get('final_value', 0):,.2f}")
            logger.info(f"   💵 Total P&L: ${result.get('total_pnl', 0):,.2f}")
        
        # Save detailed results
        detailed_results = {
            'summary': results,
            'trade_details': engine.trade_details,
            'market_regime_history': engine.market_regime_history,
            'elliott_wave_patterns': engine.elliott_wave_patterns,
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
        filename = f"comprehensive_backtest_polygon_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Detailed results saved to: {filename}")
        logger.info("=" * 80)
        logger.info("🎉 COMPREHENSIVE BACKTEST COMPLETED!")
        logger.info("=" * 80)
        
        return detailed_results
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_comprehensive_backtest())

