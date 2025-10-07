"""
Risk Alert Manager Service

Provides risk alert management and notification capabilities for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.risk_alert import RiskAlert, AlertType, AlertSeverity, AlertStatus


logger = logging.getLogger(__name__)


@dataclass
class AlertNotification:
    """Alert notification configuration."""
    channel: str  # "email", "dashboard", "api", "sms"
    recipients: List[str]
    template: str
    enabled: bool = True


class RiskAlertManager:
    """
    Risk alert management service.
    
    Provides functionality to manage risk alerts, send notifications,
    and track alert lifecycle.
    """
    
    def __init__(self, notification_service=None):
        """
        Initialize risk alert manager.
        
        Args:
            notification_service: External notification service (optional)
        """
        self.notification_service = notification_service
        self.alerts_cache = {}
        self.notification_configs = {}
        self.alert_history = {}
    
    def create_alert(
        self,
        portfolio_id: str,
        risk_limits_id: str,
        alert_type: str,
        alert_severity: str,
        limit_name: str,
        limit_value: float,
        current_value: float,
        breach_percentage: float,
        alert_message: str,
        recommended_action: str
    ) -> RiskAlert:
        """
        Create a new risk alert.
        
        Args:
            portfolio_id: Portfolio identifier
            risk_limits_id: Risk limits identifier
            alert_type: Type of alert ("warning", "breach", "critical")
            alert_severity: Severity level ("low", "medium", "high", "critical")
            limit_name: Name of the limit that was breached
            limit_value: Limit value
            current_value: Current value that breached the limit
            breach_percentage: Percentage of breach
            alert_message: Alert message
            recommended_action: Recommended action
            
        Returns:
            RiskAlert object
        """
        logger.info(f"Creating {alert_severity} {alert_type} alert for portfolio {portfolio_id}")
        
        # Validate inputs
        self._validate_alert_inputs(
            portfolio_id, risk_limits_id, alert_type, alert_severity,
            limit_name, limit_value, current_value, breach_percentage,
            alert_message, recommended_action
        )
        
        # Create alert
        alert = RiskAlert(
            portfolio_id=portfolio_id,
            risk_limits_id=risk_limits_id,
            alert_type=AlertType(alert_type),
            alert_severity=AlertSeverity(alert_severity),
            limit_name=limit_name,
            limit_value=limit_value,
            current_value=current_value,
            breach_percentage=breach_percentage,
            alert_message=alert_message,
            recommended_action=recommended_action
        )
        
        # Store in cache
        if portfolio_id not in self.alerts_cache:
            self.alerts_cache[portfolio_id] = []
        self.alerts_cache[portfolio_id].append(alert)
        
        # Add to history
        self._add_to_history(portfolio_id, alert, "created")
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        logger.info(f"Created alert {alert.risk_alert_id} for portfolio {portfolio_id}")
        return alert
    
    def acknowledge_alert(
        self,
        portfolio_id: str,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """
        Acknowledge a risk alert.
        
        Args:
            portfolio_id: Portfolio identifier
            alert_id: Alert identifier
            acknowledged_by: User who acknowledged the alert
            
        Returns:
            True if acknowledged successfully, False otherwise
        """
        logger.info(f"Acknowledging alert {alert_id} for portfolio {portfolio_id}")
        
        alert = self._find_alert(portfolio_id, alert_id)
        if not alert:
            logger.warning(f"Alert {alert_id} not found for portfolio {portfolio_id}")
            return False
        
        try:
            alert.acknowledge(acknowledged_by)
            self._add_to_history(portfolio_id, alert, "acknowledged", {"acknowledged_by": acknowledged_by})
            
            # Send acknowledgment notification
            self._send_acknowledgment_notification(alert, acknowledged_by)
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except ValueError as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
            return False
    
    def resolve_alert(
        self,
        portfolio_id: str,
        alert_id: str
    ) -> bool:
        """
        Resolve a risk alert.
        
        Args:
            portfolio_id: Portfolio identifier
            alert_id: Alert identifier
            
        Returns:
            True if resolved successfully, False otherwise
        """
        logger.info(f"Resolving alert {alert_id} for portfolio {portfolio_id}")
        
        alert = self._find_alert(portfolio_id, alert_id)
        if not alert:
            logger.warning(f"Alert {alert_id} not found for portfolio {portfolio_id}")
            return False
        
        try:
            alert.resolve()
            self._add_to_history(portfolio_id, alert, "resolved")
            
            # Send resolution notification
            self._send_resolution_notification(alert)
            
            logger.info(f"Alert {alert_id} resolved")
            return True
            
        except ValueError as e:
            logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
            return False
    
    def escalate_alert(
        self,
        portfolio_id: str,
        alert_id: str
    ) -> bool:
        """
        Escalate a risk alert.
        
        Args:
            portfolio_id: Portfolio identifier
            alert_id: Alert identifier
            
        Returns:
            True if escalated successfully, False otherwise
        """
        logger.info(f"Escalating alert {alert_id} for portfolio {portfolio_id}")
        
        alert = self._find_alert(portfolio_id, alert_id)
        if not alert:
            logger.warning(f"Alert {alert_id} not found for portfolio {portfolio_id}")
            return False
        
        try:
            alert.escalate()
            self._add_to_history(portfolio_id, alert, "escalated")
            
            # Send escalation notification
            self._send_escalation_notification(alert)
            
            logger.info(f"Alert {alert_id} escalated to level {alert.escalation_level}")
            return True
            
        except ValueError as e:
            logger.error(f"Failed to escalate alert {alert_id}: {str(e)}")
            return False
    
    def get_active_alerts(
        self,
        portfolio_id: str,
        severity_filter: Optional[str] = None
    ) -> List[RiskAlert]:
        """
        Get active alerts for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            severity_filter: Optional severity filter
            
        Returns:
            List of active RiskAlert objects
        """
        alerts = self.alerts_cache.get(portfolio_id, [])
        active_alerts = [alert for alert in alerts if alert.is_active()]
        
        if severity_filter:
            try:
                severity_enum = AlertSeverity(severity_filter)
                active_alerts = [alert for alert in active_alerts if alert.alert_severity == severity_enum]
            except ValueError:
                logger.warning(f"Invalid severity filter: {severity_filter}")
        
        return active_alerts
    
    def get_alert_history(
        self,
        portfolio_id: str,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get alert history for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            status_filter: Optional status filter
            severity_filter: Optional severity filter
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert history entries
        """
        alerts = self.alerts_cache.get(portfolio_id, [])
        
        # Apply filters
        if status_filter:
            try:
                status_enum = AlertStatus(status_filter)
                alerts = [alert for alert in alerts if alert.alert_status == status_enum]
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")
        
        if severity_filter:
            try:
                severity_enum = AlertSeverity(severity_filter)
                alerts = [alert for alert in alerts if alert.alert_severity == severity_enum]
            except ValueError:
                logger.warning(f"Invalid severity filter: {severity_filter}")
        
        # Sort by timestamp (most recent first) and limit results
        alerts.sort(key=lambda x: x.alert_timestamp, reverse=True)
        
        return [alert.to_dict() for alert in alerts[:limit]]
    
    def get_alerts_summary(
        self,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """
        Get alerts summary for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary with alerts summary
        """
        alerts = self.alerts_cache.get(portfolio_id, [])
        
        if not alerts:
            return {
                "portfolio_id": portfolio_id,
                "total_alerts": 0,
                "active_alerts": 0,
                "acknowledged_alerts": 0,
                "resolved_alerts": 0,
                "alerts_by_severity": {},
                "alerts_by_type": {}
            }
        
        # Count alerts by status
        active_alerts = [alert for alert in alerts if alert.is_active()]
        acknowledged_alerts = [alert for alert in alerts if alert.is_acknowledged()]
        resolved_alerts = [alert for alert in alerts if alert.is_resolved()]
        
        # Count alerts by severity
        alerts_by_severity = {}
        for severity in AlertSeverity:
            alerts_by_severity[severity.value] = len([alert for alert in alerts if alert.alert_severity == severity])
        
        # Count alerts by type
        alerts_by_type = {}
        for alert_type in AlertType:
            alerts_by_type[alert_type.value] = len([alert for alert in alerts if alert.alert_type == alert_type])
        
        return {
            "portfolio_id": portfolio_id,
            "total_alerts": len(alerts),
            "active_alerts": len(active_alerts),
            "acknowledged_alerts": len(acknowledged_alerts),
            "resolved_alerts": len(resolved_alerts),
            "alerts_by_severity": alerts_by_severity,
            "alerts_by_type": alerts_by_type
        }
    
    def get_alerts_requiring_attention(
        self,
        portfolio_id: str
    ) -> List[RiskAlert]:
        """
        Get alerts that require immediate attention.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            List of alerts requiring immediate attention
        """
        alerts = self.alerts_cache.get(portfolio_id, [])
        
        requiring_attention = []
        for alert in alerts:
            if alert.requires_immediate_attention():
                requiring_attention.append(alert)
        
        # Sort by priority score (highest first)
        requiring_attention.sort(key=lambda x: x.get_priority_score(), reverse=True)
        
        return requiring_attention
    
    def configure_notifications(
        self,
        portfolio_id: str,
        notification_configs: List[Dict[str, Any]]
    ) -> bool:
        """
        Configure alert notifications for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            notification_configs: List of notification configurations
            
        Returns:
            True if configured successfully, False otherwise
        """
        logger.info(f"Configuring notifications for portfolio {portfolio_id}")
        
        # Validate notification configurations
        for config in notification_configs:
            if not self._validate_notification_config(config):
                logger.error(f"Invalid notification configuration: {config}")
                return False
        
        # Store notification configurations
        self.notification_configs[portfolio_id] = notification_configs
        
        logger.info(f"Configured {len(notification_configs)} notification channels for portfolio {portfolio_id}")
        return True
    
    def _validate_alert_inputs(
        self,
        portfolio_id: str,
        risk_limits_id: str,
        alert_type: str,
        alert_severity: str,
        limit_name: str,
        limit_value: float,
        current_value: float,
        breach_percentage: float,
        alert_message: str,
        recommended_action: str
    ) -> None:
        """Validate alert creation inputs."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if not risk_limits_id:
            raise ValueError("Risk limits ID is required")
        
        try:
            AlertType(alert_type)
        except ValueError:
            raise ValueError(f"Invalid alert type: {alert_type}")
        
        try:
            AlertSeverity(alert_severity)
        except ValueError:
            raise ValueError(f"Invalid alert severity: {alert_severity}")
        
        if not limit_name:
            raise ValueError("Limit name is required")
        
        if limit_value <= 0:
            raise ValueError("Limit value must be positive")
        
        if current_value < 0:
            raise ValueError("Current value must be non-negative")
        
        if breach_percentage < 0:
            raise ValueError("Breach percentage must be non-negative")
        
        if not alert_message:
            raise ValueError("Alert message is required")
        
        if not recommended_action:
            raise ValueError("Recommended action is required")
    
    def _find_alert(self, portfolio_id: str, alert_id: str) -> Optional[RiskAlert]:
        """Find an alert by ID in the portfolio's alerts."""
        alerts = self.alerts_cache.get(portfolio_id, [])
        
        for alert in alerts:
            if str(alert.risk_alert_id) == alert_id:
                return alert
        
        return None
    
    def _add_to_history(
        self,
        portfolio_id: str,
        alert: RiskAlert,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add alert action to history."""
        if portfolio_id not in self.alert_history:
            self.alert_history[portfolio_id] = []
        
        history_entry = {
            "timestamp": datetime.utcnow(),
            "alert_id": str(alert.risk_alert_id),
            "action": action,
            "alert_summary": alert.get_alert_summary(),
            "metadata": metadata or {}
        }
        
        self.alert_history[portfolio_id].append(history_entry)
    
    def _send_alert_notifications(self, alert: RiskAlert) -> None:
        """Send alert notifications."""
        portfolio_id = alert.portfolio_id
        notification_configs = self.notification_configs.get(portfolio_id, [])
        
        for config in notification_configs:
            if not config.get("enabled", True):
                continue
            
            try:
                self._send_notification(alert, config)
                alert.mark_notification_sent()
            except Exception as e:
                logger.error(f"Failed to send notification via {config['channel']}: {str(e)}")
    
    def _send_acknowledgment_notification(self, alert: RiskAlert, acknowledged_by: str) -> None:
        """Send acknowledgment notification."""
        # Mock implementation - in practice, this would send actual notifications
        logger.info(f"Sending acknowledgment notification for alert {alert.risk_alert_id}")
    
    def _send_resolution_notification(self, alert: RiskAlert) -> None:
        """Send resolution notification."""
        # Mock implementation - in practice, this would send actual notifications
        logger.info(f"Sending resolution notification for alert {alert.risk_alert_id}")
    
    def _send_escalation_notification(self, alert: RiskAlert) -> None:
        """Send escalation notification."""
        # Mock implementation - in practice, this would send actual notifications
        logger.info(f"Sending escalation notification for alert {alert.risk_alert_id}")
    
    def _send_notification(self, alert: RiskAlert, config: Dict[str, Any]) -> None:
        """Send notification via specified channel."""
        channel = config["channel"]
        
        if channel == "email":
            self._send_email_notification(alert, config)
        elif channel == "dashboard":
            self._send_dashboard_notification(alert, config)
        elif channel == "api":
            self._send_api_notification(alert, config)
        elif channel == "sms":
            self._send_sms_notification(alert, config)
        else:
            logger.warning(f"Unknown notification channel: {channel}")
    
    def _send_email_notification(self, alert: RiskAlert, config: Dict[str, Any]) -> None:
        """Send email notification."""
        # Mock implementation
        logger.info(f"Sending email notification for alert {alert.risk_alert_id} to {config.get('recipients', [])}")
    
    def _send_dashboard_notification(self, alert: RiskAlert, config: Dict[str, Any]) -> None:
        """Send dashboard notification."""
        # Mock implementation
        logger.info(f"Sending dashboard notification for alert {alert.risk_alert_id}")
    
    def _send_api_notification(self, alert: RiskAlert, config: Dict[str, Any]) -> None:
        """Send API notification."""
        # Mock implementation
        logger.info(f"Sending API notification for alert {alert.risk_alert_id}")
    
    def _send_sms_notification(self, alert: RiskAlert, config: Dict[str, Any]) -> None:
        """Send SMS notification."""
        # Mock implementation
        logger.info(f"Sending SMS notification for alert {alert.risk_alert_id} to {config.get('recipients', [])}")
    
    def _validate_notification_config(self, config: Dict[str, Any]) -> bool:
        """Validate notification configuration."""
        required_fields = ["channel"]
        for field in required_fields:
            if field not in config:
                return False
        
        valid_channels = ["email", "dashboard", "api", "sms"]
        if config["channel"] not in valid_channels:
            return False
        
        return True
    
    def clear_alerts_cache(self, portfolio_id: Optional[str] = None) -> None:
        """Clear alerts cache for a portfolio or all portfolios."""
        if portfolio_id:
            if portfolio_id in self.alerts_cache:
                del self.alerts_cache[portfolio_id]
            logger.info(f"Cleared alerts cache for portfolio {portfolio_id}")
        else:
            self.alerts_cache.clear()
            self.notification_configs.clear()
            self.alert_history.clear()
            logger.info("Cleared all alerts cache")






















