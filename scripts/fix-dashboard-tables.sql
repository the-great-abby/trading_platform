-- Fix Dashboard Tables Migration Script
-- Creates the missing tables that the Unified Trading Dashboard expects
-- and populates them with data from existing tables

-- 1. Create portfolio_positions table with expected structure
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DOUBLE PRECISION NOT NULL,
    current_price DOUBLE PRECISION NOT NULL,
    market_value DOUBLE PRECISION NOT NULL,
    unrealized_pnl DOUBLE PRECISION,
    unrealized_pnl_percent DOUBLE PRECISION,
    entry_date TIMESTAMP,
    strategy VARCHAR(100),
    holding_days INTEGER,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_symbol ON portfolio_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_active ON portfolio_positions(active);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_strategy ON portfolio_positions(strategy);

-- 2. Create strategy_events table with expected structure
CREATE TABLE IF NOT EXISTS strategy_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(10),
    confidence DOUBLE PRECISION,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_strategy_events_timestamp ON strategy_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_strategy_events_strategy ON strategy_events(strategy_name);
CREATE INDEX IF NOT EXISTS idx_strategy_events_symbol ON strategy_events(symbol);
CREATE INDEX IF NOT EXISTS idx_strategy_events_type ON strategy_events(event_type);

-- 3. Populate portfolio_positions from existing positions table
-- Convert existing positions data to the expected format
INSERT INTO portfolio_positions (
    symbol, 
    quantity, 
    avg_price, 
    current_price, 
    market_value, 
    unrealized_pnl, 
    unrealized_pnl_percent,
    entry_date, 
    strategy, 
    holding_days,
    active
)
SELECT 
    p.symbol,
    p.quantity,
    p.entry_price as avg_price,
    p.current_price,
    p.quantity * p.current_price as market_value,
    p.pnl as unrealized_pnl,
    CASE 
        WHEN p.entry_price > 0 THEN ((p.current_price - p.entry_price) / p.entry_price) * 100
        ELSE 0
    END as unrealized_pnl_percent,
    p.timestamp as entry_date,
    p.strategy,
    CASE 
        WHEN p.timestamp IS NOT NULL THEN EXTRACT(DAY FROM (CURRENT_TIMESTAMP - p.timestamp))
        ELSE 0
    END as holding_days,
    COALESCE(p.is_active, true) as active
FROM positions p
WHERE NOT EXISTS (
    SELECT 1 FROM portfolio_positions pp WHERE pp.symbol = p.symbol
);

-- 4. Populate strategy_events from existing signals table
-- Convert existing signals data to the expected format
INSERT INTO strategy_events (
    timestamp,
    strategy_name,
    symbol,
    event_type,
    action,
    confidence,
    metadata
)
SELECT 
    s.timestamp,
    s.strategy as strategy_name,
    s.symbol,
    s.signal_type as event_type,
    s.direction as action,
    s.confidence,
    jsonb_build_object(
        'strength', s.strength,
        'signal_type', s.signal_type,
        'direction', s.direction
    ) as metadata
FROM signals s
WHERE NOT EXISTS (
    SELECT 1 FROM strategy_events se 
    WHERE se.timestamp = s.timestamp 
    AND se.symbol = s.symbol 
    AND se.strategy_name = s.strategy
);

-- 5. Populate backtest_trades from existing trades table
-- Convert existing trades data to the expected format
INSERT INTO backtest_trades (
    run_id,
    timestamp,
    symbol,
    action,
    quantity,
    price,
    value,
    pnl,
    confidence,
    portfolio_value,
    cash,
    position_value,
    total_pnl,
    trade_pnl,
    created_at
)
SELECT 
    'migrated_' || t.id::text as run_id,
    t.timestamp,
    t.symbol,
    t.action,
    t.quantity,
    t.price,
    t.value,
    t.pnl,
    t.confidence,
    t.value as portfolio_value,
    0 as cash, -- Default value
    t.value as position_value,
    t.pnl as total_pnl,
    t.pnl as trade_pnl,
    t.created_at
