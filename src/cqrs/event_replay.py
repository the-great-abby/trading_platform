"""
Event Replay System for CQRS Trading Platform
Handles replaying events for testing, debugging, and system restoration
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID

from .base import Event, EventStore, EventBus, EventHandler
from .aggregate_repository import AggregateRepository


logger = logging.getLogger(__name__)


class EventReplayEngine:
    """Engine for replaying events from the event store"""
    
    def __init__(self, event_store: EventStore, event_bus: EventBus):
        self.event_store = event_store
        self.event_bus = event_bus
        self.replay_handlers: Dict[str, List[EventHandler]] = {}
        self.is_replaying = False
        
    def register_replay_handler(self, event_type: str, handler: EventHandler):
        """Register a handler for event replay"""
        if event_type not in self.replay_handlers:
            self.replay_handlers[event_type] = []
        self.replay_handlers[event_type].append(handler)
        logger.info(f"Registered replay handler for event type: {event_type}")
    
    async def replay_events(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        aggregate_ids: Optional[List[str]] = None,
        event_types: Optional[List[str]] = None,
        batch_size: int = 1000,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Replay events with various filters
        
        Args:
            from_timestamp: Start timestamp for replay
            to_timestamp: End timestamp for replay
            aggregate_ids: Specific aggregate IDs to replay
            event_types: Specific event types to replay
            batch_size: Number of events to process in each batch
            dry_run: If True, don't actually replay events, just count them
            
        Returns:
            Dictionary with replay statistics
        """
        logger.info(f"Starting event replay from {from_timestamp} to {to_timestamp}")
        
        if self.is_replaying:
            raise RuntimeError("Event replay already in progress")
        
        self.is_replaying = True
        start_time = datetime.utcnow()
        
        try:
            # Get events from event store
            events = await self._get_events_for_replay(
                from_timestamp, to_timestamp, aggregate_ids, event_types
            )
            
            if not events:
                logger.info("No events found for replay")
                return {
                    "total_events": 0,
                    "processed_events": 0,
                    "errors": 0,
                    "duration": 0,
                    "dry_run": dry_run
                }
            
            logger.info(f"Found {len(events)} events to replay")
            
            if dry_run:
                return await self._dry_run_replay(events)
            
            # Process events in batches
            return await self._process_events_in_batches(events, batch_size, start_time)
            
        finally:
            self.is_replaying = False
    
    async def _get_events_for_replay(
        self,
        from_timestamp: Optional[datetime],
        to_timestamp: Optional[datetime],
        aggregate_ids: Optional[List[str]],
        event_types: Optional[List[str]]
    ) -> List[Event]:
        """Get events from event store based on filters"""
        # This would be implemented based on your specific event store
        # For now, we'll use a placeholder implementation
        
        all_events = await self.event_store.get_all_events()
        
        # Apply filters
        filtered_events = []
        
        for event in all_events:
            # Timestamp filter
            if from_timestamp and event.timestamp < from_timestamp:
                continue
            if to_timestamp and event.timestamp > to_timestamp:
                continue
            
            # Aggregate ID filter
            if aggregate_ids and event.aggregate_id not in aggregate_ids:
                continue
            
            # Event type filter
            if event_types and type(event).__name__ not in event_types:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp and version
        filtered_events.sort(key=lambda e: (e.timestamp, e.version))
        
        return filtered_events
    
    async def _dry_run_replay(self, events: List[Event]) -> Dict[str, Any]:
        """Perform a dry run to count events without actually replaying"""
        event_type_counts = {}
        aggregate_counts = {}
        
        for event in events:
            event_type = type(event).__name__
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            if event.aggregate_id:
                aggregate_counts[event.aggregate_id] = aggregate_counts.get(event.aggregate_id, 0) + 1
        
        return {
            "total_events": len(events),
            "processed_events": 0,
            "errors": 0,
            "duration": 0,
            "dry_run": True,
            "event_type_counts": event_type_counts,
            "aggregate_counts": aggregate_counts,
            "first_event": events[0].timestamp if events else None,
            "last_event": events[-1].timestamp if events else None
        }
    
    async def _process_events_in_batches(
        self, events: List[Event], batch_size: int, start_time: datetime
    ) -> Dict[str, Any]:
        """Process events in batches for better performance"""
        total_events = len(events)
        processed_events = 0
        errors = 0
        error_details = []
        
        for i in range(0, total_events, batch_size):
            batch = events[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: events {i+1}-{min(i+batch_size, total_events)}")
            
            for event in batch:
                try:
                    await self._replay_single_event(event)
                    processed_events += 1
                except Exception as e:
                    errors += 1
                    error_details.append({
                        "event_id": str(event.event_id),
                        "aggregate_id": event.aggregate_id,
                        "event_type": type(event).__name__,
                        "timestamp": event.timestamp.isoformat(),
                        "error": str(e)
                    })
                    logger.error(f"Error replaying event {event.event_id}: {e}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Event replay completed: {processed_events} processed, {errors} errors in {duration:.2f}s")
        
        return {
            "total_events": total_events,
            "processed_events": processed_events,
            "errors": errors,
            "duration": duration,
            "dry_run": False,
            "error_details": error_details,
            "success_rate": (processed_events / total_events * 100) if total_events > 0 else 0
        }
    
    async def _replay_single_event(self, event: Event):
        """Replay a single event"""
        event_type = type(event).__name__
        
        # Find handlers for this event type
        handlers = self.replay_handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No replay handlers registered for event type: {event_type}")
            return
        
        # Execute all handlers for this event
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Handler {handler.__class__.__name__} failed for event {event.event_id}: {e}")
                raise


class SnapshotReplayEngine:
    """Engine for replaying from snapshots"""
    
    def __init__(self, event_store: EventStore, aggregate_repository: AggregateRepository):
        self.event_store = event_store
        self.aggregate_repository = aggregate_repository
    
    async def replay_from_snapshot(
        self,
        aggregate_id: str,
        snapshot_version: int,
        to_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Replay events for an aggregate from a specific snapshot version
        
        Args:
            aggregate_id: ID of the aggregate to replay
            snapshot_version: Version to start replaying from
            to_version: Version to replay to (None for latest)
            
        Returns:
            Dictionary with replay statistics
        """
        logger.info(f"Replaying aggregate {aggregate_id} from version {snapshot_version}")
        
        # Get events after the snapshot version
        events = await self.event_store.get_events_after_version(
            aggregate_id, snapshot_version
        )
        
        if to_version:
            events = [e for e in events if e.version <= to_version]
        
        if not events:
            logger.info(f"No events to replay for aggregate {aggregate_id}")
            return {
                "aggregate_id": aggregate_id,
                "events_replayed": 0,
                "final_version": snapshot_version
            }
        
        # Replay events to rebuild the aggregate
        aggregate = await self.aggregate_repository.get_by_id(aggregate_id)
        if not aggregate:
            logger.warning(f"Aggregate {aggregate_id} not found")
            return {
                "aggregate_id": aggregate_id,
                "events_replayed": 0,
                "error": "Aggregate not found"
            }
        
        # Apply events to rebuild state
        for event in events:
            aggregate.apply(event)
        
        # Save the rebuilt aggregate
        await self.aggregate_repository.save(aggregate)
        
        logger.info(f"Replayed {len(events)} events for aggregate {aggregate_id}")
        
        return {
            "aggregate_id": aggregate_id,
            "events_replayed": len(events),
            "final_version": aggregate.version,
            "start_version": snapshot_version,
            "end_version": aggregate.version
        }


class EventReplayCLI:
    """Command-line interface for event replay operations"""
    
    def __init__(self, replay_engine: EventReplayEngine, snapshot_engine: SnapshotReplayEngine):
        self.replay_engine = replay_engine
        self.snapshot_engine = snapshot_engine
    
    async def replay_events_cli(self, args: Dict[str, Any]):
        """CLI interface for event replay"""
        from_timestamp = None
        to_timestamp = None
        
        if args.get("from_date"):
            from_timestamp = datetime.fromisoformat(args["from_date"])
        if args.get("to_date"):
            to_timestamp = datetime.fromisoformat(args["to_date"])
        
        result = await self.replay_engine.replay_events(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            aggregate_ids=args.get("aggregate_ids"),
            event_types=args.get("event_types"),
            batch_size=args.get("batch_size", 1000),
            dry_run=args.get("dry_run", False)
        )
        
        self._print_replay_results(result)
    
    async def replay_aggregate_cli(self, args: Dict[str, Any]):
        """CLI interface for aggregate replay"""
        result = await self.snapshot_engine.replay_from_snapshot(
            aggregate_id=args["aggregate_id"],
            snapshot_version=args["snapshot_version"],
            to_version=args.get("to_version")
        )
        
        self._print_aggregate_replay_results(result)
    
    def _print_replay_results(self, result: Dict[str, Any]):
        """Print replay results in a formatted way"""
        print("\n" + "="*50)
        print("EVENT REPLAY RESULTS")
        print("="*50)
        
        if result.get("dry_run"):
            print(f"DRY RUN - No events were actually replayed")
            print(f"Total events found: {result['total_events']}")
            
            if result.get("event_type_counts"):
                print("\nEvent type breakdown:")
                for event_type, count in result["event_type_counts"].items():
                    print(f"  {event_type}: {count}")
            
            if result.get("aggregate_counts"):
                print(f"\nTop 10 aggregates by event count:")
                sorted_aggregates = sorted(
                    result["aggregate_counts"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
                for aggregate_id, count in sorted_aggregates:
                    print(f"  {aggregate_id}: {count}")
        else:
            print(f"Total events: {result['total_events']}")
            print(f"Processed events: {result['processed_events']}")
            print(f"Errors: {result['errors']}")
            print(f"Success rate: {result['success_rate']:.2f}%")
            print(f"Duration: {result['duration']:.2f} seconds")
            
            if result.get("error_details"):
                print(f"\nError details:")
                for error in result["error_details"][:5]:  # Show first 5 errors
                    print(f"  Event {error['event_id']}: {error['error']}")
        
        print("="*50)
    
    def _print_aggregate_replay_results(self, result: Dict[str, Any]):
        """Print aggregate replay results"""
        print("\n" + "="*50)
        print("AGGREGATE REPLAY RESULTS")
        print("="*50)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Aggregate ID: {result['aggregate_id']}")
            print(f"Events replayed: {result['events_replayed']}")
            print(f"Final version: {result['final_version']}")
            if result.get("start_version") and result.get("end_version"):
                print(f"Version range: {result['start_version']} -> {result['end_version']}")
        
        print("="*50)


class EventReplayManager:
    """High-level manager for event replay operations"""
    
    def __init__(
        self,
        event_store: EventStore,
        event_bus: EventBus,
        aggregate_repository: AggregateRepository
    ):
        self.replay_engine = EventReplayEngine(event_store, event_bus)
        self.snapshot_engine = SnapshotReplayEngine(event_store, aggregate_repository)
        self.cli = EventReplayCLI(self.replay_engine, self.snapshot_engine)
    
    def register_replay_handlers(self, handlers: Dict[str, List[EventHandler]]):
        """Register multiple replay handlers at once"""
        for event_type, handler_list in handlers.items():
            for handler in handler_list:
                self.replay_engine.register_replay_handler(event_type, handler)
    
    async def replay_for_testing(
        self,
        test_scenario: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Replay events for testing specific scenarios"""
        logger.info(f"Replaying events for test scenario: {test_scenario}")
        
        # Define test scenarios
        scenarios = {
            "trading_day": {
                "from_timestamp": datetime.utcnow().replace(hour=9, minute=30, second=0),
                "to_timestamp": datetime.utcnow().replace(hour=16, minute=0, second=0),
                "event_types": ["OrderPlacedEvent", "OrderFilledEvent", "TradeExecutedEvent"]
            },
            "market_crash": {
                "event_types": ["OrderCancelledEvent", "RiskLimitExceededEvent"],
                "batch_size": 500
            },
            "strategy_backtest": {
                "event_types": ["SignalGeneratedEvent", "StrategyExecutedEvent"],
                "batch_size": 1000
            }
        }
        
        scenario_config = scenarios.get(test_scenario, {})
        
        # Override with provided timestamps if specified
        if from_timestamp:
            scenario_config["from_timestamp"] = from_timestamp
        if to_timestamp:
            scenario_config["to_timestamp"] = to_timestamp
        
        return await self.replay_engine.replay_events(**scenario_config)
    
    async def restore_system_state(
        self,
        restore_point: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Restore system to a specific point in time"""
        logger.info(f"Restoring system to point: {restore_point}")
        
        # Define restore points
        restore_points = {
            "start_of_day": datetime.utcnow().replace(hour=9, minute=30, second=0),
            "before_crash": datetime.utcnow() - timedelta(hours=2),
            "yesterday_close": datetime.utcnow() - timedelta(days=1)
        }
        
        target_timestamp = restore_points.get(restore_point)
        if not target_timestamp:
            raise ValueError(f"Unknown restore point: {restore_point}")
        
        return await self.replay_engine.replay_events(
            to_timestamp=target_timestamp,
            dry_run=dry_run
        ) 