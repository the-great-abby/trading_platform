"""
Centralized API Gateway for Space Trading Station
Single entry point for all external systems
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, push_to_gateway

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('gateway_request_duration_seconds', 'Request latency', ['method', 'endpoint'])

# Configuration
class GatewayConfig:
    """Gateway configuration"""
    # Service URLs
    TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://trading-service:8000")
    MARKET_DATA_SERVICE_URL = os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data-service:8000")
    PORTFOLIO_SERVICE_URL = os.getenv("PORTFOLIO_SERVICE_URL", "http://portfolio-service:8000")
    ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")
    STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:8000")
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
    RISK_SERVICE_URL = os.getenv("RISK_SERVICE_URL", "http://risk-service:8000")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:8000")
    
    # Redis for caching and rate limiting
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Security
    API_KEY_HEADER = "X-API-Key"
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Caching
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
    
    # Timeouts
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

config = GatewayConfig()

# Pydantic models
class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]

class TradingRequest(BaseModel):
    """Trading request model"""
    symbol: str
    action: str  # buy, sell
    quantity: int
    order_type: str = "market"  # market, limit, stop
    price: Optional[float] = None
    strategy: Optional[str] = None

class MarketDataRequest(BaseModel):
    """Market data request model"""
    symbols: List[str]
    interval: str = "1d"  # 1m, 5m, 15m, 1h, 1d
    period: str = "1y"  # 1d, 5d, 1m, 3m, 6m, 1y, 2y, 5y, 10y

class PortfolioRequest(BaseModel):
    """Portfolio request model"""
    account_id: Optional[str] = None
    include_positions: bool = True
    include_history: bool = False

class BacktestRequest(BaseModel):
    """Backtest request model"""
    strategy: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000
    commission: float = 0.001

# Global variables
redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, http_client
    
    # Initialize Redis
    try:
        redis_client = redis.from_url(config.REDIS_URL)
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        redis_client = None
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT)
    logger.info("✅ HTTP client initialized")
    
    yield
    
    # Cleanup
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()
    logger.info("✅ Gateway shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Space Trading Station API Gateway",
    description="Centralized API gateway for all trading system operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
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

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key and return user ID"""
    # In production, implement proper API key validation
    # For now, accept any valid Bearer token
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return "user_123"  # Return user ID

# Rate limiting
async def check_rate_limit(request: Request, user_id: str = Depends(verify_api_key)):
    """Check rate limit for user"""
    if not redis_client:
        return  # Skip rate limiting if Redis is unavailable
    
    key = f"rate_limit:{user_id}:{request.url.path}"
    current = await redis_client.get(key)
    
    if current and int(current) >= config.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, config.RATE_LIMIT_WINDOW)
    await pipe.execute()

# Request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track requests for monitoring"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    # Record metrics
    duration = (datetime.utcnow() - start_time).total_seconds()
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error="Internal server error",
            message="An unexpected error occurred"
        ).dict()
    )

