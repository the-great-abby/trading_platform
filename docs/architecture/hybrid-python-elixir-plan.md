# Hybrid Python/Elixir Trading Platform with NATS

## Executive Summary

Migrate the current all-Python trading platform to a hybrid architecture where
**Elixir handles real-time orchestration, process supervision, and event routing**
while **Python retains quantitative computation, strategy logic, and ML/AI**,
connected via **NATS JetStream** as the unified messaging backbone (replacing
Kafka and RabbitMQ).

---

## Guiding Principle: Play to Each Language's Strengths

| Concern | Best Fit | Why |
|---------|----------|-----|
| Concurrent connections, real-time event routing | **Elixir** | BEAM VM's lightweight processes, preemptive scheduling, near-zero cost per connection |
| Fault tolerance, self-healing supervision | **Elixir** | OTP supervisor trees, "let it crash" philosophy |
| Stateful long-running processes (order lifecycle, risk gates) | **Elixir** | GenServers with state, backed by supervision |
| WebSocket/live dashboards | **Elixir** | Phoenix LiveView - native bidirectional real-time UI |
| Numerical computation (pandas, numpy, scipy) | **Python** | Unmatched ecosystem for data manipulation |
| ML/AI models (TF, PyTorch, scikit-learn) | **Python** | No viable alternative in any other language |
| Financial libraries (QuantLib, CVXPY, PyPortfolioOpt) | **Python** | Domain-specific libraries only exist in Python |
| Strategy authoring | **Python** | 50+ existing strategies, familiar to quant developers |
| Backtesting & simulation | **Python** | Data-heavy, leverages pandas/numpy throughout |

---

## Proposed Architecture

```
                          ┌─────────────────────────┐
                          │     Phoenix LiveView     │
                          │   Unified Dashboard(s)   │
                          │  (replaces 8+ dashboard  │
                          │      services)           │
                          └────────────┬────────────┘
                                       │
                          ┌────────────▼────────────┐
                          │    Elixir Gateway /      │
                          │    Phoenix API Layer     │
                          │  (replaces gateway +     │
                          │   command-api/query-api) │
                          └────────────┬────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
    ┌────────────▼──────────┐  ┌──────▼───────┐  ┌─────────▼──────────┐
    │  Elixir: Trading      │  │ Elixir: Risk │  │  Elixir: Order     │
    │  Engine Orchestrator  │  │ Enforcement  │  │  Management FSM    │
    │  (GenServer)          │  │ (GenServer)  │  │  (GenStateMachine)  │
    └────────────┬──────────┘  └──────┬───────┘  └─────────┬──────────┘
                 │                     │                     │
    ═════════════╪═════════════════════╪═════════════════════╪══════════
                 │              NATS JetStream               │
    ═════════════╪═════════════════════╪═════════════════════╪══════════
                 │                     │                     │
    ┌────────────▼──────────┐  ┌──────▼───────┐  ┌─────────▼──────────┐
    │  Python: Strategy     │  │ Python: Risk │  │  Python: Market    │
    │  Workers (50+)        │  │ Computation  │  │  Data Fetchers     │
    │  (signal generation)  │  │ (VaR, stats) │  │  (Polygon, yfinance│
    └───────────────────────┘  └──────────────┘  │   Public.com)      │
                                                  └────────────────────┘
    ┌───────────────────────┐  ┌──────────────┐  ┌────────────────────┐
    │  Python: Backtesting  │  │ Python: ML / │  │  Python: Portfolio │
    │  Engine               │  │ AI Models    │  │  Optimization      │
    └───────────────────────┘  └──────────────┘  └────────────────────┘
```

---

## What Moves to Elixir (and Why)

### 1. Trading Engine Orchestrator
**Currently:** `src/core/trading_engine.py` - async Python event loop
**Becomes:** An Elixir `GenServer` supervised by OTP

