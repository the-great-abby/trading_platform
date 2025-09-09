"""
Market data routes
"""

from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any

from src.api.models.cqrs_models import (
    GetMarketDataRequest, GetPerformanceRequest, GetBacktestResultsRequest,
    MarketDataResponse, PerformanceResponse, BacktestResultsResponse
)

router = APIRouter()


@router.get("/market-data/{symbol}", response_model=Dict[str, Any])
async def get_market_data(symbol: str, app_request: Request, 
                         start_date: str = None, end_date: str = None, interval: str = "1d"):
    """Get market data"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetMarketDataQuery
    query = GetMarketDataQuery(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return {
            "success": True,
            "market_data": result.get("market_data")
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Market data not found")
        )


@router.get("/performance/{user_id}/{account_id}", response_model=Dict[str, Any])
async def get_performance(user_id: str, account_id: str, app_request: Request,
                         start_date: str, end_date: str, 
                         metrics: str = "total_return,sharpe_ratio,max_drawdown"):
    """Get performance metrics"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Parse metrics
    metrics_list = [m.strip() for m in metrics.split(",")]
    
    # Create query
    from src.services.cqrs.queries import GetPerformanceQuery
    query = GetPerformanceQuery(
        user_id=user_id,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        metrics=metrics_list
    )
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return {
            "success": True,
            "performance": result.get("performance")
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Performance data not found")
        )


@router.get("/backtest/{strategy_id}", response_model=Dict[str, Any])
async def get_backtest_results(strategy_id: str, app_request: Request,
                              start_date: str, end_date: str):
    """Get backtest results"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetBacktestResultsQuery
    query = GetBacktestResultsQuery(
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return {
            "success": True,
            "backtest_results": result.get("backtest_results")
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Backtest results not found")
        )
