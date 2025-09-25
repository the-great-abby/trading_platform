# Tasks: Fix Backtest Engine Issues and Improve Options Strategy Testing

**Input**: Design documents from `/specs/001-fix-backtest-engine/`
**Prerequisites**: plan.md (required), research.md, spec.md

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
- Paths shown below assume trading system architecture - adjust based on plan.md structure

## Phase 3.1: Setup
- [x] T001 Create backtest engine test structure in tests/backtesting/
- [x] T002 [P] Initialize mock options data generation module in src/services/mock_options_data.py
- [x] T003 [P] Configure error handling and logging improvements in src/utils/error_handler.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test BacktestResult attribute consistency in tests/contract/test_backtest_result.py
- [x] T005 [P] Contract test options data service fallback in tests/contract/test_options_data_fallback.py
- [x] T006 [P] Integration test mock options data generation in tests/integration/test_mock_options_data.py
- [x] T007 [P] Integration test strategy fallback mechanism in tests/integration/test_strategy_fallback.py
- [x] T008 [P] Backtest validation test for Iron Condor strategy in tests/backtesting/test_iron_condor_backtest.py
- [x] T009 [P] Backtest validation test for Butterfly Spread strategy in tests/backtesting/test_butterfly_spread_backtest.py
- [x] T010 [P] Backtest validation test for Calendar Spread strategy in tests/backtesting/test_calendar_spread_backtest.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T011 [P] Fix BacktestResult attribute standardization in src/backtesting/engine/backtest_engine.py
- [x] T012 [P] Implement MockOptionsDataService in src/services/mock_options_data_service.py
- [x] T013 [P] Create MockOptionContract dataclass in src/core/types.py
- [x] T014 [P] Implement strategy fallback mechanism in src/strategies/base.py
- [x] T015 [P] Update IronCondorStrategy error handling in src/strategies/options/iron_condor_strategy.py
- [x] T016 [P] Update ButterflySpreadStrategy error handling in src/strategies/options/butterfly_spread_strategy.py
- [x] T017 [P] Update CalendarSpreadStrategy error handling in src/strategies/options/calendar_spread_strategy.py
- [x] T018 [P] Create comprehensive backtest script in services/strategy-service/working_options_backtest.py

## Phase 3.4: Integration
- [x] T019 Connect MockOptionsDataService to BacktestEngine
- [x] T020 Implement graceful degradation in options data service initialization
- [x] T021 Add structured logging for backtest execution and error tracking
- [x] T022 Update strategy service configuration for containerized environment
- [x] T023 Test backtest engine with real paper trading configuration

## Phase 3.5: Polish
- [ ] T024 [P] Unit tests for MockOptionsDataService in tests/unit/test_mock_options_data_service.py
- [ ] T025 [P] Unit tests for BacktestResult standardization in tests/unit/test_backtest_result.py
- [ ] T026 Performance optimization for batch backtesting (<30s for 5 symbols × 3 strategies)
- [ ] T027 [P] Update backtest documentation in docs/backtesting-guide.md
- [ ] T028 [P] Update strategy service API documentation
- [ ] T029 Remove temporary test scripts and clean up code
- [ ] T030 Run comprehensive backtest validation with all strategies

## Dependencies
- Tests (T004-T010) before implementation (T011-T018)
- MockOptionsDataService (T012) before integration (T019)
- Strategy updates (T015-T017) before integration (T020-T021)
- Core implementation (T011-T018) before polish (T024-T030)

## Parallel Execution Examples

### Group 1: Test Setup (T004-T010) - Can run in parallel
```bash
# Run all contract and integration tests in parallel
pytest tests/contract/test_backtest_result.py &
pytest tests/contract/test_options_data_fallback.py &
pytest tests/integration/test_mock_options_data.py &
pytest tests/integration/test_strategy_fallback.py &
pytest tests/backtesting/test_iron_condor_backtest.py &
pytest tests/backtesting/test_butterfly_spread_backtest.py &
pytest tests/backtesting/test_calendar_spread_backtest.py &
wait
```

### Group 2: Core Implementation (T011-T018) - Can run in parallel
```bash
# Update core files in parallel
# Edit src/backtesting/engine/backtest_engine.py &
# Edit src/services/mock_options_data_service.py &
# Edit src/core/types.py &
# Edit src/strategies/base.py &
# Edit src/strategies/options/iron_condor_strategy.py &
# Edit src/strategies/options/butterfly_spread_strategy.py &
# Edit src/strategies/options/calendar_spread_strategy.py &
# Edit services/strategy-service/working_options_backtest.py &
```

### Group 3: Polish Tasks (T024-T025, T027-T028) - Can run in parallel
```bash
# Run unit tests and update docs in parallel
pytest tests/unit/test_mock_options_data_service.py &
pytest tests/unit/test_backtest_result.py &
# Update docs/backtesting-guide.md &
# Update strategy service API docs &
```

## Task Validation Checklist
- [x] All contract tests have corresponding implementation tasks
- [x] All entities (BacktestResult, MockOptionContract) have model tasks
- [x] All strategy updates have corresponding tests
- [x] Integration tasks connect all components
- [x] Polish tasks include performance and documentation
- [x] Parallel execution examples provided
- [x] Dependencies clearly defined

## Success Criteria
- All backtest tests pass without errors
- Options strategies execute trades with mock data
- BacktestResult attributes are consistent
- Error handling provides clear messages and fallbacks
- Performance meets <30s requirement for batch testing
- Documentation is updated and accurate

---

**Ready for execution**: All tasks are specific and actionable for LLM implementation
