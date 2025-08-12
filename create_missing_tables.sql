-- Create missing tables for vectorization service
-- These tables are expected by the background-vectorization-service

-- 1. NEWS_ARTICLES TABLE
-- This is what the vectorization service expects instead of historical_news
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    url TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment_score FLOAT,
    impact_score FLOAT,
    confidence_score FLOAT,
    event_type VARCHAR(50),
    affected_symbols JSONB,
    news_metadata JSONB,
    provider_id VARCHAR(100),
    ticker VARCHAR(10),
    vectorized BOOLEAN DEFAULT FALSE,
    vector_embedding JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for news_articles
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles (published_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles (source);
CREATE INDEX IF NOT EXISTS idx_news_articles_ticker ON news_articles (ticker);
CREATE INDEX IF NOT EXISTS idx_news_articles_event_type ON news_articles (event_type);
CREATE INDEX IF NOT EXISTS idx_news_articles_sentiment ON news_articles (sentiment_score);
CREATE INDEX IF NOT EXISTS idx_news_articles_impact ON news_articles (impact_score);
CREATE INDEX IF NOT EXISTS idx_news_articles_vectorized ON news_articles (vectorized);

-- 2. MARKET_DATA TABLE  
-- This is what the vectorization service expects instead of historical_prices
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10,4) NOT NULL,
    high_price DECIMAL(10,4) NOT NULL,
    low_price DECIMAL(10,4) NOT NULL,
    close_price DECIMAL(10,4) NOT NULL,
    volume INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,
    interval VARCHAR(10) NOT NULL DEFAULT '1d',
    vectorized BOOLEAN DEFAULT FALSE,
    vector_embedding JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, provider, interval)
);

-- Create indexes for market_data
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data (symbol, date);
CREATE INDEX IF NOT EXISTS idx_market_data_provider ON market_data (provider);
CREATE INDEX IF NOT EXISTS idx_market_data_interval ON market_data (interval);
CREATE INDEX IF NOT EXISTS idx_market_data_vectorized ON market_data (vectorized);

-- 3. EARNINGS_REPORTS TABLE
-- This table is completely missing and needed by the vectorization service
CREATE TABLE IF NOT EXISTS earnings_reports (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    quarter VARCHAR(10) NOT NULL,  -- e.g., 'Q1', 'Q2', 'Q3', 'Q4'
    year INTEGER NOT NULL,
    eps DECIMAL(10,4),  -- Earnings per share
    revenue DECIMAL(20,2),  -- Revenue in dollars
    report_date DATE NOT NULL,
    eps_estimate DECIMAL(10,4),  -- Expected EPS
    revenue_estimate DECIMAL(20,2),  -- Expected revenue
    eps_surprise DECIMAL(10,4),  -- EPS surprise (actual - estimate)
    revenue_surprise DECIMAL(20,2),  -- Revenue surprise
    guidance TEXT,  -- Forward-looking guidance
    conference_call_date DATE,
    notes TEXT,
    vectorized BOOLEAN DEFAULT FALSE,
    vector_embedding JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for earnings_reports
CREATE INDEX IF NOT EXISTS idx_earnings_reports_symbol ON earnings_reports (symbol);
CREATE INDEX IF NOT EXISTS idx_earnings_reports_date ON earnings_reports (report_date);
CREATE INDEX IF NOT EXISTS idx_earnings_reports_quarter_year ON earnings_reports (quarter, year);
CREATE INDEX IF NOT EXISTS idx_earnings_reports_vectorized ON earnings_reports (vectorized);

-- Insert some sample data to get started
-- Sample earnings reports for popular symbols
INSERT INTO earnings_reports (symbol, quarter, year, eps, revenue, report_date, eps_estimate, revenue_estimate, eps_surprise, revenue_surprise, guidance, notes) VALUES
('AAPL', 'Q4', 2024, 2.18, 119575000000, '2024-10-28', 2.10, 118000000000, 0.08, 1575000000, 'Strong holiday quarter expected', 'iPhone 15 Pro sales exceeded expectations'),
('MSFT', 'Q4', 2024, 2.94, 62020000000, '2024-10-24', 2.85, 61000000000, 0.09, 1020000000, 'Cloud growth continues', 'Azure revenue up 29% year-over-year'),
('GOOGL', 'Q4', 2024, 1.64, 86310000000, '2024-10-23', 1.59, 85000000000, 0.05, 1310000000, 'AI investments paying off', 'YouTube and cloud services strong'),
('AMZN', 'Q4', 2024, 0.78, 169961000000, '2024-10-26', 0.72, 166000000000, 0.06, 3961000000, 'AWS growth accelerating', 'E-commerce and cloud both performing well'),
('TSLA', 'Q4', 2024, 0.71, 25167000000, '2024-10-23', 0.68, 24500000000, 0.03, 667000000, 'Production capacity expanding', 'Cybertruck production ramping up')
ON CONFLICT DO NOTHING;

-- Sample market data for the same symbols
INSERT INTO market_data (symbol, date, open_price, high_price, low_price, close_price, volume, provider, interval) VALUES
('AAPL', '2024-12-20', 195.50, 197.80, 194.20, 196.90, 45678900, 'yahoo', '1d'),
('MSFT', '2024-12-20', 375.20, 378.90, 373.50, 376.40, 23456700, 'yahoo', '1d'),
('GOOGL', '2024-12-20', 142.30, 144.80, 141.90, 143.70, 34567800, 'yahoo', '1d'),
('AMZN', '2024-12-20', 155.80, 158.40, 154.60, 157.20, 56789000, 'yahoo', '1d'),
('TSLA', '2024-12-20', 248.90, 252.30, 247.10, 250.80, 78901200, 'yahoo', '1d')
ON CONFLICT DO NOTHING;

-- Sample news articles
INSERT INTO news_articles (title, content, summary, source, url, author, published_at, ticker, event_type, affected_symbols) VALUES
('Apple Reports Strong Q4 Earnings', 'Apple Inc. reported better-than-expected fourth-quarter results...', 'Apple beats Q4 estimates with strong iPhone sales', 'reuters', 'https://reuters.com/apple-q4-2024', 'John Smith', '2024-10-28 16:30:00', 'AAPL', 'earnings', '["AAPL"]'),
('Microsoft Cloud Growth Continues', 'Microsoft Corporation reported strong cloud revenue growth...', 'Microsoft Azure revenue up 29% year-over-year', 'bloomberg', 'https://bloomberg.com/microsoft-q4-2024', 'Jane Doe', '2024-10-24 16:30:00', 'MSFT', 'earnings', '["MSFT"]'),
('Google AI Investments Show Results', 'Alphabet Inc. reported strong quarterly results...', 'Google AI investments driving growth', 'cnbc', 'https://cnbc.com/google-q4-2024', 'Bob Johnson', '2024-10-23 16:30:00', 'GOOGL', 'earnings', '["GOOGL"]')
ON CONFLICT DO NOTHING;

-- Update alembic version to reflect these new tables
INSERT INTO alembic_version (version_num) VALUES ('20241220_add_vectorization_tables') 
ON CONFLICT (version_num) DO NOTHING;
