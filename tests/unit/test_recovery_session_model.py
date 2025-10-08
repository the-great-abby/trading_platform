"""
Unit tests for RecoverySession model
Tests the RecoverySession Pydantic model validation and behavior
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

from src.services.trade_recovery.models.recovery_session import (
    RecoverySession, RecoverySessionCreate, RecoverySessionUpdate,
    RecoverySessionResponse, RecoverySessionStatus, RecoveryProgress,
    SessionStatus, RecoveryType
)


class TestRecoverySessionModel:
    """Test cases for RecoverySession model"""
    
    def test_recovery_session_creation_valid_data(self):
        """Test creating RecoverySession with valid data"""
        session_data = {
            "id": str(uuid4()),
            "account_id": "acc_123",
            "user_id": "user_456",
            "status": SessionStatus.IN_PROGRESS,
            "recovery_type": RecoveryType.DATABASE_FAILURE,
            "description": "Test recovery session",
            "total_trades_detected": 5,
            "trades_processed": 3,
            "trades_assigned": 2,
            "started_at": datetime(2024, 1, 15, 10, 30, 0),
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
            "updated_at": datetime(2024, 1, 15, 10, 30, 0)
        }
        
        session = RecoverySession(**session_data)
        
        assert session.id == session_data["id"]
        assert session.account_id == "acc_123"
        assert session.user_id == "user_456"
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.recovery_type == RecoveryType.DATABASE_FAILURE
        assert session.description == "Test recovery session"
        assert session.total_trades_detected == 5
        assert session.trades_processed == 3
        assert session.trades_assigned == 2
        assert session.started_at == datetime(2024, 1, 15, 10, 30, 0)
        assert session.completed_at is None
        assert session.cancelled_at is None
        assert session.cancellation_reason is None
        assert session.error_message is None
        assert session.summary is None
    
    def test_recovery_session_creation_minimal_data(self):
        """Test creating RecoverySession with minimal required data"""
        session_data = {
            "id": str(uuid4()),
            "account_id": "acc_123",
            "status": SessionStatus.IN_PROGRESS,
            "recovery_type": RecoveryType.DATABASE_FAILURE,
            "started_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        session = RecoverySession(**session_data)
        
        assert session.id == session_data["id"]
        assert session.account_id == "acc_123"
        assert session.user_id is None
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.recovery_type == RecoveryType.DATABASE_FAILURE
        assert session.description is None
        assert session.total_trades_detected == 0
        assert session.trades_processed == 0
        assert session.trades_assigned == 0
        assert session.completed_at is None
        assert session.cancelled_at is None
    
    def test_recovery_session_validation_missing_required_fields(self):
        """Test validation fails with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySession(
                account_id="acc_123",
                status=SessionStatus.IN_PROGRESS,
                recovery_type=RecoveryType.DATABASE_FAILURE
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("id",) for error in errors)
        assert any(error["loc"] == ("started_at",) for error in errors)
        assert any(error["loc"] == ("created_at",) for error in errors)
        assert any(error["loc"] == ("updated_at",) for error in errors)
    
    def test_recovery_session_validation_invalid_status(self):
        """Test validation fails with invalid status"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySession(
                id=str(uuid4()),
                account_id="acc_123",
                status="INVALID_STATUS",
                recovery_type=RecoveryType.DATABASE_FAILURE,
                started_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)
    
    def test_recovery_session_validation_invalid_recovery_type(self):
        """Test validation fails with invalid recovery type"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySession(
                id=str(uuid4()),
                account_id="acc_123",
                status=SessionStatus.IN_PROGRESS,
                recovery_type="INVALID_TYPE",
                started_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("recovery_type",) for error in errors)
    
    def test_recovery_session_validation_negative_counts(self):
        """Test validation fails with negative counts"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySession(
                id=str(uuid4()),
                account_id="acc_123",
                status=SessionStatus.IN_PROGRESS,
                recovery_type=RecoveryType.DATABASE_FAILURE,
                total_trades_detected=-1,
                started_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("total_trades_detected",) for error in errors)
    
    def test_recovery_session_calculate_completion_percentage(self):
        """Test calculating completion percentage"""
        session = RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            status=SessionStatus.IN_PROGRESS,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            total_trades_detected=10,
            trades_processed=7,
            trades_assigned=5,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Completion percentage should be based on trades_processed / total_trades_detected
        expected_percentage = (7 / 10) * 100
        assert session.calculate_completion_percentage() == expected_percentage
    
    def test_recovery_session_calculate_completion_percentage_zero_total(self):
        """Test completion percentage when total_trades_detected is zero"""
        session = RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            status=SessionStatus.IN_PROGRESS,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            total_trades_detected=0,
            trades_processed=0,
            trades_assigned=0,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert session.calculate_completion_percentage() == 0.0
    
    def test_recovery_session_calculate_completion_percentage_completed(self):
        """Test completion percentage for completed session"""
        session = RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            status=SessionStatus.COMPLETED,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            total_trades_detected=10,
            trades_processed=10,
            trades_assigned=8,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert session.calculate_completion_percentage() == 100.0
    
    def test_recovery_session_serialization(self):
        """Test RecoverySession serialization to dict"""
        session = RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            status=SessionStatus.IN_PROGRESS,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            description="Test session",
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session_dict = session.dict()
        
        assert isinstance(session_dict, dict)
        assert session_dict["account_id"] == "acc_123"
        assert session_dict["status"] == SessionStatus.IN_PROGRESS
        assert session_dict["recovery_type"] == RecoveryType.DATABASE_FAILURE
        assert session_dict["description"] == "Test session"
    
    def test_recovery_session_json_serialization(self):
        """Test RecoverySession JSON serialization"""
        session = RecoverySession(
            id=str(uuid4()),
            account_id="acc_123",
            status=SessionStatus.IN_PROGRESS,
            recovery_type=RecoveryType.DATABASE_FAILURE,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        json_str = session.json()
        
        assert isinstance(json_str, str)
        assert "acc_123" in json_str
        assert "IN_PROGRESS" in json_str
        assert "DATABASE_FAILURE" in json_str


class TestRecoverySessionCreate:
    """Test cases for RecoverySessionCreate model"""
    
    def test_recovery_session_create_valid_data(self):
        """Test creating RecoverySessionCreate with valid data"""
        create_data = {
            "account_id": "acc_123",
            "user_id": "user_456",
            "recovery_type": RecoveryType.DATABASE_FAILURE,
            "description": "Test recovery session"
        }
        
        session_create = RecoverySessionCreate(**create_data)
        
        assert session_create.account_id == "acc_123"
        assert session_create.user_id == "user_456"
        assert session_create.recovery_type == RecoveryType.DATABASE_FAILURE
        assert session_create.description == "Test recovery session"
    
    def test_recovery_session_create_minimal_data(self):
        """Test creating RecoverySessionCreate with minimal required data"""
        create_data = {
            "account_id": "acc_123",
            "recovery_type": RecoveryType.DATABASE_FAILURE
        }
        
        session_create = RecoverySessionCreate(**create_data)
        
        assert session_create.account_id == "acc_123"
        assert session_create.user_id is None
        assert session_create.recovery_type == RecoveryType.DATABASE_FAILURE
        assert session_create.description is None
    
    def test_recovery_session_create_validation_missing_account_id(self):
        """Test validation fails with missing account_id"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySessionCreate(
                recovery_type=RecoveryType.DATABASE_FAILURE
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("account_id",) for error in errors)
    
    def test_recovery_session_create_validation_missing_recovery_type(self):
        """Test validation fails with missing recovery_type"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySessionCreate(
                account_id="acc_123"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("recovery_type",) for error in errors)


class TestRecoverySessionUpdate:
    """Test cases for RecoverySessionUpdate model"""
    
    def test_recovery_session_update_valid_data(self):
        """Test creating RecoverySessionUpdate with valid data"""
        update_data = {
            "status": SessionStatus.COMPLETED,
            "total_trades_detected": 10,
            "trades_processed": 8,
            "trades_assigned": 6,
            "completed_at": datetime.utcnow(),
            "summary": "Recovery completed successfully"
        }
        
        session_update = RecoverySessionUpdate(**update_data)
        
        assert session_update.status == SessionStatus.COMPLETED
        assert session_update.total_trades_detected == 10
        assert session_update.trades_processed == 8
        assert session_update.trades_assigned == 6
        assert session_update.completed_at is not None
        assert session_update.summary == "Recovery completed successfully"
    
    def test_recovery_session_update_empty_data(self):
        """Test creating RecoverySessionUpdate with empty data"""
        session_update = RecoverySessionUpdate()
        
        assert session_update.status is None
        assert session_update.total_trades_detected is None
        assert session_update.trades_processed is None
        assert session_update.trades_assigned is None
        assert session_update.completed_at is None
        assert session_update.cancelled_at is None
        assert session_update.cancellation_reason is None
        assert session_update.error_message is None
        assert session_update.summary is None
    
    def test_recovery_session_update_validation_negative_counts(self):
        """Test validation fails with negative counts"""
        with pytest.raises(ValidationError) as exc_info:
            RecoverySessionUpdate(
                total_trades_detected=-1
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("total_trades_detected",) for error in errors)


class TestRecoverySessionResponse:
    """Test cases for RecoverySessionResponse model"""
    
    def test_recovery_session_response_creation(self):
        """Test creating RecoverySessionResponse"""
        response_data = {
            "id": str(uuid4()),
            "account_id": "acc_123",
            "status": SessionStatus.IN_PROGRESS,
            "recovery_type": RecoveryType.DATABASE_FAILURE,
            "description": "Test session",
            "total_trades_detected": 5,
            "trades_processed": 3,
            "trades_assigned": 2,
            "started_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = RecoverySessionResponse(**response_data)
        
        assert response.id == response_data["id"]
        assert response.account_id == "acc_123"
        assert response.status == SessionStatus.IN_PROGRESS
        assert response.recovery_type == RecoveryType.DATABASE_FAILURE
        assert response.description == "Test session"
        assert response.total_trades_detected == 5
        assert response.trades_processed == 3
        assert response.trades_assigned == 2


class TestRecoverySessionStatus:
    """Test cases for RecoverySessionStatus model"""
    
    def test_recovery_session_status_creation(self):
        """Test creating RecoverySessionStatus"""
        progress = RecoveryProgress(
            total_trades_detected=10,
            trades_processed=7,
            trades_assigned=5,
            completion_percentage=70.0
        )
        
        status_data = {
            "session_id": str(uuid4()),
            "status": SessionStatus.IN_PROGRESS,
            "progress": progress,
            "last_updated": datetime.utcnow()
        }
        
        session_status = RecoverySessionStatus(**status_data)
        
        assert session_status.session_id == status_data["session_id"]
        assert session_status.status == SessionStatus.IN_PROGRESS
        assert session_status.progress == progress
        assert session_status.last_updated is not None


class TestRecoveryProgress:
    """Test cases for RecoveryProgress model"""
    
    def test_recovery_progress_creation(self):
        """Test creating RecoveryProgress"""
        progress = RecoveryProgress(
            total_trades_detected=10,
            trades_processed=7,
            trades_assigned=5,
            completion_percentage=70.0
        )
        
        assert progress.total_trades_detected == 10
        assert progress.trades_processed == 7
        assert progress.trades_assigned == 5
        assert progress.completion_percentage == 70.0
    
    def test_recovery_progress_validation_negative_counts(self):
        """Test validation fails with negative counts"""
        with pytest.raises(ValidationError) as exc_info:
            RecoveryProgress(
                total_trades_detected=-1,
                trades_processed=0,
                trades_assigned=0,
                completion_percentage=0.0
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("total_trades_detected",) for error in errors)
    
    def test_recovery_progress_validation_invalid_percentage(self):
        """Test validation fails with invalid completion percentage"""
        with pytest.raises(ValidationError) as exc_info:
            RecoveryProgress(
                total_trades_detected=10,
                trades_processed=5,
                trades_assigned=3,
                completion_percentage=150.0  # > 100%
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("completion_percentage",) for error in errors)


class TestSessionStatus:
    """Test cases for SessionStatus enum"""
    
    def test_session_status_values(self):
        """Test SessionStatus enum values"""
        assert SessionStatus.IN_PROGRESS == "IN_PROGRESS"
        assert SessionStatus.COMPLETED == "COMPLETED"
        assert SessionStatus.CANCELLED == "CANCELLED"
        assert SessionStatus.FAILED == "FAILED"
    
    def test_session_status_validation(self):
        """Test SessionStatus validation"""
        assert SessionStatus("IN_PROGRESS") == SessionStatus.IN_PROGRESS
        assert SessionStatus("COMPLETED") == SessionStatus.COMPLETED
        assert SessionStatus("CANCELLED") == SessionStatus.CANCELLED
        assert SessionStatus("FAILED") == SessionStatus.FAILED
        
        with pytest.raises(ValueError):
            SessionStatus("INVALID")


class TestRecoveryType:
    """Test cases for RecoveryType enum"""
    
    def test_recovery_type_values(self):
        """Test RecoveryType enum values"""
        assert RecoveryType.DATABASE_FAILURE == "DATABASE_FAILURE"
        assert RecoveryType.SYSTEM_RESTART == "SYSTEM_RESTART"
        assert RecoveryType.MANUAL_RECOVERY == "MANUAL_RECOVERY"
        assert RecoveryType.DISASTER_RECOVERY == "DISASTER_RECOVERY"
    
    def test_recovery_type_validation(self):
        """Test RecoveryType validation"""
        assert RecoveryType("DATABASE_FAILURE") == RecoveryType.DATABASE_FAILURE
        assert RecoveryType("SYSTEM_RESTART") == RecoveryType.SYSTEM_RESTART
        assert RecoveryType("MANUAL_RECOVERY") == RecoveryType.MANUAL_RECOVERY
        assert RecoveryType("DISASTER_RECOVERY") == RecoveryType.DISASTER_RECOVERY
        
        with pytest.raises(ValueError):
            RecoveryType("INVALID")




















