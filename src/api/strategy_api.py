"""
Strategy API - Provides dynamic strategy information to the frontend
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..strategies.strategy_registry import get_strategy_registry, discover_strategies

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyInfo(BaseModel):
    """Strategy information model"""
    name: str
    category: str
    description: str
    module: str


class StrategyCategory(BaseModel):
    """Strategy category information"""
    name: str
    strategies: List[str]
    count: int


class StrategyListResponse(BaseModel):
    """Response model for strategy list"""
    categories: Dict[str, StrategyCategory]
    all_strategies: List[str]
    total_count: int


@router.get("/", response_model=StrategyListResponse)
async def get_strategies():
    """Get all available strategies organized by category"""
    try:
        registry = get_strategy_registry()
        
        # Discover strategies if not already done
        if not registry.discovered:
            discover_strategies()
        
        # Get categories
        categories = registry.get_all_categories()
        
        # Build response
        category_responses = {}
        all_strategies = []
        
        for category_name, strategy_list in categories.items():
            if strategy_list:  # Only include categories with strategies
                category_responses[category_name] = StrategyCategory(
                    name=category_name,
                    strategies=sorted(strategy_list),
                    count=len(strategy_list)
                )
                all_strategies.extend(strategy_list)
        
        return StrategyListResponse(
            categories=category_responses,
            all_strategies=sorted(all_strategies),
            total_count=len(all_strategies)
        )
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving strategies: {str(e)}")


@router.get("/categories/{category}")
async def get_strategies_by_category(category: str):
    """Get strategies by category"""
    try:
        registry = get_strategy_registry()
        strategies = registry.get_strategies_by_category(category)
        
        return {
            "category": category,
            "strategies": sorted(strategies),
            "count": len(strategies)
        }
        
    except Exception as e:
        logger.error(f"Error getting strategies for category {category}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving strategies: {str(e)}")


@router.get("/info/{strategy_name}")
async def get_strategy_info(strategy_name: str):
    """Get detailed information about a specific strategy"""
    try:
        registry = get_strategy_registry()
        info = registry.get_strategy_info(strategy_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy info for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving strategy info: {str(e)}")


@router.get("/validate")
async def validate_strategies():
    """Validate all discovered strategies"""
    try:
        registry = get_strategy_registry()
        results = registry.validate_strategies()
        
        return {
            "valid_count": len(results["valid"]),
            "invalid_count": len(results["invalid"]),
            "valid_strategies": results["valid"],
            "invalid_strategies": results["invalid"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        logger.error(f"Error validating strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating strategies: {str(e)}")


@router.get("/list")
async def list_strategies():
    """Get a formatted list of all strategies"""
    try:
        registry = get_strategy_registry()
        return {"strategies_list": registry.list_strategies()}
        
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing strategies: {str(e)}")


@router.get("/count")
async def get_strategy_count():
    """Get the total number of available strategies"""
    try:
        registry = get_strategy_registry()
        categories = registry.get_all_categories()
        
        total_count = sum(len(strategies) for strategies in categories.values())
        category_counts = {cat: len(strategies) for cat, strategies in categories.items()}
        
        return {
            "total_strategies": total_count,
            "category_counts": category_counts
        }
        
    except Exception as e:
        logger.error(f"Error getting strategy count: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting strategy count: {str(e)}") 