**Rationale:** The trading engine is the heartbeat of the system. It coordinates
market data arrival, strategy signal evaluation, risk checks, and order
execution. This is a *coordination* problem, not a *computation* problem. The
BEAM VM excels here - each symbol/strategy pair can be its own lightweight
process, all supervised, all concurrent, with backpressure handled naturally.

**Key benefit:** If a single symbol's processing crashes, the supervisor
restarts just that process. The rest of the system is unaffected. In the
current Python async model, an unhandled exception in one coroutine can cascade.

### 2. Order Management (Finite State Machine)
**Currently:** `src/services/order_management/` + `services/order-service`
**Becomes:** Elixir `GenStateMachine` per order

**Rationale:** Orders have a well-defined lifecycle (pending -> submitted ->
partial_fill -> filled/cancelled/rejected). Elixir's `GenStateMachine` models
this perfectly, with each order being its own supervised process. State
transitions emit events to NATS. This replaces the current mix of database
state tracking and in-memory management.

### 3. Risk Enforcement Layer
**Currently:** `src/risk/risk_manager.py` - synchronous checks in the trading loop
**Becomes:** Elixir GenServer with ETS tables for fast lookups

**Rationale:** Risk *computation* (VaR calculations, correlation matrices,
Monte Carlo) stays in Python. But risk *enforcement* (checking position limits,
daily loss limits, concentration limits, circuit breakers) moves to Elixir.
These are fast lookups and comparisons that gate every order - they need to be
low-latency and highly available. ETS tables provide concurrent read access
without bottlenecking.

The split:
- **Python computes** risk metrics periodically, publishes to `risk.metrics.*`
- **Elixir enforces** limits in real-time using the latest computed metrics

### 4. Gateway & API Layer
**Currently:** `services/gateway` + `services/command-api` + `services/query-api` (3 separate Python services)
**Becomes:** Single Phoenix application

**Rationale:** Phoenix handles HTTP, WebSocket, and API routing in one
framework. The existing CQRS command/query separation maps naturally to
Phoenix contexts. Authentication, rate limiting, and request routing are all
first-class in Phoenix.

### 5. Real-Time Dashboards
**Currently:** 8+ separate dashboard services (trading-dashboard, ai-stock-dashboard, unified-analytics-dashboard, etc.)
**Becomes:** Phoenix LiveView application(s)

**Rationale:** This is arguably the biggest operational simplification. Each
current dashboard is a separate Node.js or Python service with its own
WebSocket handling. Phoenix LiveView replaces all of them with server-rendered
real-time UIs. No JavaScript framework needed. State lives on the server,
updates push automatically. One deployment instead of eight.

### 6. Signal Router / Event Bus
**Currently:** `services/signal-management-service` + Kafka consumers
**Becomes:** Elixir processes consuming from NATS, routing signals to
appropriate handlers

**Rationale:** Signal routing is pure coordination - receive a signal from a
strategy worker, validate it, route it to risk checks, then to order
management. No heavy computation. Elixir's pattern matching on message subjects
makes this clean and maintainable.

### 7. Notification Dispatch
**Currently:** `services/notification-service`
**Becomes:** Elixir GenServer with adapters for Discord/Slack/email

**Rationale:** Notification dispatch is a fan-out problem with retry logic -
a natural fit for supervised Elixir processes. If Discord's API is slow, it
doesn't block Slack notifications. Each channel is an independent process.

---

## What Stays in Python (and Why)

### 1. All 50+ Trading Strategies
The strategies are the *intellectual property* of the system. They use:
- pandas DataFrames for OHLCV manipulation
- numpy/scipy for statistical calculations
- scikit-learn for ML-based signals
- TensorFlow/PyTorch for neural network strategies
- QuantLib for options pricing

Rewriting these in Elixir would be impractical and pointless. Python's data
science ecosystem has no equivalent.

**Interaction model:** Each strategy runs as a Python worker process. It
subscribes to `market.data.{symbol}` on NATS, computes signals, and publishes
to `signals.{strategy_name}.{symbol}`.

