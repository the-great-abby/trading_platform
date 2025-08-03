"""
Unit tests for CQRS base classes
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.cqrs.base import Command, Query, Event, CommandBus, QueryBus, EventBus, AggregateRoot


class TestCommand:
    """Test Command base class"""
    
    def test_command_creation(self):
        """Test command creation with default values"""
        cmd = Command()
        assert isinstance(cmd.command_id, UUID)
        assert isinstance(cmd.timestamp, datetime)
        assert cmd.user_id is None
        assert cmd.correlation_id is None
    
    def test_command_creation_with_values(self):
        """Test command creation with provided values"""
        user_id = "user123"
        correlation_id = uuid4()
        cmd = Command(user_id=user_id, correlation_id=correlation_id)
        
        assert cmd.user_id == user_id
        assert cmd.correlation_id == correlation_id
    
    def test_command_json_serialization(self):
        """Test command JSON serialization"""
        cmd = Command(user_id="user123")
        cmd_dict = cmd.model_dump()
        
        assert "command_id" in cmd_dict
        assert "timestamp" in cmd_dict
        assert cmd_dict["user_id"] == "user123"


class TestQuery:
    """Test Query base class"""
    
    def test_query_creation(self):
        """Test query creation with default values"""
        query = Query()
        assert isinstance(query.query_id, UUID)
        assert isinstance(query.timestamp, datetime)
        assert query.user_id is None
    
    def test_query_creation_with_values(self):
        """Test query creation with provided values"""
        user_id = "user123"
        query = Query(user_id=user_id)
        assert query.user_id == user_id


class TestEvent:
    """Test Event base class"""
    
    def test_event_creation(self):
        """Test event creation with default values"""
        event = Event()
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)
        assert event.version == 1
        assert event.aggregate_id is None
        assert event.correlation_id is None
    
    def test_event_creation_with_values(self):
        """Test event creation with provided values"""
        aggregate_id = "order123"
        correlation_id = uuid4()
        event = Event(aggregate_id=aggregate_id, correlation_id=correlation_id, version=5)
        
        assert event.aggregate_id == aggregate_id
        assert event.correlation_id == correlation_id
        assert event.version == 5


class TestCommandBus:
    """Test CommandBus"""
    
    @pytest.fixture
    def command_bus(self):
        return CommandBus()
    
    @pytest.fixture
    def mock_handler(self):
        class MockHandler:
            def __init__(self):
                self.handled_commands = []
            
            async def handle(self, command):
                self.handled_commands.append(command)
                return "success"
        
        return MockHandler()
    
    def test_register_handler(self, command_bus, mock_handler):
        """Test handler registration"""
        command_bus.register_handler(Command, mock_handler)
        assert Command in command_bus._handlers
        assert command_bus._handlers[Command] == mock_handler
    
    @pytest.mark.asyncio
    async def test_dispatch_command(self, command_bus, mock_handler):
        """Test command dispatch"""
        command_bus.register_handler(Command, mock_handler)
        cmd = Command()
        
        result = await command_bus.dispatch(cmd)
        
        assert result == "success"
        assert len(mock_handler.handled_commands) == 1
        assert mock_handler.handled_commands[0] == cmd
    
    @pytest.mark.asyncio
    async def test_dispatch_unregistered_command(self, command_bus):
        """Test dispatch of unregistered command type"""
        cmd = Command()
        
        with pytest.raises(ValueError, match="No handler registered"):
            await command_bus.dispatch(cmd)


class TestQueryBus:
    """Test QueryBus"""
    
    @pytest.fixture
    def query_bus(self):
        return QueryBus()
    
    @pytest.fixture
    def mock_handler(self):
        class MockHandler:
            def __init__(self):
                self.handled_queries = []
            
            async def handle(self, query):
                self.handled_queries.append(query)
                return {"data": "test"}
        
        return MockHandler()
    
    def test_register_handler(self, query_bus, mock_handler):
        """Test handler registration"""
        query_bus.register_handler(Query, mock_handler)
        assert Query in query_bus._handlers
        assert query_bus._handlers[Query] == mock_handler
    
    @pytest.mark.asyncio
    async def test_dispatch_query(self, query_bus, mock_handler):
        """Test query dispatch"""
        query_bus.register_handler(Query, mock_handler)
        query = Query()
        
        result = await query_bus.dispatch(query)
        
        assert result == {"data": "test"}
        assert len(mock_handler.handled_queries) == 1
        assert mock_handler.handled_queries[0] == query


class TestEventBus:
    """Test EventBus"""
    
    @pytest.fixture
    def event_bus(self):
        return EventBus()
    
    @pytest.fixture
    def mock_handler(self):
        class MockHandler:
            def __init__(self):
                self.handled_events = []
            
            async def handle(self, event):
                self.handled_events.append(event)
        
        return MockHandler()
    
    def test_register_handler(self, event_bus, mock_handler):
        """Test handler registration"""
        event_bus.register_handler(Event, mock_handler)
        assert Event in event_bus._handlers
        assert mock_handler in event_bus._handlers[Event]
    
    def test_register_multiple_handlers(self, event_bus, mock_handler):
        """Test registering multiple handlers for same event type"""
        handler2 = type(mock_handler)()  # Create another handler
        
        event_bus.register_handler(Event, mock_handler)
        event_bus.register_handler(Event, handler2)
        
        assert len(event_bus._handlers[Event]) == 2
        assert mock_handler in event_bus._handlers[Event]
        assert handler2 in event_bus._handlers[Event]
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus, mock_handler):
        """Test event publishing"""
        event_bus.register_handler(Event, mock_handler)
        event = Event()
        
        await event_bus.publish(event)
        
        assert len(mock_handler.handled_events) == 1
        assert mock_handler.handled_events[0] == event
    
    @pytest.mark.asyncio
    async def test_publish_event_no_handlers(self, event_bus):
        """Test publishing event with no handlers"""
        event = Event()
        
        # Should not raise an exception
        await event_bus.publish(event)
    
    @pytest.mark.asyncio
    async def test_publish_event_handler_error(self, event_bus):
        """Test publishing event when handler raises error"""
        class ErrorHandler:
            async def handle(self, event):
                raise Exception("Handler error")
        
        event_bus.register_handler(Event, ErrorHandler())
        event = Event()
        
        # Should not raise an exception, just log error
        await event_bus.publish(event)


class TestAggregateRoot:
    """Test AggregateRoot"""
    
    @pytest.fixture
    def aggregate(self):
        return AggregateRoot("test-aggregate")
    
    def test_aggregate_creation(self, aggregate):
        """Test aggregate creation"""
        assert aggregate.aggregate_id == "test-aggregate"
        assert aggregate.version == 0
        assert len(aggregate.get_uncommitted_events()) == 0
    
    def test_apply_event(self, aggregate):
        """Test applying event to aggregate"""
        event = Event(aggregate_id="test-aggregate")
        
        aggregate.apply(event)
        
        assert aggregate.version == 1
        assert len(aggregate.get_uncommitted_events()) == 1
        assert aggregate.get_uncommitted_events()[0] == event
    
    def test_mark_events_as_committed(self, aggregate):
        """Test marking events as committed"""
        event = Event(aggregate_id="test-aggregate")
        aggregate.apply(event)
        
        assert len(aggregate.get_uncommitted_events()) == 1
        
        aggregate.mark_events_as_committed()
        
        assert len(aggregate.get_uncommitted_events()) == 0
    
    def test_apply_multiple_events(self, aggregate):
        """Test applying multiple events"""
        event1 = Event(aggregate_id="test-aggregate")
        event2 = Event(aggregate_id="test-aggregate")
        
        aggregate.apply(event1)
        aggregate.apply(event2)
        
        assert aggregate.version == 2
        assert len(aggregate.get_uncommitted_events()) == 2
    
    def test_get_uncommitted_events_copy(self, aggregate):
        """Test that get_uncommitted_events returns a copy"""
        event = Event(aggregate_id="test-aggregate")
        aggregate.apply(event)
        
        events = aggregate.get_uncommitted_events()
        events.append("should not affect original")
        
        assert len(aggregate.get_uncommitted_events()) == 1 