"""
Trade Recovery API Routes

Handles trade recovery operations and disaster recovery scenarios.
Consolidated into Live Trading Service for resource efficiency.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.live_trading.database import get_db_session
from src.services.live_trading.public_api_client import PublicAPIClient
from src.services.live_trading.recovery_service import RecoveryService
from src.services.live_trading.recovery_models import (
    RecoverySessionCreate, RecoverySessionResponse, RecoverySessionStatus,
    ActiveTradeResponse, StrategyMatchResponse, StrategyAssignmentRequest,
    StrategyAssignmentResponse, RecoveryProgress
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recovery", tags=["recovery"])


# Pydantic models for API
class ActiveTradeRequest(BaseModel):
    """Request to detect active trades"""
    account_id: str = Field(..., description="Trading account ID")
    include_closed: bool = Field(default=False, description="Include recently closed trades")


class StrategyMatchRequest(BaseModel):
    """Request to match strategies for a trade"""
    trade_id: str = Field(..., description="Trade ID")
    session_id: str = Field(..., description="Recovery session ID")


class RecoverySessionUpdate(BaseModel):
    """Update recovery session"""
    status: Optional[str] = Field(None, description="Session status")
    total_trades_detected: Optional[int] = Field(None, description="Total trades detected")
    trades_processed: Optional[int] = Field(None, description="Trades processed")
    trades_assigned: Optional[int] = Field(None, description="Trades assigned")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message")
    summary: Optional[str] = Field(None, description="Session summary")


@router.post("/sessions", response_model=RecoverySessionResponse)
async def create_recovery_session(
    session_data: RecoverySessionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new recovery session"""
    try:
        recovery_service = RecoveryService(db)
        session = await recovery_service.create_recovery_session(session_data)
        
        logger.info(f"Created recovery session {session.id} for account {session.account_id}")
        return RecoverySessionResponse.from_orm(session)
        
    except Exception as e:
        logger.error(f"Failed to create recovery session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recovery session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=RecoverySessionResponse)
async def get_recovery_session(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recovery session by ID"""
    try:
        recovery_service = RecoveryService(db)
        session = await recovery_service.get_recovery_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery session not found"
            )
        
        return RecoverySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recovery session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery session: {str(e)}"
        )


@router.get("/sessions/{session_id}/status", response_model=RecoverySessionStatus)
async def get_recovery_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recovery session status with progress details"""
    try:
        recovery_service = RecoveryService(db)
        status_info = await recovery_service.get_recovery_session_status(session_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery session not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recovery session status {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery session status: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=RecoverySessionResponse)
async def update_recovery_session(
    session_id: str,
    update_data: RecoverySessionUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update recovery session"""
    try:
        recovery_service = RecoveryService(db)
        session = await recovery_service.update_recovery_session(session_id, update_data)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery session not found"
            )
        
        return RecoverySessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update recovery session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recovery session: {str(e)}"
        )


@router.get("/sessions", response_model=List[RecoverySessionResponse])
async def list_recovery_sessions(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    """List recovery sessions"""
    try:
        recovery_service = RecoveryService(db)
        sessions = await recovery_service.list_recovery_sessions(account_id, status, limit)
        
        return [RecoverySessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to list recovery sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list recovery sessions: {str(e)}"
        )


@router.post("/trades/active", response_model=List[ActiveTradeResponse])
async def detect_active_trades(
    request: ActiveTradeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Detect active trades for an account"""
    try:
        recovery_service = RecoveryService(db)
        trades = await recovery_service.detect_active_trades(
            request.account_id, 
            request.include_closed
        )
        
        logger.info(f"Detected {len(trades)} active trades for account {request.account_id}")
        return [ActiveTradeResponse.from_orm(trade) for trade in trades]
        
    except Exception as e:
        logger.error(f"Failed to detect active trades for account {request.account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect active trades: {str(e)}"
        )


@router.get("/strategies/available", response_model=List[Dict[str, Any]])
async def get_available_strategies(
    account_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get available strategies for recovery"""
    try:
        recovery_service = RecoveryService(db)
        strategies = await recovery_service.get_available_strategies(account_id)
        
        return strategies
        
    except Exception as e:
        logger.error(f"Failed to get available strategies for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available strategies: {str(e)}"
        )


@router.post("/strategies/match", response_model=List[StrategyMatchResponse])
async def match_strategies(
    request: StrategyMatchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Match strategies for a specific trade"""
    try:
        recovery_service = RecoveryService(db)
        matches = await recovery_service.match_strategies_for_trade(
            request.trade_id, 
            request.session_id
        )
        
        return [StrategyMatchResponse.from_orm(match) for match in matches]
        
    except Exception as e:
        logger.error(f"Failed to match strategies for trade {request.trade_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match strategies: {str(e)}"
        )


@router.post("/assign-strategy", response_model=StrategyAssignmentResponse)
async def assign_strategy(
    request: StrategyAssignmentRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Assign a strategy to a trade"""
    try:
        recovery_service = RecoveryService(db)
        assignment = await recovery_service.assign_strategy_to_trade(request)
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign strategy to trade"
            )
        
        return StrategyAssignmentResponse.from_orm(assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign strategy to trade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign strategy: {str(e)}"
        )


@router.post("/assign-strategy/{assignment_id}/confirm")
async def confirm_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Confirm a strategy assignment"""
    try:
        recovery_service = RecoveryService(db)
        success = await recovery_service.confirm_assignment(assignment_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already processed"
            )
        
        return {"message": "Assignment confirmed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm assignment {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm assignment: {str(e)}"
        )


@router.post("/assign-strategy/{assignment_id}/reject")
async def reject_assignment(
    assignment_id: str,
    reason: str = "User rejected assignment",
    db: AsyncSession = Depends(get_db_session)
):
    """Reject a strategy assignment"""
    try:
        recovery_service = RecoveryService(db)
        success = await recovery_service.reject_assignment(assignment_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already processed"
            )
        
        return {"message": "Assignment rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject assignment {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject assignment: {str(e)}"
        )


@router.get("/sessions/{session_id}/assignments", response_model=List[StrategyAssignmentResponse])
async def get_session_assignments(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get strategy assignments for a recovery session"""
    try:
        recovery_service = RecoveryService(db)
        assignments = await recovery_service.get_session_assignments(session_id)
        
        return [StrategyAssignmentResponse.from_orm(assignment) for assignment in assignments]
        
    except Exception as e:
        logger.error(f"Failed to get assignments for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignments: {str(e)}"
        )


@router.get("/sessions/{session_id}/logs")
async def get_recovery_logs(
    session_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recovery logs for a session"""
    try:
        recovery_service = RecoveryService(db)
        logs = await recovery_service.get_recovery_logs(session_id, limit)
        
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get recovery logs for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery logs: {str(e)}"
        )


@router.post("/bulk-assign")
async def bulk_assign_strategies(
    session_id: str,
    auto_assign: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """Bulk assign strategies to all trades in a session"""
    try:
        recovery_service = RecoveryService(db)
        results = await recovery_service.bulk_assign_strategies(session_id, auto_assign)
        
        return {
            "message": "Bulk assignment completed",
            "results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r.get("success", False)])
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk assign strategies for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk assign strategies: {str(e)}"
        )


