### 2. Backtesting Engine
**Currently:** `src/backtesting/engine/backtest_engine.py`
**Stays:** Python service, invoked via NATS request/reply

**Rationale:** Backtesting is batch computation over historical DataFrames.
It shares code with the live strategies. Keeping it in Python means strategy
code is identical between backtest and live modes.

### 3. Market Data Fetchers
**Currently:** `src/data/public_data.py`, `src/data/market_data.py`, market-data-service
**Stays:** Python workers publishing to NATS

**Rationale:** The Polygon, yfinance, and Public.com client libraries are
Python-only. These workers fetch data on a schedule or in response to requests
and publish normalized market data to `market.data.*` subjects.

### 4. Portfolio Optimization
**Currently:** `src/portfolio/optimization/`
**Stays:** Python service using CVXPY, PyPortfolioOpt

**Rationale:** Convex optimization solvers are Python/C. This runs
periodically and publishes results to NATS.

### 5. ML/AI Pipeline
**Currently:** `src/services/ai/`, `services/llm-service`, `services/ai-decision-engine`
**Stays:** Python services

**Rationale:** LLM integrations, sentiment analysis, neural network inference -
all require Python's ML ecosystem.

### 6. Risk Computation
**Currently:** VaR calculations, correlation analysis, Monte Carlo in `src/risk/`
**Stays:** Python workers

**Rationale:** Heavy numerical computation. Publishes computed risk metrics
to NATS for Elixir's enforcement layer to consume.

### 7. Data Pipeline / ETL
**Currently:** `services/data-transformation-pipeline`
**Stays:** Python

**Rationale:** pandas-heavy transformation logic.

---

## NATS as the Messaging Backbone

### Why NATS over Kafka + RabbitMQ

| Aspect | Current (Kafka + RabbitMQ) | Proposed (NATS JetStream) |
|--------|---------------------------|---------------------------|
| Operational complexity | Two separate systems to maintain | Single system |
| Latency | Kafka optimized for throughput, not latency | Sub-millisecond publish |
| Protocol | Kafka's binary protocol + AMQP | Simple text protocol, trivial to debug |
| Persistence | Kafka topics + RabbitMQ queues | JetStream streams (unified) |
| Request/Reply | Not native | First-class pattern |
| Clustering | Zookeeper (Kafka) + Erlang clustering (RMQ) | Built-in RAFT consensus |
| Resource usage | Heavy (JVM for Kafka) | ~20MB RAM for NATS server |
| Client libraries | Good for both | Excellent for both Python and Elixir |

### Proposed NATS Subject Hierarchy

```
# Market Data (published by Python fetchers, consumed by Python strategies + Elixir engine)
market.data.{symbol}              # Real-time OHLCV + indicators
market.data.options.{symbol}      # Options chain updates
market.news.{symbol}              # News/sentiment updates

# Strategy Signals (published by Python strategy workers)
signals.{strategy_name}.{symbol}  # Individual strategy signals
signals.ensemble.{symbol}         # Ensemble/combined signals

# Risk (bidirectional)
risk.metrics.{symbol}             # Python -> Elixir: computed risk metrics
risk.check.request                # Elixir -> Python: request risk computation
risk.check.response               # Python -> Elixir: computation results
risk.breach.{level}               # Elixir -> all: risk limit breaches

# Orders (managed by Elixir)
orders.submit                     # New order requests
orders.status.{order_id}          # Order status updates
orders.fill.{order_id}            # Fill notifications
orders.cancel.{order_id}          # Cancellation requests

# Portfolio (bidirectional)
portfolio.positions                # Current positions snapshot
portfolio.update                   # Position changes
portfolio.optimization.request     # Request portfolio rebalance
portfolio.optimization.result      # Optimization results

# System
system.heartbeat.{service}        # Service health
system.config.reload              # Configuration updates
system.circuit_breaker.{service}  # Circuit breaker state changes

# Backtesting (request/reply via NATS)
backtest.request                   # Submit backtest job
backtest.status.{job_id}           # Job progress
backtest.result.{job_id}           # Completed results
```

