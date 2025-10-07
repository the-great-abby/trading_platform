"""
Unit tests for StrategyAssignmentService
Tests the StrategyAssignmentService functionality and assignment logic
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from src.services.trade_recovery.services.strategy_assignment_service import (
    StrategyAssignmentService, StrategyAssignmentError
)
from src.services.trade_recovery.models.active_trade import (
    ActiveTrade, TradeSide, PositionType
)
from src.services.trade_recovery.models.strategy_assignment import (
    StrategyAssignment, StrategyAssignmentCreate, StrategyAssignmentUpdate,
    AssignmentStatus, AssignmentReason
)
from src.services.trade_recovery.models.recovery_session import (
    RecoverySession, SessionStatus, RecoveryType
)


class TestStrategyAssignmentService:
    """Test cases for StrategyAssignmentService"""
    
    @pytest.fixture
    def mock_database_client(self):
        """Mock database client"""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_strategy_matcher(self):
        """Mock strategy matcher service"""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def strategy_assignment_service(self, mock_database_client, mock_strategy_matcher):
        """Create StrategyAssignmentService instance with mocked dependencies"""
        service = StrategyAssignmentService()
        service.database_client = mock_database_client
        service.strategy_matcher = mock_strategy_matcher
        return service
    
    @pytest.fixture
    def sample_trade(self):
        """Create a sample ActiveTrade for testing"""
        return ActiveTrade(
            id="trade_123",
            account_id="acc_123",
            symbol="AAPL",
            quantity=Decimal("100.0"),
            side=TradeSide.BUY,
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            entry_time=datetime(2024, 1, 15, 10, 30, 0),
            detected_at=datetime.utcnow(),
            position_type=PositionType.STOCK
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
    
    @pytest.fixture
    def sample_assignment(self):
        """Create a sample StrategyAssignment for testing"""
        return StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id="trade_123",
            strategy_id="strategy_1",
            strategy_name="Elliott Wave Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.ASSIGNED,
            auto_assigned=True,
            user_confirmed=None,
            assigned_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_strategy_assignment_service_initialization(self):
        """Test StrategyAssignmentService initialization"""
        service = StrategyAssignmentService()
        
        assert service.database_client is None
        assert service.strategy_matcher is None
    
    @pytest.mark.asyncio
    async def test_assign_strategy_to_trade_success(self, strategy_assignment_service, sample_trade, sample_session):
        """Test successful strategy assignment to trade"""
        # Mock strategy matching
        mock_match = {
            "strategy_id": "strategy_1",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "match_reason": "High confidence Elliott Wave pattern detected"
        }
        
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(return_value=[mock_match])
        
        # Mock database operations
        strategy_assignment_service.database_client.create_strategy_assignment = AsyncMock(return_value="assignment_123")
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        assignment = await strategy_assignment_service.assign_strategy_to_trade(
            sample_trade, sample_session, auto_assign=True
        )
        
        assert assignment is not None
        assert assignment.strategy_id == "strategy_1"
        assert assignment.strategy_name == "Elliott Wave Strategy"
        assert assignment.confidence_score == 0.85
        assert assignment.auto_assigned is True
        assert assignment.status == AssignmentStatus.ASSIGNED
    
    @pytest.mark.asyncio
    async def test_assign_strategy_to_trade_no_matches(self, strategy_assignment_service, sample_trade, sample_session):
        """Test strategy assignment with no matches"""
        # Mock no strategy matches
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(return_value=[])
        strategy_assignment_service.strategy_matcher.suggest_fallback_strategies = AsyncMock(return_value=[])
        
        assignment = await strategy_assignment_service.assign_strategy_to_trade(
            sample_trade, sample_session, auto_assign=True
        )
        
        assert assignment is None
    
    @pytest.mark.asyncio
    async def test_assign_strategy_to_trade_fallback_strategies(self, strategy_assignment_service, sample_trade, sample_session):
        """Test strategy assignment with fallback strategies"""
        # Mock no direct matches but fallback suggestions
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(return_value=[])
        
        mock_fallback = {
            "strategy_id": "strategy_3",
            "strategy_name": "Conservative Strategy",
            "confidence_score": 0.45,
            "suggestion_reason": "Conservative approach for uncertain conditions"
        }
        
        strategy_assignment_service.strategy_matcher.suggest_fallback_strategies = AsyncMock(return_value=[mock_fallback])
        
        # Mock database operations
        strategy_assignment_service.database_client.create_strategy_assignment = AsyncMock(return_value="assignment_123")
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        assignment = await strategy_assignment_service.assign_strategy_to_trade(
            sample_trade, sample_session, auto_assign=True
        )
        
        assert assignment is not None
        assert assignment.strategy_id == "strategy_3"
        assert assignment.strategy_name == "Conservative Strategy"
        assert assignment.confidence_score == 0.45
        assert assignment.auto_assigned is True
    
    @pytest.mark.asyncio
    async def test_assign_strategy_to_trade_manual_assignment(self, strategy_assignment_service, sample_trade, sample_session):
        """Test manual strategy assignment"""
        # Mock database operations
        strategy_assignment_service.database_client.create_strategy_assignment = AsyncMock(return_value="assignment_123")
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        assignment = await strategy_assignment_service.assign_strategy_to_trade(
            sample_trade, sample_session, auto_assign=False,
            strategy_id="strategy_1", strategy_name="Manual Strategy", confidence_score=0.9
        )
        
        assert assignment is not None
        assert assignment.strategy_id == "strategy_1"
        assert assignment.strategy_name == "Manual Strategy"
        assert assignment.confidence_score == 0.9
        assert assignment.auto_assigned is False
        assert assignment.assignment_reason == AssignmentReason.MANUAL_ASSIGNMENT
    
    @pytest.mark.asyncio
    async def test_assign_strategy_to_trade_database_error(self, strategy_assignment_service, sample_trade, sample_session):
        """Test strategy assignment with database error"""
        # Mock strategy matching
        mock_match = {
            "strategy_id": "strategy_1",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "match_reason": "High confidence match"
        }
        
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(return_value=[mock_match])
        
        # Mock database error
        strategy_assignment_service.database_client.create_strategy_assignment = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(StrategyAssignmentError) as exc_info:
            await strategy_assignment_service.assign_strategy_to_trade(
                sample_trade, sample_session, auto_assign=True
            )
        
        assert "Failed to assign strategy to trade" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_confirm_assignment_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignment confirmation"""
        # Mock database operations
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[sample_assignment.dict()])
        strategy_assignment_service.database_client.update_strategy_assignment = AsyncMock(return_value=True)
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        updated_assignment = await strategy_assignment_service.confirm_assignment(
            sample_assignment.id, sample_assignment.session_id, "user_456"
        )
        
        assert updated_assignment is not None
        assert updated_assignment.status == AssignmentStatus.CONFIRMED
        assert updated_assignment.user_confirmed is True
        assert updated_assignment.confirmed_at is not None
    
    @pytest.mark.asyncio
    async def test_confirm_assignment_not_found(self, strategy_assignment_service):
        """Test assignment confirmation when assignment not found"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[])
        
        updated_assignment = await strategy_assignment_service.confirm_assignment(
            str(uuid4()), str(uuid4()), "user_456"
        )
        
        assert updated_assignment is None
    
    @pytest.mark.asyncio
    async def test_reject_assignment_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignment rejection"""
        # Mock database operations
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[sample_assignment.dict()])
        strategy_assignment_service.database_client.update_strategy_assignment = AsyncMock(return_value=True)
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        updated_assignment = await strategy_assignment_service.reject_assignment(
            sample_assignment.id, sample_assignment.session_id, "user_456", "User prefers different strategy"
        )
        
        assert updated_assignment is not None
        assert updated_assignment.status == AssignmentStatus.REJECTED
        assert updated_assignment.user_confirmed is False
        assert updated_assignment.rejected_at is not None
        assert updated_assignment.rejection_reason == "User prefers different strategy"
    
    @pytest.mark.asyncio
    async def test_reject_assignment_not_found(self, strategy_assignment_service):
        """Test assignment rejection when assignment not found"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[])
        
        updated_assignment = await strategy_assignment_service.reject_assignment(
            str(uuid4()), str(uuid4()), "user_456", "User prefers different strategy"
        )
        
        assert updated_assignment is None
    
    @pytest.mark.asyncio
    async def test_get_assignments_for_session_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignments retrieval for session"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[sample_assignment.dict()])
        
        assignments = await strategy_assignment_service.get_assignments_for_session(sample_assignment.session_id)
        
        assert len(assignments) == 1
        assert assignments[0].id == sample_assignment.id
        assert assignments[0].strategy_id == "strategy_1"
        assert assignments[0].strategy_name == "Elliott Wave Strategy"
    
    @pytest.mark.asyncio
    async def test_get_assignments_for_session_empty(self, strategy_assignment_service):
        """Test assignments retrieval for session with no assignments"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[])
        
        assignments = await strategy_assignment_service.get_assignments_for_session(str(uuid4()))
        
        assert len(assignments) == 0
    
    @pytest.mark.asyncio
    async def test_get_assignments_for_trade_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignments retrieval for trade"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[sample_assignment.dict()])
        
        assignments = await strategy_assignment_service.get_assignments_for_trade(sample_assignment.trade_id)
        
        assert len(assignments) == 1
        assert assignments[0].trade_id == sample_assignment.trade_id
    
    @pytest.mark.asyncio
    async def test_get_assignment_statistics_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignment statistics retrieval"""
        strategy_assignment_service.database_client.get_strategy_assignments = AsyncMock(return_value=[sample_assignment.dict()])
        
        stats = await strategy_assignment_service.get_assignment_statistics(sample_assignment.session_id)
        
        assert stats is not None
        assert "total_assignments" in stats
        assert "auto_assigned" in stats
        assert "user_confirmed" in stats
        assert "user_rejected" in stats
        assert "pending_confirmation" in stats
    
    @pytest.mark.asyncio
    async def test_bulk_assign_strategies_success(self, strategy_assignment_service, sample_trade, sample_session):
        """Test successful bulk strategy assignment"""
        trades = [sample_trade]
        
        # Mock strategy matching
        mock_match = {
            "strategy_id": "strategy_1",
            "strategy_name": "Elliott Wave Strategy",
            "confidence_score": 0.85,
            "match_reason": "High confidence match"
        }
        
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(return_value=[mock_match])
        
        # Mock database operations
        strategy_assignment_service.database_client.create_strategy_assignment = AsyncMock(return_value="assignment_123")
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        results = await strategy_assignment_service.bulk_assign_strategies(trades, sample_session)
        
        assert len(results) == 1
        assert results[0]["trade_id"] == sample_trade.id
        assert results[0]["success"] is True
        assert results[0]["assignment_id"] == "assignment_123"
    
    @pytest.mark.asyncio
    async def test_bulk_assign_strategies_partial_failure(self, strategy_assignment_service, sample_trade, sample_session):
        """Test bulk strategy assignment with partial failure"""
        trades = [sample_trade]
        
        # Mock strategy matching failure
        strategy_assignment_service.strategy_matcher.match_strategies = AsyncMock(side_effect=Exception("Matching error"))
        
        results = await strategy_assignment_service.bulk_assign_strategies(trades, sample_session)
        
        assert len(results) == 1
        assert results[0]["trade_id"] == sample_trade.id
        assert results[0]["success"] is False
        assert "error" in results[0]
    
    @pytest.mark.asyncio
    async def test_validate_assignment_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignment validation"""
        is_valid = await strategy_assignment_service._validate_assignment(sample_assignment)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_assignment_invalid(self, strategy_assignment_service):
        """Test assignment validation with invalid assignment"""
        invalid_assignment = StrategyAssignment(
            id=str(uuid4()),
            session_id=str(uuid4()),
            trade_id="",  # Empty trade_id
            strategy_id="strategy_1",
            strategy_name="Test Strategy",
            confidence_score=0.85,
            assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
            status=AssignmentStatus.ASSIGNED,
            assigned_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        is_valid = await strategy_assignment_service._validate_assignment(invalid_assignment)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_calculate_assignment_metrics_success(self, strategy_assignment_service, sample_assignment):
        """Test successful assignment metrics calculation"""
        assignments = [sample_assignment]
        
        metrics = await strategy_assignment_service._calculate_assignment_metrics(assignments)
        
        assert metrics is not None
        assert "total_assignments" in metrics
        assert "auto_assigned" in metrics
        assert "user_confirmed" in metrics
        assert "user_rejected" in metrics
        assert "pending_confirmation" in metrics
        assert "avg_confidence_score" in metrics
    
    @pytest.mark.asyncio
    async def test_update_session_progress_success(self, strategy_assignment_service, sample_session):
        """Test successful session progress update"""
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(return_value=True)
        
        await strategy_assignment_service._update_session_progress(sample_session.id, 1)
        
        strategy_assignment_service.database_client.update_recovery_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_session_progress_error(self, strategy_assignment_service):
        """Test session progress update with error"""
        strategy_assignment_service.database_client.update_recovery_session = AsyncMock(side_effect=Exception("Database error"))
        
        # Should not raise exception, just log error
        await strategy_assignment_service._update_session_progress(str(uuid4()), 1)


class TestStrategyAssignmentError:
    """Test cases for StrategyAssignmentError exception"""
    
    def test_strategy_assignment_error_creation(self):
        """Test StrategyAssignmentError creation"""
        error = StrategyAssignmentError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


















