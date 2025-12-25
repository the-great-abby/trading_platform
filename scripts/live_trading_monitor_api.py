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
    status: str = "FILLED"  # FILLED, PENDING, SUBMITTED, etc.
    option_type: str = None  # CALL/PUT or None for stocks
    strike_price: float = None
    expiration_date: str = None
    rejection_reason: str = None  # Why the trade failed to submit


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
        
        # Rejected trade attempts tracking
        self.rejected_attempts: List[Dict] = []
        
        # Position tracking
        self.last_positions: List[Dict] = []
        
        # Strategy performance
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # Portfolio tracking (will be updated from API)
        self.initial_capital = 0.0
        self.current_value = 0.0
        self.equity = 0.0
        self.buying_power = 0.0
        self.cash_balance = 0.0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        
        # Performance metrics
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Real-time counters
        self.total_trades = 0
        self.today_trades = 0
        self.today_pnl = 0.0
        
        logger.info(f"📊 Live Trading Monitor initialized")
        logger.info(f"🔗 Connected to live trading service: {self.live_service_url}")
    
    async def fetch_orders_from_api(self) -> List[Dict]:
        """Fetch orders from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/trading/orders",
                    params={
                        "account_id": self.account_id,
                        # Don't filter by status - show all recent orders (FILLED, PENDING, SUBMITTED)
                    },
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
                    params={"account_id": self.account_id, "status_filter": "OPEN"},
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
    
    async def fetch_account_balance_from_api(self) -> Dict:
        """Fetch account balance from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/account/balance/{self.account_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Account balance data: {data}")
                        return data
                    else:
                        response_text = await response.text()
                        logger.error(f"Failed to fetch account balance: HTTP {response.status} - {response_text}")
                        return {}
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching account balance from API")
            return {}
        except Exception as e:
            logger.error(f"Error fetching account balance from API: {e}", exc_info=True)
            return {}
    
    async def fetch_rejected_attempts_from_api(self) -> List[Dict]:
        """Fetch rejected trade attempts from live trading service API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.live_service_url}/api/v1/trading/rejected-attempts",
                    params={
                        "account_id": self.account_id,
                        "limit": 100
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('rejected_attempts', [])
                        else:
                            logger.warning(f"API returned error: {data.get('error')}")
                            return []
                    else:
                        logger.error(f"Failed to fetch rejected attempts: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching rejected attempts from API: {e}")
            return []
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol from Polygon"""
        try:
            # Get Polygon API key from environment or k8s secret
            api_key = os.environ.get('POLYGON_API_KEY')
            if not api_key:
                try:
                    # Try to get from kubectl
                    import subprocess
                    result = subprocess.run(
                        ['kubectl', 'get', 'secret', 'polygon-api-key', '-n', 'trading-system', 
                         '-o', "jsonpath='{.data.api-key}'"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        import base64
                        api_key = base64.b64decode(result.stdout.strip("'")).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Could not fetch Polygon API key from k8s: {e}")
            
            if not api_key:
                logger.warning(f"No Polygon API key available, using last known price for {symbol}")
                return 0.0
            
            # Fetch current price from Polygon
            async with aiohttp.ClientSession() as session:
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
                async with session.get(
                    url,
                    params={'apiKey': api_key},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            return float(data['results'][0]['c'])  # Close price
                    logger.warning(f"Failed to fetch price for {symbol}: HTTP {response.status}")
                    return 0.0
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return 0.0
    
    def convert_api_order_to_trade_record(self, order: Dict) -> TradeRecord:
        """Convert API order to TradeRecord"""
        try:
            from datetime import timezone
            
            # Parse timestamps - use filled_at if available (shows when trade executed), otherwise created_at
            # Database stores in UTC, so we need to ensure we treat it as UTC
            if order.get('filled_at'):
                timestamp_str = order['filled_at'].replace('Z', '+00:00')
            else:
                timestamp_str = order['created_at'].replace('Z', '+00:00')
            
            # Parse the timestamp
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # If no timezone info, assume UTC (database default)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            # For live_trades, we calculate P&L based on current price vs entry price
            # For now, use 0 as we'll calculate from positions
            pnl = 0.0
            
            # Get action (default to BUY if not present)
            action = order.get('action', 'BUY')
            
            return TradeRecord(
                timestamp=timestamp,
                symbol=order['symbol'],
                action=action,
                quantity=int(order['quantity']),
                price=float(order.get('price', order.get('average_price', 0))),
                strategy=order.get('strategy', 'UNKNOWN'),
                pnl=pnl,
                portfolio_value=self.current_value,
                trade_id=order.get('order_id', order.get('trade_id', '')),
                status=order.get('status', 'UNKNOWN'),
                option_type=order.get('option_type'),
                strike_price=float(order.get('strike_price')) if order.get('strike_price') else None,
                expiration_date=order.get('expiration_date'),
                rejection_reason=order.get('rejection_reason')
            )
        except Exception as e:
            logger.error(f"Error converting order to trade record: {e}")
            logger.debug(f"Order data: {order}")
            return None
    
    async def update_from_api(self):
        """Update monitor data from live trading service API"""
        try:
            # Fetch account balance from API
            balance_data = await self.fetch_account_balance_from_api()
            if balance_data and 'equity' in balance_data:
                self.equity = float(balance_data.get('equity', 0))
                self.buying_power = float(balance_data.get('buying_power', 0))
                self.cash_balance = float(balance_data.get('cash_balance', 0))
                self.current_value = self.equity  # Account balance = equity
                
                # Set initial capital on first fetch if not set
                if self.initial_capital == 0.0:
                    self.initial_capital = self.equity
                    self.peak_value = self.equity
            else:
                logger.error("Failed to fetch account balance - cannot update portfolio values")
                # Don't update if we didn't get valid balance data
                return
            
            # Fetch orders from API
            orders = await self.fetch_orders_from_api()
            
            # Fetch positions from API
            positions = await self.fetch_positions_from_api()
            
            # Fetch rejected trade attempts
            self.rejected_attempts = await self.fetch_rejected_attempts_from_api()
            
            # Update positions with real-time prices
            for position in positions:
                if position.get('status') == 'OPEN':
                    symbol = position.get('symbol')
                    current_price = await self._get_current_price(symbol)
                    if current_price and current_price > 0:
                        position['current_price'] = current_price
                        # Recalculate unrealized P&L
                        quantity = float(position.get('quantity', 0))
                        avg_price = float(position.get('average_price', 0))
                        position['unrealized_pnl'] = (current_price - avg_price) * quantity
            
            self.last_positions = positions  # Store for display
            
            # Convert orders to trade records (already filtered to FILLED orders)
            new_trades = []
            for order in orders:
                trade_record = self.convert_api_order_to_trade_record(order)
                if trade_record:
                    new_trades.append(trade_record)
            
            # Update trades list (API returns newest first, so we keep them in that order)
            self.trades = new_trades
            self.recent_trades = deque(new_trades[:100], maxlen=100)  # Take first 100 (newest)
            
            # Update counters
            self.total_trades = len(self.trades)
            
            # Calculate today's trades
            today = datetime.now().date()
            self.today_trades = sum(1 for trade in self.trades if trade.timestamp.date() == today)
            
            # Calculate initial capital (cost basis) = cash + sum(cost of all positions)
            total_position_cost = 0.0
            for position in positions:
                if position.get('status') == 'OPEN':
                    quantity = float(position.get('quantity', 0))
                    entry_price = float(position.get('average_price', 0))
                    total_position_cost += quantity * entry_price
            
            # Initial capital is what we actually paid
            calculated_initial_capital = self.cash_balance + total_position_cost
            
            # Set initial capital on first fetch, or update if it changed significantly
            if self.initial_capital == 0.0:
                self.initial_capital = calculated_initial_capital
                self.peak_value = self.equity
            
            # Calculate total P&L: current equity - initial capital (cost basis)
            self.total_pnl = self.equity - calculated_initial_capital
            
            # Calculate today's P&L from closed trades
            self.today_pnl = sum(trade.pnl for trade in self.trades if trade.timestamp.date() == today)
            
            # Update peak value and drawdown
            if self.current_value > self.peak_value:
                self.peak_value = self.current_value
            
            current_drawdown = (self.peak_value - self.current_value) / self.peak_value if self.peak_value > 0 else 0
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # Update strategy performance
            self._update_strategy_performance()
            
            self.last_update = datetime.now()
            
            logger.info(f"📊 Updated from API: {self.total_trades} trades, {len(positions)} positions, P&L: ${self.total_pnl:.2f}")
            
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
            'equity': self.equity,
            'buying_power': self.buying_power,
            'cash_balance': self.cash_balance,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': (self.total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'today_trades': self.today_trades,
            'today_pnl': self.today_pnl,
            'strategies': list(self.strategy_performance.keys()),
            'recent_trades': [trade.__dict__ for trade in list(self.recent_trades)[:10]],  # First 10 (newest)
            'last_update': self.last_update.isoformat(),
            'live_service_url': self.live_service_url
        }
    
    def print_status(self):
        """Print current status"""
        status = self.get_status()
        
        # Calculate position cost for display
        total_position_cost = 0.0
        total_position_value = 0.0
        for pos in self.last_positions:
            if pos.get('status') == 'OPEN':
                qty = float(pos.get('quantity', 0))
                avg_price = float(pos.get('average_price', 0))
                current_price = float(pos.get('current_price', avg_price))
                total_position_cost += qty * avg_price
                total_position_value += qty * current_price
        
        print(f"\n📊 Live Trading Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"💰 Account Balance (Equity): ${self.equity:,.2f}")
        print(f"💵 Cash Balance: ${self.cash_balance:,.2f}")
        print(f"💼 Position Cost Basis: ${total_position_cost:,.2f}")
        print(f"📈 Position Market Value: ${total_position_value:,.2f}")
        print(f"💵 Buying Power: ${self.buying_power:,.2f}")
        print(f"📊 Total P&L: ${status['total_pnl']:,.2f} ({status['total_pnl_percent']:+.2f}%)")
        print(f"📉 Max Drawdown: {status['max_drawdown']:.2%}")
        print(f"📈 Total Filled Trades: {status['total_trades']}")
        print(f"📅 Today's Trades: {status['today_trades']}")
        print(f"📊 Today's P&L: ${status['today_pnl']:,.2f}")
        
        # Show position details if available
        if hasattr(self, 'last_positions') and self.last_positions:
            print(f"\n💼 Current Positions ({len(self.last_positions)}):")
            for pos in self.last_positions:
                if pos.get('status') == 'OPEN':
                    symbol = pos.get('symbol', 'N/A')
                    qty = pos.get('quantity', 0)
                    avg_price = pos.get('average_price', 0)
                    current_price = pos.get('current_price', avg_price)
                    unrealized_pnl = pos.get('unrealized_pnl', 0)
                    
                    print(f"  {symbol}: {qty} shares @ ${avg_price:.2f} (Current: ${current_price:.2f}, P&L: ${unrealized_pnl:.2f})")
                    
                    # Show exit strategy if available
                    if pos.get('exit_strategy'):
                        exit_strategy = pos['exit_strategy']
                        print(f"    🎯 Exit Strategy:")
                        print(f"       • Max Hold: {exit_strategy.get('max_holding_days', 'N/A')} days")
                        print(f"       • Profit Target: {exit_strategy.get('profit_target_pct', 'N/A'):.1%}" if isinstance(exit_strategy.get('profit_target_pct'), (int, float)) else f"       • Profit Target: {exit_strategy.get('profit_target_pct', 'N/A')}")
                        print(f"       • Stop Loss: {exit_strategy.get('stop_loss_pct', 'N/A'):.1%}" if isinstance(exit_strategy.get('stop_loss_pct'), (int, float)) else f"       • Stop Loss: {exit_strategy.get('stop_loss_pct', 'N/A')}")
                        print(f"       • Min Holding: {exit_strategy.get('min_holding_hours', 'N/A')} hours")
                        
                        # Show anxiety-reducing message
                        if exit_strategy.get('anxiety_reduction_message'):
                            print(f"    🛡️  Protection:")
                            for line in exit_strategy['anxiety_reduction_message'].split('\n'):
                                if line.strip():
                                    print(f"       {line}")
                        
                        # Show closest exit condition
                        if exit_strategy.get('closest_exit'):
                            closest = exit_strategy['closest_exit']
                            print(f"    ⏰ Closest Exit: {closest.get('description', 'Unknown')}")
                    else:
                        # Show default exit strategy
                        print(f"    🎯 Exit Strategy:")
                        print(f"       • Max Hold: 30 days")
                        print(f"       • Profit Target: 15.0%")
                        print(f"       • Stop Loss: 8.0%")
                        print(f"       • Min Holding: 4 hours")
                        print(f"    🛡️  Protection:")
                        print(f"       Your position is protected by automatic exit strategies")
                        print(f"       Risk is limited to 8% stop loss per position")
        
        print(f"\n🔗 Data Source: Live Trading Service API ({status['live_service_url']})")
        print(f"🕒 Last Update: {status['last_update']}")
        
        if status['strategies']:
            print(f"\n📊 Strategy Performance:")
            for strategy_name in status['strategies']:
                strategy = self.strategy_performance[strategy_name]
                print(f"  {strategy_name}:")
                print(f"    Trades: {strategy.total_trades} | Win Rate: {strategy.win_rate:.1%}")
                print(f"    P&L: ${strategy.total_pnl:.2f} | Avg Win: ${strategy.avg_win:.2f} | Avg Loss: ${strategy.avg_loss:.2f}")
        
        # Show rejected trade attempts if any
        if self.rejected_attempts:
            print(f"\n🚫 Recent Rejected Trade Attempts ({len(self.rejected_attempts)}):")
            
            # Import Mountain timezone
            import pytz
            mountain_tz = pytz.timezone('America/Denver')
            
            # Show up to 10 most recent rejections
            for attempt in self.rejected_attempts[:10]:
                try:
                    from datetime import timezone
                    attempt_time = datetime.fromisoformat(attempt['created_at'].replace('Z', '+00:00'))
                    
                    # Ensure it has timezone info (assume UTC if not)
                    if attempt_time.tzinfo is None:
                        attempt_time = attempt_time.replace(tzinfo=timezone.utc)
                    
                    # Convert to Mountain Time (MST/MDT)
                    attempt_time = attempt_time.astimezone(mountain_tz)
                    
                    # Get timezone name (will show MST or MDT depending on daylight saving)
                    tz_name = attempt_time.strftime('%Z')  # MST or MDT
                    time_str = f"{attempt_time.strftime('%H:%M:%S')} {tz_name}"
                    
                    symbol = attempt['symbol']
                    action = attempt['action']
                    strategy = attempt['strategy']
                    rejection_reason = attempt['rejection_reason']
                    rejection_category = attempt['rejection_category']
                    confidence_score = attempt.get('confidence_score')
                    
                    # Choose icon based on rejection category
                    if rejection_category == "BUYING_POWER":
                        icon = "💸"
                    elif rejection_category == "RISK":
                        icon = "⚠️"
                    elif rejection_category == "CONFIDENCE":
                        icon = "📉"
                    elif rejection_category == "POSITION_EXISTS":
                        icon = "🔄"
                    elif rejection_category == "VALIDATION":
                        icon = "❌"
                    else:
                        icon = "🚫"
                    
                    # Build display string
                    confidence_str = f" (confidence: {confidence_score:.2f})" if confidence_score else ""
                    
                    print(f"  {icon} {time_str} | {symbol} | {strategy} | {action}{confidence_str}")
                    print(f"     Reason: {rejection_reason}")
                    
                except Exception as e:
                    logger.error(f"Error displaying rejected attempt: {e}")
        
        if status['recent_trades']:
            print(f"\n📈 Recent Trades:")
            
            # Import Mountain timezone
            import pytz
            mountain_tz = pytz.timezone('America/Denver')
            
            for trade in status['recent_trades'][:5]:  # Show first 5 (newest) trades
                if isinstance(trade['timestamp'], str):
                    from datetime import timezone
                    trade_time = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                    # Ensure it has timezone info (assume UTC if not)
                    if trade_time.tzinfo is None:
                        trade_time = trade_time.replace(tzinfo=timezone.utc)
                else:
                    trade_time = trade['timestamp']
                
                # Convert to Mountain Time (MST/MDT)
                if trade_time.tzinfo is not None:
                    trade_time = trade_time.astimezone(mountain_tz)
                
                # Show trade with status indicator
                order_status = trade.get('status', 'UNKNOWN')
                rejection_reason = trade.get('rejection_reason')
                
                # Determine status icon - check for rejection reasons
                if order_status == 'FILLED':
                    status_icon = "✅"
                elif rejection_reason:
                    # Has rejection reason - show as failed
                    status_icon = "🚫"
                elif order_status in ['PENDING', 'SUBMITTED']:
                    status_icon = "⏳"
                elif order_status == 'CANCELLED':
                    status_icon = "❌"
                else:
                    status_icon = "❓"
                
                # Build trade description
                symbol_display = trade['symbol']
                option_type = trade.get('option_type')
                strike_price = trade.get('strike_price')
                expiration_date = trade.get('expiration_date')
                
                # Check if it's an option trade
                if option_type and strike_price:
                    # Format expiration date
                    if expiration_date:
                        try:
                            exp_dt = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                            exp_str = exp_dt.strftime('%m/%d/%y')
                        except:
                            exp_str = expiration_date[:10] if len(expiration_date) >= 10 else expiration_date
                    else:
                        exp_str = "??/??/??"
                    
                    # Format as: SYMBOL $STRIKE CALL/PUT EXP
                    symbol_display = f"📊 {symbol_display} ${strike_price:.0f} {option_type} {exp_str}"
                else:
                    # Stock trade
                    symbol_display = f"📈 {symbol_display}"
                
                # Build status display with rejection reason if present
                if rejection_reason:
                    # Extract key error message from rejection reason
                    error_msg = rejection_reason
                    # Try to extract the message part if it's JSON-like
                    if '"message"' in error_msg:
                        import re
                        match = re.search(r'"message":"([^"]+)"', error_msg)
                        if match:
                            error_msg = match.group(1)
                    # Truncate if too long
                    if len(error_msg) > 60:
                        error_msg = error_msg[:57] + "..."
                    status_display = f"FAILED: {error_msg}"
                else:
                    status_display = f"Status: {order_status}"
                
                # Format time with Mountain timezone indicator
                if trade_time.tzinfo:
                    # Get timezone name (will show MST or MDT depending on daylight saving)
                    tz_name = trade_time.strftime('%Z')  # MST or MDT
                    time_str = f"{trade_time.strftime('%H:%M:%S')} {tz_name}"
                else:
                    time_str = trade_time.strftime('%H:%M:%S')
                
                print(f"  {status_icon} {time_str} | {symbol_display} | {trade['strategy']} | "
                      f"{trade['quantity']} @ ${trade['price']:.2f} | {status_display}")
    
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






