# Tasks: Elliott Wave Analysis Service

**Input**: Design documents from `/specs/009-elliott-wave-analysis/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Found: Elliott Wave Analysis Service implementation plan
   → Extract: Python 3.11+, FastAPI, Kubernetes, options integration
2. Load optional design documents:
   → ✅ data-model.md: Extract entities → model tasks
   → ✅ contracts/: Each file → contract test task
   → ✅ research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, API endpoints
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

## Phase 3.1: Setup
- [x] T001 Create Elliott Wave service structure in services/elliott-wave-service/
- [x] T002 Initialize Python project with FastAPI dependencies in services/elliott-wave-service/requirements.txt
- [x] T003 [P] Configure Dockerfile for Elliott Wave service in services/elliott-wave-service/Dockerfile
- [x] T004 [P] Configure Kubernetes deployment in k8s/elliott-wave-service.yaml
- [x] T005 [P] Update PORT_MAP.md with Elliott Wave service port mapping

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T006 [P] Contract test Elliott Wave API in tests/contract/test_elliott_wave_contracts.py
- [x] T007 [P] Integration test pattern detection in tests/integration/test_pattern_detection.py
- [x] T008 [P] Integration test options signal generation in tests/integration/test_options_integration.py
- [x] T009 [P] Backtest validation test in tests/backtesting/test_elliott_wave_backtest.py
- [x] T010 [P] Performance test analysis timing in tests/performance/test_analysis_timing.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T011 [P] ElliottWavePattern model in services/elliott-wave-service/models.py
- [x] T012 [P] WavePoint model in services/elliott-wave-service/models.py
- [x] T013 [P] FibonacciLevel model in services/elliott-wave-service/models.py
- [x] T014 [P] TradingSignal model in services/elliott-wave-service/models.py
- [x] T015 [P] Advanced pattern detection in services/elliott-wave-service/advanced_pattern_detection.py
- [x] T016 [P] Options integration in services/elliott-wave-service/options_integration.py
- [x] T017 [P] Main Elliott Wave analyzer in services/elliott-wave-service/main.py
- [x] T018 [P] Configuration updates in src/utils/trading_config.py

## Phase 3.4: Integration
- [x] T019 Connect Elliott Wave service to market data service
- [x] T020 [P] Health check middleware in services/elliott-wave-service/main.py
- [x] T021 [P] Request/response logging in services/elliott-wave-service/main.py
- [x] T022 [P] CORS and security headers in services/elliott-wave-service/main.py
- [x] T023 [P] Error handling middleware in services/elliott-wave-service/main.py

## Phase 3.5: Polish
- [x] T024 [P] Unit tests for pattern detection in tests/unit/test_pattern_detection.py
- [x] T025 [P] Unit tests for Fibonacci calculations in tests/unit/test_fibonacci_calculations.py
- [x] T026 [P] Unit tests for options integration in tests/unit/test_options_integration.py
- [x] T027 Performance tests (<30 seconds analysis target)
- [x] T028 [P] Update docs/api.md with Elliott Wave endpoints
- [x] T029 [P] Update quickstart.md with deployment instructions
- [x] T030 [P] Run manual testing validation
- [x] T031 [P] Remove code duplication and optimize

## Dependencies
- Tests (T006-T010) before implementation (T011-T018)
- T011-T014 blocks T015-T017 (models before services)
- T015-T017 blocks T019 (core before integration)
- Implementation before polish (T024-T031)

## Parallel Example
```
# Launch T006-T010 together:
Task: "Contract test GET /elliott-wave/analyze/{symbol} in tests/contract/test_elliott_wave_contracts.py"
Task: "Integration test pattern detection in tests/integration/test_pattern_detection.py"
Task: "Integration test options signal generation in tests/integration/test_options_integration.py"
Task: "Backtest validation test in tests/backtesting/test_elliott_wave_backtest.py"
Task: "Performance test analysis timing in tests/performance/test_analysis_timing.py"
```

## Task Details

### T001: Create Elliott Wave service structure
**File**: `services/elliott-wave-service/`
**Description**: Create directory structure for Elliott Wave analysis service
**Dependencies**: None
**Validation**: Directory exists with proper structure

### T002: Initialize Python project with FastAPI dependencies
**File**: `services/elliott-wave-service/requirements.txt`
**Description**: Define Python dependencies for Elliott Wave service
**Dependencies**: T001
**Validation**: Requirements file contains FastAPI, pandas, numpy, aiohttp

### T003: Configure Dockerfile
**File**: `services/elliott-wave-service/Dockerfile`
**Description**: Create container configuration for Elliott Wave service
**Dependencies**: T002
**Validation**: Dockerfile builds successfully

### T004: Configure Kubernetes deployment
**File**: `k8s/elliott-wave-service.yaml`
**Description**: Create Kubernetes deployment and service manifests
**Dependencies**: T003
**Validation**: Kubernetes manifests are valid

### T005: Update PORT_MAP.md
**File**: `PORT_MAP.md`
**Description**: Add Elliott Wave service to port mapping documentation
**Dependencies**: T004
**Validation**: Port mapping updated with service details

### T006: Contract test Elliott Wave API
**File**: `tests/contract/test_elliott_wave_contracts.py`
**Description**: Test API contracts and schemas (must fail initially)
**Dependencies**: T005
**Validation**: Tests fail with proper error messages

### T007: Integration test pattern detection
**File**: `tests/integration/test_pattern_detection.py`
**Description**: Test Elliott Wave pattern detection algorithms
**Dependencies**: T006
**Validation**: Tests fail with pattern detection errors

### T008: Integration test options signal generation
**File**: `tests/integration/test_options_integration.py`
**Description**: Test options trading signal generation
**Dependencies**: T007
**Validation**: Tests fail with signal generation errors

### T009: Backtest validation test
**File**: `tests/backtesting/test_elliott_wave_backtest.py`
**Description**: Test Elliott Wave analysis with historical data
**Dependencies**: T008
**Validation**: Tests fail with backtest errors

### T010: Performance test analysis timing
**File**: `tests/performance/test_analysis_timing.py`
**Description**: Test analysis performance (<30 seconds target)
**Dependencies**: T009
**Validation**: Tests fail with timing errors

### T011-T014: Model Implementation
**Files**: `services/elliott-wave-service/models.py`
**Description**: Implement ElliottWavePattern, WavePoint, FibonacciLevel, TradingSignal models
**Dependencies**: T010
**Validation**: Models pass validation tests

### T015: Advanced pattern detection
**File**: `services/elliott-wave-service/advanced_pattern_detection.py`
**Description**: Implement advanced Elliott Wave pattern detection algorithms
**Dependencies**: T011-T014
**Validation**: Pattern detection works correctly

### T016: Options integration
**File**: `services/elliott-wave-service/options_integration.py`
**Description**: Implement options trading signal generation
**Dependencies**: T015
**Validation**: Options signals generated correctly

### T017: Main Elliott Wave analyzer
**File**: `services/elliott-wave-service/main.py`
**Description**: Implement main FastAPI service with all endpoints
**Dependencies**: T016
**Validation**: All API endpoints work correctly

### T018: Configuration updates
**File**: `src/utils/trading_config.py`
**Description**: Add Elliott Wave service configuration
**Dependencies**: T017
**Validation**: Configuration loaded correctly

### T019: Market data service integration
**Description**: Connect Elliott Wave service to existing market data service
**Dependencies**: T018
**Validation**: Market data retrieved successfully

### T020-T023: Middleware and Integration
**Files**: `services/elliott-wave-service/main.py`
**Description**: Add health checks, logging, CORS, error handling
**Dependencies**: T019
**Validation**: Middleware functions correctly

### T024-T026: Unit Tests
**Files**: `tests/unit/test_*.py`
**Description**: Unit tests for pattern detection, Fibonacci calculations, options integration
**Dependencies**: T020-T023
**Validation**: All unit tests pass

### T027: Performance Tests
**Description**: Validate <30 seconds analysis target
**Dependencies**: T024-T026
**Validation**: Performance targets met

### T028-T031: Documentation and Polish
**Files**: `docs/api.md`, `quickstart.md`
**Description**: Update documentation, manual testing, code optimization
**Dependencies**: T027
**Validation**: Documentation complete, manual tests pass

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T006)
- [x] All entities have model tasks (T011-T014)
- [x] All tests come before implementation (T006-T010 before T011-T018)
- [x] Parallel tasks truly independent (marked with [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Follow TDD approach: Red → Green → Refactor
- Maintain constitutional compliance throughout implementation
