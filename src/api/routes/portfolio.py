"""
Portfolio management routes
"""

from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any

from src.api.models.cqrs_models import (
    GetPortfolioRequest, GetPositionsRequest, UpdatePortfolioRequest,
    PortfolioResponse, PositionResponse
)

router = APIRouter()


@router.get("/portfolio/{user_id}/{account_id}", response_model=Dict[str, Any])
async def get_portfolio(user_id: str, account_id: str, app_request: Request, 
                       include_positions: bool = False, include_performance: bool = False):
    """Get portfolio details"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetPortfolioQuery
    query = GetPortfolioQuery(
        user_id=user_id,
        account_id=account_id,
        include_positions=include_positions,
        include_performance=include_performance
    )
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return {
            "success": True,
            "portfolio": result.get("portfolio")
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Portfolio not found")
        )


@router.put("/portfolio/{portfolio_id}", response_model=Dict[str, Any])
async def update_portfolio(portfolio_id: str, request: UpdatePortfolioRequest, app_request: Request):
    """Update portfolio"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create command
    from src.services.cqrs.commands import UpdatePortfolioCommand
    command = UpdatePortfolioCommand(
        portfolio_id=portfolio_id,
        name=request.name,
        cash_balance=request.cash_balance,
        user_id=request.user_id,
        account_id=request.account_id
    )
    
    # Dispatch command
    result = await cqrs_service.dispatch_command(command)
    
    if result.get("success"):
        return {
            "success": True,
            "portfolio_id": result.get("portfolio_id"),
            "status": result.get("status")
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to update portfolio")
        )


@router.get("/positions/{user_id}/{account_id}", response_model=Dict[str, Any])
async def get_positions(user_id: str, account_id: str, app_request: Request,
                       symbol: str = None, status: str = None):
    """Get positions"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetPositionsQuery
    query = GetPositionsQuery(
        user_id=user_id,
        account_id=account_id,
        symbol=symbol,
        status=status
    )
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return {
            "success": True,
            "positions": result.get("positions")
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Positions not found")
        )
