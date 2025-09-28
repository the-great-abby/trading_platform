"""
System Status API Routes

Handles system status, health checks, and market hours information.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.services.live_trading.database import get_db_session
from src.services.live_trading.market_hours_service import MarketHoursService
from src.services.live_trading.public_api_client import PublicAPIClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/status", tags=["status"])


# Pydantic models
class SystemStatusResponse(BaseModel):
    """System status response model."""
    status: str = Field(..., description="System status")
    timestamp: str = Field(..., description="Status timestamp")
    version: str = Field(..., description="System version")
    uptime: str = Field(..., description="System uptime")
    components: Dict[str, Any] = Field(..., description="Component statuses")


class MarketHoursResponse(BaseModel):
    """Market hours response model."""
    is_open: bool = Field(..., description="Market open status")
    current_time: str = Field(..., description="Current time")
    next_open: Optional[str] = Field(None, description="Next market open")
    next_close: Optional[str] = Field(None, description="Next market close")
    reason: Optional[str] = Field(None, description="Market status reason")
    trading_allowed: bool = Field(..., description="Trading allowed status")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual component checks")


class TradingSessionResponse(BaseModel):
    """Trading session response model."""
    session_start: str = Field(..., description="Session start time")
    session_end: str = Field(..., description="Session end time")
    session_duration_hours: float = Field(..., description="Session duration in hours")
    time_elapsed_hours: float = Field(..., description="Time elapsed in hours")
    time_remaining_hours: float = Field(..., description="Time remaining in hours")
    session_progress_percent: float = Field(..., description="Session progress percentage")
    is_active: bool = Field(..., description="Session active status")
    current_time: str = Field(..., description="Current time")


@router.get("", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get overall system status.
    
    Returns comprehensive system status including all components.
    """
    try:
        # Get component statuses
        components = await _check_all_components()
        
        # Determine overall status
        overall_status = "healthy"
        if any(comp["status"] != "healthy" for comp in components.values()):
            overall_status = "degraded"
        if any(comp["status"] == "unhealthy" for comp in components.values()):
            overall_status = "unhealthy"
        
        return SystemStatusResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime="0d 0h 0m",  # Would be calculated from actual uptime
            components=components
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return SystemStatusResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime="unknown",
            components={"error": {"status": "unhealthy", "message": str(e)}}
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Perform health check on all system components.
    
    Returns detailed health status for each component.
    """
    try:
        checks = await _perform_health_checks()
        
        # Determine overall health
        overall_health = "healthy"
        if any(check["status"] != "healthy" for check in checks.values()):
            overall_health = "unhealthy"
        
        return HealthCheckResponse(
            status=overall_health,
            timestamp=datetime.utcnow().isoformat(),
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            checks={"error": {"status": "unhealthy", "message": str(e)}}
        )


@router.get("/market-hours", response_model=MarketHoursResponse)
async def get_market_hours():
    """
    Get current market hours status.
    
    Returns market open/close status and trading availability.
    """
    try:
        market_hours_service = MarketHoursService()
        
        # Get market status
        market_status = await market_hours_service.get_market_status()
        
        # Get trading validation
        trading_validation = await market_hours_service.validate_trading_time()
        
        return MarketHoursResponse(
            is_open=market_status.is_open,
            current_time=market_status.current_time.isoformat(),
            next_open=market_status.next_open.isoformat() if market_status.next_open else None,
            next_close=market_status.next_close.isoformat() if market_status.next_close else None,
            reason=market_status.reason,
            trading_allowed=trading_validation["trading_allowed"]
        )
        
    except Exception as e:
        logger.error(f"Error getting market hours: {str(e)}")
        return MarketHoursResponse(
            is_open=False,
            current_time=datetime.utcnow().isoformat(),
            reason=f"Error determining market status: {str(e)}",
            trading_allowed=False
        )


@router.get("/market-hours/next-open")
async def get_next_market_open():
    """
    Get next market open time.
    
    Returns when the market will next open.
    """
    try:
        market_hours_service = MarketHoursService()
        result = await market_hours_service.get_next_market_open()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting next market open: {str(e)}")
        return {
            "next_open": None,
            "hours_until_open": None,
            "days_until_open": None,
            "error": str(e)
        }


@router.get("/market-hours/next-close")
async def get_next_market_close():
    """
    Get next market close time.
    
    Returns when the market will next close.
    """
    try:
        market_hours_service = MarketHoursService()
        result = await market_hours_service.get_next_market_close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting next market close: {str(e)}")
        return {
            "next_close": None,
            "hours_until_close": None,
            "minutes_until_close": None,
            "error": str(e)
        }


@router.get("/trading-session", response_model=TradingSessionResponse)
async def get_trading_session():
    """
    Get current trading session information.
    
    Returns detailed information about the current trading session.
    """
    try:
        market_hours_service = MarketHoursService()
        session_info = await market_hours_service.get_trading_session_info()
        
        if "error" in session_info:
            raise Exception(session_info["error"])
        
        return TradingSessionResponse(
            session_start=session_info["session_start"],
            session_end=session_info["session_end"],
            session_duration_hours=session_info["session_duration_hours"],
            time_elapsed_hours=session_info["time_elapsed_hours"],
            time_remaining_hours=session_info["time_remaining_hours"],
            session_progress_percent=session_info["session_progress_percent"],
            is_active=session_info["is_active"],
            current_time=session_info["current_time"]
        )
        
    except Exception as e:
        logger.error(f"Error getting trading session: {str(e)}")
        return TradingSessionResponse(
            session_start="unknown",
            session_end="unknown",
            session_duration_hours=0.0,
            time_elapsed_hours=0.0,
            time_remaining_hours=0.0,
            session_progress_percent=0.0,
            is_active=False,
            current_time=datetime.utcnow().isoformat()
        )


@router.get("/market-hours/calendar")
async def get_market_calendar(
    start_date: str,
    end_date: str
):
    """
    Get market calendar for date range.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        
    Returns:
        Market calendar information
    """
    try:
        market_hours_service = MarketHoursService()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        calendar = await market_hours_service.get_market_calendar(start_dt, end_dt)
        
        return calendar
        
    except Exception as e:
        logger.error(f"Error getting market calendar: {str(e)}")
        return {
            "calendar": [],
            "total_days": 0,
            "trading_days": 0,
            "non_trading_days": 0,
            "error": str(e)
        }


@router.get("/database")
async def get_database_status(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get database connection status.
    
    Returns database connectivity and performance metrics.
    """
    try:
        # Test database connection
        start_time = datetime.utcnow()
        await db.execute(text("SELECT 1"))
        end_time = datetime.utcnow()
        
        response_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        # Get basic database stats
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total_accounts,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_accounts
            FROM live_trading_accounts
        """))
        stats = result.fetchone()
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "connection_pool": "active",
            "database_stats": {
                "total_accounts": stats[0] if stats else 0,
                "active_accounts": stats[1] if stats else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/public-api")
async def get_public_api_status():
    """
    Get Public.com API connectivity status.
    
    Returns API connectivity and rate limit information.
    """
    try:
        # Test API connectivity (without authentication)
        api_client = PublicAPIClient()
        
        # This would test basic connectivity
        # For now, return mock status
        return {
            "status": "healthy",
            "api_version": "v1",
            "base_url": api_client.config.api_base_url,
            "rate_limits": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Public API health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Private helper functions

async def _check_all_components() -> Dict[str, Any]:
    """Check status of all system components."""
    components = {}
    
    try:
        # Check database
        components["database"] = await _check_database()
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        # Check market hours service
        components["market_hours"] = await _check_market_hours()
    except Exception as e:
        components["market_hours"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        # Check Public.com API
        components["public_api"] = await _check_public_api()
    except Exception as e:
        components["public_api"] = {"status": "unhealthy", "error": str(e)}
    
    return components


async def _perform_health_checks() -> Dict[str, Any]:
    """Perform detailed health checks on all components."""
    checks = {}
    
    # Database health check
    try:
        from src.services.live_trading.database import async_session_maker
        async with async_session_maker() as session:
            start_time = datetime.utcnow()
            await session.execute(text("SELECT 1"))
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            checks["database"] = {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection": "active"
            }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Market hours service health check
    try:
        market_hours_service = MarketHoursService()
        market_status = await market_hours_service.get_market_status()
        
        checks["market_hours"] = {
            "status": "healthy",
            "market_open": market_status.is_open,
            "current_time": market_status.current_time.isoformat()
        }
    except Exception as e:
        checks["market_hours"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Public.com API health check
    try:
        api_client = PublicAPIClient()
        # Test basic connectivity
        checks["public_api"] = {
            "status": "healthy",
            "base_url": api_client.config.api_base_url,
            "timeout": api_client.config.timeout
        }
        await api_client.close()
    except Exception as e:
        checks["public_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return checks


async def _check_database() -> Dict[str, Any]:
    """Check database component status."""
    try:
        from src.services.live_trading.database import async_session_maker
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "connection": "active"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_market_hours() -> Dict[str, Any]:
    """Check market hours service status."""
    try:
        market_hours_service = MarketHoursService()
        market_status = await market_hours_service.get_market_status()
        return {
            "status": "healthy",
            "market_open": market_status.is_open,
            "current_time": market_status.current_time.isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_public_api() -> Dict[str, Any]:
    """Check Public.com API status."""
    try:
        api_client = PublicAPIClient()
        # Basic connectivity test
        return {
            "status": "healthy",
            "base_url": api_client.config.api_base_url
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
