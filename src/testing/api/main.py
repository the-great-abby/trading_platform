#!/usr/bin/env python3
"""
Main FastAPI application for Strategy Engine Testing Framework
"""

import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .routes import testing_router
from .schemas import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper error handling and cleanup"""
    startup_successful = False
    
    # Startup
    logger.info("Starting Strategy Engine Testing Framework API")
    
    # Initialize services
    try:
        # Skip database initialization for now
        logger.info("Services initialized successfully (database initialization skipped)")
        startup_successful = True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error("Application startup failed - shutting down")
        raise
    
    try:
        yield
    except Exception as e:
        logger.error(f"Application error during runtime: {e}")
        logger.error("Initiating emergency shutdown")
    finally:
        # Shutdown - always runs, even if there was an error
        logger.info("Shutting down Strategy Engine Testing Framework API")
        
        # Cleanup resources
        try:
            # Here you would close database connections, Redis connections, etc.
            logger.info("Resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Strategy Engine Testing Framework API",
    description="Comprehensive testing framework for trading strategies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"path": str(request.url)}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"path": str(request.url), "exception": str(exc)}
        ).model_dump()
    )


# Include routers
app.include_router(testing_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Strategy Engine Testing Framework API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/testing/health"
    }


# OpenAPI customization
def custom_openapi():
    """Custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Strategy Engine Testing Framework API",
        version="1.0.0",
        description="""
        # Strategy Engine Testing Framework API
        
        This API provides comprehensive testing capabilities for trading strategies including:
        
        - **Strategy Validation**: Interface and functionality validation
        - **Signal Testing**: Signal generation and quality validation  
        - **Performance Testing**: Execution time, memory, and CPU monitoring
        - **Ensemble Testing**: Multi-strategy coordination and conflict resolution
        - **Mock Data Generation**: Realistic market data for testing
        - **Test Suite Management**: Comprehensive test orchestration
        
        ## Key Features
        
        - Real-time strategy validation
        - Comprehensive signal quality analysis
        - Performance benchmarking and optimization recommendations
        - Multi-regime mock data generation
        - Batch operation support
        - Detailed test reporting and analytics
        
        ## Supported Strategy Types
        
        - **Basic Strategies**: Moving averages, RSI, MACD
        - **Options Strategies**: Iron condor, covered calls, cash-secured puts
        - **Advanced Strategies**: Elliott Wave, Ichimoku, Neural Network, Quantum Momentum
        
        ## Market Regimes
        
        - Bull Market
        - Bear Market  
        - Sideways Market
        - Volatile Market
        
        ## Timeframes
        
        - 1 minute, 5 minutes, 15 minutes
        - 1 hour, 4 hours
        - 1 day
        """,
        routes=app.routes,
    )
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "testing",
            "description": "Strategy testing and validation operations"
        },
        {
            "name": "health",
            "description": "Health check and monitoring endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Health check endpoint
@app.get("/health")
async def simple_health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "strategy-testing-framework"}


if __name__ == "__main__":
    import uvicorn
    import time
    
    uvicorn.run(
        "src.testing.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
