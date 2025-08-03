"""
Market Data Service Metrics
Prometheus metrics for the market data service
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
from typing import Dict, Any

class MarketDataMetrics:
    """Metrics collection for market data service"""
    
    def __init__(self):
        # Data request metrics
        self.data_requests_total = Counter(
            'market_data_requests_total', 
            'Total market data requests', 
            ['symbol', 'data_type', 'status']
        )
        
        self.data_request_latency_seconds = Histogram(
            'market_data_request_latency_seconds',
            'Market data request latency in seconds',
            ['symbol', 'data_type']
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'market_data_cache_hits_total',
            'Total cache hits',
            ['symbol', 'data_type']
        )
        
        self.cache_misses_total = Counter(
            'market_data_cache_misses_total',
            'Total cache misses',
            ['symbol', 'data_type']
        )
        
        self.cache_hit_ratio = Gauge(
            'market_data_cache_hit_ratio',
            'Cache hit ratio (0-1)',
            ['symbol']
        )
        
        # Data quality metrics
        self.data_points_processed_total = Counter(
            'market_data_points_processed_total',
            'Total data points processed',
            ['symbol', 'data_type']
        )
        
        self.data_quality_score = Gauge(
            'market_data_quality_score',
            'Data quality score (0-1)',
            ['symbol']
        )
        
        # Error metrics
        self.data_errors_total = Counter(
            'market_data_errors_total',
            'Total data errors',
            ['error_type', 'symbol']
        )
        
        # Rate limiting metrics
        self.rate_limit_hits_total = Counter(
            'market_data_rate_limit_hits_total',
            'Total rate limit hits',
            ['data_source']
        )
        
        # Service metrics (renamed to avoid conflict)
        self.http_requests_total = Counter(
            'market_data_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration_seconds = Histogram(
            'market_data_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Data source metrics
        self.data_source_health = Gauge(
            'market_data_source_health',
            'Data source health status (1=healthy, 0=unhealthy)',
            ['data_source']
        )
        
        self.data_source_latency_seconds = Histogram(
            'market_data_source_latency_seconds',
            'Data source latency in seconds',
            ['data_source']
        )

# Global metrics instance
market_data_metrics = MarketDataMetrics()

def record_data_request(symbol: str, data_type: str, status: str, duration: float):
    """Record data request metrics"""
    market_data_metrics.data_requests_total.labels(
        symbol=symbol, 
        data_type=data_type, 
        status=status
    ).inc()
    
    market_data_metrics.data_request_latency_seconds.labels(
        symbol=symbol, 
        data_type=data_type
    ).observe(duration)

def record_cache_hit(symbol: str, data_type: str):
    """Record cache hit"""
    market_data_metrics.cache_hits_total.labels(
        symbol=symbol, 
        data_type=data_type
    ).inc()

def record_cache_miss(symbol: str, data_type: str):
    """Record cache miss"""
    market_data_metrics.cache_misses_total.labels(
        symbol=symbol, 
        data_type=data_type
    ).inc()

def update_cache_hit_ratio(symbol: str, hit_ratio: float):
    """Update cache hit ratio"""
    market_data_metrics.cache_hit_ratio.labels(symbol=symbol).set(hit_ratio)

def record_data_points_processed(symbol: str, data_type: str, count: int):
    """Record data points processed"""
    market_data_metrics.data_points_processed_total.labels(
        symbol=symbol, 
        data_type=data_type
    ).inc(count)

def update_data_quality_score(symbol: str, quality_score: float):
    """Update data quality score"""
    market_data_metrics.data_quality_score.labels(symbol=symbol).set(quality_score)

def record_data_error(error_type: str, symbol: str):
    """Record data error"""
    market_data_metrics.data_errors_total.labels(
        error_type=error_type, 
        symbol=symbol
    ).inc()

def record_rate_limit_hit(data_source: str):
    """Record rate limit hit"""
    market_data_metrics.rate_limit_hits_total.labels(data_source=data_source).inc()

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    market_data_metrics.http_requests_total.labels(
        method=method, 
        endpoint=endpoint, 
        status=str(status)
    ).inc()
    
    market_data_metrics.http_request_duration_seconds.labels(
        method=method, 
        endpoint=endpoint
    ).observe(duration)

def update_data_source_health(data_source: str, is_healthy: bool):
    """Update data source health"""
    market_data_metrics.data_source_health.labels(data_source=data_source).set(1 if is_healthy else 0)

def record_data_source_latency(data_source: str, latency: float):
    """Record data source latency"""
    market_data_metrics.data_source_latency_seconds.labels(data_source=data_source).observe(latency) 