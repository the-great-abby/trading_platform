# Tasks: Backtest Test Validation Framework

**Input**: Design documents from `/specs/012-currently-have-a/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/
**Context**: Database is externally controlled in separate Kubernetes namespace (not available via port forward)

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
- **Strategies**: `src/strategies/` for trading strategy implementations
- **Deployments**: `k8s/` for Kubernetes manifests
- **Testing**: `tests/` with strategy-specific test directories
- **Validation Framework**: `src/validation/` for new validation framework components

## Phase 3.1: Setup
- [x] T001 Create validation framework project structure in src/validation/
- [x] T002 Initialize Python validation framework with pytest, asyncio, pandas, numpy dependencies
- [x] T003 [P] Configure linting and formatting tools for validation framework
- [x] T004 Create validation framework requirements file requirements-validation.txt
- [x] T005 [P] Set up pytest plugin structure for backtest validation

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T006 [P] Contract test validation API in tests/contract/test_validation_api.py
- [x] T007 [P] Integration test script discovery in tests/integration/test_script_discovery.py
- [x] T008 [P] Integration test script execution in tests/integration/test_script_execution.py
- [x] T009 [P] Integration test result validation in tests/integration/test_result_validation.py
- [x] T010 [P] Integration test batch validation in tests/integration/test_batch_validation.py
- [x] T011 [P] Integration test report generation in tests/integration/test_report_generation.py
- [x] T012 [P] Backtest validation test in tests/backtesting/test_backtest_validation.py
- [x] T013 [P] Configuration management test in tests/unit/test_config_management.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T014 [P] BacktestScript model in src/validation/models/backtest_script.py
- [x] T015 [P] BacktestResult model in src/validation/models/backtest_result.py
- [x] T016 [P] ValidationReport model in src/validation/models/validation_report.py
- [x] T017 [P] TestConfiguration model in src/validation/models/test_configuration.py
- [x] T018 [P] Script discovery service in src/validation/discovery/script_discovery.py
- [x] T019 [P] Script execution service in src/validation/execution/script_executor.py
- [x] T020 [P] Result validation service in src/validation/validation/result_validator.py
- [x] T021 [P] Batch validation service in src/validation/execution/batch_validator.py
- [x] T022 [P] Report generation service in src/validation/reporting/report_generator.py
- [x] T023 [P] Configuration management service in src/validation/config/config_manager.py
- [x] T024 [P] Pytest plugin implementation in src/validation/plugin/validation_plugin.py
- [x] T025 [P] CLI interface in src/validation/cli/validation_cli.py

## Phase 3.4: Integration
- [x] T026 Connect validation framework to external database (separate Kubernetes namespace)
- [x] T027 [P] Database service adapter for external database connection
- [ ] T028 [P] Kubernetes service configuration for validation framework
- [x] T029 [P] Environment variable management for external database access
- [x] T030 [P] Error handling and retry logic for external database connectivity
- [x] T031 [P] Logging integration with existing trading system logging
- [x] T032 [P] Metrics collection integration with Prometheus
- [x] T033 [P] Health check endpoints for validation framework

## Phase 3.5: API Implementation
- [x] T034 [P] Script discovery API endpoint in src/validation/api/script_endpoints.py
- [x] T035 [P] Script validation API endpoint in src/validation/api/validation_endpoints.py
- [x] T036 [P] Batch validation API endpoint in src/validation/api/batch_endpoints.py
- [x] T037 [P] Report generation API endpoint in src/validation/api/report_endpoints.py
- [x] T038 [P] Configuration management API endpoint in src/validation/api/config_endpoints.py
- [x] T039 [P] Result retrieval API endpoint in src/validation/api/result_endpoints.py
- [x] T040 [P] FastAPI application setup in src/validation/api/main.py (renamed from app.py)
- [x] T041 [P] API middleware and error handling in src/validation/api/main.py (integrated)

## Phase 3.6: Kubernetes Deployment
- [x] T042 [P] Validation service Kubernetes deployment in k8s/validation-service.yaml
- [x] T043 [P] Validation service ConfigMap in k8s/validation-configmap.yaml
- [x] T044 [P] Validation service Service definition in k8s/validation-service-svc.yaml
- [x] T045 [P] Validation service ingress configuration in k8s/validation-ingress.yaml
- [x] T046 [P] Database connection configuration for external namespace
- [x] T047 [P] PORT_MAP.md updates for validation service (port 11080)

## Phase 3.7: Configuration and Integration
- [x] T048 [P] Update centralized configuration in src/utils/trading_config.py
- [x] T049 [P] Integration with existing backtest engine in src/backtesting/engine/backtest_engine.py
- [x] T050 [P] pytest.ini updates for validation plugin configuration
- [x] T051 [P] Makefile updates for validation framework commands
- [x] T052 [P] Documentation updates in docs/validation/

## Phase 3.8: Polish
- [x] T053 [P] Unit tests for all validation components in tests/unit/test_validation_components.py
- [x] T054 [P] Performance tests for validation framework in tests/performance/test_validation_performance.py
- [x] T055 [P] Update quickstart.md with actual implementation examples
- [x] T056 [P] Create validation framework documentation in docs/validation/README.md
- [x] T057 [P] Remove code duplication and optimize validation logic
- [x] T058 [P] Run manual testing scenarios from quickstart.md
- [x] T059 [P] Generate final validation report using the framework itself

## Dependencies
- Tests (T006-T013) before implementation (T014-T025)
- Models (T014-T017) before services (T018-T025)
- Services before API implementation (T034-T041)
- API implementation before Kubernetes deployment (T042-T047)
- Core implementation before integration (T026-T033)
- Integration before polish (T053-T059)

## Parallel Execution Examples

### Phase 3.2: Test Generation (T006-T013)
```bash
# Launch all contract and integration tests in parallel:
Task: "Contract test validation API in tests/contract/test_validation_api.py"
Task: "Integration test script discovery in tests/integration/test_script_discovery.py"
Task: "Integration test script execution in tests/integration/test_script_execution.py"
Task: "Integration test result validation in tests/integration/test_result_validation.py"
Task: "Integration test batch validation in tests/integration/test_batch_validation.py"
Task: "Integration test report generation in tests/integration/test_report_generation.py"
Task: "Backtest validation test in tests/backtesting/test_backtest_validation.py"
Task: "Configuration management test in tests/unit/test_config_management.py"
```

### Phase 3.3: Model Creation (T014-T017)
```bash
# Launch all model creation tasks in parallel:
Task: "BacktestScript model in src/validation/models/backtest_script.py"
Task: "BacktestResult model in src/validation/models/backtest_result.py"
Task: "ValidationReport model in src/validation/models/validation_report.py"
Task: "TestConfiguration model in src/validation/models/test_configuration.py"
```

### Phase 3.3: Service Implementation (T018-T025)
```bash
# Launch all service implementation tasks in parallel:
Task: "Script discovery service in src/validation/discovery/script_discovery.py"
Task: "Script execution service in src/validation/execution/script_executor.py"
Task: "Result validation service in src/validation/validation/result_validator.py"
Task: "Batch validation service in src/validation/execution/batch_validator.py"
Task: "Report generation service in src/validation/reporting/report_generator.py"
Task: "Configuration management service in src/validation/config/config_manager.py"
Task: "Pytest plugin implementation in src/validation/plugin/validation_plugin.py"
Task: "CLI interface in src/validation/cli/validation_cli.py"
```

### Phase 3.4: Integration Tasks (T027-T033)
```bash
# Launch all integration tasks in parallel:
Task: "Database service adapter for external database connection"
Task: "Kubernetes service configuration for validation framework"
Task: "Environment variable management for external database access"
Task: "Error handling and retry logic for external database connectivity"
Task: "Logging integration with existing trading system logging"
Task: "Metrics collection integration with Prometheus"
Task: "Health check endpoints for validation framework"
```

### Phase 3.5: API Implementation (T034-T041)
```bash
# Launch all API endpoint tasks in parallel:
Task: "Script discovery API endpoint in src/validation/api/script_endpoints.py"
Task: "Script validation API endpoint in src/validation/api/validation_endpoints.py"
Task: "Batch validation API endpoint in src/validation/api/batch_endpoints.py"
Task: "Report generation API endpoint in src/validation/api/report_endpoints.py"
Task: "Configuration management API endpoint in src/validation/api/config_endpoints.py"
Task: "Result retrieval API endpoint in src/validation/api/result_endpoints.py"
Task: "FastAPI application setup in src/validation/api/app.py"
Task: "API middleware and error handling in src/validation/api/middleware.py"
```

### Phase 3.6: Kubernetes Deployment (T042-T047)
```bash
# Launch all Kubernetes deployment tasks in parallel:
Task: "Validation service Kubernetes deployment in k8s/validation-service.yaml"
Task: "Validation service ConfigMap in k8s/validation-configmap.yaml"
Task: "Validation service Service definition in k8s/validation-service-svc.yaml"
Task: "Validation service ingress configuration in k8s/validation-ingress.yaml"
Task: "Database connection configuration for external namespace"
Task: "PORT_MAP.md updates for validation service (port 11080)"
```

## Database Integration Notes

### External Database Considerations
- Database is in separate Kubernetes namespace (not accessible via port forward)
- Must use Kubernetes service discovery for database connection
- Connection string format: `postgresql://user:pass@db-service.namespace.svc.cluster.local:5432/validation_db`
- Implement connection pooling and retry logic for network reliability
- Use environment variables for database configuration
- Implement health checks for database connectivity

### Database Schema Migration
- Create Alembic migration for validation framework tables
- Tables: `backtest_scripts`, `backtest_results`, `validation_reports`, `test_configurations`
- Use existing database migration infrastructure
- Test migrations in development environment first

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (test_validation_api.py)
- [x] All entities have model tasks (BacktestScript, BacktestResult, ValidationReport, TestConfiguration)
- [x] All tests come before implementation (TDD approach)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] External database integration properly handled
- [x] Kubernetes deployment tasks included
- [x] Integration with existing trading system considered

## Task Execution Notes
- Each task must be specific enough for LLM execution without additional context
- Database connectivity will be handled via Kubernetes service discovery
- All validation framework components will be containerized and deployed to Kubernetes
- Integration with existing pytest infrastructure is maintained
- External database connection is properly abstracted and configurable
