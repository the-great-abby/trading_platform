"""
Logging and Metrics Service

Handles structured logging and metrics collection for the live trading system.
"""

import asyncio
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import structlog

logger = logging.getLogger(__name__)


@dataclass
class LoggingConfig:
    """Configuration for logging service."""
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5
    enable_console: bool = True
    enable_metrics: bool = True
    metrics_port: int = 8081


@dataclass
class TradeEvent:
    """Trade event for structured logging."""
    event_type: str
    account_id: str
    trade_id: Optional[str] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RiskEvent:
    """Risk event for structured logging."""
    event_type: str
    account_id: str
    risk_type: str
    risk_level: str
    value: Optional[float] = None
    limit: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class LoggingService:
    """Service for structured logging and metrics collection."""
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """Initialize the logging service."""
        self.config = config or LoggingConfig()
        self.metrics_enabled = self.config.enable_metrics
        
        # Prometheus metrics
        if self.metrics_enabled:
            self._init_metrics()
        
        # Structured logger
        self._init_structured_logger()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Trade metrics
        self.trade_counter = Counter(
            'live_trading_trades_total',
            'Total number of trades executed',
            ['account_id', 'symbol', 'strategy', 'status']
        )
        
        self.trade_value_histogram = Histogram(
            'live_trading_trade_value_usd',
            'Trade value in USD',
            ['account_id', 'symbol', 'strategy'],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
        )
        
        self.trade_duration_histogram = Histogram(
            'live_trading_trade_duration_seconds',
            'Time taken to execute trades',
            ['account_id', 'symbol', 'strategy'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        # Risk metrics
        self.risk_violation_counter = Counter(
            'live_trading_risk_violations_total',
            'Total number of risk violations',
            ['account_id', 'risk_type', 'severity']
        )
        
        self.risk_exposure_gauge = Gauge(
            'live_trading_risk_exposure_usd',
            'Current risk exposure in USD',
            ['account_id', 'risk_type']
        )
        
        # API metrics
        self.api_request_counter = Counter(
            'live_trading_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'live_trading_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # System metrics
        self.active_connections_gauge = Gauge(
            'live_trading_active_connections',
            'Number of active connections'
        )
        
        self.emergency_stops_counter = Counter(
            'live_trading_emergency_stops_total',
            'Total number of emergency stops',
            ['account_id', 'reason']
        )
        
        # Portfolio metrics
        self.portfolio_value_gauge = Gauge(
            'live_trading_portfolio_value_usd',
            'Current portfolio value in USD',
            ['account_id']
        )
        
        self.portfolio_pnl_gauge = Gauge(
            'live_trading_portfolio_pnl_usd',
            'Current portfolio P&L in USD',
            ['account_id']
        )
        
        logger.info("Prometheus metrics initialized")
    
    def _init_structured_logger(self):
        """Initialize structured logger."""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logger
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Create logger
        self.logger = structlog.get_logger("live_trading")
        
        # Set up handlers
        handlers = []
        
        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            handlers.append(console_handler)
        
        if self.config.log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.log_file,
                maxBytes=self._parse_size(self.config.max_file_size),
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(log_level)
            handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        for handler in handlers:
            if self.config.log_format == "json":
                handler.setFormatter(logging.Formatter(
                    '%(message)s'  # JSON format from structlog
                ))
            else:
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            root_logger.addHandler(handler)
        
        logger.info("Structured logging initialized")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def log_trade_event(self, event: TradeEvent):
        """Log a trade event."""
        try:
            # Convert to dict for logging
            event_dict = asdict(event)
            if event.timestamp is None:
                event_dict['timestamp'] = datetime.utcnow().isoformat()
            else:
                event_dict['timestamp'] = event.timestamp.isoformat()
            
            # Log with structured logger
            self.logger.info(
                "Trade event",
                **event_dict
            )
            
            # Update metrics
            if self.metrics_enabled:
                self.trade_counter.labels(
                    account_id=event.account_id,
                    symbol=event.symbol or "unknown",
                    strategy=event.strategy or "unknown",
                    status=event.status or "unknown"
                ).inc()
                
                if event.price and event.quantity:
                    trade_value = event.price * event.quantity
                    self.trade_value_histogram.labels(
                        account_id=event.account_id,
                        symbol=event.symbol or "unknown",
                        strategy=event.strategy or "unknown"
                    ).observe(trade_value)
            
        except Exception as e:
            logger.error(f"Error logging trade event: {str(e)}")
    
    def log_risk_event(self, event: RiskEvent):
        """Log a risk event."""
        try:
            # Convert to dict for logging
            event_dict = asdict(event)
            if event.timestamp is None:
                event_dict['timestamp'] = datetime.utcnow().isoformat()
            else:
                event_dict['timestamp'] = event.timestamp.isoformat()
            
            # Log with structured logger
            self.logger.warning(
                "Risk event",
                **event_dict
            )
            
            # Update metrics
            if self.metrics_enabled:
                self.risk_violation_counter.labels(
                    account_id=event.account_id,
                    risk_type=event.risk_type,
                    severity=event.risk_level
                ).inc()
                
                if event.value is not None:
                    self.risk_exposure_gauge.labels(
                        account_id=event.account_id,
                        risk_type=event.risk_type
                    ).set(event.value)
            
        except Exception as e:
            logger.error(f"Error logging risk event: {str(e)}")
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log an API request."""
        try:
            self.logger.info(
                "API request",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_seconds=duration
            )
            
            # Update metrics
            if self.metrics_enabled:
                self.api_request_counter.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
                
                self.api_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
            
        except Exception as e:
            logger.error(f"Error logging API request: {str(e)}")
    
    def log_emergency_stop(self, account_id: str, reason: str):
        """Log an emergency stop event."""
        try:
            self.logger.critical(
                "Emergency stop activated",
                account_id=account_id,
                reason=reason,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Update metrics
            if self.metrics_enabled:
                self.emergency_stops_counter.labels(
                    account_id=account_id,
                    reason=reason
                ).inc()
            
        except Exception as e:
            logger.error(f"Error logging emergency stop: {str(e)}")
    
    def update_portfolio_metrics(self, account_id: str, portfolio_value: float, pnl: float):
        """Update portfolio metrics."""
        try:
            if self.metrics_enabled:
                self.portfolio_value_gauge.labels(account_id=account_id).set(portfolio_value)
                self.portfolio_pnl_gauge.labels(account_id=account_id).set(pnl)
        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {str(e)}")
    
    def update_connection_metrics(self, active_connections: int):
        """Update connection metrics."""
        try:
            if self.metrics_enabled:
                self.active_connections_gauge.set(active_connections)
        except Exception as e:
            logger.error(f"Error updating connection metrics: {str(e)}")
    
    def start_metrics_server(self):
        """Start Prometheus metrics server."""
        try:
            if self.metrics_enabled:
                start_http_server(self.config.metrics_port)
                logger.info(f"Prometheus metrics server started on port {self.config.metrics_port}")
        except Exception as e:
            logger.error(f"Error starting metrics server: {str(e)}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        try:
            if not self.metrics_enabled:
                return {"metrics_enabled": False}
            
            # This would typically query the metrics endpoint
            # For now, return a basic summary
            return {
                "metrics_enabled": True,
                "metrics_port": self.config.metrics_port,
                "available_metrics": [
                    "live_trading_trades_total",
                    "live_trading_trade_value_usd",
                    "live_trading_trade_duration_seconds",
                    "live_trading_risk_violations_total",
                    "live_trading_risk_exposure_usd",
                    "live_trading_api_requests_total",
                    "live_trading_api_request_duration_seconds",
                    "live_trading_active_connections",
                    "live_trading_emergency_stops_total",
                    "live_trading_portfolio_value_usd",
                    "live_trading_portfolio_pnl_usd"
                ]
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {str(e)}")
            return {"error": str(e)}
    
    def log_system_event(self, event_type: str, message: str, **kwargs):
        """Log a system event."""
        try:
            self.logger.info(
                "System event",
                event_type=event_type,
                message=message,
                timestamp=datetime.utcnow().isoformat(),
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log an error with context."""
        try:
            error_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if context:
                error_data.update(context)
            
            self.logger.error(
                "Error occurred",
                **error_data,
                exc_info=True
            )
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
    
    def log_performance_metric(self, metric_name: str, value: float, **labels):
        """Log a performance metric."""
        try:
            self.logger.info(
                "Performance metric",
                metric_name=metric_name,
                value=value,
                timestamp=datetime.utcnow().isoformat(),
                **labels
            )
        except Exception as e:
            logger.error(f"Error logging performance metric: {str(e)}")
