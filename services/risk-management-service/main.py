"""
Risk Management Service Main Application

FastAPI application for the comprehensive risk management framework.
Provides VaR calculations, stress testing, correlation analysis, compliance reporting,
risk monitoring, limits management, and alerting capabilities.
"""

import logging
import time
import traceback
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import UUID
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import risk management services
from src.risk.services.var_calculator import VaRCalculator, VaRCalculationResult
from src.risk.services.stress_tester import StressTester
from src.risk.services.correlation_analyzer import CorrelationAnalyzer
from src.risk.services.compliance_reporter import ComplianceReporter
from src.risk.services.risk_monitor import RiskMonitor
from src.risk.services.risk_limits_manager import RiskLimitsManager
from src.risk.services.risk_alert_manager import RiskAlertManager

# Import integrations
from src.risk.integrations.portfolio_service_integration import get_portfolio_integration
from src.risk.integrations.trading_engine_integration import get_trading_engine_integration
from src.risk.integrations.market_data_service_integration import get_market_data_integration
from src.risk.integrations.data_synchronization_service import get_data_sync_service
from src.risk.integrations.cross_service_monitoring import get_cross_service_monitoring

# Import monitoring
from src.risk.monitoring.prometheus_metrics import get_metrics, record_api_metrics
from src.risk.monitoring.health_monitor import get_health_monitor
from src.risk.logging.risk_logging_config import get_risk_logger, configure_risk_logging

# Import database
from src.risk.database.connection import initialize_database, close_database, health_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for API requests and responses
class VaRCalculationRequest(BaseModel):
    """Request model for VaR calculation."""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    confidence_levels: List[float] = Field(default=[0.95, 0.99], description="Confidence levels for VaR calculation")
    calculation_method: str = Field(default="historical_simulation", description="Calculation method")
    data_period_days: int = Field(default=252, description="Historical data period in days")
    include_expected_shortfall: bool = Field(default=True, description="Include expected shortfall calculation")
    include_risk_contributions: bool = Field(default=True, description="Include risk contributions analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "confidence_levels": [0.95, 0.99],
                "calculation_method": "historical_simulation",
                "data_period_days": 252,
                "include_expected_shortfall": True,
                "include_risk_contributions": True
            }
        }


class StressTestRequest(BaseModel):
    """Request model for stress testing."""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    scenarios: Optional[List[str]] = Field(default=None, description="Standard scenarios to run")
    custom_scenarios: Optional[List[Dict[str, Any]]] = Field(default=None, description="Custom scenarios")
    include_position_impacts: bool = Field(default=True, description="Include position-level impacts")
    include_sector_impacts: bool = Field(default=True, description="Include sector-level impacts")
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenarios": ["market_crash", "volatility_spike", "rate_shock"],
                "include_position_impacts": True,
                "include_sector_impacts": True
            }
        }


class CorrelationAnalysisRequest(BaseModel):
    """Request model for correlation analysis."""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    rolling_period_days: int = Field(default=30, description="Rolling correlation period in days")
    include_sector_analysis: bool = Field(default=True, description="Include sector-level analysis")
    include_diversification_recommendations: bool = Field(default=True, description="Include diversification recommendations")
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "rolling_period_days": 30,
                "include_sector_analysis": True,
                "include_diversification_recommendations": True
            }
        }


class RiskLimitsRequest(BaseModel):
    """Request model for risk limits configuration."""
    portfolio_id: str = Field(..., description="Portfolio identifier")
    limits: List[Dict[str, Any]] = Field(..., description="Risk limits configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "limits": [
                    {
                        "limit_type": "position_size",
                        "limit_value": 0.15,
                        "limit_unit": "percentage",
                        "enforcement_action": "alert"
                    }
                ]
            }
        }


class APIResponse(BaseModel):
    """Standard API response model."""
    status: str = Field(..., description="Response status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error information")
    timestamp: str = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")


# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Risk Management Service")
    initialize_database()
    yield
    # Shutdown
    logger.info("Shutting down Risk Management Service")
    close_database()


