"""
Trade Recovery Service

Consolidated recovery service integrated into Live Trading Service.
Handles trade detection, strategy matching, and recovery operations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from .recovery_models import (
    ActiveTrade, RecoverySession, RecoverySessionCreate, RecoverySessionStatus,
    RecoveryProgress, StrategyAssignment, StrategyAssignmentRequest,
    StrategyMatch, SessionStatus, RecoveryType, AssignmentStatus, AssignmentReason,
    TradeSide, PositionType, OptionDetails, ActiveTradeModel, RecoverySessionModel,
    StrategyAssignmentModel, RecoveryLogModel
)
from .public_api_client import PublicAPIClient

logger = logging.getLogger(__name__)


class RecoveryService:
    """Service for handling trade recovery operations"""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize recovery service"""
        self.db = db_session
        self.broker_client = PublicAPIClient()
    
    async def create_recovery_session(self, session_data: RecoverySessionCreate) -> RecoverySession:
        """Create a new recovery session"""
        try:
            session_id = str(uuid4())
            
            # Create database record
            db_session = RecoverySessionModel(
                id=session_id,
                account_id=session_data.account_id,
                user_id=session_data.user_id,
                status=SessionStatus.IN_PROGRESS.value,
                recovery_type=session_data.recovery_type.value,
                description=session_data.description,
                started_at=datetime.utcnow()
            )
            
            self.db.add(db_session)
            await self.db.commit()
            await self.db.refresh(db_session)
            
            # Create recovery log
            await self._create_recovery_log(
                session_id,
                "info",
                f"Recovery session created for account {session_data.account_id}",
                {"recovery_type": session_data.recovery_type.value}
            )
            
            # Convert to Pydantic model
            session = RecoverySession(
                id=db_session.id,
                account_id=db_session.account_id,
                user_id=db_session.user_id,
                status=SessionStatus(db_session.status),
                recovery_type=RecoveryType(db_session.recovery_type),
                description=db_session.description,
                total_trades_detected=db_session.total_trades_detected,
                trades_processed=db_session.trades_processed,
                trades_assigned=db_session.trades_assigned,
                started_at=db_session.started_at,
                completed_at=db_session.completed_at,
                cancelled_at=db_session.cancelled_at,
                cancellation_reason=db_session.cancellation_reason,
                error_message=db_session.error_message,
                summary=db_session.summary,
                created_at=db_session.created_at,
                updated_at=db_session.updated_at
            )
            
            logger.info(f"Created recovery session {session_id} for account {session_data.account_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create recovery session: {e}")
            raise
    
    async def get_recovery_session(self, session_id: str) -> Optional[RecoverySession]:
        """Get recovery session by ID"""
        try:
            result = await self.db.execute(
                select(RecoverySessionModel).where(RecoverySessionModel.id == session_id)
            )
            db_session = result.scalar_one_or_none()
            
            if not db_session:
                return None
            
            return RecoverySession(
                id=db_session.id,
                account_id=db_session.account_id,
                user_id=db_session.user_id,
                status=SessionStatus(db_session.status),
                recovery_type=RecoveryType(db_session.recovery_type),
                description=db_session.description,
                total_trades_detected=db_session.total_trades_detected,
                trades_processed=db_session.trades_processed,
                trades_assigned=db_session.trades_assigned,
                started_at=db_session.started_at,
                completed_at=db_session.completed_at,
                cancelled_at=db_session.cancelled_at,
                cancellation_reason=db_session.cancellation_reason,
                error_message=db_session.error_message,
                summary=db_session.summary,
                created_at=db_session.created_at,
                updated_at=db_session.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get recovery session {session_id}: {e}")
            return None
    
    async def update_recovery_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[RecoverySession]:
        """Update recovery session"""
        try:
            # Update database record
            update_values = {k: v for k, v in update_data.items() if v is not None}
            update_values['updated_at'] = datetime.utcnow()
            
            result = await self.db.execute(
                update(RecoverySessionModel)
                .where(RecoverySessionModel.id == session_id)
                .values(**update_values)
            )
            
            if result.rowcount == 0:
                return None
            
            await self.db.commit()
            
            # Get updated session
            return await self.get_recovery_session(session_id)
            
        except Exception as e:
            logger.error(f"Failed to update recovery session {session_id}: {e}")
            return None
    
    async def get_recovery_session_status(self, session_id: str) -> Optional[RecoverySessionStatus]:
        """Get recovery session status with progress details"""
        try:
            session = await self.get_recovery_session(session_id)
            if not session:
                return None
            
            # Calculate progress
            progress = RecoveryProgress(
                total_trades_detected=session.total_trades_detected,
                trades_processed=session.trades_processed,
                trades_assigned=session.trades_assigned,
                completion_percentage=session.calculate_completion_percentage()
            )
            
            return RecoverySessionStatus(
                session_id=session.id,
                status=session.status,
                progress=progress,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get recovery session status {session_id}: {e}")
            return None
    
    async def list_recovery_sessions(self, account_id: Optional[str] = None, 
                                   status: Optional[str] = None, limit: int = 50) -> List[RecoverySession]:
        """List recovery sessions"""
        try:
            query = select(RecoverySessionModel)
            
            if account_id:
                query = query.where(RecoverySessionModel.account_id == account_id)
            
            if status:
                query = query.where(RecoverySessionModel.status == status)
            
            query = query.order_by(RecoverySessionModel.started_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            db_sessions = result.scalars().all()
            
            sessions = []
            for db_session in db_sessions:
                session = RecoverySession(
                    id=db_session.id,
                    account_id=db_session.account_id,
                    user_id=db_session.user_id,
                    status=SessionStatus(db_session.status),
                    recovery_type=RecoveryType(db_session.recovery_type),
                    description=db_session.description,
                    total_trades_detected=db_session.total_trades_detected,
                    trades_processed=db_session.trades_processed,
                    trades_assigned=db_session.trades_assigned,
                    started_at=db_session.started_at,
                    completed_at=db_session.completed_at,
                    cancelled_at=db_session.cancelled_at,
                    cancellation_reason=db_session.cancellation_reason,
                    error_message=db_session.error_message,
                    summary=db_session.summary,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list recovery sessions: {e}")
            return []
    
    async def detect_active_trades(self, account_id: str, include_closed: bool = False) -> List[ActiveTrade]:
        """Detect active trades for an account"""
        try:
            logger.info(f"Detecting active trades for account {account_id}")
            
            # Get positions from broker API
            positions = await self.broker_client.get_positions(account_id)
            
            active_trades = []
            for position in positions:
                try:
                    # Convert position to ActiveTrade
                    trade = await self._convert_position_to_trade(position, account_id)
                    
                    # Store in database
                    await self._store_trade_in_db(trade)
                    
                    active_trades.append(trade)
                    
                except Exception as e:
                    logger.error(f"Failed to convert position to trade: {e}")
                    continue
            
            logger.info(f"Detected {len(active_trades)} active trades for account {account_id}")
            return active_trades
            
        except Exception as e:
            logger.error(f"Failed to detect active trades for account {account_id}: {e}")
            raise
    
    async def _convert_position_to_trade(self, position: Dict[str, Any], account_id: str) -> ActiveTrade:
        """Convert broker position to ActiveTrade object"""
        try:
            # Extract basic position data
            symbol = position.get("symbol", "")
            quantity = Decimal(str(position.get("quantity", 0)))
            side = TradeSide(position.get("side", "BUY"))
            entry_price = Decimal(str(position.get("entry_price", 0)))
            current_price = Decimal(str(position.get("current_price", 0))) if position.get("current_price") else None
            position_type = PositionType(position.get("position_type", "STOCK"))
            
            # Extract optional data
            entry_date = None
            if position.get("entry_date"):
                entry_date = datetime.fromisoformat(position["entry_date"].replace("Z", "+00:00"))
            
            # Handle option details
            option_details = None
            if position_type == PositionType.OPTION and position.get("option_details"):
                option_data = position["option_details"]
                option_details = OptionDetails(
                    strike=Decimal(str(option_data.get("strike", 0))) if option_data.get("strike") else None,
                    expiration=datetime.fromisoformat(option_data["expiration"].replace("Z", "+00:00")) if option_data.get("expiration") else None,
                    option_type=option_data.get("option_type")
                )
            
            # Calculate unrealized P&L
            unrealized_pnl = None
            if current_price:
                if side == TradeSide.BUY:
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:  # SELL
                    unrealized_pnl = (entry_price - current_price) * quantity
            
            # Create ActiveTrade object
            trade = ActiveTrade(
                id=str(uuid4()),
                account_id=account_id,
                symbol=symbol,
                quantity=quantity,
                side=side,
                entry_price=entry_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                entry_time=entry_date or datetime.utcnow(),
                detected_at=datetime.utcnow(),
                position_type=position_type,
                option_details=option_details,
                trade_metadata=position.get("metadata", {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to convert position to trade: {e}")
            raise
    
    async def _store_trade_in_db(self, trade: ActiveTrade):
        """Store trade in database"""
        try:
            db_trade = ActiveTradeModel(
                id=trade.id,
                account_id=trade.account_id,
                symbol=trade.symbol,
                side=trade.side.value,
                quantity=float(trade.quantity),
                entry_price=float(trade.entry_price),
                current_price=float(trade.current_price) if trade.current_price else None,
                unrealized_pnl=float(trade.unrealized_pnl) if trade.unrealized_pnl else None,
                entry_time=trade.entry_time,
                detected_at=trade.detected_at,
                trade_metadata=trade.trade_metadata
            )
            
            self.db.add(db_trade)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store trade {trade.id} in database: {e}")
            # Don't raise here to avoid breaking the detection process
    
    async def get_available_strategies(self, account_id: str) -> List[Dict[str, Any]]:
        """Get available strategies for recovery"""
        try:
            # This would typically call the strategy service
            # For now, return mock data
            strategies = [
                {
                    "id": "strategy_1",
                    "name": "Elliott Wave Strategy",
                    "description": "Elliott Wave pattern detection",
                    "is_active": True,
                    "confidence_threshold": 0.7
                },
                {
                    "id": "strategy_2",
                    "name": "Moving Average Strategy",
                    "description": "Moving average crossover strategy",
                    "is_active": True,
                    "confidence_threshold": 0.6
                }
            ]
            
            return strategies
            
        except Exception as e:
            logger.error(f"Failed to get available strategies for account {account_id}: {e}")
            return []
    
    async def match_strategies_for_trade(self, trade_id: str, session_id: str) -> List[StrategyMatch]:
        """Match strategies for a specific trade"""
        try:
            # Get trade details
            result = await self.db.execute(
                select(ActiveTradeModel).where(ActiveTradeModel.id == trade_id)
            )
            db_trade = result.scalar_one_or_none()
            
            if not db_trade:
                return []
            
            # Mock strategy matching logic
            # In a real implementation, this would call the strategy service
            matches = [
                StrategyMatch(
                    strategy_id="strategy_1",
                    strategy_name="Elliott Wave Strategy",
                    confidence_score=0.85,
                    match_reason="High confidence Elliott Wave pattern detected",
                    market_conditions="Bullish trend with clear wave structure"
                ),
                StrategyMatch(
                    strategy_id="strategy_2",
                    strategy_name="Moving Average Strategy",
                    confidence_score=0.65,
                    match_reason="Price above moving averages",
                    market_conditions="Uptrend confirmed"
                )
            ]
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to match strategies for trade {trade_id}: {e}")
            return []
    
    async def assign_strategy_to_trade(self, request: StrategyAssignmentRequest) -> Optional[StrategyAssignment]:
        """Assign a strategy to a trade"""
        try:
            assignment_id = str(uuid4())
            
            # Create database record
            db_assignment = StrategyAssignmentModel(
                id=assignment_id,
                session_id=request.session_id,
                trade_id=request.trade_id,
                strategy_id=request.strategy_id,
                strategy_name=request.strategy_name,
                confidence_score=request.confidence_score,
                assignment_reason=request.assignment_reason.value,
                status=AssignmentStatus.ASSIGNED.value,
                auto_assigned=request.auto_assigned,
                notes=request.notes,
                assigned_at=datetime.utcnow()
            )
            
            self.db.add(db_assignment)
            await self.db.commit()
            await self.db.refresh(db_assignment)
            
            # Update session progress
            await self._update_session_progress(request.session_id, 1)
            
            # Create recovery log
            await self._create_recovery_log(
                request.session_id,
                "info",
                f"Strategy {request.strategy_name} assigned to trade {request.trade_id}",
                {
                    "assignment_id": assignment_id,
                    "strategy_id": request.strategy_id,
                    "confidence_score": request.confidence_score
                }
            )
            
            # Convert to Pydantic model
            assignment = StrategyAssignment(
                id=db_assignment.id,
                session_id=db_assignment.session_id,
                trade_id=db_assignment.trade_id,
                strategy_id=db_assignment.strategy_id,
                strategy_name=db_assignment.strategy_name,
                confidence_score=db_assignment.confidence_score,
                assignment_reason=AssignmentReason(db_assignment.assignment_reason),
                status=AssignmentStatus(db_assignment.status),
                auto_assigned=db_assignment.auto_assigned,
                user_confirmed=db_assignment.user_confirmed,
                assigned_at=db_assignment.assigned_at,
                confirmed_at=db_assignment.confirmed_at,
                rejected_at=db_assignment.rejected_at,
                rejection_reason=db_assignment.rejection_reason,
                notes=db_assignment.notes,
                created_at=db_assignment.created_at,
                updated_at=db_assignment.updated_at
            )
            
            logger.info(f"Assigned strategy {request.strategy_name} to trade {request.trade_id}")
            return assignment
            
        except Exception as e:
            logger.error(f"Failed to assign strategy to trade: {e}")
            return None
    
    async def confirm_assignment(self, assignment_id: str) -> bool:
        """Confirm a strategy assignment"""
        try:
            result = await self.db.execute(
                update(StrategyAssignmentModel)
                .where(StrategyAssignmentModel.id == assignment_id)
                .values(
                    status=AssignmentStatus.CONFIRMED.value,
                    user_confirmed=True,
                    confirmed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            if result.rowcount == 0:
                return False
            
            await self.db.commit()
            
            # Create recovery log
            await self._create_recovery_log(
                assignment_id,  # Using assignment_id as session context
                "info",
                f"Strategy assignment {assignment_id} confirmed by user",
                {"assignment_id": assignment_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to confirm assignment {assignment_id}: {e}")
            return False
    
    async def reject_assignment(self, assignment_id: str, reason: str) -> bool:
        """Reject a strategy assignment"""
        try:
            result = await self.db.execute(
                update(StrategyAssignmentModel)
                .where(StrategyAssignmentModel.id == assignment_id)
                .values(
                    status=AssignmentStatus.REJECTED.value,
                    user_confirmed=False,
                    rejected_at=datetime.utcnow(),
                    rejection_reason=reason,
                    updated_at=datetime.utcnow()
                )
            )
            
            if result.rowcount == 0:
                return False
            
            await self.db.commit()
            
            # Create recovery log
            await self._create_recovery_log(
                assignment_id,  # Using assignment_id as session context
                "warning",
                f"Strategy assignment {assignment_id} rejected by user",
                {"assignment_id": assignment_id, "reason": reason}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject assignment {assignment_id}: {e}")
            return False
    
    async def get_session_assignments(self, session_id: str) -> List[StrategyAssignment]:
        """Get strategy assignments for a recovery session"""
        try:
            result = await self.db.execute(
                select(StrategyAssignmentModel)
                .where(StrategyAssignmentModel.session_id == session_id)
                .order_by(StrategyAssignmentModel.assigned_at.desc())
            )
            db_assignments = result.scalars().all()
            
            assignments = []
            for db_assignment in db_assignments:
                assignment = StrategyAssignment(
                    id=db_assignment.id,
                    session_id=db_assignment.session_id,
                    trade_id=db_assignment.trade_id,
                    strategy_id=db_assignment.strategy_id,
                    strategy_name=db_assignment.strategy_name,
                    confidence_score=db_assignment.confidence_score,
                    assignment_reason=AssignmentReason(db_assignment.assignment_reason),
                    status=AssignmentStatus(db_assignment.status),
                    auto_assigned=db_assignment.auto_assigned,
                    user_confirmed=db_assignment.user_confirmed,
                    assigned_at=db_assignment.assigned_at,
                    confirmed_at=db_assignment.confirmed_at,
                    rejected_at=db_assignment.rejected_at,
                    rejection_reason=db_assignment.rejection_reason,
                    notes=db_assignment.notes,
                    created_at=db_assignment.created_at,
                    updated_at=db_assignment.updated_at
                )
                assignments.append(assignment)
            
            return assignments
            
        except Exception as e:
            logger.error(f"Failed to get assignments for session {session_id}: {e}")
            return []
    
    async def get_recovery_logs(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recovery logs for a session"""
        try:
            result = await self.db.execute(
                select(RecoveryLogModel)
                .where(RecoveryLogModel.session_id == session_id)
                .order_by(RecoveryLogModel.timestamp.desc())
                .limit(limit)
            )
            db_logs = result.scalars().all()
            
            logs = []
            for db_log in db_logs:
                log = {
                    "id": db_log.id,
                    "session_id": db_log.session_id,
                    "level": db_log.level,
                    "message": db_log.message,
                    "details": db_log.details,
                    "timestamp": db_log.timestamp.isoformat()
                }
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get recovery logs for session {session_id}: {e}")
            return []
    
    async def bulk_assign_strategies(self, session_id: str, auto_assign: bool = True) -> List[Dict[str, Any]]:
        """Bulk assign strategies to all trades in a session"""
        try:
            # Get all trades for the session
            result = await self.db.execute(
                select(ActiveTradeModel)
                .where(ActiveTradeModel.account_id.in_(
                    select(RecoverySessionModel.account_id)
                    .where(RecoverySessionModel.id == session_id)
                ))
            )
            trades = result.scalars().all()
            
            results = []
            for trade in trades:
                try:
                    # Match strategies for this trade
                    matches = await self.match_strategies_for_trade(trade.id, session_id)
                    
                    if matches:
                        # Use the best match
                        best_match = max(matches, key=lambda m: m.confidence_score)
                        
                        # Create assignment request
                        assignment_request = StrategyAssignmentRequest(
                            session_id=session_id,
                            trade_id=trade.id,
                            strategy_id=best_match.strategy_id,
                            strategy_name=best_match.strategy_name,
                            confidence_score=best_match.confidence_score,
                            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                            auto_assigned=auto_assign
                        )
                        
                        # Assign strategy
                        assignment = await self.assign_strategy_to_trade(assignment_request)
                        
                        results.append({
                            "trade_id": trade.id,
                            "success": True,
                            "assignment_id": assignment.id if assignment else None,
                            "strategy_name": best_match.strategy_name,
                            "confidence_score": best_match.confidence_score
                        })
                    else:
                        results.append({
                            "trade_id": trade.id,
                            "success": False,
                            "error": "No matching strategies found"
                        })
                        
                except Exception as e:
                    results.append({
                        "trade_id": trade.id,
                        "success": False,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to bulk assign strategies for session {session_id}: {e}")
            return []
    
    async def _update_session_progress(self, session_id: str, trades_assigned: int):
        """Update session progress"""
        try:
            await self.db.execute(
                update(RecoverySessionModel)
                .where(RecoverySessionModel.id == session_id)
                .values(
                    trades_assigned=RecoverySessionModel.trades_assigned + trades_assigned,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update session progress for {session_id}: {e}")
    
    async def _create_recovery_log(self, session_id: str, level: str, message: str, details: Dict[str, Any]):
        """Create recovery log entry"""
        try:
            log = RecoveryLogModel(
                id=str(uuid4()),
                session_id=session_id,
                level=level,
                message=message,
                details=details,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(log)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create recovery log: {e}")
