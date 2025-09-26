# Tasks: Live Trading System with Public.com API

**Input**: Design documents from `/specs/008-title-live-trading/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Found: Python 3.11+, FastAPI, SQLAlchemy, asyncio, httpx, redis, psycopg2-binary
   → ✅ Extract: Trading system architecture, Kubernetes deployment
2. Load optional design documents:
   → ✅ data-model.md: 7 entities → 7 model tasks
   → ✅ contracts/: 1 OpenAPI file → 1 contract test task
   → ✅ research.md: Public.com API integration, risk management sharing
3. Generate tasks by category:
   → Setup: live-trading-service project init, dependencies, linting
   → Tests: contract tests, integration tests, backtest validation
   → Core: 7 entity models, services, API endpoints
   → Integration: DB, Public.com API, risk management, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → ✅ All contracts have tests
   → ✅ All entities have models
   → ✅ All endpoints implemented
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Trading System**: `services/`, `src/`, `k8s/`, `tests/` at repository root
- **Services**: `services/live-trading-service/` for new microservice
- **Models**: `src/services/live_trading/models.py` for entity models
- **API**: `services/live-trading-service/main.py` for FastAPI application
- **Deployments**: `k8s/live-trading-service.yaml` for Kubernetes manifest
- **Testing**: `tests/live_trading/` with contract, integration, unit tests

## Phase 3.1: Setup
- [x] T001 Create live-trading-service project structure in services/live-trading-service/
- [x] T002 Initialize Python project with FastAPI, SQLAlchemy, asyncio, httpx, redis, psycopg2-binary dependencies in services/live-trading-service/requirements.txt
- [x] T003 [P] Configure linting and formatting tools (black, isort, flake8) in services/live-trading-service/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [x] T004 [P] Contract test OpenAPI specification in tests/live_trading/contract/test_openapi_contract.py
- [x] T005 [P] Integration test Public.com API authentication in tests/live_trading/integration/test_public_api_auth.py
- [x] T006 [P] Integration test live trade execution in tests/live_trading/integration/test_live_trade_execution.py
- [x] T007 [P] Integration test risk management enforcement in tests/live_trading/integration/test_risk_enforcement.py
- [x] T008 [P] Integration test market hours enforcement in tests/live_trading/integration/test_market_hours.py
- [x] T009 [P] Integration test emergency stop functionality in tests/live_trading/integration/test_emergency_stop.py
- [x] T010 [P] Integration test position tracking and P&L in tests/live_trading/integration/test_position_tracking.py
- [x] T011 [P] Backtest validation for Iron Condor strategy in tests/live_trading/backtesting/test_iron_condor_backtest.py
- [x] T012 [P] Backtest validation for Butterfly Spread strategy in tests/live_trading/backtesting/test_butterfly_backtest.py
- [x] T013 [P] Backtest validation for Calendar Spread strategy in tests/live_trading/backtesting/test_calendar_backtest.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Entity Models (Parallel)
- [x] T014 [P] LiveTradingAccount model in src/services/live_trading/models.py (lines 1-50)
- [x] T015 [P] LivePosition model in src/services/live_trading/models.py (lines 51-100)
- [x] T016 [P] LiveTrade model in src/services/live_trading/models.py (lines 101-150)
- [x] T017 [P] RiskProfile model in src/services/live_trading/models.py (lines 151-200)
- [x] T018 [P] APICredentials model in src/services/live_trading/models.py (lines 201-250)
- [x] T019 [P] TradeSignal model in src/services/live_trading/models.py (lines 251-300)
- [x] T020 [P] OrderStatus model in src/services/live_trading/models.py (lines 301-350)

### Database Setup
- [x] T021 Create database migration for live trading tables in src/services/live_trading/migrations/001_create_live_trading_tables.py
- [x] T022 Create database indexes and constraints in src/services/live_trading/migrations/002_create_indexes.py

### Core Services (Sequential)
- [x] T023 Public.com API client in src/services/live_trading/public_api_client.py
- [x] T024 Risk management service in src/services/live_trading/risk_service.py
- [x] T025 Trading service in src/services/live_trading/trading_service.py
- [x] T026 Position management service in src/services/live_trading/position_service.py
- [x] T027 Market hours service in src/services/live_trading/market_hours_service.py

### API Endpoints (Sequential)
- [x] T028 Authentication endpoints in services/live-trading-service/routes/auth.py
- [x] T029 Account management endpoints in services/live-trading-service/routes/accounts.py
- [x] T030 Trading endpoints in services/live-trading-service/routes/trading.py
- [x] T031 Risk management endpoints in services/live-trading-service/routes/risk.py
- [x] T032 System status endpoints in services/live-trading-service/routes/status.py

### Infrastructure
- [x] T033 [P] Dockerfile for live-trading-service in services/live-trading-service/Dockerfile
- [x] T034 [P] Kubernetes deployment manifest in k8s/live-trading-service.yaml
- [ ] T035 [P] Configuration updates in src/utils/trading_config.py (add live trading config)
- [ ] T036 [P] PORT_MAP.md updates for live-trading-service (port 11120)

## Phase 3.4: Integration
- [x] T037 Connect live trading service to PostgreSQL database
- [x] T038 Integrate with Redis for caching and session management
- [x] T039 Implement Public.com API authentication and token management
- [x] T040 Connect to shared risk management components
- [x] T041 Implement structured logging and metrics collection
- [x] T042 Add CORS and security headers for API endpoints
- [x] T043 Implement health checks and readiness probes

## Phase 3.5: Polish
- [ ] T044 [P] Unit tests for entity models in tests/live_trading/unit/test_models.py
- [ ] T045 [P] Unit tests for Public.com API client in tests/live_trading/unit/test_public_api_client.py
- [ ] T046 [P] Unit tests for risk management service in tests/live_trading/unit/test_risk_service.py
- [ ] T047 [P] Unit tests for trading service in tests/live_trading/unit/test_trading_service.py
- [ ] T048 [P] Unit tests for position management service in tests/live_trading/unit/test_position_service.py
- [ ] T049 [P] Unit tests for market hours service in tests/live_trading/unit/test_market_hours_service.py
- [ ] T050 Performance tests (<200ms API response) in tests/live_trading/performance/test_api_performance.py
- [ ] T051 [P] Update API documentation in docs/live-trading-api.md
- [ ] T052 [P] Update system architecture documentation in docs/live-trading-architecture.md
- [ ] T053 Remove code duplication and refactor common patterns
- [ ] T054 Run quickstart.md validation tests

## Dependencies
- Setup (T001-T003) before everything
- Tests (T004-T013) before implementation (T014-T036) - TDD requirement
- Entity models (T014-T020) before database migrations (T021-T022)
- Database migrations (T021-T022) before services (T023-T027)
- Services (T023-T027) before API endpoints (T028-T032)
- API endpoints (T028-T032) before infrastructure (T033-T036)
- Core implementation (T014-T036) before integration (T037-T043)
- Integration (T037-T043) before polish (T044-T054)

## Parallel Execution Examples

### Phase 3.2: Launch all contract tests together
```bash
# T004-T013 can run in parallel (different test files)
Task: "Contract test OpenAPI specification in tests/live_trading/contract/test_openapi_contract.py"
Task: "Integration test Public.com API authentication in tests/live_trading/integration/test_public_api_auth.py"
Task: "Integration test live trade execution in tests/live_trading/integration/test_live_trade_execution.py"
Task: "Integration test risk management enforcement in tests/live_trading/integration/test_risk_enforcement.py"
Task: "Integration test market hours enforcement in tests/live_trading/integration/test_market_hours.py"
Task: "Integration test emergency stop functionality in tests/live_trading/integration/test_emergency_stop.py"
Task: "Integration test position tracking and P&L in tests/live_trading/integration/test_position_tracking.py"
Task: "Backtest validation for Iron Condor strategy in tests/live_trading/backtesting/test_iron_condor_backtest.py"
Task: "Backtest validation for Butterfly Spread strategy in tests/live_trading/backtesting/test_butterfly_backtest.py"
Task: "Backtest validation for Calendar Spread strategy in tests/live_trading/backtesting/test_calendar_backtest.py"
```

### Phase 3.3: Launch entity models together
```bash
# T014-T020 can run in parallel (different lines in same file)
Task: "LiveTradingAccount model in src/services/live_trading/models.py (lines 1-50)"
Task: "LivePosition model in src/services/live_trading/models.py (lines 51-100)"
Task: "LiveTrade model in src/services/live_trading/models.py (lines 101-150)"
Task: "RiskProfile model in src/services/live_trading/models.py (lines 151-200)"
Task: "APICredentials model in src/services/live_trading/models.py (lines 201-250)"
Task: "TradeSignal model in src/services/live_trading/models.py (lines 251-300)"
Task: "OrderStatus model in src/services/live_trading/models.py (lines 301-350)"
```

### Phase 3.3: Launch infrastructure tasks together
```bash
# T033-T036 can run in parallel (different files)
Task: "Dockerfile for live-trading-service in services/live-trading-service/Dockerfile"
Task: "Kubernetes deployment manifest in k8s/live-trading-service.yaml"
Task: "Configuration updates in src/utils/trading_config.py"
Task: "PORT_MAP.md updates for live-trading-service"
```

### Phase 3.5: Launch unit tests together
```bash
# T044-T049 can run in parallel (different test files)
Task: "Unit tests for entity models in tests/live_trading/unit/test_models.py"
Task: "Unit tests for Public.com API client in tests/live_trading/unit/test_public_api_client.py"
Task: "Unit tests for risk management service in tests/live_trading/unit/test_risk_service.py"
Task: "Unit tests for trading service in tests/live_trading/unit/test_trading_service.py"
Task: "Unit tests for position management service in tests/live_trading/unit/test_position_service.py"
Task: "Unit tests for market hours service in tests/live_trading/unit/test_market_hours_service.py"
```

## Task Generation Rules Applied

1. **From Contracts**: ✅
   - 1 OpenAPI contract file → 1 contract test task (T004)
   - 15 endpoints → 5 sequential endpoint implementation tasks (T028-T032)

2. **From Data Model**: ✅
   - 7 entities → 7 parallel model creation tasks (T014-T020)
   - Relationships → database migration tasks (T021-T022)

3. **From User Stories**: ✅
   - 5 acceptance scenarios → 7 integration test tasks (T005-T010)
   - 3 strategies → 3 backtest validation tasks (T011-T013)

4. **Ordering**: ✅
   - Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - Dependencies properly block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (OpenAPI → T004)
- [x] All entities have model tasks (7 entities → T014-T020)
- [x] All tests come before implementation (T004-T013 before T014-T036)
- [x] Parallel tasks truly independent (different files or different line ranges)
- [x] Each task specifies exact file path and line ranges where applicable
- [x] No task modifies same file as another [P] task (proper line range separation)

## Notes
- **[P] tasks**: Different files or different line ranges, no dependencies
- **TDD compliance**: All tests (T004-T013) must be written and fail before implementation
- **Commit strategy**: Commit after each task completion
- **File conflicts**: Avoided by using line ranges for same-file parallel tasks
- **Constitutional compliance**: Follows Kubernetes-first, options trading, TDD, risk management, observability principles

## Success Criteria
- ✅ 54 total tasks covering complete live trading system implementation
- ✅ TDD approach with tests first (10 test tasks before 36 implementation tasks)
- ✅ Parallel execution opportunities identified for efficiency
- ✅ Clear dependency chain from setup through polish
- ✅ All design artifacts translated to actionable tasks
- ✅ Constitutional requirements met throughout task sequence

This task list provides a complete roadmap for implementing the live trading system with Public.com API integration, following TDD principles and maintaining constitutional compliance throughout the development process.
