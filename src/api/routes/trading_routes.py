"""
Trading API Routes
REST API endpoints for trading operations
"""

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator

from src.services.trading.trading_service import TradingService
from src.services.trading.market_data_service import MarketDataService
from src.api.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/trading", tags=["trading"])

# Pydantic models for API requests/responses
class PlaceOrderRequest(BaseModel):
    """Request model for placing an order"""
    symbol: str = Field(..., description="Trading symbol (e.g., 'AAPL')")
    side: str = Field(..., description="Order side ('buy' or 'sell')")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    order_type: str = Field(default="market", description="Order type")
    price: Optional[Decimal] = Field(None, description="Limit price")
    stop_price: Optional[Decimal] = Field(None, description="Stop price")
    time_in_force: str = Field(default="GTC", description="Time in force")
    client_order_id: Optional[str] = Field(None, description="Client order ID")
    
    @validator('side')
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('Side must be "buy" or "sell"')
        return v
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v not in ['market', 'limit', 'stop', 'stop_limit']:
            raise ValueError('Invalid order type')
        return v
    
    @validator('time_in_force')
    def validate_time_in_force(cls, v):
        if v not in ['GTC', 'IOC', 'FOK', 'DAY']:
            raise ValueError('Invalid time in force')
        return v


class PlaceOrderResponse(BaseModel):
    """Response model for placing an order"""
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order"""
    order_id: str = Field(..., description="Order ID to cancel")


class CancelOrderResponse(BaseModel):
    """Response model for cancelling an order"""
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class OrderStatusResponse(BaseModel):
    """Response model for order status"""
    success: bool
    order: Optional[dict] = None
    error: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Response model for portfolio"""
    success: bool
    portfolio: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class PositionsResponse(BaseModel):
    """Response model for positions"""
    success: bool
    positions: List[dict] = Field(default_factory=list)
    timestamp: datetime
    error: Optional[str] = None


class OrdersResponse(BaseModel):
    """Response model for orders"""
    success: bool
    orders: List[dict] = Field(default_factory=list)
    timestamp: datetime
    error: Optional[str] = None


class MarketDataResponse(BaseModel):
    """Response model for market data"""
    success: bool
    symbol: str
    price: Optional[Decimal] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    error: Optional[str] = None


# Dependency to get trading service
async def get_trading_service() -> TradingService:
    """Get trading service instance"""
    from fastapi import Request
    from src.services.cqrs.cqrs_service import CQRSService
    from unittest.mock import Mock
    import os
    
    # Try to get the real CQRS service from app state
    # This is a bit of a hack since we can't easily access app state from here
    # We'll need to modify this to use proper dependency injection
    try:
        # For now, create a new CQRS service with real database connection
        from src.services.database import initialize_database
        database_url = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")
        db_manager = await initialize_database(database_url)
        cqrs_service = CQRSService(db_manager, None)  # No Redis for now
    except Exception as e:
        print(f"Failed to initialize real database connection: {e}")
        # Fallback to mock connections
        cqrs_service = CQRSService(db_conn=Mock(), redis_client=Mock())
    
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    return TradingService(cqrs_service, discord_webhook_url=discord_webhook_url)


# Dependency to get market data service
async def get_market_data_service() -> MarketDataService:
    """Get market data service instance"""
    service = MarketDataService()
    await service.initialize()
    return service


