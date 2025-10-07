# Tasks: Kubernetes Secrets Management via Makefile

**Input**: Design documents from `/specs/013-i-d-like/`
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
- **Infrastructure**: `scripts/`, `k8s/`, `tests/` at repository root
- **Shell Scripts**: `scripts/` for automation utilities
- **Kubernetes**: `k8s/secrets/` for secret templates
- **Testing**: `tests/infrastructure/` for infrastructure tests
- Paths follow trading system architecture with infrastructure automation focus

## Phase 3.1: Setup
- [ ] T001 Create infrastructure directory structure per implementation plan
- [ ] T002 Create .env.example template file with secret variable examples
- [ ] T003 [P] Configure shell script linting with shellcheck integration

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test makefile targets API in tests/contract/test_makefile_targets.py
- [ ] T005 [P] Integration test .env file validation in tests/integration/test_env_validation.py
- [ ] T006 [P] Integration test kubectl operations in tests/integration/test_kubectl_operations.py
- [ ] T007 [P] Integration test secret naming conversion in tests/integration/test_naming_conversion.py
- [ ] T008 [P] End-to-end test complete workflow in tests/integration/test_secrets_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T009 [P] Secret configuration mapping in scripts/secret-config.yaml
- [ ] T010 [P] Environment file validation script in scripts/validate-env.sh
- [ ] T011 [P] Secret update script in scripts/update-secrets.sh
- [ ] T012 [P] Secret listing script in scripts/list-secrets.sh
- [ ] T013 [P] Helper utilities script in scripts/secret-helpers.sh
- [ ] T014 [P] Kubernetes secret templates in k8s/secrets/api-keys.yaml
- [ ] T015 [P] Kubernetes secret templates in k8s/secrets/database.yaml
- [ ] T016 [P] Makefile targets for secrets management in Makefile
- [ ] T017 [P] PORT_MAP.md updates for secret management operations

## Phase 3.4: Integration
- [ ] T018 Connect secret scripts to kubectl cluster validation
- [ ] T019 Integrate error handling with next steps guidance
- [ ] T020 Add logging for secret operations (without exposing values)
- [ ] T021 Integrate with existing Makefile patterns and dependencies

## Phase 3.5: Polish
- [ ] T022 [P] Unit tests for validation functions in tests/unit/test_validation.py
- [ ] T023 [P] Unit tests for naming conversion in tests/unit/test_naming_conversion.py
- [ ] T024 [P] Performance tests (<5 seconds for secret updates)
- [ ] T025 [P] Update documentation in docs/secrets-management.md
- [ ] T026 [P] Remove code duplication and optimize scripts
- [ ] T027 Run quickstart.md validation workflow

## Dependencies
- Tests (T004-T008) before implementation (T009-T017)
- T009 blocks T010, T011, T012 (configuration needed for scripts)
- T010, T011, T012 block T016 (scripts needed for Makefile targets)
- T013, T014, T015 block T016 (templates needed for Makefile)
- Implementation before integration (T018-T021)
- Integration before polish (T022-T027)

## Parallel Example
```
# Launch T004-T008 together (all different files):
Task: "Contract test makefile targets API in tests/contract/test_makefile_targets.py"
Task: "Integration test .env file validation in tests/integration/test_env_validation.py"
Task: "Integration test kubectl operations in tests/integration/test_kubectl_operations.py"
Task: "Integration test secret naming conversion in tests/integration/test_naming_conversion.py"
Task: "End-to-end test complete workflow in tests/integration/test_secrets_workflow.py"

# Launch T010-T015 together (all different files):
Task: "Environment file validation script in scripts/validate-env.sh"
Task: "Secret update script in scripts/update-secrets.sh"
Task: "Secret listing script in scripts/list-secrets.sh"
Task: "Helper utilities script in scripts/secret-helpers.sh"
Task: "Kubernetes secret templates in k8s/secrets/api-keys.yaml"
Task: "Kubernetes secret templates in k8s/secrets/database.yaml"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Shell scripts must follow `set -euo pipefail` pattern from research
- All secret operations must never log actual secret values

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - makefile-targets.yaml → contract test task [P] (T004)
   - Each endpoint → implementation task in scripts/
   
2. **From Data Model**:
   - Secret Configuration → configuration mapping task [P] (T009)
   - Environment File → validation script task [P] (T010)
   - Makefile Target → Makefile implementation task (T016)
   
3. **From User Stories**:
   - Each quickstart scenario → integration test [P] (T005-T008)
   - Complete workflow → end-to-end test [P] (T008)
   
4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004 for makefile-targets.yaml)
- [x] All entities have model tasks (T009 for Secret Configuration, T010 for Environment File)
- [x] All tests come before implementation (T004-T008 before T009-T017)
- [x] Parallel tasks truly independent (different files for all [P] tasks)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Shell script security patterns from research.md included
- [x] Makefile target patterns from research.md followed
- [x] Error handling patterns from research.md implemented

## Implementation Details

### Secret Configuration Mapping (T009)
Based on data model entities:
- API Keys: POLYGON_API_KEY → polygon-api-key, ALPHA_VANTAGE_API_KEY → alpha-vantage-api-key
- Database: DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME → db-credentials (combined secret)

### Script Structure (T010-T013)
Following research.md patterns:
```bash
#!/bin/bash
set -euo pipefail

# Validation functions
validate_env_file() { ... }
validate_cluster_connection() { ... }

# Core operations
update_secret() { ... }
list_secrets() { ... }

# Main execution
main() {
    validate_prerequisites
    execute_operation
    provide_next_steps
}
```

### Makefile Targets (T016)
Following existing patterns:
```makefile
.PHONY: secrets-update secrets-validate secrets-list

secrets-update: validate-env
	@echo "Updating Kubernetes secrets from .env file..."
	@scripts/update-secrets.sh
	@echo "✅ Secrets updated successfully!"
	@echo "Next steps: [specific guidance]"
```

### Error Handling (T019)
Following research.md patterns:
```bash
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo "Next steps:"
    echo "  1. Check cluster connectivity: kubectl cluster-info"
    echo "  2. Verify kubeconfig: kubectl config current-context"
    exit 1
fi
```











