"""
Unit tests for StrategyAssignment model
Tests the StrategyAssignment Pydantic model validation and behavior
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import ValidationError

from src.services.trade_recovery.models.strategy_assignment import (
    StrategyAssignment, StrategyAssignmentCreate, StrategyAssignmentUpdate,
    StrategyAssignmentResponse, AssignmentStatus, AssignmentReason
)


class TestStrategyAssignmentModel:
    """Test cases for StrategyAssignment model"""
    
    def test_strategy_assignment_creation_valid_data(self):
        """Test creating StrategyAssignment with valid data"""
        assignment_data = {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "trade_id": str(uuid4()),
            "strategy_id": "strategy_123",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "assignment_reason": AssignmentReason.HIGH_CONFIDENCE_MATCH,
            "status": AssignmentStatus.ASSIGNED,
            "auto_assigned": True,
            "user_confirmed": None,
            "assigned_at": datetime(2024, 1, 15, 10, 30, 0),
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
            "updated_at": datetime(2024, 1, 15, 10, 30, 0)
        }
        
        assignment = StrategyAssignment(**assignment_data)
        
        assert assignment.id == assignment_data["id"]
        assert assignment.session_id == assignment_data["session_id"]
        assert assignment.trade_id == assignment_data["trade_id"]
        assert assignment.strategy_id == "strategy_123"
        assert assignment.strategy_name == "Elliott Wave Strategy"
        assert assignment.confidence_score == 0.85
        assert assignment.assignment_reason == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert assignment.status == AssignmentStatus.ASSIGNED
        assert assignment.auto_assigned is True
        assert assignment.user_confirmed is None
        assert assignment.assigned_at == datetime(2024, 1, 15, 10, 30, 0)
        assert assignment.confirmed_at is None
        assert assignment.rejected_at is None
        assert assignment.rejection_reason is None
        assert assignment.notes is None
    
    def test_strategy_assignment_creation_minimal_data(self):
        """Test creating StrategyAssignment with minimal required data"""
        assignment_data = {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "trade_id": str(uuid4()),
            "strategy_id": "strategy_123",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.75,
            "assignment_reason": AssignmentReason.HIGH_CONFIDENCE_MATCH,
            "status": AssignmentStatus.ASSIGNED,
            "assigned_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        assignment = StrategyAssignment(**assignment_data)
        
        assert assignment.id == assignment_data["id"]
        assert assignment.session_id == assignment_data["session_id"]
        assert assignment.trade_id == assignment_data["trade_id"]
        assert assignment.strategy_id == "strategy_123"
        assert assignment.strategy_name == "Elliott Wave Strategy"
        assert assignment.confidence_score == 0.75
        assert assignment.assignment_reason == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert assignment.status == AssignmentStatus.ASSIGNED
        assert assignment.auto_assigned is False  # Default value
        assert assignment.user_confirmed is None
        assert assignment.confirmed_at is None
        assert assignment.rejected_at is None
        assert assignment.rejection_reason is None
        assert assignment.notes is None
    
    def test_strategy_assignment_validation_missing_required_fields(self):
        """Test validation fails with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignment(
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                status=AssignmentStatus.ASSIGNED
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("id",) for error in errors)
        assert any(error["loc"] == ("assigned_at",) for error in errors)
        assert any(error["loc"] == ("created_at",) for error in errors)
        assert any(error["loc"] == ("updated_at",) for error in errors)
    
    def test_strategy_assignment_validation_invalid_status(self):
        """Test validation fails with invalid status"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignment(
                id=str(uuid4()),
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                status="INVALID_STATUS",
                assigned_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)
    
    def test_strategy_assignment_validation_invalid_reason(self):
        """Test validation fails with invalid assignment reason"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignment(
                id=str(uuid4()),
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason="INVALID_REASON",
                status=AssignmentStatus.ASSIGNED,
                assigned_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("assignment_reason",) for error in errors)
    
    def test_strategy_assignment_validation_invalid_confidence_score(self):
        """Test validation fails with invalid confidence score"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignment(
                id=str(uuid4()),
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=1.5,  # > 1.0
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                status=AssignmentStatus.ASSIGNED,
                assigned_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("confidence_score",) for error in errors)
    
    def test_strategy_assignment_validation_negative_confidence_score(self):
        """Test validation fails with negative confidence score"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignment(
                id=str(uuid4()),
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=-0.1,  # < 0.0
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                status=AssignmentStatus.ASSIGNED,
                assigned_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("confidence_score",) for error in errors)
    
    def test_strategy_assignment_confirmed_status(self):
        """Test StrategyAssignment with confirmed status"""
        assignment = StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id=str(uuid4()),
            strategy_id="strategy_123",
            strategy_name="Elliott Wave Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.CONFIRMED,
            auto_assigned=True,
            user_confirmed=True,
            assigned_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert assignment.status == AssignmentStatus.CONFIRMED
        assert assignment.user_confirmed is True
        assert assignment.confirmed_at is not None
        assert assignment.rejected_at is None
        assert assignment.rejection_reason is None
    
    def test_strategy_assignment_rejected_status(self):
        """Test StrategyAssignment with rejected status"""
        assignment = StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id=str(uuid4()),
            strategy_id="strategy_123",
            strategy_name="Elliott Wave Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.REJECTED,
            auto_assigned=True,
            user_confirmed=False,
            assigned_at=datetime.utcnow(),
            rejected_at=datetime.utcnow(),
            rejection_reason="User prefers different strategy",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert assignment.status == AssignmentStatus.REJECTED
        assert assignment.user_confirmed is False
        assert assignment.rejected_at is not None
        assert assignment.rejection_reason == "User prefers different strategy"
        assert assignment.confirmed_at is None
    
    def test_strategy_assignment_serialization(self):
        """Test StrategyAssignment serialization to dict"""
        assignment = StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id=str(uuid4()),
            strategy_id="strategy_123",
            strategy_name="Elliott Wave Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.ASSIGNED,
            auto_assigned=True,
            assigned_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assignment_dict = assignment.dict()
        
        assert isinstance(assignment_dict, dict)
        assert assignment_dict["strategy_id"] == "strategy_123"
        assert assignment_dict["strategy_name"] == "Elliott Wave Strategy"
        assert assignment_dict["confidence_score"] == 0.85
        assert assignment_dict["assignment_reason"] == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert assignment_dict["status"] == AssignmentStatus.ASSIGNED
        assert assignment_dict["auto_assigned"] is True
    
    def test_strategy_assignment_json_serialization(self):
        """Test StrategyAssignment JSON serialization"""
        assignment = StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id=str(uuid4()),
            strategy_id="strategy_123",
            strategy_name="Elliott Wave Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.ASSIGNED,
            assigned_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        json_str = assignment.json()
        
        assert isinstance(json_str, str)
        assert "strategy_123" in json_str
        assert "Elliott Wave Strategy" in json_str
        assert "0.85" in json_str
        assert "HIGH_CONFIDENCE_MATCH" in json_str
        assert "ASSIGNED" in json_str


