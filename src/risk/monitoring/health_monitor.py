"""
Health Monitor for Risk Management Framework

Comprehensive health monitoring and status reporting for the risk management system.
"""

import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..database.connection import health_check as db_health_check
from ..integrations.portfolio_service_integration import get_portfolio_integration
from ..integrations.trading_engine_integration import get_trading_engine_integration
from ..integrations.market_data_service_integration import get_market_data_integration
from ..integrations.data_synchronization_service import get_data_sync_service
from ..integrations.cross_service_monitoring import get_cross_service_monitoring
from .prometheus_metrics import get_metrics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Component health information."""
    name: str
    status: HealthStatus
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SystemHealth:
    """Overall system health information."""
    overall_status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    system_metrics: Dict[str, Any]
    uptime_seconds: float
    version: str = "1.0.0"


class HealthMonitor:
    """Health monitoring system for risk management framework."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.start_time = time.time()
        self.health_history: List[SystemHealth] = []
        self.max_history_size = 100
        
        # Component health checkers
        self.health_checkers = {
            'database': self._check_database_health,
            'portfolio_integration': self._check_portfolio_integration_health,
            'trading_engine_integration': self._check_trading_engine_integration_health,
            'market_data_integration': self._check_market_data_integration_health,
            'data_synchronization': self._check_data_synchronization_health,
            'cross_service_monitoring': self._check_cross_service_monitoring_health,
            'system_resources': self._check_system_resources_health
        }
    
    def get_overall_health(self) -> SystemHealth:
        """
        Get overall system health status.
        
        Returns:
            SystemHealth object with comprehensive health information
        """
        logger.info("Performing comprehensive health check")
        
        components = []
        overall_status = HealthStatus.HEALTHY
        
        # Check each component
        for component_name, checker_func in self.health_checkers.items():
            try:
                component_health = checker_func()
                components.append(component_health)
                
                # Update overall status based on component health
                if component_health.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif component_health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {str(e)}")
                components.append(ComponentHealth(
                    name=component_name,
                    status=HealthStatus.UNKNOWN,
                    last_check=datetime.utcnow(),
                    error_message=str(e)
                ))
                overall_status = HealthStatus.UNHEALTHY
        
        # Get system metrics
        system_metrics = self._get_system_metrics()
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        
        # Create system health object
        system_health = SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            components=components,
            system_metrics=system_metrics,
            uptime_seconds=uptime_seconds
        )
        
        # Update health history
        self._update_health_history(system_health)
        
        # Update Prometheus metrics
        self._update_prometheus_metrics(system_health)
        
        logger.info(f"Health check completed: {overall_status.value}")
        return system_health
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """
        Get health status for a specific component.
        
        Args:
            component_name: Name of the component to check
            
        Returns:
            ComponentHealth object or None if component not found
        """
        if component_name not in self.health_checkers:
            logger.warning(f"Unknown component: {component_name}")
            return None
        
        try:
            return self.health_checkers[component_name]()
        except Exception as e:
            logger.error(f"Health check failed for {component_name}: {str(e)}")
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    def get_health_history(self, limit: int = 10) -> List[SystemHealth]:
        """
        Get health check history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of SystemHealth objects
        """
        return self.health_history[-limit:]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary information.
        
        Returns:
            Dictionary with health summary
        """
        if not self.health_history:
            return {
                'status': 'unknown',
                'last_check': None,
                'uptime_seconds': time.time() - self.start_time,
                'component_count': 0,
                'healthy_components': 0,
                'degraded_components': 0,
                'unhealthy_components': 0
            }
        
        latest_health = self.health_history[-1]
        
        # Count component statuses
        healthy_count = sum(1 for c in latest_health.components if c.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for c in latest_health.components if c.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for c in latest_health.components if c.status == HealthStatus.UNHEALTHY)
        
        return {
            'status': latest_health.overall_status.value,
            'last_check': latest_health.timestamp.isoformat(),
            'uptime_seconds': latest_health.uptime_seconds,
            'component_count': len(latest_health.components),
            'healthy_components': healthy_count,
            'degraded_components': degraded_count,
            'unhealthy_components': unhealthy_count,
            'system_metrics': latest_health.system_metrics
        }
    
    def _check_database_health(self) -> ComponentHealth:
        """Check database health."""
        start_time = time.time()
        
        try:
            db_health = db_health_check()
            response_time = (time.time() - start_time) * 1000
            
            if db_health.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='database',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=db_health
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='database',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_portfolio_integration_health(self) -> ComponentHealth:
        """Check portfolio integration health."""
        start_time = time.time()
        
        try:
            portfolio_integration = get_portfolio_integration()
            health_data = portfolio_integration.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if health_data.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='portfolio_integration',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=health_data
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='portfolio_integration',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_trading_engine_integration_health(self) -> ComponentHealth:
        """Check trading engine integration health."""
        start_time = time.time()
        
        try:
            trading_engine_integration = get_trading_engine_integration()
            health_data = trading_engine_integration.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if health_data.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='trading_engine_integration',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=health_data
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='trading_engine_integration',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_market_data_integration_health(self) -> ComponentHealth:
        """Check market data integration health."""
        start_time = time.time()
        
        try:
            market_data_integration = get_market_data_integration()
            health_data = market_data_integration.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if health_data.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='market_data_integration',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=health_data
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='market_data_integration',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_data_synchronization_health(self) -> ComponentHealth:
        """Check data synchronization health."""
        start_time = time.time()
        
        try:
            data_sync_service = get_data_sync_service()
            health_data = data_sync_service.get_sync_health()
            response_time = (time.time() - start_time) * 1000
            
            if health_data.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
            elif health_data.get('status') == 'degraded':
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='data_synchronization',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=health_data
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='data_synchronization',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_cross_service_monitoring_health(self) -> ComponentHealth:
        """Check cross-service monitoring health."""
        start_time = time.time()
        
        try:
            monitoring = get_cross_service_monitoring()
            health_summary = monitoring.get_service_health_summary()
            response_time = (time.time() - start_time) * 1000
            
            if health_summary.get('overall_status') == 'healthy':
                status = HealthStatus.HEALTHY
            elif health_summary.get('overall_status') == 'degraded':
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name='cross_service_monitoring',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=health_summary
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='cross_service_monitoring',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_system_resources_health(self) -> ComponentHealth:
        """Check system resources health."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status based on resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 70:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            metadata = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
            
            return ComponentHealth(
                name='system_resources',
                status=status,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=metadata
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name='system_resources',
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_total_gb': memory.total / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_total_gb': disk.total / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {'error': str(e)}
    
    def _update_health_history(self, system_health: SystemHealth) -> None:
        """Update health history."""
        self.health_history.append(system_health)
        
        # Keep only recent history
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def _update_prometheus_metrics(self, system_health: SystemHealth) -> None:
        """Update Prometheus metrics with health information."""
        try:
            metrics = get_metrics()
            
            # Update system health metrics
            for component in system_health.components:
                health_value = 1.0 if component.status == HealthStatus.HEALTHY else 0.0
                metrics.update_system_health(component.name, health_value)
            
            # Update memory usage
            if 'memory_percent' in system_health.system_metrics:
                memory_bytes = (system_health.system_metrics['memory_percent'] / 100.0) * system_health.system_metrics['memory_total_gb'] * (1024**3)
                metrics.update_memory_usage('risk_management', int(memory_bytes))
                
        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {str(e)}")


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    
    return _health_monitor


def initialize_health_monitor() -> HealthMonitor:
    """Initialize health monitor."""
    global _health_monitor
    
    _health_monitor = HealthMonitor()
    return _health_monitor
























