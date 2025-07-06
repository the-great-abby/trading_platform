"""
Unit tests for event replay system
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.cqrs.event_replay import (
    EventReplayEngine,
    SnapshotReplayEngine,
    EventReplayManager,
    ReplayConfig,
    ReplayStatistics
)
from src.services.trading.events import OrderPlacedEvent, OrderFilledEvent


class TestEventReplayEngine:
    """Test EventReplayEngine"""
    
    @pytest.fixture
    def mock_event_store(self):
        mock = AsyncMock()
        mock.get_events.return_value = [
            OrderPlacedEvent(
                aggregate_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=100
            ),
            OrderFilledEvent(
                aggregate_id="order-123",
                filled_quantity=100,
                fill_price=Decimal("150.00")
            )
        ]
        return mock
    
    @pytest.fixture
    def mock_event_bus(self):
        return AsyncMock()
    
    @pytest.fixture
    def replay_engine(self, mock_event_store, mock_event_bus):
        return EventReplayEngine(
            event_store=mock_event_store,
            event_bus=mock_event_bus
        )
    
    @pytest.mark.asyncio
    async def test_replay_events_basic(self, replay_engine, mock_event_store, mock_event_bus):
        """Test basic event replay"""
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            event_types=["OrderPlacedEvent", "OrderFilledEvent"]
        )
        
        result = await replay_engine.replay_events(config)
        
        assert result.total_events == 2
        assert result.successful_events == 2
        assert result.failed_events == 0
        assert result.start_time is not None
        assert result.end_time is not None
        
        # Verify event store was called
        mock_event_store.get_events.assert_called_once()
        
        # Verify events were published
        assert mock_event_bus.publish.call_count == 2
    
    @pytest.mark.asyncio
    async def test_replay_events_with_filters(self, replay_engine, mock_event_store):
        """Test event replay with filters"""
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            event_types=["OrderPlacedEvent"],
            aggregate_ids=["order-123"]
        )
        
        await replay_engine.replay_events(config)
        
        # Verify filters were passed to event store
        call_args = mock_event_store.get_events.call_args
        assert call_args is not None
        kwargs = call_args.kwargs
        assert kwargs["event_types"] == ["OrderPlacedEvent"]
        assert kwargs["aggregate_ids"] == ["order-123"]
    
    @pytest.mark.asyncio
    async def test_replay_events_dry_run(self, replay_engine, mock_event_bus):
        """Test event replay in dry run mode"""
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            dry_run=True
        )
        
        result = await replay_engine.replay_events(config)
        
        assert result.total_events == 2
        assert result.successful_events == 2
        assert result.failed_events == 0
        
        # Verify no events were actually published in dry run
        mock_event_bus.publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_replay_events_with_error(self, replay_engine, mock_event_bus):
        """Test event replay with handler error"""
        # Make event bus raise an error
        mock_event_bus.publish.side_effect = Exception("Handler error")
        
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        result = await replay_engine.replay_events(config)
        
        assert result.total_events == 2
        assert result.successful_events == 0
        assert result.failed_events == 2
        assert len(result.errors) == 2
    
    @pytest.mark.asyncio
    async def test_replay_events_batch_processing(self, replay_engine, mock_event_store):
        """Test event replay with batch processing"""
        # Create more events
        events = [
            OrderPlacedEvent(
                aggregate_id=f"order-{i}",
                symbol="AAPL",
                side="BUY",
                quantity=100
            ) for i in range(10)
        ]
        mock_event_store.get_events.return_value = events
        
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            batch_size=3
        )
        
        result = await replay_engine.replay_events(config)
        
        assert result.total_events == 10
        assert result.successful_events == 10
        assert result.failed_events == 0


class TestSnapshotReplayEngine:
    """Test SnapshotReplayEngine"""
    
    @pytest.fixture
    def mock_snapshot_store(self):
        mock = AsyncMock()
        mock.get_snapshot.return_value = {
            "aggregate_id": "order-123",
            "version": 5,
            "data": {"status": "filled", "quantity": 100}
        }
        return mock
    
    @pytest.fixture
    def mock_event_store(self):
        return AsyncMock()
    
    @pytest.fixture
    def snapshot_engine(self, mock_snapshot_store, mock_event_store):
        return SnapshotReplayEngine(
            snapshot_store=mock_snapshot_store,
            event_store=mock_event_store
        )
    
    @pytest.mark.asyncio
    async def test_replay_from_snapshot(self, snapshot_engine, mock_snapshot_store, mock_event_store):
        """Test replaying from snapshot"""
        mock_event_store.get_events.return_value = [
            OrderFilledEvent(
                aggregate_id="order-123",
                filled_quantity=100,
                fill_price=Decimal("150.00")
            )
        ]
        
        config = ReplayConfig(
            aggregate_ids=["order-123"],
            use_snapshots=True
        )
        
        result = await snapshot_engine.replay_from_snapshot(config)
        
        assert result.total_events == 1
        assert result.successful_events == 1
        assert result.failed_events == 0
        
        # Verify snapshot was retrieved
        mock_snapshot_store.get_snapshot.assert_called_once_with("order-123")
        
        # Verify events after snapshot were retrieved
        mock_event_store.get_events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_replay_from_snapshot_no_snapshot(self, snapshot_engine, mock_snapshot_store):
        """Test replaying when no snapshot exists"""
        mock_snapshot_store.get_snapshot.return_value = None
        
        config = ReplayConfig(
            aggregate_ids=["order-123"],
            use_snapshots=True
        )
        
        result = await snapshot_engine.replay_from_snapshot(config)
        
        assert result.total_events == 0
        assert result.successful_events == 0
        assert result.failed_events == 0


class TestEventReplayManager:
    """Test EventReplayManager"""
    
    @pytest.fixture
    def mock_replay_engine(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_snapshot_engine(self):
        return AsyncMock()
    
    @pytest.fixture
    def replay_manager(self, mock_replay_engine, mock_snapshot_engine):
        return EventReplayManager(
            replay_engine=mock_replay_engine,
            snapshot_engine=mock_snapshot_engine
        )
    
    @pytest.mark.asyncio
    async def test_replay_events_basic(self, replay_manager, mock_replay_engine):
        """Test basic replay through manager"""
        mock_replay_engine.replay_events.return_value = ReplayStatistics(
            total_events=5,
            successful_events=5,
            failed_events=0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        result = await replay_manager.replay_events(config)
        
        assert result.total_events == 5
        assert result.successful_events == 5
        assert result.failed_events == 0
        
        mock_replay_engine.replay_events.assert_called_once_with(config)
    
    @pytest.mark.asyncio
    async def test_replay_events_with_snapshots(self, replay_manager, mock_snapshot_engine):
        """Test replay with snapshots through manager"""
        mock_snapshot_engine.replay_from_snapshot.return_value = ReplayStatistics(
            total_events=3,
            successful_events=3,
            failed_events=0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        config = ReplayConfig(
            aggregate_ids=["order-123"],
            use_snapshots=True
        )
        
        result = await replay_manager.replay_events(config)
        
        assert result.total_events == 3
        assert result.successful_events == 3
        assert result.failed_events == 0
        
        mock_snapshot_engine.replay_from_snapshot.assert_called_once_with(config)
    
    @pytest.mark.asyncio
    async def test_replay_test_scenario(self, replay_manager, mock_replay_engine):
        """Test replaying predefined test scenario"""
        mock_replay_engine.replay_events.return_value = ReplayStatistics(
            total_events=10,
            successful_events=10,
            failed_events=0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        result = await replay_manager.replay_test_scenario("sma_crossover_test")
        
        assert result.total_events == 10
        assert result.successful_events == 10
        assert result.failed_events == 0
        
        # Verify scenario config was used
        call_args = mock_replay_engine.replay_events.call_args
        assert call_args is not None
        config = call_args.args[0]
        assert config.scenario_name == "sma_crossover_test"
    
    @pytest.mark.asyncio
    async def test_replay_test_scenario_invalid(self, replay_manager):
        """Test replaying invalid test scenario"""
        with pytest.raises(ValueError, match="Unknown test scenario"):
            await replay_manager.replay_test_scenario("invalid_scenario")


class TestReplayConfig:
    """Test ReplayConfig"""
    
    def test_replay_config_creation(self):
        """Test creating replay config"""
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            event_types=["OrderPlacedEvent"],
            aggregate_ids=["order-123"],
            dry_run=True,
            batch_size=100
        )
        
        assert config.start_date is not None
        assert config.end_date is not None
        assert config.event_types == ["OrderPlacedEvent"]
        assert config.aggregate_ids == ["order-123"]
        assert config.dry_run is True
        assert config.batch_size == 100
    
    def test_replay_config_defaults(self):
        """Test replay config with defaults"""
        config = ReplayConfig()
        
        assert config.start_date is None
        assert config.end_date is None
        assert config.event_types is None
        assert config.aggregate_ids is None
        assert config.dry_run is False
        assert config.batch_size == 1000
        assert config.use_snapshots is False
    
    def test_replay_config_validation(self):
        """Test replay config validation"""
        # Valid config
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        assert config.start_date < config.end_date
        
        # Invalid date range
        with pytest.raises(ValueError):
            ReplayConfig(
                start_date=datetime.now(),
                end_date=datetime.now() - timedelta(days=1)
            )


class TestReplayStatistics:
    """Test ReplayStatistics"""
    
    def test_replay_statistics_creation(self):
        """Test creating replay statistics"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        stats = ReplayStatistics(
            total_events=100,
            successful_events=95,
            failed_events=5,
            start_time=start_time,
            end_time=end_time,
            errors=["Error 1", "Error 2"]
        )
        
        assert stats.total_events == 100
        assert stats.successful_events == 95
        assert stats.failed_events == 5
        assert stats.start_time == start_time
        assert stats.end_time == end_time
        assert len(stats.errors) == 2
        assert stats.duration == 10.0
    
    def test_replay_statistics_calculation(self):
        """Test replay statistics calculations"""
        stats = ReplayStatistics(
            total_events=100,
            successful_events=90,
            failed_events=10,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=5)
        )
        
        assert stats.success_rate == 0.9
        assert stats.failure_rate == 0.1
        assert stats.duration == 5.0
    
    def test_replay_statistics_zero_events(self):
        """Test replay statistics with zero events"""
        stats = ReplayStatistics(
            total_events=0,
            successful_events=0,
            failed_events=0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        assert stats.success_rate == 0.0
        assert stats.failure_rate == 0.0
        assert stats.duration == 0.0


class TestEventReplayIntegration:
    """Integration tests for event replay"""
    
    @pytest.mark.asyncio
    async def test_full_replay_workflow(self):
        """Test complete replay workflow"""
        # Mock dependencies
        mock_event_store = AsyncMock()
        mock_event_bus = AsyncMock()
        mock_snapshot_store = AsyncMock()
        
        # Create test events
        events = [
            OrderPlacedEvent(
                aggregate_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=100
            ),
            OrderFilledEvent(
                aggregate_id="order-123",
                filled_quantity=100,
                fill_price=Decimal("150.00")
            )
        ]
        mock_event_store.get_events.return_value = events
        
        # Create engines
        replay_engine = EventReplayEngine(mock_event_store, mock_event_bus)
        snapshot_engine = SnapshotReplayEngine(mock_snapshot_store, mock_event_store)
        manager = EventReplayManager(replay_engine, snapshot_engine)
        
        # Execute replay
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            dry_run=True
        )
        
        result = await manager.replay_events(config)
        
        # Verify results
        assert result.total_events == 2
        assert result.successful_events == 2
        assert result.failed_events == 0
        
        # Verify no events were published in dry run
        mock_event_bus.publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_replay_with_error_handling(self):
        """Test replay with error handling"""
        mock_event_store = AsyncMock()
        mock_event_bus = AsyncMock()
        
        # Make event bus fail on second event
        mock_event_bus.publish.side_effect = [
            None,  # First event succeeds
            Exception("Handler error")  # Second event fails
        ]
        
        events = [
            OrderPlacedEvent(
                aggregate_id="order-123",
                symbol="AAPL",
                side="BUY",
                quantity=100
            ),
            OrderFilledEvent(
                aggregate_id="order-123",
                filled_quantity=100,
                fill_price=Decimal("150.00")
            )
        ]
        mock_event_store.get_events.return_value = events
        
        replay_engine = EventReplayEngine(mock_event_store, mock_event_bus)
        
        config = ReplayConfig(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        result = await replay_engine.replay_events(config)
        
        assert result.total_events == 2
        assert result.successful_events == 1
        assert result.failed_events == 1
        assert len(result.errors) == 1 