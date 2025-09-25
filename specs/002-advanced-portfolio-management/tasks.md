# Tasks: Advanced Portfolio Management System

**Input**: Design documents from `/specs/002-advanced-portfolio-management/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Trading System**: `services/`, `src/`, `k8s/`, `tests/` at repository root
- **Services**: `services/{service-name}/` for microservices
- **Portfolio**: `src/portfolio/` for portfolio management implementations
- **Deployments**: `k8s/` for Kubernetes manifests
- **Testing**: `tests/` with portfolio-specific test directories
- Paths follow trading system architecture per plan.md structure

## Phase 3.1: Setup
- [x] T001 Create portfolio service directory structure in services/portfolio-service/
- [x] T002 Initialize Python project with portfolio optimization dependencies (cvxpy, PyPortfolioOpt, QuantLib)
- [x] T003 [P] Configure linting and formatting tools for portfolio code
- [x] T004 [P] Create database migration for portfolio tables in alembic/versions/
- [x] T005 [P] Update requirements.txt with portfolio optimization packages

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T006 [P] Contract test portfolio API in tests/contract/test_portfolio_api.py
- [x] T007 [P] Contract test optimization API in tests/contract/test_optimization_api.py
- [x] T008 [P] Contract test rebalancing API in tests/contract/test_rebalancing_api.py
- [x] T009 [P] Contract test risk calculations API in tests/contract/test_risk_api.py
- [x] T010 [P] Integration test portfolio optimization workflow in tests/integration/test_portfolio_optimization.py
- [x] T011 [P] Integration test Black-Litterman model in tests/integration/test_black_litterman.py
- [x] T012 [P] Integration test risk parity optimization in tests/integration/test_risk_parity.py
- [x] T013 [P] Integration test tax-loss harvesting in tests/integration/test_tax_optimization.py
- [x] T014 [P] Portfolio backtesting validation test in tests/portfolio/test_portfolio_backtest.py

## Phase 3.3: Core Data Models (ONLY after tests are failing)
- [x] T015 [P] Portfolio entity model in src/portfolio/models/portfolio.py
- [x] T016 [P] Position entity model in src/portfolio/models/position.py
- [x] T017 [P] Asset entity model in src/portfolio/models/asset.py
- [x] T018 [P] OptimizationResult entity model in src/portfolio/models/optimization_result.py
- [x] T019 [P] MarketView entity model in src/portfolio/models/market_view.py
- [x] T020 [P] RebalancingRecommendation entity model in src/portfolio/models/rebalancing_recommendation.py
- [x] T021 [P] TradeRecommendation entity model in src/portfolio/models/rebalancing_recommendation.py
- [x] T022 [P] RiskMetrics entity model in src/portfolio/models/risk_metrics.py

## Phase 3.4: Core Services Implementation
- [x] T023 [P] PortfolioManager service in src/portfolio/services/portfolio_manager.py
- [x] T024 [P] MPTOptimizer service in src/portfolio/optimization/mpt_optimizer.py
- [x] T025 [P] BlackLittermanOptimizer service in src/portfolio/optimization/black_litterman_optimizer.py
- [x] T026 [P] RiskParityOptimizer service in src/portfolio/optimization/risk_parity_optimizer.py
- [x] T027 [P] RebalancingManager service in src/portfolio/rebalancing/rebalancing_manager.py
- [x] T028 [P] TaxOptimizer service in src/portfolio/tax/tax_optimizer.py
- [x] T029 [P] RiskManager service in src/portfolio/risk/risk_manager.py
- [x] T030 [P] PortfolioBacktester service in src/portfolio/backtesting/portfolio_backtester.py

## Phase 3.5: API Services Implementation
- [x] T031 [P] Portfolio API service in services/portfolio-service/main.py
- [x] T032 [P] Risk management API service in services/risk-management-service/main.py
- [x] T033 [P] Portfolio optimization endpoints in services/portfolio-service/api/optimization.py
- [x] T034 [P] Rebalancing endpoints in services/portfolio-service/api/rebalancing.py
- [x] T035 [P] Tax optimization API in services/portfolio-service/api/tax.py
- [x] T036 [P] Backtesting API endpoints in services/portfolio-service/api/backtesting.py

## Phase 3.6: Database Integration
- [x] T037 [P] Portfolio database repository in src/portfolio/repositories/portfolio_repository.py
- [x] T038 [P] Optimization result repository in src/portfolio/repositories/optimization_repository.py
- [x] T039 [P] Risk metrics repository in src/portfolio/repositories/risk_repository.py
- [x] T040 [P] Database connection configuration in src/portfolio/database/connection.py
- [x] T041 [P] Database migrations for portfolio tables in alembic/versions/
- [x] T042 [P] Database connection pooling in src/portfolio/database/pool.py
- [x] T043 [P] Database health monitoring in src/portfolio/database/health.py
- [x] T044 [P] Database performance optimization in src/portfolio/database/optimization.py

## Phase 3.7: Configuration and Utilities
- [x] T045 [P] Portfolio configuration in src/portfolio/config/portfolio_config.py
- [x] T046 [P] Portfolio validation utilities in src/portfolio/utils/validation.py
- [x] T047 [P] Portfolio calculation utilities in src/portfolio/utils/calculations.py
- [x] T048 [P] Market data integration utilities in src/portfolio/utils/market_data.py

## Phase 3.8: Kubernetes Deployment
- [x] T049 [P] Enhanced Portfolio service deployment in k8s/enhanced-portfolio-service.yaml
- [x] T050 [P] Enhanced Risk management service deployment in k8s/enhanced-risk-management-service.yaml
- [x] T051 [P] Portfolio service configmap in k8s/enhanced-portfolio-service.yaml
- [x] T052 [P] Risk management service configmap in k8s/enhanced-risk-management-service.yaml
- [x] T053 [P] Portfolio service service definition in k8s/enhanced-portfolio-service.yaml
- [x] T054 [P] Risk management service service definition in k8s/enhanced-risk-management-service.yaml

## Phase 3.9: Integration with Existing System
- [x] T055 [P] Market data service integration in src/portfolio/integrations/market_data_service.py
- [x] T056 [P] Unified analytics dashboard integration in services/unified-analytics-dashboard/
- [x] T057 [P] MCP service integration for portfolio insights in services/mcp-service/
- [x] T058 [P] System integration testing in scripts/test-portfolio-system-integration.py

## Phase 3.10: Demo Scripts and Examples
- [x] T059 [P] Portfolio optimization demo script in demo/portfolio-management/portfolio_optimization_demo.py
- [x] T060 [P] Risk parity demo script in demo/portfolio-management/risk_parity_demo.py
- [x] T061 [P] Black-Litterman demo script in demo/portfolio-management/black_litterman_demo.py
- [x] T062 [P] Complete system demo script in demo/portfolio-management/complete_system_demo.py
- [x] T063 [P] Demo runner script in demo/portfolio-management/run_demos.py

## Phase 3.11: Polish and Optimization
- [x] T064 [P] Unit tests for portfolio models in tests/unit/test_portfolio_models.py
- [x] T065 [P] Unit tests for optimization algorithms in tests/unit/test_optimization_algorithms.py
- [x] T066 [P] Unit tests for risk calculations in tests/unit/test_risk_calculations.py
- [x] T067 [P] Integration tests in tests/integration/test_portfolio_system_integration.py
- [x] T068 [P] Performance optimization in src/portfolio/utils/performance_optimizer.py
- [x] T069 [P] Documentation updates in docs/ADVANCED_PORTFOLIO_MANAGEMENT_API.md
- [x] T070 [P] Final system validation and testing
- [x] T071 [P] Deployment and monitoring setup

## Dependencies
- Tests (T006-T014) before implementation (T015-T071)
- Data models (T015-T022) before services (T023-T030)
- Services (T023-T030) before API endpoints (T031-T036)
- Database integration (T037-T044) before full service deployment
- Configuration (T045-T048) before service deployment
- Kubernetes deployment (T049-T054) after all services complete
- Integration (T055-T058) after core services complete
- Demo scripts (T059-T063) after core functionality complete
- Polish tasks (T064-T071) after all implementation complete

## Parallel Execution Examples

### Phase 3.2: Launch All Contract Tests Together
```bash
# These can all run in parallel - different files, no dependencies
Task T006: "Contract test portfolio API in tests/contract/test_portfolio_api.py"
Task T007: "Contract test optimization API in tests/contract/test_optimization_api.py"
Task T008: "Contract test rebalancing API in tests/contract/test_rebalancing_api.py"
Task T009: "Contract test risk calculations API in tests/contract/test_risk_api.py"
```

### Phase 3.3: Launch All Data Models Together
```bash
# These can all run in parallel - different model files
Task T015: "Portfolio entity model in src/portfolio/models/portfolio.py"
Task T016: "Position entity model in src/portfolio/models/position.py"
Task T017: "Asset entity model in src/portfolio/models/asset.py"
Task T018: "OptimizationResult entity model in src/portfolio/models/optimization_result.py"
Task T019: "MarketView entity model in src/portfolio/models/market_view.py"
Task T020: "RebalancingRecommendation entity model in src/portfolio/models/rebalancing_recommendation.py"
Task T021: "TradeRecommendation entity model in src/portfolio/models/trade_recommendation.py"
Task T022: "RiskMetrics entity model in src/portfolio/models/risk_metrics.py"
```

### Phase 3.4: Launch All Core Services Together
```bash
# These can all run in parallel - different service files
Task T023: "PortfolioManager service in src/portfolio/services/portfolio_manager.py"
Task T024: "MPTOptimizer service in src/portfolio/optimization/mpt_optimizer.py"
Task T025: "BlackLittermanOptimizer service in src/portfolio/optimization/black_litterman_optimizer.py"
Task T026: "RiskParityOptimizer service in src/portfolio/optimization/risk_parity_optimizer.py"
Task T027: "RebalancingManager service in src/portfolio/rebalancing/rebalancing_manager.py"
Task T028: "TaxOptimizer service in src/portfolio/tax/tax_optimizer.py"
Task T029: "RiskManager service in src/portfolio/risk/risk_manager.py"
Task T030: "PortfolioBacktester service in src/portfolio/backtesting/portfolio_backtester.py"
```

### Phase 3.8: Launch All Kubernetes Deployments Together
```bash
# These can all run in parallel - different deployment files
Task T046: "Portfolio service deployment in k8s/portfolio-service.yaml"
Task T047: "Risk management service deployment in k8s/risk-management-service.yaml"
Task T048: "Portfolio service configmap in k8s/portfolio-service-configmap.yaml"
Task T049: "Risk management service configmap in k8s/risk-management-service-configmap.yaml"
Task T050: "Portfolio service service definition in k8s/portfolio-service-service.yaml"
Task T051: "Risk management service service definition in k8s/risk-management-service-service.yaml"
```

## Critical Implementation Notes

### Technology Stack Requirements
- **Python 3.11+** with scientific computing libraries
- **cvxpy** for convex optimization (Modern Portfolio Theory)
- **PyPortfolioOpt** for portfolio optimization utilities
- **QuantLib** for quantitative finance calculations
- **PostgreSQL/TimescaleDB** for portfolio data storage
- **Redis** for optimization result caching
- **FastAPI** for REST API services
- **Kubernetes** for containerized deployment

### Performance Requirements
- **Portfolio Optimization**: <60 seconds for 50+ assets
- **Rebalancing Calculations**: <5 seconds
- **Risk Calculations**: <500ms
- **API Response Times**: <200ms for CRUD operations
- **Throughput**: 1000 portfolio operations/minute

### Data Model Validation
- Portfolio weights must sum to 1.0 (excluding cash)
- Position quantities must be positive for long positions
- VaR values must be negative (representing losses)
- Correlation values must be between -1 and 1
- Optimization weights must be within specified constraints

### Integration Points
- **Market Data Service**: 15-minute delayed data integration
- **Existing Backtesting Framework**: Portfolio strategy validation
- **Unified Analytics Dashboard**: Portfolio performance visualization
- **MCP Service**: AI-powered portfolio insights
- **Risk Management System**: Portfolio risk monitoring

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T006-T009)
- [x] All entities have model tasks (T015-T022)
- [x] All tests come before implementation (T006-T014 before T015-T068)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Performance requirements specified (<60s optimization, <5s rebalancing)
- [x] Technology stack dependencies identified (cvxpy, PyPortfolioOpt, QuantLib)
- [x] Database schema migration tasks included (T004, T037-T041)
- [x] Kubernetes deployment tasks included (T046-T051)
- [x] Integration with existing system tasks included (T052-T055)

---

**Total Tasks**: 68
**Parallel Execution Opportunities**: 45 tasks can run in parallel
**Estimated Implementation Time**: 4-6 weeks with parallel execution
**Critical Path**: Tests → Models → Services → APIs → Deployment → Integration → Polish
