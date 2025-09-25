"""
Compliance Reporter Service

Provides regulatory compliance reporting and audit trail management for the
comprehensive risk management framework.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import json
from dataclasses import dataclass

from ..models.compliance_report import ComplianceReport, ReportType, ComplianceStatus, ReportFormat


logger = logging.getLogger(__name__)


class ComplianceReporter:
    """
    Regulatory compliance reporting service.
    
    Provides comprehensive compliance reports including trade documentation,
    audit trails, and regulatory status monitoring.
    """
    
    def __init__(self, risk_metrics_provider=None, trade_data_provider=None):
        """
        Initialize compliance reporter.
        
        Args:
            risk_metrics_provider: Provider for risk metrics data (optional)
            trade_data_provider: Provider for trade data (optional)
        """
        self.risk_metrics_provider = risk_metrics_provider
        self.trade_data_provider = trade_data_provider
        self.report_cache = {}
    
    def generate_compliance_report(
        self,
        portfolio_id: str,
        report_type: str = "daily",
        report_period_start: Optional[date] = None,
        report_period_end: Optional[date] = None,
        format: str = "JSON",
        include_trade_documentation: bool = True,
        include_audit_trail: bool = True,
        include_position_reporting: bool = True,
        include_risk_metrics: bool = True,
        include_regulatory_checks: bool = True
    ) -> ComplianceReport:
        """
        Generate a comprehensive compliance report.
        
        Args:
            portfolio_id: Portfolio identifier
            report_type: Type of report ('daily', 'weekly', 'monthly', 'ad_hoc')
            report_period_start: Start date for report period
            report_period_end: End date for report period
            format: Report format ('PDF', 'CSV', 'JSON')
            include_trade_documentation: Whether to include trade documentation
            include_audit_trail: Whether to include audit trail
            include_position_reporting: Whether to include position reporting
            include_risk_metrics: Whether to include risk metrics summary
            include_regulatory_checks: Whether to include regulatory compliance checks
            
        Returns:
            ComplianceReport object
        """
        logger.info(f"Generating {report_type} compliance report for portfolio {portfolio_id}")
        
        # Validate inputs
        self._validate_inputs(portfolio_id, report_type, report_period_start, report_period_end, format)
        
        # Set default dates if not provided
        if not report_period_end:
            report_period_end = date.today()
        
        if not report_period_start:
            report_period_start = self._calculate_report_start_date(report_type, report_period_end)
        
        # Generate report content
        audit_trail = {}
        if include_audit_trail:
            audit_trail = self._generate_audit_trail(portfolio_id, report_period_start, report_period_end)
        
        trade_documentation = {}
        if include_trade_documentation:
            trade_documentation = self._generate_trade_documentation(portfolio_id, report_period_start, report_period_end)
        
        position_reporting = {}
        if include_position_reporting:
            position_reporting = self._generate_position_reporting(portfolio_id, report_period_end)
        
        risk_metrics_summary = {}
        if include_risk_metrics:
            risk_metrics_summary = self._generate_risk_metrics_summary(portfolio_id, report_period_end)
        
        regulatory_checks = {}
        if include_regulatory_checks:
            regulatory_checks = self._perform_regulatory_checks(portfolio_id, report_period_start, report_period_end)
        
        # Detect violations and generate recommendations
        violations_detected = self._detect_compliance_violations(
            audit_trail, trade_documentation, position_reporting, risk_metrics_summary, regulatory_checks
        )
        
        recommendations = self._generate_compliance_recommendations(violations_detected)
        
        # Determine overall compliance status
        compliance_status = self._determine_compliance_status(violations_detected)
        
        # Create compliance report
        report = ComplianceReport(
            portfolio_id=portfolio_id,
            report_type=ReportType(report_type),
            report_period_start=report_period_start,
            report_period_end=report_period_end,
            compliance_status=compliance_status,
            audit_trail=audit_trail,
            trade_documentation=trade_documentation,
            position_reporting=position_reporting,
            risk_metrics_summary=risk_metrics_summary,
            regulatory_checks=regulatory_checks,
            violations_detected=violations_detected,
            recommendations=recommendations,
            report_format=ReportFormat(format),
            generated_by="compliance_reporter_service"
        )
        
        # Generate report file if needed
        if format in ["PDF", "CSV"]:
            report.report_file_path = self._generate_report_file(report, format)
        
        logger.info(f"Completed {report_type} compliance report for portfolio {portfolio_id}")
        return report
    
    def _validate_inputs(
        self,
        portfolio_id: str,
        report_type: str,
        report_period_start: Optional[date],
        report_period_end: Optional[date],
        format: str
    ) -> None:
        """Validate compliance report inputs."""
        if not portfolio_id:
            raise ValueError("Portfolio ID is required")
        
        if report_type not in ["daily", "weekly", "monthly", "ad_hoc"]:
            raise ValueError(f"Invalid report type: {report_type}")
        
        if format not in ["PDF", "CSV", "JSON"]:
            raise ValueError(f"Invalid report format: {format}")
        
        if report_period_start and report_period_end:
            if report_period_end <= report_period_start:
                raise ValueError("Report period end must be after report period start")
    
    def _calculate_report_start_date(self, report_type: str, report_period_end: date) -> date:
        """Calculate report start date based on report type."""
        if report_type == "daily":
            return report_period_end
        elif report_type == "weekly":
            return report_period_end - timedelta(days=6)
        elif report_type == "monthly":
            # Approximate month as 30 days
            return report_period_end - timedelta(days=29)
        else:  # ad_hoc
            return report_period_end - timedelta(days=6)
    
    def _generate_audit_trail(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate audit trail for the report period."""
        # Mock implementation - in practice, this would query audit logs
        audit_entries = []
        
        current_date = start_date
        while current_date <= end_date:
            # Generate mock audit entries
            audit_entries.extend([
                {
                    "timestamp": datetime.combine(current_date, datetime.min.time()).isoformat(),
                    "action": "portfolio_rebalance",
                    "user": "system",
                    "details": f"Portfolio {portfolio_id} rebalanced",
                    "ip_address": "127.0.0.1",
                    "session_id": f"session_{current_date.strftime('%Y%m%d')}"
                },
                {
                    "timestamp": datetime.combine(current_date, datetime.min.time().replace(hour=9)).isoformat(),
                    "action": "risk_check",
                    "user": "risk_manager",
                    "details": f"Risk metrics calculated for portfolio {portfolio_id}",
                    "ip_address": "192.168.1.100",
                    "session_id": f"session_{current_date.strftime('%Y%m%d')}"
                }
            ])
            current_date += timedelta(days=1)
        
        return {
            "report_period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_entries": len(audit_entries),
            "entries": audit_entries,
            "summary": {
                "portfolio_rebalances": len([e for e in audit_entries if e["action"] == "portfolio_rebalance"]),
                "risk_checks": len([e for e in audit_entries if e["action"] == "risk_check"]),
                "unique_users": len(set(e["user"] for e in audit_entries))
            }
        }
    
    def _generate_trade_documentation(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate trade documentation for the report period."""
        # Mock implementation - in practice, this would query trade data
        trades = []
        
        # Generate mock trades
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        for i in range(10):  # Mock 10 trades
            trade_date = start_date + timedelta(days=i % (end_date - start_date).days)
            symbol = symbols[i % len(symbols)]
            
            trades.append({
                "trade_id": f"trade_{i:04d}",
                "timestamp": datetime.combine(trade_date, datetime.min.time().replace(hour=10, minute=30)).isoformat(),
                "symbol": symbol,
                "action": "BUY" if i % 2 == 0 else "SELL",
                "quantity": 100 + (i * 50),
                "price": 150.0 + (i * 5.0),
                "total_value": (100 + (i * 50)) * (150.0 + (i * 5.0)),
                "commission": 1.0,
                "strategy": "momentum" if i % 2 == 0 else "mean_reversion",
                "execution_venue": "NYSE",
                "order_type": "MARKET"
            })
        
        return {
            "report_period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_trades": len(trades),
            "trades": trades,
            "summary": {
                "total_buy_trades": len([t for t in trades if t["action"] == "BUY"]),
                "total_sell_trades": len([t for t in trades if t["action"] == "SELL"]),
                "total_volume": sum(t["total_value"] for t in trades),
                "total_commission": sum(t["commission"] for t in trades),
                "unique_symbols": len(set(t["symbol"] for t in trades))
            }
        }
    
    def _generate_position_reporting(
        self,
        portfolio_id: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """Generate position reporting as of a specific date."""
        # Mock implementation - in practice, this would query position data
        positions = [
            {
                "symbol": "AAPL",
                "quantity": 1000,
                "market_value": 150000.0,
                "cost_basis": 145000.0,
                "unrealized_pnl": 5000.0,
                "sector": "technology",
                "weight": 0.30
            },
            {
                "symbol": "MSFT",
                "quantity": 500,
                "market_value": 120000.0,
                "cost_basis": 115000.0,
                "unrealized_pnl": 5000.0,
                "sector": "technology",
                "weight": 0.24
            },
            {
                "symbol": "JPM",
                "quantity": 200,
                "market_value": 30000.0,
                "cost_basis": 31000.0,
                "unrealized_pnl": -1000.0,
                "sector": "financial",
                "weight": 0.06
            }
        ]
        
        return {
            "as_of_date": as_of_date.isoformat(),
            "total_positions": len(positions),
            "positions": positions,
            "summary": {
                "total_market_value": sum(p["market_value"] for p in positions),
                "total_cost_basis": sum(p["cost_basis"] for p in positions),
                "total_unrealized_pnl": sum(p["unrealized_pnl"] for p in positions),
                "sector_concentration": {
                    sector: sum(p["weight"] for p in positions if p["sector"] == sector)
                    for sector in set(p["sector"] for p in positions)
                }
            }
        }
    
    def _generate_risk_metrics_summary(
        self,
        portfolio_id: str,
        as_of_date: date
    ) -> Dict[str, Any]:
        """Generate risk metrics summary."""
        # Mock implementation - in practice, this would query risk metrics
        return {
            "as_of_date": as_of_date.isoformat(),
            "var_95": 2500.0,
            "var_99": 3500.0,
            "expected_shortfall_95": 3200.0,
            "expected_shortfall_99": 4500.0,
            "portfolio_volatility": 0.18,
            "maximum_drawdown": 0.12,
            "sharpe_ratio": 1.25,
            "sortino_ratio": 1.45,
            "calmar_ratio": 1.08,
            "concentration_risk": 0.35,
            "correlation_risk": 0.28,
            "leverage_ratio": 1.0,
            "cash_ratio": 0.05
        }
    
    def _perform_regulatory_checks(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Perform regulatory compliance checks."""
        # Mock implementation - in practice, this would perform actual regulatory checks
        checks = [
            {
                "check_name": "position_size_limit",
                "status": "PASS",
                "description": "All positions within size limits",
                "details": "Maximum position weight: 30% (limit: 40%)"
            },
            {
                "check_name": "sector_concentration",
                "status": "WARNING",
                "description": "Technology sector concentration high",
                "details": "Technology sector weight: 54% (limit: 50%)"
            },
            {
                "check_name": "daily_loss_limit",
                "status": "PASS",
                "description": "Daily losses within limits",
                "details": "Maximum daily loss: $1,200 (limit: $2,000)"
            },
            {
                "check_name": "var_limit",
                "status": "PASS",
                "description": "VaR within acceptable limits",
                "details": "VaR 95%: $2,500 (limit: $5,000)"
            },
            {
                "check_name": "wash_sale_compliance",
                "status": "PASS",
                "description": "No wash sale violations detected",
                "details": "All trades comply with wash sale rules"
            }
        ]
        
        return {
            "report_period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_checks": len(checks),
            "checks": checks,
            "summary": {
                "passed": len([c for c in checks if c["status"] == "PASS"]),
                "warnings": len([c for c in checks if c["status"] == "WARNING"]),
                "failed": len([c for c in checks if c["status"] == "FAIL"])
            }
        }
    
    def _detect_compliance_violations(
        self,
        audit_trail: Dict[str, Any],
        trade_documentation: Dict[str, Any],
        position_reporting: Dict[str, Any],
        risk_metrics_summary: Dict[str, Any],
        regulatory_checks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect compliance violations from report data."""
        violations = []
        
        # Check regulatory compliance violations
        for check in regulatory_checks.get("checks", []):
            if check["status"] == "FAIL":
                violations.append({
                    "violation_type": "regulatory_compliance",
                    "description": f"Regulatory check failed: {check['check_name']}",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif check["status"] == "WARNING":
                violations.append({
                    "violation_type": "regulatory_warning",
                    "description": f"Regulatory warning: {check['check_name']}",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check position concentration violations
        sector_concentrations = position_reporting.get("summary", {}).get("sector_concentration", {})
        for sector, weight in sector_concentrations.items():
            if weight > 0.5:  # 50% sector limit
                violations.append({
                    "violation_type": "sector_concentration",
                    "description": f"Sector concentration limit exceeded for {sector}: {weight:.1%}",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check risk metric violations
        if risk_metrics_summary.get("var_95", 0) > 5000:  # $5,000 VaR limit
            violations.append({
                "violation_type": "var_limit",
                "description": f"VaR limit exceeded: ${risk_metrics_summary['var_95']:.0f}",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return violations
    
    def _generate_compliance_recommendations(
        self,
        violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate compliance recommendations based on violations."""
        recommendations = []
        
        for violation in violations:
            violation_type = violation["violation_type"]
            severity = violation["severity"]
            
            if violation_type == "sector_concentration":
                recommendations.append("Consider diversifying portfolio across more sectors to reduce concentration risk")
            elif violation_type == "var_limit":
                recommendations.append("Review portfolio risk exposure and consider reducing position sizes or hedging")
            elif violation_type == "regulatory_compliance":
                recommendations.append("Address regulatory compliance issues immediately to avoid penalties")
            elif violation_type == "regulatory_warning":
                recommendations.append("Monitor regulatory warnings and take preventive action")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Portfolio appears to be in compliance with regulatory requirements")
        
        recommendations.append("Continue regular monitoring and reporting")
        recommendations.append("Maintain comprehensive audit trails for all trading activities")
        
        return recommendations
    
    def _determine_compliance_status(self, violations: List[Dict[str, Any]]) -> ComplianceStatus:
        """Determine overall compliance status based on violations."""
        if not violations:
            return ComplianceStatus.COMPLIANT
        
        # Check for high severity violations
        high_severity_violations = [v for v in violations if v["severity"] == "high"]
        if high_severity_violations:
            return ComplianceStatus.VIOLATION
        
        # Check for medium severity violations
        medium_severity_violations = [v for v in violations if v["severity"] == "medium"]
        if medium_severity_violations:
            return ComplianceStatus.WARNING
        
        return ComplianceStatus.COMPLIANT
    
    def _generate_report_file(self, report: ComplianceReport, format: str) -> str:
        """Generate report file in specified format."""
        # Mock implementation - in practice, this would generate actual files
        filename = report.get_report_filename()
        
        if format == "CSV":
            # Generate CSV content
            content = self._generate_csv_content(report)
        elif format == "PDF":
            # Generate PDF content (mock)
            content = "PDF content would be generated here"
        else:
            content = json.dumps(report.to_dict(), indent=2)
        
        # In practice, this would write to actual file system
        file_path = f"/tmp/compliance_reports/{filename}"
        
        logger.info(f"Generated {format} report file: {file_path}")
        return file_path
    
    def _generate_csv_content(self, report: ComplianceReport) -> str:
        """Generate CSV content for compliance report."""
        # Mock CSV generation
        csv_lines = [
            "Report Type,Portfolio ID,Period Start,Period End,Compliance Status",
            f"{report.report_type.value},{report.portfolio_id},{report.report_period_start},{report.report_period_end},{report.compliance_status.value}",
            "",
            "Violations,Severity,Description",
        ]
        
        for violation in report.violations_detected:
            csv_lines.append(f"{violation['violation_type']},{violation['severity']},{violation['description']}")
        
        return "\n".join(csv_lines)
    
    def get_compliance_history(
        self,
        portfolio_id: str,
        limit: int = 30
    ) -> List[ComplianceReport]:
        """Get compliance report history for a portfolio."""
        # Mock implementation - in practice, this would query database
        return []
    
    def validate_report_parameters(
        self,
        report_type: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> bool:
        """Validate compliance report parameters."""
        try:
            # Validate report type
            ReportType(report_type)
            
            # Validate dates
            if start_date and end_date:
                if end_date <= start_date:
                    return False
            
            return True
            
        except ValueError:
            return False
    
    def clear_cache(self) -> None:
        """Clear report cache."""
        self.report_cache.clear()
        logger.info("Compliance report cache cleared")