class TestStrategyAssignmentCreate:
    """Test cases for StrategyAssignmentCreate model"""
    
    def test_strategy_assignment_create_valid_data(self):
        """Test creating StrategyAssignmentCreate with valid data"""
        create_data = {
            "session_id": str(uuid4()),
            "trade_id": str(uuid4()),
            "strategy_id": "strategy_123",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "assignment_reason": AssignmentReason.HIGH_CONFIDENCE_MATCH,
            "auto_assigned": True,
            "notes": "High confidence match based on market conditions"
        }
        
        assignment_create = StrategyAssignmentCreate(**create_data)
        
        assert assignment_create.session_id == create_data["session_id"]
        assert assignment_create.trade_id == create_data["trade_id"]
        assert assignment_create.strategy_id == "strategy_123"
        assert assignment_create.strategy_name == "Elliott Wave Strategy"
        assert assignment_create.confidence_score == 0.85
        assert assignment_create.assignment_reason == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert assignment_create.auto_assigned is True
        assert assignment_create.notes == "High confidence match based on market conditions"
    
    def test_strategy_assignment_create_minimal_data(self):
        """Test creating StrategyAssignmentCreate with minimal required data"""
        create_data = {
            "session_id": str(uuid4()),
            "trade_id": str(uuid4()),
            "strategy_id": "strategy_123",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.75,
            "assignment_reason": AssignmentReason.HIGH_CONFIDENCE_MATCH
        }
        
        assignment_create = StrategyAssignmentCreate(**create_data)
        
        assert assignment_create.session_id == create_data["session_id"]
        assert assignment_create.trade_id == create_data["trade_id"]
        assert assignment_create.strategy_id == "strategy_123"
        assert assignment_create.strategy_name == "Elliott Wave Strategy"
        assert assignment_create.confidence_score == 0.75
        assert assignment_create.assignment_reason == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert assignment_create.auto_assigned is False  # Default value
        assert assignment_create.notes is None
    
    def test_strategy_assignment_create_validation_missing_session_id(self):
        """Test validation fails with missing session_id"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignmentCreate(
                trade_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("session_id",) for error in errors)
    
    def test_strategy_assignment_create_validation_missing_trade_id(self):
        """Test validation fails with missing trade_id"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignmentCreate(
                session_id=str(uuid4()),
                strategy_id="strategy_123",
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("trade_id",) for error in errors)
    
    def test_strategy_assignment_create_validation_missing_strategy_id(self):
        """Test validation fails with missing strategy_id"""
        with pytest.raises(ValidationError) as exc_info:
            StrategyAssignmentCreate(
                session_id=str(uuid4()),
                trade_id=str(uuid4()),
                strategy_name="Elliott Wave Strategy",
                confidence_score=0.75,
                assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("strategy_id",) for error in errors)