### JetStream Streams Configuration

```
# Persistent streams (data must survive restarts)
MARKET_DATA     - subjects: market.data.>        - retention: 24h, interest-based
SIGNALS         - subjects: signals.>            - retention: 7d, limits-based
ORDERS          - subjects: orders.>             - retention: 90d, limits-based (audit trail)
RISK            - subjects: risk.>               - retention: 30d
PORTFOLIO       - subjects: portfolio.>          - retention: 30d
SYSTEM          - subjects: system.>             - retention: 7d

# Ephemeral (in-memory, speed over durability)
BACKTEST        - subjects: backtest.>           - retention: memory, 1h
```

---

## Elixir Application Structure

```
trading_platform_ex/
├── mix.exs
├── config/
│   ├── config.exs
│   ├── dev.exs
│   ├── prod.exs
│   └── runtime.exs              # Runtime config from env vars
├── lib/
│   ├── trading_platform/
│   │   ├── application.ex        # OTP Application + Supervisor tree
│   │   │
│   │   ├── engine/
│   │   │   ├── trading_engine.ex       # Core orchestrator GenServer
│   │   │   ├── symbol_supervisor.ex    # DynamicSupervisor for per-symbol processes
│   │   │   ├── symbol_worker.ex        # Per-symbol coordination process
│   │   │   └── trading_modes.ex        # Paper/Live/Backtest mode behavior
│   │   │
│   │   ├── orders/
│   │   │   ├── order_manager.ex        # Order registry and supervision
│   │   │   ├── order_fsm.ex            # GenStateMachine per order
│   │   │   ├── execution/
│   │   │   │   ├── public_com.ex       # Public.com execution adapter
│   │   │   │   └── paper.ex            # Paper trading execution
│   │   │   └── order_book.ex           # Active orders ETS table
│   │   │
│   │   ├── risk/
│   │   │   ├── risk_enforcer.ex        # Real-time risk gate GenServer
│   │   │   ├── risk_state.ex           # ETS-backed risk metrics cache
│   │   │   ├── circuit_breaker.ex      # Trading halt logic
│   │   │   └── position_limits.ex      # Position/concentration limits
│   │   │
│   │   ├── signals/
│   │   │   ├── signal_router.ex        # Routes signals from strategies
│   │   │   ├── signal_aggregator.ex    # Combines signals for ensemble
│   │   │   └── signal_validator.ex     # Basic signal sanity checks
│   │   │
│   │   ├── portfolio/
│   │   │   ├── portfolio_tracker.ex    # Real-time position tracking
│   │   │   └── position_store.ex       # ETS-backed position cache
│   │   │
│   │   ├── nats/
│   │   │   ├── connection.ex           # NATS connection supervisor
│   │   │   ├── publisher.ex            # Publish helper
│   │   │   ├── consumer.ex             # JetStream consumer behavior
│   │   │   └── subjects.ex             # Subject constants/helpers
│   │   │
│   │   ├── notifications/
│   │   │   ├── dispatcher.ex           # Fan-out to channels
│   │   │   ├── discord.ex              # Discord adapter
│   │   │   └── slack.ex                # Slack adapter
│   │   │
│   │   └── telemetry/
│   │       ├── metrics.ex              # Prometheus metrics
│   │       └── event_handler.ex        # Telemetry event handlers
│   │
│   └── trading_platform_web/
│       ├── router.ex                   # Phoenix router
│       ├── endpoint.ex                 # Phoenix endpoint
│       ├── controllers/                # REST API controllers
│       ├── channels/                   # WebSocket channels
│       └── live/                       # LiveView dashboards
│           ├── trading_dashboard_live.ex
│           ├── portfolio_live.ex
│           ├── risk_dashboard_live.ex
│           ├── backtest_live.ex
│           ├── signals_live.ex
│           └── system_health_live.ex
│
├── test/
│   ├── trading_platform/
│   │   ├── engine/
│   │   ├── orders/
│   │   ├── risk/
│   │   └── signals/
│   └── trading_platform_web/
│       ├── controllers/
│       └── live/
│
└── priv/
    └── static/                  # Static assets for LiveView
```

