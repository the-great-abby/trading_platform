#!/usr/bin/env python3
"""
HybridIchimokuStrategy Paper Trading Monitor
===========================================

Real-time monitoring of the HybridIchimokuStrategy performance in paper trading.
Tracks trades, performance metrics, and strategy analysis.
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridIchimokuMonitor:
    """Monitor HybridIchimokuStrategy paper trading performance"""
    
    def __init__(self, api_base_url: str = "http://localhost:11115"):
        self.api_base_url = api_base_url
        self.start_time = datetime.now()
        self.trade_history = []
        self.performance_history = []
        
        logger.info("🎯 HybridIchimokuStrategy Monitor initialized")
        logger.info(f"📊 Monitoring API: {api_base_url}")
    
    def get_paper_trading_status(self) -> Dict[str, Any]:
        """Get current paper trading status"""
        try:
            response = requests.get(f"{self.api_base_url}/api/paper-trading/status")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get status: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {}
    
    def get_paper_trading_performance(self) -> Dict[str, Any]:
        """Get paper trading performance metrics"""
        try:
            response = requests.get(f"{self.api_base_url}/api/paper-trading/performance")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get performance: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return {}
    
    def get_recent_trades(self) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            response = requests.get(f"{self.api_base_url}/api/paper-trading/trades")
            if response.status_code == 200:
                return response.json().get('trades', [])
            else:
                logger.error(f"Failed to get trades: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    def analyze_strategy_performance(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze strategy performance from trades"""
        if not trades:
            return {}
        
        # Filter for HybridIchimokuStrategy trades
        hybrid_trades = [t for t in trades if t.get('strategy') == 'HybridIchimokuStrategy']
        
        if not hybrid_trades:
            return {}
        
        # Calculate metrics
        total_trades = len(hybrid_trades)
        winning_trades = len([t for t in hybrid_trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in hybrid_trades if t.get('pnl', 0) < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t.get('pnl', 0) for t in hybrid_trades)
        avg_win = sum(t.get('pnl', 0) for t in hybrid_trades if t.get('pnl', 0) > 0) / max(winning_trades, 1)
        avg_loss = sum(t.get('pnl', 0) for t in hybrid_trades if t.get('pnl', 0) < 0) / max(losing_trades, 1)
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Analyze asset class distribution
        asset_classes = {}
        for trade in hybrid_trades:
            metadata = trade.get('metadata', {})
            hybrid_strategy = metadata.get('hybrid_strategy', {})
            asset_class = hybrid_strategy.get('asset_class', 'UNKNOWN')
            asset_classes[asset_class] = asset_classes.get(asset_class, 0) + 1
        
        # Analyze Elliott Wave patterns
        patterns = {}
        for trade in hybrid_trades:
            metadata = trade.get('metadata', {})
            hybrid_strategy = metadata.get('hybrid_strategy', {})
            elliott_pattern = hybrid_strategy.get('elliott_pattern', {})
            pattern_type = elliott_pattern.get('pattern_type', 'UNKNOWN')
            patterns[pattern_type] = patterns.get(pattern_type, 0) + 1
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'asset_class_distribution': asset_classes,
            'elliott_pattern_distribution': patterns
        }
    
    def display_status(self, status: Dict[str, Any]):
        """Display current status"""
        if not status:
            logger.warning("⚠️ No status data available")
            return
        
        data = status.get('data', {})
        
        print("\n" + "="*60)
        print("🎯 HYBRID ICHIMOKU STRATEGY - PAPER TRADING STATUS")
        print("="*60)
        
        # Basic info
        is_running = data.get('is_running', False)
        start_time = data.get('start_time', 'Unknown')
        portfolio_value = data.get('portfolio_value', 0)
        total_trades = data.get('total_trades', 0)
        total_pnl = data.get('total_pnl', 0)
        
        print(f"📊 Status: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")
        print(f"⏰ Started: {start_time}")
        print(f"💰 Portfolio Value: ${portfolio_value:,.2f}")
        print(f"📈 Total Trades: {total_trades}")
        print(f"💵 Total P&L: ${total_pnl:+,.2f}")
        
        # Active strategies
        active_strategies = data.get('active_strategies', [])
        print(f"🎯 Active Strategies: {', '.join(active_strategies)}")
        
        # Last trade
        last_trade = data.get('last_trade')
        if last_trade:
            print(f"🔄 Last Trade: {last_trade.get('symbol', 'N/A')} {last_trade.get('action', 'N/A')} @ ${last_trade.get('price', 0):.2f}")
        else:
            print("🔄 Last Trade: None")
        
        print("="*60)
    
    def display_performance_analysis(self, analysis: Dict[str, Any]):
        """Display performance analysis"""
        if not analysis:
            logger.info("📊 No performance analysis available yet")
            return
        
        print("\n" + "="*60)
        print("📈 HYBRID ICHIMOKU STRATEGY - PERFORMANCE ANALYSIS")
        print("="*60)
        
        # Basic metrics
        total_trades = analysis.get('total_trades', 0)
        win_rate = analysis.get('win_rate', 0)
        total_pnl = analysis.get('total_pnl', 0)
        profit_factor = analysis.get('profit_factor', 0)
        
        print(f"📊 Total Trades: {total_trades}")
        print(f"🎯 Win Rate: {win_rate:.1%}")
        print(f"💵 Total P&L: ${total_pnl:+,.2f}")
        print(f"📈 Profit Factor: {profit_factor:.2f}")
        
        # Asset class distribution
        asset_classes = analysis.get('asset_class_distribution', {})
        if asset_classes:
            print(f"\n💰 Asset Class Distribution:")
            for asset_class, count in asset_classes.items():
                percentage = (count / total_trades) * 100 if total_trades > 0 else 0
                print(f"   {asset_class}: {count} trades ({percentage:.1f}%)")
        
        # Elliott Wave pattern distribution
        patterns = analysis.get('elliott_pattern_distribution', {})
        if patterns:
            print(f"\n🌊 Elliott Wave Pattern Distribution:")
            for pattern, count in patterns.items():
                percentage = (count / total_trades) * 100 if total_trades > 0 else 0
                print(f"   {pattern}: {count} trades ({percentage:.1f}%)")
        
        print("="*60)
    
    def monitor_continuously(self, interval: int = 30):
        """Monitor continuously with specified interval"""
        logger.info(f"🔄 Starting continuous monitoring (every {interval} seconds)")
        logger.info("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Get current status
                status = self.get_paper_trading_status()
                self.display_status(status)
                
                # Get recent trades and analyze
                trades = self.get_recent_trades()
                analysis = self.analyze_strategy_performance(trades)
                self.display_performance_analysis(analysis)
                
                # Wait for next check
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    def run_single_check(self):
        """Run a single check and display results"""
        logger.info("🔍 Running single performance check")
        
        # Get current status
        status = self.get_paper_trading_status()
        self.display_status(status)
        
        # Get recent trades and analyze
        trades = self.get_recent_trades()
        analysis = self.analyze_strategy_performance(trades)
        self.display_performance_analysis(analysis)
        
        return status, analysis

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor HybridIchimokuStrategy paper trading')
    parser.add_argument('--interval', type=int, default=30, help='Monitoring interval in seconds')
    parser.add_argument('--single', action='store_true', help='Run single check instead of continuous monitoring')
    parser.add_argument('--api-url', default='http://localhost:11115', help='API base URL')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = HybridIchimokuMonitor(api_base_url=args.api_url)
    
    if args.single:
        monitor.run_single_check()
    else:
        monitor.monitor_continuously(interval=args.interval)

if __name__ == "__main__":
    main()





