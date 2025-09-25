"""
Comprehensive Risk Management Framework

This package provides institutional-grade risk management capabilities for algorithmic trading portfolios,
including VaR calculations, stress testing, correlation analysis, compliance reporting, and risk monitoring.
"""

__version__ = "1.0.0"
__author__ = "Trading System Team"

# Core risk management components
from .models import (
    RiskMetrics,
    StressTestResult,
    CorrelationAnalysis,
    ComplianceReport,
    RiskLimits,
    RiskAlert,
    RiskContributions,
)

from .services import (
    VaRCalculator,
    StressTester,
    CorrelationAnalyzer,
    ComplianceReporter,
    RiskMonitor,
    RiskLimitsManager,
    RiskAlertManager,
)

__all__ = [
    # Models
    "RiskMetrics",
    "StressTestResult", 
    "CorrelationAnalysis",
    "ComplianceReport",
    "RiskLimits",
    "RiskAlert",
    "RiskContributions",
    # Services
    "VaRCalculator",
    "StressTester",
    "CorrelationAnalyzer", 
    "ComplianceReporter",
    "RiskMonitor",
    "RiskLimitsManager",
    "RiskAlertManager",
]