#!/usr/bin/env python3
"""
Paper Trading Monitor
Real-time monitoring of paper trading with trade tracking and performance metrics
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque
import json

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
    """Real-time paper trading monitor"""
    
    def __init__(self, refresh_interval: int = 5):
        self.refresh_interval = refresh_interval
        self.is_running = False
        
        # Trade tracking
        self.trades: List[TradeRecord] = []
        self.recent_trades: deque = deque(maxlen=100)
        
        # Strategy performance
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # Portfolio tracking
        self.initial_capital = 4000  # Updated to match live trading
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
        
        logger.info("📊 Paper Trading Monitor initialized")
    
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
        
        logger.info(f"📈 Trade recorded: {trade.action} {trade.quantity} {trade.symbol} @ {trade.price}")
    
    def _update_portfolio(self, trade: TradeRecord):
        """Update portfolio with trade"""
        # Update current value
        self.current_value = trade.portfolio_value
        self.total_pnl = self.current_value - self.initial_capital
        
        # Update peak and drawdown
        if self.current_value > self.peak_value:
            self.peak_value = self.current_value
        
        current_drawdown = (self.peak_value - self.current_value) / self.peak_value
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
    
    def _update_strategy_performance(self, trade: TradeRecord):
        """Update strategy performance metrics"""
        strategy_name = trade.strategy
        
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(name=strategy_name)
        
        strategy = self.strategy_performance[strategy_name]
        strategy.total_trades += 1
        strategy.total_pnl += trade.pnl
        strategy.last_trade = trade.timestamp
        
        if trade.pnl > 0:
            strategy.wins += 1
        else:
            strategy.losses += 1
        
        # Update win rate
        strategy.win_rate = strategy.wins / strategy.total_trades if strategy.total_trades > 0 else 0
        
        # Update averages
        if strategy.wins > 0:
            strategy.avg_win = strategy.total_pnl / strategy.wins
        if strategy.losses > 0:
            strategy.avg_loss = strategy.total_pnl / strategy.losses
    
    def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        return {
            "total_trades": self.total_trades,
            "today_trades": self.today_trades,
            "total_pnl": self.total_pnl,
            "today_pnl": self.today_pnl,
            "portfolio_value": self.current_value,
            "return_percentage": (self.total_pnl / self.initial_capital) * 100,
            "max_drawdown": self.max_drawdown * 100,
            "uptime": (datetime.now() - self.start_time).total_seconds() / 3600,
            "strategies": len(self.strategy_performance)
        }
    
    def get_strategy_performance(self) -> Dict[str, Dict]:
        """Get performance by strategy"""
        return {
            name: {
                "total_trades": perf.total_trades,
                "wins": perf.wins,
                "losses": perf.losses,
                "win_rate": perf.win_rate,
                "total_pnl": perf.total_pnl,
                "avg_win": perf.avg_win,
                "avg_loss": perf.avg_loss,
                "last_trade": perf.last_trade.isoformat() if perf.last_trade else None
            }
            for name, perf in self.strategy_performance.items()
        }
    
    def get_recent_trades(self, count: int = 10) -> List[Dict]:
        """Get recent trades"""
        recent = list(self.recent_trades)[-count:]
        return [
            {
                "timestamp": trade.timestamp.isoformat(),
                "symbol": trade.symbol,
                "action": trade.action,
                "quantity": trade.quantity,
                "price": trade.price,
                "strategy": trade.strategy,
                "pnl": trade.pnl
            }
            for trade in recent
        ]
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        self.is_running = True
        logger.info("🚀 Starting Paper Trading Monitor...")
        
        while self.is_running:
            try:
                # Display current status
                self._display_status()
                
                # Wait for next update
                await asyncio.sleep(self.refresh_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Stopping monitor...")
                self.is_running = False
            except Exception as e:
                logger.error(f"❌ Error in monitoring: {e}")
                await asyncio.sleep(5)
    
    def _display_status(self):
        """Display current trading status"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*80)
        print("🚀 PAPER TRADING MONITOR")
        print("="*80)
        
        # Portfolio Summary
        print(f"💰 Portfolio Value: ${summary['portfolio_value']:,.2f}")
        print(f"📈 Total P&L: ${summary['total_pnl']:,.2f} ({summary['return_percentage']:.2f}%)")
        print(f"📉 Max Drawdown: {summary['max_drawdown']:.2f}%")
        print(f"⏱️  Uptime: {summary['uptime']:.1f} hours")
        
        # Today's Activity
        print(f"\n📅 Today's Activity:")
        print(f"   Trades: {summary['today_trades']}")
        print(f"   P&L: ${summary['today_pnl']:,.2f}")
        
        # Strategy Performance
        print(f"\n📊 Strategy Performance:")
        strategy_perf = self.get_strategy_performance()
        for strategy_name, perf in strategy_perf.items():
            print(f"   {strategy_name}:")
            print(f"     Trades: {perf['total_trades']}, Win Rate: {perf['win_rate']:.1%}")
            print(f"     P&L: ${perf['total_pnl']:,.2f}")
        
        # Recent Trades
        print(f"\n🔄 Recent Trades:")
        recent_trades = self.get_recent_trades(5)
        for trade in recent_trades:
            print(f"   {trade['timestamp'][11:19]} | {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f} | P&L: ${trade['pnl']:.2f}")
        
        print("="*80)
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Press Ctrl+C to stop monitoring")


async def main():
    """Main monitoring function"""
    monitor = PaperTradingMonitor()
    
    # Start monitoring
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main()) 