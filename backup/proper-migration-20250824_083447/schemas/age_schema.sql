-- Graph analytics tables for Apache AGE
CREATE TABLE IF NOT EXISTS trading_relationships (
    id SERIAL PRIMARY KEY,
    source_symbol VARCHAR(10) NOT NULL,
    target_symbol VARCHAR(10) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    correlation DECIMAL(5,4),
    strength DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_correlations (
    id SERIAL PRIMARY KEY,
    symbol1 VARCHAR(10) NOT NULL,
    symbol2 VARCHAR(10) NOT NULL,
    correlation_30d DECIMAL(5,4),
    correlation_90d DECIMAL(5,4),
    correlation_1y DECIMAL(5,4),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_networks (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL,
    affected_symbols TEXT[],
    related_news_ids INTEGER[],
    network_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
