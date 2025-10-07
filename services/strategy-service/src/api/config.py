"""
Strategy Configuration API
=========================

This module provides API endpoints for getting strategy configurations
for different systems (backtesting, paper trading, live trading).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["strategy-config"])

@router.get("/multi-strategy-ensemble/{system}")
async def get_multi_strategy_ensemble_config(system: str) -> Dict[str, Any]:
    """
    Get MultiStrategyEnsemble configuration for a specific system.
    
    Args:
        system: The system type ('backtesting', 'paper_trading', 'live_trading')
        
    Returns:
        Configuration dictionary for the MultiStrategyEnsemble
    """
    try:
        # Import here to avoid circular imports
        from src.utils.multi_strategy_ensemble_config import get_multi_strategy_ensemble_config
        
        config = get_multi_strategy_ensemble_config(system)
        
        logger.info(f"📋 Retrieved {system} configuration for MultiStrategyEnsemble")
        return {
            "success": True,
            "system": system,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting {system} configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {system} configuration: {str(e)}"
        )

@router.get("/multi-strategy-ensemble/{system}/weights")
async def get_strategy_weights(system: str) -> Dict[str, Any]:
    """
    Get strategy weights for a specific system.
    
    Args:
        system: The system type ('backtesting', 'paper_trading', 'live_trading')
        
    Returns:
        Strategy weights dictionary
    """
    try:
        from src.utils.multi_strategy_ensemble_config import get_strategy_weights
        
        weights = get_strategy_weights(system)
        
        logger.info(f"⚖️ Retrieved {system} strategy weights")
        return {
            "success": True,
            "system": system,
            "weights": weights
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting {system} strategy weights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {system} strategy weights: {str(e)}"
        )

@router.get("/multi-strategy-ensemble/{system}/symbols")
async def get_strategy_symbols(system: str) -> Dict[str, Any]:
    """
    Get symbol list for a specific system.
    
    Args:
        system: The system type ('backtesting', 'paper_trading', 'live_trading')
        
    Returns:
        Symbol list for the system
    """
    try:
        from src.utils.multi_strategy_ensemble_config import get_symbols
        
        symbols = get_symbols(system)
        
        logger.info(f"📊 Retrieved {system} symbol list ({len(symbols)} symbols)")
        return {
            "success": True,
            "system": system,
            "symbols": symbols,
            "count": len(symbols)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting {system} symbol list: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {system} symbol list: {str(e)}"
        )
