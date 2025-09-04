#!/usr/bin/env python3
"""
Architecture Vectorizer Service
Scans repository for documentation and vectorizes it for RAG chat
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import aiohttp
import json
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArchitectureVectorizer:
    """Service to vectorize architecture documentation"""
    
    def __init__(self):
        self.vector_storage_url = os.getenv("VECTOR_STORAGE_URL", "http://localhost:11151")
        self.repo_root = os.getenv("REPO_ROOT", "/app")
        self.docs_patterns = [
            "**/*.md",           # Markdown files
            "**/*.rst",          # ReStructuredText files
            "**/*.txt",          # Text files
            "**/*.yaml",         # YAML files
            "**/*.yml",          # YAML files
            "**/*.py",           # Python files (for docstrings)
            "**/*.js",           # JavaScript files
            "**/*.html",         # HTML files
            "**/*.sh",           # Shell scripts
        ]
        
        # Architecture-specific directories to prioritize
        self.architecture_dirs = [
            "docs/",
            "k8s/",
            "services/",
            "src/",
            "README.md",
            "Makefile",
        ]
        
        # File categories for better organization
        self.file_categories = {
            "kubernetes": ["k8s/", "kubernetes", "deployment", "service", "pod"],
            "architecture": ["architecture", "design", "system", "service"],
            "trading": ["trading", "strategy", "backtest", "portfolio"],
            "monitoring": ["monitoring", "grafana", "prometheus", "health"],
            "database": ["database", "postgres", "timescale", "vector"],
            "api": ["api", "endpoint", "service", "gateway"],
        }
    
    async def vectorize_repository(self):
        """Main method to vectorize the entire repository"""
        try:
            logger.info("🚀 Starting repository vectorization...")
            
            # Find all documentation files
            files = await self._discover_documentation_files()
            logger.info(f"📁 Found {len(files)} documentation files")
            
            # Process and vectorize each file
            processed_count = 0
            for file_path in files:
                try:
                    await self._process_file(file_path)
                    processed_count += 1
                    if processed_count % 10 == 0:
                        logger.info(f"✅ Processed {processed_count}/{len(files)} files")
                except Exception as e:
                    logger.error(f"❌ Failed to process {file_path}: {e}")
            
            logger.info(f"🎉 Vectorization complete! Processed {processed_count} files")
            
        except Exception as e:
            logger.error(f"❌ Vectorization failed: {e}")
            raise
    
    async def _discover_documentation_files(self) -> List[Path]:
        """Discover all documentation files in the repository"""
        files = []
        repo_path = Path(self.repo_root)
        
        for pattern in self.docs_patterns:
            try:
                pattern_files = list(repo_path.glob(pattern))
                files.extend(pattern_files)
            except Exception as e:
                logger.warning(f"Failed to process pattern {pattern}: {e}")
        
        # Remove duplicates and filter out non-files
        files = list(set([f for f in files if f.is_file()]))
        
        # Sort by priority (architecture directories first)
        files.sort(key=lambda x: self._get_file_priority(x))
        
        return files
    
    def _get_file_priority(self, file_path: Path) -> int:
        """Get priority score for file processing order"""
        priority = 0
        file_str = str(file_path).lower()
        
        # Higher priority for architecture-related files
        for dir_name in self.architecture_dirs:
            if dir_name.lower() in file_str:
                priority -= 10
        
        # Higher priority for specific file types
        if file_path.name.lower() in ["readme.md", "architecture.md", "design.md"]:
            priority -= 20
        
        return priority
    
    async def _process_file(self, file_path: Path):
        """Process and vectorize a single file"""
        try:
            # Read file content
            content = await self._read_file_content(file_path)
            if not content:
                return
            
            # Determine file category
            category = self._categorize_file(file_path, content)
            
            # Create chunks for vectorization
            chunks = self._create_content_chunks(content, file_path)
            
            # Vectorize each chunk
            for i, chunk in enumerate(chunks):
                await self._vectorize_chunk(chunk, file_path, category, i)
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
    
    async def _read_file_content(self, file_path: Path) -> str:
        """Read file content with proper encoding handling"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"Could not read {file_path} with any encoding")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""
    
    def _categorize_file(self, file_path: Path, content: str) -> str:
        """Categorize file based on path and content"""
        file_str = str(file_path).lower()
        content_lower = content.lower()
        
        # Check for category keywords
        for category, keywords in self.file_categories.items():
            for keyword in keywords:
                if keyword in file_str or keyword in content_lower:
                    return category
        
        # Default categories based on file extension
        if file_path.suffix == '.md':
            return "documentation"
        elif file_path.suffix in ['.yaml', '.yml']:
            return "configuration"
        elif file_path.suffix == '.py':
            return "code"
        else:
            return "general"
    
    def _create_content_chunks(self, content: str, file_path: Path) -> List[str]:
        """Create manageable chunks from file content"""
        chunks = []
        
        # Split by headers for markdown files
        if file_path.suffix == '.md':
            lines = content.split('\n')
            current_chunk = []
            
            for line in lines:
                if line.startswith('#'):
                    # Save previous chunk if it exists
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk).strip()
                        if chunk_text and len(chunk_text) > 50:
                            chunks.append(chunk_text)
                        current_chunk = []
                
                current_chunk.append(line)
            
            # Add the last chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text and len(chunk_text) > 50:
                    chunks.append(chunk_text)
        
        # For other files, split by paragraphs or fixed size
        else:
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para and len(para) > 50:
                    chunks.append(para)
        
        # If no chunks created, create fixed-size chunks
        if not chunks:
            chunk_size = 1000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
        
        return chunks
    
    async def _vectorize_chunk(self, chunk: str, file_path: Path, category: str, chunk_index: int):
        """Vectorize a content chunk and store it"""
        try:
            # Create metadata
            metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "category": category,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "content_hash": hashlib.md5(chunk.encode()).hexdigest(),
                "content_length": len(chunk),
                "source": "architecture-vectorizer"
            }
            
            # Prepare vectorization request
            vector_request = {
                "content": chunk,
                "metadata": metadata,
                "embedding_model": "text-embedding-ada-002",  # Default model
                "namespace": f"architecture_{category}"
            }
            
            # Send to vector storage
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/store",
                    json=vector_request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Vectorized chunk {chunk_index} from {file_path.name}")
                    else:
                        logger.warning(f"Failed to vectorize chunk from {file_path.name}: {response.status}")
            
        except Exception as e:
            logger.error(f"Failed to vectorize chunk from {file_path.name}: {e}")
    
    async def search_architecture(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search vectorized architecture knowledge"""
        try:
            search_request = {
                "query": query,
                "limit": limit,
                "namespace": f"architecture_{category}" if category else "architecture_*"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/search",
                    json=search_request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
                    else:
                        logger.warning(f"Search failed: {response.status}")
                        return []
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

async def main():
    """Main function to run the vectorizer"""
    vectorizer = ArchitectureVectorizer()
    
    # Check if running as a one-time job or continuous service
    if os.getenv("RUN_ONCE", "false").lower() == "true":
        # One-time vectorization
        await vectorizer.vectorize_repository()
    else:
        # Continuous service mode
        while True:
            try:
                await vectorizer.vectorize_repository()
                # Wait before next run
                await asyncio.sleep(int(os.getenv("VECTORIZE_INTERVAL", "3600")))  # Default: 1 hour
            except Exception as e:
                logger.error(f"Vectorization cycle failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

if __name__ == "__main__":
    asyncio.run(main())





