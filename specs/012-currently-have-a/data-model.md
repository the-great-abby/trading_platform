# Data Model: Backtest Test Validation Framework

## Core Entities

### BacktestScript
Represents a backtest script with metadata about its location, parameters, and expected outputs.

**Fields**:
- `id`: UUID (primary key)
- `name`: string (script name/identifier)
- `file_path`: string (absolute path to script file)
- `function_name`: string (entry point function name)
- `class_name`: string (class name if applicable, nullable)
- `script_type`: enum (INDIVIDUAL_STRATEGY, MULTI_STRATEGY, OPTIONS, COMPREHENSIVE)
- `parameters`: JSON (default parameters for execution)
- `expected_outputs`: JSON (expected result structure)
- `timeout_seconds`: integer (execution timeout)
- `dependencies`: array[string] (required modules/packages)
- `created_at`: timestamp
- `updated_at`: timestamp
- `last_validated_at`: timestamp (nullable)
- `validation_status`: enum (NEVER_RUN, PASSING, FAILING, ERROR)

**Validation Rules**:
- `name` must be unique within the system
- `file_path` must exist and be readable
- `function_name` must exist in the script
- `timeout_seconds` must be positive
- `script_type` must be one of the defined enum values

**State Transitions**:
- NEVER_RUN → PASSING/FAILING (after first validation)
- PASSING → FAILING (when validation fails)
- FAILING → PASSING (when issues are fixed)
- Any state → ERROR (when execution fails)

### BacktestResult
Contains the output data from a backtest execution including performance metrics and trade data.

**Fields**:
- `id`: UUID (primary key)
- `script_id`: UUID (foreign key to BacktestScript)
- `execution_id`: UUID (unique identifier for this execution)
- `start_time`: timestamp
- `end_time`: timestamp
- `duration_seconds`: float
- `status`: enum (SUCCESS, FAILED, TIMEOUT, ERROR)
- `exit_code`: integer
- `stdout`: text
- `stderr`: text
- `performance_metrics`: JSON
  - `total_return_pct`: float
  - `sharpe_ratio`: float
  - `max_drawdown_pct`: float
  - `win_rate`: float
  - `total_trades`: integer
  - `initial_capital`: float
  - `final_capital`: float
- `trade_data`: JSON (array of trade records)
- `validation_errors`: JSON (array of validation error details)
- `resource_usage`: JSON
  - `peak_memory_mb`: float
  - `average_cpu_percent`: float
- `created_at`: timestamp

**Validation Rules**:
- `script_id` must reference existing BacktestScript
- `start_time` must be before `end_time`
- `duration_seconds` must be positive
- `performance_metrics` must contain required fields
- `status` must be one of the defined enum values

**State Transitions**:
- Created → SUCCESS (when execution completes successfully)
- Created → FAILED (when script exits with non-zero code)
- Created → TIMEOUT (when execution exceeds timeout)
- Created → ERROR (when execution fails due to system error)

### ValidationReport
Aggregated results from testing multiple backtest scripts with pass/fail status and detailed analysis.

**Fields**:
- `id`: UUID (primary key)
- `report_name`: string
- `generated_at`: timestamp
- `total_scripts`: integer
- `passed_scripts`: integer
- `failed_scripts`: integer
- `error_scripts`: integer
- `execution_summary`: JSON
  - `total_execution_time_seconds`: float
  - `average_execution_time_seconds`: float
  - `parallel_execution_enabled`: boolean
- `consistency_results`: JSON (consistency analysis across multiple runs)
- `performance_analysis`: JSON (performance trends and insights)
- `recommendations`: JSON (array of improvement recommendations)
- `detailed_results`: JSON (array of individual script results)
- `created_at`: timestamp

**Validation Rules**:
- `total_scripts` must equal sum of passed + failed + error scripts
- `execution_summary` must contain required timing fields
- `detailed_results` must contain results for all tested scripts

### TestConfiguration
Settings that define how backtests should be validated including tolerances and expected behaviors.

**Fields**:
- `id`: UUID (primary key)
- `name`: string (configuration name)
- `description`: text
- `tolerances`: JSON
  - `returns_tolerance_pct`: float (default: 0.1)
  - `ratios_tolerance`: float (default: 0.01)
  - `drawdown_tolerance_pct`: float (default: 0.05)
  - `win_rate_tolerance_pct`: float (default: 0.5)
- `timeouts`: JSON
  - `quick_test_seconds`: integer (default: 30)
  - `standard_test_seconds`: integer (default: 300)
  - `comprehensive_test_seconds`: integer (default: 1800)
  - `options_test_seconds`: integer (default: 600)
- `validation_rules`: JSON
  - `require_exact_trade_counts`: boolean (default: true)
  - `allow_missing_metrics`: array[string] (default: [])
  - `required_metrics`: array[string] (default: all standard metrics)
- `execution_settings`: JSON
  - `parallel_execution`: boolean (default: true)
  - `max_parallel_jobs`: integer (default: 4)
  - `retry_failed_tests`: boolean (default: true)
  - `max_retries`: integer (default: 2)
- `is_default`: boolean (default: false)
- `created_at`: timestamp
- `updated_at`: timestamp

**Validation Rules**:
- `name` must be unique within the system
- All tolerance values must be non-negative
- All timeout values must be positive
- `max_parallel_jobs` must be positive
- Only one configuration can have `is_default = true`

## Relationships

### BacktestScript → BacktestResult
- One-to-many relationship
- A script can have multiple execution results
- Cascade delete: when script is deleted, all its results are deleted

### TestConfiguration → BacktestResult
- One-to-many relationship (via execution context)
- Configuration used for validation is stored with each result

### ValidationReport → BacktestResult
- One-to-many relationship
- Report aggregates multiple execution results
- Results are referenced by execution_id

## Data Integrity Constraints

### Referential Integrity
- All foreign key relationships must be maintained
- Orphaned records are not allowed
- Cascade deletes are implemented where appropriate

### Business Rules
- Script names must be unique
- Only one default configuration is allowed
- Execution results cannot be modified after creation
- Validation reports are immutable once generated

### Performance Constraints
- Large JSON fields are indexed appropriately
- Queries are optimized for common access patterns
- Archival strategy for old execution results

## Data Migration Considerations

### Schema Evolution
- JSON fields allow for schema evolution without breaking changes
- New fields can be added with default values
- Deprecated fields are marked but not removed immediately

### Data Retention
- Execution results older than 90 days are archived
- Validation reports are retained for 1 year
- Script metadata is retained indefinitely

### Backup and Recovery
- Regular backups of all validation data
- Point-in-time recovery capability
- Cross-region replication for disaster recovery

