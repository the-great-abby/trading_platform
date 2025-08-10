#!/usr/bin/env python3
"""
SQLAlchemy models for PostgreSQL vector storage
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class VectorEmbedding(Base):
    """Vector embedding model for PostgreSQL"""
    __tablename__ = 'vector_embeddings'
    
    id = Column(String(100), primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON array of floats
    metadata_json = Column(JSON, nullable=True)
    vector_type = Column(String(50), nullable=False)  # "news", "market_data", "decision", "analysis"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 