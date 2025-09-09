"""
Event Subscription Service for CQRS
Handles subscribing to events and updating projections automatically
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID

from src.services.cqrs.event_store import EventStore
from src.services.cqrs.projection_update_service import ProjectionUpdateService

logger = logging.getLogger(__name__)


class EventSubscriptionService:
    """Service for subscribing to events and updating projections"""
    
    def __init__(self, event_store: EventStore, projection_update_service: ProjectionUpdateService):
        self.event_store = event_store
        self.projection_update_service = projection_update_service
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._is_running = False
        self._last_processed_timestamp: Optional[datetime] = None
    
    async def start(self, poll_interval: float = 1.0):
        """Start the event subscription service"""
        if self._is_running:
            logger.warning("Event subscription service is already running")
            return
        
        self._is_running = True
        logger.info("Starting event subscription service")
        
        # Initialize last processed timestamp to now
        if self._last_processed_timestamp is None:
            self._last_processed_timestamp = datetime.utcnow() - timedelta(hours=1)
        
        try:
            while self._is_running:
                await self._process_new_events()
                await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Error in event subscription service: {e}")
        finally:
            self._is_running = False
            logger.info("Event subscription service stopped")
    
    async def stop(self):
        """Stop the event subscription service"""
        self._is_running = False
        logger.info("Stopping event subscription service")
    
    async def _process_new_events(self):
        """Process new events since last check"""
        try:
            # Get events since last processed timestamp
            events = await self.event_store.replay_events(
                from_date=self._last_processed_timestamp,
                limit=1000  # Process in batches
            )
            
            if not events:
                return
            
            # Process events through projection update service
            results = await self.projection_update_service.process_events_batch(events)
            
            # Update last processed timestamp
            if events:
                self._last_processed_timestamp = max(event.timestamp for event in events)
            
            logger.info(f"Processed {results['processed']} events, {results['failed']} failed, {results['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"Failed to process new events: {e}")
    
    def subscribe_to_event_type(self, event_type: str, handler: Callable):
        """Subscribe to a specific event type"""
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        
        self._subscriptions[event_type].append(handler)
        logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe_from_event_type(self, event_type: str, handler: Callable):
        """Unsubscribe from a specific event type"""
        if event_type in self._subscriptions:
            try:
                self._subscriptions[event_type].remove(handler)
                logger.info(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
    
    async def process_event_immediately(self, event: Any) -> bool:
        """Process a single event immediately"""
        try:
            # Process through projection update service
            success = await self.projection_update_service.process_event(event)
            
            # Also call any custom subscribers
            event_type = event.__class__.__name__
            if event_type in self._subscriptions:
                for handler in self._subscriptions[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error in custom event handler for {event_type}: {e}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process event immediately: {e}")
            return False
    
    async def replay_events_from_timestamp(self, from_timestamp: datetime) -> Dict[str, int]:
        """Replay events from a specific timestamp"""
        try:
            events = await self.event_store.replay_events(
                from_date=from_timestamp,
                limit=10000  # Large limit for replay
            )
            
            if not events:
                return {"processed": 0, "failed": 0, "skipped": 0}
            
            # Process events in batches
            batch_size = 100
            total_results = {"processed": 0, "failed": 0, "skipped": 0}
            
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]
                results = await self.projection_update_service.process_events_batch(batch)
                
                for key in total_results:
                    total_results[key] += results[key]
                
                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            logger.info(f"Replayed events from {from_timestamp}: {total_results}")
            return total_results
            
        except Exception as e:
            logger.error(f"Failed to replay events from timestamp: {e}")
            return {"processed": 0, "failed": 0, "skipped": 0}
    
    async def get_subscription_status(self) -> Dict[str, Any]:
        """Get the current status of the subscription service"""
        return {
            "is_running": self._is_running,
            "last_processed_timestamp": self._last_processed_timestamp,
            "subscription_count": sum(len(handlers) for handlers in self._subscriptions.values()),
            "subscribed_event_types": list(self._subscriptions.keys())
        }


class EventHandler:
    """Base class for custom event handlers"""
    
    async def handle(self, event: Any) -> None:
        """Handle an event - override this method"""
        pass


class PortfolioEventHandler(EventHandler):
    """Example custom event handler for portfolio events"""
    
    def __init__(self, portfolio_id: str):
        self.portfolio_id = portfolio_id
    
    async def handle(self, event: Any):
        """Handle portfolio-related events"""
        if hasattr(event, 'portfolio_id') and event.portfolio_id == self.portfolio_id:
            logger.info(f"Portfolio {self.portfolio_id} event: {event.__class__.__name__}")
            # Add custom logic here


class OrderEventHandler(EventHandler):
    """Example custom event handler for order events"""
    
    def __init__(self, order_id: str):
        self.order_id = order_id
    
    async def handle(self, event: Any):
        """Handle order-related events"""
        if hasattr(event, 'order_id') and event.order_id == self.order_id:
            logger.info(f"Order {self.order_id} event: {event.__class__.__name__}")
            # Add custom logic here


class StrategyEventHandler(EventHandler):
    """Example custom event handler for strategy events"""
    
    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
    
    async def handle(self, event: Any):
        """Handle strategy-related events"""
        if hasattr(event, 'strategy_id') and event.strategy_id == self.strategy_id:
            logger.info(f"Strategy {self.strategy_id} event: {event.__class__.__name__}")
            # Add custom logic here
