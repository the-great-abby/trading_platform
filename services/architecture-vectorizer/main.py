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
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

class ArchitectureVectorizer:
    """Service to vectorize architecture documentation"""
    
    def __init__(self):
        self.vector_storage_url = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama-host.ollama-controller.svc.cluster.local:11434")
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
        # For testing, let's start with just docs/ and md/ directories
        self.architecture_dirs = [
            "docs/",
            "md/",
            "README.md",
        ]
        
        # Directories to exclude from scanning
        self.exclude_dirs = [
            ".git/",
            "htmlcov/",
            "logs/",
            "backup/",
            "node_modules/",
            ".pytest_cache/",
            ".venv/",
            "test-env/",
            "migration-env/",
            "k8s-job-generator-env/",
            "port_monitor_logs/",
            "port_watcher_logs/",
            "port_watcher_v2_logs/",
            "test-data/",
            "test_scripts/",
            "tests/",
            "old-2025-07-07/",
            ".benchmarks/",
            ".cursor/",
            ".grc/",
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
            logger.info(f"🔗 Vector storage URL: {self.vector_storage_url}")
            logger.info(f"📂 Repository root: {self.repo_root}")
            
            # Find all documentation files
            files = await self._discover_documentation_files()
            logger.info(f"📁 Found {len(files)} documentation files")
            
            # Log file details
            for i, file_path in enumerate(files[:10]):  # Log first 10 files
                logger.info(f"📄 File {i+1}: {file_path}")
            if len(files) > 10:
                logger.info(f"📄 ... and {len(files) - 10} more files")
            
            # Process and vectorize each file
            processed_count = 0
            error_count = 0
            total_chunks_processed = 0
            
            for i, file_path in enumerate(files):
                try:
                    logger.info(f"🔄 Processing file {i+1}/{len(files)}: {file_path}")
                    file_chunks = await self._process_file(file_path)
                    processed_count += 1
                    total_chunks_processed += file_chunks
                    logger.info(f"✅ Successfully processed {file_path} ({file_chunks} chunks)")
                    
                    # Progress indicators
                    progress_percent = (processed_count / len(files)) * 100
                    logger.info(f"📊 File Progress: {processed_count}/{len(files)} files ({progress_percent:.1f}%) | Total Chunks: {total_chunks_processed}")
                    
                    if processed_count % 5 == 0:
                        logger.info(f"🎯 Milestone: {processed_count} files completed, {total_chunks_processed} total chunks vectorized")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Failed to process {file_path}: {e}")
                    logger.error(f"📋 Error details: {str(e)}")
            
            logger.info(f"🎉 Vectorization complete!")
            logger.info(f"📊 Final stats: {processed_count} successful, {error_count} failed out of {len(files)} total files")
            
        except Exception as e:
            logger.error(f"💥 Vectorization failed with exception: {e}")
            logger.error(f"📋 Exception details: {str(e)}")
            raise
    
    async def _discover_documentation_files(self) -> List[Path]:
        """Discover all documentation files in the repository"""
        files = []
        repo_path = Path(self.repo_root)
        
        # First, scan priority directories specifically
        for priority_dir in self.architecture_dirs:
            if priority_dir.endswith('/'):
                # Directory
                dir_path = repo_path / priority_dir
                if dir_path.exists() and dir_path.is_dir():
                    logger.info(f"🔍 Scanning priority directory: {priority_dir}")
                    for pattern in self.docs_patterns:
                        try:
                            pattern_files = list(dir_path.glob(pattern))
                            files.extend(pattern_files)
                        except Exception as e:
                            logger.warning(f"Failed to process pattern {pattern} in {priority_dir}: {e}")
            else:
                # Single file
                file_path = repo_path / priority_dir
                if file_path.exists() and file_path.is_file():
                    files.append(file_path)
        
        # Skip full repository scan for now - just use priority directories
        logger.info(f"🔍 Skipping full repository scan - using priority directories only")
        
        # Remove duplicates and filter out non-files
        files = list(set([f for f in files if f.is_file()]))
        
        # Filter out files in excluded directories
        filtered_files = []
        for file_path in files:
            file_str = str(file_path)
            should_exclude = False
            
            for exclude_dir in self.exclude_dirs:
                if exclude_dir in file_str:
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(file_path)
        
        # Sort by priority (architecture directories first)
        filtered_files.sort(key=lambda x: self._get_file_priority(x))
        
        logger.info(f"🔍 Filtered from {len(files)} to {len(filtered_files)} files after excluding directories")
        
        return filtered_files
    
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
    
    async def _process_file(self, file_path: Path) -> int:
        """Process and vectorize a single file"""
        try:
            logger.info(f"📖 Reading file: {file_path}")
            
            # Read file content
            content = await self._read_file_content(file_path)
            if not content:
                logger.warning(f"⚠️ Empty or unreadable file: {file_path}")
                return 0
            
            logger.info(f"📄 File size: {len(content)} characters")
            
            # Determine file category
            category = self._categorize_file(file_path, content)
            logger.info(f"🏷️ File category: {category}")
            
            # Create chunks for vectorization
            chunks = self._create_content_chunks(content, file_path)
            logger.info(f"📦 Created {len(chunks)} chunks for vectorization")
            
            # Vectorize each chunk
            for i, chunk in enumerate(chunks):
                logger.info(f"🔄 Vectorizing chunk {i+1}/{len(chunks)} from {file_path.name}")
                await self._vectorize_chunk(chunk, file_path, category, i)
            
            logger.info(f"✅ Completed processing {file_path.name} with {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"💥 Failed to process file {file_path}: {e}")
            logger.error(f"📋 Exception type: {type(e).__name__}")
            raise
    
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
            logger.info(f"🔄 Processing chunk {chunk_index} from {file_path.name} (category: {category})")
            
            # Create content hash for upsert logic
            content_hash = hashlib.md5(chunk.encode()).hexdigest()
            
            # Create metadata
            metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "category": category,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "content_hash": content_hash,
                "content_length": len(chunk),
                "source": "architecture-vectorizer"
            }
            
            logger.debug(f"📝 Created metadata for chunk {chunk_index}: {metadata}")
            
            # Store content in PostgreSQL vector storage with upsert logic
            logger.info(f"💾 Storing content in PostgreSQL vector storage: {self.vector_storage_url}/api/vectorize/text")
            await self._store_content(chunk, metadata, f"architecture_{category}", content_hash)
            
            logger.info(f"✅ Successfully vectorized chunk {chunk_index} from {file_path.name}")
            
        except Exception as e:
            logger.error(f"💥 Exception in vectorize_chunk for {file_path.name}: {e}")
            logger.error(f"📋 Chunk content preview: {chunk[:100]}...")
            raise
    
    
    async def _store_content(self, content: str, metadata: Dict[str, Any], vector_type: str, content_hash: str = None):
        """Store content in PostgreSQL vector storage with upsert logic"""
        try:
            store_request = {
                "content": content,
                "metadata": metadata,
                "vector_type": vector_type,
                "upsert": True,  # Enable upsert mode
                "content_hash": content_hash  # Use content hash for deduplication
            }
            
            logger.debug(f"📤 Sending storage request to PostgreSQL: {json.dumps(store_request, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectorize/text",
                    json=store_request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"📡 PostgreSQL response: {response.status} - {response_text[:200]}...")
                    
                    if response.status == 200:
                        result = await response.json()
                        action = result.get('action', 'created')
                        embedding_id = result.get('embedding_id')
                        
                        if action == 'updated':
                            logger.info(f"🔄 Updated existing content with ID: {embedding_id}")
                        else:
                            logger.info(f"✅ Created new content with ID: {embedding_id}")
                        
                        logger.debug(f"📊 Storage result: {result}")
                    else:
                        logger.error(f"❌ Failed to store content: {response.status}")
                        logger.error(f"📄 Response body: {response_text}")
                        raise Exception(f"PostgreSQL storage failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"💥 Exception in store_content: {e}")
            raise
    
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





