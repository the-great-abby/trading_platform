"""
Documentation Tool for MCP Service
Provides comprehensive documentation search, retrieval, and analysis capabilities
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class DocumentationEntry:
    """Represents a documentation entry"""
    file_path: str
    title: str
    content: str
    category: str
    tags: List[str]
    last_modified: datetime
    size: int
    relevance_score: float = 0.0

class DocumentationTool:
    """Tool for documentation search, retrieval, and analysis"""
    
    def __init__(self, base_path: str = None):
        # Use environment variables if available, otherwise fall back to default
        if base_path is None:
            base_path = os.getenv("BASE_PATH", "/Users/abby/code/trading")
        
        self.base_path = Path(base_path)
        
        # Use environment variables for docs and md paths if available
        docs_env = os.getenv("DOCS_PATH")
        md_env = os.getenv("MD_PATH")
        
        if docs_env:
            self.docs_path = Path(docs_env)
        else:
            self.docs_path = self.base_path / "docs"
            
        if md_env:
            self.md_path = Path(md_env)
        else:
            self.md_path = self.base_path / "md"
        self.documentation_index: Dict[str, DocumentationEntry] = {}
        self.category_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.search_index: Dict[str, List[str]] = defaultdict(list)
        
        # Documentation categories
        self.categories = {
            "architecture": ["architecture", "system", "design", "overview"],
            "trading": ["trading", "strategy", "backtest", "portfolio", "market"],
            "ai": ["ai", "llm", "analysis", "intelligence", "ml"],
            "kubernetes": ["kubernetes", "k8s", "deployment", "pods", "services"],
            "monitoring": ["monitoring", "observability", "metrics", "logs", "health"],
            "development": ["development", "dev", "coding", "implementation", "setup"],
            "deployment": ["deployment", "deploy", "production", "staging"],
            "data": ["data", "database", "storage", "migration", "analytics"],
            "security": ["security", "auth", "permissions", "access"],
            "api": ["api", "endpoints", "rest", "graphql", "integration"]
        }
        
        # Initialize documentation index synchronously
        self.build_index()
    
    def build_index(self):
        """Build comprehensive documentation index synchronously"""
        try:
            # Index docs directory
            self._index_directory_sync(self.docs_path, "docs")
            
            # Index md directory  
            self._index_directory_sync(self.md_path, "md")
            
            print(f"Documentation index built: {len(self.documentation_index)} entries")
            
        except Exception as e:
            print(f"Error building documentation index: {e}")
    
    def _index_directory_sync(self, directory: Path, source: str):
        """Index a directory synchronously"""
        if not directory.exists():
            print(f"Directory {directory} does not exist")
            return
            
        for file_path in directory.rglob("*.md"):
            try:
                self._index_file_sync(file_path, source)
            except Exception as e:
                print(f"Error indexing file {file_path}: {e}")
    
    def _index_file_sync(self, file_path: Path, source: str):
        """Index a single file synchronously"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first line or filename
            title = self._extract_title(content, file_path.name)
            
            # Determine category
            category = self._categorize_file(content, file_path.name)
            
            # Extract tags
            tags = self._extract_tags(content, file_path.name)
            
            # Get file stats
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size
            
            # Create documentation entry
            entry = DocumentationEntry(
                file_path=str(file_path),
                title=title,
                content=content,
                category=category,
                tags=tags,
                last_modified=last_modified,
                size=size
            )
            
            # Add to indexes
            self.documentation_index[str(file_path)] = entry
            self.category_index[category].append(str(file_path))
            
            for tag in tags:
                self.tag_index[tag].append(str(file_path))
            
            # Build search index
            search_text = f"{title} {content}".lower()
            words = re.findall(r'\b\w+\b', search_text)
            for word in words:
                if len(word) > 2:  # Skip short words
                    self.search_index[word].append(str(file_path))
                    
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from content or filename"""
        # Try to extract title from first markdown header
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # Fall back to filename without extension
        return filename.replace('.md', '').replace('_', ' ').title()
    
    def _categorize_file(self, content: str, filename: str) -> str:
        """Categorize file based on content and filename"""
        text = f"{content} {filename}".lower()
        
        # Check each category
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        # Default category
        return "general"
    
    def _extract_tags(self, content: str, filename: str) -> List[str]:
        """Extract tags from content and filename"""
        tags = set()
        
        # Look for markdown tags
        tag_pattern = r'#(\w+)'
        matches = re.findall(tag_pattern, content)
        tags.update(matches)
        
        # Look for common keywords in content and filename
        common_tags = ['trading', 'ai', 'kubernetes', 'docker', 'python', 'api', 'database', 'monitoring']
        text = f"{content} {filename}".lower()
        for tag in common_tags:
            if tag in text:
                tags.add(tag)
        
        return list(tags)
    
    async def _build_documentation_index(self):
        """Build comprehensive documentation index"""
        try:
            # Index docs directory
            await self._index_directory(self.docs_path, "docs")
            
            # Index md directory  
            await self._index_directory(self.md_path, "md")
            
            # Build search index
            await self._build_search_index()
            
            print(f"Documentation index built: {len(self.documentation_index)} entries")
        except Exception as e:
            print(f"Error building documentation index: {e}")
    
    async def _index_directory(self, directory: Path, category_prefix: str):
        """Index all markdown files in a directory"""
        if not directory.exists():
            return
            
        for file_path in directory.rglob("*.md"):
            try:
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                    
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from content or filename
                title = self._extract_title(content, file_path.name)
                
                # Determine category
                category = self._determine_category(content, file_path.name, category_prefix)
                
                # Extract tags
                tags = self._extract_tags(content, file_path.name)
                
                # Get file stats
                stat = file_path.stat()
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Create documentation entry
                entry = DocumentationEntry(
                    file_path=str(file_path.relative_to(self.base_path)),
                    title=title,
                    content=content,
                    category=category,
                    tags=tags,
                    last_modified=last_modified,
                    size=stat.st_size
                )
                
                # Add to index
                self.documentation_index[str(file_path.relative_to(self.base_path))] = entry
                
                # Add to category index
                self.category_index[category].append(str(file_path.relative_to(self.base_path)))
                
                # Add to tag index
                for tag in tags:
                    self.tag_index[tag].append(str(file_path.relative_to(self.base_path)))
                    
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from markdown content"""
        # Look for H1 header
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Look for title in frontmatter
        frontmatter_match = re.search(r'^---\s*\n(?:.*\n)*?title:\s*(.+)$', content, re.MULTILINE)
        if frontmatter_match:
            return frontmatter_match.group(1).strip()
        
        # Use filename as fallback
        return filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
    
    def _determine_category(self, content: str, filename: str, category_prefix: str) -> str:
        """Determine category based on content and filename"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Check for category keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in content_lower or keyword in filename_lower:
                    return category
        
        # Default category based on directory
        return category_prefix
    
    def _extract_tags(self, content: str, filename: str) -> List[str]:
        """Extract tags from content and filename"""
        tags = set()
        
        # Extract tags from frontmatter
        frontmatter_match = re.search(r'^---\s*\n(?:.*\n)*?tags:\s*(.+)$', content, re.MULTILINE)
        if frontmatter_match:
            frontmatter_tags = [tag.strip() for tag in frontmatter_match.group(1).split(',')]
            tags.update(frontmatter_tags)
        
        # Extract tags from content keywords
        content_lower = content.lower()
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in content_lower:
                    tags.add(keyword)
        
        # Add filename-based tags
        filename_words = re.findall(r'\w+', filename.lower())
        tags.update(filename_words)
        
        return list(tags)
    
    async def _build_search_index(self):
        """Build search index for fast text search"""
        for file_path, entry in self.documentation_index.items():
            # Index title and content
            searchable_text = f"{entry.title} {entry.content}".lower()
            words = re.findall(r'\w+', searchable_text)
            
            for word in words:
                if len(word) > 2:  # Skip short words
                    self.search_index[word].append(file_path)
    
    async def search_documentation(self, query: str, category: Optional[str] = None, 
                                 limit: int = 10) -> Dict[str, Any]:
        """Search documentation with query"""
        try:
            query_lower = query.lower()
            query_words = re.findall(r'\w+', query_lower)
            
            # Score entries based on query relevance
            scored_entries = []
            
            for file_path, entry in self.documentation_index.items():
                # Skip if category filter doesn't match
                if category and entry.category != category:
                    continue
                
                score = 0.0
                content_lower = entry.content.lower()
                title_lower = entry.title.lower()
                
                # Title matches get higher score
                for word in query_words:
                    if word in title_lower:
                        score += 3.0
                    if word in content_lower:
                        score += 1.0
                
                # Exact phrase matches get bonus
                if query_lower in title_lower:
                    score += 5.0
                if query_lower in content_lower:
                    score += 2.0
                
                # Tag matches
                for word in query_words:
                    if word in [tag.lower() for tag in entry.tags]:
                        score += 2.0
                
                if score > 0:
                    entry.relevance_score = score
                    scored_entries.append(entry)
            
            # Sort by relevance score
            scored_entries.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Return top results
            results = []
            for entry in scored_entries[:limit]:
                results.append({
                    "file_path": entry.file_path,
                    "title": entry.title,
                    "category": entry.category,
                    "tags": entry.tags,
                    "relevance_score": entry.relevance_score,
                    "last_modified": entry.last_modified.isoformat(),
                    "size": entry.size,
                    "preview": self._get_content_preview(entry.content, query)
                })
            
            return {
                "query": query,
                "category": category,
                "total_results": len(scored_entries),
                "returned_results": len(results),
                "results": results
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def _get_content_preview(self, content: str, query: str, max_length: int = 200) -> str:
        """Get content preview with query highlighted"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Find first occurrence of query
        query_pos = content_lower.find(query_lower)
        if query_pos == -1:
            # If query not found, return beginning of content
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # Get context around query
        start = max(0, query_pos - max_length // 2)
        end = min(len(content), query_pos + max_length // 2)
        
        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        
        return preview
    
    async def get_documentation_by_category(self, category: str) -> Dict[str, Any]:
        """Get all documentation in a specific category"""
        try:
            if category not in self.category_index:
                return {"error": f"Category '{category}' not found"}
            
            entries = []
            for file_path in self.category_index[category]:
                if file_path in self.documentation_index:
                    entry = self.documentation_index[file_path]
                    entries.append({
                        "file_path": entry.file_path,
                        "title": entry.title,
                        "tags": entry.tags,
                        "last_modified": entry.last_modified.isoformat(),
                        "size": entry.size
                    })
            
            return {
                "category": category,
                "total_entries": len(entries),
                "entries": entries
            }
            
        except Exception as e:
            return {"error": f"Failed to get category documentation: {str(e)}"}
    
    async def get_documentation_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get all documentation with a specific tag"""
        try:
            if tag not in self.tag_index:
                return {"error": f"Tag '{tag}' not found"}
            
            entries = []
            for file_path in self.tag_index[tag]:
                if file_path in self.documentation_index:
                    entry = self.documentation_index[file_path]
                    entries.append({
                        "file_path": entry.file_path,
                        "title": entry.title,
                        "category": entry.category,
                        "tags": entry.tags,
                        "last_modified": entry.last_modified.isoformat(),
                        "size": entry.size
                    })
            
            return {
                "tag": tag,
                "total_entries": len(entries),
                "entries": entries
            }
            
        except Exception as e:
            return {"error": f"Failed to get tag documentation: {str(e)}"}
    
    async def get_documentation_content(self, file_path: str) -> Dict[str, Any]:
        """Get full content of a specific documentation file"""
        try:
            if file_path not in self.documentation_index:
                return {"error": f"File '{file_path}' not found in documentation index"}
            
            entry = self.documentation_index[file_path]
            return {
                "file_path": entry.file_path,
                "title": entry.title,
                "content": entry.content,
                "category": entry.category,
                "tags": entry.tags,
                "last_modified": entry.last_modified.isoformat(),
                "size": entry.size
            }
            
        except Exception as e:
            return {"error": f"Failed to get documentation content: {str(e)}"}
    
    async def get_documentation_overview(self) -> Dict[str, Any]:
        """Get overview of all documentation"""
        try:
            # Count by category
            category_counts = {}
            for category, files in self.category_index.items():
                category_counts[category] = len(files)
            
            # Count by tag
            tag_counts = {}
            for tag, files in self.tag_index.items():
                tag_counts[tag] = len(files)
            
            # Get total stats
            total_files = len(self.documentation_index)
            total_size = sum(entry.size for entry in self.documentation_index.values())
            
            # Get recent files
            recent_files = sorted(
                self.documentation_index.values(),
                key=lambda x: x.last_modified,
                reverse=True
            )[:5]
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories": category_counts,
                "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "recent_files": [
                    {
                        "file_path": entry.file_path,
                        "title": entry.title,
                        "last_modified": entry.last_modified.isoformat()
                    }
                    for entry in recent_files
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to get documentation overview: {str(e)}"}
    
    async def get_available_categories(self) -> List[str]:
        """Get list of available categories"""
        return list(self.category_index.keys())
    
    async def get_available_tags(self) -> List[str]:
        """Get list of available tags"""
        return list(self.tag_index.keys())
    
    async def get_documentation_stats(self) -> Dict[str, Any]:
        """Get detailed documentation statistics"""
        try:
            # File type distribution
            file_types = defaultdict(int)
            for entry in self.documentation_index.values():
                file_types[entry.category] += 1
            
            # Size distribution
            sizes = [entry.size for entry in self.documentation_index.values()]
            avg_size = sum(sizes) / len(sizes) if sizes else 0
            
            # Tag distribution
            tag_counts = {}
            for tag, files in self.tag_index.items():
                tag_counts[tag] = len(files)
            
            return {
                "total_files": len(self.documentation_index),
                "total_categories": len(self.category_index),
                "total_tags": len(self.tag_index),
                "average_file_size": round(avg_size, 2),
                "largest_file": max(self.documentation_index.values(), key=lambda x: x.size).file_path if self.documentation_index else None,
                "category_distribution": dict(file_types),
                "tag_distribution": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)),
                "index_built_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to get documentation stats: {str(e)}"}
