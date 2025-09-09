"""
Main FastAPI application for CQRS Trading System
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from typing import Dict, Any

from src.services.cqrs.cqrs_service import CQRSService
from src.api.middleware.auth_middleware import AuthMiddleware
from src.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware
from src.api.middleware.error_middleware import ErrorHandlingMiddleware
from src.api.middleware.metrics_middleware import MetricsMiddleware
from src.api.config.api_config import APIConfig
from src.api.routes import orders, portfolio, market_data, strategies, health


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Load configuration
    config = APIConfig()
    
    # Create FastAPI app
    app = FastAPI(
        title=config.title,
        version=config.version,
        description=config.description,
        debug=config.debug
    )
    
    # Add middleware (order matters!)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    
    # Initialize CQRS service with mock connections for now
    # Real database connection will be initialized in startup event
    from unittest.mock import Mock
    mock_db_conn = Mock()
    mock_redis_client = Mock()
    cqrs_service = CQRSService(mock_db_conn, mock_redis_client)
    app.state.cqrs_service = cqrs_service
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(orders.router, prefix="/api", tags=["orders"])
    app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
    app.include_router(market_data.router, prefix="/api", tags=["market-data"])
    app.include_router(strategies.router, prefix="/api", tags=["strategies"])
    
    # Add WebSocket support
    from src.api.websocket import websocket_router
    from src.api.routes.trading_routes import router as trading_router
    from src.api.routes.websocket_routes import router as websocket_trading_router
    
    app.include_router(websocket_router, tags=["websocket"])
    app.include_router(trading_router, tags=["trading"])
    app.include_router(websocket_trading_router, tags=["websocket-trading"])
    
    return app


# Create app instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("Starting CQRS API application")
    
    # Import logging
    #import logging
    # Initialize database connection
    import os
    from src.services.database import initialize_database
    
    database_url = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")
    
    try:
        db_manager = await initialize_database(database_url)
        cqrs_service = CQRSService(db_manager, None)  # No Redis for now
        app.state.cqrs_service = cqrs_service
        app.state.db_manager = db_manager
        logger = logging.getLogger("cqrs_api")
        logger.info("CQRS service initialized with real database connection")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        logger.info("Continuing with mock database connections")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    # import logging
    logger = logging.getLogger("cqrs_api")
    logger.info("Shutting down CQRS API application")
    
    # Close database connections
    if hasattr(app.state, 'db_manager') and app.state.db_manager:
        from src.services.database import close_database
        await close_database()


# Expose cqrs_service for testing
cqrs_service = app.state.cqrs_service


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Trading System CQRS API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cqrs-api",
        "timestamp": time.time()
    }


@app.get("/api/cqrs/status")
async def cqrs_status(request: Request):
    """Get CQRS service status"""
    cqrs_service = request.app.state.cqrs_service
    status = await cqrs_service.get_service_status()
    return status


@app.get("/metrics")
async def metrics(request: Request):
    """Get application metrics"""
    # Get metrics from middleware if available
    metrics_middleware = None
    for middleware in request.app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'MetricsMiddleware':
            metrics_middleware = middleware
            break
    
    if metrics_middleware and hasattr(metrics_middleware, 'get_metrics'):
        return metrics_middleware.get_metrics()
    
    # Fallback metrics
    return {
        "requests_total": 0,
        "response_time_seconds": 0.0,
        "errors_total": 0,
        "status": "healthy"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "timestamp": time.time()
        }
    )
