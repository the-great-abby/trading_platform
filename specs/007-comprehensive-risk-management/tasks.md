# Tasks: Comprehensive Risk Management Framework

**Input**: Design documents from `/specs/007-comprehensive-risk-management/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

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
- **Risk Management**: `src/risk/` for risk management components
- **Deployments**: `k8s/` for Kubernetes manifests
- **Testing**: `tests/` with risk-specific test directories

## Phase 3.1: Setup
- [ ] T001 Create project structure for risk management service
- [ ] T002 Initialize Python project with risk management dependencies
- [ ] T003 [P] Configure linting and formatting tools for risk management code

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (from contracts/)
- [ ] T004 [P] Contract test VaR calculation API in tests/contract/test_var_calculation_api.py
- [ ] T005 [P] Contract test stress testing API in tests/contract/test_stress_testing_api.py
- [ ] T006 [P] Contract test correlation analysis API in tests/contract/test_correlation_analysis_api.py
- [ ] T007 [P] Contract test compliance reporting API in tests/contract/test_compliance_reporting_api.py
- [ ] T008 [P] Contract test risk monitoring API in tests/contract/test_risk_monitoring_api.py
- [ ] T009 [P] Contract test risk limits configuration API in tests/contract/test_risk_limits_api.py
- [ ] T010 [P] Contract test risk alerts API in tests/contract/test_risk_alerts_api.py

### Integration Tests (from quickstart scenarios)
- [ ] T011 [P] Integration test VaR calculation workflow in tests/integration/test_var_calculation_workflow.py
- [ ] T012 [P] Integration test stress testing workflow in tests/integration/test_stress_testing_workflow.py
- [ ] T013 [P] Integration test correlation analysis workflow in tests/integration/test_correlation_analysis_workflow.py
- [ ] T014 [P] Integration test compliance reporting workflow in tests/integration/test_compliance_reporting_workflow.py
- [ ] T015 [P] Integration test risk monitoring workflow in tests/integration/test_risk_monitoring_workflow.py
- [ ] T016 [P] Integration test end-to-end risk assessment workflow in tests/integration/test_end_to_end_risk_assessment.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (from data-model.md entities)
- [ ] T017 [P] RiskMetrics model in src/risk/models/risk_metrics.py
- [ ] T018 [P] StressTestResult model in src/risk/models/stress_test_result.py
- [ ] T019 [P] CorrelationAnalysis model in src/risk/models/correlation_analysis.py
- [ ] T020 [P] ComplianceReport model in src/risk/models/compliance_report.py
- [ ] T021 [P] RiskLimits model in src/risk/models/risk_limits.py
- [ ] T022 [P] RiskAlert model in src/risk/models/risk_alert.py
- [ ] T023 [P] RiskContributions model in src/risk/models/risk_contributions.py

### Core Services (from research.md decisions)
- [ ] T024 [P] VaR Calculator service in src/risk/services/var_calculator.py
- [ ] T025 [P] Stress Tester service in src/risk/services/stress_tester.py
- [ ] T026 [P] Correlation Analyzer service in src/risk/services/correlation_analyzer.py
- [ ] T027 [P] Compliance Reporter service in src/risk/services/compliance_reporter.py
- [ ] T028 [P] Risk Monitor service in src/risk/services/risk_monitor.py
- [ ] T029 [P] Risk Limits Manager service in src/risk/services/risk_limits_manager.py
- [ ] T030 [P] Risk Alert Manager service in src/risk/services/risk_alert_manager.py

### API Service Implementation
- [ ] T031 Risk Management Service main application in services/risk-management-service/main.py
- [ ] T032 [P] VaR calculation API endpoints in services/risk-management-service/api/var_calculation.py
- [ ] T033 [P] Stress testing API endpoints in services/risk-management-service/api/stress_testing.py
- [ ] T034 [P] Correlation analysis API endpoints in services/risk-management-service/api/correlation_analysis.py
- [ ] T035 [P] Compliance reporting API endpoints in services/risk-management-service/api/compliance_reporting.py
- [ ] T036 [P] Risk monitoring API endpoints in services/risk-management-service/api/risk_monitoring.py
- [ ] T037 [P] Risk limits configuration API endpoints in services/risk-management-service/api/risk_limits.py
- [ ] T038 [P] Risk alerts API endpoints in services/risk-management-service/api/risk_alerts.py

### Database Integration
- [ ] T039 [P] Database repositories for risk entities in src/risk/repositories/
- [ ] T040 Database migration for risk management tables in alembic/versions/007_comprehensive_risk_management.py
- [ ] T041 [P] Database connection and pooling configuration in src/risk/database/connection.py

### Configuration and Utilities
- [ ] T042 [P] Risk management configuration in src/risk/config/risk_config.py
- [ ] T043 [P] Risk calculation utilities in src/risk/utils/risk_calculations.py
- [ ] T044 [P] Market data integration utilities in src/risk/utils/market_data_integration.py
- [ ] T045 [P] Risk validation utilities in src/risk/utils/risk_validation.py

## Phase 3.4: Integration
- [ ] T046 Connect Risk Management Service to PostgreSQL/TimescaleDB
- [ ] T047 [P] Authentication middleware for risk management endpoints
- [ ] T048 [P] Request/response logging for risk calculations
- [ ] T049 [P] CORS and security headers for risk management API
- [ ] T050 [P] Prometheus metrics integration for risk calculations
- [ ] T051 [P] RabbitMQ event integration for risk monitoring
- [ ] T052 [P] Redis caching integration for risk metrics

## Phase 3.5: Deployment and Infrastructure
- [ ] T053 [P] Kubernetes deployment configuration in k8s/risk-management-service.yaml
- [ ] T054 [P] Kubernetes service configuration in k8s/risk-management-service.yaml
- [ ] T055 [P] Kubernetes ConfigMap for risk management configuration
- [ ] T056 [P] Kubernetes health checks and probes for risk service
- [ ] T057 [P] PORT_MAP.md updates for risk management service (port 11182)
- [ ] T058 [P] Deployment scripts for risk management service

## Phase 3.6: System Integration
- [x] T059 [P] Integration with existing Portfolio Service for position data
- [x] T060 [P] Integration with Market Data Service for historical data
- [x] T061 [P] Integration with Trading Engine for trade validation
- [x] T062 [P] Data synchronization service for cross-service consistency
- [x] T063 [P] Cross-service monitoring and alerting system

## Phase 3.7: Monitoring and Observability
- [x] T064 [P] Structured logging configuration for risk calculations
- [x] T065 [P] Prometheus metrics for risk calculation performance
- [x] T066 [P] Grafana dashboard configuration for risk monitoring
- [x] T067 [P] Health check endpoints for risk management service
- [x] T068 [P] Alert system integration for risk limit breaches

## Phase 3.8: Polish and Optimization
- [x] T069 [P] Unit tests for all risk calculation algorithms in tests/unit/test_risk_calculations.py
- [x] T070 [P] Unit tests for all risk models in tests/unit/test_risk_models.py
- [x] T071 [P] Unit tests for all risk services in tests/unit/test_risk_services.py
- [x] T072 [P] Performance tests for risk calculations (<5s VaR, <30s stress testing)
- [x] T073 [P] Load testing for risk management API endpoints
- [x] T074 [P] Memory usage optimization for risk calculations (<100MB)
- [x] T075 [P] Documentation updates for risk management API
- [x] T076 [P] API documentation generation and publishing
- [x] T077 [P] Quickstart guide validation and testing
- [x] T078 [P] Error handling and edge case testing

## Dependencies
- Tests (T004-T016) before implementation (T017-T078)
- Models (T017-T023) before services (T024-T030)
- Services (T024-T030) before API endpoints (T031-T038)
- Database setup (T039-T041) before API implementation
- Configuration (T042-T045) before service implementation
- Integration (T046-T052) after core implementation
- Deployment (T053-T058) after integration
- System integration (T059-T063) after deployment
- Monitoring (T064-T068) after system integration
- Polish (T069-T078) after all core functionality

## Parallel Execution Examples

### Launch T004-T010 together (Contract Tests):
```
Task: "Contract test VaR calculation API in tests/contract/test_var_calculation_api.py"
Task: "Contract test stress testing API in tests/contract/test_stress_testing_api.py"
Task: "Contract test correlation analysis API in tests/contract/test_correlation_analysis_api.py"
Task: "Contract test compliance reporting API in tests/contract/test_compliance_reporting_api.py"
Task: "Contract test risk monitoring API in tests/contract/test_risk_monitoring_api.py"
Task: "Contract test risk limits configuration API in tests/contract/test_risk_limits_api.py"
Task: "Contract test risk alerts API in tests/contract/test_risk_alerts_api.py"
```

### Launch T017-T023 together (Data Models):
```
Task: "RiskMetrics model in src/risk/models/risk_metrics.py"
Task: "StressTestResult model in src/risk/models/stress_test_result.py"
Task: "CorrelationAnalysis model in src/risk/models/correlation_analysis.py"
Task: "ComplianceReport model in src/risk/models/compliance_report.py"
Task: "RiskLimits model in src/risk/models/risk_limits.py"
Task: "RiskAlert model in src/risk/models/risk_alert.py"
Task: "RiskContributions model in src/risk/models/risk_contributions.py"
```

### Launch T024-T030 together (Core Services):
```
Task: "VaR Calculator service in src/risk/services/var_calculator.py"
Task: "Stress Tester service in src/risk/services/stress_tester.py"
Task: "Correlation Analyzer service in src/risk/services/correlation_analyzer.py"
Task: "Compliance Reporter service in src/risk/services/compliance_reporter.py"
Task: "Risk Monitor service in src/risk/services/risk_monitor.py"
Task: "Risk Limits Manager service in src/risk/services/risk_limits_manager.py"
Task: "Risk Alert Manager service in src/risk/services/risk_alert_manager.py"
```

### Launch T032-T038 together (API Endpoints):
```
Task: "VaR calculation API endpoints in services/risk-management-service/api/var_calculation.py"
Task: "Stress testing API endpoints in services/risk-management-service/api/stress_testing.py"
Task: "Correlation analysis API endpoints in services/risk-management-service/api/correlation_analysis.py"
Task: "Compliance reporting API endpoints in services/risk-management-service/api/compliance_reporting.py"
Task: "Risk monitoring API endpoints in services/risk-management-service/api/risk_monitoring.py"
Task: "Risk limits configuration API endpoints in services/risk-management-service/api/risk_limits.py"
Task: "Risk alerts API endpoints in services/risk-management-service/api/risk_alerts.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Follow TDD approach: Red → Green → Refactor
- All risk calculations must be validated against known benchmarks
- Performance targets: VaR <5s, Stress Testing <30s, Correlation Analysis <10s

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Integration → Deployment → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
