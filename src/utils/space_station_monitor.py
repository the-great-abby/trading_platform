"""
Space Trading Station Performance Monitor
Inspired by Unix 'top' command for real-time trading performance tracking
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import os
from loguru import logger

# Optional import for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system metrics will be simulated")

from ..core.types import TradeSignal, Trade

# Optional database services
try:
    from ..services.database.market_data_service import MarketDataService
    from ..services.database.backtest_results_service import BacktestResultsService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Database services not available - running in demo mode")

# Optional backtest API client
try:
    from .backtest_api_client import BacktestAPIClient
    BACKTEST_API_AVAILABLE = True
except ImportError:
    BACKTEST_API_AVAILABLE = False
    logger.warning("Backtest API client not available")


@dataclass
class StrategyPerformance:
    """Strategy performance metrics"""
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    current_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    last_signal_time: Optional[datetime] = None
    last_signal_action: Optional[str] = None
    last_signal_confidence: Optional[float] = None


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_latency: float
    active_connections: int
    queue_size: int


class SpaceStationMonitor:
    """Real-time Space Trading Station performance monitor"""
    
    def __init__(self, refresh_interval: int = 5):
        self.refresh_interval = refresh_interval
        self.is_running = False
        
        # Performance tracking
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.recent_trades: deque = deque(maxlen=1000)
        self.system_metrics = SystemMetrics(0, 0, 0, 0, 0, 0)
        
        # Real-time counters
        self.total_trades = 0
        self.total_pnl = 0.0
        self.active_strategies = 0
        self.ai_signals_generated = 0
        self.news_events_processed = 0
        
        # Time tracking
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Services (optional)
        self.market_data_service = None
        self.backtest_service = None
        self.backtest_api_client = None
        
        if DATABASE_AVAILABLE:
            try:
                self.market_data_service = MarketDataService()
                self.backtest_service = BacktestResultsService()
            except Exception as e:
                logger.warning(f"Database services not available: {e}")
        
        # Initialize backtest API client
        if BACKTEST_API_AVAILABLE:
            try:
                self.backtest_api_client = BacktestAPIClient()
                logger.info("✅ Backtest API client initialized")
            except Exception as e:
                logger.warning(f"Backtest API client not available: {e}")
        
        # Performance history
        self.pnl_history = deque(maxlen=100)
        self.trade_history = deque(maxlen=100)
        
    async def start_monitoring(self):
        """Start the Space Station monitor"""
        self.is_running = True
        logger.info("🚀 Space Station Monitor: Mission Control is now active")
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_system_metrics, daemon=True).start()
        threading.Thread(target=self._update_display, daemon=True).start()
        
        # Start data collection
        await self._collect_performance_data()
    
    async def stop_monitoring(self):
        """Stop the Space Station monitor"""
        self.is_running = False
        logger.info("🛑 Space Station Monitor: Mission Control shutdown")
    
    def add_trade(self, trade: Trade):
        """Add a new trade to the monitor"""
        self.recent_trades.append(trade)
        self.total_trades += 1
        self.total_pnl += trade.pnl if hasattr(trade, 'pnl') and trade.pnl else 0.0
        
        # Update strategy performance
        strategy_name = trade.strategy if hasattr(trade, 'strategy') else 'Unknown'
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_pnl=0.0,
                current_pnl=0.0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0
            )
        
        # Update strategy metrics
        strategy = self.strategy_performance[strategy_name]
        strategy.total_trades += 1
        strategy.total_pnl += trade.pnl if hasattr(trade, 'pnl') and trade.pnl else 0.0
        
        if hasattr(trade, 'pnl') and trade.pnl and trade.pnl > 0:
            strategy.winning_trades += 1
        elif hasattr(trade, 'pnl') and trade.pnl and trade.pnl < 0:
            strategy.losing_trades += 1
        
        # Update win rate
        if strategy.total_trades > 0:
            strategy.win_rate = strategy.winning_trades / strategy.total_trades
        
        # Update averages
        if strategy.winning_trades > 0:
            strategy.avg_win = strategy.total_pnl / strategy.winning_trades
        if strategy.losing_trades > 0:
            strategy.avg_loss = strategy.total_pnl / strategy.losing_trades
    
    def add_signal(self, signal: TradeSignal):
        """Add a new trading signal to the monitor"""
        strategy_name = signal.strategy
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_pnl=0.0,
                current_pnl=0.0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0
            )
        
        strategy = self.strategy_performance[strategy_name]
        strategy.last_signal_time = datetime.now()
        strategy.last_signal_action = signal.action
        strategy.last_signal_confidence = signal.confidence
        
        if 'AI' in strategy_name:
            self.ai_signals_generated += 1
    
    async def fetch_api_data(self):
        """Fetch data from the backtest API"""
        if not self.backtest_api_client:
            return
        
        try:
            # Fetch recent backtest runs
            runs = await self.backtest_api_client.list_backtest_runs(limit=10)
            if runs:
                logger.info(f"📊 Fetched {len(runs)} backtest runs from API")
                
                # Update strategy performance from API data
                for run in runs:
                    strategy_name = run.get('strategy_name', 'Unknown')
                    if strategy_name not in self.strategy_performance:
                        self.strategy_performance[strategy_name] = StrategyPerformance(
                            strategy_name=strategy_name,
                            total_trades=0,
                            winning_trades=0,
                            losing_trades=0,
                            total_pnl=0.0,
                            current_pnl=0.0,
                            win_rate=0.0,
                            avg_win=0.0,
                            avg_loss=0.0,
                            max_drawdown=0.0,
                            sharpe_ratio=0.0
                        )
                    
                    # Update with API data
                    strategy = self.strategy_performance[strategy_name]
                    strategy.total_pnl = run.get('total_pnl', 0.0)
                    strategy.total_trades = run.get('total_trades', 0)
                    strategy.win_rate = run.get('win_rate', 0.0)
                    
                    # Update total PnL
                    self.total_pnl = sum(s.total_pnl for s in self.strategy_performance.values())
                    self.total_trades = sum(s.total_trades for s in self.strategy_performance.values())
            
            # Fetch strategy comparison
            comparison = await self.backtest_api_client.compare_strategies()
            if comparison.get('success'):
                logger.info("📈 Strategy comparison data updated from API")
                
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
    
    def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.is_running:
            try:
                if PSUTIL_AVAILABLE:
                    # CPU and Memory
                    self.system_metrics.cpu_usage = psutil.cpu_percent(interval=1)
                    self.system_metrics.memory_usage = psutil.virtual_memory().percent
                    
                    # Disk I/O
                    disk_io = psutil.disk_io_counters()
                    if disk_io:
                        self.system_metrics.disk_io = disk_io.read_bytes + disk_io.write_bytes
                    else:
                        self.system_metrics.disk_io = 0
                    
                    # Network
                    net_io = psutil.net_io_counters()
                    self.system_metrics.network_latency = net_io.bytes_sent + net_io.bytes_recv
                    
                    # Active connections (simplified)
                    self.system_metrics.active_connections = len(psutil.net_connections())
                else:
                    # Simulated metrics when psutil is not available
                    self.system_metrics.cpu_usage = 25.0 + (time.time() % 20)
                    self.system_metrics.memory_usage = 60.0 + (time.time() % 15)
                    self.system_metrics.disk_io = 1000000 + int(time.time() % 1000000)
                    self.system_metrics.network_latency = 500000 + int(time.time() % 500000)
                    self.system_metrics.active_connections = 5 + int(time.time() % 10)
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
    
    async def _collect_performance_data(self):
        """Collect performance data from services"""
        while self.is_running:
            try:
                # Fetch data from API every few cycles
                if self.backtest_api_client and time.time() % (self.refresh_interval * 3) < self.refresh_interval:
                    await self.fetch_api_data()
                
                # Update active strategies count
                self.active_strategies = len(self.strategy_performance)
                
                # Update PnL history
                self.pnl_history.append(self.total_pnl)
                
                # Update trade history
                if self.recent_trades:
                    self.trade_history.append(len(self.recent_trades))
                
                # Calculate Sharpe ratio for each strategy
                for strategy in self.strategy_performance.values():
                    if strategy.total_trades > 0:
                        # Simplified Sharpe calculation
                        strategy.sharpe_ratio = strategy.total_pnl / max(strategy.total_trades, 1)
                
                await asyncio.sleep(self.refresh_interval)
                
            except Exception as e:
                logger.error(f"Error collecting performance data: {e}")
    
    def _update_display(self):
        """Update the display in a separate thread"""
        while self.is_running:
            try:
                self._print_dashboard()
                time.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"Error updating display: {e}")
    
    def _print_dashboard(self):
        """Print the Space Station dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Header
        print("🚀 SPACE TRADING STATION - MISSION CONTROL DASHBOARD")
        print("=" * 80)
        print(f"🕐 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Uptime: {datetime.now() - self.start_time}")
        print()
        
        # System Overview
        print("📊 SYSTEM OVERVIEW")
        print("-" * 40)
        print(f"CPU Usage: {self.system_metrics.cpu_usage:.1f}%")
        print(f"Memory Usage: {self.system_metrics.memory_usage:.1f}%")
        print(f"Active Strategies: {self.active_strategies}")
        print(f"Total Trades: {self.total_trades}")
        print(f"Total P&L: ${self.total_pnl:,.2f}")
        print(f"AI Signals Generated: {self.ai_signals_generated}")
        print()
        
        # Recent Activity (Last 5 seconds)
        print("⚡ RECENT ACTIVITY (Last 5 seconds)")
        print("-" * 40)
        recent_trades = [t for t in self.recent_trades 
                        if datetime.now() - getattr(t, 'timestamp', datetime.now()) < timedelta(seconds=5)]
        print(f"Recent Trades: {len(recent_trades)}")
        print(f"Recent P&L: ${sum(getattr(t, 'pnl', 0) for t in recent_trades):,.2f}")
        print()
        
        # Strategy Performance Table
        print("📈 STRATEGY PERFORMANCE")
        print("-" * 80)
        print(f"{'Strategy':<20} {'Trades':<8} {'Win Rate':<10} {'P&L':<12} {'Sharpe':<8} {'Last Signal':<15}")
        print("-" * 80)
        
        # Sort strategies by total P&L
        sorted_strategies = sorted(
            self.strategy_performance.values(),
            key=lambda x: x.total_pnl,
            reverse=True
        )
        
        for strategy in sorted_strategies[:10]:  # Top 10 strategies
            last_signal = strategy.last_signal_time.strftime('%H:%M:%S') if strategy.last_signal_time else 'N/A'
            print(f"{strategy.strategy_name:<20} "
                  f"{strategy.total_trades:<8} "
                  f"{strategy.win_rate*100:<9.1f}% "
                  f"${strategy.total_pnl:<11,.2f} "
                  f"{strategy.sharpe_ratio:<8.2f} "
                  f"{last_signal:<15}")
        
        print()
        
        # AI Navigation Systems Status
        print("🤖 AI NAVIGATION SYSTEMS STATUS")
        print("-" * 40)
        ai_strategies = [s for s in self.strategy_performance.values() if 'AI' in s.strategy_name]
        for strategy in ai_strategies:
            status = "🟢 ACTIVE" if strategy.last_signal_time and \
                    (datetime.now() - strategy.last_signal_time).seconds < 60 else "🟡 IDLE"
            print(f"{strategy.strategy_name:<25} {status}")
        
        print()
        
        # Performance Trends
        print("📊 PERFORMANCE TRENDS")
        print("-" * 40)
        if len(self.pnl_history) > 1:
            pnl_change = self.pnl_history[-1] - self.pnl_history[-2]
            trend = "📈" if pnl_change > 0 else "📉" if pnl_change < 0 else "➡️"
            print(f"P&L Trend: {trend} ${pnl_change:,.2f}")
        
        if len(self.trade_history) > 1:
            trade_change = self.trade_history[-1] - self.trade_history[-2]
            print(f"Trade Activity: {'📈' if trade_change > 0 else '📉' if trade_change < 0 else '➡️'} {trade_change}")
        
        print()
        print("Press Ctrl+C to exit Mission Control")
        print("=" * 80)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance"""
        return {
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl,
            'active_strategies': self.active_strategies,
            'ai_signals': self.ai_signals_generated,
            'uptime': str(datetime.now() - self.start_time),
            'system_metrics': {
                'cpu': self.system_metrics.cpu_usage,
                'memory': self.system_metrics.memory_usage,
                'disk_io': self.system_metrics.disk_io,
                'network': self.system_metrics.network_latency
            },
            'strategies': {
                name: {
                    'total_trades': perf.total_trades,
                    'win_rate': perf.win_rate,
                    'total_pnl': perf.total_pnl,
                    'sharpe_ratio': perf.sharpe_ratio,
                    'last_signal': perf.last_signal_time.isoformat() if perf.last_signal_time else None
                }
                for name, perf in self.strategy_performance.items()
            }
        }


# Global monitor instance
space_station_monitor = SpaceStationMonitor()


async def start_space_station_monitor():
    """Start the Space Station monitor"""
    await space_station_monitor.start_monitoring()


def add_trade_to_monitor(trade: Trade):
    """Add a trade to the monitor"""
    space_station_monitor.add_trade(trade)


def add_signal_to_monitor(signal: TradeSignal):
    """Add a signal to the monitor"""
    space_station_monitor.add_signal(signal)


def get_performance_summary() -> Dict[str, Any]:
    """Get current performance summary"""
    return space_station_monitor.get_performance_summary()


if __name__ == "__main__":
    """Run the Space Station Monitor standalone"""
    print("🚀 Starting Space Trading Station Monitor...")
    print("This is ORION, Mission Control. All systems are go!")
    
    try:
        asyncio.run(start_space_station_monitor())
    except KeyboardInterrupt:
        print("\n🛑 Mission Control shutdown initiated by user")
        asyncio.run(space_station_monitor.stop_monitoring())
    except Exception as e:
        print(f"❌ Mission Control error: {e}")
        asyncio.run(space_station_monitor.stop_monitoring()) 