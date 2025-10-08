#!/usr/bin/env python3
"""
Detailed Backtest Results Analyzer
=================================

Analyzes the detailed backtest results to provide insights into:
- Trade-by-trade analysis with entry/exit reasons
- Strategy performance breakdown
- Market regime impact on performance
- Elliott Wave pattern success rates
- Options strategy effectiveness
- Risk management effectiveness
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestResultsAnalyzer:
    """Analyzes detailed backtest results"""
    
    def __init__(self, results_file: str):
        """Initialize with results file"""
        self.results_file = results_file
        self.data = self.load_results()
        self.trades_df = None
        self.regime_df = None
        self.patterns_df = None
        
    def load_results(self) -> Dict:
        """Load results from JSON file"""
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def analyze_trades(self):
        """Analyze trade details"""
        if not self.data.get('trade_details'):
            logger.warning("No trade details found in results")
            return
            
        trades = self.data['trade_details']
        self.trades_df = pd.DataFrame(trades)
        
        logger.info("📊 TRADE ANALYSIS")
        logger.info("=" * 50)
        
        # Overall trade statistics
        total_trades = len(trades)
        logger.info(f"Total Trades: {total_trades}")
        
        if total_trades == 0:
            logger.warning("No trades executed")
            return
        
        # Strategy breakdown
        strategy_counts = self.trades_df['strategy'].value_counts()
        logger.info(f"\nStrategy Trade Counts:")
        for strategy, count in strategy_counts.items():
            logger.info(f"  {strategy}: {count} trades")
        
        # Entry reasons analysis
        if 'entry_reason' in self.trades_df.columns:
            entry_reasons = self.trades_df['entry_reason'].value_counts()
            logger.info(f"\nEntry Reasons:")
            for reason, count in entry_reasons.items():
                logger.info(f"  {reason}: {count}")
        
        # Confidence analysis
        if 'confidence' in self.trades_df.columns:
            avg_confidence = self.trades_df['confidence'].mean()
            min_confidence = self.trades_df['confidence'].min()
            max_confidence = self.trades_df['confidence'].max()
            logger.info(f"\nConfidence Analysis:")
            logger.info(f"  Average: {avg_confidence:.2f}")
            logger.info(f"  Range: {min_confidence:.2f} - {max_confidence:.2f}")
        
        # Market regime analysis
        if 'market_regime' in self.trades_df.columns:
            regime_counts = self.trades_df['market_regime'].value_counts()
            logger.info(f"\nTrades by Market Regime:")
            for regime, count in regime_counts.items():
                logger.info(f"  {regime}: {count}")
    
    def analyze_market_regimes(self):
        """Analyze market regime changes and impact"""
        if not self.data.get('market_regime_history'):
            logger.warning("No market regime history found")
            return
            
        regimes = self.data['market_regime_history']
        self.regime_df = pd.DataFrame(regimes)
        
        logger.info("\n🌊 MARKET REGIME ANALYSIS")
        logger.info("=" * 50)
        
        total_regime_changes = len(regimes)
        logger.info(f"Total Regime Changes: {total_regime_changes}")
        
        if total_regime_changes > 0:
            # Most common regime transitions
            regime_transitions = self.regime_df.groupby(['old_regime', 'new_regime']).size()
            logger.info(f"\nRegime Transitions:")
            for (old, new), count in regime_transitions.items():
                logger.info(f"  {old} → {new}: {count}")
            
            # Average confidence in regime changes
            avg_confidence = self.regime_df['confidence'].mean()
            logger.info(f"\nAverage Regime Change Confidence: {avg_confidence:.2f}")
    
    def analyze_elliott_wave_patterns(self):
        """Analyze Elliott Wave pattern detection and success"""
        if not self.data.get('elliott_wave_patterns'):
            logger.warning("No Elliott Wave patterns found")
            return
            
        patterns = self.data['elliott_wave_patterns']
        self.patterns_df = pd.DataFrame(patterns)
        
        logger.info("\n🌊 ELLIOTT WAVE PATTERN ANALYSIS")
        logger.info("=" * 50)
        
        total_patterns = len(patterns)
        logger.info(f"Total Patterns Detected: {total_patterns}")
        
        if total_patterns > 0:
            # Pattern types
            pattern_types = self.patterns_df['pattern_type'].value_counts()
            logger.info(f"\nPattern Types:")
            for pattern_type, count in pattern_types.items():
                logger.info(f"  {pattern_type}: {count}")
            
            # Confidence analysis
            avg_confidence = self.patterns_df['confidence'].mean()
            logger.info(f"\nAverage Pattern Confidence: {avg_confidence:.2f}")
            
            # Symbols with most patterns
            symbol_patterns = self.patterns_df['symbol'].value_counts()
            logger.info(f"\nSymbols with Most Patterns:")
            for symbol, count in symbol_patterns.head(5).items():
                logger.info(f"  {symbol}: {count}")
    
    def analyze_strategy_performance(self):
        """Analyze individual strategy performance"""
        summary = self.data.get('summary', {})
        
        logger.info("\n📈 STRATEGY PERFORMANCE ANALYSIS")
        logger.info("=" * 50)
        
        if not summary:
            logger.warning("No strategy performance data found")
            return
        
        # Create performance DataFrame
        performance_data = []
        for strategy, results in summary.items():
            performance_data.append({
                'Strategy': strategy,
                'Total_Return': results.get('total_return', 0),
                'Sharpe_Ratio': results.get('sharpe_ratio', 0),
                'Max_Drawdown': results.get('max_drawdown', 0),
                'Win_Rate': results.get('win_rate', 0),
                'Total_Trades': results.get('total_trades', 0),
                'Final_Value': results.get('final_value', 0),
                'Total_PnL': results.get('total_pnl', 0)
            })
        
        perf_df = pd.DataFrame(performance_data)
        
        # Sort by total return
        perf_df = perf_df.sort_values('Total_Return', ascending=False)
        
        logger.info("Strategy Performance (sorted by return):")
        logger.info("-" * 50)
        
        for _, row in perf_df.iterrows():
            logger.info(f"\n{row['Strategy']}:")
            logger.info(f"  Return: {row['Total_Return']:.2%}")
            logger.info(f"  Sharpe: {row['Sharpe_Ratio']:.3f}")
            logger.info(f"  Max DD: {row['Max_Drawdown']:.2%}")
            logger.info(f"  Win Rate: {row['Win_Rate']:.2%}")
            logger.info(f"  Trades: {row['Total_Trades']}")
            logger.info(f"  Final Value: ${row['Final_Value']:,.2f}")
    
    def generate_trade_report(self):
        """Generate detailed trade-by-trade report"""
        if not self.trades_df is not None and len(self.trades_df) > 0:
            logger.info("\n📋 DETAILED TRADE REPORT")
            logger.info("=" * 50)
            
            # Show first 10 trades in detail
            logger.info("First 10 Trades:")
            for i, (_, trade) in enumerate(self.trades_df.head(10).iterrows()):
                logger.info(f"\nTrade {i+1}:")
                logger.info(f"  Symbol: {trade['symbol']}")
                logger.info(f"  Action: {trade['action']}")
                logger.info(f"  Quantity: {trade['quantity']}")
                logger.info(f"  Price: ${trade['price']:.2f}")
                logger.info(f"  Strategy: {trade['strategy']}")
                logger.info(f"  Reason: {trade.get('entry_reason', 'N/A')}")
                logger.info(f"  Confidence: {trade.get('confidence', 'N/A')}")
                logger.info(f"  Market Regime: {trade.get('market_regime', 'N/A')}")
                if trade.get('elliott_pattern'):
                    logger.info(f"  Elliott Pattern: {trade['elliott_pattern']}")
    
    def save_analysis_report(self, output_file: str = None):
        """Save detailed analysis report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"backtest_analysis_report_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            # Redirect logger to file
            original_handlers = logger.handlers[:]
            logger.handlers = []
            
            file_handler = logging.FileHandler(output_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Re-run analysis to file
            self.analyze_trades()
            self.analyze_market_regimes()
            self.analyze_elliott_wave_patterns()
            self.analyze_strategy_performance()
            self.generate_trade_report()
            
            # Restore original handlers
            logger.handlers = original_handlers
        
        logger.info(f"\n💾 Analysis report saved to: {output_file}")
    
    def run_full_analysis(self):
        """Run complete analysis"""
        logger.info("🔍 ANALYZING DETAILED BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Results File: {self.results_file}")
        logger.info("=" * 60)
        
        self.analyze_trades()
        self.analyze_market_regimes()
        self.analyze_elliott_wave_patterns()
        self.analyze_strategy_performance()
        self.generate_trade_report()
        self.save_analysis_report()

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_detailed_backtest_results.py <results_file.json>")
        print("\nAvailable result files:")
        import glob
        result_files = glob.glob("comprehensive_backtest_detailed_*.json")
        for file in result_files:
            print(f"  {file}")
        return
    
    results_file = sys.argv[1]
    
    try:
        analyzer = BacktestResultsAnalyzer(results_file)
        analyzer.run_full_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()

