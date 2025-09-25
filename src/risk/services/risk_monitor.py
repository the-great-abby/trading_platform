"""
Risk Monitor Service

Provides real-time risk monitoring and alerting capabilities for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.risk_metrics import RiskMetrics
from ..models.risk_limits import RiskLimits
from ..models.risk_alert import RiskAlert, AlertType, AlertSeverity, AlertStatus


logger = logging.getLogger(__name__)


@dataclass
class RiskMonitoringStatus:
    """Current risk monitoring status for a portfolio."""
    portfolio_id: str
    monitoring_timestamp: datetime
    risk_status: str  # "within_limits", "warning", "breach"
    current_metrics: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
    next_monitoring: datetime


class RiskMonitor:
    """
    Real-time risk monitoring service.
    
    Provides continuous monitoring of portfolio risk metrics and automatic
    alerting when risk limits are breached.
    """
    
    def __init__(self, risk_calculator=None, alert_manager=None):
        """
        Initialize risk monitor.
        
        Args:
            risk_calculator: VaR calculator service (optional)
            alert_manager: Risk alert manager service (optional)
        """
        self.risk_calculator = risk_calculator
        self.alert_manager = alert_manager
        self.monitoring_cache = {}
        self.active_alerts = {}
    
    def get_risk_monitoring_status(
        self,
        portfolio_id: str,
        include_current_metrics: bool = True,
        include_active_alerts: bool = True
    ) -> RiskMonitoringStatus:
        """
        Get current risk monitoring status for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            include_current_metrics: Whether to include current risk metrics
            include_active_alerts: Whether to include active alerts
            
        Returns:
            RiskMonitoringStatus object
        """
        logger.info(f"Getting risk monitoring status for portfolio {portfolio_id}")
        
        # Validate inputs
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        # Get current risk metrics
        current_metrics = {}
        if include_current_metrics:
            current_metrics = self._get_current_risk_metrics(portfolio_id)
        
        # Get active alerts
        active_alerts = []
        if include_active_alerts:
            active_alerts = self._get_active_alerts(portfolio_id)
        
        # Determine overall risk status
        risk_status = self._determine_risk_status(current_metrics, active_alerts)
        
        # Calculate next monitoring time (15 minutes from now)
        next_monitoring = datetime.utcnow() + timedelta(minutes=15)
        
        # Create monitoring status
        status = RiskMonitoringStatus(
            portfolio_id=portfolio_id,
            monitoring_timestamp=datetime.utcnow(),
            risk_status=risk_status,
            current_metrics=current_metrics,
            active_alerts=active_alerts,
            next_monitoring=next_monitoring
        )
        
        logger.info(f"Risk monitoring status for portfolio {portfolio_id}: {risk_status}")
        return status
    
    def monitor_risk_limits(
        self,
        portfolio_id: str,
        risk_limits: List[RiskLimits],
        current_portfolio_value: float,
        current_positions: List[Dict[str, Any]]
    ) -> List[RiskAlert]:
        """
        Monitor risk limits and generate alerts if breached.
        
        Args:
            portfolio_id: Portfolio identifier
            risk_limits: List of risk limits to monitor
            current_portfolio_value: Current portfolio value
            current_positions: Current portfolio positions
            
        Returns:
            List of new risk alerts generated
        """
        logger.info(f"Monitoring risk limits for portfolio {portfolio_id}")
        
        new_alerts = []
        
        for risk_limit in risk_limits:
            if not risk_limit.is_active:
                continue
            
            # Update current value based on portfolio state
            current_value = self._calculate_current_limit_value(
                risk_limit, current_portfolio_value, current_positions
            )
            
            # Update the limit with current value
            limit_status = risk_limit.update_current_value(current_value)
            
            # Check if limit is breached or in warning
            if risk_limit.is_breached():
                alert = self._create_breach_alert(risk_limit, limit_status)
                new_alerts.append(alert)
            elif risk_limit.is_warning():
                alert = self._create_warning_alert(risk_limit, limit_status)
                new_alerts.append(alert)
        
        # Store new alerts
        if new_alerts:
            self.active_alerts[portfolio_id] = new_alerts
        
        logger.info(f"Generated {len(new_alerts)} new risk alerts for portfolio {portfolio_id}")
        return new_alerts
    
    def _get_current_risk_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Get current risk metrics for a portfolio."""
        # Mock implementation - in practice, this would query latest risk metrics
        return {
            "var_95": 2500.0,
            "var_99": 3500.0,
            "portfolio_volatility": 0.18,
            "maximum_drawdown": 0.12,
            "sharpe_ratio": 1.25,
            "concentration_risk": 0.35,
            "correlation_risk": 0.28,
            "leverage_ratio": 1.0,
            "cash_ratio": 0.05,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _get_active_alerts(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get active alerts for a portfolio."""
        # Get alerts from cache
        alerts = self.active_alerts.get(portfolio_id, [])
        
        # Convert to dictionary format
        return [alert.to_dict() for alert in alerts if alert.is_active()]
    
    def _determine_risk_status(
        self,
        current_metrics: Dict[str, Any],
        active_alerts: List[Dict[str, Any]]
    ) -> str:
        """Determine overall risk status based on metrics and alerts."""
        # Check for critical alerts
        critical_alerts = [alert for alert in active_alerts if alert.get("alert_severity") == "critical"]
        if critical_alerts:
            return "breach"
        
        # Check for high severity alerts
        high_alerts = [alert for alert in active_alerts if alert.get("alert_severity") == "high"]
        if high_alerts:
            return "breach"
        
        # Check for warning alerts
        warning_alerts = [alert for alert in active_alerts if alert.get("alert_type") == "warning"]
        if warning_alerts:
            return "warning"
        
        # Check risk metrics thresholds
        if current_metrics:
            var_95 = current_metrics.get("var_95", 0)
            if var_95 > 5000:  # $5,000 VaR threshold
                return "warning"
            
            volatility = current_metrics.get("portfolio_volatility", 0)
            if volatility > 0.25:  # 25% volatility threshold
                return "warning"
        
        return "within_limits"
    
    def _calculate_current_limit_value(
        self,
        risk_limit: RiskLimits,
        portfolio_value: float,
        positions: List[Dict[str, Any]]
    ) -> float:
        """Calculate current value for a risk limit."""
        limit_type = risk_limit.limit_type
        
        if limit_type.value == "position_size":
            # Calculate largest position as percentage of portfolio
            if not positions:
                return 0.0
            
            max_position_value = max(
                pos.get("current_value", pos.get("weight", 0.0) * portfolio_value)
                for pos in positions
            )
            return max_position_value / portfolio_value if portfolio_value > 0 else 0.0
        
        elif limit_type.value == "daily_loss":
            # Calculate daily loss (mock implementation)
            return abs(self._calculate_daily_loss(portfolio_value, positions))
        
        elif limit_type.value == "sector_concentration":
            # Calculate largest sector concentration
            return self._calculate_max_sector_concentration(positions)
        
        elif limit_type.value == "var_limit":
            # Get current VaR from metrics
            return self._get_current_var(portfolio_value)
        
        elif limit_type.value == "volatility_limit":
            # Get current volatility from metrics
            return self._get_current_volatility()
        
        else:
            return 0.0
    
    def _calculate_daily_loss(
        self,
        portfolio_value: float,
        positions: List[Dict[str, Any]]
    ) -> float:
        """Calculate daily loss for the portfolio."""
        # Mock implementation - in practice, this would calculate actual daily P&L
        total_unrealized_pnl = sum(
            pos.get("unrealized_pnl", 0.0) for pos in positions
        )
        
        # Add some random daily movement
        import random
        random.seed(hash(str(positions)) % 2**32)
        daily_movement = random.uniform(-0.02, 0.02) * portfolio_value
        
        return total_unrealized_pnl + daily_movement
    
    def _calculate_max_sector_concentration(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate maximum sector concentration."""
        if not positions:
            return 0.0
        
        sector_weights = {}
        for position in positions:
            sector = position.get("sector", "unknown")
            weight = position.get("weight", 0.0)
            
            if sector not in sector_weights:
                sector_weights[sector] = 0.0
            sector_weights[sector] += weight
        
        return max(sector_weights.values()) if sector_weights else 0.0
    
    def _get_current_var(self, portfolio_value: float) -> float:
        """Get current VaR value."""
        # Mock implementation - in practice, this would get actual VaR
        return 2500.0  # $2,500 VaR
    
    def _get_current_volatility(self) -> float:
        """Get current portfolio volatility."""
        # Mock implementation - in practice, this would get actual volatility
        return 0.18  # 18% volatility
    
    def _create_breach_alert(
        self,
        risk_limit: RiskLimits,
        limit_status: Dict[str, Any]
    ) -> RiskAlert:
        """Create a breach alert for a risk limit."""
        breach_percentage = ((risk_limit.current_value - risk_limit.limit_value) / risk_limit.limit_value) * 100
        
        alert = RiskAlert(
            portfolio_id=risk_limit.portfolio_id,
            risk_limits_id=risk_limit.risk_limits_id,
            alert_type=AlertType.BREACH,
            alert_severity=AlertSeverity.HIGH,
            limit_name=risk_limit.limit_description,
            limit_value=risk_limit.limit_value,
            current_value=risk_limit.current_value,
            breach_percentage=breach_percentage,
            alert_message=f"Risk limit breached: {risk_limit.limit_description}. Current: {risk_limit.current_value:.2f}, Limit: {risk_limit.limit_value:.2f}",
            recommended_action=f"Take action: {risk_limit.enforcement_action.value}"
        )
        
        return alert
    
    def _create_warning_alert(
        self,
        risk_limit: RiskLimits,
        limit_status: Dict[str, Any]
    ) -> RiskAlert:
        """Create a warning alert for a risk limit."""
        utilization_pct = (risk_limit.current_value / risk_limit.limit_value) * 100
        
        alert = RiskAlert(
            portfolio_id=risk_limit.portfolio_id,
            risk_limits_id=risk_limit.risk_limits_id,
            alert_type=AlertType.WARNING,
            alert_severity=AlertSeverity.MEDIUM,
            limit_name=risk_limit.limit_description,
            limit_value=risk_limit.limit_value,
            current_value=risk_limit.current_value,
            breach_percentage=utilization_pct,
            alert_message=f"Risk limit warning: {risk_limit.limit_description}. Current: {risk_limit.current_value:.2f}, Limit: {risk_limit.limit_value:.2f} ({utilization_pct:.1f}%)",
            recommended_action="Monitor closely and consider reducing risk exposure"
        )
        
        return alert
    
    def get_monitoring_schedule(self, portfolio_id: str) -> Dict[str, Any]:
        """Get monitoring schedule for a portfolio."""
        # Mock implementation - in practice, this would query monitoring configuration
        return {
            "portfolio_id": portfolio_id,
            "monitoring_frequency_minutes": 15,
            "next_monitoring": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            "monitoring_enabled": True,
            "alert_channels": ["email", "dashboard", "api"],
            "escalation_rules": {
                "warning_timeout_minutes": 30,
                "breach_timeout_minutes": 5,
                "escalation_levels": ["risk_manager", "portfolio_manager", "compliance_officer"]
            }
        }
    
    def update_monitoring_frequency(
        self,
        portfolio_id: str,
        frequency_minutes: int
    ) -> bool:
        """Update monitoring frequency for a portfolio."""
        if frequency_minutes < 1:
            raise ValueError("Monitoring frequency must be at least 1 minute")
        
        # Mock implementation - in practice, this would update configuration
        logger.info(f"Updated monitoring frequency for portfolio {portfolio_id} to {frequency_minutes} minutes")
        return True
    
    def enable_monitoring(self, portfolio_id: str) -> bool:
        """Enable risk monitoring for a portfolio."""
        # Mock implementation - in practice, this would update monitoring status
        logger.info(f"Enabled risk monitoring for portfolio {portfolio_id}")
        return True
    
    def disable_monitoring(self, portfolio_id: str) -> bool:
        """Disable risk monitoring for a portfolio."""
        # Mock implementation - in practice, this would update monitoring status
        logger.info(f"Disabled risk monitoring for portfolio {portfolio_id}")
        return True
    
    def acknowledge_alert(
        self,
        portfolio_id: str,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge a risk alert."""
        # Find alert in active alerts
        alerts = self.active_alerts.get(portfolio_id, [])
        for alert in alerts:
            if str(alert.risk_alert_id) == alert_id:
                alert.acknowledge(acknowledged_by)
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True
        
        logger.warning(f"Alert {alert_id} not found for portfolio {portfolio_id}")
        return False
    
    def resolve_alert(
        self,
        portfolio_id: str,
        alert_id: str
    ) -> bool:
        """Resolve a risk alert."""
        # Find alert in active alerts
        alerts = self.active_alerts.get(portfolio_id, [])
        for alert in alerts:
            if str(alert.risk_alert_id) == alert_id:
                alert.resolve()
                logger.info(f"Alert {alert_id} resolved")
                return True
        
        logger.warning(f"Alert {alert_id} not found for portfolio {portfolio_id}")
        return False
    
    def get_alert_history(
        self,
        portfolio_id: str,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alert history for a portfolio."""
        # Mock implementation - in practice, this would query database
        alerts = self.active_alerts.get(portfolio_id, [])
        
        # Filter by status if specified
        if status_filter:
            alerts = [alert for alert in alerts if alert.alert_status.value == status_filter]
        
        # Convert to dictionary format and limit results
        return [alert.to_dict() for alert in alerts[:limit]]
    
    def clear_monitoring_cache(self, portfolio_id: Optional[str] = None) -> None:
        """Clear monitoring cache for a portfolio or all portfolios."""
        if portfolio_id:
            if portfolio_id in self.monitoring_cache:
                del self.monitoring_cache[portfolio_id]
            logger.info(f"Cleared monitoring cache for portfolio {portfolio_id}")
        else:
            self.monitoring_cache.clear()
            self.active_alerts.clear()
            logger.info("Cleared all monitoring cache")

