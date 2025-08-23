#!/usr/bin/env python3
"""
Trading Engine Metrics - Real Trading Data for Prometheus
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry
from datetime import datetime
import json
from typing import Dict, Any

class TradingEngineMetrics:
    """Real trading metrics for Prometheus"""
    
    def __init__(self):
        # Create a custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Trading performance metrics
        self.trades_total = Counter(
            'trading_trades_total',
            'Total number of trades executed',
            ['symbol', 'action', 'strategy', 'status'],
            registry=self.registry
        )
        
        self.trades_value_total = Counter(
            'trading_trades_value_total', 
            'Total value of all trades',
            ['symbol', 'action', 'strategy'],
            registry=self.registry
        )
        
        self.pnl_total = Gauge(
            'trading_pnl_total',
            'Total profit/loss across all positions',
            registry=self.registry
        )
        
        self.daily_pnl = Gauge(
            'trading_daily_pnl',
            'Daily profit/loss',
            registry=self.registry
        )
        
        self.active_positions = Gauge(
            'trading_active_positions',
            'Number of currently active positions',
            registry=self.registry
        )
        
        self.portfolio_value = Gauge(
            'trading_portfolio_value',
            'Current total portfolio value',
            registry=self.registry
        )
        
        # Win/Loss tracking
        self.win_count = Counter(
            'trading_win_count',
            'Number of winning trades',
            ['symbol', 'strategy'],
            registry=self.registry
        )
        
        self.loss_count = Counter(
            'trading_loss_count', 
            'Number of losing trades',
            ['symbol', 'strategy'],
            registry=self.registry
        )
        
        # Performance ratios
        self.win_rate = Gauge(
            'trading_win_rate',
            'Current win rate percentage',
            registry=self.registry
        )
        
        self.sharpe_ratio = Gauge(
            'trading_sharpe_ratio',
            'Sharpe ratio of trading performance',
            registry=self.registry
        )
        
        self.profit_factor = Gauge(
            'trading_profit_factor',
            'Ratio of gross profit to gross loss', 
            registry=self.registry
        )
        
        self.max_drawdown = Gauge(
            'trading_max_drawdown',
            'Maximum drawdown percentage',
            registry=self.registry
        )
        
        # Order execution metrics
        self.order_latency = Histogram(
            'trading_order_latency_seconds',
            'Order execution latency in seconds',
            ['symbol', 'action'],
            registry=self.registry
        )
        
        # Risk metrics
        self.risk_exposure = Gauge(
            'trading_risk_exposure_total',
            'Total risk exposure',
            registry=self.registry
        )
        
        # Service health
        self.engine_uptime = Gauge(
            'trading_engine_uptime_seconds',
            'Trading engine uptime in seconds',
            registry=self.registry
        )
        
        self.last_trade_timestamp = Gauge(
            'trading_last_trade_timestamp',
            'Timestamp of last executed trade',
            registry=self.registry
        )
        
        # Initialize values
        self.start_time = datetime.utcnow()
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0
        
    def record_trade(self, symbol: str, action: str, quantity: int, price: float, 
                    strategy: str, status: str = 'executed', pnl: float = 0.0):
        """Record a trade execution"""
        trade_value = abs(quantity * price)
        
        # Update counters
        self.trades_total.labels(
            symbol=symbol, 
            action=action, 
            strategy=strategy, 
            status=status
        ).inc()
        
        self.trades_value_total.labels(
            symbol=symbol,
            action=action, 
            strategy=strategy
        ).inc(trade_value)
        
        # Track wins/losses
        if pnl > 0:
            self.win_count.labels(symbol=symbol, strategy=strategy).inc()
            self.total_wins += 1
            self.gross_profit += pnl
        elif pnl < 0:
            self.loss_count.labels(symbol=symbol, strategy=strategy).inc()
            self.total_losses += 1
            self.gross_loss += abs(pnl)
        
        self.total_trades += 1
        self.last_trade_timestamp.set(datetime.utcnow().timestamp())
        
        # Update derived metrics
        self._update_performance_metrics()
        
    def update_portfolio(self, total_value: float, daily_pnl: float, 
                        active_positions_count: int, total_pnl: float):
        """Update portfolio metrics"""
        self.portfolio_value.set(total_value)
        self.daily_pnl.set(daily_pnl)
        self.active_positions.set(active_positions_count)
        self.pnl_total.set(total_pnl)
        
    def update_risk_metrics(self, total_exposure: float, max_drawdown_pct: float):
        """Update risk metrics"""
        self.risk_exposure.set(total_exposure)
        self.max_drawdown.set(max_drawdown_pct)
        
    def _update_performance_metrics(self):
        """Update calculated performance metrics"""
        # Win rate
        if self.total_trades > 0:
            win_rate_pct = (self.total_wins / self.total_trades) * 100
            self.win_rate.set(win_rate_pct)
        
        # Profit factor
        if self.gross_loss > 0:
            profit_factor = self.gross_profit / self.gross_loss
            self.profit_factor.set(profit_factor)
        
        # Uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        self.engine_uptime.set(uptime_seconds)
        
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics text"""
        return generate_latest(self.registry).decode('utf-8')
        
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get trading statistics summary"""
        return {
            'total_trades': self.total_trades,
            'total_wins': self.total_wins,
            'total_losses': self.total_losses,
            'win_rate': (self.total_wins / self.total_trades * 100) if self.total_trades > 0 else 0,
            'gross_profit': self.gross_profit,
            'gross_loss': self.gross_loss,
            'profit_factor': (self.gross_profit / self.gross_loss) if self.gross_loss > 0 else 0,
            'uptime_hours': (datetime.utcnow() - self.start_time).total_seconds() / 3600
        }










