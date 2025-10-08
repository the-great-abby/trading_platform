"""
Options Scanning Routes

API endpoints for scanning options opportunities.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import logging
import os

from src.services.live_trading.database import get_db_session
from src.services.live_trading.options_scanner_service import OptionsScannerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/options", tags=["options"])


@router.post("/scan/{account_id}")
async def scan_options_opportunities(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Scan for options trading opportunities.
    
    This endpoint:
    1. Analyzes multiple symbols for options opportunities
    2. Checks IV levels, earnings, volatility, and Greeks
    3. Returns ranked opportunities with strategy suggestions
    """
    try:
        logger.info(f"🔍 Options scan requested for account {account_id}")
        
        # Get account buying power for budget filtering
        from sqlalchemy import text
        result = await db.execute(text("""
            SELECT buying_power, cash_balance
            FROM live_trading_accounts
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        available_cash = float(account_data[0]) if account_data and account_data[0] else 4000.0
        
        logger.info(f"Available cash for options: ${available_cash:.2f}")
        
        # Call strategy service's options scanning endpoint
        import httpx
        strategy_service_url = "http://strategy-service.trading-system.svc.cluster.local:80"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{strategy_service_url}/api/options/scan",
                params={
                    "available_cash": available_cash,
                    "min_confidence": 0.6
                }
            )
            response.raise_for_status()
            scan_result = response.json()
        
        return {
            "success": True,
            "account_id": account_id,
            "available_cash": available_cash,
            **scan_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Options scan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Options scan failed: {str(e)}"
        )


@router.post("/execute/{account_id}")
async def execute_options_opportunities(
    account_id: str,
    max_trades: int = 3,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Scan for options opportunities and execute trades.
    
    This endpoint:
    1. Scans for budget-friendly options opportunities
    2. Ranks them by confidence
    3. Executes top opportunities (up to max_trades)
    
    Args:
        account_id: Account ID
        max_trades: Maximum number of trades to execute (default: 3)
    """
    try:
        logger.info(f"🚀 Options scan & execute requested for account {account_id}")
        
        # Get account buying power
        from sqlalchemy import text
        result = await db.execute(text("""
            SELECT buying_power, cash_balance
            FROM live_trading_accounts
            WHERE account_id = :account_id
        """), {"account_id": account_id})
        
        account_data = result.fetchone()
        available_cash = float(account_data[0]) if account_data and account_data[0] else 4000.0
        
        logger.info(f"Available cash for options: ${available_cash:.2f}")
        
        # Scan for opportunities
        import httpx
        strategy_service_url = "http://strategy-service.trading-system.svc.cluster.local:80"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{strategy_service_url}/api/options/scan",
                params={
                    "available_cash": available_cash,
                    "min_confidence": 0.6
                }
            )
            response.raise_for_status()
            scan_result = response.json()
        
        opportunities = scan_result.get('opportunities', [])
        
        if not opportunities:
            return {
                "success": True,
                "account_id": account_id,
                "available_cash": available_cash,
                "opportunities_found": 0,
                "orders_submitted": 0,
                "message": "No affordable options opportunities found"
            }
        
        # Execute opportunities
        from src.services.live_trading.options_execution_service import OptionsExecutionService
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.public_api_client import PublicAPIClient
        
        # Initialize services
        api_client = PublicAPIClient()
        risk_service = RiskService(db)
        position_service = PositionService(db)
        trading_service = TradingService(db, api_client, risk_service, position_service)
        options_service = OptionsExecutionService(db, trading_service)
        
        # Execute opportunities
        execution_result = await options_service.execute_options_opportunities(
            account_id=account_id,
            opportunities=opportunities,
            max_trades=max_trades
        )
        
        return {
            "success": True,
            "account_id": account_id,
            "available_cash": available_cash,
            **scan_result,
            **execution_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Options execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Options execution failed: {str(e)}"
        )


@router.get("/opportunities/{account_id}")
async def get_recent_opportunities(
    account_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get recently identified options opportunities.
    
    Returns the most recent scan results.
    """
    try:
        # For now, return empty - in production you'd store scan results in DB
        return {
            "success": True,
            "account_id": account_id,
            "opportunities": [],
            "message": "Run /scan/{account_id} to generate new opportunities"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