# Create FastAPI application
app = FastAPI(
    title="Risk Management Service",
    description="Comprehensive risk management framework for algorithmic trading portfolios",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


# Global service instances
var_calculator = VaRCalculator()
stress_tester = StressTester()
correlation_analyzer = CorrelationAnalyzer()
compliance_reporter = ComplianceReporter()
risk_monitor = RiskMonitor()
risk_limits_manager = RiskLimitsManager()
risk_alert_manager = RiskAlertManager()


# Utility functions
def generate_request_id() -> str:
    """Generate unique request ID."""
    return f"req_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"


def create_error_response(
    error_code: str,
    error_message: str,
    status_code: int = 400,
    request_id: str = None
) -> JSONResponse:
    """Create standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": {
                "code": error_code,
                "message": error_message
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or generate_request_id()
        }
    )


def create_success_response(
    data: Dict[str, Any],
    request_id: str = None
) -> Dict[str, Any]:
    """Create standardized success response."""
    return {
        "status": "success",
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or generate_request_id()
    }


def get_mock_portfolio_data(portfolio_id: str) -> List[Dict[str, Any]]:
    """Get mock portfolio data for testing."""
    return [
        {
            "symbol": "AAPL",
            "weight": 0.30,
            "current_value": 30000.0,
            "sector": "technology",
            "asset_type": "stock"
        },
        {
            "symbol": "MSFT",
            "weight": 0.25,
            "current_value": 25000.0,
            "sector": "technology",
            "asset_type": "stock"
        },
        {
            "symbol": "JPM",
            "weight": 0.20,
            "current_value": 20000.0,
            "sector": "financial",
            "asset_type": "stock"
        },
        {
            "symbol": "XOM",
            "weight": 0.15,
            "current_value": 15000.0,
            "sector": "energy",
            "asset_type": "stock"
        },
        {
            "symbol": "JNJ",
            "weight": 0.10,
            "current_value": 10000.0,
            "sector": "healthcare",
            "asset_type": "stock"
        }
    ]


# API Routes

@app.get("/health", response_model=APIResponse)
async def health_check_endpoint():
    """Health check endpoint."""
    try:
        # Check database health
        db_health = health_check()
        
        # Check service health
        service_health = {
            "database": db_health,
            "services": {
                "var_calculator": "healthy",
                "stress_tester": "healthy",
                "correlation_analyzer": "healthy",
                "compliance_reporter": "healthy",
                "risk_monitor": "healthy",
                "risk_limits_manager": "healthy",
                "risk_alert_manager": "healthy"
            }
        }
        
        return create_success_response(service_health)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response(
            "HEALTH_CHECK_FAILED",
            "Service health check failed",
            500
        )


@app.post("/api/risk/var-calculation", response_model=APIResponse)
async def calculate_var(request: VaRCalculationRequest):
    """Calculate Value at Risk for a portfolio."""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        logger.info(f"VaR calculation request {request_id} for portfolio {request.portfolio_id}")
        
        # Get portfolio data (mock implementation)
        portfolio_positions = get_mock_portfolio_data(request.portfolio_id)
        portfolio_value = sum(pos["current_value"] for pos in portfolio_positions)
        
        # Calculate VaR
        result = var_calculator.calculate_var(
            portfolio_id=request.portfolio_id,
            portfolio_positions=portfolio_positions,
            confidence_levels=request.confidence_levels,
            calculation_method=request.calculation_method,
            data_period_days=request.data_period_days,
            include_expected_shortfall=request.include_expected_shortfall,
            include_risk_contributions=request.include_risk_contributions,
            portfolio_value=portfolio_value
        )
        
        # Calculate response time
        calculation_duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "portfolio_id": request.portfolio_id,
            "calculation_timestamp": result.var_metrics.calculation_timestamp.isoformat(),
            "var_metrics": {
                "var_95": result.var_metrics.var_95,
                "var_99": result.var_metrics.var_99,
                "portfolio_volatility": result.var_metrics.portfolio_volatility,
                "confidence_intervals": result.var_metrics.confidence_intervals
            },
            "expected_shortfall": {
                "es_95": result.var_metrics.expected_shortfall_95,
                "es_99": result.var_metrics.expected_shortfall_99
            },
            "calculation_metadata": {
                "calculation_method": result.var_metrics.calculation_method,
                "data_period_days": result.var_metrics.data_period_days,
                "calculation_duration_ms": calculation_duration_ms,
                "data_quality_score": 0.95  # Mock value
            }
        }
        
        # Add risk contributions if requested
        if request.include_risk_contributions and result.risk_contributions:
            response_data["risk_contributions"] = {
                "total_portfolio_risk": result.risk_contributions.total_portfolio_risk,
                "asset_contributions": result.risk_contributions.asset_contributions
            }
        
        logger.info(f"VaR calculation completed for request {request_id} in {calculation_duration_ms}ms")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in VaR calculation request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"VaR calculation failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "CALCULATION_FAILED",
            "VaR calculation failed",
            500,
            request_id
        )


@app.post("/api/risk/stress-test", response_model=APIResponse)
async def run_stress_test(request: StressTestRequest):
    """Run stress tests on a portfolio."""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        logger.info(f"Stress test request {request_id} for portfolio {request.portfolio_id}")
        
        # Get portfolio data (mock implementation)
        portfolio_positions = get_mock_portfolio_data(request.portfolio_id)
        portfolio_value = sum(pos["current_value"] for pos in portfolio_positions)
        
        # Run stress tests
        results = stress_tester.run_stress_tests(
            portfolio_id=request.portfolio_id,
            portfolio_positions=portfolio_positions,
            scenarios=request.scenarios,
            custom_scenarios=request.custom_scenarios,
            include_position_impacts=request.include_position_impacts,
            include_sector_impacts=request.include_sector_impacts,
            portfolio_value=portfolio_value
        )
        
        # Calculate response time
        calculation_duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "portfolio_id": request.portfolio_id,
            "test_timestamp": datetime.utcnow().isoformat(),
            "initial_portfolio_value": portfolio_value,
            "scenario_results": [
                {
                    "scenario_name": result.scenario_name,
                    "scenario_type": result.scenario_type.value,
                    "stressed_portfolio_value": result.stressed_portfolio_value,
                    "portfolio_value_change": result.portfolio_value_change,
                    "portfolio_value_change_pct": result.portfolio_value_change_pct,
                    "status": result.status.value
                }
                for result in results
            ],
            "test_metadata": {
                "total_scenarios": len(results),
                "completed_scenarios": len([r for r in results if r.status.value == "completed"]),
                "failed_scenarios": len([r for r in results if r.status.value == "failed"]),
                "test_duration_ms": calculation_duration_ms
            }
        }
        
        logger.info(f"Stress test completed for request {request_id} in {calculation_duration_ms}ms")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in stress test request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Stress test failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "STRESS_TEST_FAILED",
            "Stress testing failed",
            500,
            request_id
        )


@app.post("/api/risk/correlation-analysis", response_model=APIResponse)
async def analyze_correlations(request: CorrelationAnalysisRequest):
    """Analyze asset correlations for a portfolio."""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        logger.info(f"Correlation analysis request {request_id} for portfolio {request.portfolio_id}")
        
        # Get portfolio data (mock implementation)
        portfolio_positions = get_mock_portfolio_data(request.portfolio_id)
        portfolio_value = sum(pos["current_value"] for pos in portfolio_positions)
        
        # Analyze correlations
        result = correlation_analyzer.analyze_correlations(
            portfolio_id=request.portfolio_id,
            portfolio_positions=portfolio_positions,
            rolling_period_days=request.rolling_period_days,
            include_sector_analysis=request.include_sector_analysis,
            include_diversification_recommendations=request.include_diversification_recommendations,
            portfolio_value=portfolio_value
        )
        
        # Calculate response time
        calculation_duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "portfolio_id": request.portfolio_id,
            "analysis_timestamp": result.analysis_timestamp.isoformat(),
            "concentration_risk_score": result.concentration_risk_score,
            "sector_concentration": result.sector_concentration,
            "diversification_ratio": result.diversification_ratio,
            "effective_number_of_assets": result.effective_number_of_assets,
            "recommendations": result.recommendations,
            "analysis_metadata": {
                "rolling_period_days": result.rolling_correlation_period,
                "analysis_method": result.analysis_method,
                "calculation_duration_ms": calculation_duration_ms
            }
        }
        
        logger.info(f"Correlation analysis completed for request {request_id} in {calculation_duration_ms}ms")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in correlation analysis request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Correlation analysis failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "CORRELATION_ANALYSIS_FAILED",
            "Correlation analysis failed",
            500,
            request_id
        )


@app.get("/api/risk/compliance-report", response_model=APIResponse)
async def generate_compliance_report(
    portfolio_id: str,
    report_type: str = "daily",
    format: str = "JSON"
):
    """Generate compliance report for a portfolio."""
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        logger.info(f"Compliance report request {request_id} for portfolio {portfolio_id}")
        
        # Generate compliance report
        report = compliance_reporter.generate_compliance_report(
            portfolio_id=portfolio_id,
            report_type=report_type,
            format=format
        )
        
        # Calculate response time
        calculation_duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "compliance_report_id": str(report.compliance_report_id),
            "report_timestamp": report.report_timestamp.isoformat(),
            "compliance_status": report.compliance_status.value,
            "report_period_start": report.report_period_start.isoformat(),
            "report_period_end": report.report_period_end.isoformat(),
            "report_file_path": report.report_file_path,
            "violations_detected": report.violations_detected,
            "recommendations": report.recommendations,
            "report_metadata": {
                "report_type": report.report_type.value,
                "format": report.report_format.value,
                "generated_by": report.generated_by,
                "generation_duration_ms": calculation_duration_ms
            }
        }
        
        logger.info(f"Compliance report generated for request {request_id} in {calculation_duration_ms}ms")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in compliance report request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Compliance report generation failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "COMPLIANCE_REPORT_FAILED",
            "Compliance report generation failed",
            500,
            request_id
        )


@app.get("/api/risk/monitoring", response_model=APIResponse)
async def get_risk_monitoring_status(portfolio_id: str):
    """Get risk monitoring status for a portfolio."""
    request_id = generate_request_id()
    
    try:
        logger.info(f"Risk monitoring status request {request_id} for portfolio {portfolio_id}")
        
        # Get monitoring status
        status = risk_monitor.get_risk_monitoring_status(portfolio_id)
        
        # Prepare response data
        response_data = {
            "portfolio_id": status.portfolio_id,
            "monitoring_timestamp": status.monitoring_timestamp.isoformat(),
            "risk_status": status.risk_status,
            "current_metrics": status.current_metrics,
            "active_alerts": status.active_alerts,
            "next_monitoring": status.next_monitoring.isoformat()
        }
        
        logger.info(f"Risk monitoring status retrieved for request {request_id}")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in risk monitoring request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Risk monitoring status failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "RISK_MONITORING_FAILED",
            "Risk monitoring status failed",
            500,
            request_id
        )


@app.put("/api/risk/limits", response_model=APIResponse)
async def configure_risk_limits(request: RiskLimitsRequest):
    """Configure risk limits for a portfolio."""
    request_id = generate_request_id()
    
    try:
        logger.info(f"Risk limits configuration request {request_id} for portfolio {request.portfolio_id}")
        
        # Configure risk limits
        limits = risk_limits_manager.configure_risk_limits(
            portfolio_id=request.portfolio_id,
            limits_configuration=request.limits
        )
        
        # Prepare response data
        response_data = {
            "portfolio_id": request.portfolio_id,
            "configured_limits": [
                {
                    "limit_id": str(limit.risk_limits_id),
                    "limit_type": limit.limit_type.value,
                    "limit_value": limit.limit_value,
                    "limit_unit": limit.limit_unit,
                    "enforcement_action": limit.enforcement_action.value
                }
                for limit in limits
            ],
            "configuration_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Risk limits configured for request {request_id}")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in risk limits request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Risk limits configuration failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "RISK_LIMITS_CONFIGURATION_FAILED",
            "Risk limits configuration failed",
            500,
            request_id
        )


@app.get("/api/risk/alerts", response_model=APIResponse)
async def get_risk_alerts(
    portfolio_id: str,
    status: str = "active",
    limit: int = 100
):
    """Get risk alerts for a portfolio."""
    request_id = generate_request_id()
    
    try:
        logger.info(f"Risk alerts request {request_id} for portfolio {portfolio_id}")
        
        # Get alerts
        if status == "active":
            alerts = risk_alert_manager.get_active_alerts(portfolio_id)
        else:
            alerts = risk_alert_manager.get_alert_history(
                portfolio_id=portfolio_id,
                status_filter=status,
                limit=limit
            )
        
        # Prepare response data
        response_data = {
            "portfolio_id": portfolio_id,
            "alerts": [alert.to_dict() if hasattr(alert, 'to_dict') else alert for alert in alerts],
            "total_count": len(alerts),
            "status_filter": status
        }
        
        logger.info(f"Risk alerts retrieved for request {request_id}")
        return create_success_response(response_data, request_id)
        
    except ValueError as e:
        logger.warning(f"Validation error in risk alerts request {request_id}: {str(e)}")
        return create_error_response("INVALID_PARAMETERS", str(e), 400, request_id)
        
    except Exception as e:
        logger.error(f"Risk alerts retrieval failed for request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "RISK_ALERTS_FAILED",
            "Risk alerts retrieval failed",
            500,
            request_id
        )


# Additional endpoints for history and scenarios
@app.get("/api/risk/var-calculation/history", response_model=APIResponse)
async def get_var_calculation_history(
    portfolio_id: str,
    limit: int = 30
):
    """Get VaR calculation history for a portfolio."""
    request_id = generate_request_id()
    
    try:
        logger.info(f"VaR history request {request_id} for portfolio {portfolio_id}")
        
        # Mock history data
        history_data = {
            "portfolio_id": portfolio_id,
            "var_history": [
                {
                    "calculation_timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "var_95": 2500.0 - (i * 100),
                    "var_99": 3500.0 - (i * 150),
                    "portfolio_volatility": 0.18 - (i * 0.01)
                }
                for i in range(min(limit, 10))
            ],
            "total_count": 10
        }
        
        return create_success_response(history_data, request_id)
        
    except Exception as e:
        logger.error(f"VaR history retrieval failed for request {request_id}: {str(e)}")
        return create_error_response(
            "VAR_HISTORY_FAILED",
            "VaR history retrieval failed",
            500,
            request_id
        )


@app.get("/api/risk/stress-test/scenarios", response_model=APIResponse)
async def get_available_scenarios():
    """Get available stress test scenarios."""
    request_id = generate_request_id()
    
    try:
        logger.info(f"Available scenarios request {request_id}")
        
        scenarios = stress_tester.get_available_scenarios()
        
        response_data = {
            "standard_scenarios": scenarios,
            "scenario_parameters": {
                "market_crash": {
                    "market_decline": {"type": "float", "default": -0.30, "min": -0.50, "max": -0.10},
                    "duration_days": {"type": "int", "default": 5, "min": 1, "max": 30}
                },
                "rate_shock": {
                    "rate_increase": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.05}
                }
            }
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Available scenarios retrieval failed for request {request_id}: {str(e)}")
        return create_error_response(
            "SCENARIOS_FAILED",
            "Available scenarios retrieval failed",
            500,
            request_id
        )


# Integration endpoints
@app.get("/api/integration/portfolio/{portfolio_id}")
async def get_portfolio_data(
    portfolio_id: str,
    request: Request,
    include_positions: bool = True,
    include_performance: bool = True
):
    """Get portfolio data from portfolio service integration."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting portfolio data for {portfolio_id}, request {request_id}")
        
        portfolio_integration = get_portfolio_integration()
        portfolio_data = portfolio_integration.get_portfolio_data(
            portfolio_id, include_positions, include_performance
        )
        
        if portfolio_data is None:
            return create_error_response(
                "PORTFOLIO_NOT_FOUND",
                f"Portfolio {portfolio_id} not found",
                404,
                request_id
            )
        
        # Convert PortfolioData to dict for JSON response
        response_data = {
            "portfolio_id": portfolio_data.portfolio_id,
            "positions": portfolio_data.positions,
            "total_value": portfolio_data.total_value,
            "cash_balance": portfolio_data.cash_balance,
            "last_updated": portfolio_data.last_updated.isoformat(),
            "metadata": portfolio_data.metadata
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Portfolio data retrieval failed for {portfolio_id}, request {request_id}: {str(e)}")
        return create_error_response(
            "PORTFOLIO_DATA_FAILED",
            "Portfolio data retrieval failed",
            500,
            request_id
        )


@app.post("/api/integration/trade/validate")
async def validate_trade_risk(
    trade_data: Dict[str, Any],
    request: Request
):
    """Validate trade against risk limits."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Validating trade risk, request {request_id}")
        
        trading_engine_integration = get_trading_engine_integration()
        
        # Extract required fields
        portfolio_id = trade_data.get('portfolio_id')
        if not portfolio_id:
            return create_error_response(
                "MISSING_PORTFOLIO_ID",
                "Portfolio ID is required",
                400,
                request_id
            )
        
        # Get risk limits for portfolio
        risk_limits_manager = RiskLimitsManager()
        risk_limits = risk_limits_manager.get_risk_limits(portfolio_id)
        
        # Validate trade
        risk_check = trading_engine_integration.validate_trade_risk(
            trade_data, portfolio_id, risk_limits
        )
        
        response_data = {
            "trade_id": risk_check.trade_id,
            "approved": risk_check.approved,
            "risk_score": risk_check.risk_score,
            "risk_factors": risk_check.risk_factors,
            "warnings": risk_check.warnings,
            "recommendations": risk_check.recommendations,
            "metadata": risk_check.metadata
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Trade validation failed, request {request_id}: {str(e)}")
        return create_error_response(
            "TRADE_VALIDATION_FAILED",
            "Trade validation failed",
            500,
            request_id
        )


@app.get("/api/integration/market-data/current-prices")
async def get_current_prices(
    symbols: str,
    request: Request
):
    """Get current prices from market data service."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting current prices for symbols, request {request_id}")
        
        market_data_integration = get_market_data_integration()
        
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',')]
        
        # Get current prices
        prices = market_data_integration.get_current_prices(symbol_list)
        
        # Convert MarketData objects to dicts
        response_data = {}
        for symbol, market_data in prices.items():
            response_data[symbol] = {
                "symbol": market_data.symbol,
                "price": market_data.price,
                "volume": market_data.volume,
                "timestamp": market_data.timestamp.isoformat(),
                "bid": market_data.bid,
                "ask": market_data.ask,
                "high": market_data.high,
                "low": market_data.low,
                "open_price": market_data.open_price,
                "metadata": market_data.metadata
            }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Current prices retrieval failed, request {request_id}: {str(e)}")
        return create_error_response(
            "PRICES_FAILED",
            "Current prices retrieval failed",
            500,
            request_id
        )


