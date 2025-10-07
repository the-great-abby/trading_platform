# Data Model: Active Trade Recovery and Management

**Feature**: Active Trade Recovery and Management  
**Date**: 2025-01-27  
**Phase**: 1 - Design

## Core Entities

### ActiveTrade
Represents an open position detected on a trading account during recovery.

**Fields**:
- `id`: UUID (primary key)
- `account_id`: String (foreign key to account)
- `symbol`: String (trading symbol, e.g., "AAPL", "TSLA")
- `quantity`: Decimal (number of shares/contracts)
- `side`: Enum (BUY, SELL)
- `entry_price`: Decimal (price at which position was opened)
- `current_price`: Decimal (current market price)
- `current_value`: Decimal (current position value)
- `unrealized_pnl`: Decimal (unrealized profit/loss)
- `entry_date`: DateTime (when position was opened)
- `detected_at`: DateTime (when position was detected by recovery system)
- `position_type`: Enum (STOCK, OPTION, FUTURE, etc.)
- `option_details`: JSON (for options: strike, expiration, option_type)

**Validation Rules**:
- `quantity` must be positive
- `entry_price` and `current_price` must be positive
- `symbol` must be valid trading symbol format
- `entry_date` must be before `detected_at`

**State Transitions**:
- DETECTED → ASSIGNED (when strategy is assigned)
- ASSIGNED → MANAGED (when management begins)
- MANAGED → CLOSED (when position is closed)

### RecoverySession
Represents a system startup event where active trades are detected and recovery actions are taken.

**Fields**:
- `id`: UUID (primary key)
- `account_id`: String (foreign key to account)
- `started_at`: DateTime (when recovery session began)
- `completed_at`: DateTime (when recovery session completed)
- `status`: Enum (IN_PROGRESS, COMPLETED, FAILED, CANCELLED)
- `total_trades_detected`: Integer (number of trades found)
- `trades_processed`: Integer (number of trades processed)
- `trades_assigned`: Integer (number of trades with strategies assigned)
- `error_message`: String (if session failed)
- `recovery_type`: Enum (DATABASE_FAILURE, MANUAL_RECOVERY, SCHEDULED_RECOVERY)

**Validation Rules**:
- `started_at` must be before `completed_at` (if completed)
- `total_trades_detected` must be >= 0
- `trades_processed` must be <= `total_trades_detected`
- `trades_assigned` must be <= `trades_processed`

**State Transitions**:
- CREATED → IN_PROGRESS (when detection begins)
- IN_PROGRESS → COMPLETED (when all trades processed)
- IN_PROGRESS → FAILED (when error occurs)
- IN_PROGRESS → CANCELLED (when user cancels)

### StrategyAssignment
Represents the mapping of a recovered trade to a specific trading strategy for ongoing management.

**Fields**:
- `id`: UUID (primary key)
- `recovery_session_id`: UUID (foreign key to RecoverySession)
- `active_trade_id`: UUID (foreign key to ActiveTrade)
- `strategy_name`: String (name of assigned strategy)
- `assigned_at`: DateTime (when strategy was assigned)
- `assigned_by`: String (user who made assignment)
- `confidence_score`: Decimal (0.0-1.0, system confidence in assignment)
- `assignment_reason`: String (reason for assignment)
- `status`: Enum (PENDING, ACTIVE, PAUSED, CANCELLED)
- `strategy_parameters`: JSON (strategy-specific parameters)

**Validation Rules**:
- `confidence_score` must be between 0.0 and 1.0
- `strategy_name` must be valid strategy name
- `assigned_at` must be after recovery session start

**State Transitions**:
- PENDING → ACTIVE (when management begins)
- ACTIVE → PAUSED (when management is paused)
- PAUSED → ACTIVE (when management resumes)
- ACTIVE → CANCELLED (when assignment is cancelled)

### RecoveryLog
Represents the audit trail of all recovery actions taken by the system.

**Fields**:
- `id`: UUID (primary key)
- `recovery_session_id`: UUID (foreign key to RecoverySession)
- `action`: Enum (TRADE_DETECTED, STRATEGY_ASSIGNED, TRADE_MANAGED, ERROR_OCCURRED)
- `timestamp`: DateTime (when action occurred)
- `details`: JSON (action-specific details)
- `user_id`: String (user who performed action, if applicable)
- `trade_id`: UUID (foreign key to ActiveTrade, if applicable)
- `strategy_name`: String (strategy involved, if applicable)
- `severity`: Enum (INFO, WARNING, ERROR, CRITICAL)

**Validation Rules**:
- `timestamp` must be valid datetime
- `details` must be valid JSON
- `severity` must be valid enum value

## Entity Relationships

### One-to-Many Relationships
- `RecoverySession` → `ActiveTrade` (one session can detect many trades)
- `RecoverySession` → `StrategyAssignment` (one session can have many assignments)
- `RecoverySession` → `RecoveryLog` (one session can have many log entries)
- `ActiveTrade` → `StrategyAssignment` (one trade can have one assignment)
- `ActiveTrade` → `RecoveryLog` (one trade can have many log entries)

### Foreign Key Constraints
- `ActiveTrade.account_id` → Account table
- `RecoverySession.account_id` → Account table
- `StrategyAssignment.recovery_session_id` → RecoverySession.id
- `StrategyAssignment.active_trade_id` → ActiveTrade.id
- `RecoveryLog.recovery_session_id` → RecoverySession.id
- `RecoveryLog.trade_id` → ActiveTrade.id

## Database Schema Considerations

### Indexes
- `ActiveTrade.account_id, detected_at` (for account-specific queries)
- `RecoverySession.account_id, started_at` (for account-specific sessions)
- `StrategyAssignment.recovery_session_id` (for session-specific assignments)
- `RecoveryLog.recovery_session_id, timestamp` (for session audit trail)

### Constraints
- Unique constraint on `ActiveTrade.account_id, symbol, detected_at` (prevent duplicates)
- Check constraint on `ActiveTrade.quantity > 0`
- Check constraint on `StrategyAssignment.confidence_score BETWEEN 0.0 AND 1.0`

### Partitioning
- `RecoveryLog` table partitioned by `timestamp` (monthly partitions)
- `ActiveTrade` table partitioned by `detected_at` (monthly partitions)

## Data Validation Rules

### Business Rules
1. **Trade Detection**: Only detect trades that are currently open (not closed)
2. **Strategy Assignment**: Only assign strategies that are currently available and enabled
3. **Recovery Session**: Only one active recovery session per account at a time
4. **Audit Trail**: All recovery actions must be logged with timestamp and user

### Data Integrity Rules
1. **Referential Integrity**: All foreign keys must reference existing records
2. **Temporal Integrity**: All timestamps must be consistent (start < end, etc.)
3. **Value Integrity**: All numeric values must be within valid ranges
4. **Enum Integrity**: All enum fields must use valid values

## Performance Considerations

### Query Optimization
- Use composite indexes for common query patterns
- Implement query result caching for strategy matching
- Use database views for complex recovery status queries

### Data Retention
- `RecoveryLog`: Retain for 7 years (compliance requirement)
- `ActiveTrade`: Retain for 2 years after position closure
- `RecoverySession`: Retain for 2 years after completion
- `StrategyAssignment`: Retain for 2 years after cancellation

### Backup Strategy
- Daily incremental backups for all tables
- Weekly full backups for audit tables
- Point-in-time recovery capability for compliance


















