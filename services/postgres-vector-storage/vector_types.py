#!/usr/bin/env python3
"""
Vector types for PostgreSQL vector storage
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class VectorSearchResult:
    """Search result with similarity score"""
    id: str
    content: str
    similarity: float
    meta_info: Dict[str, Any]
    vector_type: str 