-- CQRS Read Model Database Schema
-- Optimized tables for efficient querying

-- Portfolio Read Model
CREATE TABLE IF NOT EXISTS portfolio_read_model (
    portfolio_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_value DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    unrealized_pnl DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    realized_pnl DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_return DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_return_percentage DECIMAL(8,4) NOT NULL DEFAULT 0.0000,
    position_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Position Read Model
CREATE TABLE IF NOT EXISTS position_read_model (
    position_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL REFERENCES portfolio_read_model(portfolio_id),
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    market_value DECIMAL(15,2) NOT NULL,
    cost_basis DECIMAL(15,2) NOT NULL,
    unrealized_pnl DECIMAL(15,2) NOT NULL,
    realized_pnl DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Market Data Read Model
CREATE TABLE IF NOT EXISTS market_data_read_model (
    symbol VARCHAR(20) PRIMARY KEY,
    current_price DECIMAL(10,4) NOT NULL,
    price_change DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    price_change_pct DECIMAL(8,4) NOT NULL DEFAULT 0.0000,
    volume BIGINT NOT NULL DEFAULT 0,
    high_52w DECIMAL(10,4),
    low_52w DECIMAL(10,4),
    market_cap BIGINT,
    pe_ratio DECIMAL(8,4),
    dividend_yield DECIMAL(8,4),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Performance Read Model
CREATE TABLE IF NOT EXISTS performance_read_model (
    performance_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL REFERENCES portfolio_read_model(portfolio_id),
    strategy_id VARCHAR(50),
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_return DECIMAL(15,2) NOT NULL,
    total_return_pct DECIMAL(8,4) NOT NULL,
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    win_rate DECIMAL(8,4),
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    average_win DECIMAL(15,2),
    average_loss DECIMAL(15,2),
    profit_factor DECIMAL(8,4),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Order Read Model
CREATE TABLE IF NOT EXISTS order_read_model (
    order_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL REFERENCES portfolio_read_model(portfolio_id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- buy, sell
    quantity INTEGER NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- market, limit, stop, stop_limit
    price DECIMAL(10,4),
    stop_price DECIMAL(10,4),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    filled_quantity INTEGER NOT NULL DEFAULT 0,
    average_fill_price DECIMAL(10,4),
    time_in_force VARCHAR(10) NOT NULL DEFAULT 'GTC',
    strategy_id VARCHAR(50),
    signal_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    metadata JSONB
);

-- Strategy Read Model
CREATE TABLE IF NOT EXISTS strategy_read_model (
    strategy_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    parameters JSONB NOT NULL,
    performance_metrics JSONB,
    last_signal_at TIMESTAMP,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Analytics Read Model (for aggregated analytics)
CREATE TABLE IF NOT EXISTS analytics_read_model (
    analytics_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolio_read_model(portfolio_id),
    strategy_id VARCHAR(50) REFERENCES strategy_read_model(strategy_id),
    user_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- performance, risk, correlation, etc.
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_portfolio_user_account ON portfolio_read_model(user_id, account_id);
CREATE INDEX IF NOT EXISTS idx_position_portfolio ON position_read_model(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_position_symbol ON position_read_model(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_updated ON market_data_read_model(last_updated);
CREATE INDEX IF NOT EXISTS idx_performance_portfolio ON performance_read_model(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_performance_strategy ON performance_read_model(strategy_id);
CREATE INDEX IF NOT EXISTS idx_performance_period ON performance_read_model(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_order_portfolio ON order_read_model(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_order_symbol ON order_read_model(symbol);
CREATE INDEX IF NOT EXISTS idx_order_status ON order_read_model(status);
CREATE INDEX IF NOT EXISTS idx_order_created ON order_read_model(created_at);
CREATE INDEX IF NOT EXISTS idx_strategy_user ON strategy_read_model(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_type ON strategy_read_model(strategy_type);
CREATE INDEX IF NOT EXISTS idx_analytics_portfolio ON analytics_read_model(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_analytics_strategy ON analytics_read_model(strategy_id);
CREATE INDEX IF NOT EXISTS idx_analytics_metric ON analytics_read_model(metric_type, metric_name);