@app.get("/api/integration/sync/status")
async def get_sync_status(
    request: Request,
    service: Optional[str] = None
):
    """Get data synchronization status."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting sync status, request {request_id}")
        
        data_sync_service = get_data_sync_service()
        sync_status = data_sync_service.get_sync_status(service)
        
        # Convert SyncStatus objects to dicts
        response_data = {}
        for service_name, status in sync_status.items():
            if status:
                response_data[service_name] = {
                    "service": status.service,
                    "last_sync": status.last_sync.isoformat(),
                    "status": status.status,
                    "records_synced": status.records_synced,
                    "error_message": status.error_message,
                    "metadata": status.metadata
                }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Sync status retrieval failed, request {request_id}: {str(e)}")
        return create_error_response(
            "SYNC_STATUS_FAILED",
            "Sync status retrieval failed",
            500,
            request_id
        )


@app.get("/api/integration/monitoring/health")
async def get_monitoring_health(
    request: Request
):
    """Get cross-service monitoring health."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting monitoring health, request {request_id}")
        
        monitoring = get_cross_service_monitoring()
        health_summary = monitoring.get_service_health_summary()
        
        return create_success_response(health_summary, request_id)
        
    except Exception as e:
        logger.error(f"Monitoring health retrieval failed, request {request_id}: {str(e)}")
        return create_error_response(
            "MONITORING_HEALTH_FAILED",
            "Monitoring health retrieval failed",
            500,
            request_id
        )


