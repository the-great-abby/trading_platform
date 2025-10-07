-- Strategy State Management Schema
-- Stores strategy configuration, state, and performance metrics

-- Strategy configurations table
CREATE TABLE IF NOT EXISTS strategy_configurations (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, version)
);

-- Strategy state table
CREATE TABLE IF NOT EXISTS strategy_states (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    state_data JSONB NOT NULL,
    last_signal_time TIMESTAMP WITH TIME ZONE,
    position_count INTEGER DEFAULT 0,
    total_pnl DECIMAL(15,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, symbol)
);

-- Strategy performance metrics table
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15,2) DEFAULT 0.0,
    max_drawdown DECIMAL(8,4) DEFAULT 0.0,
    sharpe_ratio DECIMAL(8,4) DEFAULT 0.0,
    win_rate DECIMAL(8,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_name, symbol, date)
);

-- Strategy signals table
CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- BUY, SELL, HOLD
    confidence DECIMAL(8,4) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_strategy_states_name_symbol ON strategy_states(strategy_name, symbol);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_name_date ON strategy_performance(strategy_name, date);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_timestamp ON strategy_signals(timestamp);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_name_symbol ON strategy_signals(strategy_name, symbol);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_strategy_configurations_updated_at 
    BEFORE UPDATE ON strategy_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategy_states_updated_at 
    BEFORE UPDATE ON strategy_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
