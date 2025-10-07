"""
Database Client Integration
Connects all services to PostgreSQL database using SQLAlchemy
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select, update, delete, func
import uuid

from ...utils.trading_config import get_trade_recovery_config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class ActiveTradeModel(Base):
    """Database model for active trades"""
    __tablename__ = "active_trades"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)  # 'buy' or 'sell'
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecoverySessionModel(Base):
    """Database model for recovery sessions"""
    __tablename__ = "recovery_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    recovery_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_trades_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trades_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trades_assigned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyAssignmentModel(Base):
    """Database model for strategy assignments"""
    __tablename__ = "strategy_assignments"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("recovery_sessions.id"), nullable=False, index=True)
    trade_id: Mapped[str] = mapped_column(String, ForeignKey("active_trades.id"), nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    assignment_reason: Mapped[str] = mapped_column(Text, nullable=False)
    auto_assigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecoveryLogModel(Base):
    """Database model for recovery logs"""
    __tablename__ = "recovery_logs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("recovery_sessions.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String, nullable=False)  # 'info', 'warning', 'error', 'debug'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DatabaseClient:
    """Database client for trade recovery services"""
    
    def __init__(self):
        """Initialize database client"""
        self.config = get_trade_recovery_config()
        self.db_config = self.config['database']
        
        self.engine = None
        self.session_factory = None
        self.connected = False
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.db_config['url'],
                pool_size=self.db_config['pool_size'],
                max_overflow=self.db_config['max_overflow'],
                pool_timeout=self.db_config['pool_timeout'],
                pool_recycle=self.db_config['pool_recycle'],
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.session_factory() as session:
                await session.execute(select(1))
            
            self.connected = True
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self.connected:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Active Trade Operations
    async def create_active_trade(self, trade_data: Dict[str, Any]) -> str:
        """Create active trade record"""
        trade_id = str(uuid.uuid4())
        
        async with self.get_session() as session:
            trade = ActiveTradeModel(
                id=trade_id,
                account_id=trade_data['account_id'],
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                quantity=trade_data['quantity'],
                entry_price=trade_data['entry_price'],
                current_price=trade_data.get('current_price'),
                unrealized_pnl=trade_data.get('unrealized_pnl'),
                entry_time=trade_data['entry_time'],
                detected_at=trade_data.get('detected_at', datetime.utcnow()),
                metadata=trade_data.get('metadata')
            )
            
            session.add(trade)
            await session.commit()
            
            logger.debug(f"Created active trade {trade_id}")
            return trade_id
    
    async def get_active_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get active trade by ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(ActiveTradeModel).where(ActiveTradeModel.id == trade_id)
            )
            trade = result.scalar_one_or_none()
            
            if trade:
                return {
                    'id': trade.id,
                    'account_id': trade.account_id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'current_price': trade.current_price,
                    'unrealized_pnl': trade.unrealized_pnl,
                    'entry_time': trade.entry_time,
                    'detected_at': trade.detected_at,
                    'metadata': trade.metadata,
                    'created_at': trade.created_at,
                    'updated_at': trade.updated_at
                }
            return None
    
    async def list_active_trades(self, account_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List active trades for an account"""
        async with self.get_session() as session:
            result = await session.execute(
                select(ActiveTradeModel)
                .where(ActiveTradeModel.account_id == account_id)
                .order_by(ActiveTradeModel.detected_at.desc())
                .limit(limit)
            )
            trades = result.scalars().all()
            
            return [
                {
                    'id': trade.id,
                    'account_id': trade.account_id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'current_price': trade.current_price,
                    'unrealized_pnl': trade.unrealized_pnl,
                    'entry_time': trade.entry_time,
                    'detected_at': trade.detected_at,
                    'metadata': trade.metadata,
                    'created_at': trade.created_at,
                    'updated_at': trade.updated_at
                }
                for trade in trades
            ]
    
    async def update_active_trade(self, trade_id: str, update_data: Dict[str, Any]) -> bool:
        """Update active trade"""
        async with self.get_session() as session:
            result = await session.execute(
                update(ActiveTradeModel)
                .where(ActiveTradeModel.id == trade_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            
            return result.rowcount > 0
    
    async def delete_active_trade(self, trade_id: str) -> bool:
        """Delete active trade"""
        async with self.get_session() as session:
            result = await session.execute(
                delete(ActiveTradeModel).where(ActiveTradeModel.id == trade_id)
            )
            
            return result.rowcount > 0
    
    # Recovery Session Operations
    async def create_recovery_session(self, session_data: Dict[str, Any]) -> str:
        """Create recovery session record"""
        session_id = str(uuid.uuid4())
        
        async with self.get_session() as session:
            recovery_session = RecoverySessionModel(
                id=session_id,
                account_id=session_data['account_id'],
                user_id=session_data.get('user_id'),
                status=session_data.get('status', 'active'),
                recovery_type=session_data['recovery_type'],
                description=session_data.get('description'),
                total_trades_detected=session_data.get('total_trades_detected', 0),
                trades_processed=session_data.get('trades_processed', 0),
                trades_assigned=session_data.get('trades_assigned', 0),
                started_at=session_data.get('started_at', datetime.utcnow())
            )
            
            session.add(recovery_session)
            await session.commit()
            
            logger.debug(f"Created recovery session {session_id}")
            return session_id
    
    async def get_recovery_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get recovery session by ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(RecoverySessionModel).where(RecoverySessionModel.id == session_id)
            )
            recovery_session = result.scalar_one_or_none()
            
            if recovery_session:
                return {
                    'id': recovery_session.id,
                    'account_id': recovery_session.account_id,
                    'user_id': recovery_session.user_id,
                    'status': recovery_session.status,
                    'recovery_type': recovery_session.recovery_type,
                    'description': recovery_session.description,
                    'total_trades_detected': recovery_session.total_trades_detected,
                    'trades_processed': recovery_session.trades_processed,
                    'trades_assigned': recovery_session.trades_assigned,
                    'started_at': recovery_session.started_at,
                    'completed_at': recovery_session.completed_at,
                    'cancelled_at': recovery_session.cancelled_at,
                    'cancellation_reason': recovery_session.cancellation_reason,
                    'error_message': recovery_session.error_message,
                    'summary': recovery_session.summary,
                    'created_at': recovery_session.created_at,
                    'updated_at': recovery_session.updated_at
                }
            return None
    
    async def update_recovery_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update recovery session"""
        async with self.get_session() as session:
            result = await session.execute(
                update(RecoverySessionModel)
                .where(RecoverySessionModel.id == session_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            
            return result.rowcount > 0
    
    async def list_recovery_sessions(self, account_id: str, status: Optional[str] = None, 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """List recovery sessions for an account"""
        async with self.get_session() as session:
            query = select(RecoverySessionModel).where(RecoverySessionModel.account_id == account_id)
            
            if status:
                query = query.where(RecoverySessionModel.status == status)
            
            result = await session.execute(
                query.order_by(RecoverySessionModel.started_at.desc()).limit(limit)
            )
            sessions = result.scalars().all()
            
            return [
                {
                    'id': session.id,
                    'account_id': session.account_id,
                    'user_id': session.user_id,
                    'status': session.status,
                    'recovery_type': session.recovery_type,
                    'description': session.description,
                    'total_trades_detected': session.total_trades_detected,
                    'trades_processed': session.trades_processed,
                    'trades_assigned': session.trades_assigned,
                    'started_at': session.started_at,
                    'completed_at': session.completed_at,
                    'cancelled_at': session.cancelled_at,
                    'cancellation_reason': session.cancellation_reason,
                    'error_message': session.error_message,
                    'summary': session.summary,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at
                }
                for session in sessions
            ]
    
    # Strategy Assignment Operations
    async def create_strategy_assignment(self, assignment_data: Dict[str, Any]) -> str:
        """Create strategy assignment record"""
        assignment_id = str(uuid.uuid4())
        
        async with self.get_session() as session:
            assignment = StrategyAssignmentModel(
                id=assignment_id,
                session_id=assignment_data['session_id'],
                trade_id=assignment_data['trade_id'],
                strategy_id=assignment_data['strategy_id'],
                strategy_name=assignment_data['strategy_name'],
                confidence_score=assignment_data['confidence_score'],
                assignment_reason=assignment_data['assignment_reason'],
                auto_assigned=assignment_data.get('auto_assigned', False),
                user_confirmed=assignment_data.get('user_confirmed')
            )
            
            session.add(assignment)
            await session.commit()
            
            logger.debug(f"Created strategy assignment {assignment_id}")
            return assignment_id
    
    async def get_strategy_assignments(self, session_id: str) -> List[Dict[str, Any]]:
        """Get strategy assignments for a session"""
        async with self.get_session() as session:
            result = await session.execute(
                select(StrategyAssignmentModel)
                .where(StrategyAssignmentModel.session_id == session_id)
                .order_by(StrategyAssignmentModel.assigned_at.desc())
            )
            assignments = result.scalars().all()
            
            return [
                {
                    'id': assignment.id,
                    'session_id': assignment.session_id,
                    'trade_id': assignment.trade_id,
                    'strategy_id': assignment.strategy_id,
                    'strategy_name': assignment.strategy_name,
                    'confidence_score': assignment.confidence_score,
                    'assignment_reason': assignment.assignment_reason,
                    'auto_assigned': assignment.auto_assigned,
                    'user_confirmed': assignment.user_confirmed,
                    'assigned_at': assignment.assigned_at,
                    'created_at': assignment.created_at,
                    'updated_at': assignment.updated_at
                }
                for assignment in assignments
            ]
    
    # Recovery Log Operations
    async def create_recovery_log(self, log_data: Dict[str, Any]) -> str:
        """Create recovery log record"""
        log_id = str(uuid.uuid4())
        
        async with self.get_session() as session:
            log = RecoveryLogModel(
                id=log_id,
                session_id=log_data['session_id'],
                level=log_data['level'],
                message=log_data['message'],
                details=log_data.get('details'),
                timestamp=log_data.get('timestamp', datetime.utcnow())
            )
            
            session.add(log)
            await session.commit()
            
            logger.debug(f"Created recovery log {log_id}")
            return log_id
    
    async def get_recovery_logs(self, session_id: str, level: Optional[str] = None, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get recovery logs for a session"""
        async with self.get_session() as session:
            query = select(RecoveryLogModel).where(RecoveryLogModel.session_id == session_id)
            
            if level:
                query = query.where(RecoveryLogModel.level == level)
            
            result = await session.execute(
                query.order_by(RecoveryLogModel.timestamp.desc()).limit(limit)
            )
            logs = result.scalars().all()
            
            return [
                {
                    'id': log.id,
                    'session_id': log.session_id,
                    'level': log.level,
                    'message': log.message,
                    'details': log.details,
                    'timestamp': log.timestamp,
                    'created_at': log.created_at
                }
                for log in logs
            ]
    
    # Statistics and Analytics
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a recovery session"""
        async with self.get_session() as session:
            # Get session info
            session_result = await session.execute(
                select(RecoverySessionModel).where(RecoverySessionModel.id == session_id)
            )
            recovery_session = session_result.scalar_one_or_none()
            
            if not recovery_session:
                return {}
            
            # Count assignments
            assignments_result = await session.execute(
                select(func.count(StrategyAssignmentModel.id))
                .where(StrategyAssignmentModel.session_id == session_id)
            )
            total_assignments = assignments_result.scalar() or 0
            
            # Count logs by level
            logs_result = await session.execute(
                select(RecoveryLogModel.level, func.count(RecoveryLogModel.id))
                .where(RecoveryLogModel.session_id == session_id)
                .group_by(RecoveryLogModel.level)
            )
            log_counts = {row[0]: row[1] for row in logs_result}
            
            return {
                'session_id': session_id,
                'status': recovery_session.status,
                'total_trades_detected': recovery_session.total_trades_detected,
                'trades_processed': recovery_session.trades_processed,
                'trades_assigned': recovery_session.trades_assigned,
                'total_assignments': total_assignments,
                'log_counts': log_counts,
                'started_at': recovery_session.started_at.isoformat(),
                'completed_at': recovery_session.completed_at.isoformat() if recovery_session.completed_at else None,
                'cancelled_at': recovery_session.cancelled_at.isoformat() if recovery_session.cancelled_at else None
            }
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleaned = {'sessions': 0, 'trades': 0, 'logs': 0}
        
        async with self.get_session() as session:
            # Clean up old completed sessions
            sessions_result = await session.execute(
                delete(RecoverySessionModel)
                .where(RecoverySessionModel.status.in_(['completed', 'cancelled']))
                .where(RecoverySessionModel.updated_at < cutoff_date)
            )
            cleaned['sessions'] = sessions_result.rowcount
            
            # Clean up old trades
            trades_result = await session.execute(
                delete(ActiveTradeModel)
                .where(ActiveTradeModel.detected_at < cutoff_date)
            )
            cleaned['trades'] = trades_result.rowcount
            
            # Clean up old logs
            logs_result = await session.execute(
                delete(RecoveryLogModel)
                .where(RecoveryLogModel.timestamp < cutoff_date)
            )
            cleaned['logs'] = logs_result.rowcount
        
        logger.info(f"Cleaned up old data: {cleaned}")
        return cleaned
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self.connected = False
            logger.info("Database connection closed")


