@router.post("/orders", response_model=PlaceOrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Place a new order
    
    - **symbol**: Trading symbol (e.g., 'AAPL')
    - **side**: Order side ('buy' or 'sell')
    - **quantity**: Order quantity (must be positive)
    - **order_type**: Order type ('market', 'limit', 'stop', 'stop_limit')
    - **price**: Limit price (required for limit orders)
    - **stop_price**: Stop price (required for stop orders)
    - **time_in_force**: Time in force ('GTC', 'IOC', 'FOK')
    - **client_order_id**: Optional client-provided order ID
    """
    try:
        result = await trading_service.place_order(
            user_id=current_user["user_id"],
            account_id=current_user["account_id"],
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            client_order_id=request.client_order_id
        )
        
        return PlaceOrderResponse(**result)
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/orders/{order_id}/cancel", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Cancel an existing order
    
    - **order_id**: Order ID to cancel
    """
    try:
        result = await trading_service.cancel_order(
            user_id=current_user["user_id"],
            account_id=current_user["account_id"],
            order_id=order_id
        )
        
        return CancelOrderResponse(**result)
        
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/orders/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Get order status
    
    - **order_id**: Order ID to check
    """
    try:
        result = await trading_service.get_order_status(order_id)
        
        return OrderStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/orders", response_model=OrdersResponse)
async def get_orders(
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service),
    status: Optional[str] = Query(None, description="Filter by order status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get user orders
    
    - **status**: Optional status filter
    - **symbol**: Optional symbol filter
    """
    try:
        result = await trading_service.get_orders(
            user_id=current_user["user_id"],
            account_id=current_user["account_id"],
            status=status,
            symbol=symbol
        )
        
        return OrdersResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Get user portfolio
    """
    try:
        result = await trading_service.get_portfolio(
            user_id=current_user["user_id"],
            account_id=current_user["account_id"]
        )
        
        return PortfolioResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(
    current_user: dict = Depends(get_current_user),
    trading_service: TradingService = Depends(get_trading_service),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get user positions
    
    - **symbol**: Optional symbol filter
    """
    try:
        result = await trading_service.get_positions(
            user_id=current_user["user_id"],
            account_id=current_user["account_id"],
            symbol=symbol
        )
        
        return PositionsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get latest market data for a symbol
    
    - **symbol**: Trading symbol
    """
    try:
        market_data = await market_data_service.get_latest_price(symbol)
        
        if market_data:
            return MarketDataResponse(
                success=True,
                symbol=market_data.symbol,
                price=market_data.price,
                volume=market_data.volume,
                timestamp=market_data.timestamp,
                bid=market_data.bid,
                ask=market_data.ask,
                high=market_data.high,
                low=market_data.low,
                open=market_data.open,
                change=market_data.change,
                change_percent=market_data.change_percent
            )
        else:
            return MarketDataResponse(
                success=False,
                symbol=symbol,
                error="No data available for symbol"
            )
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/market-data/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    interval: str = Query("1min", description="Data interval"),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get historical market data for a symbol
    
    - **symbol**: Trading symbol
    - **start_date**: Start date
    - **end_date**: End date
    - **interval**: Data interval ('1min', '5min', '1hour', '1day')
    """
    try:
        historical_data = await market_data_service.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "data": [
                {
                    "timestamp": data.timestamp,
                    "price": data.price,
                    "volume": data.volume,
                    "high": data.high,
                    "low": data.low,
                    "open": data.open
                }
                for data in historical_data
            ],
            "count": len(historical_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Test endpoints (bypass authentication for testing)
@router.post("/test/orders", response_model=PlaceOrderResponse)
async def test_place_order(
    request: PlaceOrderRequest,
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Test endpoint for placing orders (bypasses authentication)
    """
    try:
        result = await trading_service.place_order(
            user_id="test-user",
            account_id="test-account",
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            client_order_id=request.client_order_id
        )
        
        return PlaceOrderResponse(**result)
        
    except Exception as e:
        logger.error(f"Error placing test order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test/orders", response_model=OrdersResponse)
async def test_get_orders(
    trading_service: TradingService = Depends(get_trading_service),
    status: Optional[str] = Query(None, description="Filter by order status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Test endpoint for getting orders (bypasses authentication)
    """
    try:
        result = await trading_service.get_orders(
            user_id="test-user",
            account_id="test-account",
            status=status,
            symbol=symbol
        )
        
        return OrdersResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting test orders: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test/portfolio", response_model=PortfolioResponse)
async def test_get_portfolio(
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Test endpoint for getting portfolio (bypasses authentication)
    """
    try:
        result = await trading_service.get_portfolio(
            user_id="test-user",
            account_id="test-account"
        )
        
        return PortfolioResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting test portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test/positions", response_model=PositionsResponse)
async def test_get_positions(
    trading_service: TradingService = Depends(get_trading_service),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Test endpoint for getting positions (bypasses authentication)
    """
    try:
        result = await trading_service.get_positions(
            user_id="test-user",
            account_id="test-account",
            symbol=symbol
        )
        
        return PositionsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting test positions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/test/portfolio/notify")
async def test_portfolio_notification(
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Test endpoint for sending portfolio notification to Discord
    """
    try:
        # Get portfolio data
        portfolio_result = await trading_service.get_portfolio(
            user_id="test-user",
            account_id="test-account"
        )
        
        if portfolio_result.get("success"):
            portfolio = portfolio_result.get("portfolio", {})
            
            # Send Discord notification
            if hasattr(trading_service, 'discord_service') and trading_service.discord_service:
                await trading_service.discord_service.send_portfolio_notification(
                    user_id="test-user",
                    account_id="test-account",
                    portfolio_value=portfolio.get("total_value", 100000),
                    total_pnl=portfolio.get("total_pnl", 5000),
                    positions=portfolio.get("positions", [])
                )
                
                return {
                    "success": True,
                    "message": "Portfolio notification sent to Discord",
                    "portfolio": portfolio
                }
            else:
                return {
                    "success": False,
                    "message": "Discord service not available",
                    "portfolio": portfolio
                }
        else:
            return {
                "success": False,
                "message": "Failed to get portfolio data",
                "error": portfolio_result.get("error")
            }
        
    except Exception as e:
        logger.error(f"Error sending test portfolio notification: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/test/risk/alert")
async def test_risk_alert(
    alert_type: str = "Position Limit Exceeded",
    message: str = "Test risk alert - position size exceeds 10% of portfolio",
    severity: str = "warning",
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Test endpoint for sending risk alert to Discord
    """
    try:
        if hasattr(trading_service, 'discord_service') and trading_service.discord_service:
            await trading_service.discord_service.send_risk_alert(
                alert_type=alert_type,
                message=message,
                user_id="test-user",
                account_id="test-account",
                severity=severity
            )
            
            return {
                "success": True,
                "message": f"Risk alert sent to Discord: {alert_type}",
                "alert_type": alert_type,
                "severity": severity
            }
        else:
            return {
                "success": False,
                "message": "Discord service not available"
            }
        
    except Exception as e:
        logger.error(f"Error sending test risk alert: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/test/system/alert")
async def test_system_alert(
    alert_type: str = "System Health Check",
    message: str = "Test system alert - all services running normally",
    severity: str = "info",
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    Test endpoint for sending system alert to Discord
    """
    try:
        if hasattr(trading_service, 'discord_service') and trading_service.discord_service:
            await trading_service.discord_service.send_system_alert(
                alert_type=alert_type,
                message=message,
                severity=severity
            )
            
            return {
                "success": True,
                "message": f"System alert sent to Discord: {alert_type}",
                "alert_type": alert_type,
                "severity": severity
            }
        else:
            return {
                "success": False,
                "message": "Discord service not available"
            }
        
    except Exception as e:
        logger.error(f"Error sending test system alert: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
