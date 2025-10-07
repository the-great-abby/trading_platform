#!/usr/bin/env python3
"""
Live Trading Monitor - Database-backed monitoring with API integration
Real-time monitoring of live trading with trade tracking and performance metrics
"""

import asyncio
import logging
import time
import json
import os
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Record of a live trade"""
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


class LiveTradingMonitor:
    """Real-time live trading monitor that fetches data from live trading service API"""
    
    def __init__(self, refresh_interval: int = 5):
        self.refresh_interval = refresh_interval
        self.is_running = False
        
        # Live trading service configuration
        self.live_service_url = "http://localhost:11120"
        self.account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
        
        # Trade tracking
        self.trades: List[TradeRecord] = []
        self.recent_trades: deque = deque(maxlen=100)
        
        # Strategy performance
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # Portfolio tracking
        self.initial_capital = 4000.0
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
        
        logger.info(f"📊 Live Trading Monitor initialized with ${self.initial_capital:,.2f} capital")
        logger.info(f"🔗 Connected to live trading service: {self.live_service_url}")
    
    async def fetch_orders_from_api(self) -> List[Dict]:
        """Fetch orders from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/trading/orders",
                    params={"account_id": self.account_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('orders', [])
                        else:
                            logger.warning(f"API returned error: {data.get('error')}")
                            return []
                    else:
                        logger.error(f"Failed to fetch orders: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching orders from API: {e}")
            return []
    
    async def fetch_positions_from_api(self) -> List[Dict]:
        """Fetch positions from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/trading/positions",
                    params={"account_id": self.account_id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('positions', [])
                        else:
                            logger.warning(f"API returned error: {data.get('error')}")
                            return []
                    else:
                        logger.error(f"Failed to fetch positions: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching positions from API: {e}")
            return []
    
    async def fetch_account_info_from_api(self) -> Dict:
        """Fetch account information from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/accounts/{self.account_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('account', {})
                        else:
                            logger.warning(f"API returned error: {data.get('error')}")
                            return {}
                    else:
                        logger.error(f"Failed to fetch account info: HTTP {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching account info from API: {e}")
            return {}
    
    def convert_api_order_to_trade_record(self, order: Dict) -> TradeRecord:
        """Convert API order to TradeRecord"""
        try:
            # Parse timestamps
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            
            # Calculate P&L (simplified - using premium as P&L for now)
            pnl = float(order.get('premium', 0))
            
            return TradeRecord(
                timestamp=created_at,
                symbol=order['symbol'],
                action='BUY',  # All orders are BUY for now
                quantity=int(order['quantity']),
                price=float(order.get('average_price', order.get('premium', 0))),
                strategy=order['strategy'],
                pnl=pnl,
                portfolio_value=self.current_value,
                trade_id=order['order_id']
            )
        except Exception as e:
            logger.error(f"Error converting order to trade record: {e}")
            return None
    
    async def update_from_api(self):
        """Update monitor data from live trading service API"""
        try:
            # Fetch orders from API
            orders = await self.fetch_orders_from_api()
            
            # Convert orders to trade records
            new_trades = []
            for order in orders:
                trade_record = self.convert_api_order_to_trade_record(order)
                if trade_record:
                    new_trades.append(trade_record)
            
            # Update trades list
            self.trades = new_trades
            self.recent_trades = deque(new_trades[-100:], maxlen=100)
            
            # Update counters
            self.total_trades = len(self.trades)
            
            # Calculate today's trades
            today = datetime.now().date()
            self.today_trades = sum(1 for trade in self.trades if trade.timestamp.date() == today)
            
            # Calculate P&L
            self.total_pnl = sum(trade.pnl for trade in self.trades)
            self.today_pnl = sum(trade.pnl for trade in self.trades if trade.timestamp.date() == today)
            
            # Update current value
            self.current_value = self.initial_capital + self.total_pnl
            
            # Update peak value and drawdown
            if self.current_value > self.peak_value:
                self.peak_value = self.current_value
            
            current_drawdown = (self.peak_value - self.current_value) / self.peak_value if self.peak_value > 0 else 0
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # Update strategy performance
            self._update_strategy_performance()
            
            self.last_update = datetime.now()
            
            logger.info(f"📊 Updated from API: {self.total_trades} trades, P&L: ${self.total_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating from API: {e}")
    
    def _update_strategy_performance(self):
        """Update strategy performance metrics"""
        strategy_stats = {}
        
        for trade in self.trades:
            strategy = trade.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'total_trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_pnl': 0.0,
                    'last_trade': None
                }
            
            stats = strategy_stats[strategy]
            stats['total_trades'] += 1
            stats['total_pnl'] += trade.pnl
            stats['last_trade'] = trade.timestamp
            
            if trade.pnl > 0:
                stats['wins'] += 1
            else:
                stats['losses'] += 1
        
        # Convert to StrategyPerformance objects
        self.strategy_performance = {}
        for strategy, stats in strategy_stats.items():
            win_rate = stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
            avg_win = stats['total_pnl'] / stats['wins'] if stats['wins'] > 0 else 0
            avg_loss = stats['total_pnl'] / stats['losses'] if stats['losses'] > 0 else 0
            
            self.strategy_performance[strategy] = StrategyPerformance(
                name=strategy,
                total_trades=stats['total_trades'],
                wins=stats['wins'],
                losses=stats['losses'],
                total_pnl=stats['total_pnl'],
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                last_trade=stats['last_trade']
            )
    
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
            'recent_trades': [trade.__dict__ for trade in list(self.recent_trades)[-10:]],
            'last_update': self.last_update.isoformat(),
            'live_service_url': self.live_service_url
        }
    
    def print_status(self):
        """Print current status"""
        status = self.get_status()
        
        print(f"\n📊 Live Trading Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"💰 Initial Capital: ${status['initial_capital']:,.2f}")
        print(f"📈 Current Value: ${status['current_value']:,.2f}")
        print(f"📊 Total P&L: ${status['total_pnl']:,.2f} ({status['total_pnl_percent']:+.2f}%)")
        print(f"📉 Max Drawdown: {status['max_drawdown']:.2%}")
        print(f"📈 Total Trades: {status['total_trades']}")
        print(f"📅 Today's Trades: {status['today_trades']}")
        print(f"📊 Today's P&L: ${status['today_pnl']:,.2f}")
        print(f"🔗 Data Source: Live Trading Service API ({status['live_service_url']})")
        print(f"🕒 Last Update: {status['last_update']}")
        
        if status['strategies']:
            print(f"\n📊 Strategy Performance:")
            for strategy_name in status['strategies']:
                strategy = self.strategy_performance[strategy_name]
                print(f"  {strategy_name}:")
                print(f"    Trades: {strategy.total_trades} | Win Rate: {strategy.win_rate:.1%}")
                print(f"    P&L: ${strategy.total_pnl:.2f} | Avg Win: ${strategy.avg_win:.2f} | Avg Loss: ${strategy.avg_loss:.2f}")
        
        if status['recent_trades']:
            print(f"\n📈 Recent Trades:")
            for trade in status['recent_trades'][-5:]:  # Show last 5 trades
                if isinstance(trade['timestamp'], str):
                    trade_time = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                else:
                    trade_time = trade['timestamp']
                print(f"  {trade_time.strftime('%H:%M:%S')} | {trade['symbol']} | {trade['strategy']} | "
                      f"{trade['quantity']} @ ${trade['price']:.2f} | P&L: ${trade['pnl']:.2f}")
    
    async def run_single(self):
        """Run a single update"""
        await self.update_from_api()
        self.print_status()
    
    async def run_continuous(self, interval_minutes: int = 5):
        """Run continuous monitoring"""
        self.is_running = True
        logger.info(f"🔄 Starting continuous monitoring (every {interval_minutes} minutes)")
        
        try:
            while self.is_running:
                await self.update_from_api()
                self.print_status()
                
                # Wait for next update
                await asyncio.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous monitoring: {e}")
        finally:
            self.is_running = False


async def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = LiveTradingMonitor()
    
    # Run single update
    await monitor.run_single()
    
    # Ask user if they want continuous monitoring
    try:
        response = input("\n🔄 Start continuous monitoring? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            interval = input("⏰ Update interval in minutes (default 5): ").strip()
            try:
                interval_minutes = int(interval) if interval else 5
            except ValueError:
                interval_minutes = 5
            
            await monitor.run_continuous(interval_minutes)
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())




