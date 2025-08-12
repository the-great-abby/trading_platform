-- Update sample data with recent dates so vectorization service can process it
-- The vectorizers look for data from the last 30 days

-- Update earnings reports to recent dates
UPDATE earnings_reports 
SET report_date = CURRENT_DATE - INTERVAL '15 days',
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA');

-- Update market data to recent dates
UPDATE market_data 
SET date = CURRENT_DATE - INTERVAL '10 days',
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA');

-- Update news articles to recent dates
UPDATE news_articles 
SET published_at = CURRENT_TIMESTAMP - INTERVAL '5 days',
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (1, 2, 3);

-- Verify the updates
SELECT 'earnings_reports' as table_name, symbol, report_date FROM earnings_reports
UNION ALL
SELECT 'market_data' as table_name, symbol, date::text FROM market_data
UNION ALL
SELECT 'news_articles' as table_name, ticker, published_at::text FROM news_articles;