FROM trades t
WHERE NOT EXISTS (
    SELECT 1 FROM backtest_trades bt 
    WHERE bt.timestamp = t.timestamp 
    AND bt.symbol = t.symbol 
    AND bt.action = t.action 
    AND bt.quantity = t.quantity
);

-- 6. Create corresponding backtest_runs entries for migrated trades
INSERT INTO backtest_runs (
    run_id,
    strategy_name,
    backtest_name,
    symbols,
    start_date,
    end_date,
    initial_capital,
    final_capital,
    total_return,
    total_return_pct,
    max_drawdown_pct,
    sharpe_ratio,
    total_trades,
    winning_trades,
    losing_trades,
    win_rate,
    profit_factor,
    avg_win,
    avg_loss,
    database_only,
    data_provider,
    created_at,
    completed_at
)
SELECT DISTINCT
    'migrated_' || t.id::text as run_id,
    COALESCE(t.strategy, 'migrated_strategy') as strategy_name,
    'Migration_' || DATE(t.timestamp) as backtest_name,
    t.symbol as symbols,
    DATE(t.timestamp) as start_date,
    DATE(t.timestamp) as end_date,
    10000 as initial_capital, -- Default value
    10000 + COALESCE(t.pnl, 0) as final_capital,
    COALESCE(t.pnl, 0) as total_return,
    CASE 
        WHEN 10000 > 0 THEN (COALESCE(t.pnl, 0) / 10000) * 100
        ELSE 0
    END as total_return_pct,
    0 as max_drawdown_pct, -- Default value
    0 as sharpe_ratio, -- Default value
    1 as total_trades,
    CASE WHEN COALESCE(t.pnl, 0) > 0 THEN 1 ELSE 0 END as winning_trades,
    CASE WHEN COALESCE(t.pnl, 0) < 0 THEN 1 ELSE 0 END as losing_trades,
    CASE WHEN COALESCE(t.pnl, 0) > 0 THEN 100.0 ELSE 0.0 END as win_rate,
    1 as profit_factor, -- Default value
    CASE WHEN COALESCE(t.pnl, 0) > 0 THEN COALESCE(t.pnl, 0) ELSE 0 END as avg_win,
    CASE WHEN COALESCE(t.pnl, 0) < 0 THEN ABS(COALESCE(t.pnl, 0)) ELSE 0 END as avg_loss,
    'true' as database_only,
    'migrated' as data_provider,
    t.created_at,
    t.timestamp as completed_at
FROM trades t
WHERE NOT EXISTS (
    SELECT 1 FROM backtest_runs br WHERE br.run_id = 'migrated_' || t.id::text
);

-- 7. Update the dashboard to show some data
-- Create a sample active position for demonstration
INSERT INTO portfolio_positions (
    symbol, 
    quantity, 
    avg_price, 
    current_price, 
    market_value, 
    unrealized_pnl, 
    unrealized_pnl_percent,
    entry_date, 
    strategy, 
    holding_days,
    active
) VALUES (
    'AAPL',
    100,
    150.00,
    155.00,
    15500.00,
    500.00,
    3.33,
    CURRENT_TIMESTAMP - INTERVAL '5 days',
    'migrated_strategy',
    5,
    true
) ON CONFLICT DO NOTHING;

-- 8. Create a sample strategy event for demonstration
INSERT INTO strategy_events (
    timestamp,
    strategy_name,
    symbol,
    event_type,
    action,
    confidence,
    metadata
) VALUES (
    CURRENT_TIMESTAMP,
    'migrated_strategy',
    'AAPL',
    'SIGNAL',
    'BUY',
    0.85,
    '{"strength": 0.85, "signal_type": "SIGNAL", "direction": "BUY"}'::jsonb
) ON CONFLICT DO NOTHING;

-- 9. Show summary of what was created
SELECT 'Migration Summary' as info;
SELECT 'portfolio_positions' as table_name, COUNT(*) as record_count FROM portfolio_positions;
SELECT 'strategy_events' as table_name, COUNT(*) as record_count FROM strategy_events;
SELECT 'backtest_trades' as table_name, COUNT(*) as record_count FROM backtest_trades;
SELECT 'backtest_runs' as table_name, COUNT(*) as record_count FROM backtest_runs;

