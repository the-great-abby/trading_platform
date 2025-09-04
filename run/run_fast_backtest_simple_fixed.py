#!/usr/bin/env python3
"""
Simplified Fast Backtest with Post-Processing LLM Evaluation
Fixed version that avoids strategy compatibility issues
"""

import asyncio
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Add src to path
sys.path.append('/app/src')

from src.services.ai.ollama_service import OllamaService
from src.services.ai.trade_evaluator import TradeEvaluator
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.trading_config import get_symbols, get_options_symbols
from src.utils.enhanced_logging import get_trading_logger

class SimpleFixedBacktest:
    def __init__(self):
        self.logger = get_trading_logger()
        
        # Test configuration
        self.test_period = {
            'start_date': '2023-07-15',
            'end_date': '2025-07-14'
        }
        
        # Use only working strategies
        self.working_strategies = [
            'RSI',
            'MACD', 
            'BollingerBands',
            'SMA',
            'EMA',
            'Stochastic',
            'WilliamsR',
            'ADX',
            'Ichimoku',
            'GreeksEnhanced'
        ]
        
        # Risk settings
        self.risk_config = {
            'initial_capital': 1000000,  # 1M
            'position_size': 0.05,  # 5% per trade
            'max_daily_trades': 10,
            'stop_loss': 0.02,  # 2%
            'take_profit': 0.04,  # 4%
            'confidence_threshold': 0.3  # Lower threshold
        }

    async def run_fast_backtest(self):
        """Run the simplified backtest with working strategies only"""
        self.logger.info("🚀 Starting Simplified Fast Backtest with Post-Processing LLM Evaluation")
        self.logger.info("=" * 75)
        
        # Configuration
        self.logger.info("📊 Configuration:")
        self.logger.info(f"   Test Period: {self.test_period['start_date']} to {self.test_period['end_date']}")
        duration = (datetime.strptime(self.test_period['end_date'], '%Y-%m-%d') - 
                   datetime.strptime(self.test_period['start_date'], '%Y-%m-%d')).days
        self.logger.info(f"   Duration: {duration} days")
        self.logger.info(f"   Working Strategies: {len(self.working_strategies)}")
        self.logger.info(f"   LLM Evaluation: DISABLED during execution")
        self.logger.info(f"   Post-Processing LLM: ENABLED")
        
        # Initialize backtest engine
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        
        self.logger.info("\n📈 PHASE 1: Core Strategies (Fast Execution)")
        self.logger.info("-" * 55)
        
        # Run backtest with working strategies only
        results = await engine.run_backtest(
            symbols=get_symbols(),
            start_date=self.test_period['start_date'],
            end_date=self.test_period['end_date'],
            strategies=self.working_strategies
        )
        
        # Collect trades for LLM analysis
        trades_data = []
        for strategy_name, result in results.items():
            if result and hasattr(result, 'trades') and result.trades:
                self.logger.info(f"✅ {strategy_name}: {len(result.trades)} trades")
                
                # Collect trades for LLM analysis
                for trade in result.trades:
                    if hasattr(trade, 'price') and hasattr(trade, 'pnl'):
                        trades_data.append({
                            'strategy': strategy_name,
                            'symbol': getattr(trade, 'symbol', 'Unknown'),
                            'entry_price': trade.price,
                            'exit_price': trade.price,  # Use same price for now
                            'entry_time': getattr(trade, 'timestamp', 'Unknown'),
                            'exit_time': getattr(trade, 'timestamp', 'Unknown'),
                            'pnl': trade.pnl,
                            'return_pct': trade.pnl / trade.price if trade.price else 0
                        })
            else:
                self.logger.info(f"⚠️  {strategy_name}: No trades generated")
        
        # Save trades for LLM analysis
        if trades_data:
            df = pd.DataFrame(trades_data)
            df.to_csv('trades_for_llm.csv', index=False)
            self.logger.info(f"💾 Saved {len(trades_data)} trades to trades_for_llm.csv for LLM post-processing.")
        
        # Run LLM post-processing
        if trades_data:
            await self._run_post_processing_llm_analysis(results)
        else:
            self.logger.info("⚠️  No trades generated, skipping LLM analysis")
        
        # Final summary
        self.logger.info("\n📊 Final Summary:")
        total_trades = len(trades_data)
        self.logger.info(f"   Total Trades: {total_trades}")
        self.logger.info(f"   Strategies Run: {len(results)}")
        self.logger.info(f"   Working Strategies: {len([r for r in results.values() if r and hasattr(r, 'trades') and r.trades])}")
        
        return results

    async def _run_post_processing_llm_analysis(self, results: Dict[str, Any]):
        """Run LLM analysis on saved trades"""
        self.logger.info("\n🤖 PHASE 2: Post-Processing LLM Analysis")
        self.logger.info("-" * 55)
        
        try:
            # Configure Ollama
            self.logger.info("🔧 Configuring Ollama for post-processing analysis...")
            ollama_url = "http://192.168.0.18:11434"  # Host IP
            self.logger.info(f"   Ollama URL: {ollama_url}")
            self.logger.info(f"   Timeout: 120.0s")
            
            ollama_service = OllamaService(ollama_url)
            trade_evaluator = TradeEvaluator(ollama_service)
            
            # Load trades
            df = pd.read_csv('trades_for_llm.csv')
            
            # Analyze top strategies
            strategy_counts = df['strategy'].value_counts()
            top_strategies = strategy_counts.head(5).index.tolist()
            
            self.logger.info("📊 Analyzing top 5 strategies with LLM:")
            for strategy in top_strategies:
                self.logger.info(f"   - {strategy}")
            
            # LLM analysis for each top strategy
            for strategy in top_strategies:
                self.logger.info(f"\n🤖 LLM Analysis: {strategy}")
                
                strategy_trades = df[df['strategy'] == strategy]
                
                # Prepare trade summary for LLM
                trade_summary = {
                    'strategy': strategy,
                    'total_trades': len(strategy_trades),
                    'winning_trades': len(strategy_trades[strategy_trades['pnl'] > 0]),
                    'losing_trades': len(strategy_trades[strategy_trades['pnl'] < 0]),
                    'total_pnl': strategy_trades['pnl'].sum(),
                    'avg_return': strategy_trades['return_pct'].mean(),
                    'max_profit': strategy_trades['pnl'].max(),
                    'max_loss': strategy_trades['pnl'].min(),
                    'sample_trades': strategy_trades.head(3).to_dict('records')
                }
                
                # LLM evaluation
                try:
                    evaluation = await trade_evaluator.evaluate_strategy_performance(trade_summary)
                    self.logger.info(f"✅ LLM Evaluation for {strategy}: {evaluation[:200]}...")
                except Exception as e:
                    self.logger.error(f"❌ LLM evaluation failed for {strategy}: {str(e)}")
            
            self.logger.info("\n✅ LLM post-processing analysis completed")
            
        except Exception as e:
            self.logger.error(f"❌ LLM post-processing failed: {str(e)}")

async def main():
    """Main entry point"""
    backtest = SimpleFixedBacktest()
    await backtest.run_fast_backtest()

if __name__ == "__main__":
    asyncio.run(main()) 