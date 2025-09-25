# Trading System Constitution

## Core Principles

### I. Kubernetes-First Architecture
All services must be containerized and deployable via Kubernetes; Microservices architecture with clear service boundaries; Each service must have health checks, metrics, and logging

### II. Options Trading Focus
Features must support options strategies (Iron Condor, Covered Calls, Cash-Secured Puts); Real-time market data integration required; Greeks calculations for risk management

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced; All strategies must have backtest validation

### IV. Risk Management Integration
Every trading feature must include risk controls; Position sizing and portfolio limits enforced; Real-time P&L tracking required

### V. Observability & Monitoring
Structured logging required; Metrics collection for all trading activities; Performance monitoring for strategy execution; Alert system for risk breaches

## Technology Stack Requirements
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, asyncio
- **Database**: PostgreSQL/TimescaleDB for time-series data, Redis for caching
- **Containerization**: Docker with multi-stage builds, Kubernetes deployment
- **Market Data**: Polygon API, Alpha Vantage API with proper caching
- **Monitoring**: Prometheus metrics, Grafana dashboards, structured logging
- **Testing**: pytest, pytest-asyncio, mock data for backtesting
- **Port Management**: 11000-11999 range, PORT_MAP.md tracking

## Development Workflow
- **Code Review**: All PRs must verify compliance with trading system principles
- **Testing Gates**: Unit tests, integration tests, backtest validation required
- **Deployment**: Kubernetes rolling updates with health checks
- **Documentation**: API docs, strategy documentation, PORT_MAP.md updates required
- **Configuration**: Centralized in `src/utils/trading_config.py`
- **Risk Management**: Position sizing, stop-losses, portfolio limits mandatory

## Governance
Constitution supersedes all other practices; Amendments require documentation, approval, migration plan

All PRs/reviews must verify compliance; Complexity must be justified; Use PORT_MAP.md for infrastructure tracking; Use spec-kit for feature development

**Version**: 1.0.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20