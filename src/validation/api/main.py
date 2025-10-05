"""
Main FastAPI application for the validation framework

This module creates and configures the FastAPI application with all
API endpoints, middleware, and error handling.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from . import script_endpoints
from . import validation_endpoints
from . import batch_endpoints
from . import report_endpoints
from . import config_endpoints
from . import result_endpoints
from ..integration import (
    setup_validation_logging, 
    get_validation_logger,
    HealthChecker,
    get_metrics_collector
)

# Set up logging
logger = setup_validation_logging()
validation_logger = get_validation_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    validation_logger.info("Validation Framework API starting up...")
    
    # Initialize health checker
    app.state.health_checker = HealthChecker()
    
    # Initialize metrics collector
    app.state.metrics_collector = get_metrics_collector()
    
    validation_logger.info("Validation Framework API startup complete")
    
    yield
    
    # Shutdown
    validation_logger.info("Validation Framework API shutting down...")
    validation_logger.info("Validation Framework API shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Validation Framework API",
        description="REST API for backtest script validation and testing",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests."""
        start_time = time.time()
        
        # Log request
        validation_logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        validation_logger.info(
            f"Response: {response.status_code} - "
            f"Processing time: {process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Add exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        validation_logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(exc)
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            health_checker = app.state.health_checker
            health_status = await health_checker.check_health()
            
            return {
                "status": "healthy" if health_status["healthy"] else "unhealthy",
                "timestamp": health_status["timestamp"],
                "checks": health_status["checks"],
                "version": "1.0.0"
            }
        except Exception as e:
            validation_logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e)
                }
            )
    
    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        try:
            metrics_collector = app.state.metrics_collector
            metrics_data = metrics_collector.export_prometheus_format()
            
            return JSONResponse(
                content={"metrics": metrics_data},
                media_type="text/plain"
            )
        except Exception as e:
            validation_logger.error(f"Metrics collection failed: {e}")
            raise HTTPException(status_code=500, detail="Metrics collection failed")
    
    # API info endpoint
    @app.get("/")
    async def api_info():
        """API information endpoint."""
        return {
            "name": "Validation Framework API",
            "version": "1.0.0",
            "description": "REST API for backtest script validation and testing",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics",
                "docs": "/docs",
                "redoc": "/redoc",
                "scripts": "/api/v1/scripts",
                "validation": "/api/v1/validation",
                "batch": "/api/v1/batch",
                "reports": "/api/v1/reports",
                "config": "/api/v1/config",
                "results": "/api/v1/results"
            }
        }
    
    # Include API routers
    app.include_router(script_endpoints.router)
    app.include_router(validation_endpoints.router)
    app.include_router(batch_endpoints.router)
    app.include_router(report_endpoints.router)
    app.include_router(config_endpoints.router)
    app.include_router(result_endpoints.router)
    
    validation_logger.info("FastAPI application created and configured")
    
    return app


# Application instance will be created when needed


if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn
    uvicorn.run(
        "validation_framework.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
