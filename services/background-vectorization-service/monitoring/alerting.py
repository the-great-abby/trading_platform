#!/usr/bin/env python3
"""
Enhanced Monitoring and Alerting System for Background Vectorization Service

Provides comprehensive monitoring, alerting, and performance tracking for production use.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"

class AlertType(Enum):
    """Types of alerts."""
    PERFORMANCE = "performance"
    ERROR = "error"
    RESOURCE = "resource"
    BUSINESS = "business"
    INTEGRATION = "integration"

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False

class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.performance_thresholds = {
            "job_processing_time": 300.0,  # 5 minutes
            "queue_size": 100,
            "error_rate": 0.1,  # 10%
            "success_rate": 0.8,  # 80%
            "memory_usage": 0.8,  # 80%
            "cpu_usage": 0.8,  # 80%
        }
        
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
        
    def create_alert(self, alert_type: AlertType, severity: AlertSeverity, 
                    title: str, message: str, metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert."""
        alert_id = f"{alert_type.value}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # Notify all handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        logger.info(f"Alert created: {alert.title} ({alert.severity.value})")
        return alert
        
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            logger.info(f"Alert acknowledged: {alert_id}")
            
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            logger.info(f"Alert resolved: {alert_id}")
            
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts.values() if not alert.resolved]
        
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts.values() if alert.severity == severity]
        
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Get alerts by type."""
        return [alert for alert in self.alerts.values() if alert.type == alert_type]

class PerformanceMonitor:
    """Monitors service performance and triggers alerts."""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.last_check = datetime.utcnow()
        
    async def monitor_performance(self, current_metrics: Dict[str, Any]):
        """Monitor performance metrics and trigger alerts if needed."""
        try:
            # Store metrics history
            timestamp = datetime.utcnow()
            for key, value in current_metrics.items():
                if key not in self.metrics_history:
                    self.metrics_history[key] = []
                self.metrics_history[key].append({
                    "timestamp": timestamp,
                    "value": value
                })
                
                # Keep only last 1000 data points
                if len(self.metrics_history[key]) > 1000:
                    self.metrics_history[key] = self.metrics_history[key][-1000:]
            
            # Check performance thresholds
            await self._check_performance_thresholds(current_metrics)
            
            # Check for anomalies
            await self._check_anomalies(current_metrics)
            
            self.last_check = timestamp
            
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            
    async def _check_performance_thresholds(self, metrics: Dict[str, Any]):
        """Check if metrics exceed thresholds."""
        thresholds = self.alert_manager.performance_thresholds
        
        # Check job processing time
        if "avg_processing_time" in metrics:
            avg_time = metrics["avg_processing_time"]
            if avg_time > thresholds["job_processing_time"]:
                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    AlertSeverity.WARNING,
                    "High Job Processing Time",
                    f"Average job processing time ({avg_time:.2f}s) exceeds threshold ({thresholds['job_processing_time']}s)",
                    {"current_value": avg_time, "threshold": thresholds["job_processing_time"]}
                )
        
        # Check queue size
        if "queue_size" in metrics:
            queue_size = metrics["queue_size"]
            if queue_size > thresholds["queue_size"]:
                self.alert_manager.create_alert(
                    AlertType.PERFORMANCE,
                    AlertSeverity.WARNING,
                    "Large Job Queue",
                    f"Job queue size ({queue_size}) exceeds threshold ({thresholds['queue_size']})",
                    {"current_value": queue_size, "threshold": thresholds["queue_size"]}
                )
        
        # Check error rate
        if "total_jobs_processed" in metrics and "failed_vectorizations" in metrics:
            total_jobs = metrics["total_jobs_processed"]
            failed_jobs = metrics["failed_vectorizations"]
            if total_jobs > 0:
                error_rate = failed_jobs / total_jobs
                if error_rate > thresholds["error_rate"]:
                    self.alert_manager.create_alert(
                        AlertType.PERFORMANCE,
                        AlertSeverity.CRITICAL,
                        "High Error Rate",
                        f"Error rate ({error_rate:.2%}) exceeds threshold ({thresholds['error_rate']:.1%})",
                        {"current_value": error_rate, "threshold": thresholds["error_rate"]}
                    )
        
        # Check success rate
        if "total_jobs_processed" in metrics and "successful_vectorizations" in metrics:
            total_jobs = metrics["total_jobs_processed"]
            successful_jobs = metrics["successful_vectorizations"]
            if total_jobs > 0:
                success_rate = successful_jobs / total_jobs
                if success_rate < thresholds["success_rate"]:
                    self.alert_manager.create_alert(
                        AlertType.PERFORMANCE,
                        AlertSeverity.WARNING,
                        "Low Success Rate",
                        f"Success rate ({success_rate:.2%}) below threshold ({thresholds['success_rate']:.1%})",
                        {"current_value": success_rate, "threshold": thresholds["success_rate"]}
                    )
                    
    async def _check_anomalies(self, metrics: Dict[str, Any]):
        """Check for anomalous patterns in metrics."""
        # Check for sudden drops in success rate
        if "successful_vectorizations" in self.metrics_history:
            recent_success = self.metrics_history["successful_vectorizations"][-10:]
            if len(recent_success) >= 10:
                recent_avg = sum(point["value"] for point in recent_success) / len(recent_success)
                if recent_avg < 1:  # Less than 1 successful job in last 10
                    self.alert_manager.create_alert(
                        AlertType.PERFORMANCE,
                        AlertSeverity.WARNING,
                        "Low Recent Success Rate",
                        f"Recent success rate is very low ({recent_avg:.2f})",
                        {"recent_average": recent_avg, "data_points": len(recent_success)}
                    )
        
        # Check for queue buildup
        if "queue_size" in self.metrics_history:
            recent_queue = self.metrics_history["queue_size"][-5:]
            if len(recent_queue) >= 5:
                queue_trend = recent_queue[-1]["value"] - recent_queue[0]["value"]
                if queue_trend > 20:  # Queue growing by more than 20
                    self.alert_manager.create_alert(
                        AlertType.PERFORMANCE,
                        AlertSeverity.WARNING,
                        "Queue Buildup Detected",
                        f"Job queue is building up (growth: +{queue_trend} jobs)",
                        {"queue_growth": queue_trend, "time_period": "5 data points"}
                    )

class ResourceMonitor:
    """Monitors system resources and triggers alerts."""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        
    async def check_resources(self, resource_metrics: Dict[str, Any]):
        """Check resource usage and trigger alerts if needed."""
        try:
            # Check memory usage
            if "memory_usage_percent" in resource_metrics:
                memory_usage = resource_metrics["memory_usage_percent"]
                if memory_usage > 80:
                    self.alert_manager.create_alert(
                        AlertType.RESOURCE,
                        AlertSeverity.WARNING,
                        "High Memory Usage",
                        f"Memory usage is high: {memory_usage:.1f}%",
                        {"current_usage": memory_usage, "threshold": 80}
                    )
                    
            # Check CPU usage
            if "cpu_usage_percent" in resource_metrics:
                cpu_usage = resource_metrics["cpu_usage_percent"]
                if cpu_usage > 80:
                    self.alert_manager.create_alert(
                        AlertType.RESOURCE,
                        AlertSeverity.WARNING,
                        "High CPU Usage",
                        f"CPU usage is high: {cpu_usage:.1f}%",
                        {"current_usage": cpu_usage, "threshold": 80}
                    )
                    
            # Check disk usage
            if "disk_usage_percent" in resource_metrics:
                disk_usage = resource_metrics["disk_usage_percent"]
                if disk_usage > 90:
                    self.alert_manager.create_alert(
                        AlertType.RESOURCE,
                        AlertSeverity.CRITICAL,
                        "High Disk Usage",
                        f"Disk usage is critical: {disk_usage:.1f}%",
                        {"current_usage": disk_usage, "threshold": 90}
                    )
                    
        except Exception as e:
            logger.error(f"Error in resource monitoring: {e}")

class IntegrationMonitor:
    """Monitors integration health and triggers alerts."""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.integration_status = {}
        
    async def check_integration_health(self, integration_checks: Dict[str, Any]):
        """Check integration health and trigger alerts if needed."""
        try:
            for integration_name, status in integration_checks.items():
                if not status.get("healthy", False):
                    # Check if this is a new failure
                    if integration_name not in self.integration_status or self.integration_status[integration_name].get("healthy", True):
                        self.alert_manager.create_alert(
                            AlertType.INTEGRATION,
                            AlertSeverity.CRITICAL,
                            f"Integration Failure: {integration_name}",
                            f"Integration {integration_name} is not healthy",
                            {"integration": integration_name, "status": status}
                        )
                        
                # Update status
                self.integration_status[integration_name] = status
                
        except Exception as e:
            logger.error(f"Error in integration monitoring: {e}")

# Default alert handlers
def console_alert_handler(alert: Alert):
    """Default console alert handler."""
    timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {alert.severity.value.upper()}: {alert.title}")
    print(f"  {alert.message}")
    if alert.metadata:
        print(f"  Metadata: {json.dumps(alert.metadata, indent=2)}")
    print()

def log_alert_handler(alert: Alert):
    """Default log alert handler."""
    log_level = logging.WARNING if alert.severity in [AlertSeverity.WARNING, AlertSeverity.ERROR] else logging.INFO
    if alert.severity == AlertSeverity.CRITICAL:
        log_level = logging.ERROR
        
    logger.log(log_level, f"ALERT [{alert.severity.value.upper()}]: {alert.title} - {alert.message}")

# Initialize global instances
alert_manager = AlertManager()
performance_monitor = PerformanceMonitor(alert_manager)
resource_monitor = ResourceMonitor(alert_manager)
integration_monitor = IntegrationMonitor(alert_manager)

# Add default handlers
alert_manager.add_alert_handler(console_alert_handler)
alert_manager.add_alert_handler(log_alert_handler)
