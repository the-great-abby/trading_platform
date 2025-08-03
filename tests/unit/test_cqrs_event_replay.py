"""
Tests for CQRS event replay system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.cqrs.event_replay import (
    EventReplayEngine, 
    SnapshotReplayEngine, 
    EventReplayCLI, 
    EventReplayManager
)
from src.cqrs.base import Event, EventStore, EventBus, EventHandler
from src.cqrs.aggregate_repository import AggregateRepository


class MockEvent(Event):
    """Mock event for testing"""
    
    def __init__(self, event_id: str, aggregate_id: str, timestamp: datetime, version: int = 1):
        super().__init__(
            event_id=event_id,
            aggregate_id=aggregate_id,
            timestamp=timestamp,
            version=version
        )


class MockEventHandler(EventHandler):
    """Mock event handler for testing"""
    
    def __init__(self):
        self.handled_events = []
    
    async def handle(self, event: Event):
        self.handled_events.append(event)


class TestEventReplayEngine:
    """Test the EventReplayEngine"""
    
    @pytest.fixture
    def mock_event_store(self):
        """Mock event store"""
        store = Mock(spec=EventStore)
        store.get_all_events = AsyncMock()
        return store
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        bus = Mock(spec=EventBus)
        return bus
    
    @pytest.fixture
    def replay_engine(self, mock_event_store, mock_event_bus):
        """Event replay engine with mocked dependencies"""
        return EventReplayEngine(mock_event_store, mock_event_bus)
    
    @pytest.fixture
    def sample_events(self):
        """Sample events for testing"""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        return [
            MockEvent("event-1", "aggregate-1", base_time, 1),
            MockEvent("event-2", "aggregate-1", base_time + timedelta(minutes=1), 2),
            MockEvent("event-3", "aggregate-2", base_time + timedelta(minutes=2), 1),
            MockEvent("event-4", "aggregate-1", base_time + timedelta(minutes=3), 3),
            MockEvent("event-5", "aggregate-2", base_time + timedelta(minutes=4), 2),
        ]
    
    def test_replay_engine_initialization(self, replay_engine, mock_event_store, mock_event_bus):
        """Test EventReplayEngine initialization"""
        assert replay_engine.event_store == mock_event_store
        assert replay_engine.event_bus == mock_event_bus
        assert replay_engine.replay_handlers == {}
        assert replay_engine.is_replaying is False
    
    def test_register_replay_handler(self, replay_engine):
        """Test registering replay handlers"""
        handler = MockEventHandler()
        
        replay_engine.register_replay_handler("MockEvent", handler)
        
        assert "MockEvent" in replay_engine.replay_handlers
        assert handler in replay_engine.replay_handlers["MockEvent"]
    
    def test_register_multiple_handlers(self, replay_engine):
        """Test registering multiple handlers for same event type"""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()
        
        replay_engine.register_replay_handler("MockEvent", handler1)
        replay_engine.register_replay_handler("MockEvent", handler2)
        
        assert len(replay_engine.replay_handlers["MockEvent"]) == 2
        assert handler1 in replay_engine.replay_handlers["MockEvent"]
        assert handler2 in replay_engine.replay_handlers["MockEvent"]
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_success(self, mock_logger, replay_engine, sample_events):
        """Test successful event replay"""
        replay_engine.event_store.get_all_events.return_value = sample_events
        
        # Register a handler
        handler = MockEventHandler()
        replay_engine.register_replay_handler("MockEvent", handler)
        
        result = await replay_engine.replay_events()
        
        # Verify results
        assert result["total_events"] == 5
        assert result["processed_events"] == 5
        assert result["errors"] == 0
        assert result["dry_run"] is False
        
        # Verify handler was called for each event
        assert len(handler.handled_events) == 5
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_no_events(self, mock_logger, replay_engine):
        """Test replay with no events"""
        replay_engine.event_store.get_all_events.return_value = []
        
        result = await replay_engine.replay_events()
        
        assert result["total_events"] == 0
        assert result["processed_events"] == 0
        assert result["errors"] == 0
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_with_filters(self, mock_logger, replay_engine, sample_events):
        """Test replay with filters"""
        replay_engine.event_store.get_all_events.return_value = sample_events
        
        # Test timestamp filter
        from_timestamp = datetime(2024, 1, 15, 10, 1, 0)
        result = await replay_engine.replay_events(from_timestamp=from_timestamp)
        
        # Should filter out events before from_timestamp
        assert result["processed_events"] < 5
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_dry_run(self, mock_logger, replay_engine, sample_events):
        """Test dry run replay"""
        replay_engine.event_store.get_all_events.return_value = sample_events
        
        result = await replay_engine.replay_events(dry_run=True)
        
        assert result["dry_run"] is True
        assert result["processed_events"] == 0
        assert "event_type_counts" in result
        assert "aggregate_counts" in result
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_already_replaying(self, mock_logger, replay_engine):
        """Test replay when already in progress"""
        replay_engine.is_replaying = True
        
        with pytest.raises(RuntimeError, match="Event replay already in progress"):
            await replay_engine.replay_events()
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_with_errors(self, mock_logger, replay_engine, sample_events):
        """Test replay with handler errors"""
        replay_engine.event_store.get_all_events.return_value = sample_events
        
        # Create handler that raises exception
        error_handler = MockEventHandler()
        error_handler.handle = AsyncMock(side_effect=Exception("Handler error"))
        
        replay_engine.register_replay_handler("MockEvent", error_handler)
        
        result = await replay_engine.replay_events()
        
        assert result["errors"] > 0
        assert "error_details" in result
        assert len(result["error_details"]) > 0
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_events_batch_processing(self, mock_logger, replay_engine, sample_events):
        """Test batch processing of events"""
        replay_engine.event_store.get_all_events.return_value = sample_events
        
        handler = MockEventHandler()
        replay_engine.register_replay_handler("MockEvent", handler)
        
        result = await replay_engine.replay_events(batch_size=2)
        
        assert result["processed_events"] == 5
        assert len(handler.handled_events) == 5


class TestSnapshotReplayEngine:
    """Test the SnapshotReplayEngine"""
    
    @pytest.fixture
    def mock_event_store(self):
        """Mock event store"""
        store = Mock(spec=EventStore)
        store.get_events_after_version = AsyncMock()
        return store
    
    @pytest.fixture
    def mock_aggregate_repository(self):
        """Mock aggregate repository"""
        repo = Mock(spec=AggregateRepository)
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def snapshot_engine(self, mock_event_store, mock_aggregate_repository):
        """Snapshot replay engine with mocked dependencies"""
        return SnapshotReplayEngine(mock_event_store, mock_aggregate_repository)
    
    @pytest.fixture
    def mock_aggregate(self):
        """Mock aggregate for testing"""
        aggregate = Mock()
        aggregate.version = 5
        aggregate.apply = Mock()
        return aggregate
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_from_snapshot_success(self, mock_logger, snapshot_engine, mock_aggregate):
        """Test successful snapshot replay"""
        # Mock events after version
        events = [
            MockEvent("event-1", "aggregate-1", datetime.now(), 2),
            MockEvent("event-2", "aggregate-1", datetime.now(), 3),
        ]
        snapshot_engine.event_store.get_events_after_version.return_value = events
        snapshot_engine.aggregate_repository.get_by_id.return_value = mock_aggregate
        
        result = await snapshot_engine.replay_from_snapshot("aggregate-1", 1)
        
        assert result["aggregate_id"] == "aggregate-1"
        assert result["events_replayed"] == 2
        assert result["final_version"] == 5
        assert result["start_version"] == 1
        assert result["end_version"] == 5
        
        # Verify events were applied
        assert mock_aggregate.apply.call_count == 2
        snapshot_engine.aggregate_repository.save.assert_called_once_with(mock_aggregate)
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_from_snapshot_no_events(self, mock_logger, snapshot_engine):
        """Test snapshot replay with no events"""
        snapshot_engine.event_store.get_events_after_version.return_value = []
        
        result = await snapshot_engine.replay_from_snapshot("aggregate-1", 1)
        
        assert result["aggregate_id"] == "aggregate-1"
        assert result["events_replayed"] == 0
        assert result["final_version"] == 1
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_from_snapshot_aggregate_not_found(self, mock_logger, snapshot_engine):
        """Test snapshot replay with aggregate not found"""
        events = [MockEvent("event-1", "aggregate-1", datetime.now(), 2)]
        snapshot_engine.event_store.get_events_after_version.return_value = events
        snapshot_engine.aggregate_repository.get_by_id.return_value = None
        
        result = await snapshot_engine.replay_from_snapshot("aggregate-1", 1)
        
        assert result["aggregate_id"] == "aggregate-1"
        assert result["events_replayed"] == 0
        assert "error" in result
        assert result["error"] == "Aggregate not found"
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_from_snapshot_with_to_version(self, mock_logger, snapshot_engine, mock_aggregate):
        """Test snapshot replay with to_version limit"""
        events = [
            MockEvent("event-1", "aggregate-1", datetime.now(), 2),
            MockEvent("event-2", "aggregate-1", datetime.now(), 3),
            MockEvent("event-3", "aggregate-1", datetime.now(), 4),
        ]
        snapshot_engine.event_store.get_events_after_version.return_value = events
        snapshot_engine.aggregate_repository.get_by_id.return_value = mock_aggregate
        
        result = await snapshot_engine.replay_from_snapshot("aggregate-1", 1, to_version=3)
        
        assert result["events_replayed"] == 2  # Only events with version <= 3
        assert result["end_version"] == 3


class TestEventReplayCLI:
    """Test the EventReplayCLI"""
    
    @pytest.fixture
    def mock_replay_engine(self):
        """Mock replay engine"""
        engine = Mock(spec=EventReplayEngine)
        engine.replay_events = AsyncMock()
        return engine
    
    @pytest.fixture
    def mock_snapshot_engine(self):
        """Mock snapshot engine"""
        engine = Mock(spec=SnapshotReplayEngine)
        engine.replay_from_snapshot = AsyncMock()
        return engine
    
    @pytest.fixture
    def cli(self, mock_replay_engine, mock_snapshot_engine):
        """Event replay CLI with mocked dependencies"""
        return EventReplayCLI(mock_replay_engine, mock_snapshot_engine)
    
    @patch('builtins.print')
    async def test_replay_events_cli_success(self, mock_print, cli, mock_replay_engine):
        """Test successful CLI event replay"""
        mock_result = {
            "total_events": 100,
            "processed_events": 95,
            "errors": 5,
            "duration": 10.5,
            "success_rate": 95.0
        }
        mock_replay_engine.replay_events.return_value = mock_result
        
        args = {
            "from_date": "2024-01-01T00:00:00",
            "to_date": "2024-01-15T23:59:59",
            "aggregate_ids": ["agg-1", "agg-2"],
            "event_types": ["MockEvent"],
            "batch_size": 500,
            "dry_run": False
        }
        
        await cli.replay_events_cli(args)
        
        # Verify replay was called with correct parameters
        mock_replay_engine.replay_events.assert_called_once()
        call_args = mock_replay_engine.replay_events.call_args
        
        assert call_args[1]["batch_size"] == 500
        assert call_args[1]["dry_run"] is False
        assert call_args[1]["aggregate_ids"] == ["agg-1", "agg-2"]
        assert call_args[1]["event_types"] == ["MockEvent"]
        
        # Verify output was printed
        assert mock_print.call_count > 0
    
    @patch('builtins.print')
    async def test_replay_aggregate_cli_success(self, mock_print, cli, mock_snapshot_engine):
        """Test successful CLI aggregate replay"""
        mock_result = {
            "aggregate_id": "agg-1",
            "events_replayed": 10,
            "final_version": 15,
            "start_version": 5,
            "end_version": 15
        }
        mock_snapshot_engine.replay_from_snapshot.return_value = mock_result
        
        args = {
            "aggregate_id": "agg-1",
            "snapshot_version": 5,
            "to_version": 15
        }
        
        await cli.replay_aggregate_cli(args)
        
        # Verify replay was called with correct parameters
        mock_snapshot_engine.replay_from_snapshot.assert_called_once_with(
            aggregate_id="agg-1",
            snapshot_version=5,
            to_version=15
        )
        
        # Verify output was printed
        assert mock_print.call_count > 0
    
    @patch('builtins.print')
    async def test_print_replay_results_dry_run(self, mock_print, cli):
        """Test printing dry run results"""
        result = {
            "dry_run": True,
            "total_events": 100,
            "event_type_counts": {"MockEvent": 80, "OtherEvent": 20},
            "aggregate_counts": {"agg-1": 50, "agg-2": 30, "agg-3": 20},
            "first_event": datetime(2024, 1, 1),
            "last_event": datetime(2024, 1, 15)
        }
        
        cli._print_replay_results(result)
        
        # Verify dry run message was printed
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0
    
    @patch('builtins.print')
    async def test_print_replay_results_with_errors(self, mock_print, cli):
        """Test printing results with errors"""
        result = {
            "dry_run": False,
            "total_events": 100,
            "processed_events": 90,
            "errors": 10,
            "duration": 15.5,
            "success_rate": 90.0,
            "error_details": [
                {"event_id": "event-1", "error": "Handler failed"},
                {"event_id": "event-2", "error": "Database error"}
            ]
        }
        
        cli._print_replay_results(result)
        
        # Verify error information was printed
        error_calls = [call for call in mock_print.call_args_list if "Error details" in str(call)]
        assert len(error_calls) > 0


class TestEventReplayManager:
    """Test the EventReplayManager"""
    
    @pytest.fixture
    def mock_event_store(self):
        """Mock event store"""
        store = Mock(spec=EventStore)
        return store
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        bus = Mock(spec=EventBus)
        return bus
    
    @pytest.fixture
    def mock_aggregate_repository(self):
        """Mock aggregate repository"""
        repo = Mock(spec=AggregateRepository)
        return repo
    
    @pytest.fixture
    def manager(self, mock_event_store, mock_event_bus, mock_aggregate_repository):
        """Event replay manager with mocked dependencies"""
        return EventReplayManager(mock_event_store, mock_event_bus, mock_aggregate_repository)
    
    def test_manager_initialization(self, manager, mock_event_store, mock_event_bus, mock_aggregate_repository):
        """Test EventReplayManager initialization"""
        assert manager.replay_engine is not None
        assert manager.snapshot_engine is not None
        assert manager.cli is not None
    
    def test_register_replay_handlers(self, manager):
        """Test registering multiple replay handlers"""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()
        
        handlers = {
            "MockEvent": [handler1, handler2],
            "OtherEvent": [handler1]
        }
        
        manager.register_replay_handlers(handlers)
        
        # Verify handlers were registered
        assert "MockEvent" in manager.replay_engine.replay_handlers
        assert "OtherEvent" in manager.replay_engine.replay_handlers
        assert len(manager.replay_engine.replay_handlers["MockEvent"]) == 2
        assert len(manager.replay_engine.replay_handlers["OtherEvent"]) == 1
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_for_testing_trading_day(self, mock_logger, manager):
        """Test replay for trading day scenario"""
        manager.replay_engine.replay_events = AsyncMock()
        
        result = await manager.replay_for_testing("trading_day")
        
        # Verify replay was called with trading day parameters
        manager.replay_engine.replay_events.assert_called_once()
        call_args = manager.replay_engine.replay_events.call_args
        
        assert "event_types" in call_args[1]
        assert "OrderPlacedEvent" in call_args[1]["event_types"]
        assert "OrderFilledEvent" in call_args[1]["event_types"]
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_for_testing_market_crash(self, mock_logger, manager):
        """Test replay for market crash scenario"""
        manager.replay_engine.replay_events = AsyncMock()
        
        result = await manager.replay_for_testing("market_crash")
        
        # Verify replay was called with market crash parameters
        manager.replay_engine.replay_events.assert_called_once()
        call_args = manager.replay_engine.replay_events.call_args
        
        assert "event_types" in call_args[1]
        assert "OrderCancelledEvent" in call_args[1]["event_types"]
        assert call_args[1]["batch_size"] == 500
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_for_testing_strategy_backtest(self, mock_logger, manager):
        """Test replay for strategy backtest scenario"""
        manager.replay_engine.replay_events = AsyncMock()
        
        result = await manager.replay_for_testing("strategy_backtest")
        
        # Verify replay was called with strategy backtest parameters
        manager.replay_engine.replay_events.assert_called_once()
        call_args = manager.replay_engine.replay_events.call_args
        
        assert "event_types" in call_args[1]
        assert "SignalGeneratedEvent" in call_args[1]["event_types"]
        assert "StrategyExecutedEvent" in call_args[1]["event_types"]
        assert call_args[1]["batch_size"] == 1000
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_for_testing_unknown_scenario(self, mock_logger, manager):
        """Test replay for unknown scenario"""
        manager.replay_engine.replay_events = AsyncMock()
        
        result = await manager.replay_for_testing("unknown_scenario")
        
        # Should use default parameters
        manager.replay_engine.replay_events.assert_called_once()
    
    @patch('src.cqrs.event_replay.logger')
    async def test_restore_system_state(self, mock_logger, manager):
        """Test system state restoration"""
        manager.replay_engine.replay_events = AsyncMock()
        
        result = await manager.restore_system_state("start_of_day", dry_run=True)
        
        # Verify replay was called with restoration parameters
        manager.replay_engine.replay_events.assert_called_once()
        call_args = manager.replay_engine.replay_events.call_args
        
        assert call_args[1]["dry_run"] is True
        assert "to_timestamp" in call_args[1]
    
    @patch('src.cqrs.event_replay.logger')
    async def test_restore_system_state_unknown_point(self, mock_logger, manager):
        """Test system state restoration with unknown restore point"""
        with pytest.raises(ValueError, match="Unknown restore point"):
            await manager.restore_system_state("unknown_point")


class TestEventReplayEdgeCases:
    """Test edge cases for event replay system"""
    
    @pytest.fixture
    def edge_case_replay_engine(self):
        """Replay engine for edge case testing"""
        event_store = Mock(spec=EventStore)
        event_bus = Mock(spec=EventBus)
        return EventReplayEngine(event_store, event_bus)
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_with_malformed_events(self, mock_logger, edge_case_replay_engine):
        """Test replay with malformed events"""
        # Create events with missing required fields
        malformed_events = [
            Mock(),  # Not an Event
            MockEvent("event-1", None, datetime.now()),  # Missing aggregate_id
            MockEvent("event-2", "agg-1", None),  # Missing timestamp
        ]
        
        edge_case_replay_engine.event_store.get_all_events.return_value = malformed_events
        
        # Should handle gracefully
        result = await edge_case_replay_engine.replay_events()
        
        assert result["errors"] > 0
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_with_handler_timeout(self, mock_logger, edge_case_replay_engine):
        """Test replay with handler timeout"""
        events = [MockEvent("event-1", "agg-1", datetime.now())]
        edge_case_replay_engine.event_store.get_all_events.return_value = events
        
        # Create handler that times out
        timeout_handler = MockEventHandler()
        timeout_handler.handle = AsyncMock(side_effect=asyncio.TimeoutError("Handler timeout"))
        
        edge_case_replay_engine.register_replay_handler("MockEvent", timeout_handler)
        
        result = await edge_case_replay_engine.replay_events()
        
        assert result["errors"] > 0
    
    @patch('src.cqrs.event_replay.logger')
    async def test_replay_with_large_batch_size(self, mock_logger, edge_case_replay_engine):
        """Test replay with very large batch size"""
        # Create many events
        events = [MockEvent(f"event-{i}", f"agg-{i%10}", datetime.now()) for i in range(10000)]
        edge_case_replay_engine.event_store.get_all_events.return_value = events
        
        result = await edge_case_replay_engine.replay_events(batch_size=10000)
        
        assert result["total_events"] == 10000
        assert result["processed_events"] == 0  # No handlers registered


class TestEventReplayPerformance:
    """Performance tests for event replay system"""
    
    @pytest.fixture
    def performance_replay_engine(self):
        """Replay engine for performance testing"""
        event_store = Mock(spec=EventStore)
        event_bus = Mock(spec=EventBus)
        return EventReplayEngine(event_store, event_bus)
    
    @patch('src.cqrs.event_replay.logger')
    async def test_large_event_replay_performance(self, mock_logger, performance_replay_engine):
        """Test performance with large number of events"""
        import time
        
        # Create large number of events
        events = [MockEvent(f"event-{i}", f"agg-{i%100}", datetime.now()) for i in range(10000)]
        performance_replay_engine.event_store.get_all_events.return_value = events
        
        # Register fast handler
        fast_handler = MockEventHandler()
        performance_replay_engine.register_replay_handler("MockEvent", fast_handler)
        
        start_time = time.time()
        result = await performance_replay_engine.replay_events(batch_size=1000)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 10.0  # Less than 10 seconds
        assert result["processed_events"] == 10000 