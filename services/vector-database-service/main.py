#!/usr/bin/env python3
"""
Vector Database Service - Semantic search for market data and decisions
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
from dataclasses import dataclass
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Database Service", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:12001")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")

@dataclass
class VectorEmbedding:
    """Vector embedding for semantic search"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    vector_type: str  # "news", "market_data", "decision", "analysis"

@dataclass
class SearchResult:
    """Search result with similarity score"""
    id: str
    content: str
    similarity: float
    metadata: Dict[str, Any]
    vector_type: str

class VectorDatabase:
    """In-memory vector database with semantic search capabilities"""
    
    def __init__(self):
        self.embeddings: Dict[str, VectorEmbedding] = {}
        self.embedding_cache: Dict[str, List[float]] = {}
        
    async def add_embedding(self, content: str, metadata: Dict[str, Any], 
                           vector_type: str) -> str:
        """Add content to vector database"""
        
        # Generate embedding using LLM
        embedding = await self._generate_embedding(content)
        
        # Create unique ID
        content_hash = hashlib.md5(content.encode()).hexdigest()
        embedding_id = f"{vector_type}_{content_hash}"
        
        # Store embedding
        vector_embedding = VectorEmbedding(
            id=embedding_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            created_at=datetime.now(),
            vector_type=vector_type
        )
        
        self.embeddings[embedding_id] = vector_embedding
        logger.info(f"Added embedding: {embedding_id} ({vector_type})")
        
        return embedding_id
    
    async def search_similar(self, query: str, vector_type: Optional[str] = None, 
                           top_k: int = 5) -> List[SearchResult]:
        """Search for similar content"""
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        # Calculate similarities
        similarities = []
        for embedding_id, embedding in self.embeddings.items():
            if vector_type and embedding.vector_type != vector_type:
                continue
                
            similarity = self._cosine_similarity(query_embedding, embedding.embedding)
            similarities.append(SearchResult(
                id=embedding_id,
                content=embedding.content,
                similarity=similarity,
                metadata=embedding.metadata,
                vector_type=embedding.vector_type
            ))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_k]
    
    async def search_by_metadata(self, metadata_filters: Dict[str, Any], 
                                top_k: int = 10) -> List[SearchResult]:
        """Search by metadata filters"""
        
        results = []
        for embedding_id, embedding in self.embeddings.items():
            # Check if embedding matches all filters
            matches = True
            for key, value in metadata_filters.items():
                if key not in embedding.metadata or embedding.metadata[key] != value:
                    matches = False
                    break
            
            if matches:
                results.append(SearchResult(
                    id=embedding_id,
                    content=embedding.content,
                    similarity=1.0,  # Exact match
                    metadata=embedding.metadata,
                    vector_type=embedding.vector_type
                ))
        
        return results[:top_k]
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using LLM service"""
        
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
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
                        self.embedding_cache[cache_key] = embedding
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
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        # Ensure same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(a * a for a in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

class MarketDataVectorizer:
    """Vectorize market data for semantic search"""
    
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
    
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
        
        metadata = {
            "symbol": symbol,
            "data_type": "market_data",
            "timestamp": datetime.now().isoformat(),
            "price": market_data.get('price'),
            "volume": market_data.get('volume'),
            "change_percent": market_data.get('change_percent')
        }
        
        return await self.vector_db.add_embedding(content, metadata, "market_data")
    
    async def vectorize_news_article(self, article: Dict[str, Any]) -> str:
        """Vectorize news article"""
        
        content = f"""
Title: {article.get('title', '')}
Content: {article.get('content', '')}
Summary: {article.get('summary', '')}
Source: {article.get('source', '')}
Sentiment: {article.get('sentiment_score', 0)}
        """
        
        metadata = {
            "symbol": article.get('ticker'),
            "data_type": "news",
            "timestamp": article.get('published_at'),
            "source": article.get('source'),
            "sentiment_score": article.get('sentiment_score'),
            "event_type": article.get('event_type')
        }
        
        return await self.vector_db.add_embedding(content, metadata, "news")
    
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
        
        metadata = {
            "symbol": decision.get('symbol'),
            "data_type": "decision",
            "timestamp": decision.get('created_at'),
            "action": decision.get('action'),
            "confidence": decision.get('confidence'),
            "risk_level": decision.get('risk_level')
        }
        
        return await self.vector_db.add_embedding(content, metadata, "decision")

# Initialize services
vector_db = VectorDatabase()
market_vectorizer = MarketDataVectorizer(vector_db)

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

@app.get("/api/search/similar")
async def search_similar(query: str, vector_type: Optional[str] = None, 
                        top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar content"""
    try:
        results = await vector_db.search_similar(query, vector_type, top_k)
        return [
            {
                "id": result.id,
                "content": result.content,
                "similarity": result.similarity,
                "metadata": result.metadata,
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
        results = await vector_db.search_by_metadata(metadata_filters, top_k)
        return [
            {
                "id": result.id,
                "content": result.content,
                "similarity": result.similarity,
                "metadata": result.metadata,
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
        market_results = await vector_db.search_similar(
            f"market data for {symbol}", "market_data", 3
        )
        
        # Search for similar news
        news_results = await vector_db.search_similar(
            f"news about {symbol}", "news", 5
        )
        
        # Search for similar decisions
        decision_results = await vector_db.search_similar(
            f"investment decision for {symbol}", "decision", 3
        )
        
        return {
            "market_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.metadata
                }
                for result in market_results
            ],
            "news_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.metadata
                }
                for result in news_results
            ],
            "decision_context": [
                {
                    "content": result.content,
                    "similarity": result.similarity,
                    "metadata": result.metadata
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
        stats = {
            "total_embeddings": len(vector_db.embeddings),
            "embeddings_by_type": {},
            "cache_size": len(vector_db.embedding_cache)
        }
        
        # Count by type
        for embedding in vector_db.embeddings.values():
            vector_type = embedding.vector_type
            stats["embeddings_by_type"][vector_type] = stats["embeddings_by_type"].get(vector_type, 0) + 1
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 