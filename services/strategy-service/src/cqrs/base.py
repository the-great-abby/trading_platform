"""
Base CQRS classes and interfaces
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID, uuid4
import json

from pydantic import BaseModel


# Type variables for generic handlers
C = TypeVar('C', bound='Command')
Q = TypeVar('Q', bound='Query')
E = TypeVar('E', bound='Event')


@dataclass
class Command(BaseModel):
    """Base class for all commands"""
    command_id: UUID = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    correlation_id: Optional[UUID] = None
    
    def __post_init__(self):
        if self.command_id is None:
            self.command_id = uuid4()
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


@dataclass
class Query(BaseModel):
    """Base class for all queries"""
    query_id: UUID = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.query_id is None:
            self.query_id = uuid4()
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


@dataclass
class Event(BaseModel):
    """Base class for all events"""
    event_id: UUID = None
    timestamp: datetime = None
    version: int = 1
    aggregate_id: Optional[str] = None
    correlation_id: Optional[UUID] = None
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = uuid4()
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class CommandHandler(ABC):
    """Base class for command handlers"""
    
    @abstractmethod
    async def handle(self, command: Command) -> Any:
        """Handle a command"""
        pass


class QueryHandler(ABC):
    """Base class for query handlers"""
    
    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """Handle a query"""
        pass


class EventHandler(ABC):
    """Base class for event handlers"""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event"""
        pass


class CommandBus:
    """Command bus for dispatching commands to handlers"""
    
    def __init__(self):
        self._handlers: Dict[Type[Command], CommandHandler] = {}
    
    def register_handler(self, command_type: Type[Command], handler: CommandHandler):
        """Register a command handler"""
        self._handlers[command_type] = handler
    
    async def dispatch(self, command: Command) -> Any:
        """Dispatch a command to its handler"""
        handler = self._handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler registered for command type: {type(command)}")
        
        return await handler.handle(command)


class QueryBus:
    """Query bus for dispatching queries to handlers"""
    
    def __init__(self):
        self._handlers: Dict[Type[Query], QueryHandler] = {}
    
    def register_handler(self, query_type: Type[Query], handler: QueryHandler):
        """Register a query handler"""
        self._handlers[query_type] = handler
    
    async def dispatch(self, query: Query) -> Any:
        """Dispatch a query to its handler"""
        handler = self._handlers.get(type(query))
        if not handler:
            raise ValueError(f"No handler registered for query type: {type(query)}")
        
        return await handler.handle(query)


class EventBus:
    """Event bus for publishing and subscribing to events"""
    
    def __init__(self):
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
    
    def register_handler(self, event_type: Type[Event], handler: EventHandler):
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers"""
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                # Log error but don't fail other handlers
                print(f"Error handling event {event.event_id}: {e}")


class AggregateRoot:
    """Base class for aggregate roots in event sourcing"""
    
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self._uncommitted_events: List[Event] = []
    
    def apply(self, event: Event) -> None:
        """Apply an event to the aggregate"""
        self._apply_event(event)
        self.version += 1
        self._uncommitted_events.append(event)
    
    def _apply_event(self, event: Event) -> None:
        """Apply an event (to be overridden by subclasses)"""
        method_name = f"apply_{event.__class__.__name__.lower()}"
        if hasattr(self, method_name):
            getattr(self, method_name)(event)
    
    def get_uncommitted_events(self) -> List[Event]:
        """Get uncommitted events"""
        return self._uncommitted_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Mark events as committed"""
        self._uncommitted_events.clear()


class EventStore:
    """Event store for persisting and retrieving events"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def save_events(self, aggregate_id: str, events: List[Event], expected_version: int) -> None:
        """Save events for an aggregate"""
        # Implementation would connect to database and save events
        # This is a simplified version
        for event in events:
            event.aggregate_id = aggregate_id
            event.version = expected_version + 1
            # Save to database
            print(f"Saving event: {event.event_id} for aggregate: {aggregate_id}")
    
    async def get_events(self, aggregate_id: str) -> List[Event]:
        """Get all events for an aggregate"""
        # Implementation would query database
        # This is a simplified version
        return []
    
    async def get_events_by_type(self, event_type: Type[Event]) -> List[Event]:
        """Get all events of a specific type"""
        # Implementation would query database
        # This is a simplified version
        return []


class Repository:
    """Repository for managing aggregates"""
    
    def __init__(self, event_store: EventStore, aggregate_class: Type[AggregateRoot]):
        self.event_store = event_store
        self.aggregate_class = aggregate_class
    
    async def save(self, aggregate: AggregateRoot) -> None:
        """Save an aggregate"""
        events = aggregate.get_uncommitted_events()
        if events:
            await self.event_store.save_events(
                aggregate.aggregate_id,
                events,
                aggregate.version - len(events)
            )
            aggregate.mark_events_as_committed()
    
    async def get_by_id(self, aggregate_id: str) -> Optional[AggregateRoot]:
        """Get an aggregate by ID"""
        events = await self.event_store.get_events(aggregate_id)
        if not events:
            return None
        
        aggregate = self.aggregate_class(aggregate_id)
        for event in events:
            aggregate.apply(event)
        
        return aggregate 