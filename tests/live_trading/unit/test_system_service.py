"""
Unit tests for system service.

Tests emergency stop functionality, system status, and operational controls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from src.services.live_trading.system_service import (
    SystemService, SystemError, EmergencyStopActiveError
)
from src.services.live_trading.models import (
    LiveTradingAccount, RiskProfile, RiskLevel
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    return AsyncMock()


@pytest.fixture
def sample_account():
    """Create sample trading account."""
    return LiveTradingAccount(
        account_id="test-account-123",
        public_account_id="public-123",
        account_name="Test Account",
        account_type="CASH",
        buying_power=10000.0,
        cash_balance=5000.0,
        equity=15000.0,
        is_active=True
    )


@pytest.fixture
def sample_risk_profile():
    """Create sample risk profile."""
    return RiskProfile(
        account_id="test-account-123",
        max_position_size=10000.0,
        max_portfolio_risk=0.05,
        max_daily_loss=1000.0,
        max_daily_trades=20,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD"]',
        max_greeks_exposure='{"delta": 1000.0, "gamma": 100.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )


@pytest.fixture
def system_service(mock_db_session, mock_redis_client):
    """Create system service instance."""
    return SystemService(mock_db_session, mock_redis_client)


class TestEmergencyStop:
    """Test emergency stop functionality."""
    
    @pytest.mark.asyncio
    async def test_activate_emergency_stop_success(self, system_service, mock_db_session, 
                                                 mock_redis_client, sample_risk_profile):
        """Test successful emergency stop activation."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        reason = "Market volatility too high"
        
        result = await system_service.activate_emergency_stop("test-account-123", reason)
        
        assert result["success"] is True
        assert result["account_id"] == "test-account-123"
        assert result["status"] == "activated"
        assert result["reason"] == reason
        
        # Verify Redis was updated
        mock_redis_client.set.assert_called_with(
            "emergency_stop:test-account-123",
            "true",
            ex=None
        )
        
        # Verify database was updated
        assert sample_risk_profile.emergency_stop_active is True
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_activate_emergency_stop_account_not_found(self, system_service, mock_db_session):
        """Test emergency stop activation when account not found."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(SystemError, match="Account not found"):
            await system_service.activate_emergency_stop("nonexistent-account", "Test reason")
    
    @pytest.mark.asyncio
    async def test_deactivate_emergency_stop_success(self, system_service, mock_db_session, 
                                                   mock_redis_client, sample_risk_profile):
        """Test successful emergency stop deactivation."""
        sample_risk_profile.emergency_stop_active = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await system_service.deactivate_emergency_stop("test-account-123")
        
        assert result["success"] is True
        assert result["account_id"] == "test-account-123"
        assert result["status"] == "deactivated"
        
        # Verify Redis was updated
        mock_redis_client.delete.assert_called_with("emergency_stop:test-account-123")
        
        # Verify database was updated
        assert sample_risk_profile.emergency_stop_active is False
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_deactivate_emergency_stop_not_active(self, system_service, mock_db_session, 
                                                      sample_risk_profile):
        """Test emergency stop deactivation when not active."""
        sample_risk_profile.emergency_stop_active = False
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await system_service.deactivate_emergency_stop("test-account-123")
        
        assert result["success"] is True
        assert result["status"] == "already_deactivated"
        
        # Verify Redis was still called
        mock_redis_client.delete.assert_called_with("emergency_stop:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_emergency_stop_active(self, system_service, mock_redis_client):
        """Test emergency stop check when active."""
        mock_redis_client.get.return_value = "true"
        
        result = await system_service.check_emergency_stop("test-account-123")
        
        assert result is True
        mock_redis_client.get.assert_called_with("emergency_stop:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_emergency_stop_not_active(self, system_service, mock_redis_client):
        """Test emergency stop check when not active."""
        mock_redis_client.get.return_value = None
        
        result = await system_service.check_emergency_stop("test-account-123")
        
        assert result is False
        mock_redis_client.get.assert_called_with("emergency_stop:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_emergency_stop_redis_error(self, system_service, mock_redis_client):
        """Test emergency stop check with Redis error."""
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        with pytest.raises(SystemError, match="Redis connection error"):
            await system_service.check_emergency_stop("test-account-123")


class TestSystemStatus:
    """Test system status methods."""
    
    @pytest.mark.asyncio
    async def test_get_system_status_healthy(self, system_service, mock_redis_client):
        """Test getting system status when healthy."""
        mock_redis_client.get.return_value = None  # No emergency stop
        
        result = await system_service.get_system_status()
        
        assert result["status"] == "healthy"
        assert result["emergency_stop_active"] is False
        assert result["timestamp"] is not None
        assert result["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_system_status_emergency_stop(self, system_service, mock_redis_client):
        """Test getting system status when emergency stop is active."""
        mock_redis_client.get.return_value = "true"
        
        result = await system_service.get_system_status()
        
        assert result["status"] == "emergency_stop_active"
        assert result["emergency_stop_active"] is True
        assert result["timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_get_system_status_redis_error(self, system_service, mock_redis_client):
        """Test getting system status with Redis error."""
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        result = await system_service.get_system_status()
        
        assert result["status"] == "error"
        assert result["error"] == "Redis connection error"
    
    @pytest.mark.asyncio
    async def test_get_operational_status(self, system_service, mock_db_session, mock_redis_client):
        """Test getting operational status."""
        mock_redis_client.get.return_value = None  # No emergency stop
        
        # Mock database connectivity check
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        
        result = await system_service.get_operational_status()
        
        assert result["database"] == "connected"
        assert result["redis"] == "connected"
        assert result["emergency_stop"] == "inactive"
        assert result["overall_status"] == "operational"
    
    @pytest.mark.asyncio
    async def test_get_operational_status_database_error(self, system_service, mock_db_session, mock_redis_client):
        """Test getting operational status with database error."""
        mock_redis_client.get.return_value = None
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        result = await system_service.get_operational_status()
        
        assert result["database"] == "error"
        assert result["redis"] == "connected"
        assert result["emergency_stop"] == "inactive"
        assert result["overall_status"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_get_operational_status_redis_error(self, system_service, mock_db_session, mock_redis_client):
        """Test getting operational status with Redis error."""
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        
        result = await system_service.get_operational_status()
        
        assert result["database"] == "connected"
        assert result["redis"] == "error"
        assert result["emergency_stop"] == "unknown"
        assert result["overall_status"] == "degraded"


class TestSystemControls:
    """Test system control methods."""
    
    @pytest.mark.asyncio
    async def test_pause_trading_success(self, system_service, mock_redis_client):
        """Test successful trading pause."""
        result = await system_service.pause_trading("test-account-123", "Scheduled maintenance")
        
        assert result["success"] is True
        assert result["account_id"] == "test-account-123"
        assert result["status"] == "paused"
        assert result["reason"] == "Scheduled maintenance"
        
        # Verify Redis was updated
        mock_redis_client.set.assert_called_with(
            "trading_paused:test-account-123",
            "Scheduled maintenance",
            ex=3600  # 1 hour default
        )
    
    @pytest.mark.asyncio
    async def test_pause_trading_with_custom_duration(self, system_service, mock_redis_client):
        """Test trading pause with custom duration."""
        result = await system_service.pause_trading("test-account-123", "System update", duration_seconds=7200)
        
        assert result["success"] is True
        assert result["status"] == "paused"
        
        # Verify Redis was updated with custom duration
        mock_redis_client.set.assert_called_with(
            "trading_paused:test-account-123",
            "System update",
            ex=7200
        )
    
    @pytest.mark.asyncio
    async def test_resume_trading_success(self, system_service, mock_redis_client):
        """Test successful trading resume."""
        result = await system_service.resume_trading("test-account-123")
        
        assert result["success"] is True
        assert result["account_id"] == "test-account-123"
        assert result["status"] == "resumed"
        
        # Verify Redis was updated
        mock_redis_client.delete.assert_called_with("trading_paused:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_trading_paused_active(self, system_service, mock_redis_client):
        """Test trading pause check when active."""
        mock_redis_client.get.return_value = "Scheduled maintenance"
        
        result = await system_service.check_trading_paused("test-account-123")
        
        assert result is True
        mock_redis_client.get.assert_called_with("trading_paused:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_trading_paused_not_active(self, system_service, mock_redis_client):
        """Test trading pause check when not active."""
        mock_redis_client.get.return_value = None
        
        result = await system_service.check_trading_paused("test-account-123")
        
        assert result is False
        mock_redis_client.get.assert_called_with("trading_paused:test-account-123")
    
    @pytest.mark.asyncio
    async def test_check_trading_paused_redis_error(self, system_service, mock_redis_client):
        """Test trading pause check with Redis error."""
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        with pytest.raises(SystemError, match="Redis connection error"):
            await system_service.check_trading_paused("test-account-123")


class TestSystemHealth:
    """Test system health monitoring."""
    
    @pytest.mark.asyncio
    async def test_perform_health_check_healthy(self, system_service, mock_db_session, mock_redis_client):
        """Test health check when system is healthy."""
        # Mock database check
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        
        # Mock Redis check
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = None  # No emergency stop
        
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "healthy"
        assert result["checks"]["database"] == "healthy"
        assert result["checks"]["redis"] == "healthy"
        assert result["checks"]["emergency_stop"] == "inactive"
        assert result["timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_perform_health_check_database_error(self, system_service, mock_db_session, mock_redis_client):
        """Test health check with database error."""
        mock_db_session.execute.side_effect = Exception("Database connection error")
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = None
        
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "degraded"
        assert result["checks"]["database"] == "unhealthy"
        assert result["checks"]["redis"] == "healthy"
        assert result["checks"]["emergency_stop"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_perform_health_check_redis_error(self, system_service, mock_db_session, mock_redis_client):
        """Test health check with Redis error."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        mock_redis_client.ping.side_effect = Exception("Redis connection error")
        
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "degraded"
        assert result["checks"]["database"] == "healthy"
        assert result["checks"]["redis"] == "unhealthy"
        assert result["checks"]["emergency_stop"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_perform_health_check_emergency_stop(self, system_service, mock_db_session, mock_redis_client):
        """Test health check when emergency stop is active."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        mock_redis_client.ping.return_value = True
        mock_redis_client.get.return_value = "true"  # Emergency stop active
        
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "emergency_stop_active"
        assert result["checks"]["database"] == "healthy"
        assert result["checks"]["redis"] == "healthy"
        assert result["checks"]["emergency_stop"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, system_service, mock_db_session, mock_redis_client):
        """Test getting system metrics."""
        # Mock database metrics
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = 100  # Active connections
        
        # Mock Redis metrics
        mock_redis_client.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024000,
            "keyspace_hits": 1000,
            "keyspace_misses": 100
        }
        
        result = await system_service.get_system_metrics()
        
        assert "database" in result
        assert "redis" in result
        assert "timestamp" in result
        
        assert result["database"]["active_connections"] == 100
        assert result["redis"]["connected_clients"] == 5
        assert result["redis"]["used_memory"] == 1024000
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_error(self, system_service, mock_db_session, mock_redis_client):
        """Test getting system metrics with error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_redis_client.info.side_effect = Exception("Redis error")
        
        result = await system_service.get_system_metrics()
        
        assert result["database"]["error"] == "Database error"
        assert result["redis"]["error"] == "Redis error"


class TestSystemMaintenance:
    """Test system maintenance methods."""
    
    @pytest.mark.asyncio
    async def test_start_maintenance_mode(self, system_service, mock_redis_client):
        """Test starting maintenance mode."""
        result = await system_service.start_maintenance_mode("Database migration", 3600)
        
        assert result["success"] is True
        assert result["status"] == "maintenance_mode_active"
        assert result["reason"] == "Database migration"
        assert result["estimated_duration"] == 3600
        
        # Verify Redis was updated
        mock_redis_client.set.assert_called_with(
            "maintenance_mode",
            "Database migration",
            ex=3600
        )
    
    @pytest.mark.asyncio
    async def test_stop_maintenance_mode(self, system_service, mock_redis_client):
        """Test stopping maintenance mode."""
        result = await system_service.stop_maintenance_mode()
        
        assert result["success"] is True
        assert result["status"] == "maintenance_mode_inactive"
        
        # Verify Redis was updated
        mock_redis_client.delete.assert_called_with("maintenance_mode")
    
    @pytest.mark.asyncio
    async def test_check_maintenance_mode_active(self, system_service, mock_redis_client):
        """Test maintenance mode check when active."""
        mock_redis_client.get.return_value = "Database migration"
        
        result = await system_service.check_maintenance_mode()
        
        assert result is True
        mock_redis_client.get.assert_called_with("maintenance_mode")
    
    @pytest.mark.asyncio
    async def test_check_maintenance_mode_inactive(self, system_service, mock_redis_client):
        """Test maintenance mode check when inactive."""
        mock_redis_client.get.return_value = None
        
        result = await system_service.check_maintenance_mode()
        
        assert result is False
        mock_redis_client.get.assert_called_with("maintenance_mode")
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, system_service, mock_redis_client):
        """Test cleaning up expired sessions."""
        mock_redis_client.scan.return_value = (0, ["session:expired1", "session:expired2"])
        mock_redis_client.delete.return_value = 2
        
        result = await system_service.cleanup_expired_sessions()
        
        assert result["cleaned_sessions"] == 2
        assert result["success"] is True
        
        # Verify Redis was called
        mock_redis_client.scan.assert_called()
        mock_redis_client.delete.assert_called_with("session:expired1", "session:expired2")
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_error(self, system_service, mock_redis_client):
        """Test cleaning up expired sessions with error."""
        mock_redis_client.scan.side_effect = Exception("Redis error")
        
        result = await system_service.cleanup_expired_sessions()
        
        assert result["success"] is False
        assert result["error"] == "Redis error"
        assert result["cleaned_sessions"] == 0