# Health check
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check"""
    services = {}
    
    # Check all services
    service_urls = {
        "trading": config.TRADING_SERVICE_URL,
        "market_data": config.MARKET_DATA_SERVICE_URL,
        "portfolio": config.PORTFOLIO_SERVICE_URL,
        "analytics": config.ANALYTICS_SERVICE_URL,
        "strategy": config.STRATEGY_SERVICE_URL,
        "order": config.ORDER_SERVICE_URL,
        "risk": config.RISK_SERVICE_URL,
        "user": config.USER_SERVICE_URL,
        "backtest": config.BACKTEST_API_URL
    }
    
    for service_name, url in service_urls.items():
        try:
            if http_client:
                response = await http_client.get(f"{url}/health", timeout=5)
                services[service_name] = "healthy" if response.status_code == 200 else "error"
            else:
                services[service_name] = "unknown"
        except Exception as e:
            services[service_name] = "error"
            logger.warning(f"Service {service_name} health check failed: {e}")
    
    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            services["redis"] = "healthy"
        except:
            services["redis"] = "error"
    else:
        services["redis"] = "unknown"
    
    return HealthCheck(
        status="healthy" if all(s == "healthy" for s in services.values()) else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services=services
    )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# API Documentation
@app.get("/", response_model=APIResponse)
async def root():
    """API Gateway root endpoint"""
    return APIResponse(
        success=True,
        data={
            "service": "Space Trading Station API Gateway",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": {
                "trading": "/api/v1/trading",
                "market_data": "/api/v1/market-data",
                "portfolio": "/api/v1/portfolio",
                "analytics": "/api/v1/analytics",
                "strategies": "/api/v1/strategies",
                "orders": "/api/v1/orders",
                "risk": "/api/v1/risk",
                "backtest": "/api/v1/backtest",
                "users": "/api/v1/users"
            },
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        },
        message="Welcome to Space Trading Station API Gateway"
    )

# Trading endpoints
@app.post("/api/v1/trading/orders", response_model=APIResponse)
async def create_order(
    request: TradingRequest,
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Create a new trading order"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.post(
            f"{config.ORDER_SERVICE_URL}/orders",
            json=request.dict(),
            headers={"Authorization": f"Bearer {user_id}"}
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Order created successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")

@app.get("/api/v1/trading/orders", response_model=APIResponse)
async def get_orders(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get user's trading orders"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.ORDER_SERVICE_URL}/orders",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Orders retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get orders")

# Market data endpoints
@app.post("/api/v1/market-data/quotes", response_model=APIResponse)
async def get_market_quotes(
    request: MarketDataRequest,
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get market data quotes"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.post(
            f"{config.MARKET_DATA_SERVICE_URL}/quotes",
            json=request.dict()
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Market data retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market data")

# Portfolio endpoints
@app.get("/api/v1/portfolio", response_model=APIResponse)
async def get_portfolio(
    request: PortfolioRequest,
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get user portfolio"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.PORTFOLIO_SERVICE_URL}/portfolio",
            params=request.dict(exclude_none=True),
            headers={"Authorization": f"Bearer {user_id}"}
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Portfolio retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio")

# Strategy endpoints
@app.get("/api/v1/strategies", response_model=APIResponse)
async def get_strategies(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get available trading strategies"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.STRATEGY_SERVICE_URL}/strategies"
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Strategies retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get strategies")

@app.post("/api/v1/strategies/recommendations", response_model=APIResponse)
async def get_strategy_recommendations(
    request: Dict[str, Any],
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get strategy recommendations"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.post(
            f"{config.STRATEGY_SERVICE_URL}/recommendations/stock",
            json=request
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Recommendations generated successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

# Backtest endpoints
@app.post("/api/v1/backtest/run", response_model=APIResponse)
async def run_backtest(
    request: BacktestRequest,
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Run a backtest"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.post(
            f"{config.BACKTEST_API_URL}/api/v1/backtest",
            json=request.dict()
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Backtest started successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")

@app.get("/api/v1/backtest/results", response_model=APIResponse)
async def get_backtest_results(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get backtest results"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.BACKTEST_API_URL}/api/v1/runs"
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Backtest results retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtest results")

# Analytics endpoints
@app.get("/api/v1/analytics/performance", response_model=APIResponse)
async def get_performance_analytics(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get performance analytics"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.ANALYTICS_SERVICE_URL}/analytics/performance"
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Performance analytics retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")

# Risk management endpoints
@app.get("/api/v1/risk/positions", response_model=APIResponse)
async def get_risk_positions(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get risk positions"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.RISK_SERVICE_URL}/risk/positions"
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="Risk positions retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting risk positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk positions")

# User management endpoints
@app.get("/api/v1/users/profile", response_model=APIResponse)
async def get_user_profile(
    user_id: str = Depends(verify_api_key),
    _: None = Depends(check_rate_limit)
):
    """Get user profile"""
    try:
        if not http_client:
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_client.get(
            f"{config.USER_SERVICE_URL}/users/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        
        if response.status_code == 200:
            return APIResponse(
                success=True,
                data=response.json(),
                message="User profile retrieved successfully"
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

# WebSocket support for real-time data
@app.websocket("/ws/market-data")
async def websocket_market_data(websocket):
    """WebSocket endpoint for real-time market data"""
    try:
        await websocket.accept()
        
        while True:
            # Send real-time market data
            # This would integrate with your market data service
            data = {
                "type": "market_data",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "AAPL": {"price": 150.25, "change": 0.5},
                    "MSFT": {"price": 300.10, "change": -0.3}
                }
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(1)  # Send updates every second
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
