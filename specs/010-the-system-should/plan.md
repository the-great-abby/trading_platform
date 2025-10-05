# Implementation Plan: Active Trade Recovery and Management

**Branch**: `010-the-system-should` | **Date**: 2025-01-27 | **Spec**: `/specs/010-the-system-should/spec.md`
**Input**: Feature specification from `/specs/010-the-system-should/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Active Trade Recovery and Management system that detects existing trades on trading accounts after database failures and allows users to select appropriate strategies for ongoing management. The system provides intelligent strategy suggestions based on trade characteristics and market conditions.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy, asyncio, Redis, PostgreSQL/TimescaleDB  
**Storage**: PostgreSQL/TimescaleDB for trade data, Redis for caching, structured logging  
**Testing**: pytest, pytest-asyncio, mock data for backtesting  
**Target Platform**: Kubernetes cluster (Linux containers)  
**Project Type**: web (microservices architecture)  
**Performance Goals**: <200ms response time for trade detection, real-time strategy updates  
**Constraints**: Must integrate with existing trading system, maintain audit trail, support multiple trading accounts  
**Scale/Scope**: Handle 100+ concurrent trades, support 20+ trading strategies, multi-account management

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Kubernetes-First Architecture ✅
- **Compliance**: Feature will be implemented as microservice in existing Kubernetes architecture
- **Health Checks**: Service will include health endpoints for trade detection status
- **Metrics**: Structured logging and Prometheus metrics for recovery operations
- **Service Boundaries**: Clear separation between trade detection, strategy selection, and management

### II. Options Trading Focus ✅
- **Compliance**: Feature supports all existing options strategies (Iron Condor, Covered Calls, etc.)
- **Market Data**: Integrates with existing market data service for real-time pricing
- **Greeks**: Leverages existing Greeks calculations for strategy matching

### III. Test-First (NON-NEGOTIABLE) ✅
- **TDD Approach**: Contract tests first, then implementation
- **Backtest Validation**: All strategy assignments validated through backtesting
- **Red-Green-Refactor**: Strict adherence to TDD cycle

### IV. Risk Management Integration ✅
- **Risk Controls**: All recovered trades subject to existing risk management rules
- **Position Sizing**: Maintains existing position sizing constraints
- **P&L Tracking**: Real-time P&L tracking for recovered trades

### V. Observability & Monitoring ✅
- **Structured Logging**: All recovery actions logged with structured format
- **Metrics**: Recovery success rates, strategy assignment performance
- **Alerts**: Notifications for recovery failures or strategy mismatches

## Project Structure

### Documentation (this feature)
```
specs/010-the-system-should/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Trading System Architecture (DEFAULT)
services/
├── strategy-service/           # Trading strategies and backtesting
├── market-data-service/        # Market data APIs and caching
├── unified-trading-dashboard/  # Trading interface
├── unified-analytics-dashboard/# Analytics and reporting
├── trade-recovery-service/    # NEW: Active trade recovery service
└── mcp-service/               # AI integration

src/
├── strategies/                # Trading strategy implementations
│   ├── options/              # Options-specific strategies
│   ├── momentum/             # Momentum strategies
│   └── mean_reversion/       # Mean reversion strategies
├── services/                 # Core trading services
│   └── trade_recovery/       # NEW: Trade recovery service
├── backtesting/              # Backtesting engine
├── utils/                    # Utilities and configuration
│   └── trading_config.py     # Centralized configuration
└── core/                     # Core trading types and interfaces

tests/
├── contract/                 # API contract tests
├── integration/              # Integration tests
├── unit/                     # Unit tests
└── backtesting/              # Strategy backtesting tests

k8s/                         # Kubernetes deployments
├── *.yaml                   # Service deployments
└── configmap.yaml           # Configuration management

scripts/                     # Utility scripts
├── populate_*_data.py       # Data population scripts
└── update_paper_trading_status.py
```

**Structure Decision**: DEFAULT (microservices architecture)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Trade detection API integration patterns
   - Strategy matching algorithms
   - Recovery session management
   - Multi-account support patterns

2. **Generate and dispatch research agents**:
   ```
   Task: "Research trade detection API patterns for broker integration"
   Task: "Find best practices for strategy matching algorithms in trading systems"
   Task: "Research recovery session management patterns for financial systems"
   Task: "Find patterns for multi-account trade management"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - ActiveTrade entity with symbol, quantity, entry_price, current_value, pnl
   - RecoverySession entity with timestamp, account_id, status
   - StrategyAssignment entity with trade_id, strategy_name, assigned_at
   - RecoveryLog entity with action, timestamp, details

2. **Generate API contracts** from functional requirements:
   - GET /api/v1/trades/active - detect active trades
   - POST /api/v1/recovery/sessions - create recovery session
   - GET /api/v1/strategies/available - get available strategies
   - POST /api/v1/recovery/assign-strategy - assign strategy to trade
   - GET /api/v1/recovery/sessions/{id}/status - get recovery status

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Database failure recovery scenario
   - Multi-trade management scenario
   - Strategy assignment scenario

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh cursor` for your AI assistant
   - Add trade recovery service context
   - Update recent changes (keep last 3)

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected - feature aligns with existing architecture and constitutional principles.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*