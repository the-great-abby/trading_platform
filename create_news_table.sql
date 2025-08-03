-- Create historical_news table
CREATE TABLE IF NOT EXISTS historical_news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    url TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP,
    sentiment_score FLOAT,
    impact_score FLOAT,
    confidence_score FLOAT,
    event_type VARCHAR(50),
    affected_symbols JSONB,
    news_metadata JSONB,
    provider_id VARCHAR(100),
    ticker VARCHAR(10)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_news_event_type ON historical_news (event_type);
CREATE INDEX IF NOT EXISTS idx_news_impact ON historical_news (impact_score);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON historical_news (published_at);
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON historical_news (sentiment_score);
CREATE INDEX IF NOT EXISTS idx_news_source ON historical_news (source);
CREATE INDEX IF NOT EXISTS idx_news_ticker ON historical_news (ticker);

-- Update alembic version
INSERT INTO alembic_version (version_num) VALUES ('20250706015740') ON CONFLICT DO NOTHING; 