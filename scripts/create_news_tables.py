#!/usr/bin/env python3
"""
Create news tables directly in the database
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

def create_news_tables():
    """Create the news tables in the database"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print(f"🔗 Connecting to database...")
    engine = create_engine(
        database_url,
        echo=False,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30
    )
    
    try:
        # Create tables directly
        with engine.connect() as conn:
            print("📊 Creating historical_news table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS historical_news (
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
                    ticker VARCHAR(10)
                )
            '''))
            
            print("📊 Creating news_cache table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS news_cache (
                    symbol VARCHAR(10) NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    earliest_date TIMESTAMP,
                    latest_date TIMESTAMP,
                    total_articles INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, source)
                )
            '''))
            
            print("🔍 Creating indexes...")
            # Create indexes
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_news_published_at ON historical_news (published_at)',
                'CREATE INDEX IF NOT EXISTS idx_news_source ON historical_news (source)',
                'CREATE INDEX IF NOT EXISTS idx_news_ticker ON historical_news (ticker)',
                'CREATE INDEX IF NOT EXISTS idx_news_event_type ON historical_news (event_type)',
                'CREATE INDEX IF NOT EXISTS idx_news_sentiment ON historical_news (sentiment_score)',
                'CREATE INDEX IF NOT EXISTS idx_news_impact ON historical_news (impact_score)',
                'CREATE INDEX IF NOT EXISTS idx_cache_symbol ON news_cache (symbol)',
                'CREATE INDEX IF NOT EXISTS idx_cache_source ON news_cache (source)'
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    print(f"⚠️  Index creation warning: {e}")
            
            conn.commit()
            print("✅ News tables created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = create_news_tables()
    if success:
        print("🎉 Database setup completed!")
    else:
        print("💥 Database setup failed!")
        exit(1) 