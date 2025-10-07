"""
RecoverySessionService for trade recovery system
Handles recovery session state management and operations
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import redis.asyncio as redis
import json

from ..models.recovery_session import (
    RecoverySession, RecoverySessionCreate, RecoverySessionUpdate, 
    RecoverySessionResponse, RecoverySessionStatus, RecoveryProgress,
    SessionStatus, RecoveryType
)
from ..models.recovery_log import RecoveryLog, LogAction, LogSeverity

logger = logging.getLogger(__name__)


class RecoverySessionService:
    """Service for managing recovery sessions"""
    
    def __init__(self, redis_url: str, db_session_factory=None):
        """
        Initialize RecoverySessionService
        
        Args:
            redis_url: Redis connection URL for session state
            db_session_factory: Database session factory
        """
        self.redis_url = redis_url
        self.db_session_factory = db_session_factory
        self.redis_client = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RecoverySessionError(f"Failed to connect to Redis: {str(e)}")
    
    async def create_recovery_session(self, session_data: RecoverySessionCreate, 
                                    user_id: Optional[str] = None) -> RecoverySession:
        """
        Create a new recovery session
        
        Args:
            session_data: Recovery session creation data
            user_id: User creating the session
            
        Returns:
            Created recovery session
            
        Raises:
            RecoverySessionError: If session creation fails
        """
        try:
            logger.info(f"Creating recovery session for account {session_data.account_id}")
            
            # Check if there's already an active session for this account
            existing_session = await self.get_active_session(session_data.account_id)
            if existing_session:
                raise RecoverySessionError("Active recovery session already exists for account")
            
            # Create new session
            session = RecoverySession(
                account_id=session_data.account_id,
                recovery_type=session_data.recovery_type,
                description=session_data.description,
                status=SessionStatus.IN_PROGRESS
            )
            
            # Store in Redis
            await self._store_session_in_redis(session)
            
            # Create recovery log
            await self._create_recovery_log(
                session.id,
                LogAction.SESSION_STARTED,
                {
                    "account_id": session.account_id,
                    "recovery_type": session.recovery_type.value,
                    "description": session.description
                },
                user_id
            )
            
            logger.info(f"Created recovery session {session.id} for account {session.account_id}")
            return session
            
        except RecoverySessionError:
            raise
        except Exception as e:
            logger.error(f"Failed to create recovery session: {e}")
            raise RecoverySessionError(f"Failed to create recovery session: {str(e)}")
    
    async def get_recovery_session(self, session_id: UUID) -> Optional[RecoverySession]:
        """
        Get a recovery session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Recovery session or None if not found
        """
        try:
            session_data = await self.redis_client.get(f"recovery_session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                return RecoverySession(**data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get recovery session {session_id}: {e}")
            return None
    
    async def get_active_session(self, account_id: str) -> Optional[RecoverySession]:
        """
        Get active recovery session for an account
        
        Args:
            account_id: Account ID
            
        Returns:
            Active recovery session or None
        """
        try:
            # Get all sessions for account
            sessions = await self.list_recovery_sessions(account_id, status=SessionStatus.IN_PROGRESS)
            return sessions[0] if sessions else None
            
        except Exception as e:
            logger.error(f"Failed to get active session for account {account_id}: {e}")
            return None
    
    async def list_recovery_sessions(self, account_id: str, status: Optional[SessionStatus] = None, 
                                   limit: int = 50) -> List[RecoverySession]:
        """
        List recovery sessions for an account
        
        Args:
            account_id: Account ID
            status: Filter by status
            limit: Maximum number of sessions to return
            
        Returns:
            List of recovery sessions
        """
        try:
            # Get session keys for account
            pattern = f"recovery_session:*"
            keys = await self.redis_client.keys(pattern)
            
            sessions = []
            for key in keys:
                session_data = await self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    session = RecoverySession(**data)
                    
                    # Filter by account and status
                    if session.account_id == account_id:
                        if status is None or session.status == status:
                            sessions.append(session)
            
            # Sort by started_at (newest first) and limit
            sessions.sort(key=lambda x: x.started_at, reverse=True)
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list recovery sessions for account {account_id}: {e}")
            return []
    
    async def update_recovery_session(self, session_id: UUID, update_data: RecoverySessionUpdate,
                                    user_id: Optional[str] = None) -> Optional[RecoverySession]:
        """
        Update a recovery session
        
        Args:
            session_id: Session ID
            update_data: Update data
            user_id: User making the update
            
        Returns:
            Updated recovery session or None if not found
        """
        try:
            logger.info(f"Updating recovery session {session_id}")
            
            # Get existing session
            session = await self.get_recovery_session(session_id)
            if not session:
                return None
            
            # Update fields
            if update_data.status is not None:
                old_status = session.status
                session.status = update_data.status
                
                # Set completed_at if status is COMPLETED
                if update_data.status == SessionStatus.COMPLETED:
                    session.completed_at = datetime.utcnow()
                
                # Create log for status change
                await self._create_recovery_log(
                    session_id,
                    LogAction.SESSION_COMPLETED if update_data.status == SessionStatus.COMPLETED else LogAction.ERROR_OCCURRED,
                    {
                        "old_status": old_status.value,
                        "new_status": update_data.status.value,
                        "completed_at": session.completed_at.isoformat() if session.completed_at else None
                    },
                    user_id
                )
            
            if update_data.error_message is not None:
                session.error_message = update_data.error_message
                
                # Create log for error
                await self._create_recovery_log(
                    session_id,
                    LogAction.ERROR_OCCURRED,
                    {"error_message": update_data.error_message},
                    user_id,
                    severity=LogSeverity.ERROR
                )
            
            if update_data.total_trades_detected is not None:
                session.total_trades_detected = update_data.total_trades_detected
            
            if update_data.trades_processed is not None:
                session.trades_processed = update_data.trades_processed
            
            if update_data.trades_assigned is not None:
                session.trades_assigned = update_data.trades_assigned
            
            if update_data.completed_at is not None:
                session.completed_at = update_data.completed_at
            
            # Store updated session
            await self._store_session_in_redis(session)
            
            logger.info(f"Updated recovery session {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to update recovery session {session_id}: {e}")
            raise RecoverySessionError(f"Failed to update recovery session: {str(e)}")
    
    async def get_recovery_session_status(self, session_id: UUID) -> Optional[RecoverySessionStatus]:
        """
        Get recovery session status with progress details
        
        Args:
            session_id: Session ID
            
        Returns:
            Recovery session status or None if not found
        """
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
    
    async def _store_session_in_redis(self, session: RecoverySession):
        """Store session in Redis"""
        try:
            key = f"recovery_session:{session.id}"
            data = session.dict()
            await self.redis_client.set(key, json.dumps(data, default=str))
            
            # Set expiration (24 hours)
            await self.redis_client.expire(key, 86400)
            
        except Exception as e:
            logger.error(f"Failed to store session in Redis: {e}")
            raise RecoverySessionError(f"Failed to store session: {str(e)}")
    
    async def _create_recovery_log(self, session_id: UUID, action: LogAction, 
                                 details: Dict[str, Any], user_id: Optional[str] = None,
                                 severity: LogSeverity = LogSeverity.INFO):
        """Create a recovery log entry"""
        try:
            log = RecoveryLog(
                recovery_session_id=session_id,
                action=action,
                details=details,
                user_id=user_id,
                severity=severity
            )
            
            # Store log in Redis
            log_key = f"recovery_log:{log.id}"
            log_data = log.dict()
            await self.redis_client.set(log_key, json.dumps(log_data, default=str))
            
            # Add to session logs list
            session_logs_key = f"recovery_session_logs:{session_id}"
            await self.redis_client.lpush(session_logs_key, str(log.id))
            
        except Exception as e:
            logger.error(f"Failed to create recovery log: {e}")
    
    async def get_recovery_logs(self, session_id: UUID, limit: int = 100) -> List[RecoveryLog]:
        """Get recovery logs for a session"""
        try:
            session_logs_key = f"recovery_session_logs:{session_id}"
            log_ids = await self.redis_client.lrange(session_logs_key, 0, limit - 1)
            
            logs = []
            for log_id in log_ids:
                log_data = await self.redis_client.get(f"recovery_log:{log_id.decode()}")
                if log_data:
                    data = json.loads(log_data)
                    logs.append(RecoveryLog(**data))
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get recovery logs for session {session_id}: {e}")
            return []
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


class RecoverySessionError(Exception):
    """Exception raised when recovery session operations fail"""
    pass


















