"""
Prometheus Metrics for Risk Management

Prometheus metrics collection for the comprehensive risk management framework.
Provides detailed metrics for monitoring risk calculations, performance, and system health.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import wraps
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.core import REGISTRY

logger = logging.getLogger(__name__)


class RiskMetrics:
    """Risk management metrics collector."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize risk metrics collector.
        
        Args:
            registry: Optional Prometheus registry (uses default if None)
        """
        self.registry = registry or REGISTRY
        
        # Initialize metrics
        self._initialize_metrics()
    
    def _initialize_metrics(self) -> None:
        """Initialize all Prometheus metrics."""
        
        # Risk calculation metrics
        self.var_calculations_total = Counter(
            'risk_var_calculations_total',
            'Total number of VaR calculations',
            ['portfolio_id', 'method', 'confidence_level', 'status']
        )
        
        self.var_calculation_duration = Histogram(
            'risk_var_calculation_duration_seconds',
            'Duration of VaR calculations',
            ['portfolio_id', 'method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.var_values = Gauge(
            'risk_var_values',
            'Current VaR values',
            ['portfolio_id', 'confidence_level']
        )
        
        self.expected_shortfall_values = Gauge(
            'risk_expected_shortfall_values',
            'Current Expected Shortfall values',
            ['portfolio_id', 'confidence_level']
        )
        
        # Stress testing metrics
        self.stress_tests_total = Counter(
            'risk_stress_tests_total',
            'Total number of stress tests',
            ['portfolio_id', 'scenario', 'status']
        )
        
        self.stress_test_duration = Histogram(
            'risk_stress_test_duration_seconds',
            'Duration of stress tests',
            ['portfolio_id', 'scenario'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.stress_test_results = Gauge(
            'risk_stress_test_results',
            'Stress test results',
            ['portfolio_id', 'scenario', 'metric']
        )
        
        # Correlation analysis metrics
        self.correlation_analyses_total = Counter(
            'risk_correlation_analyses_total',
            'Total number of correlation analyses',
            ['portfolio_id', 'status']
        )
        
        self.correlation_analysis_duration = Histogram(
            'risk_correlation_analysis_duration_seconds',
            'Duration of correlation analyses',
            ['portfolio_id'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.correlation_matrix_size = Gauge(
            'risk_correlation_matrix_size',
            'Size of correlation matrix',
            ['portfolio_id']
        )
        
        # Risk monitoring metrics
        self.risk_checks_total = Counter(
            'risk_checks_total',
            'Total number of risk checks',
            ['portfolio_id', 'check_type', 'status']
        )
        
        self.risk_limits_breached = Counter(
            'risk_limits_breached_total',
            'Total number of risk limit breaches',
            ['portfolio_id', 'limit_type', 'severity']
        )
        
        self.risk_alerts_active = Gauge(
            'risk_alerts_active',
            'Number of active risk alerts',
            ['portfolio_id', 'severity']
        )
        
        self.risk_monitoring_duration = Histogram(
            'risk_monitoring_duration_seconds',
            'Duration of risk monitoring cycles',
            ['portfolio_id'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        # Portfolio metrics
        self.portfolio_risk_metrics = Gauge(
            'risk_portfolio_risk_metrics',
            'Portfolio risk metrics',
            ['portfolio_id', 'metric_type']
        )
        
        self.portfolio_positions_count = Gauge(
            'risk_portfolio_positions_count',
            'Number of positions in portfolio',
            ['portfolio_id']
        )
        
        self.portfolio_total_value = Gauge(
            'risk_portfolio_total_value',
            'Total portfolio value',
            ['portfolio_id']
        )
        
        self.portfolio_cash_ratio = Gauge(
            'risk_portfolio_cash_ratio',
            'Cash ratio in portfolio',
            ['portfolio_id']
        )
        
        # Integration metrics
        self.integration_requests_total = Counter(
            'risk_integration_requests_total',
            'Total integration requests',
            ['service', 'endpoint', 'status']
        )
        
        self.integration_request_duration = Histogram(
            'risk_integration_request_duration_seconds',
            'Duration of integration requests',
            ['service', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.integration_errors_total = Counter(
            'risk_integration_errors_total',
            'Total integration errors',
            ['service', 'endpoint', 'error_type']
        )
        
        # Data synchronization metrics
        self.sync_operations_total = Counter(
            'risk_sync_operations_total',
            'Total synchronization operations',
            ['service', 'operation_type', 'status']
        )
        
        self.sync_duration = Histogram(
            'risk_sync_duration_seconds',
            'Duration of synchronization operations',
            ['service', 'operation_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.sync_records_processed = Counter(
            'risk_sync_records_processed_total',
            'Total records processed in sync operations',
            ['service', 'operation_type']
        )
        
        # System health metrics
        self.system_health = Gauge(
            'risk_system_health',
            'System health status',
            ['component']
        )
        
        self.database_connections_active = Gauge(
            'risk_database_connections_active',
            'Active database connections',
            ['database']
        )
        
        self.cache_hit_ratio = Gauge(
            'risk_cache_hit_ratio',
            'Cache hit ratio',
            ['cache_type']
        )
        
        self.memory_usage = Gauge(
            'risk_memory_usage_bytes',
            'Memory usage in bytes',
            ['component']
        )
        
        # API metrics
        self.api_requests_total = Counter(
            'risk_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status']
        )
        
        self.api_request_duration = Histogram(
            'risk_api_request_duration_seconds',
            'Duration of API requests',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.api_errors_total = Counter(
            'risk_api_errors_total',
            'Total API errors',
            ['method', 'endpoint', 'error_type']
        )
        
        # Performance metrics
        self.calculation_queue_size = Gauge(
            'risk_calculation_queue_size',
            'Size of calculation queue',
            ['calculation_type']
        )
        
        self.calculation_throughput = Summary(
            'risk_calculation_throughput_seconds',
            'Calculation throughput',
            ['calculation_type']
        )
        
        # Service info
        self.service_info = Info(
            'risk_service_info',
            'Risk management service information'
        )
        
        # Set service info
        self.service_info.info({
            'version': '1.0.0',
            'build_date': datetime.utcnow().isoformat(),
            'component': 'risk-management'
        })
    
    def record_var_calculation(
        self,
        portfolio_id: str,
        method: str,
        confidence_level: float,
        duration: float,
        status: str,
        var_value: Optional[float] = None,
        expected_shortfall: Optional[float] = None
    ) -> None:
        """
        Record VaR calculation metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            method: Calculation method
            confidence_level: Confidence level
            duration: Calculation duration
            status: Calculation status
            var_value: Calculated VaR value
            expected_shortfall: Calculated expected shortfall
        """
        self.var_calculations_total.labels(
            portfolio_id=portfolio_id,
            method=method,
            confidence_level=str(confidence_level),
            status=status
        ).inc()
        
        self.var_calculation_duration.labels(
            portfolio_id=portfolio_id,
            method=method
        ).observe(duration)
        
        if var_value is not None:
            self.var_values.labels(
                portfolio_id=portfolio_id,
                confidence_level=str(confidence_level)
            ).set(var_value)
        
        if expected_shortfall is not None:
            self.expected_shortfall_values.labels(
                portfolio_id=portfolio_id,
                confidence_level=str(confidence_level)
            ).set(expected_shortfall)
    
    def record_stress_test(
        self,
        portfolio_id: str,
        scenario: str,
        duration: float,
        status: str,
        results: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Record stress test metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            scenario: Stress test scenario
            duration: Test duration
            status: Test status
            results: Test results
        """
        self.stress_tests_total.labels(
            portfolio_id=portfolio_id,
            scenario=scenario,
            status=status
        ).inc()
        
        self.stress_test_duration.labels(
            portfolio_id=portfolio_id,
            scenario=scenario
        ).observe(duration)
        
        if results:
            for metric, value in results.items():
                self.stress_test_results.labels(
                    portfolio_id=portfolio_id,
                    scenario=scenario,
                    metric=metric
                ).set(value)
    
    def record_correlation_analysis(
        self,
        portfolio_id: str,
        duration: float,
        status: str,
        matrix_size: Optional[int] = None
    ) -> None:
        """
        Record correlation analysis metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            duration: Analysis duration
            status: Analysis status
            matrix_size: Size of correlation matrix
        """
        self.correlation_analyses_total.labels(
            portfolio_id=portfolio_id,
            status=status
        ).inc()
        
        self.correlation_analysis_duration.labels(
            portfolio_id=portfolio_id
        ).observe(duration)
        
        if matrix_size is not None:
            self.correlation_matrix_size.labels(
                portfolio_id=portfolio_id
            ).set(matrix_size)
    
    def record_risk_check(
        self,
        portfolio_id: str,
        check_type: str,
        status: str,
        duration: float
    ) -> None:
        """
        Record risk check metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            check_type: Type of risk check
            status: Check status
            duration: Check duration
        """
        self.risk_checks_total.labels(
            portfolio_id=portfolio_id,
            check_type=check_type,
            status=status
        ).inc()
        
        self.risk_monitoring_duration.labels(
            portfolio_id=portfolio_id
        ).observe(duration)
    
    def record_risk_limit_breach(
        self,
        portfolio_id: str,
        limit_type: str,
        severity: str
    ) -> None:
        """
        Record risk limit breach.
        
        Args:
            portfolio_id: Portfolio identifier
            limit_type: Type of limit breached
            severity: Breach severity
        """
        self.risk_limits_breached.labels(
            portfolio_id=portfolio_id,
            limit_type=limit_type,
            severity=severity
        ).inc()
    
    def update_risk_alerts(
        self,
        portfolio_id: str,
        severity_counts: Dict[str, int]
    ) -> None:
        """
        Update risk alert metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            severity_counts: Count of alerts by severity
        """
        for severity, count in severity_counts.items():
            self.risk_alerts_active.labels(
                portfolio_id=portfolio_id,
                severity=severity
            ).set(count)
    
    def update_portfolio_metrics(
        self,
        portfolio_id: str,
        total_value: float,
        positions_count: int,
        cash_ratio: float,
        risk_metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Update portfolio metrics.
        
        Args:
            portfolio_id: Portfolio identifier
            total_value: Total portfolio value
            positions_count: Number of positions
            cash_ratio: Cash ratio
            risk_metrics: Additional risk metrics
        """
        self.portfolio_total_value.labels(
            portfolio_id=portfolio_id
        ).set(total_value)
        
        self.portfolio_positions_count.labels(
            portfolio_id=portfolio_id
        ).set(positions_count)
        
        self.portfolio_cash_ratio.labels(
            portfolio_id=portfolio_id
        ).set(cash_ratio)
        
        if risk_metrics:
            for metric_type, value in risk_metrics.items():
                self.portfolio_risk_metrics.labels(
                    portfolio_id=portfolio_id,
                    metric_type=metric_type
                ).set(value)
    
    def record_integration_request(
        self,
        service: str,
        endpoint: str,
        duration: float,
        status: str,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record integration request metrics.
        
        Args:
            service: Service name
            endpoint: API endpoint
            duration: Request duration
            status: Request status
            error_type: Error type if failed
        """
        self.integration_requests_total.labels(
            service=service,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.integration_request_duration.labels(
            service=service,
            endpoint=endpoint
        ).observe(duration)
        
        if error_type:
            self.integration_errors_total.labels(
                service=service,
                endpoint=endpoint,
                error_type=error_type
            ).inc()
    
    def record_sync_operation(
        self,
        service: str,
        operation_type: str,
        duration: float,
        status: str,
        records_processed: int
    ) -> None:
        """
        Record synchronization operation metrics.
        
        Args:
            service: Service name
            operation_type: Type of sync operation
            duration: Operation duration
            status: Operation status
            records_processed: Number of records processed
        """
        self.sync_operations_total.labels(
            service=service,
            operation_type=operation_type,
            status=status
        ).inc()
        
        self.sync_duration.labels(
            service=service,
            operation_type=operation_type
        ).observe(duration)
        
        self.sync_records_processed.labels(
            service=service,
            operation_type=operation_type
        ).inc(records_processed)
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status: str,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record API request metrics.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            duration: Request duration
            status: Request status
            error_type: Error type if failed
        """
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if error_type:
            self.api_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type
            ).inc()
    
    def update_system_health(
        self,
        component: str,
        health_status: float
    ) -> None:
        """
        Update system health metrics.
        
        Args:
            component: Component name
            health_status: Health status (1.0 = healthy, 0.0 = unhealthy)
        """
        self.system_health.labels(
            component=component
        ).set(health_status)
    
    def update_database_connections(
        self,
        database: str,
        active_connections: int
    ) -> None:
        """
        Update database connection metrics.
        
        Args:
            database: Database name
            active_connections: Number of active connections
        """
        self.database_connections_active.labels(
            database=database
        ).set(active_connections)
    
    def update_cache_metrics(
        self,
        cache_type: str,
        hit_ratio: float
    ) -> None:
        """
        Update cache metrics.
        
        Args:
            cache_type: Cache type
            hit_ratio: Cache hit ratio
        """
        self.cache_hit_ratio.labels(
            cache_type=cache_type
        ).set(hit_ratio)
    
    def update_memory_usage(
        self,
        component: str,
        memory_bytes: int
    ) -> None:
        """
        Update memory usage metrics.
        
        Args:
            component: Component name
            memory_bytes: Memory usage in bytes
        """
        self.memory_usage.labels(
            component=component
        ).set(memory_bytes)
    
    def update_calculation_queue(
        self,
        calculation_type: str,
        queue_size: int
    ) -> None:
        """
        Update calculation queue metrics.
        
        Args:
            calculation_type: Type of calculation
            queue_size: Queue size
        """
        self.calculation_queue_size.labels(
            calculation_type=calculation_type
        ).set(queue_size)
    
    def record_calculation_throughput(
        self,
        calculation_type: str,
        duration: float
    ) -> None:
        """
        Record calculation throughput.
        
        Args:
            calculation_type: Type of calculation
            duration: Calculation duration
        """
        self.calculation_throughput.labels(
            calculation_type=calculation_type
        ).observe(duration)


# Global metrics instance
_metrics = None


def get_metrics() -> RiskMetrics:
    """Get global risk metrics instance."""
    global _metrics
    
    if _metrics is None:
        _metrics = RiskMetrics()
    
    return _metrics


def initialize_metrics(registry: Optional[CollectorRegistry] = None) -> RiskMetrics:
    """Initialize risk metrics."""
    global _metrics
    
    _metrics = RiskMetrics(registry)
    return _metrics


def get_metrics_output() -> str:
    """Get Prometheus metrics output."""
    return generate_latest(REGISTRY).decode('utf-8')


# Metrics decorators
def record_calculation_metrics(calculation_type: str, portfolio_id: str = None):
    """Decorator to record calculation metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics
                if hasattr(result, 'var_value'):
                    metrics.record_var_calculation(
                        portfolio_id=portfolio_id or 'unknown',
                        method=calculation_type,
                        confidence_level=0.95,  # Default
                        duration=duration,
                        status='success',
                        var_value=getattr(result, 'var_value', None),
                        expected_shortfall=getattr(result, 'expected_shortfall', None)
                    )
                else:
                    metrics.record_calculation_throughput(calculation_type, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                if calculation_type == 'var_calculation':
                    metrics.record_var_calculation(
                        portfolio_id=portfolio_id or 'unknown',
                        method=calculation_type,
                        confidence_level=0.95,
                        duration=duration,
                        status='error'
                    )
                else:
                    metrics.record_calculation_throughput(calculation_type, duration)
                
                raise
        
        return wrapper
    return decorator


def record_api_metrics(method: str, endpoint: str):
    """Decorator to record API metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.record_api_request(
                    method=method,
                    endpoint=endpoint,
                    duration=duration,
                    status='success'
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                metrics.record_api_request(
                    method=method,
                    endpoint=endpoint,
                    duration=duration,
                    status='error',
                    error_type=type(e).__name__
                )
                
                raise
        
        return wrapper
    return decorator


def record_integration_metrics(service: str, endpoint: str):
    """Decorator to record integration metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.record_integration_request(
                    service=service,
                    endpoint=endpoint,
                    duration=duration,
                    status='success'
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                metrics.record_integration_request(
                    service=service,
                    endpoint=endpoint,
                    duration=duration,
                    status='error',
                    error_type=type(e).__name__
                )
                
                raise
        
        return wrapper
    return decorator
























