"""
Strategy management routes
"""

from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any

from src.api.models.cqrs_models import (
    CreateStrategyRequest, StrategyResponse
)

router = APIRouter()


@router.post("/strategies", response_model=Dict[str, Any], status_code=201)
async def create_strategy(request: CreateStrategyRequest, app_request: Request):
    """Create a new strategy"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create command
    from src.services.cqrs.commands import CreateStrategyCommand
    command = CreateStrategyCommand(
        name=request.name,
        description=request.description,
        parameters=request.parameters,
        user_id=request.user_id,
        account_id=request.account_id
    )
    
    # Dispatch command
    result = await cqrs_service.dispatch_command(command)
    
    if result.get("success"):
        return {
            "success": True,
            "strategy_id": result.get("strategy_id"),
            "status": result.get("status")
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to create strategy")
        )


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str, app_request: Request):
    """Get strategy details"""
    cqrs_service = app_request.app.state.cqrs_service
    
    # Create query
    from src.services.cqrs.queries import GetStrategyQuery
    query = GetStrategyQuery(strategy_id=strategy_id)
    
    # Execute query
    result = await cqrs_service.execute_query(query)
    
    if result.get("success"):
        return result.get("strategy")
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Strategy not found")
        )
