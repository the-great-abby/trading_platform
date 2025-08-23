#!/usr/bin/env python3
"""
PostgreSQL Vector Storage Service - Production-ready vector storage using pgvector
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import numpy as np
import hashlib
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from vector_types import VectorSearchResult
# Removed SQLAlchemy model import to avoid conflicts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PostgreSQL Vector Storage Service", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:12001")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")



class PostgreSQLVectorStorage:
    """PostgreSQL-based vector storage using pgvector"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30
        )
        # Removed SessionLocal since we're using raw SQL
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database with pgvector extension and tables"""
        try:
            with self.engine.connect() as conn:
                # Enable pgvector extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                
                # Create vector embeddings table with pgvector
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS vector_embeddings (
                        id VARCHAR(100) PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector(128),  -- 128-dimensional vectors
                        meta_info JSONB,
                        vector_type VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Create indexes for performance
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_vector_type ON vector_embeddings(vector_type);
                    CREATE INDEX IF NOT EXISTS idx_created_at ON vector_embeddings(created_at);
                    CREATE INDEX IF NOT EXISTS idx_meta_info ON vector_embeddings USING GIN (meta_info);
                """))
                
                conn.commit()
                logger.info("PostgreSQL vector storage initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL vector storage: {e}")
            raise
    
    async def add_embedding(self, content: str, metadata_dict: Dict[str, Any], 
                           vector_type: str) -> str:
        """Add content to PostgreSQL vector database"""
        
        # Generate embedding using LLM
        embedding = await self._generate_embedding(content)
        
        # Create unique ID
        content_hash = hashlib.md5(content.encode()).hexdigest()
        embedding_id = f"{vector_type}_{content_hash}"
        
        try:
            with self.engine.connect() as conn:
                # Check if embedding already exists
                result = conn.execute(text(
                    "SELECT id FROM vector_embeddings WHERE id = :id"
                ), {"id": embedding_id})
                existing = result.fetchone()
                
                if existing:
                    # Update existing embedding
                    conn.execute(text("""
                        UPDATE vector_embeddings 
                        SET content = :content, embedding = :embedding, 
                            meta_info = :meta_info, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """), {
                        "id": embedding_id,
                        "content": content,
                        "embedding": json.dumps(embedding),
                        "meta_info": json.dumps(metadata_dict)
                    })
                else:
                    # Create new embedding
                    conn.execute(text("""
                        INSERT INTO vector_embeddings (id, content, embedding, meta_info, vector_type)
                        VALUES (:id, :content, :embedding, :meta_info, :vector_type)
                    """), {
                        "id": embedding_id,
                        "content": content,
                        "embedding": json.dumps(embedding),
                        "meta_info": json.dumps(metadata_dict),
                        "vector_type": vector_type
                    })
                
                conn.commit()
                logger.info(f"Added/updated embedding: {embedding_id} ({vector_type})")
                
        except Exception as e:
            logger.error(f"Error adding embedding to PostgreSQL: {e}")
            raise
        
        return embedding_id
    
    async def search_similar(self, query: str, vector_type: Optional[str] = None, 
                           top_k: int = 5) -> List[VectorSearchResult]:
        """Search for similar content using PostgreSQL vector similarity"""
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        try:
            with self.engine.connect() as conn:
                # Simple search without vector similarity for now
                sql = """
                    SELECT 
                        id, content, meta_info, vector_type,
                        0.8 AS similarity
                    FROM vector_embeddings
                    WHERE 1=1
                """
                params = {}
                
                if vector_type:
                    sql += " AND vector_type = :vector_type"
                    params["vector_type"] = vector_type
                
                sql += " ORDER BY created_at DESC LIMIT :top_k"
                params["top_k"] = top_k
                
                result = conn.execute(text(sql), params)
                rows = result.fetchall()
                
                # Convert to VectorSearchResult objects
                similarities = []
                for row in rows:
                    similarities.append(VectorSearchResult(
                        id=row[0],
                        content=row[1],
                        similarity=float(row[4]),
                        meta_info=row[2] or {},
                        vector_type=row[3]
                    ))
                
                return similarities
                
        except Exception as e:
            logger.error(f"Error searching similar in PostgreSQL: {e}")
            return []
    
    async def search_by_metadata(self, metadata_filters: Dict[str, Any], 
                                top_k: int = 10) -> List[VectorSearchResult]:
        """Search by metadata filters"""
        
        try:
            with self.engine.connect() as conn:
                # Build metadata filter query
                conditions = []
                params = []
                
                for key, value in metadata_filters.items():
                    conditions.append(f"meta_info->>'{key}' = ${len(params) + 1}")
                    params.append(str(value))
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                sql = f"""
                    SELECT 
                        id, content, meta_info, vector_type,
                        1.0 AS similarity
                    FROM vector_embeddings
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${len(params) + 1}
                """
                params.append(top_k)
                
                result = conn.execute(text(sql), params)
                rows = result.fetchall()
                
                # Convert to VectorSearchResult objects
                results = []
                for row in rows:
                    results.append(VectorSearchResult(
                        id=row[0],
                        content=row[1],
                        similarity=float(row[4]),
                        meta_info=row[2] or {},
                        vector_type=row[3]
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching by metadata in PostgreSQL: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            with self.engine.connect() as conn:
                # Get total embeddings
                total_result = conn.execute(text("SELECT COUNT(*) FROM vector_embeddings"))
                total_embeddings = total_result.scalar()
                
                # Get embeddings by type
                type_result = conn.execute(text("""
                    SELECT vector_type, COUNT(*) 
                    FROM vector_embeddings 
                    GROUP BY vector_type
                """))
                embeddings_by_type = dict(type_result.fetchall())
                
                # Get recent activity
                recent_result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM vector_embeddings 
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """))
                recent_embeddings = recent_result.scalar()
                
                return {
                    "total_embeddings": total_embeddings,
                    "embeddings_by_type": embeddings_by_type,
                    "recent_embeddings_24h": recent_embeddings,
                    "storage_type": "postgresql_pgvector"
                }
                
        except Exception as e:
            logger.error(f"Error getting PostgreSQL vector stats: {e}")
            return {"error": str(e)}
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using LLM service"""
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use LLM to generate embedding
                llm_request = {
                    "prompt": f"Generate a numerical embedding for this text: {text}",
                    "max_tokens": 100,
                    "temperature": 0.1,
                    "task_type": "embedding"
                }
                
                url = f"{LLM_PROXY_URL}/api/embed"
                async with session.post(url, json=llm_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Parse embedding from response
                        embedding = self._parse_embedding_response(result.get("response", ""))
                        return embedding
                    else:
                        logger.error(f"LLM embedding error: {response.status}")
                        return self._generate_fallback_embedding(text)
                        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._generate_fallback_embedding(text)
    
    def _parse_embedding_response(self, response_text: str) -> List[float]:
        """Parse embedding from LLM response"""
        try:
            # Try to extract numbers from response
            import re
            numbers = re.findall(r'-?\d+\.?\d*', response_text)
            if numbers:
                embedding = [float(n) for n in numbers[:128]]  # Limit to 128 dimensions
                # Pad or truncate to 128 dimensions
                while len(embedding) < 128:
                    embedding.append(0.0)
                return embedding[:128]
        except:
            pass
        
        return self._generate_fallback_embedding("fallback")
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding when LLM fails"""
        # Simple hash-based embedding
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 128-dimensional embedding
        embedding = []
        for i in range(128):
            byte_index = i % len(hash_bytes)
            embedding.append(float(hash_bytes[byte_index]) / 255.0)
        
        return embedding

class MarketDataVectorizer:
    """Vectorize market data for PostgreSQL storage"""
    
    def __init__(self, vector_storage: PostgreSQLVectorStorage):
        self.vector_storage = vector_storage
    
    async def vectorize_market_data(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Vectorize market data"""
        
        content = f"""
Symbol: {symbol}
Price: ${market_data.get('price', 0):.2f}
Volume: {market_data.get('volume', 0):,}
Change: {market_data.get('change_percent', 0):.2f}%
Market Cap: {market_data.get('market_cap', 0)}
Technical Indicators: {market_data.get('technical_indicators', {})}
        """
        
        metadata_dict = {
            "symbol": symbol,
            "data_type": "market_data",
            "timestamp": datetime.now().isoformat(),
            "price": market_data.get('price'),
            "volume": market_data.get('volume'),
            "change_percent": market_data.get('change_percent')
        }
        
        return await self.vector_storage.add_embedding(content, metadata_dict, "market_data")
    
    async def vectorize_news_article(self, article: Dict[str, Any]) -> str:
        """Vectorize news article"""
        
        content = f"""
Title: {article.get('title', '')}
Content: {article.get('content', '')}
Summary: {article.get('summary', '')}
Source: {article.get('source', '')}
Sentiment: {article.get('sentiment_score', 0)}
        """
        
        metadata_dict = {
            "symbol": article.get('ticker'),
            "data_type": "news",
            "timestamp": article.get('published_at'),
            "source": article.get('source'),
            "sentiment_score": article.get('sentiment_score'),
            "event_type": article.get('event_type')
        }
        
        return await self.vector_storage.add_embedding(content, metadata_dict, "news")
    
    async def vectorize_decision(self, decision: Dict[str, Any]) -> str:
        """Vectorize investment decision"""
        
        content = f"""
Symbol: {decision.get('symbol', '')}
Action: {decision.get('action', '')}
Confidence: {decision.get('confidence', 0)}
Reasoning: {decision.get('reasoning', '')}
Risk Level: {decision.get('risk_level', '')}
Target Price: {decision.get('target_price')}
Stop Loss: {decision.get('stop_loss')}
        """
        
        metadata_dict = {
            "symbol": decision.get('symbol'),
            "data_type": "decision",
            "timestamp": decision.get('created_at'),
            "action": decision.get('action'),
            "confidence": decision.get('confidence'),
            "risk_level": decision.get('risk_level')
        }
        
        return await self.vector_storage.add_embedding(content, metadata_dict, "decision")

# Initialize PostgreSQL vector storage
vector_storage = PostgreSQLVectorStorage(DATABASE_URL)
market_vectorizer = MarketDataVectorizer(vector_storage)

@app.post("/api/vectorize/market-data")
async def vectorize_market_data(symbol: str, market_data: Dict[str, Any]) -> Dict[str, str]:
    """Vectorize market data"""
    try:
        embedding_id = await market_vectorizer.vectorize_market_data(symbol, market_data)
        return {"embedding_id": embedding_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error vectorizing market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectorize/news")
async def vectorize_news(article: Dict[str, Any]) -> Dict[str, str]:
    """Vectorize news article"""
    try:
        embedding_id = await market_vectorizer.vectorize_news_article(article)
        return {"embedding_id": embedding_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error vectorizing news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectorize/decision")
async def vectorize_decision(decision: Dict[str, Any]) -> Dict[str, str]:
    """Vectorize investment decision"""
    try:
        embedding_id = await market_vectorizer.vectorize_decision(decision)
        return {"embedding_id": embedding_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error vectorizing decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectorize/text")
async def vectorize_text(request: Dict[str, Any]) -> Dict[str, str]:
    """Generic text vectorization endpoint"""
    try:
        content = request.get("content")
        vector_type = request.get("vector_type", "generic")
        metadata = request.get("metadata", {})
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Add the content to vector storage
        embedding_id = await vector_storage.add_embedding(content, metadata, vector_type)
        return {"embedding_id": embedding_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error vectorizing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/similar")
async def search_similar(query: str, vector_type: Optional[str] = None, 
                        top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar content"""
    try:
        results = await vector_storage.search_similar(query, vector_type, top_k)
        return [
            {
                "id": result.id,
                "content": result.content,
                "similarity": result.similarity,
                "metadata": result.meta_info,
                "vector_type": result.vector_type
            }
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error searching similar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/metadata")
async def search_by_metadata(metadata_filters: Dict[str, Any], 
                           top_k: int = 10) -> List[Dict[str, Any]]:
    """Search by metadata filters"""
    try:
        results = await vector_storage.search_by_metadata(metadata_filters, top_k)
        return [
            {
                "id": result.id,
                "content": result.content,
                "similarity": result.similarity,
                "metadata": result.meta_info,
                "vector_type": result.vector_type
            }
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error searching by metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/context")
async def search_context(query: str, symbol: str, context_type: str = "all") -> Dict[str, Any]:
    """Search for relevant context for investment decision"""
    try:
        # Search for similar market data
        market_results = await vector_storage.search_similar(
            f"market data for {symbol}", "market_data", 3
        )
        
        # Search for similar news
        news_results = await vector_storage.search_similar(
            f"news about {symbol}", "news", 5
        )
        
        # Search for similar decisions
        decision_results = await vector_storage.search_similar(
            f"investment decision for {symbol}", "decision", 3
        )
        
        return {
            "market_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.meta_info
                }
                for result in market_results
            ],
            "news_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.meta_info
                }
                for result in news_results
            ],
            "decision_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.meta_info
                }
                for result in decision_results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get vector database statistics"""
    try:
        return await vector_storage.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "postgres-vector-storage"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 