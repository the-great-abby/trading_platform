# Service Topology

Factual map of the platform's services, ports, dependencies, and data flows.
Generated from code inspection (compose files, k8s manifests, per-service
`main.py`) on 2026-07-05. Where a Dockerfile `EXPOSE` disagrees with the
port in `uvicorn.run(...)`, the **code port is authoritative** and noted.

## ⚠️ Read first: there are two parallel worlds

This repo contains two topologies that **do not match**:

1. **The docker-compose world** — a textbook CQRS stack of ~9 logical
   services (gateway, command/query APIs, 8 domain services). The domain
   services here are lightweight stubs under `services/<name>/main.py`.
2. **The Kubernetes world** — 54 real service directories under
   `services/`, deployed individually into the `trading-system` namespace
   via raw `kubectl apply -f k8s/<name>.yaml`.

Most of the 54 services are **not** in any compose file, and the compose
"trading-service" etc. are not the same components as the richer k8s
services (`live-trading-service`, `risk-management-service`,
`trading-ultra-service`, …). Never assume compose and k8s deploy the same
thing.

## Service inventory (k8s world)

Ports listed are the actual listening ports from code. "env `port`" means
the service reads a `PORT` env var (default 8000).

### Core trading / execution

| Service | Purpose | Port | Key dependencies |
|---|---|---|---|
| gateway | Central API entry; proxies + health-aggregates downstream services | 8000 | market-data, backtest-api, dashboards, ai-analysis, llm |
| live-trading-service | Live trading via Public.com (has own alembic, routes, recovery CLI) | 8080 | Postgres, `ENCRYPTION_KEY` secret |
| trading-service | Internal trading ops | env `port` | infra via compose env |
| trading-core-service | Consolidated multi-function trading service | 11090 | Postgres, RabbitMQ |
| trading-engine | Trading engine w/ Prometheus metrics (**deprecated 2025-10-07, scaled to 0**) | 11080 | Postgres, TimescaleDB |
| trading-ultra-service | "Everything in one" ultra-consolidated service | 11099 | Postgres, Ollama, TimescaleDB |
| order-service | Order management | env `port` | write-db/eventstore/kafka (compose only) |
| signal-management-service | Signal operations (**dormant — scaled to 0 in consolidation**) | env `port` | — |
| strategy-service | Core trading logic + backtesting; **the hub of the HTTP graph** | env `port` | Postgres, Ollama |
| risk-service | Risk microservice | env `port` | — |
| risk-management-service | Full risk app (VaR etc.); metrics on 9090 | 8080 | own `risk_management` DB |
| risk-integration-service | Risk integration | 8080 | — |
| portfolio-service | Advanced portfolio service | 8000 | read-db, Redis |
| public-api | Public.com broker adapter | 8000 | Public.com credentials |

### Market / data

| Service | Purpose | Port | Key dependencies |
|---|---|---|---|
| market-data-service | Market data API | env `port` | read-db, Redis, public-api |
| market-data-worker | Background market-data worker | (worker) | RabbitMQ, Postgres |
| data-processing-service | Consolidated background processing | 11095 | Postgres |
| data-analysis-service | Data analysis | 11136 | Postgres |
| data-transformation-pipeline | ETL pipeline | 11135 | Postgres, RabbitMQ |
| data-pipeline-dashboard | Pipeline monitoring UI | 11137 | Postgres |
| earnings-data-service | Earnings data | 8000 | Postgres, Polygon, TimescaleDB |
| fundamental-analysis-service | Fundamental analysis | env `port` | Polygon, LLM |
| rss-feed-service | RSS feeds of daily trade recommendations | **11004** (EXPOSE says 8084) | Postgres, Polygon, RabbitMQ, strategy-service |
| elliott-wave-service | Elliott Wave pattern analysis | 8000 | options data |

### AI / LLM / vector / RAG

| Service | Purpose | Port | Key dependencies |
|---|---|---|---|
| ai-analysis-service | Buy/sell recommendations via LLM | 11085 | Postgres, Ollama |
| ai-decision-engine | Real-time investment recs (**dir only — no Dockerfile, not deployable as-is**) | 8000 | Postgres, LLM |
| ai-query-interface | NL interface to market data (**dir only**) | 8000 | TimescaleDB, LLM |
| ai-ide-service | Cursor IDE ↔ local AI bridge | 11050 | TimescaleDB, LLM |
| ai-stock-dashboard | AI stock analysis dashboard | 8000 | Postgres, LLM, TimescaleDB |
| llm-service | LLM service for RAG search | 8008 | Ollama |
| llm-worker | LLM background worker | (worker) | LLM |
| mcp-service | MCP tools service | 8000 | LLM |
| kubernetes-rag-chat | RAG chat over k8s/architecture docs | 8000 | LLM, vector store |
| architecture-vectorizer | Architecture embedding | 8000 | LLM, vector store |
| background-vectorization-service | Async vectorization | 8080 | Postgres, LLM, TimescaleDB |
| vector-database-service | Semantic search (**dir only — single main.py**) | 8000 | pgvector, LLM |
| postgres-vector-storage | pgvector storage layer | 8000 | Postgres (pgvector), LLM |

### Dashboards / UI / reporting