class TestSystemValidation:
    """Test system validation methods."""
    
    @pytest.mark.asyncio
    async def test_validate_system_requirements(self, system_service, mock_db_session, mock_redis_client):
        """Test validating system requirements."""
        # Mock database check
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        
        # Mock Redis check
        mock_redis_client.ping.return_value = True
        
        result = await system_service.validate_system_requirements()
        
        assert result["valid"] is True
        assert result["checks"]["database"] == "valid"
        assert result["checks"]["redis"] == "valid"
        assert result["checks"]["emergency_stop"] == "valid"
    
    @pytest.mark.asyncio
    async def test_validate_system_requirements_invalid(self, system_service, mock_db_session, mock_redis_client):
        """Test validating system requirements with invalid state."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        
        # Mock Redis error
        mock_redis_client.ping.side_effect = Exception("Redis error")
        
        result = await system_service.validate_system_requirements()
        
        assert result["valid"] is False
        assert result["checks"]["database"] == "invalid"
        assert result["checks"]["redis"] == "invalid"
        assert result["checks"]["emergency_stop"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_validate_account_state(self, system_service, mock_db_session, sample_account, sample_risk_profile):
        """Test validating account state."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await system_service.validate_account_state("test-account-123")
        
        assert result["valid"] is True
        assert result["account"]["active"] is True
        assert result["risk_profile"]["emergency_stop_active"] is False
    
    @pytest.mark.asyncio
    async def test_validate_account_state_invalid(self, system_service, mock_db_session, sample_account, sample_risk_profile):
        """Test validating account state with invalid state."""
        sample_account.is_active = False
        sample_risk_profile.emergency_stop_active = True
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_account
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        
        result = await system_service.validate_account_state("test-account-123")
        
        assert result["valid"] is False
        assert result["account"]["active"] is False
        assert result["risk_profile"]["emergency_stop_active"] is True


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_activate_emergency_stop_database_error(self, system_service, mock_db_session, mock_redis_client):
        """Test emergency stop activation with database error."""
        mock_db_session.execute.side_effect = Exception("Database error")
        
        with pytest.raises(SystemError, match="Database error"):
            await system_service.activate_emergency_stop("test-account-123", "Test reason")
    
    @pytest.mark.asyncio
    async def test_activate_emergency_stop_redis_error(self, system_service, mock_db_session, 
                                                     mock_redis_client, sample_risk_profile):
        """Test emergency stop activation with Redis error."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        with pytest.raises(SystemError, match="Redis error"):
            await system_service.activate_emergency_stop("test-account-123", "Test reason")
    
    @pytest.mark.asyncio
    async def test_deactivate_emergency_stop_database_error(self, system_service, mock_db_session, 
                                                          sample_risk_profile):
        """Test emergency stop deactivation with database error."""
        sample_risk_profile.emergency_stop_active = True
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_risk_profile
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with pytest.raises(SystemError, match="Database error"):
            await system_service.deactivate_emergency_stop("test-account-123")
    
    @pytest.mark.asyncio
    async def test_pause_trading_redis_error(self, system_service, mock_redis_client):
        """Test trading pause with Redis error."""
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        with pytest.raises(SystemError, match="Redis error"):
            await system_service.pause_trading("test-account-123", "Test reason")
    
    @pytest.mark.asyncio
    async def test_resume_trading_redis_error(self, system_service, mock_redis_client):
        """Test trading resume with Redis error."""
        mock_redis_client.delete.side_effect = Exception("Redis error")
        
        with pytest.raises(SystemError, match="Redis error"):
            await system_service.resume_trading("test-account-123")
    
    @pytest.mark.asyncio
    async def test_perform_health_check_multiple_errors(self, system_service, mock_db_session, mock_redis_client):
        """Test health check with multiple errors."""
        mock_db_session.execute.side_effect = Exception("Database error")
        mock_redis_client.ping.side_effect = Exception("Redis error")
        
        result = await system_service.perform_health_check()
        
        assert result["overall_status"] == "critical"
        assert result["checks"]["database"] == "unhealthy"
        assert result["checks"]["redis"] == "unhealthy"
        assert result["checks"]["emergency_stop"] == "unknown"
