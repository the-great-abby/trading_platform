#!/usr/bin/env python3
"""
Migrate News Data to External Vector Database
Moves news articles from old TimescaleDB to external vector database
"""

import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_news_data():
    """Migrate news articles to external vector database"""
    
    # Source: Old TimescaleDB
    source_config = {
        "host": "localhost",
        "port": 11140,
        "database": "trading_bot",
        "user": "trading_user",
        "password": "trading_pass"
    }
    
    # Target: Vector Storage External
    target_config = {
        "host": "localhost",
        "port": 11151,
        "database": "trading",
        "user": "postgres",
        "password": "postgres"
    }
    
    try:
        # Connect to source database
        logger.info("🔍 Connecting to source database...")
        source_conn = psycopg2.connect(**source_config)
        
        # Connect to target database
        logger.info("🔍 Connecting to vector storage external...")
        target_conn = psycopg2.connect(**target_config)
        
        # Get data from source
        with source_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM news_articles")
            source_count = cur.fetchone()[0]
            logger.info(f"📊 Source database has {source_count} news articles")
            
            cur.execute("SELECT * FROM news_articles ORDER BY published_at DESC")
            articles = cur.fetchall()
            logger.info(f"📋 Retrieved {len(articles)} articles from source")
        
        # Create table in target if it doesn't exist
        with target_conn.cursor() as cur:
            cur.execute("""
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
                    sentiment_score DOUBLE PRECISION,
                    impact_score DOUBLE PRECISION,
                    confidence_score DOUBLE PRECISION,
                    event_type VARCHAR(50),
                    affected_symbols JSONB,
                    news_metadata JSONB,
                    provider_id VARCHAR(100),
                    ticker VARCHAR(10),
                    vectorized BOOLEAN DEFAULT FALSE,
                    vector_embedding JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vectorized_at TIMESTAMP
                )
            """)
            
            # Clear existing data
            cur.execute("DELETE FROM news_articles")
            logger.info("🧹 Cleared existing data from target table")
            
            # Insert all articles
            for article in articles:
                cur.execute("""
                    INSERT INTO news_articles (
                        title, content, summary, source, url, author, published_at, 
                        fetched_at, sentiment_score, impact_score, confidence_score,
                        event_type, affected_symbols, news_metadata, provider_id,
                        ticker, vectorized, vector_embedding, created_at, updated_at, vectorized_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, article[1:])  # Skip the id column
            
            target_conn.commit()
            logger.info(f"✅ Successfully migrated {len(articles)} news articles to vector storage external")
        
        # Verify migration
        with target_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM news_articles")
            target_count = cur.fetchone()[0]
            logger.info(f"🔍 Vector storage external now has {target_count} news articles")
            
            if source_count == target_count:
                logger.info("🎉 News migration successful! All articles restored.")
            else:
                logger.warning(f"⚠️ News migration incomplete: {source_count} source vs {target_count} target")
        
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        logger.error(f"❌ News migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("🚀 Starting news data migration to vector storage external...")
    migrate_news_data()
    logger.info("✨ News migration complete!")