@app.get("/api/integration/monitoring/alerts")
async def get_monitoring_alerts(
    request: Request,
    service: Optional[str] = None,
    severity: Optional[str] = None
):
    """Get active monitoring alerts."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting monitoring alerts, request {request_id}")
        
        monitoring = get_cross_service_monitoring()
        
        # Parse severity filter
        severity_filter = None
        if severity:
            from src.risk.integrations.cross_service_monitoring import AlertSeverity
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                return create_error_response(
                    "INVALID_SEVERITY",
                    f"Invalid severity level: {severity}",
                    400,
                    request_id
                )
        
        active_alerts = monitoring.get_active_alerts(service, severity_filter)
        
        # Convert Alert objects to dicts
        response_data = []
        for alert in active_alerts:
            response_data.append({
                "alert_id": alert.alert_id,
                "service": alert.service,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "acknowledged_by": alert.acknowledged_by,
                "resolution_notes": alert.resolution_notes
            })
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Monitoring alerts retrieval failed, request {request_id}: {str(e)}")
        return create_error_response(
            "MONITORING_ALERTS_FAILED",
            "Monitoring alerts retrieval failed",
            500,
            request_id
        )


@app.post("/api/integration/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: Request,
    acknowledged_by: str,
    notes: Optional[str] = None
):
    """Acknowledge a monitoring alert."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Acknowledging alert {alert_id}, request {request_id}")
        
        monitoring = get_cross_service_monitoring()
        success = monitoring.acknowledge_alert(alert_id, acknowledged_by, notes)
        
        if not success:
            return create_error_response(
                "ALERT_NOT_FOUND",
                f"Alert {alert_id} not found",
                404,
                request_id
            )
        
        return create_success_response(
            {"alert_id": alert_id, "acknowledged_by": acknowledged_by},
            request_id
        )
        
    except Exception as e:
        logger.error(f"Alert acknowledgment failed for {alert_id}, request {request_id}: {str(e)}")
        return create_error_response(
            "ALERT_ACKNOWLEDGMENT_FAILED",
            "Alert acknowledgment failed",
            500,
            request_id
        )


