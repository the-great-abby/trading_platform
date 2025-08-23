#!/usr/bin/env python3
"""
Local Repository Vectorization Script
This script scans the local repository and vectorizes documentation into the vector storage.
"""

import os
import asyncio
import aiohttp
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalRepositoryVectorizer:
    """Local vectorizer for repository documentation"""
    
    def __init__(self):
        self.vector_storage_url = "http://localhost:11006"
        self.repo_root = Path(__file__).parent.parent  # Go up from scripts/ to repo root
        self.docs_patterns = [
            "**/*.md", "**/*.rst", "**/*.txt", "**/*.yaml", "**/*.yml",
            "**/*.py", "**/*.js", "**/*.html", "**/*.sh",
        ]
        self.architecture_dirs = [
            "docs/", "k8s/", "services/", "src/", "README.md", "Makefile",
        ]
        self.file_categories = {
            "kubernetes": ["k8s/", "kubernetes", "deployment", "service", "pod"],
            "architecture": ["architecture", "design", "system", "service"],
            "trading": ["trading", "strategy", "backtest", "portfolio"],
            "monitoring": ["monitoring", "grafana", "prometheus", "health"],
            "database": ["database", "postgres", "timescale", "vector"],
            "api": ["api", "endpoint", "service", "gateway"],
        }
        
    async def vectorize_repository(self):
        """Main method to vectorize the repository"""
        logger.info("🚀 Starting local repository vectorization...")
        
        try:
            # Discover documentation files
            files = self._discover_documentation_files()
            logger.info(f"📁 Found {len(files)} documentation files")
            
            # Process and vectorize each file
            success_count = 0
            for file_path in files:
                try:
                    await self._process_and_vectorize_file(file_path)
                    success_count += 1
                    logger.info(f"✅ Vectorized: {file_path}")
                except Exception as e:
                    logger.error(f"❌ Failed to vectorize {file_path}: {e}")
            
            logger.info(f"🎉 Vectorization complete! Successfully processed {success_count}/{len(files)} files")
            
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            raise
    
    def _discover_documentation_files(self) -> List[Path]:
        """Discover documentation files in the repository"""
        files = []
        
        for pattern in self.docs_patterns:
            if "**" in pattern:
                # Handle glob patterns
                base_pattern = pattern.replace("**/*", "")
                if base_pattern.startswith("/"):
                    base_pattern = base_pattern[1:]
                
                for file_path in self.repo_root.rglob(pattern.replace("**/*", "*")):
                    if file_path.is_file() and self._should_process_file(file_path):
                        files.append(file_path)
            else:
                # Handle specific files
                file_path = self.repo_root / pattern
                if file_path.is_file() and self._should_process_file(file_path):
                    files.append(file_path)
        
        # Also check specific architecture directories
        for dir_name in self.architecture_dirs:
            if dir_name.endswith("/"):
                dir_path = self.repo_root / dir_name
                if dir_path.is_dir():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and self._should_process_file(file_path):
                            files.append(file_path)
            else:
                file_path = self.repo_root / dir_name
                if file_path.is_file() and self._should_process_file(file_path):
                    files.append(file_path)
        
        # Remove duplicates and sort
        files = list(set(files))
        files.sort()
        return files
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed"""
        # Skip binary files and very large files
        if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
            return False
        
        # Skip hidden files and common non-documentation files
        skip_patterns = [
            ".git/", "__pycache__/", ".venv/", "node_modules/",
            ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe",
            ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg",
            ".zip", ".tar", ".gz", ".rar", ".7z",
        ]
        
        file_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in file_str:
                return False
        
        return True
    
    async def _process_and_vectorize_file(self, file_path: Path):
        """Process a single file and vectorize it"""
        try:
            # Read file content
            content = self._read_file_content(file_path)
            if not content:
                return
            
            # Determine file category
            category = self._categorize_file(file_path, content)
            
            # Chunk the content
            chunks = self._chunk_content(content, file_path)
            
            # Vectorize each chunk
            for i, chunk in enumerate(chunks):
                await self._vectorize_chunk(chunk, file_path, category, i)
                
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            raise
    
    def _read_file_content(self, file_path: Path) -> str:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content.strip()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return ""
    
    def _categorize_file(self, file_path: Path, content: str) -> str:
        """Categorize a file based on its path and content"""
        file_str = str(file_path).lower()
        content_lower = content.lower()
        
        # Check file path first
        for category, keywords in self.file_categories.items():
            for keyword in keywords:
                if keyword in file_str:
                    return category
        
        # Check content if path didn't give us a category
        for category, keywords in self.file_categories.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return category
        
        # Default category
        return "general"
    
    def _chunk_content(self, content: str, file_path: Path) -> List[str]:
        """Split content into manageable chunks"""
        # Simple chunking by lines, keeping related content together
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 1000  # characters
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        # If we have no chunks or only one very small chunk, return the whole content
        if not chunks or (len(chunks) == 1 and len(chunks[0]) < 100):
            return [content]
        
        return chunks
    
    async def _vectorize_chunk(self, chunk: str, file_path: Path, category: str, chunk_index: int):
        """Vectorize a single chunk of content"""
        try:
            # Create metadata
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path.relative_to(self.repo_root)),
                "category": category,
                "chunk_index": chunk_index,
                "file_size": file_path.stat().st_size,
                "last_modified": file_path.stat().st_mtime,
                "namespace": f"architecture_{category}",
            }
            
            # Create vector entry
            vector_data = {
                "content": chunk,
                "metadata": metadata,
                "namespace": f"architecture_{category}",
            }
            
            # Send to vector storage using the correct API endpoint
            async with aiohttp.ClientSession() as session:
                vectorize_request = {
                    "content": chunk,
                    "vector_type": f"architecture_{category}",
                    "metadata": metadata
                }
                
                async with session.post(
                    f"{self.vector_storage_url}/api/vectorize/text",
                    json=vectorize_request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Vectorized chunk {chunk_index} from {file_path.name}")
                    else:
                        logger.warning(f"Failed to vectorize chunk {chunk_index} from {file_path.name}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to vectorize chunk {chunk_index} from {file_path.name}: {e}")
            raise

async def main():
    """Main function"""
    vectorizer = LocalRepositoryVectorizer()
    await vectorizer.vectorize_repository()

if __name__ == "__main__":
    asyncio.run(main())
