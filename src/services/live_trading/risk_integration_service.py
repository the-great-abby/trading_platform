"""
Risk Integration Service

Connects live trading system to shared risk management components.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskIntegrationConfig:
    """Configuration for risk integration service."""
    risk_service_url: str = "http://enhanced-risk-management-service:80"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class RiskIntegrationService:
    """Service for integrating with shared risk management components."""
    
    def __init__(self, config: Optional[RiskIntegrationConfig] = None):
        """Initialize the risk integration service."""
        self.config = config or RiskIntegrationConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.risk_service_url,
            timeout=self.config.timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
        )
    
    async def assess_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess portfolio risk using shared risk management service.
        
        Args:
            portfolio_data: Portfolio data including positions and values
            
        Returns:
            Risk assessment results
        """
        try:
            logger.info("Assessing portfolio risk via shared risk service")
            
            response = await self.client.post("/api/v1/risk/assess", json=portfolio_data)
            
            if response.status_code == 200:
                risk_assessment = response.json()
                logger.info("Portfolio risk assessment completed")
                return risk_assessment
            else:
                logger.error(f"Risk assessment failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Risk assessment failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error in portfolio risk assessment: {str(e)}")
            return {
                "success": False,
                "error": "Risk assessment service unavailable",
                "details": str(e)
            }
    
    async def calculate_var(self, portfolio_id: str, confidence_levels: List[float] = None) -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            confidence_levels: List of confidence levels (e.g., [0.95, 0.99])
            
        Returns:
            VaR calculation results
        """
        try:
            if confidence_levels is None:
                confidence_levels = [0.95, 0.99]
            
            logger.info(f"Calculating VaR for portfolio {portfolio_id}")
            
            var_request = {
                "portfolio_id": portfolio_id,
                "confidence_levels": confidence_levels,
                "calculation_method": "historical_simulation",
                "data_period_days": 252,
                "include_expected_shortfall": True,
                "include_risk_contributions": True
            }
            
            response = await self.client.post("/api/v1/risk/var-calculation", json=var_request)
            
            if response.status_code == 200:
                var_results = response.json()
                logger.info(f"VaR calculation completed for portfolio {portfolio_id}")
                return var_results
            else:
                logger.error(f"VaR calculation failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"VaR calculation failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error in VaR calculation: {str(e)}")
            return {
                "success": False,
                "error": "VaR calculation service unavailable",
                "details": str(e)
            }
    
    async def run_stress_test(self, portfolio_id: str, scenarios: List[str] = None) -> Dict[str, Any]:
        """
        Run stress test on a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            scenarios: List of stress test scenarios
            
        Returns:
            Stress test results
        """
        try:
            if scenarios is None:
                scenarios = ["market_crash", "volatility_spike", "interest_rate_shock"]
            
            logger.info(f"Running stress test for portfolio {portfolio_id}")
            
            stress_test_request = {
                "portfolio_id": portfolio_id,
                "scenarios": scenarios,
                "include_position_impacts": True,
                "include_sector_impacts": True
            }
            
            response = await self.client.post("/api/v1/risk/stress-test", json=stress_test_request)
            
            if response.status_code == 200:
                stress_results = response.json()
                logger.info(f"Stress test completed for portfolio {portfolio_id}")
                return stress_results
            else:
                logger.error(f"Stress test failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Stress test failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error in stress test: {str(e)}")
            return {
                "success": False,
                "error": "Stress test service unavailable",
                "details": str(e)
            }
    
    async def analyze_correlations(self, portfolio_id: str, rolling_period_days: int = 30) -> Dict[str, Any]:
        """
        Analyze correlations within a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            rolling_period_days: Rolling period for correlation analysis
            
        Returns:
            Correlation analysis results
        """
        try:
            logger.info(f"Analyzing correlations for portfolio {portfolio_id}")
            
            correlation_request = {
                "portfolio_id": portfolio_id,
                "rolling_period_days": rolling_period_days,
                "include_sector_analysis": True,
                "include_diversification_recommendations": True
            }
            
            response = await self.client.post("/api/v1/risk/correlation-analysis", json=correlation_request)
            
            if response.status_code == 200:
                correlation_results = response.json()
                logger.info(f"Correlation analysis completed for portfolio {portfolio_id}")
                return correlation_results
            else:
                logger.error(f"Correlation analysis failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Correlation analysis failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}")
            return {
                "success": False,
                "error": "Correlation analysis service unavailable",
                "details": str(e)
            }
    
    async def get_compliance_report(self, portfolio_id: str, report_type: str = "daily") -> Dict[str, Any]:
        """
        Get compliance report for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            report_type: Type of compliance report (daily, weekly, monthly)
            
        Returns:
            Compliance report
        """
        try:
            logger.info(f"Generating {report_type} compliance report for portfolio {portfolio_id}")
            
            params = {
                "portfolio_id": portfolio_id,
                "report_type": report_type,
                "format": "JSON"
            }
            
            response = await self.client.get("/api/v1/risk/compliance-report", params=params)
            
            if response.status_code == 200:
                compliance_report = response.json()
                logger.info(f"Compliance report generated for portfolio {portfolio_id}")
                return compliance_report
            else:
                logger.error(f"Compliance report failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Compliance report failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {
                "success": False,
                "error": "Compliance report service unavailable",
                "details": str(e)
            }
    
    async def get_risk_monitoring_status(self, portfolio_id: str) -> Dict[str, Any]:
        """
        Get risk monitoring status for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Risk monitoring status
        """
        try:
            logger.info(f"Getting risk monitoring status for portfolio {portfolio_id}")
            
            params = {"portfolio_id": portfolio_id}
            
            response = await self.client.get("/api/v1/risk/monitoring", params=params)
            
            if response.status_code == 200:
                monitoring_status = response.json()
                logger.info(f"Risk monitoring status retrieved for portfolio {portfolio_id}")
                return monitoring_status
            else:
                logger.error(f"Risk monitoring status failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Risk monitoring status failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error getting risk monitoring status: {str(e)}")
            return {
                "success": False,
                "error": "Risk monitoring service unavailable",
                "details": str(e)
            }
    
    async def configure_risk_limits(self, portfolio_id: str, limits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Configure risk limits for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            limits: List of risk limit configurations
            
        Returns:
            Risk limit configuration results
        """
        try:
            logger.info(f"Configuring risk limits for portfolio {portfolio_id}")
            
            limits_request = {
                "portfolio_id": portfolio_id,
                "limits": limits
            }
            
            response = await self.client.put("/api/v1/risk/limits", json=limits_request)
            
            if response.status_code == 200:
                limits_result = response.json()
                logger.info(f"Risk limits configured for portfolio {portfolio_id}")
                return limits_result
            else:
                logger.error(f"Risk limits configuration failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Risk limits configuration failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error configuring risk limits: {str(e)}")
            return {
                "success": False,
                "error": "Risk limits configuration service unavailable",
                "details": str(e)
            }
    
    async def get_risk_alerts(self, portfolio_id: str, status: str = "active", limit: int = 100) -> Dict[str, Any]:
        """
        Get risk alerts for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            status: Alert status filter (active, resolved, all)
            limit: Maximum number of alerts to return
            
        Returns:
            Risk alerts
        """
        try:
            logger.info(f"Getting risk alerts for portfolio {portfolio_id}")
            
            params = {
                "portfolio_id": portfolio_id,
                "status": status,
                "limit": limit
            }
            
            response = await self.client.get("/api/v1/risk/alerts", params=params)
            
            if response.status_code == 200:
                alerts = response.json()
                logger.info(f"Risk alerts retrieved for portfolio {portfolio_id}")
                return alerts
            else:
                logger.error(f"Risk alerts retrieval failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Risk alerts retrieval failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error getting risk alerts: {str(e)}")
            return {
                "success": False,
                "error": "Risk alerts service unavailable",
                "details": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on risk integration service."""
        try:
            start_time = datetime.utcnow()
            response = await self.client.get("/health")
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "service_url": self.config.risk_service_url,
                    "timestamp": end_time.isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Health check failed: {response.status_code}",
                    "service_url": self.config.risk_service_url,
                    "timestamp": end_time.isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service_url": self.config.risk_service_url,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the HTTP client."""
        try:
            await self.client.aclose()
            logger.info("Risk integration service client closed")
        except Exception as e:
            logger.error(f"Error closing risk integration service client: {str(e)}")
