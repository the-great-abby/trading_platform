"""
Event Store for CQRS Event Sourcing
Handles event persistence, retrieval, and replay functionality
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import asyncpg
from pydantic import BaseModel

from src.services.cqrs.events import BaseEvent

logger = logging.getLogger(__name__)


class EventStore:
    """Event store for persisting and retrieving events"""
    
    def __init__(self, db_conn: asyncpg.Connection):
        self.db_conn = db_conn
    
    async def create_tables(self):
        """Create event store tables if they don't exist"""
        try:
            # Events table
            await self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id UUID PRIMARY KEY,
                    aggregate_id VARCHAR(100) NOT NULL,
                    aggregate_type VARCHAR(50) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    event_version INTEGER NOT NULL DEFAULT 1,
                    event_data JSONB NOT NULL,
                    metadata JSONB,
                    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    correlation_id UUID,
                    causation_id UUID,
                    user_id VARCHAR(100),
                    session_id VARCHAR(100)
                )
            """)
            
            # Event snapshots table for performance optimization
            await self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS event_snapshots (
                    aggregate_id VARCHAR(100) NOT NULL,
                    aggregate_type VARCHAR(50) NOT NULL,
                    version INTEGER NOT NULL,
                    snapshot_data JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (aggregate_id, version)
                )
            """)
            
            # Event streams table for tracking stream positions
            await self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS event_streams (
                    stream_id VARCHAR(100) PRIMARY KEY,
                    stream_type VARCHAR(50) NOT NULL,
                    last_event_version INTEGER NOT NULL DEFAULT 0,
                    last_processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for efficient querying
            await self.db_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_aggregate 
                ON events(aggregate_id, aggregate_type, occurred_at)
            """)
            
            await self.db_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type 
                ON events(event_type, occurred_at)
            """)
            
            await self.db_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_correlation 
                ON events(correlation_id)
            """)
            
            await self.db_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_user 
                ON events(user_id, occurred_at)
            """)
            
            logger.info("Event store tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create event store tables: {e}")
            raise
    
    async def append_events(
        self, 
        aggregate_id: str, 
        aggregate_type: str, 
        events: List[BaseEvent],
        expected_version: Optional[int] = None,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Append events to the event store"""
        try:
            async with self.db_conn.transaction():
                # Check current version if expected_version is provided
                if expected_version is not None:
                    current_version = await self.get_aggregate_version(aggregate_id, aggregate_type)
                    if current_version != expected_version:
                        raise ConcurrencyError(
                            f"Expected version {expected_version}, but current version is {current_version}"
                        )
                
                # Insert events
                for i, event in enumerate(events):
                    event_id = uuid4()
                    version = (expected_version or 0) + i + 1
                    
                    # Serialize event data
                    event_data = self._serialize_event(event)
                    
                    await self.db_conn.execute("""
                        INSERT INTO events (
                            event_id, aggregate_id, aggregate_type, event_type,
                            event_version, event_data, metadata, occurred_at,
                            correlation_id, causation_id, user_id, session_id
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """, 
                        event_id,
                        aggregate_id,
                        aggregate_type,
                        event.__class__.__name__,
                        version,
                        event_data,
                        event.metadata,
                        event.occurred_at,
                        correlation_id,
                        causation_id,
                        user_id,
                        session_id
                    )
                
                # Update stream position
                await self._update_stream_position(aggregate_id, aggregate_type, len(events))
                
                logger.info(f"Appended {len(events)} events for {aggregate_type}:{aggregate_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to append events for {aggregate_id}: {e}")
            return False
    
    async def get_events(
        self,
        aggregate_id: str,
        aggregate_type: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[BaseEvent]:
        """Get events for a specific aggregate"""
        try:
            query = """
                SELECT event_type, event_data, metadata, occurred_at, event_version
                FROM events 
                WHERE aggregate_id = $1 AND aggregate_type = $2 
                AND event_version > $3
            """
            params = [aggregate_id, aggregate_type, from_version]
            
            if to_version is not None:
                query += " AND event_version <= $4"
                params.append(to_version)
            
            query += " ORDER BY event_version ASC"
            
            rows = await self.db_conn.fetch(query, *params)
            
            events = []
            for row in rows:
                event = self._deserialize_event(
                    row['event_type'],
                    row['event_data'],
                    row['metadata'],
                    row['occurred_at']
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events for {aggregate_id}: {e}")
            return []
    
    async def get_events_by_type(
        self,
        event_type: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[BaseEvent]:
        """Get events by type within a date range"""
        try:
            query = """
                SELECT event_type, event_data, metadata, occurred_at, event_version,
                       aggregate_id, aggregate_type
                FROM events 
                WHERE event_type = $1
            """
            params = [event_type]
            
            if from_date:
                query += " AND occurred_at >= $2"
                params.append(from_date)
                if to_date:
                    query += " AND occurred_at <= $3"
                    params.append(to_date)
            elif to_date:
                query += " AND occurred_at <= $2"
                params.append(to_date)
            
            query += " ORDER BY occurred_at ASC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.db_conn.fetch(query, *params)
            
            events = []
            for row in rows:
                event = self._deserialize_event(
                    row['event_type'],
                    row['event_data'],
                    row['metadata'],
                    row['occurred_at']
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events by type {event_type}: {e}")
            return []
    
    async def get_events_by_correlation(
        self, correlation_id: UUID) -> List[BaseEvent]:
        """Get all events for a correlation ID"""
        try:
            query = """
                SELECT event_type, event_data, metadata, occurred_at, event_version,
                       aggregate_id, aggregate_type
                FROM events 
                WHERE correlation_id = $1
                ORDER BY occurred_at ASC
            """
            
            rows = await self.db_conn.fetch(query, correlation_id)
            
            events = []
            for row in rows:
                event = self._deserialize_event(
                    row['event_type'],
                    row['event_data'],
                    row['metadata'],
                    row['occurred_at']
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events by correlation {correlation_id}: {e}")
            return []
    
    async def get_aggregate_version(self, aggregate_id: str, aggregate_type: str) -> int:
        """Get the current version of an aggregate"""
        try:
            query = """
                SELECT MAX(event_version) as version
                FROM events 
                WHERE aggregate_id = $1 AND aggregate_type = $2
            """
            
            row = await self.db_conn.fetchrow(query, aggregate_id, aggregate_type)
            return row['version'] if row['version'] is not None else 0
            
        except Exception as e:
            logger.error(f"Failed to get aggregate version for {aggregate_id}: {e}")
            return 0
    
    async def save_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        snapshot_data: Dict[str, Any]
    ) -> bool:
        """Save a snapshot of an aggregate at a specific version"""
        try:
            await self.db_conn.execute("""
                INSERT INTO event_snapshots (aggregate_id, aggregate_type, version, snapshot_data)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (aggregate_id, version) DO UPDATE SET
                    snapshot_data = EXCLUDED.snapshot_data,
                    created_at = CURRENT_TIMESTAMP
            """, aggregate_id, aggregate_type, version, snapshot_data)
            
            logger.info(f"Saved snapshot for {aggregate_type}:{aggregate_id} at version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save snapshot for {aggregate_id}: {e}")
            return False
    
    async def get_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot for an aggregate, or at a specific version"""
        try:
            if version:
                query = """
                    SELECT snapshot_data FROM event_snapshots
                    WHERE aggregate_id = $1 AND aggregate_type = $2 AND version = $3
                """
                row = await self.db_conn.fetchrow(query, aggregate_id, aggregate_type, version)
            else:
                query = """
                    SELECT snapshot_data FROM event_snapshots
                    WHERE aggregate_id = $1 AND aggregate_type = $2
                    ORDER BY version DESC LIMIT 1
                """
                row = await self.db_conn.fetchrow(query, aggregate_id, aggregate_type)
            
            return row['snapshot_data'] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get snapshot for {aggregate_id}: {e}")
            return None
    
    async def replay_events(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        aggregate_types: Optional[List[str]] = None
    ) -> List[BaseEvent]:
        """Replay events for rebuilding projections"""
        try:
            query = """
                SELECT event_type, event_data, metadata, occurred_at, event_version,
                       aggregate_id, aggregate_type
                FROM events 
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if from_date:
                param_count += 1
                query += f" AND occurred_at >= ${param_count}"
                params.append(from_date)
            
            if to_date:
                param_count += 1
                query += f" AND occurred_at <= ${param_count}"
                params.append(to_date)
            
            if event_types:
                param_count += 1
                query += f" AND event_type = ANY(${param_count})"
                params.append(event_types)
            
            if aggregate_types:
                param_count += 1
                query += f" AND aggregate_type = ANY(${param_count})"
                params.append(aggregate_types)
            
            query += " ORDER BY occurred_at ASC"
            
            rows = await self.db_conn.fetch(query, *params)
            
            events = []
            for row in rows:
                event = self._deserialize_event(
                    row['event_type'],
                    row['event_data'],
                    row['metadata'],
                    row['occurred_at']
                )
                events.append(event)
            
            logger.info(f"Replayed {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to replay events: {e}")
            return []
    
    def _serialize_event(self, event: BaseEvent) -> Dict[str, Any]:
        """Serialize an event to JSON-serializable format"""
        data = event.model_dump()
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, UUID):
                return str(obj)
            else:
                return obj
        
        return convert_decimals(data)
    
    def _deserialize_event(self, event_type: str, event_data: Dict[str, Any], 
                          metadata: Optional[Dict[str, Any]], occurred_at: datetime) -> BaseEvent:
        """Deserialize an event from stored data"""
        # Import event classes dynamically
        from src.services.cqrs.events import (
            OrderCreatedEvent, OrderFilledEvent, OrderCancelledEvent,
            PortfolioUpdatedEvent, PositionOpenedEvent, PositionClosedEvent,
            StrategyCreatedEvent, StrategyUpdatedEvent, StrategyDeletedEvent,
            SignalGeneratedEvent, SignalExecutedEvent, SignalCancelledEvent,
            BacktestStartedEvent, BacktestCompletedEvent, BacktestFailedEvent,
            RiskLimitExceededEvent, RiskAlertEvent, RiskClearedEvent
        )
        
        # Map event type names to classes
        event_classes = {
            'OrderCreatedEvent': OrderCreatedEvent,
            'OrderFilledEvent': OrderFilledEvent,
            'OrderCancelledEvent': OrderCancelledEvent,
            'PortfolioUpdatedEvent': PortfolioUpdatedEvent,
            'PositionOpenedEvent': PositionOpenedEvent,
            'PositionClosedEvent': PositionClosedEvent,
            'StrategyCreatedEvent': StrategyCreatedEvent,
            'StrategyUpdatedEvent': StrategyUpdatedEvent,
            'StrategyDeletedEvent': StrategyDeletedEvent,
            'SignalGeneratedEvent': SignalGeneratedEvent,
            'SignalExecutedEvent': SignalExecutedEvent,
            'SignalCancelledEvent': SignalCancelledEvent,
            'BacktestStartedEvent': BacktestStartedEvent,
            'BacktestCompletedEvent': BacktestCompletedEvent,
            'BacktestFailedEvent': BacktestFailedEvent,
            'RiskLimitExceededEvent': RiskLimitExceededEvent,
            'RiskAlertEvent': RiskAlertEvent,
            'RiskClearedEvent': RiskClearedEvent
        }
        
        event_class = event_classes.get(event_type)
        if not event_class:
            raise ValueError(f"Unknown event type: {event_type}")
        
        # Convert float back to Decimal for numeric fields
        def convert_floats_to_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimals(item) for item in obj]
            elif isinstance(obj, float):
                # Check if this should be a Decimal (price, quantity, etc.)
                if any(key in str(obj) for key in ['price', 'quantity', 'amount', 'value', 'pnl', 'return']):
                    return Decimal(str(obj))
                return obj
            else:
                return obj
        
        converted_data = convert_floats_to_decimals(event_data)
        
        # Create the event instance
        return event_class(**converted_data)
    
    async def _update_stream_position(self, aggregate_id: str, aggregate_type: str, event_count: int):
        """Update the stream position after appending events"""
        try:
            await self.db_conn.execute("""
                INSERT INTO event_streams (stream_id, stream_type, last_event_version)
                VALUES ($1, $2, $3)
                ON CONFLICT (stream_id) DO UPDATE SET
                    last_event_version = event_streams.last_event_version + $3,
                    last_processed_at = CURRENT_TIMESTAMP
            """, f"{aggregate_type}:{aggregate_id}", aggregate_type, event_count)
        except Exception as e:
            logger.error(f"Failed to update stream position for {aggregate_id}: {e}")


class ConcurrencyError(Exception):
    """Raised when there's a concurrency conflict in the event store"""
    pass
