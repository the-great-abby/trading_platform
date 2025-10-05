"""
Live Trading Service - FastAPI Application

Main application entry point for the live trading service.
Provides API endpoints for live trading with Public.com integration.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text

from src.services.live_trading.database import init_database, close_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID tracking."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{process_time:.4f}s"
        
        # Log request
        logger.info(
            f"Request processed - ID: {request_id}, Method: {request.method}, URL: {str(request.url)}, "
            f"Status: {response.status_code}, Time: {process_time:.4f}s, "
            f"IP: {request.client.host if request.client else 'unknown'}"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        if client_ip in self.clients:
            self.clients[client_ip] = [
                call_time for call_time in self.clients[client_ip]
                if current_time - call_time < self.period
            ]
        else:
            self.clients[client_ip] = []
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request
        self.clients[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.clients[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Live Trading Service...")
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Live Trading Service...")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title="Live Trading Service",
    description="API for live trading with Public.com integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware with security considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:11115",  # Unified Trading Dashboard
        "http://localhost:11114",  # Unified Analytics Dashboard
        "http://localhost:11120",  # Live Trading Service
        "https://trading.local",   # Production domain (if applicable)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=600,  # Cache preflight response for 10 minutes
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "trading.local", "*.trading.local", "*"]
)

# Include API routes
from routes.auth import router as auth_router
from routes.accounts import router as accounts_router
from routes.trading import router as trading_router
from routes.risk import router as risk_router
from routes.status import router as status_router
from routes.strategies import router as strategies_router
from routes.risk_management import router as risk_management_router
from routes.trailing_stops import router as trailing_stops_router
from routes.recovery import router as recovery_router

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(trading_router)
app.include_router(risk_router)
app.include_router(status_router)
app.include_router(strategies_router)
app.include_router(risk_management_router)
app.include_router(trailing_stops_router)
app.include_router(recovery_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        from src.services.live_trading.database import async_session_maker
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        
        # Check Redis connectivity
        from src.services.live_trading.database import redis_client
        if not redis_client.redis:
            await redis_client.connect()
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "live-trading-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": "healthy",
                "redis": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "live-trading-service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if all required services are available
        checks = {}
        
        # Check database
        try:
            from src.services.live_trading.database import async_session_maker
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ready"
        except Exception as e:
            checks["database"] = f"not ready: {str(e)}"
        
        # Check Redis
        try:
            from src.services.live_trading.database import redis_client
            if not redis_client.redis:
                await redis_client.connect()
            await redis_client.ping()
            checks["redis"] = "ready"
        except Exception as e:
            checks["redis"] = f"not ready: {str(e)}"
        
        # Check if all services are ready
        all_ready = all("ready" in status for status in checks.values())
        
        if all_ready:
            return {
                "status": "ready",
                "service": "live-trading-service",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not ready",
                    "service": "live-trading-service",
                    "timestamp": datetime.utcnow().isoformat(),
                    "checks": checks
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "service": "live-trading-service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        # This would typically return Prometheus metrics
        # For now, return a basic metrics summary
        return {
            "service": "live-trading-service",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_available": True,
            "note": "Prometheus metrics are available on the configured metrics port"
        }
    except Exception as e:
        logger.error(f"Metrics endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Metrics unavailable",
                "details": str(e)
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "service": "live-trading-service"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
