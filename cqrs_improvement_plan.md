# CQRS Improvement Plan for Trading System

## Current State Analysis

### ✅ What's Working (Command Side)
- **Command Infrastructure**: Complete command/query bus implementation
- **Trading Commands**: Order placement, cancellation, strategy management
- **Event Infrastructure**: Event bus and handler framework
- **Aggregate Pattern**: Order aggregate for state management

### ❌ What's Missing (Query Side)
- **Query Implementations**: No actual query classes
- **Read Models**: No dedicated read models for different views
- **Projection Updates**: No mechanism to update read models from events
- **Event Sourcing**: Inconsistent event generation and storage

## Improvement Roadmap

### Phase 1: Query Side Implementation (2-3 weeks)

#### 1.1 Create Query Classes
```python
# Portfolio Queries
class GetPortfolioQuery(Query):
    user_id: str
    account_id: str
    include_positions: bool = True
    include_performance: bool = True

class GetPositionsQuery(Query):
    user_id: str
    account_id: str
    symbol: Optional[str] = None
    status: Optional[str] = None

# Market Data Queries
class GetMarketDataQuery(Query):
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = "1d"

class GetRealTimePriceQuery(Query):
    symbols: List[str]

# Analytics Queries
class GetPerformanceQuery(Query):
    user_id: str
    account_id: str
    start_date: datetime
    end_date: datetime
    metrics: List[str] = ["total_return", "sharpe_ratio", "max_drawdown"]

class GetBacktestResultsQuery(Query):
    strategy_id: str
    start_date: datetime
    end_date: datetime
```

#### 1.2 Create Read Models
```python
# Portfolio Read Model
class PortfolioReadModel:
    user_id: str
    account_id: str
    total_value: Decimal
    cash_balance: Decimal
    positions: List[PositionReadModel]
    performance_metrics: PerformanceMetrics
    last_updated: datetime

class PositionReadModel:
    symbol: str
    quantity: int
    average_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal

# Market Data Read Model
class MarketDataReadModel:
    symbol: str
    current_price: Decimal
    price_change: Decimal
    price_change_pct: Decimal
    volume: int
    last_updated: datetime
    historical_data: List[PricePoint]

# Analytics Read Model
class AnalyticsReadModel:
    strategy_id: str
    total_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    avg_trade_duration: timedelta
    last_updated: datetime
```

#### 1.3 Create Query Handlers
```python
class GetPortfolioHandler(QueryHandler):
    def __init__(self, portfolio_read_model_repo: PortfolioReadModelRepository):
        self.repo = portfolio_read_model_repo
    
    async def handle(self, query: GetPortfolioQuery) -> PortfolioReadModel:
        return await self.repo.get_by_user_and_account(
            query.user_id, query.account_id
        )

class GetMarketDataHandler(QueryHandler):
    def __init__(self, market_data_read_model_repo: MarketDataReadModelRepository):
        self.repo = market_data_read_model_repo
    
    async def handle(self, query: GetMarketDataQuery) -> MarketDataReadModel:
        return await self.repo.get_by_symbol_and_date_range(
            query.symbol, query.start_date, query.end_date
        )
```

### Phase 2: Event Sourcing Implementation (2-3 weeks)

#### 2.1 Event Store
```python
class EventStore:
    async def append_events(self, stream_id: str, events: List[Event], expected_version: int):
        """Append events to event store with optimistic concurrency control"""
        pass
    
    async def get_events(self, stream_id: str, from_version: int = 0) -> List[Event]:
        """Get events from event store"""
        pass
    
    async def get_events_by_type(self, event_type: str, from_date: datetime) -> List[Event]:
        """Get events by type for projection updates"""
        pass
```

#### 2.2 Event Generation in Commands
```python
class PlaceOrderHandler(CommandHandler):
    async def handle(self, command: PlaceOrderCommand) -> None:
        # Create order aggregate
        order = OrderAggregate.create(command)
        
        # Apply business logic
        order.place()
        
        # Generate events
        events = order.get_uncommitted_events()
        
        # Store in event store
        await self.event_store.append_events(
            f"order-{order.order_id}", 
            events, 
            order.version
        )
        
        # Publish events
        for event in events:
            await self.event_bus.publish(event)
```