class TestStrategyAssignmentUpdate:
    """Test cases for StrategyAssignmentUpdate model"""
    
    def test_strategy_assignment_update_valid_data(self):
        """Test creating StrategyAssignmentUpdate with valid data"""
        update_data = {
            "status": AssignmentStatus.CONFIRMED,
            "user_confirmed": True,
            "confirmed_at": datetime.utcnow(),
            "notes": "User confirmed assignment"
        }
        
        assignment_update = StrategyAssignmentUpdate(**update_data)
        
        assert assignment_update.status == AssignmentStatus.CONFIRMED
        assert assignment_update.user_confirmed is True
        assert assignment_update.confirmed_at is not None
        assert assignment_update.notes == "User confirmed assignment"
    
    def test_strategy_assignment_update_rejection_data(self):
        """Test creating StrategyAssignmentUpdate with rejection data"""
        update_data = {
            "status": AssignmentStatus.REJECTED,
            "user_confirmed": False,
            "rejected_at": datetime.utcnow(),
            "rejection_reason": "User prefers different strategy",
            "notes": "User rejected assignment"
        }
        
        assignment_update = StrategyAssignmentUpdate(**update_data)
        
        assert assignment_update.status == AssignmentStatus.REJECTED
        assert assignment_update.user_confirmed is False
        assert assignment_update.rejected_at is not None
        assert assignment_update.rejection_reason == "User prefers different strategy"
        assert assignment_update.notes == "User rejected assignment"
    
    def test_strategy_assignment_update_empty_data(self):
        """Test creating StrategyAssignmentUpdate with empty data"""
        assignment_update = StrategyAssignmentUpdate()
        
        assert assignment_update.status is None
        assert assignment_update.user_confirmed is None
        assert assignment_update.confirmed_at is None
        assert assignment_update.rejected_at is None
        assert assignment_update.rejection_reason is None
        assert assignment_update.notes is None


class TestStrategyAssignmentResponse:
    """Test cases for StrategyAssignmentResponse model"""
    
    def test_strategy_assignment_response_creation(self):
        """Test creating StrategyAssignmentResponse"""
        response_data = {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "trade_id": str(uuid4()),
            "strategy_id": "strategy_123",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "assignment_reason": AssignmentReason.HIGH_CONFIDENCE_MATCH,
            "status": AssignmentStatus.ASSIGNED,
            "auto_assigned": True,
            "user_confirmed": None,
            "assigned_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = StrategyAssignmentResponse(**response_data)
        
        assert response.id == response_data["id"]
        assert response.session_id == response_data["session_id"]
        assert response.trade_id == response_data["trade_id"]
        assert response.strategy_id == "strategy_123"
        assert response.strategy_name == "Elliott Wave Strategy"
        assert response.confidence_score == 0.85
        assert response.assignment_reason == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert response.status == AssignmentStatus.ASSIGNED
        assert response.auto_assigned is True


class TestAssignmentStatus:
    """Test cases for AssignmentStatus enum"""
    
    def test_assignment_status_values(self):
        """Test AssignmentStatus enum values"""
        assert AssignmentStatus.ASSIGNED == "ASSIGNED"
        assert AssignmentStatus.CONFIRMED == "CONFIRMED"
        assert AssignmentStatus.REJECTED == "REJECTED"
        assert AssignmentStatus.CANCELLED == "CANCELLED"
    
    def test_assignment_status_validation(self):
        """Test AssignmentStatus validation"""
        assert AssignmentStatus("ASSIGNED") == AssignmentStatus.ASSIGNED
        assert AssignmentStatus("CONFIRMED") == AssignmentStatus.CONFIRMED
        assert AssignmentStatus("REJECTED") == AssignmentStatus.REJECTED
        assert AssignmentStatus("CANCELLED") == AssignmentStatus.CANCELLED
        
        with pytest.raises(ValueError):
            AssignmentStatus("INVALID")


class TestAssignmentReason:
    """Test cases for AssignmentReason enum"""
    
    def test_assignment_reason_values(self):
        """Test AssignmentReason enum values"""
        assert AssignmentReason.HIGH_CONFIDENCE_MATCH == "HIGH_CONFIDENCE_MATCH"
        assert AssignmentReason.MARKET_CONDITIONS == "MARKET_CONDITIONS"
        assert AssignmentReason.USER_PREFERENCE == "USER_PREFERENCE"
        assert AssignmentReason.FALLBACK_ASSIGNMENT == "FALLBACK_ASSIGNMENT"
        assert AssignmentReason.MANUAL_ASSIGNMENT == "MANUAL_ASSIGNMENT"
    
    def test_assignment_reason_validation(self):
        """Test AssignmentReason validation"""
        assert AssignmentReason("HIGH_CONFIDENCE_MATCH") == AssignmentReason.HIGH_CONFIDENCE_MATCH
        assert AssignmentReason("MARKET_CONDITIONS") == AssignmentReason.MARKET_CONDITIONS
        assert AssignmentReason("USER_PREFERENCE") == AssignmentReason.USER_PREFERENCE
        assert AssignmentReason("FALLBACK_ASSIGNMENT") == AssignmentReason.FALLBACK_ASSIGNMENT
        assert AssignmentReason("MANUAL_ASSIGNMENT") == AssignmentReason.MANUAL_ASSIGNMENT
        
        with pytest.raises(ValueError):
            AssignmentReason("INVALID")


















