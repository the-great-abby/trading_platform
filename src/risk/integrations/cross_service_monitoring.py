"""
Cross-Service Monitoring and Alerting

Provides comprehensive monitoring and alerting across all integrated
services in the risk management framework.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
import time

from ..utils.risk_utils import CacheUtils, PerformanceUtils
from .portfolio_service_integration import get_portfolio_integration
from .trading_engine_integration import get_trading_engine_integration
from .market_data_service_integration import get_market_data_integration
from .data_synchronization_service import get_data_sync_service


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    service: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class ServiceHealth:
    """Service health status."""
    service_name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool
    check_interval_seconds: int
    alert_thresholds: Dict[str, Any]
    notification_channels: List[str]
    escalation_rules: Dict[str, Any]


class CrossServiceMonitoring:
    """
    Cross-service monitoring and alerting system.
    
    Monitors health, performance, and data consistency across all
    integrated services in the risk management framework.
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 300,  # 5 minutes
        alert_retention_hours: int = 24,
        max_alerts_per_service: int = 100
    ):
        """
        Initialize cross-service monitoring.
        
        Args:
            check_interval_seconds: Health check interval in seconds
            alert_retention_hours: How long to retain alerts
            max_alerts_per_service: Maximum alerts per service
        """
        self.check_interval_seconds = check_interval_seconds
        self.alert_retention_hours = alert_retention_hours
        self.max_alerts_per_service = max_alerts_per_service
        
        # Monitoring state
        self.service_health: Dict[str, ServiceHealth] = {}
        self.active_alerts: Dict[str, List[Alert]] = {}
        self.alert_history: List[Alert] = []
        
        # Monitoring configuration
        self.monitoring_config: Dict[str, MonitoringConfig] = {}
        
        # Integration services
        self.portfolio_integration = get_portfolio_integration()
        self.trading_engine_integration = get_trading_engine_integration()
        self.market_data_integration = get_market_data_integration()
        self.data_sync_service = get_data_sync_service()
        
        # Monitoring control
        self._monitoring_thread = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Alert handlers
        self._alert_handlers: List[Callable[[Alert], None]] = []
        
        # Initialize monitoring configurations
        self._initialize_monitoring_configs()
    
    def start_monitoring(self) -> bool:
        """
        Start the cross-service monitoring system.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("Cross-service monitoring is already running")
            return True
        
        try:
            # Reset stop event
            self._stop_event.clear()
            
            # Start monitoring thread
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="CrossServiceMonitoring",
                daemon=True
            )
            self._monitoring_thread.start()
            
            self._running = True
            logger.info("Cross-service monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start cross-service monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop the cross-service monitoring system.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cross-service monitoring is not running")
            return True
        
        try:
            # Signal stop
            self._stop_event.set()
            
            # Wait for thread to finish
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=30)
            
            self._running = False
            logger.info("Cross-service monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop cross-service monitoring: {str(e)}")
            return False
    
    @PerformanceUtils.measure_execution_time
    def check_service_health(self, service_name: str) -> ServiceHealth:
        """
        Check health of a specific service.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            ServiceHealth object with health status
        """
        logger.debug(f"Checking health for service: {service_name}")
        
        start_time = time.time()
        status = 'unhealthy'
        error_count = 0
        success_count = 0
        metadata = {}
        
        try:
            # Check service-specific health
            if service_name == 'portfolio_service':
                health_data = self.portfolio_integration.health_check()
                status = health_data.get('status', 'unhealthy')
                metadata = health_data
                
            elif service_name == 'trading_engine':
                health_data = self.trading_engine_integration.health_check()
                status = health_data.get('status', 'unhealthy')
                metadata = health_data
                
            elif service_name == 'market_data_service':
                health_data = self.market_data_integration.health_check()
                status = health_data.get('status', 'unhealthy')
                metadata = health_data
                
            elif service_name == 'data_synchronization':
                health_data = self.data_sync_service.get_sync_health()
                status = health_data.get('status', 'unhealthy')
                metadata = health_data
                
            else:
                logger.warning(f"Unknown service for health check: {service_name}")
                status = 'unhealthy'
                metadata = {'error': 'Unknown service'}
            
            # Update counters
            if status == 'healthy':
                success_count = 1
            else:
                error_count = 1
                
        except Exception as e:
            logger.error(f"Error checking health for {service_name}: {str(e)}")
            status = 'unhealthy'
            error_count = 1
            metadata = {'error': str(e)}
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Create service health object
        service_health = ServiceHealth(
            service_name=service_name,
            status=status,
            last_check=datetime.utcnow(),
            response_time_ms=response_time_ms,
            error_count=error_count,
            success_count=success_count,
            metadata=metadata
        )
        
        # Update service health
        self.service_health[service_name] = service_health
        
        # Check for health alerts
        self._check_health_alerts(service_name, service_health)
        
        return service_health
    
    @PerformanceUtils.measure_execution_time
    def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """
        Check health of all integrated services.
        
        Returns:
            Dictionary mapping service names to health status
        """
        logger.info("Checking health for all integrated services")
        
        services_to_check = [
            'portfolio_service',
            'trading_engine',
            'market_data_service',
            'data_synchronization'
        ]
        
        health_results = {}
        
        for service_name in services_to_check:
            try:
                health = self.check_service_health(service_name)
                health_results[service_name] = health
                
            except Exception as e:
                logger.error(f"Error checking health for {service_name}: {str(e)}")
                # Create unhealthy status
                health_results[service_name] = ServiceHealth(
                    service_name=service_name,
                    status='unhealthy',
                    last_check=datetime.utcnow(),
                    error_count=1,
                    metadata={'error': str(e)}
                )
        
        logger.info(f"Health check completed for {len(health_results)} services")
        return health_results
    
    def create_alert(
        self,
        service: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            service: Service that generated the alert
            severity: Alert severity level
            title: Alert title
            description: Alert description
            metadata: Additional alert metadata
            
        Returns:
            Created Alert object
        """
        alert_id = f"{service}_{int(time.time())}"
        
        alert = Alert(
            alert_id=alert_id,
            service=service,
            severity=severity,
            status=AlertStatus.ACTIVE,
            title=title,
            description=description,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Add to active alerts
        if service not in self.active_alerts:
            self.active_alerts[service] = []
        
        self.active_alerts[service].append(alert)
        
        # Add to alert history
        self.alert_history.append(alert)
        
        # Clean up old alerts
        self._cleanup_old_alerts()
        
        # Notify alert handlers
        self._notify_alert_handlers(alert)
        
        logger.info(f"Alert created: {alert_id} - {title}")
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: str = None
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert identifier
            acknowledged_by: User who acknowledged the alert
            notes: Optional acknowledgment notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find alert in active alerts
            for service_alerts in self.active_alerts.values():
                for alert in service_alerts:
                    if alert.alert_id == alert_id:
                        alert.status = AlertStatus.ACKNOWLEDGED
                        alert.acknowledged_by = acknowledged_by
                        alert.resolution_notes = notes
                        
                        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                        return True
            
            logger.warning(f"Alert not found for acknowledgment: {alert_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
            return False
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: str = None
    ) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert identifier
            resolution_notes: Optional resolution notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find alert in active alerts
            for service_alerts in self.active_alerts.values():
                for alert in service_alerts:
                    if alert.alert_id == alert_id:
                        alert.status = AlertStatus.RESOLVED
                        alert.resolved_at = datetime.utcnow()
                        alert.resolution_notes = resolution_notes
                        
                        # Move from active to resolved
                        service_alerts.remove(alert)
                        
                        logger.info(f"Alert resolved: {alert_id}")
                        return True
            
            logger.warning(f"Alert not found for resolution: {alert_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
            return False
    
    def get_active_alerts(
        self,
        service: Optional[str] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            service: Filter by service (None for all)
            severity: Filter by severity (None for all)
            
        Returns:
            List of active alerts
        """
        active_alerts = []
        
        for service_name, alerts in self.active_alerts.items():
            if service and service_name != service:
                continue
            
            for alert in alerts:
                if alert.status == AlertStatus.ACTIVE:
                    if severity is None or alert.severity == severity:
                        active_alerts.append(alert)
        
        return active_alerts
    
    def get_service_health_summary(self) -> Dict[str, Any]:
        """
        Get overall service health summary.
        
        Returns:
            Health summary dictionary
        """
        total_services = len(self.service_health)
        healthy_services = sum(
            1 for health in self.service_health.values()
            if health.status == 'healthy'
        )
        degraded_services = sum(
            1 for health in self.service_health.values()
            if health.status == 'degraded'
        )
        unhealthy_services = sum(
            1 for health in self.service_health.values()
            if health.status == 'unhealthy'
        )
        
        # Calculate overall health status
        if unhealthy_services > 0:
            overall_status = 'unhealthy'
        elif degraded_services > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'degraded_services': degraded_services,
            'unhealthy_services': unhealthy_services,
            'last_check': max(
                (health.last_check for health in self.service_health.values()),
                default=datetime.utcnow()
            ).isoformat(),
            'active_alerts': len(self.get_active_alerts()),
            'critical_alerts': len(self.get_active_alerts(severity=AlertSeverity.CRITICAL)),
            'error_alerts': len(self.get_active_alerts(severity=AlertSeverity.ERROR))
        }
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Add an alert handler.
        
        Args:
            handler: Function to call when alerts are created
        """
        self._alert_handlers.append(handler)
        logger.info("Alert handler added")
    
    def remove_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Remove an alert handler.
        
        Args:
            handler: Function to remove
        """
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)
            logger.info("Alert handler removed")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Cross-service monitoring loop started")
        
        while not self._stop_event.is_set():
            try:
                # Perform health checks
                self.check_all_services_health()
                
                # Check data consistency
                self._check_data_consistency()
                
                # Check performance metrics
                self._check_performance_metrics()
                
                # Wait for next check
                self._stop_event.wait(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                # Wait before retrying
                self._stop_event.wait(60)
        
        logger.info("Cross-service monitoring loop stopped")
    
    def _check_health_alerts(self, service_name: str, health: ServiceHealth) -> None:
        """Check for health-related alerts."""
        config = self.monitoring_config.get(service_name)
        if not config or not config.enabled:
            return
        
        # Check response time threshold
        if health.response_time_ms and health.response_time_ms > config.alert_thresholds.get('response_time_ms', 5000):
            self.create_alert(
                service=service_name,
                severity=AlertSeverity.WARNING,
                title=f"High Response Time - {service_name}",
                description=f"Response time {health.response_time_ms:.2f}ms exceeds threshold",
                metadata={'response_time_ms': health.response_time_ms}
            )
        
        # Check error rate threshold
        total_requests = health.success_count + health.error_count
        if total_requests > 0:
            error_rate = health.error_count / total_requests
            if error_rate > config.alert_thresholds.get('error_rate', 0.1):
                self.create_alert(
                    service=service_name,
                    severity=AlertSeverity.ERROR,
                    title=f"High Error Rate - {service_name}",
                    description=f"Error rate {error_rate:.2%} exceeds threshold",
                    metadata={'error_rate': error_rate}
                )
        
        # Check service status
        if health.status == 'unhealthy':
            self.create_alert(
                service=service_name,
                severity=AlertSeverity.CRITICAL,
                title=f"Service Unhealthy - {service_name}",
                description=f"Service {service_name} is reporting unhealthy status",
                metadata={'status': health.status, 'metadata': health.metadata}
            )
        elif health.status == 'degraded':
            self.create_alert(
                service=service_name,
                severity=AlertSeverity.WARNING,
                title=f"Service Degraded - {service_name}",
                description=f"Service {service_name} is reporting degraded status",
                metadata={'status': health.status, 'metadata': health.metadata}
            )
    
    def _check_data_consistency(self) -> None:
        """Check data consistency across services."""
        try:
            # This would implement data consistency checks
            # For example, comparing portfolio data between services
            pass
        except Exception as e:
            logger.error(f"Error checking data consistency: {str(e)}")
    
    def _check_performance_metrics(self) -> None:
        """Check performance metrics across services."""
        try:
            # This would implement performance monitoring
            # For example, checking response times, throughput, etc.
            pass
        except Exception as e:
            logger.error(f"Error checking performance metrics: {str(e)}")
    
    def _cleanup_old_alerts(self) -> None:
        """Clean up old alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.alert_retention_hours)
            
            # Clean up alert history
            self.alert_history = [
                alert for alert in self.alert_history
                if alert.timestamp > cutoff_time
            ]
            
            # Clean up active alerts (keep only recent ones)
            for service in list(self.active_alerts.keys()):
                self.active_alerts[service] = [
                    alert for alert in self.active_alerts[service]
                    if alert.timestamp > cutoff_time
                ]
                
                # Limit alerts per service
                if len(self.active_alerts[service]) > self.max_alerts_per_service:
                    self.active_alerts[service] = self.active_alerts[service][-self.max_alerts_per_service:]
                
                # Remove empty service entries
                if not self.active_alerts[service]:
                    del self.active_alerts[service]
                    
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {str(e)}")
    
    def _notify_alert_handlers(self, alert: Alert) -> None:
        """Notify all alert handlers of a new alert."""
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def _initialize_monitoring_configs(self) -> None:
        """Initialize monitoring configurations."""
        default_thresholds = {
            'response_time_ms': 5000,
            'error_rate': 0.1,
            'success_rate': 0.9
        }
        
        services = [
            'portfolio_service',
            'trading_engine',
            'market_data_service',
            'data_synchronization'
        ]
        
        for service in services:
            self.monitoring_config[service] = MonitoringConfig(
                enabled=True,
                check_interval_seconds=self.check_interval_seconds,
                alert_thresholds=default_thresholds.copy(),
                notification_channels=['log', 'email'],
                escalation_rules={
                    'critical': {'escalate_after_minutes': 15},
                    'error': {'escalate_after_minutes': 30}
                }
            )


# Global cross-service monitoring instance
_cross_service_monitoring = None


def get_cross_service_monitoring() -> CrossServiceMonitoring:
    """Get global cross-service monitoring instance."""
    global _cross_service_monitoring
    
    if _cross_service_monitoring is None:
        _cross_service_monitoring = CrossServiceMonitoring()
    
    return _cross_service_monitoring


def initialize_cross_service_monitoring(
    check_interval_seconds: int = 300
) -> CrossServiceMonitoring:
    """Initialize cross-service monitoring."""
    global _cross_service_monitoring
    
    _cross_service_monitoring = CrossServiceMonitoring(
        check_interval_seconds=check_interval_seconds
    )
    
    logger.info("Cross-service monitoring initialized")
    return _cross_service_monitoring



