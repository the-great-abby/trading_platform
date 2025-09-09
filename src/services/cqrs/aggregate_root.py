"""
Aggregate Root for CQRS Event Sourcing
Base class for domain aggregates that use event sourcing
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.services.cqrs.events import BaseEvent
from src.services.cqrs.event_store import EventStore

logger = logging.getLogger(__name__)


class AggregateRoot(ABC):
    """Base class for domain aggregates using event sourcing"""
    
    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0
        self.uncommitted_events: List[BaseEvent] = []
        self._event_store: Optional[EventStore] = None
    
    def set_event_store(self, event_store: EventStore):
        """Set the event store for this aggregate"""
        self._event_store = event_store
    
    def get_uncommitted_events(self) -> List[BaseEvent]:
        """Get all uncommitted events"""
        return self.uncommitted_events.copy()
    
    def mark_events_as_committed(self):
        """Mark all uncommitted events as committed"""
        self.uncommitted_events.clear()
    
    def load_from_history(self, events: List[BaseEvent]):
        """Load aggregate state from event history"""
        for event in events:
            self.apply_event(event, is_new=False)
            self.version += 1
    
    def apply_event(self, event: BaseEvent, is_new: bool = True):
        """Apply an event to the aggregate"""
        # Call the specific event handler
        handler_name = f"handle_{event.__class__.__name__}"
        handler = getattr(self, handler_name, None)
        
        if handler:
            handler(event)
        else:
            logger.warning(f"No handler found for event {event.__class__.__name__}")
        
        # Add to uncommitted events if it's a new event
        if is_new:
            self.uncommitted_events.append(event)
    
    async def save(self, correlation_id: Optional[UUID] = None, 
                   causation_id: Optional[UUID] = None,
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None) -> bool:
        """Save uncommitted events to the event store"""
        if not self._event_store:
            logger.error("No event store set for aggregate")
            return False
        
        if not self.uncommitted_events:
            return True
        
        try:
            success = await self._event_store.append_events(
                aggregate_id=self.aggregate_id,
                aggregate_type=self.aggregate_type,
                events=self.uncommitted_events,
                expected_version=self.version - len(self.uncommitted_events),
                correlation_id=correlation_id,
                causation_id=causation_id,
                user_id=user_id,
                session_id=session_id
            )
            
            if success:
                self.mark_events_as_committed()
                self.version += len(self.uncommitted_events)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save aggregate {self.aggregate_id}: {e}")
            return False
    
    @abstractmethod
    def to_snapshot(self) -> Dict[str, Any]:
        """Convert aggregate to snapshot data"""
        pass
    
    @classmethod
    @abstractmethod
    def from_snapshot(cls, snapshot_data: Dict[str, Any]) -> 'AggregateRoot':
        """Create aggregate from snapshot data"""
        pass


class OrderAggregate(AggregateRoot):
    """Order aggregate for event sourcing"""
    
    def __init__(self, order_id: str):
        super().__init__(order_id, "Order")
        self.symbol: str = ""
        self.side: str = ""
        self.quantity: int = 0
        self.order_type: str = ""
        self.price: Optional[float] = None
        self.status: str = "pending"
        self.user_id: str = ""
        self.account_id: str = ""
        self.filled_quantity: int = 0
        self.average_fill_price: Optional[float] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def place_order(self, symbol: str, side: str, quantity: int, order_type: str,
                   price: Optional[float], user_id: str, account_id: str):
        """Place a new order"""
        from src.services.cqrs.events import OrderCreatedEvent
        
        event = OrderCreatedEvent(
            order_id=self.aggregate_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            user_id=user_id,
            account_id=account_id
        )
        
        self.apply_event(event)
    
    def fill_order(self, filled_quantity: int, fill_price: float):
        """Fill part or all of an order"""
        from src.services.cqrs.events import OrderFilledEvent
        
        event = OrderFilledEvent(
            order_id=self.aggregate_id,
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            remaining_quantity=self.quantity - self.filled_quantity - filled_quantity
        )
        
        self.apply_event(event)
    
    def cancel_order(self, reason: str = "User requested"):
        """Cancel an order"""
        from src.services.cqrs.events import OrderCancelledEvent
        
        event = OrderCancelledEvent(
            order_id=self.aggregate_id,
            reason=reason,
            cancelled_quantity=self.quantity - self.filled_quantity
        )
        
        self.apply_event(event)
    
    def handle_OrderCreatedEvent(self, event):
        """Handle order created event"""
        self.symbol = event.symbol
        self.side = event.side
        self.quantity = event.quantity
        self.order_type = event.order_type
        self.price = event.price
        self.user_id = event.user_id
        self.account_id = event.account_id
        self.created_at = event.timestamp
        self.updated_at = event.timestamp
    
    def handle_OrderFilledEvent(self, event):
        """Handle order filled event"""
        self.filled_quantity += event.filled_quantity
        
        # Calculate average fill price
        if self.filled_quantity > 0:
            if self.average_fill_price is None:
                self.average_fill_price = event.fill_price
            else:
                # Weighted average
                total_value = (self.average_fill_price * (self.filled_quantity - event.filled_quantity) + 
                             event.fill_price * event.filled_quantity)
                self.average_fill_price = total_value / self.filled_quantity
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = "filled"
        else:
            self.status = "partially_filled"
        
        self.updated_at = event.timestamp
    
    def handle_OrderCancelledEvent(self, event):
        """Handle order cancelled event"""
        self.status = "cancelled"
        self.updated_at = event.timestamp
    
    def to_snapshot(self) -> Dict[str, Any]:
        """Convert to snapshot data"""
        return {
            "order_id": self.aggregate_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "status": self.status,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "filled_quantity": self.filled_quantity,
            "average_fill_price": self.average_fill_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version
        }
    
    @classmethod
    def from_snapshot(cls, snapshot_data: Dict[str, Any]) -> 'OrderAggregate':
        """Create from snapshot data"""
        order = cls(snapshot_data["order_id"])
        order.symbol = snapshot_data["symbol"]
        order.side = snapshot_data["side"]
        order.quantity = snapshot_data["quantity"]
        order.order_type = snapshot_data["order_type"]
        order.price = snapshot_data["price"]
        order.status = snapshot_data["status"]
        order.user_id = snapshot_data["user_id"]
        order.account_id = snapshot_data["account_id"]
        order.filled_quantity = snapshot_data["filled_quantity"]
        order.average_fill_price = snapshot_data["average_fill_price"]
        order.created_at = datetime.fromisoformat(snapshot_data["created_at"]) if snapshot_data["created_at"] else None
        order.updated_at = datetime.fromisoformat(snapshot_data["updated_at"]) if snapshot_data["updated_at"] else None
        order.version = snapshot_data["version"]
        return order


class PortfolioAggregate(AggregateRoot):
    """Portfolio aggregate for event sourcing"""
    
    def __init__(self, portfolio_id: str):
        super().__init__(portfolio_id, "Portfolio")
        self.user_id: str = ""
        self.account_id: str = ""
        self.name: str = ""
        self.cash_balance: float = 0.0
        self.total_value: float = 0.0
        self.positions: Dict[str, Dict[str, Any]] = {}  # symbol -> position data
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def update_portfolio(self, user_id: str, account_id: str, name: str, cash_balance: float):
        """Update portfolio information"""
        from src.services.cqrs.events import PortfolioUpdatedEvent
        
        event = PortfolioUpdatedEvent(
            portfolio_id=self.aggregate_id,
            user_id=user_id,
            account_id=account_id,
            name=name,
            cash_balance=cash_balance,
            total_value=self.total_value
        )
        
        self.apply_event(event)
    
    def open_position(self, symbol: str, quantity: int, price: float):
        """Open a new position"""
        from src.services.cqrs.events import PositionOpenedEvent
        
        event = PositionOpenedEvent(
            portfolio_id=self.aggregate_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            market_value=quantity * price
        )
        
        self.apply_event(event)
    
    def close_position(self, symbol: str, quantity: int, price: float):
        """Close a position"""
        from src.services.cqrs.events import PositionClosedEvent
        
        event = PositionClosedEvent(
            portfolio_id=self.aggregate_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            market_value=quantity * price
        )
        
        self.apply_event(event)
    
    def handle_PortfolioUpdatedEvent(self, event):
        """Handle portfolio updated event"""
        self.user_id = event.user_id
        self.account_id = event.account_id
        self.name = event.name
        self.cash_balance = event.cash_balance
        self.total_value = event.total_value
        self.updated_at = event.timestamp
        
        if not self.created_at:
            self.created_at = event.timestamp
    
    def handle_PositionOpenedEvent(self, event):
        """Handle position opened event"""
        if event.symbol in self.positions:
            # Update existing position
            pos = self.positions[event.symbol]
            total_quantity = pos["quantity"] + event.quantity
            total_cost = pos["cost_basis"] + (event.quantity * event.price)
            pos["quantity"] = total_quantity
            pos["cost_basis"] = total_cost
            pos["average_price"] = total_cost / total_quantity
        else:
            # Create new position
            self.positions[event.symbol] = {
                "quantity": event.quantity,
                "cost_basis": event.quantity * event.price,
                "average_price": event.price,
                "market_value": event.market_value
            }
        
        self.updated_at = event.timestamp
    
    def handle_PositionClosedEvent(self, event):
        """Handle position closed event"""
        if event.symbol in self.positions:
            pos = self.positions[event.symbol]
            pos["quantity"] -= event.quantity
            
            if pos["quantity"] <= 0:
                del self.positions[event.symbol]
            else:
                # Update cost basis proportionally
                from decimal import Decimal
                remaining_ratio = Decimal(pos["quantity"]) / Decimal(pos["quantity"] + event.quantity)
                pos["cost_basis"] = pos["cost_basis"] * remaining_ratio
                pos["average_price"] = pos["cost_basis"] / Decimal(pos["quantity"])
        
        self.updated_at = event.timestamp
    
    def to_snapshot(self) -> Dict[str, Any]:
        """Convert to snapshot data"""
        return {
            "portfolio_id": self.aggregate_id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "name": self.name,
            "cash_balance": self.cash_balance,
            "total_value": self.total_value,
            "positions": self.positions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version
        }
    
    @classmethod
    def from_snapshot(cls, snapshot_data: Dict[str, Any]) -> 'PortfolioAggregate':
        """Create from snapshot data"""
        portfolio = cls(snapshot_data["portfolio_id"])
        portfolio.user_id = snapshot_data["user_id"]
        portfolio.account_id = snapshot_data["account_id"]
        portfolio.name = snapshot_data["name"]
        portfolio.cash_balance = snapshot_data["cash_balance"]
        portfolio.total_value = snapshot_data["total_value"]
        portfolio.positions = snapshot_data["positions"]
        portfolio.created_at = datetime.fromisoformat(snapshot_data["created_at"]) if snapshot_data["created_at"] else None
        portfolio.updated_at = datetime.fromisoformat(snapshot_data["updated_at"]) if snapshot_data["updated_at"] else None
        portfolio.version = snapshot_data["version"]
        return portfolio