### Phase 3: Projection Updates (2-3 weeks)

#### 3.1 Projection Handlers
```python
class PortfolioProjectionHandler(EventHandler):
    async def handle(self, event: OrderFilledEvent) -> None:
        """Update portfolio read model when order is filled"""
        portfolio = await self.portfolio_repo.get_by_user_and_account(
            event.user_id, event.account_id
        )
        
        if event.side == "BUY":
            portfolio.add_position(event.symbol, event.quantity, event.price)
        else:
            portfolio.remove_position(event.symbol, event.quantity, event.price)
        
        await self.portfolio_repo.save(portfolio)

class MarketDataProjectionHandler(EventHandler):
    async def handle(self, event: PriceUpdatedEvent) -> None:
        """Update market data read model when price updates"""
        market_data = await self.market_data_repo.get_by_symbol(event.symbol)
        market_data.update_price(event.price, event.timestamp)
        await self.market_data_repo.save(market_data)
```

#### 3.2 Projection Update Service
```python
class ProjectionUpdateService:
    def __init__(self, event_store: EventStore, projection_handlers: List[EventHandler]):
        self.event_store = event_store
        self.handlers = projection_handlers
    
    async def update_projections(self):
        """Update all projections from new events"""
        # Get events since last update
        events = await self.event_store.get_events_since(self.last_processed_event_id)
        
        # Process each event through all handlers
        for event in events:
            for handler in self.handlers:
                if handler.can_handle(event):
                    await handler.handle(event)
        
        # Update last processed event ID
        self.last_processed_event_id = events[-1].event_id
```

### Phase 4: API Integration (1-2 weeks)

#### 4.1 Query API Endpoints
```python
# FastAPI endpoints for queries
@app.get("/api/portfolio/{user_id}/{account_id}")
async def get_portfolio(user_id: str, account_id: str):
    query = GetPortfolioQuery(user_id=user_id, account_id=account_id)
    return await query_bus.dispatch(query)

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str, start_date: Optional[str] = None):
    query = GetMarketDataQuery(symbol=symbol, start_date=start_date)
    return await query_bus.dispatch(query)

@app.get("/api/analytics/{strategy_id}")
async def get_analytics(strategy_id: str, start_date: str, end_date: str):
    query = GetAnalyticsQuery(strategy_id=strategy_id, start_date=start_date, end_date=end_date)
    return await query_bus.dispatch(query)
```

## Benefits of Full CQRS Implementation

### 1. **Performance Optimization**
- **Read Models**: Optimized for specific query patterns
- **Caching**: Read models can be heavily cached
- **Scalability**: Read and write models can scale independently

### 2. **Data Consistency**
- **Eventual Consistency**: Read models updated asynchronously
- **Audit Trail**: Complete event history for compliance
- **Replay Capability**: Can rebuild read models from events

### 3. **Business Logic Separation**
- **Command Side**: Focus on business rules and validation
- **Query Side**: Focus on data presentation and reporting
- **Clear Boundaries**: Easier to maintain and test

### 4. **Trading System Specific Benefits**
- **Real-time Dashboards**: Fast read models for UI
- **Historical Analysis**: Event sourcing for backtesting
- **Risk Management**: Separate read models for risk calculations
- **Compliance**: Complete audit trail for regulatory requirements

## Implementation Priority

1. **High Priority**: Query implementations for dashboards
2. **Medium Priority**: Event sourcing for audit trail
3. **Low Priority**: Advanced projection updates

## Estimated Timeline
- **Phase 1**: 2-3 weeks (Query side)
- **Phase 2**: 2-3 weeks (Event sourcing)
- **Phase 3**: 2-3 weeks (Projections)
- **Phase 4**: 1-2 weeks (API integration)
- **Total**: 7-11 weeks for full CQRS implementation

## Next Steps
1. Start with Phase 1 - Query implementations
2. Focus on high-value queries (portfolio, market data)
3. Implement read models for existing dashboards
4. Gradually add event sourcing and projections