### OTP Supervision Tree

```
TradingPlatform.Application
├── TradingPlatform.Nats.Connection          # NATS connection pool
├── TradingPlatform.Engine.TradingEngine     # Core orchestrator
├── TradingPlatform.Engine.SymbolSupervisor  # DynamicSupervisor
│   ├── SymbolWorker(:AAPL)                  # Per-symbol process
│   ├── SymbolWorker(:GOOGL)
│   └── SymbolWorker(:...)
├── TradingPlatform.Orders.OrderManager      # Order DynamicSupervisor
│   ├── OrderFSM(order_123)                  # Per-order state machine
│   ├── OrderFSM(order_124)
│   └── OrderFSM(...)
├── TradingPlatform.Risk.RiskEnforcer        # Risk enforcement
├── TradingPlatform.Signals.SignalRouter      # Signal routing
├── TradingPlatform.Portfolio.PortfolioTracker
├── TradingPlatform.Notifications.Dispatcher
│   ├── Discord adapter
│   └── Slack adapter
├── TradingPlatform.Telemetry.Metrics
└── TradingPlatformWeb.Endpoint              # Phoenix HTTP/WS
```

---

## Python Application Structure (Refactored)

The Python side simplifies considerably - it becomes a collection of NATS-connected
workers rather than a monolithic application with its own HTTP layer.

```
trading_platform_py/
├── pyproject.toml
├── src/
│   ├── common/
│   │   ├── nats_client.py           # Shared NATS connection + helpers
│   │   ├── models.py                # Shared data models (Pydantic)
│   │   ├── config.py                # Configuration (from current src/utils/config.py)
│   │   └── logging.py               # Structured logging setup
│   │
│   ├── strategies/                   # All 50+ strategies (largely unchanged)
│   │   ├── base_strategy.py          # BaseStrategy with NATS integration
│   │   ├── sma_crossover.py
│   │   ├── rsi_strategy.py
│   │   ├── elliott_wave.py
│   │   ├── iron_condor.py
│   │   └── ...                       # All existing strategies
│   │
│   ├── workers/
│   │   ├── strategy_runner.py        # Runs strategy workers (subscribes to market data, publishes signals)
│   │   ├── market_data_fetcher.py    # Fetches from Polygon/yfinance/Public.com, publishes to NATS
│   │   ├── risk_computer.py          # Computes VaR, correlation, etc., publishes metrics
│   │   ├── portfolio_optimizer.py    # Runs optimization on request, publishes results
│   │   ├── backtester.py             # Handles backtest requests via NATS request/reply
│   │   ├── ml_inference.py           # ML model inference worker
│   │   ├── news_analyzer.py          # News sentiment analysis
│   │   └── llm_service.py            # LLM provider integration
│   │
│   ├── data/
│   │   ├── polygon_client.py         # Polygon.io API client
│   │   ├── yfinance_client.py        # yfinance wrapper
│   │   ├── public_com_client.py      # Public.com API client (data only)
│   │   └── data_normalizer.py        # Normalize data from different sources
│   │
│   ├── backtesting/                  # Backtesting engine (largely unchanged)
│   │   ├── engine.py
│   │   └── optimized_engine.py
│   │
│   ├── portfolio/
│   │   └── optimization/             # CVXPY/PyPortfolioOpt (unchanged)
│   │
│   └── risk/
│       └── computation/              # VaR, Monte Carlo, etc. (unchanged)
│
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

### Key Change: BaseStrategy NATS Integration

Strategies currently receive market data through the trading engine's loop.
In the new model, each strategy worker subscribes directly to NATS:

```python
# Simplified view of the new strategy runner pattern
class StrategyRunner:
    """Runs a strategy as a NATS-connected worker."""

    async def run(self, strategy: BaseStrategy, symbols: list[str]):
        nc = await nats.connect(NATS_URL)
        js = nc.jetstream()

        for symbol in symbols:
            await js.subscribe(
                f"market.data.{symbol}",
                cb=lambda msg: self._on_market_data(strategy, msg),
                durable=f"{strategy.name}-{symbol}",
            )

    async def _on_market_data(self, strategy, msg):
        market_data = deserialize(msg.data)
        signal = await strategy.generate_signal(market_data)
        if signal:
            await self.nc.publish(
                f"signals.{strategy.name}.{market_data.symbol}",
                serialize(signal),
            )
