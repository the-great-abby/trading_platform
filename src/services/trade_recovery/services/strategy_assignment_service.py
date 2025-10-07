"""
StrategyAssignmentService for trade recovery system
Handles strategy assignment operations for recovered trades
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from ..models.strategy_assignment import (
    StrategyAssignment, StrategyAssignmentCreate, StrategyAssignmentUpdate,
    StrategyAssignmentResponse, AssignmentStatus
)
from ..models.active_trade import ActiveTrade
from ..models.recovery_session import RecoverySession
from ..models.recovery_log import RecoveryLog, LogAction, LogSeverity

logger = logging.getLogger(__name__)


class StrategyAssignmentService:
    """Service for managing strategy assignments"""
    
    def __init__(self, db_session_factory=None):
        """
        Initialize StrategyAssignmentService
        
        Args:
            db_session_factory: Database session factory
        """
        self.db_session_factory = db_session_factory
    
    async def assign_strategy_to_trade(self, assignment_data: StrategyAssignmentCreate,
                                     recovery_session: RecoverySession,
                                     active_trade: ActiveTrade) -> StrategyAssignment:
        """
        Assign a strategy to a recovered trade
        
        Args:
            assignment_data: Strategy assignment data
            recovery_session: Recovery session
            active_trade: Active trade to assign strategy to
            
        Returns:
            Created strategy assignment
            
        Raises:
            StrategyAssignmentError: If assignment fails
        """
        try:
            logger.info(f"Assigning strategy {assignment_data.strategy_name} to trade {assignment_data.active_trade_id}")
            
            # Check if trade already has an assignment
            existing_assignment = await self.get_assignment_by_trade_id(assignment_data.active_trade_id)
            if existing_assignment:
                raise StrategyAssignmentError("Trade already has strategy assignment")
            
            # Validate strategy is available
            if not await self._validate_strategy_availability(assignment_data.strategy_name, active_trade):
                raise StrategyAssignmentError(f"Strategy {assignment_data.strategy_name} is not available for this trade")
            
            # Create strategy assignment
            assignment = StrategyAssignment(
                recovery_session_id=assignment_data.recovery_session_id,
                active_trade_id=assignment_data.active_trade_id,
                strategy_name=assignment_data.strategy_name,
                assigned_by=assignment_data.assigned_by,
                confidence_score=assignment_data.confidence_score,
                assignment_reason=assignment_data.assignment_reason,
                status=AssignmentStatus.PENDING,
                strategy_parameters=assignment_data.strategy_parameters
            )
            
            # Store assignment (in a real implementation, this would use the database)
            await self._store_assignment(assignment)
            
            # Update recovery session
            await self._update_recovery_session_progress(recovery_session, active_trade)
            
            # Create recovery log
            await self._create_assignment_log(assignment, recovery_session, active_trade)
            
            logger.info(f"Successfully assigned strategy {assignment_data.strategy_name} to trade {assignment_data.active_trade_id}")
            return assignment
            
        except StrategyAssignmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to assign strategy to trade: {e}")
            raise StrategyAssignmentError(f"Failed to assign strategy: {str(e)}")
    
    async def get_assignment_by_id(self, assignment_id: UUID) -> Optional[StrategyAssignment]:
        """
        Get strategy assignment by ID
        
        Args:
            assignment_id: Assignment ID
            
        Returns:
            Strategy assignment or None if not found
        """
        try:
            # In a real implementation, this would query the database
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            logger.error(f"Failed to get assignment {assignment_id}: {e}")
            return None
    
    async def get_assignment_by_trade_id(self, trade_id: UUID) -> Optional[StrategyAssignment]:
        """
        Get strategy assignment by trade ID
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Strategy assignment or None if not found
        """
        try:
            # In a real implementation, this would query the database
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            logger.error(f"Failed to get assignment for trade {trade_id}: {e}")
            return None
    
    async def get_assignments_by_session(self, session_id: UUID) -> List[StrategyAssignment]:
        """
        Get all strategy assignments for a recovery session
        
        Args:
            session_id: Recovery session ID
            
        Returns:
            List of strategy assignments
        """
        try:
            # In a real implementation, this would query the database
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Failed to get assignments for session {session_id}: {e}")
            return []
    
    async def update_assignment_status(self, assignment_id: UUID, status: AssignmentStatus,
                                     user_id: Optional[str] = None) -> Optional[StrategyAssignment]:
        """
        Update strategy assignment status
        
        Args:
            assignment_id: Assignment ID
            status: New status
            user_id: User making the update
            
        Returns:
            Updated assignment or None if not found
        """
        try:
            logger.info(f"Updating assignment {assignment_id} status to {status}")
            
            # Get existing assignment
            assignment = await self.get_assignment_by_id(assignment_id)
            if not assignment:
                return None
            
            # Validate status transition
            if not self._validate_status_transition(assignment.status, status):
                raise StrategyAssignmentError(f"Invalid status transition from {assignment.status} to {status}")
            
            # Update status
            old_status = assignment.status
            assignment.status = status
            
            # Store updated assignment
            await self._store_assignment(assignment)
            
            # Create log for status change
            await self._create_status_change_log(assignment, old_status, status, user_id)
            
            logger.info(f"Updated assignment {assignment_id} status to {status}")
            return assignment
            
        except StrategyAssignmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to update assignment status: {e}")
            raise StrategyAssignmentError(f"Failed to update assignment status: {str(e)}")
    
    async def cancel_assignment(self, assignment_id: UUID, reason: str,
                              user_id: Optional[str] = None) -> Optional[StrategyAssignment]:
        """
        Cancel a strategy assignment
        
        Args:
            assignment_id: Assignment ID
            reason: Cancellation reason
            user_id: User cancelling the assignment
            
        Returns:
            Cancelled assignment or None if not found
        """
        try:
            logger.info(f"Cancelling assignment {assignment_id}")
            
            assignment = await self.get_assignment_by_id(assignment_id)
            if not assignment:
                return None
            
            if not assignment.can_be_cancelled():
                raise StrategyAssignmentError(f"Assignment {assignment_id} cannot be cancelled in status {assignment.status}")
            
            # Update status to cancelled
            old_status = assignment.status
            assignment.status = AssignmentStatus.CANCELLED
            
            # Store updated assignment
            await self._store_assignment(assignment)
            
            # Create log for cancellation
            await self._create_cancellation_log(assignment, reason, user_id)
            
            logger.info(f"Cancelled assignment {assignment_id}")
            return assignment
            
        except StrategyAssignmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel assignment: {e}")
            raise StrategyAssignmentError(f"Failed to cancel assignment: {str(e)}")
    
    async def get_assignment_summary(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get strategy assignment summary for a session
        
        Args:
            session_id: Recovery session ID
            
        Returns:
            Assignment summary
        """
        try:
            assignments = await self.get_assignments_by_session(session_id)
            
            summary = {
                "total_assignments": len(assignments),
                "pending_assignments": 0,
                "active_assignments": 0,
                "paused_assignments": 0,
                "cancelled_assignments": 0,
                "average_confidence": None
            }
            
            if assignments:
                confidence_scores = [float(a.confidence_score) for a in assignments if a.confidence_score is not None]
                
                for assignment in assignments:
                    if assignment.status == AssignmentStatus.PENDING:
                        summary["pending_assignments"] += 1
                    elif assignment.status == AssignmentStatus.ACTIVE:
                        summary["active_assignments"] += 1
                    elif assignment.status == AssignmentStatus.PAUSED:
                        summary["paused_assignments"] += 1
                    elif assignment.status == AssignmentStatus.CANCELLED:
                        summary["cancelled_assignments"] += 1
                
                if confidence_scores:
                    summary["average_confidence"] = Decimal(str(sum(confidence_scores) / len(confidence_scores)))
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get assignment summary for session {session_id}: {e}")
            return {
                "total_assignments": 0,
                "pending_assignments": 0,
                "active_assignments": 0,
                "paused_assignments": 0,
                "cancelled_assignments": 0,
                "average_confidence": None
            }
    
    async def _validate_strategy_availability(self, strategy_name: str, trade: ActiveTrade) -> bool:
        """Validate that a strategy is available for a trade"""
        try:
            # In a real implementation, this would check against the strategy service
            # For now, return True as placeholder
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate strategy availability: {e}")
            return False
    
    def _validate_status_transition(self, current_status: AssignmentStatus, new_status: AssignmentStatus) -> bool:
        """Validate that a status transition is allowed"""
        valid_transitions = {
            AssignmentStatus.PENDING: [AssignmentStatus.ACTIVE, AssignmentStatus.CANCELLED],
            AssignmentStatus.ACTIVE: [AssignmentStatus.PAUSED, AssignmentStatus.CANCELLED],
            AssignmentStatus.PAUSED: [AssignmentStatus.ACTIVE, AssignmentStatus.CANCELLED],
            AssignmentStatus.CANCELLED: []  # No transitions from cancelled
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    async def _store_assignment(self, assignment: StrategyAssignment):
        """Store assignment (placeholder for database storage)"""
        try:
            # In a real implementation, this would store in the database
            logger.debug(f"Storing assignment {assignment.id}")
            pass
            
        except Exception as e:
            logger.error(f"Failed to store assignment: {e}")
            raise StrategyAssignmentError(f"Failed to store assignment: {str(e)}")
    
    async def _update_recovery_session_progress(self, session: RecoverySession, trade: ActiveTrade):
        """Update recovery session progress"""
        try:
            # In a real implementation, this would update the session in the database
            logger.debug(f"Updating session progress for trade {trade.id}")
            pass
            
        except Exception as e:
            logger.error(f"Failed to update session progress: {e}")
    
    async def _create_assignment_log(self, assignment: StrategyAssignment, session: RecoverySession, trade: ActiveTrade):
        """Create log entry for strategy assignment"""
        try:
            # In a real implementation, this would create a recovery log
            logger.debug(f"Creating assignment log for {assignment.id}")
            pass
            
        except Exception as e:
            logger.error(f"Failed to create assignment log: {e}")
    
    async def _create_status_change_log(self, assignment: StrategyAssignment, old_status: AssignmentStatus,
                                      new_status: AssignmentStatus, user_id: Optional[str]):
        """Create log entry for status change"""
        try:
            # In a real implementation, this would create a recovery log
            logger.debug(f"Creating status change log for {assignment.id}")
            pass
            
        except Exception as e:
            logger.error(f"Failed to create status change log: {e}")
    
    async def _create_cancellation_log(self, assignment: StrategyAssignment, reason: str, user_id: Optional[str]):
        """Create log entry for assignment cancellation"""
        try:
            # In a real implementation, this would create a recovery log
            logger.debug(f"Creating cancellation log for {assignment.id}")
            pass
            
        except Exception as e:
            logger.error(f"Failed to create cancellation log: {e}")


class StrategyAssignmentError(Exception):
    """Exception raised when strategy assignment operations fail"""
    pass


















