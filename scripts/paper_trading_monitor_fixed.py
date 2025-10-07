#!/usr/bin/env python3
"""
Paper Trading Monitor - Updated to use correct configuration
Real-time monitoring of paper trading with trade tracking and performance metrics
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Record of a paper trade"""
    timestamp: datetime
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    price: float
    strategy: str
    pnl: float = 0.0
    portfolio_value: float = 0.0
    trade_id: str = ""


@dataclass
class StrategyPerformance:
    """Strategy performance metrics"""
    name: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    last_trade: Optional[datetime] = None


class PaperTradingMonitor:
    """Real-time paper trading monitor with proper configuration loading"""
    
    def __init__(self, refresh_interval: int = 5):
        self.refresh_interval = refresh_interval
        self.is_running = False
        
        # Load configuration
        self.config = self._load_config()
        
        # Trade tracking
        self.trades: List[TradeRecord] = []
        self.recent_trades: deque = deque(maxlen=100)
        
        # Strategy performance
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # Portfolio tracking - use config values
        self.initial_capital = self.config.get('initial_capital', 4000.0)
        self.current_value = self.initial_capital
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = self.initial_capital
        
        # Performance metrics
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Real-time counters
        self.total_trades = 0
        self.today_trades = 0
        self.today_pnl = 0.0
        
        logger.info(f"📊 Paper Trading Monitor initialized with ${self.initial_capital:,.2f} capital")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        config_file = "config/paper_trading_engine.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"📋 Loaded configuration from {config_file}")
                return config
            except Exception as e:
                logger.warning(f"Could not load config from {config_file}: {e}")
        
        # Fallback to default config
        logger.info("Using default configuration")
        return {
            'initial_capital': 4000.0,
            'max_position_size': 0.12,
            'max_risk_per_trade': 0.015,
            'trading_interval': 60,
            'strategies': ['ELLIOTT_WAVE_CORRECTIVE', 'ELLIOTT_WAVE_IMPULSE', 'CALENDAR_SPREADS', 'VOLATILITY_TRADING'],
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ'],
            'enable_alerts': True,
            'performance_tracking': True,
            'max_daily_trades': 4,
            'max_daily_loss': 150.0,
            'max_monthly_trades': 8,
            'min_cash_reserve': 0.15
        }
    
    def add_trade(self, trade: TradeRecord):
        """Add a new trade to tracking"""
        self.trades.append(trade)
        self.recent_trades.append(trade)
        
        # Update portfolio
        self._update_portfolio(trade)
        
        # Update strategy performance
        self._update_strategy_performance(trade)
        
        # Update counters
        self.total_trades += 1
        if trade.timestamp.date() == datetime.now().date():
            self.today_trades += 1
            self.today_pnl += trade.pnl
        
        logger.info(f"📈 Trade recorded: {trade.action} {trade.quantity} {trade.symbol} @ ${trade.price:.2f}")
    
    def _update_portfolio(self, trade: TradeRecord):
        """Update portfolio with trade"""
        if trade.action == "BUY":
            # Simulate buying (reduce cash, add position value)
            cost = trade.quantity * trade.price
            self.current_value -= cost
        elif trade.action == "SELL":
            # Simulate selling (add cash, remove position value)
            proceeds = trade.quantity * trade.price
            self.current_value += proceeds
        
        # Update P&L
        self.total_pnl = self.current_value - self.initial_capital
        
        # Update drawdown
        if self.current_value > self.peak_value:
            self.peak_value = self.current_value
        
        current_drawdown = (self.peak_value - self.current_value) / self.peak_value
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Update trade record with current portfolio value
        trade.portfolio_value = self.current_value
    
    def _update_strategy_performance(self, trade: TradeRecord):
        """Update strategy performance metrics"""
        strategy_name = trade.strategy
        
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(name=strategy_name)
        
        perf = self.strategy_performance[strategy_name]
        perf.total_trades += 1
        perf.total_pnl += trade.pnl
        perf.last_trade = trade.timestamp
        
        if trade.pnl > 0:
            perf.wins += 1
        else:
            perf.losses += 1
        
        # Calculate win rate
        if perf.total_trades > 0:
            perf.win_rate = perf.wins / perf.total_trades
        
        # Calculate average win/loss
        if perf.wins > 0:
            perf.avg_win = sum(t.pnl for t in self.trades if t.strategy == strategy_name and t.pnl > 0) / perf.wins
        if perf.losses > 0:
            perf.avg_loss = sum(t.pnl for t in self.trades if t.strategy == strategy_name and t.pnl < 0) / perf.losses
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'initial_capital': self.initial_capital,
            'current_value': self.current_value,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': (self.total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'today_trades': self.today_trades,
            'today_pnl': self.today_pnl,
            'strategies': list(self.strategy_performance.keys()),
            'recent_trades': [trade.__dict__ for trade in list(self.recent_trades)[-10:]]
        }
    
    def print_status(self):
        """Print current status"""
        status = self.get_status()
        
        print(f"\n📊 Paper Trading Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"💰 Initial Capital: ${status['initial_capital']:,.2f}")
        print(f"📈 Current Value: ${status['current_value']:,.2f}")
        print(f"📊 Total P&L: ${status['total_pnl']:,.2f} ({status['total_pnl_percent']:+.2f}%)")
        print(f"📉 Max Drawdown: {status['max_drawdown']:.2%}")
        print(f"📈 Total Trades: {status['total_trades']}")
        print(f"📅 Today's Trades: {status['today_trades']}")
        print(f"📊 Today's P&L: ${status['today_pnl']:,.2f}")
        
        if status['strategies']:
            print(f"\n🎯 Active Strategies:")
            for strategy in status['strategies']:
                perf = self.strategy_performance[strategy]
                print(f"  ✅ {strategy}: {perf.total_trades} trades, {perf.win_rate:.1%} win rate")
        
        if status['recent_trades']:
            print(f"\n📈 Recent Trades:")
            for trade in status['recent_trades'][-5:]:
                print(f"  {trade['timestamp']}: {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
    
    async def run_single(self):
        """Run single status check"""
        self.print_status()
    
    async def run_continuous(self, interval_minutes: int = 5):
        """Run continuous monitoring"""
        self.is_running = True
        logger.info(f"🔄 Starting continuous monitoring (every {interval_minutes} minutes)")
        
        try:
            while self.is_running:
                self.print_status()
                await asyncio.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.is_running = False


async def main():
    """Main function"""
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = PaperTradingMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        await monitor.run_continuous(interval)
    else:
        await monitor.run_single()


if __name__ == "__main__":
    asyncio.run(main())


