```

---

## Services Consolidation Map

One major benefit: the current 54 microservices consolidate significantly.

| Current Service(s) | Becomes | Language |
|---|---|---|
| `gateway`, `command-api`, `query-api` | Phoenix API (single app) | Elixir |
| `trading-dashboard-service`, `ai-stock-dashboard`, `unified-analytics-dashboard`, `unified-trading-dashboard`, `performance-dashboard`, `data-pipeline-dashboard`, `rss-dashboard`, `report-viewer-service` | Phoenix LiveView (single app) | Elixir |
| `order-service` | `TradingPlatform.Orders` (OTP) | Elixir |
| `risk-service`, `risk-integration-service` | Split: enforcement (Elixir) + computation (Python) | Both |
| `signal-management-service` | `TradingPlatform.Signals` (OTP) | Elixir |
| `notification-service` | `TradingPlatform.Notifications` (OTP) | Elixir |
| `trading-service`, `live-trading-service` | `TradingPlatform.Engine` (OTP) + Python execution client | Both |
| `strategy-service` | Python strategy workers | Python |
| `market-data-service`, `market-data-worker` | Python market data workers | Python |
| `backtest-api`, `backtest-request-service` | Python backtest worker + Phoenix LiveView UI | Both |
| `llm-service`, `ai-decision-engine` | Python ML workers | Python |
| `analytics-service` | Python computation + LiveView display | Both |
| `elliott-wave-service` | Python strategy worker (as today) | Python |
| `data-analysis-service`, `data-transformation-pipeline` | Python ETL workers | Python |
| `fundamental-analysis-service`, `earnings-data-service` | Python data workers | Python |
| `unified-news-dashboard`, `rss-feed-service` | Python fetcher + LiveView display | Both |
| `vector-database-service`, `postgres-vector-storage`, `background-vectorization-service`, `architecture-vectorizer` | Python workers (unchanged) | Python |
| `trading-monitor` | Elixir telemetry + LiveView | Elixir |
| `kubernetes-rag-chat`, `mcp-service`, `ai-ide-service` | Python services (unchanged) | Python |
| `public-api` | Absorbed into Python data client + Elixir execution adapter | Both |

**Result: ~54 services -> ~12 deployable units** (1 Elixir release + ~8-10 Python worker types + NATS + databases)

---

## Database Strategy

### Keep PostgreSQL, Simplify the Topology

- **Drop the read/write split** initially. Elixir's ETS tables and NATS
  caching reduce read load on Postgres dramatically. The current CQRS
  read/write DB separation adds operational complexity.
- **Single PostgreSQL** instance with Elixir's Ecto for schema management
  and migrations (replacing Alembic).
- **Keep TimescaleDB** for time-series market data (Python workers write,
  both languages read).
- **Drop EventStore** as a separate service. NATS JetStream streams provide
  the event log. For replay, consume from JetStream with historical delivery policy.
- **Keep Redis** for short-lived caches where ETS isn't sufficient (cross-node
  caching in a clustered deployment).
- **Drop InfluxDB** - TimescaleDB covers time-series needs.

---

## Migration Strategy: Phased Approach

### Phase 1: NATS Foundation + Elixir Skeleton
- Deploy NATS JetStream alongside existing infrastructure
- Create Elixir umbrella project with Phoenix
- Build `TradingPlatform.Nats` connection module
- Add NATS publishing to existing Python services (dual-write: existing + NATS)
- Build first LiveView dashboard (system health / NATS monitoring)

### Phase 2: Signal Pipeline Migration
- Python strategy workers subscribe to NATS for market data
- Python strategy workers publish signals to NATS
- Build Elixir `SignalRouter` consuming from NATS
- Elixir `SignalRouter` replaces `signal-management-service`
- First end-to-end flow: market data -> strategy -> signal -> Elixir router

### Phase 3: Order Management Migration
- Build Elixir `OrderFSM` and `OrderManager`
- Build execution adapters (Public.com, paper)
- Elixir order management replaces `order-service`
- Orders flow: Elixir signal router -> risk check -> order FSM -> execution

### Phase 4: Risk Enforcement Migration
- Build Elixir `RiskEnforcer` with ETS-backed state
- Python risk computation workers publish metrics to NATS
- Elixir enforces limits in the order path
- Replaces `risk-service` / `risk-integration-service`

### Phase 5: Trading Engine Orchestrator
- Build Elixir `TradingEngine` GenServer
- Build `SymbolSupervisor` + `SymbolWorker` processes
- Elixir becomes the brain; Python becomes the muscle
- Replaces `trading-service` / `live-trading-service` orchestration

### Phase 6: Dashboard Consolidation
- Migrate dashboards to Phoenix LiveView one at a time
- Trading dashboard, portfolio, risk, signals, backtesting
- Retire individual dashboard services as each LiveView is ready

### Phase 7: Decommission Legacy Infrastructure
- Remove Kafka (fully replaced by NATS)
- Remove RabbitMQ (fully replaced by NATS)
- Consolidate databases (drop EventStore, InfluxDB)
- Remove retired Python services
- Update Kubernetes manifests for new topology

---

## Inter-Language Communication Contract

All messages on NATS use **JSON** encoding with a shared schema:

```json
{
  "id": "uuid-v4",
  "timestamp": "2026-02-17T12:00:00.000Z",
  "source": "strategy.sma_crossover",
  "type": "signal",
  "payload": { ... }
}
```

**Schema validation:** JSON Schema definitions shared between Python (Pydantic
models) and Elixir (ExJsonSchema or custom structs with changesets). Schemas
live in a shared `schemas/` directory at the repo root.

```
schemas/
├── market_data.json
├── signal.json
├── order.json
├── risk_metrics.json
├── portfolio_update.json
└── system_event.json
```

---

## Deployment Topology

```
Kubernetes Cluster
├── nats (StatefulSet, 3 replicas, JetStream enabled)
├── postgresql (StatefulSet, single primary)
├── timescaledb (StatefulSet, single primary)
├── redis (StatefulSet, single primary)
│
├── trading-platform-ex (Deployment, Elixir release)
│   ├── Phoenix endpoint (HTTP + WS)
│   ├── Trading engine orchestrator
│   ├── Order management
│   ├── Risk enforcement
│   ├── Signal routing
│   └── Notification dispatch
│
├── strategy-workers (Deployment, N replicas)
│   └── Python strategy runner (all strategies)
│
├── market-data-workers (Deployment, 2 replicas)
│   └── Python market data fetcher
│
├── risk-compute-workers (Deployment, 2 replicas)
│   └── Python risk computation
│
├── backtest-workers (Deployment, 2 replicas, scales to 0)
│   └── Python backtesting engine
│
├── ml-workers (Deployment, 1-2 replicas)
│   └── Python ML/AI inference
│
├── portfolio-optimizer (Deployment, 1 replica)
│   └── Python portfolio optimization
│
├── news-workers (Deployment, 1 replica)
│   └── Python news/sentiment analysis
│
└── monitoring
    ├── prometheus
    └── grafana
