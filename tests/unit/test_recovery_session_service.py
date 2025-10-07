"""
Unit tests for RecoverySessionService
Tests the RecoverySessionService functionality and session management
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4

from src.services.trade_recovery.services.recovery_session_service import (
    RecoverySessionService, RecoverySessionError
)
from src.services.trade_recovery.models.recovery_session import (
    RecoverySession, RecoverySessionCreate, RecoverySessionUpdate,
    SessionStatus, RecoveryType
)
from src.services.trade_recovery.models.recovery_log import (
    RecoveryLog, LogAction, LogSeverity
)


class TestRecoverySessionService:
    """Test cases for RecoverySessionService"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def recovery_session_service(self, mock_redis_client):
        """Create RecoverySessionService instance with mocked dependencies"""
        service = RecoverySessionService(
            redis_url="redis://test-redis:6379",
            db_session_factory=None
        )
        service.redis_client = mock_redis_client
        return service
    
    @pytest.fixture
    def sample_session_create(self):
        """Create a sample RecoverySessionCreate for testing"""
        return RecoverySessionCreate(
            account_id="acc_123",
            user_id="user_456",
            recovery_type=RecoveryType.DATABASE_FAILURE,
            description="Test recovery session"
        )
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample RecoverySession for testing"""
        return RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            user_id="user_456",
            status=SessionStatus.IN_PROGRESS,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            description="Test recovery session",
            total_trades_detected=5,
            trades_processed=3,
            trades_assigned=2,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_recovery_session_service_initialization(self):
        """Test RecoverySessionService initialization"""
        service = RecoverySessionService(
            redis_url="redis://test-redis:6379",
            db_session_factory=None
        )
        
        assert service.redis_url == "redis://test-redis:6379"
        assert service.db_session_factory is None
        assert service.redis_client is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, recovery_session_service):
        """Test successful Redis initialization"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.ping = AsyncMock(return_value=True)
        
        await recovery_session_service.initialize()
        
        recovery_session_service.redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_redis_error(self, recovery_session_service):
        """Test Redis initialization with connection error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(RecoverySessionError) as exc_info:
            await recovery_session_service.initialize()
        
        assert "Failed to connect to Redis" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_recovery_session_success(self, recovery_session_service, sample_session_create):
        """Test successful recovery session creation"""
        # Mock Redis operations
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=None)  # No existing session
        recovery_session_service.redis_client.set = AsyncMock(return_value=True)
        recovery_session_service.redis_client.expire = AsyncMock(return_value=True)
        recovery_session_service.redis_client.lpush = AsyncMock(return_value=True)
        
        session = await recovery_session_service.create_recovery_session(sample_session_create, "user_456")
        
        assert session is not None
        assert session.account_id == "acc_123"
        assert session.user_id == "user_456"
        assert session.recovery_type == RecoveryType.DATABASE_FAILURE
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.description == "Test recovery session"
    
    @pytest.mark.asyncio
    async def test_create_recovery_session_existing_active_session(self, recovery_session_service, sample_session_create):
        """Test recovery session creation with existing active session"""
        # Mock existing active session
        existing_session_data = {
            "id": str(uuid4()),
            "account_id": "acc_123",
            "status": SessionStatus.IN_PROGRESS.value,
            "recovery_type": RecoveryType.DATABASE_FAILURE.value
        }
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(existing_session_data))
        
        with pytest.raises(RecoverySessionError) as exc_info:
            await recovery_session_service.create_recovery_session(sample_session_create, "user_456")
        
        assert "Active recovery session already exists for account" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_recovery_session_creation_error(self, recovery_session_service, sample_session_create):
        """Test recovery session creation with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=None)
        recovery_session_service.redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        with pytest.raises(RecoverySessionError) as exc_info:
            await recovery_session_service.create_recovery_session(sample_session_create, "user_456")
        
        assert "Failed to create recovery session" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_recovery_session_success(self, recovery_session_service, sample_session):
        """Test successful recovery session retrieval"""
        session_data = sample_session.dict()
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        
        session = await recovery_session_service.get_recovery_session(sample_session.id)
        
        assert session is not None
        assert session.id == sample_session.id
        assert session.account_id == "acc_123"
        assert session.status == SessionStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_get_recovery_session_not_found(self, recovery_session_service):
        """Test recovery session retrieval when not found"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=None)
        
        session = await recovery_session_service.get_recovery_session(str(uuid4()))
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_recovery_session_error(self, recovery_session_service):
        """Test recovery session retrieval with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        session = await recovery_session_service.get_recovery_session(str(uuid4()))
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_active_session_success(self, recovery_session_service, sample_session):
        """Test successful active session retrieval"""
        session_data = sample_session.dict()
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.keys = AsyncMock(return_value=[f"recovery_session:{sample_session.id}"])
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        
        session = await recovery_session_service.get_active_session("acc_123")
        
        assert session is not None
        assert session.id == sample_session.id
        assert session.account_id == "acc_123"
        assert session.status == SessionStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_get_active_session_not_found(self, recovery_session_service):
        """Test active session retrieval when not found"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.keys = AsyncMock(return_value=[])
        
        session = await recovery_session_service.get_active_session("acc_123")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_list_recovery_sessions_success(self, recovery_session_service, sample_session):
        """Test successful recovery sessions listing"""
        session_data = sample_session.dict()
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.keys = AsyncMock(return_value=[f"recovery_session:{sample_session.id}"])
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        
        sessions = await recovery_session_service.list_recovery_sessions("acc_123")
        
        assert len(sessions) == 1
        assert sessions[0].id == sample_session.id
        assert sessions[0].account_id == "acc_123"
    
    @pytest.mark.asyncio
    async def test_list_recovery_sessions_with_status_filter(self, recovery_session_service, sample_session):
        """Test recovery sessions listing with status filter"""
        session_data = sample_session.dict()
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.keys = AsyncMock(return_value=[f"recovery_session:{sample_session.id}"])
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        
        sessions = await recovery_session_service.list_recovery_sessions("acc_123", SessionStatus.IN_PROGRESS)
        
        assert len(sessions) == 1
        assert sessions[0].status == SessionStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_list_recovery_sessions_error(self, recovery_session_service):
        """Test recovery sessions listing with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.keys = AsyncMock(side_effect=Exception("Redis error"))
        
        sessions = await recovery_session_service.list_recovery_sessions("acc_123")
        
        assert len(sessions) == 0
    
    @pytest.mark.asyncio
    async def test_update_recovery_session_success(self, recovery_session_service, sample_session):
        """Test successful recovery session update"""
        session_data = sample_session.dict()
        update_data = RecoverySessionUpdate(
            status=SessionStatus.COMPLETED,
            total_trades_detected=10,
            trades_processed=8,
            trades_assigned=6
        )
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        recovery_session_service.redis_client.set = AsyncMock(return_value=True)
        recovery_session_service.redis_client.expire = AsyncMock(return_value=True)
        recovery_session_service.redis_client.lpush = AsyncMock(return_value=True)
        
        updated_session = await recovery_session_service.update_recovery_session(
            sample_session.id, update_data, "user_456"
        )
        
        assert updated_session is not None
        assert updated_session.status == SessionStatus.COMPLETED
        assert updated_session.total_trades_detected == 10
        assert updated_session.trades_processed == 8
        assert updated_session.trades_assigned == 6
    
    @pytest.mark.asyncio
    async def test_update_recovery_session_not_found(self, recovery_session_service):
        """Test recovery session update when session not found"""
        update_data = RecoverySessionUpdate(status=SessionStatus.COMPLETED)
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=None)
        
        updated_session = await recovery_session_service.update_recovery_session(
            str(uuid4()), update_data, "user_456"
        )
        
        assert updated_session is None
    
    @pytest.mark.asyncio
    async def test_update_recovery_session_error(self, recovery_session_service, sample_session):
        """Test recovery session update with error"""
        session_data = sample_session.dict()
        update_data = RecoverySessionUpdate(status=SessionStatus.COMPLETED)
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        recovery_session_service.redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        with pytest.raises(RecoverySessionError) as exc_info:
            await recovery_session_service.update_recovery_session(
                sample_session.id, update_data, "user_456"
            )
        
        assert "Failed to update recovery session" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_recovery_session_status_success(self, recovery_session_service, sample_session):
        """Test successful recovery session status retrieval"""
        session_data = sample_session.dict()
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(session_data))
        
        status = await recovery_session_service.get_recovery_session_status(sample_session.id)
        
        assert status is not None
        assert status.session_id == sample_session.id
        assert status.status == SessionStatus.IN_PROGRESS
        assert status.progress is not None
        assert status.progress.total_trades_detected == 5
        assert status.progress.trades_processed == 3
        assert status.progress.trades_assigned == 2
    
    @pytest.mark.asyncio
    async def test_get_recovery_session_status_not_found(self, recovery_session_service):
        """Test recovery session status retrieval when session not found"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.get = AsyncMock(return_value=None)
        
        status = await recovery_session_service.get_recovery_session_status(str(uuid4()))
        
        assert status is None
    
    @pytest.mark.asyncio
    async def test_get_recovery_logs_success(self, recovery_session_service):
        """Test successful recovery logs retrieval"""
        log_data = {
            "id": str(uuid4()),
            "recovery_session_id": str(uuid4()),
            "action": LogAction.SESSION_STARTED.value,
            "details": {"test": "data"},
            "user_id": "user_456",
            "severity": LogSeverity.INFO.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.lrange = AsyncMock(return_value=[str(uuid4())])
        recovery_session_service.redis_client.get = AsyncMock(return_value=str(log_data))
        
        logs = await recovery_session_service.get_recovery_logs(str(uuid4()))
        
        assert len(logs) == 1
        assert logs[0].action == LogAction.SESSION_STARTED
        assert logs[0].details == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_get_recovery_logs_error(self, recovery_session_service):
        """Test recovery logs retrieval with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.lrange = AsyncMock(side_effect=Exception("Redis error"))
        
        logs = await recovery_session_service.get_recovery_logs(str(uuid4()))
        
        assert len(logs) == 0
    
    @pytest.mark.asyncio
    async def test_store_session_in_redis_success(self, recovery_session_service, sample_session):
        """Test successful session storage in Redis"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.set = AsyncMock(return_value=True)
        recovery_session_service.redis_client.expire = AsyncMock(return_value=True)
        
        await recovery_session_service._store_session_in_redis(sample_session)
        
        recovery_session_service.redis_client.set.assert_called_once()
        recovery_session_service.redis_client.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_session_in_redis_error(self, recovery_session_service, sample_session):
        """Test session storage in Redis with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        with pytest.raises(RecoverySessionError) as exc_info:
            await recovery_session_service._store_session_in_redis(sample_session)
        
        assert "Failed to store session" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_recovery_log_success(self, recovery_session_service):
        """Test successful recovery log creation"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.set = AsyncMock(return_value=True)
        recovery_session_service.redis_client.lpush = AsyncMock(return_value=True)
        
        log = await recovery_session_service._create_recovery_log(
            str(uuid4()),
            LogAction.SESSION_STARTED,
            {"test": "data"},
            "user_456",
            LogSeverity.INFO
        )
        
        assert log is not None
        assert log.action == LogAction.SESSION_STARTED
        assert log.details == {"test": "data"}
        assert log.user_id == "user_456"
        assert log.severity == LogSeverity.INFO
    
    @pytest.mark.asyncio
    async def test_create_recovery_log_error(self, recovery_session_service):
        """Test recovery log creation with error"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        # Should not raise exception, just log error
        log = await recovery_session_service._create_recovery_log(
            str(uuid4()),
            LogAction.SESSION_STARTED,
            {"test": "data"},
            "user_456",
            LogSeverity.INFO
        )
        
        assert log is not None
    
    @pytest.mark.asyncio
    async def test_close_success(self, recovery_session_service):
        """Test successful Redis client closure"""
        recovery_session_service.redis_client = AsyncMock()
        recovery_session_service.redis_client.close = AsyncMock(return_value=None)
        
        await recovery_session_service.close()
        
        recovery_session_service.redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_no_client(self, recovery_session_service):
        """Test closure when no Redis client exists"""
        recovery_session_service.redis_client = None
        
        # Should not raise exception
        await recovery_session_service.close()


class TestRecoverySessionError:
    """Test cases for RecoverySessionError exception"""
    
    def test_recovery_session_error_creation(self):
        """Test RecoverySessionError creation"""
        error = RecoverySessionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


