| Service | Purpose | Port | Key dependencies |
|---|---|---|---|
| unified-trading-dashboard | Unified trading dashboard | **80** (EXPOSE 8080) | Postgres, Redis, LLM, TimescaleDB |
| unified-analytics-dashboard | Unified analytics (single ~4k-line main.py) | **80** (EXPOSE 8080) | Postgres, LLM, TimescaleDB |
| unified-news-dashboard | Unified news dashboard | env `port` | Postgres |
| trading-dashboard-service | Trade/strategy event feeds + dashboard | 8000 | strategy-service, market-data |
| performance-dashboard | Trade performance dashboard | 8000 | Postgres |
| rss-dashboard | Real-time RSS viewer | **8085** (EXPOSE 8080) | rss-feed-service |
| trading-monitor | Trading engine monitor | 8080 | Postgres, TimescaleDB |
| report-viewer-service | Browse backtest reports | 8084 | Postgres |
| backtest-request-service | Web UI to submit backtests | 8082 | Postgres, Polygon, LLM |
| backtest-api | Backtest API | env | backtest data PVC |

### Support

| Service | Purpose | Port | Key dependencies |
|---|---|---|---|
| analytics-service | Analytics & reporting | env `port` | read-db, Redis, InfluxDB |
| user-service | User management, JWT | env `port` | write-db, eventstore, kafka |
| notification-service | Email on backtest completion | 8083 | SMTP |
| command-api | CQRS write API | 8000 | write-db, EventStore, Kafka |
| query-api | CQRS read API | 8000 | read-db, Redis |

## Main flows

- **HTTP fan-out from gateway** (`gateway/main.py`, via `*_URL` env vars):
  market-data (:8002), backtest-api (:8003), trading-dashboard (:8004),
  health-dashboard (:8005), ai-analysis (:11085), llm (:12001),
  central-hub (:11080).
- **The hub is strategy-service.** Ranked by inbound references across
  service code: `STRATEGY_SERVICE_URL` (11), `NOTIFICATION_SERVICE_URL` (9),
  `RISK_SERVICE_URL` (7), `RSS_SERVICE_URL` (6), `ANALYSIS_SERVICE_URL` (6),
  `MARKET_DATA_SERVICE_URL` (4), `ORDER_SERVICE_URL` (2). Market data feeds
  strategy; order/risk/notification sit downstream.
- **Trade recommendation path:** Elliott Wave + strategy signals →
  unified-trading-dashboard (`:11001/api/trading/recommendations`);
  rss-feed-service pulls strategy-service + Polygon and publishes recs;
  rss-dashboard renders them.
- **CQRS event-sourcing path exists only in the compose world**
  (command side → write-db + EventStore + Kafka; query side → read-db +
  Redis). It is not reflected in the k8s manifests.

## Shared infrastructure

| Infra | Reality |
|---|---|
| PostgreSQL/TimescaleDB | The de-facto production DB is `timescaledb.trading-system.svc.cluster.local:5432/trading_bot` (26 manifest refs). Also: external `postgres-timescale-external.postgres-infra`, pgvector store `postgres-vector-external.postgres-infra`, a separate `risk_management` DB, plus compose-only `write-db`/`read-db`/`postgres-dev`. **15+ distinct Postgres URLs exist across manifests — there is no single source of truth.** |
| Redis | `redis.redis.svc.cluster.local:6379` — this k8s DNS name is hard-coded even in compose files whose Redis container is named `redis-dev` (a known misconfiguration). |
| Kafka | Infra containers + env vars exist, but **no `services/*/main.py` imports a Kafka client** — effectively unused/aspirational outside compose CQRS stubs. |
| EventStore | Same: compose-world only, no k8s service code uses it. |
| RabbitMQ | Real users: data-transformation-pipeline, market-data-worker, rss-feed-service, trading-core-service; plus cronjob-driven LLM/order queue workers. `amqp://trading:…@rabbitmq:5672/trading_vhost`. |
| InfluxDB | `docker-compose.yml` only (market-data, analytics). Not in dev compose or k8s. |
| Ollama/LLM | Dedicated `ollama-controller` namespace (API :12001, Ollama :11434). Consumed by all AI/RAG/vector services, gateway, dashboards. |
| Monitoring | Prometheus + Grafana in both worlds; exporters (node, postgres, rabbitmq) in k8s. ELK only in `docker-compose.yml`. |

## Dormant / dead / not-deployable (verified)

- **Scaled to 0 in normal operation** (`services-consolidate-*` targets):
  trading-engine, signal-management-service, strategy-service (sic), several
  dashboards.
- **Dir-only, no Dockerfile/requirements** — not independently deployable:
  ai-decision-engine, ai-query-interface, vector-database-service.
- **`k8s/deprecated/`**: 16 retired manifests; various manifests carry
  `# DEPRECATED: 2025-10-07` markers.
- Root-level `*_COMPLETE.md` / `*_SUMMARY.md` files are historical status
  notes, not authoritative architecture docs.

## Relation to the v2 plan

This topology is the "before" picture. The v2 consolidation map (which of
these ~54 services become which of ~12 deployable units) lives in
`hybrid-python-elixir-plan.md` in this directory. The Kafka/EventStore
findings above support the v2 decision to standardize on NATS: the busiest
real transport today is HTTP + RabbitMQ, not Kafka.