```

---

## Key Technical Decisions & Trade-offs

### 1. Elixir Release vs. Umbrella App
**Recommendation:** Single Elixir application (not umbrella). The trading
engine, orders, risk, and signals are tightly coupled in the hot path. An
umbrella adds complexity without benefit since they deploy together anyway.

### 2. NATS Client Libraries
- **Python:** `nats-py` (official, async, well-maintained)
- **Elixir:** `gnat` (most mature Elixir NATS client, supports JetStream)

### 3. Public.com API Calls: Python or Elixir?
**Recommendation:** Elixir for order execution, Python for data fetching.
The order execution path should be fully in Elixir (low latency, supervised).
Elixir's `Req` or `Finch` HTTP clients handle REST API calls efficiently.
Data fetching (account sync, position queries) can stay in Python since it's
not latency-critical.

### 4. Database Access: Dual or Single Language?
**Recommendation:** Elixir owns the database via Ecto. Python workers are
stateless - they read from NATS and write to NATS. If a Python worker needs
historical data, it requests it via NATS (Elixir serves it from DB/cache)
or queries TimescaleDB directly (read-only) for bulk historical data.

### 5. Configuration Management
- **Elixir:** `runtime.exs` reading from environment variables (same pattern as current `.env`)
- **Python:** Current `config.py` adapted for NATS connection settings
- **Shared:** Strategy configurations (YAML) read by Python, published to NATS for Elixir awareness

### 6. Observability
- Both languages export **Prometheus metrics** (Elixir via `telemetry` + `prom_ex`, Python via `prometheus_client`)
- Both write **structured JSON logs** (Elixir via `Logger` + JSON formatter, Python via `structlog`)
- **Distributed tracing:** OpenTelemetry (both languages have good support)
- NATS subjects provide natural trace boundaries

---

## What Gets Deleted / Retired

- **Kafka** infrastructure and all Kafka consumer/producer code
- **RabbitMQ** infrastructure and `src/services/queue/rabbitmq_service.py`
- **EventStore** (replaced by NATS JetStream)
- **InfluxDB** (replaced by TimescaleDB)
- **8 separate dashboard services** (replaced by LiveView)
- **Gateway service** (replaced by Phoenix)
- **CQRS services** (`command-api`, `query-api`) - absorbed into Phoenix
- **Signal management service** - absorbed into Elixir
- **Order service** - absorbed into Elixir
- **Notification service** - absorbed into Elixir
- Current `src/main.py` / `AlgoTrader` class (orchestration moves to Elixir)
- Current `src/core/trading_engine.py` (replaced by Elixir GenServer)
- Current `src/api/` (replaced by Phoenix)

---

## Developer Tooling (decided 2026-07-05)

The current make system (26 makefiles, ~530 targets, all `.PHONY`) is used
purely as a command runner. **Decision: do not port it.** The makefiles stay
as-is until the v2 rework; a `justfile` is introduced *with* v2, containing
only targets that earn their place in the new architecture (same pruning rule
as strategies).

- **First domains to cover:** backtesting, live/paper trading operations.
- **Division of labor:** `mix` aliases own the Elixir build/test/release
  lifecycle; `just` covers cross-cutting ops and Python job invocation; Salt
  owns provisioning.
- Recipe names should be flat and kebab-case so existing `make <target>`
  muscle memory and docs translate 1:1 where a target survives.
- The same make-to-just approach is planned for the Bot Army repos.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Team needs to learn Elixir | Start with Phase 1 (skeleton + LiveView). LiveView provides quick wins and builds familiarity. |
| NATS is less battle-tested than Kafka for financial systems | NATS is used in production at major financial institutions. JetStream provides the durability guarantees needed. Run in parallel during migration. |
| Dual-language debugging complexity | Structured logging with correlation IDs. OpenTelemetry tracing spans across NATS messages. NATS monitoring tools. |
| Strategy code changes require coordination | Strategy interface is a NATS contract (market data in, signals out). Python side is fully independent - deploy without touching Elixir. |
| Data serialization overhead (JSON on NATS) | JSON is fine for this throughput level. Can upgrade to Protobuf or MessagePack later if profiling shows serialization as a bottleneck. |
| Migration duration | Phased approach means each phase delivers value independently. Can pause between phases. Old and new systems coexist during transition. |
