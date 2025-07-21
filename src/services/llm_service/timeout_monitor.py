"""
Timeout Monitor for LLM Proxy System
Provides real-time monitoring and alerting for timeout events
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TimeoutSeverity(Enum):
    """Timeout severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TimeoutEvent:
    """Timeout event record"""
    timestamp: datetime
    component: str
    operation: str
    duration: float
    severity: TimeoutSeverity
    strategy: str
    success: bool
    fallback_used: bool
    request_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeoutAlert:
    """Timeout alert configuration"""
    name: str
    condition: str
    threshold: float
    severity: TimeoutSeverity
    enabled: bool = True
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None


class TimeoutMonitor:
    """Real-time timeout monitoring and alerting"""
    
    def __init__(self):
        self.events: List[TimeoutEvent] = []
        self.alerts: Dict[str, TimeoutAlert] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.max_events = 1000
        self.monitoring_enabled = True
        
        # Initialize default alerts
        self._setup_default_alerts()
        
        logger.info("Timeout Monitor initialized")
    
    def _setup_default_alerts(self):
        """Setup default timeout alerts"""
        
        default_alerts = [
            TimeoutAlert(
                name="high_timeout_rate",
                condition="timeout_rate > 0.1",
                threshold=0.1,
                severity=TimeoutSeverity.HIGH
            ),
            TimeoutAlert(
                name="critical_timeout_rate",
                condition="timeout_rate > 0.3",
                threshold=0.3,
                severity=TimeoutSeverity.CRITICAL
            ),
            TimeoutAlert(
                name="service_unavailable",
                condition="service_errors > 5",
                threshold=5,
                severity=TimeoutSeverity.CRITICAL
            ),
            TimeoutAlert(
                name="fallback_overuse",
                condition="fallback_rate > 0.5",
                threshold=0.5,
                severity=TimeoutSeverity.MEDIUM
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.name] = alert
    
    def register_callback(self, alert_name: str, callback: Callable):
        """Register a callback for a specific alert"""
        self.callbacks[alert_name] = callback
        logger.info(f"Registered callback for alert: {alert_name}")
    
    async def record_timeout_event(self, 
                                 component: str, 
                                 operation: str, 
                                 duration: float,
                                 strategy: str,
                                 success: bool,
                                 fallback_used: bool,
                                 request_id: Optional[str] = None,
                                 error_message: Optional[str] = None,
                                 metadata: Dict[str, Any] = None) -> TimeoutEvent:
        """Record a timeout event"""
        
        # Determine severity based on duration and context
        severity = self._determine_severity(duration, component, operation)
        
        event = TimeoutEvent(
            timestamp=datetime.utcnow(),
            component=component,
            operation=operation,
            duration=duration,
            severity=severity,
            strategy=strategy,
            success=success,
            fallback_used=fallback_used,
            request_id=request_id,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        # Add event to history
        self.events.append(event)
        
        # Trim old events if too many
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Check for alerts
        await self._check_alerts(event)
        
        logger.info(f"📊 Recorded timeout event: {component}/{operation} ({duration:.2f}s, {severity.value})")
        
        return event
    
    def _determine_severity(self, duration: float, component: str, operation: str) -> TimeoutSeverity:
        """Determine severity based on duration and context"""
        
        # Base severity on duration
        if duration < 10:
            base_severity = TimeoutSeverity.LOW
        elif duration < 30:
            base_severity = TimeoutSeverity.MEDIUM
        elif duration < 60:
            base_severity = TimeoutSeverity.HIGH
        else:
            base_severity = TimeoutSeverity.CRITICAL
        
        # Adjust based on component
        if component in ['client', 'proxy']:
            # Client and proxy timeouts are more critical
            if base_severity == TimeoutSeverity.LOW:
                base_severity = TimeoutSeverity.MEDIUM
            elif base_severity == TimeoutSeverity.MEDIUM:
                base_severity = TimeoutSeverity.HIGH
        
        # Adjust based on operation
        if operation in ['real_time_trading', 'signal_analysis']:
            # Real-time operations are more critical
            if base_severity == TimeoutSeverity.LOW:
                base_severity = TimeoutSeverity.MEDIUM
            elif base_severity == TimeoutSeverity.MEDIUM:
                base_severity = TimeoutSeverity.HIGH
        
        return base_severity
    
    async def _check_alerts(self, event: TimeoutEvent):
        """Check if any alerts should be triggered"""
        
        for alert_name, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if alert.last_triggered:
                cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            # Check if alert should trigger
            if await self._should_trigger_alert(alert, event):
                await self._trigger_alert(alert, event)
    
    async def _should_trigger_alert(self, alert: TimeoutAlert, event: TimeoutEvent) -> bool:
        """Check if an alert should be triggered"""
        
        # Get recent events (last 10 minutes)
        recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
        recent_events = [e for e in self.events if e.timestamp > recent_cutoff]
        
        if alert.name == "high_timeout_rate":
            total_requests = len(recent_events)
            timeout_events = len([e for e in recent_events if not e.success])
            timeout_rate = timeout_events / total_requests if total_requests > 0 else 0
            return timeout_rate > alert.threshold
        
        elif alert.name == "critical_timeout_rate":
            total_requests = len(recent_events)
            timeout_events = len([e for e in recent_events if not e.success])
            timeout_rate = timeout_events / total_requests if total_requests > 0 else 0
            return timeout_rate > alert.threshold
        
        elif alert.name == "service_unavailable":
            service_errors = len([e for e in recent_events 
                               if e.component in ['ollama', 'proxy'] and not e.success])
            return service_errors > alert.threshold
        
        elif alert.name == "fallback_overuse":
            total_events = len(recent_events)
            fallback_events = len([e for e in recent_events if e.fallback_used])
            fallback_rate = fallback_events / total_events if total_events > 0 else 0
            return fallback_rate > alert.threshold
        
        return False
    
    async def _trigger_alert(self, alert: TimeoutAlert, event: TimeoutEvent):
        """Trigger an alert"""
        
        alert.last_triggered = datetime.utcnow()
        
        alert_data = {
            'alert_name': alert.name,
            'severity': alert.severity.value,
            'threshold': alert.threshold,
            'triggering_event': {
                'component': event.component,
                'operation': event.operation,
                'duration': event.duration,
                'timestamp': event.timestamp.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.warning(f"🚨 ALERT: {alert.name} triggered (severity: {alert.severity.value})")
        logger.warning(f"   Component: {event.component}")
        logger.warning(f"   Operation: {event.operation}")
        logger.warning(f"   Duration: {event.duration:.2f}s")
        
        # Execute callback if registered
        if alert.name in self.callbacks:
            try:
                await self.callbacks[alert.name](alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def get_metrics(self, window_minutes: int = 10) -> Dict[str, Any]:
        """Get timeout metrics for the specified time window"""
        
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_events = [e for e in self.events if e.timestamp > cutoff]
        
        if not recent_events:
            return {
                'total_events': 0,
                'timeout_rate': 0.0,
                'average_duration': 0.0,
                'severity_distribution': {},
                'component_distribution': {},
                'operation_distribution': {},
                'fallback_rate': 0.0
            }
        
        total_events = len(recent_events)
        timeout_events = len([e for e in recent_events if not e.success])
        fallback_events = len([e for e in recent_events if e.fallback_used])
        
        # Calculate distributions
        severity_dist = {}
        component_dist = {}
        operation_dist = {}
        
        for event in recent_events:
            severity_dist[event.severity.value] = severity_dist.get(event.severity.value, 0) + 1
            component_dist[event.component] = component_dist.get(event.component, 0) + 1
            operation_dist[event.operation] = operation_dist.get(event.operation, 0) + 1
        
        return {
            'total_events': total_events,
            'timeout_rate': timeout_events / total_events,
            'average_duration': sum(e.duration for e in recent_events) / total_events,
            'severity_distribution': severity_dist,
            'component_distribution': component_dist,
            'operation_distribution': operation_dist,
            'fallback_rate': fallback_events / total_events,
            'window_minutes': window_minutes
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent timeout events"""
        
        recent_events = sorted(self.events, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [{
            'timestamp': event.timestamp.isoformat(),
            'component': event.component,
            'operation': event.operation,
            'duration': event.duration,
            'severity': event.severity.value,
            'strategy': event.strategy,
            'success': event.success,
            'fallback_used': event.fallback_used,
            'request_id': event.request_id,
            'error_message': event.error_message
        } for event in recent_events]
    
    def get_alerts_status(self) -> Dict[str, Any]:
        """Get current alerts status"""
        
        return {
            'total_alerts': len(self.alerts),
            'enabled_alerts': len([a for a in self.alerts.values() if a.enabled]),
            'alerts': [{
                'name': alert.name,
                'condition': alert.condition,
                'threshold': alert.threshold,
                'severity': alert.severity.value,
                'enabled': alert.enabled,
                'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None
            } for alert in self.alerts.values()]
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': self.get_metrics(),
            'recent_events': self.get_recent_events(),
            'alerts_status': self.get_alerts_status()
        }
        
        if format == 'json':
            return json.dumps(metrics, indent=2)
        else:
            return str(metrics)


# Global timeout monitor instance
timeout_monitor = TimeoutMonitor()


async def record_timeout_event(*args, **kwargs) -> TimeoutEvent:
    """Global function to record timeout events"""
    return await timeout_monitor.record_timeout_event(*args, **kwargs)


def get_timeout_metrics(window_minutes: int = 10) -> Dict[str, Any]:
    """Global function to get timeout metrics"""
    return timeout_monitor.get_metrics(window_minutes) 