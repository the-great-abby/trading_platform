# Data Model: Comprehensive Paper Trading System Testing

**Target Entities**: Paper trading system components requiring test validation

## Core Testing Entities

### PaperTradingEngine
**Purpose**: Core trading engine with sophisticated features requiring validation  
**State**: Active/Stopped  
**Key Fields**:
- `portfolio_value`: float (validated: positive, realistic bounds)
- `allocated_capital`: float (validated: <= portfolio_value)
- `available_capital`: computed field (portfolio_value - allocated_capital - min_cash_reserve)
- `daily_trades`: int (validated: >= 0, <= max_daily_trades)
- `weekly_trades`: int (validated: >= 0, <= max_weekly_trades)  
- `monthly_trades`: int (validated: >= 0, <= max_monthly_trades)
- `strategy_instances`: Dict[str, Strategy] (validated: strategy classes exist)
- `is_running`: bool

**State Transitions**:
- Initialize → Configured
- Configured → Running  
- Running → Stopped (graceful shutdown)

**Validation Rules**:
- Capital allocation ratios must sum to <= 1.0
- Trade limits respected during execution
- Strategy integration validated on startup

### CapitalAllocation
**Purpose**: Portfolio distribution rules requiring validation  
**Fields**:
- `max_position_size`: float (validated: 0.0-0.15, default 0.05)
- `max_portfolio_utilization`: float (validated: 0.0-1.0, default 0.80)
- `min_cash_reserve`: float (validated: 0.0-0.50, default 0.20)
- `hybrid_allocation`: HybirdAllocationConfig (conditional)

**Validation Rules**:
- Parameters must sum to logical portfolio constraints
- Hybrid allocation percentages must equal 100%

### HybridAllocationConfig  
**Purpose**: Advanced capital allocation requiring specific testing  
**Fields**:
- `enabled`: bool (conditional field)
- `cash_reserve_pct`: float (validated: 0.20 when enabled)
- `stock_allocation_pct`: float (validated: 0.20 when enabled)  
- `options_allocation_pct`: float (validated: 0.60 when enabled)

**Validation Rules**:
- When enabled: all three percentages must equal ~1.0
- Capital amounts calculated from portfolio_value

### TradeLimits
**Purpose**: Trading restrictions requiring behavior validation  
**Fields**:
- `max_daily_trades`: int (validated: 4-8 range)
- `max_weekly_trades`: int (validated: 6-12 range)  

**Validation Rules**:
- Counter resets must occur at correct intervals
- Enforcement prevents trades when limits exceeded
- Reset logic handles timezone transitions

### StrategyInstances
**Purpose**: Real strategy integration requiring validation  
**Fields**:
- `AdaptiveSectorWaveStrategy`: Strategy instance
- `HybridIchimokuStrategy`: Strategy instance  
- `ElliottWaveImpulseStrategy`: Strategy instance
- `ElliottWaveCorrectiveStrategy`: Strategy instance

**State Transitions**:
- Uninitialized → Loading → Active
- Active → Failed (service unavailable) → Fallback

**Validation Rules**:
- Strategy classes must be importable
- Service dependencies validated on startup
- Graceful fallback when external services unavailable

### PublicComOptimization
**Purpose**: Cost optimization tracking requiring validation  
**Fields**:
- `total_contracts`: int (validated: >= 0)
- `monthly_contracts`: int (validated: >= 0)
- `total_rebates`: float (validated: >= 0)
- `rebate_tier`: str (validated: Bronze/Silver/Gold/Tier 4)
- `quality_trades`: int (validated: >= 0)
- `total_trades`: int (validated: >= 0)

**Validation Rules**:
- Rebate calculation: contracts * 0.06
- Tier thresholds: 100 (Silver), 500 (Gold), 1000 (Tier 4)
- Quality rate: quality_trades / total_trades

### ExitStrategyMonitoring
**Purpose**: Exit strategy display requiring validation  
**Fields**:
- `max_holding_days`: int (validated: 30 default)
- `profit_target_pct`: float (validated: 0.10 default)
- `stop_loss_pct`: float (validated: 0.05 default)  
- `early_profit_target_pct`: float (validated: 0.08 default)

**Validation Rules**:
- Default values displayed when position data missing
- Formatting consistent across monitoring displays
- Real-time updates when position exit strategy changes

## Test Data Entities

### MockTrade
**Purpose**: Test trade data for validation  
**Fields**:
- `trade_id`: str (unique identifier)
- `timestamp`: datetime (realistic timing)
- `symbol`: str (AAPL, MSFT, GOOGL, TSLA, NVDA)
- `action`: str (BUY, SELL)
- `quantity`: int (validated: > 0)
- `price`: float (validated: realistic prices)
- `strategy`: str (matches strategy instances)
- `pnl`: float (calculated)

### MockMarketData
**Purpose**: Market data for strategy testing  
**Fields**:
- `Close`: float (realistic prices)
- `Open`: float (calculated from Close)
- `High`: float (>= Close)
- `Low`: float (<= Close)  
- `Volume`: int (realistic volume)
- `timestamp`: datetime

**Validation Rules**:
- Price movements within reasonable bounds
- Volume patterns consistent with market hours
- Data compatibility with strategy requirements

### TestConfiguration  
**Purpose**: Test-specific configuration handling  
**Fields**:
- `initial_capital`: float (test values)
- `trading_interval`: int (reduced for testing)
- `max_daily_trades`: int (adjusted for testing)
- `symbols`: List[str] (test symbol subset)
- `strategies`: List[str] (test strategy subset)

**Validation Rules**:
- Environment overrides applied correctly
- Configuration precedence validated
- Invalid config rejected with clear errors

## Relationships

```
PaperTradingEngine (1) --> (1) CapitalAllocation
PaperTradingEngine (1) --> (1) TradeLimits  
PaperTradingEngine (1) --> (*) StrategyInstances
PaperTradingEngine (1) --> (1) PublicComOptimization
PaperTradingEngine (1) --> (1) ExitStrategyMonitoring
StrategyInstances (1) --> (*) MockTrade[generates]
PaperTradingEngine (1) --> (*) MockTrade[executes]
PaperTradingEngine (1) --> (*) MockMarketData[requires]
PaperTradingEngine (1) --> (1) TestConfiguration[configures]
```













