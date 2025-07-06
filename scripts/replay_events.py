#!/usr/bin/env python3
"""
Event Replay CLI Tool
Command-line interface for replaying events in the trading system
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import List, Optional

# Add the src directory to the path
sys.path.insert(0, '../src')

from cqrs.event_replay import EventReplayManager
from cqrs.base import EventStore, EventBus
from services.trading.events import *  # Import all trading events


async def main():
    parser = argparse.ArgumentParser(description="Event Replay CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Replay events command
    replay_parser = subparsers.add_parser("replay", help="Replay events")
    replay_parser.add_argument("--from-date", help="Start date (ISO format)")
    replay_parser.add_argument("--to-date", help="End date (ISO format)")
    replay_parser.add_argument("--aggregate-ids", nargs="+", help="Specific aggregate IDs")
    replay_parser.add_argument("--event-types", nargs="+", help="Specific event types")
    replay_parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    replay_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    # Replay aggregate command
    aggregate_parser = subparsers.add_parser("aggregate", help="Replay specific aggregate")
    aggregate_parser.add_argument("aggregate_id", help="Aggregate ID to replay")
    aggregate_parser.add_argument("snapshot_version", type=int, help="Snapshot version to start from")
    aggregate_parser.add_argument("--to-version", type=int, help="Version to replay to")
    
    # Test scenarios command
    scenario_parser = subparsers.add_parser("scenario", help="Replay test scenarios")
    scenario_parser.add_argument("scenario", choices=["trading_day", "market_crash", "strategy_backtest"], 
                                help="Test scenario to replay")
    scenario_parser.add_argument("--from-date", help="Override start date")
    scenario_parser.add_argument("--to-date", help="Override end date")
    
    # System restore command
    restore_parser = subparsers.add_parser("restore", help="Restore system state")
    restore_parser.add_argument("restore_point", 
                               choices=["start_of_day", "before_crash", "yesterday_close"],
                               help="Restore point")
    restore_parser.add_argument("--execute", action="store_true", help="Actually execute restore")
    
    # List events command
    list_parser = subparsers.add_parser("list", help="List events without replaying")
    list_parser.add_argument("--from-date", help="Start date (ISO format)")
    list_parser.add_argument("--to-date", help="End date (ISO format)")
    list_parser.add_argument("--aggregate-ids", nargs="+", help="Specific aggregate IDs")
    list_parser.add_argument("--event-types", nargs="+", help="Specific event types")
    list_parser.add_argument("--limit", type=int, default=100, help="Limit number of events")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize replay manager (you'll need to implement this based on your setup)
    replay_manager = await initialize_replay_manager()
    
    try:
        if args.command == "replay":
            await handle_replay_command(replay_manager, args)
        elif args.command == "aggregate":
            await handle_aggregate_command(replay_manager, args)
        elif args.command == "scenario":
            await handle_scenario_command(replay_manager, args)
        elif args.command == "restore":
            await handle_restore_command(replay_manager, args)
        elif args.command == "list":
            await handle_list_command(replay_manager, args)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def initialize_replay_manager():
    """Initialize the replay manager with your event store and handlers"""
    # This is a placeholder - you'll need to implement this based on your setup
    # from your actual event store and bus implementations
    
    # Placeholder implementations
    class MockEventStore:
        async def get_all_events(self):
            return []
        
        async def get_events_after_version(self, aggregate_id: str, version: int):
            return []
    
    class MockEventBus:
        pass
    
    class MockAggregateRepository:
        async def get_by_id(self, aggregate_id: str):
            return None
        
        async def save(self, aggregate):
            pass
    
    event_store = MockEventStore()
    event_bus = MockEventBus()
    aggregate_repository = MockAggregateRepository()
    
    replay_manager = EventReplayManager(event_store, event_bus, aggregate_repository)
    
    # Register replay handlers for trading events
    # You'll need to implement these handlers based on your requirements
    handlers = {
        "OrderPlacedEvent": [],
        "OrderFilledEvent": [],
        "OrderCancelledEvent": [],
        "TradeExecutedEvent": [],
        "StrategyExecutedEvent": [],
        "SignalGeneratedEvent": []
    }
    
    replay_manager.register_replay_handlers(handlers)
    
    return replay_manager


async def handle_replay_command(replay_manager, args):
    """Handle the replay command"""
    print("Starting event replay...")
    
    result = await replay_manager.replay_engine.replay_events(
        from_timestamp=datetime.fromisoformat(args.from_date) if args.from_date else None,
        to_timestamp=datetime.fromisoformat(args.to_date) if args.to_date else None,
        aggregate_ids=args.aggregate_ids,
        event_types=args.event_types,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    print_replay_results(result)


async def handle_aggregate_command(replay_manager, args):
    """Handle the aggregate replay command"""
    print(f"Replaying aggregate {args.aggregate_id} from version {args.snapshot_version}...")
    
    result = await replay_manager.snapshot_engine.replay_from_snapshot(
        aggregate_id=args.aggregate_id,
        snapshot_version=args.snapshot_version,
        to_version=args.to_version
    )
    
    print_aggregate_replay_results(result)


async def handle_scenario_command(replay_manager, args):
    """Handle the scenario replay command"""
    print(f"Replaying scenario: {args.scenario}")
    
    from_timestamp = None
    to_timestamp = None
    
    if args.from_date:
        from_timestamp = datetime.fromisoformat(args.from_date)
    if args.to_date:
        to_timestamp = datetime.fromisoformat(args.to_date)
    
    result = await replay_manager.replay_for_testing(
        test_scenario=args.scenario,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp
    )
    
    print_replay_results(result)


async def handle_restore_command(replay_manager, args):
    """Handle the system restore command"""
    print(f"Restoring system to point: {args.restore_point}")
    
    result = await replay_manager.restore_system_state(
        restore_point=args.restore_point,
        dry_run=not args.execute
    )
    
    print_replay_results(result)


async def handle_list_command(replay_manager, args):
    """Handle the list events command"""
    print("Listing events...")
    
    result = await replay_manager.replay_engine.replay_events(
        from_timestamp=datetime.fromisoformat(args.from_date) if args.from_date else None,
        to_timestamp=datetime.fromisoformat(args.to_date) if args.to_date else None,
        aggregate_ids=args.aggregate_ids,
        event_types=args.event_types,
        dry_run=True
    )
    
    print_list_results(result, args.limit)


def print_replay_results(result):
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


def print_aggregate_replay_results(result):
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


def print_list_results(result, limit):
    """Print list results"""
    print("\n" + "="*50)
    print("EVENT LISTING RESULTS")
    print("="*50)
    
    print(f"Total events found: {result['total_events']}")
    
    if result.get("event_type_counts"):
        print("\nEvent type breakdown:")
        for event_type, count in result["event_type_counts"].items():
            print(f"  {event_type}: {count}")
    
    if result.get("aggregate_counts"):
        print(f"\nTop {limit} aggregates by event count:")
        sorted_aggregates = sorted(
            result["aggregate_counts"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        for aggregate_id, count in sorted_aggregates:
            print(f"  {aggregate_id}: {count}")
    
    if result.get("first_event"):
        print(f"\nFirst event: {result['first_event']}")
    if result.get("last_event"):
        print(f"Last event: {result['last_event']}")
    
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main()) 