@app.post("/api/integration/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: Request,
    resolution_notes: Optional[str] = None
):
    """Resolve a monitoring alert."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Resolving alert {alert_id}, request {request_id}")
        
        monitoring = get_cross_service_monitoring()
        success = monitoring.resolve_alert(alert_id, resolution_notes)
        
        if not success:
            return create_error_response(
                "ALERT_NOT_FOUND",
                f"Alert {alert_id} not found",
                404,
                request_id
            )
        
        return create_success_response(
            {"alert_id": alert_id, "resolved_at": datetime.utcnow().isoformat()},
            request_id
        )
        
    except Exception as e:
        logger.error(f"Alert resolution failed for {alert_id}, request {request_id}: {str(e)}")
        return create_error_response(
            "ALERT_RESOLUTION_FAILED",
            "Alert resolution failed",
            500,
            request_id
        )


# Monitoring and observability endpoints
@app.get("/metrics")
async def get_prometheus_metrics(request: Request):
    """Get Prometheus metrics."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        metrics = get_metrics()
        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {str(e)}")
        return create_error_response(
            "METRICS_FAILED",
            "Failed to get Prometheus metrics",
            500,
            request.headers.get("X-Request-ID", "unknown")
        )


@app.get("/api/monitoring/health")
@record_api_metrics("GET", "/api/monitoring/health")
async def get_comprehensive_health(request: Request):
    """Get comprehensive system health status."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting comprehensive health status, request {request_id}")
        
        health_monitor = get_health_monitor()
        system_health = health_monitor.get_overall_health()
        
        # Convert to response format
        response_data = {
            "overall_status": system_health.overall_status.value,
            "timestamp": system_health.timestamp.isoformat(),
            "uptime_seconds": system_health.uptime_seconds,
            "version": system_health.version,
            "components": [
                {
                    "name": comp.name,
                    "status": comp.status.value,
                    "last_check": comp.last_check.isoformat(),
                    "response_time_ms": comp.response_time_ms,
                    "error_message": comp.error_message,
                    "metadata": comp.metadata
                }
                for comp in system_health.components
            ],
            "system_metrics": system_health.system_metrics
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Health check failed, request {request_id}: {str(e)}")
        return create_error_response(
            "HEALTH_CHECK_FAILED",
            "Health check failed",
            500,
            request_id
        )


@app.get("/api/monitoring/health/{component}")
@record_api_metrics("GET", "/api/monitoring/health/{component}")
async def get_component_health(component: str, request: Request):
    """Get health status for a specific component."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting health status for component {component}, request {request_id}")
        
        health_monitor = get_health_monitor()
        component_health = health_monitor.get_component_health(component)
        
        if component_health is None:
            return create_error_response(
                "COMPONENT_NOT_FOUND",
                f"Component {component} not found",
                404,
                request_id
            )
        
        response_data = {
            "name": component_health.name,
            "status": component_health.status.value,
            "last_check": component_health.last_check.isoformat(),
            "response_time_ms": component_health.response_time_ms,
            "error_message": component_health.error_message,
            "metadata": component_health.metadata
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Component health check failed for {component}, request {request_id}: {str(e)}")
        return create_error_response(
            "COMPONENT_HEALTH_FAILED",
            "Component health check failed",
            500,
            request_id
        )


@app.get("/api/monitoring/health/summary")
@record_api_metrics("GET", "/api/monitoring/health/summary")
async def get_health_summary(request: Request):
    """Get health summary information."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting health summary, request {request_id}")
        
        health_monitor = get_health_monitor()
        health_summary = health_monitor.get_health_summary()
        
        return create_success_response(health_summary, request_id)
        
    except Exception as e:
        logger.error(f"Health summary failed, request {request_id}: {str(e)}")
        return create_error_response(
            "HEALTH_SUMMARY_FAILED",
            "Health summary failed",
            500,
            request_id
        )


@app.get("/api/monitoring/health/history")
@record_api_metrics("GET", "/api/monitoring/health/history")
async def get_health_history(request: Request, limit: int = 10):
    """Get health check history."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting health history (limit={limit}), request {request_id}")
        
        health_monitor = get_health_monitor()
        health_history = health_monitor.get_health_history(limit)
        
        # Convert to response format
        response_data = []
        for system_health in health_history:
            response_data.append({
                "overall_status": system_health.overall_status.value,
                "timestamp": system_health.timestamp.isoformat(),
                "uptime_seconds": system_health.uptime_seconds,
                "component_count": len(system_health.components),
                "healthy_components": sum(1 for c in system_health.components if c.status.value == "healthy"),
                "degraded_components": sum(1 for c in system_health.components if c.status.value == "degraded"),
                "unhealthy_components": sum(1 for c in system_health.components if c.status.value == "unhealthy")
            })
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Health history failed, request {request_id}: {str(e)}")
        return create_error_response(
            "HEALTH_HISTORY_FAILED",
            "Health history failed",
            500,
            request_id
        )


@app.get("/api/monitoring/metrics/summary")
@record_api_metrics("GET", "/api/monitoring/metrics/summary")
async def get_metrics_summary(request: Request):
    """Get metrics summary information."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(f"Getting metrics summary, request {request_id}")
        
        metrics = get_metrics()
        
        # Get some key metrics (this would be expanded based on actual metrics)
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_available": True,
            "prometheus_endpoint": "/metrics",
            "note": "Detailed metrics available at /metrics endpoint"
        }
        
        return create_success_response(response_data, request_id)
        
    except Exception as e:
        logger.error(f"Metrics summary failed, request {request_id}: {str(e)}")
        return create_error_response(
            "METRICS_SUMMARY_FAILED",
            "Metrics summary failed",
            500,
            request_id
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )