#!/usr/bin/env python3
"""
AI IDE Service - Bridge between Cursor IDE and your local AI infrastructure
Provides intelligent code assistance using your architecture database and local LLM
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI IDE Service", version="1.0.0")

# Add CORS middleware for Cursor IDE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Cursor IDE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:20b")  # Best for code analysis and generation
ARCHITECTURE_MODEL = os.getenv("ARCHITECTURE_MODEL", "llama3.1:8b-instruct-q6_K")  # Best for architecture queries

class CodeAnalysisRequest(BaseModel):
    code: str
    file_path: str
    context: Optional[str] = None
    analysis_type: str = "general"  # general, bug_fix, optimization, documentation

class ArchitectureQueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    include_code_examples: bool = True

class CodeGenerationRequest(BaseModel):
    prompt: str
    file_path: str
    existing_code: Optional[str] = None
    language: str = "python"

class AIIDEResponse(BaseModel):
    response: str
    confidence: float
    sources: List[Dict[str, Any]]
    suggestions: List[str]
    timestamp: datetime

class AIIDEService:
    """AI IDE Service for intelligent code assistance"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.llm_model = LLM_MODEL
        self.architecture_model = ARCHITECTURE_MODEL
        
        # Cache for frequently accessed information
        self.code_cache = {}
        self.architecture_cache = {}
        
        logger.info(f"AI IDE Service initialized with Ollama at {self.ollama_url}")
    
    async def analyze_code(self, request: CodeAnalysisRequest) -> AIIDEResponse:
        """Analyze code using architecture context and local LLM"""
        try:
            # Search architecture database for relevant context
            architecture_context = await self._search_architecture_context(
                request.code, request.file_path
            )
            
            # Prepare analysis prompt
            prompt = self._build_analysis_prompt(request, architecture_context)
            
            # Get LLM analysis
            llm_response = await self._query_ollama(prompt, self.llm_model)
            
            # Extract suggestions and confidence
            suggestions = self._extract_suggestions(llm_response)
            confidence = self._calculate_confidence(llm_response, architecture_context)
            
            return AIIDEResponse(
                response=llm_response,
                confidence=confidence,
                sources=architecture_context,
                suggestions=suggestions,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def query_architecture(self, request: ArchitectureQueryRequest) -> AIIDEResponse:
        """Query architecture database for intelligent responses"""
        try:
            # Search vector storage
            search_results = await self._search_vector_storage(request.question)
            
            # Build context-aware prompt
            prompt = self._build_architecture_prompt(request, search_results)
            
            # Get LLM response
            llm_response = await self._query_ollama(prompt, self.architecture_model)
            
            return AIIDEResponse(
                response=llm_response,
                confidence=0.9,  # High confidence for architecture queries
                sources=search_results,
                suggestions=self._extract_architecture_suggestions(search_results),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Architecture query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_code(self, request: CodeGenerationRequest) -> AIIDEResponse:
        """Generate code using architecture context"""
        try:
            # Search for similar code patterns
            similar_code = await self._search_similar_code(request.prompt, request.file_path)
            
            # Build generation prompt
            prompt = self._build_generation_prompt(request, similar_code)
            
            # Generate code
            generated_code = await self._query_ollama(prompt, self.llm_model)
            
            return AIIDEResponse(
                response=generated_code,
                confidence=0.8,
                sources=similar_code,
                suggestions=self._extract_code_suggestions(generated_code),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _search_architecture_context(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Search architecture database for relevant context"""
        try:
            # Extract key concepts from code
            concepts = self._extract_code_concepts(code, file_path)
            
            # Search vector storage
            search_query = f"{' '.join(concepts)} {file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/search",
                    json={
                        "query": search_query,
                        "limit": 5,
                        "namespace": "architecture_*"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
                    else:
                        logger.warning(f"Vector search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Architecture context search failed: {e}")
            return []
    
    async def _search_vector_storage(self, query: str) -> List[Dict[str, Any]]:
        """Search vector storage for relevant information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/search",
                    json={
                        "query": query,
                        "limit": 10,
                        "namespace": "architecture_*"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
                    else:
                        logger.warning(f"Vector search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Vector storage search failed: {e}")
            return []
    
    async def _query_ollama(self, prompt: str, model: str) -> str:
        """Query Ollama for LLM response"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 2000
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama query failed: {response.status}")
                        return "Error: Could not generate response"
                        
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return "Error: Could not connect to Ollama"
    
    async def _search_similar_code(self, query: str, limit: int = 5) -> List[dict]:
        """Search for similar code patterns in the architecture database"""
        try:
            # Use the existing vector search method
            results = await self._search_vectors(query, limit)
            return results
        except Exception as e:
            logger.error(f"Similar code search failed: {e}")
            return []
    
    def _extract_code_concepts(self, code: str, file_path: str) -> List[str]:
        """Extract key concepts from code for context search"""
        concepts = []
        
        # Extract from file path
        if "k8s" in file_path:
            concepts.append("kubernetes")
        if "service" in file_path:
            concepts.append("service")
        if "trading" in file_path:
            concepts.append("trading")
        
        # Extract from code content
        if "class " in code:
            concepts.append("class")
        if "def " in code:
            concepts.append("function")
        if "import " in code:
            concepts.append("import")
        if "async" in code:
            concepts.append("async")
        
        return concepts
    
    def _build_analysis_prompt(self, request: CodeAnalysisRequest, context: List[Dict[str, Any]]) -> str:
        """Build analysis prompt with architecture context"""
        context_str = ""
        if context:
            context_str = "\n\nRelevant Architecture Context:\n"
            for item in context[:3]:  # Limit to top 3 results
                context_str += f"- {item.get('content', '')[:200]}...\n"
        
        return f"""Analyze the following code and provide intelligent suggestions:

File: {request.file_path}
Analysis Type: {request.analysis_type}

Code:
```python
{request.code}
```

{context_str}

Please provide:
1. Code quality assessment
2. Potential improvements
3. Architecture alignment
4. Best practices suggestions
5. Potential issues or bugs

Be specific and actionable in your recommendations."""

    def _build_architecture_prompt(self, request: ArchitectureQueryRequest, context: List[Dict[str, Any]]) -> str:
        """Build architecture query prompt"""
        context_str = ""
        if context:
            context_str = "\n\nRelevant Documentation:\n"
            for item in context[:5]:
                context_str += f"- {item.get('content', '')[:300]}...\n"
        
        return f"""Answer the following question about our trading system architecture:

Question: {request.question}

{context_str}

Please provide a comprehensive answer based on our actual architecture documentation. Include specific examples and references where possible."""

    def _build_generation_prompt(self, request: CodeGenerationRequest, similar_code: List[Dict[str, Any]]) -> str:
        """Build code generation prompt"""
        similar_str = ""
        if similar_code:
            similar_str = "\n\nSimilar Code Patterns:\n"
            for item in similar_code[:2]:
                similar_str += f"```python\n{item.get('content', '')[:500]}...\n```\n"
        
        return f"""Generate code for the following request:

Prompt: {request.prompt}
File: {request.file_path}
Language: {request.language}

{similar_str}

Please generate clean, well-documented code that follows our architecture patterns."""

    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract actionable suggestions from LLM response"""
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'consider', 'should']):
                suggestions.append(line.strip())
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _extract_architecture_suggestions(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract architecture-related suggestions"""
        suggestions = []
        for source in sources:
            if 'file_path' in source:
                suggestions.append(f"Review: {source['file_path']}")
        return suggestions[:3]
    
    def _extract_code_suggestions(self, code: str) -> List[str]:
        """Extract code-related suggestions"""
        suggestions = []
        if "TODO" in code:
            suggestions.append("Complete TODO items")
        if "FIXME" in code:
            suggestions.append("Address FIXME comments")
        if "import" in code:
            suggestions.append("Verify all imports are used")
        return suggestions
    
    def _calculate_confidence(self, response: str, context: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on response quality and context"""
        base_confidence = 0.5
        
        # Boost confidence if we have good context
        if context:
            base_confidence += 0.3
        
        # Boost confidence if response is detailed
        if len(response) > 200:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)

# Initialize service
ai_ide_service = AIIDEService()

@app.post("/api/analyze-code", response_model=AIIDEResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code with architecture context"""
    return await ai_ide_service.analyze_code(request)

@app.post("/api/query-architecture", response_model=AIIDEResponse)
async def query_architecture(request: ArchitectureQueryRequest):
    """Query architecture database"""
    return await ai_ide_service.query_architecture(request)

@app.post("/api/generate-code", response_model=AIIDEResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code with architecture context"""
    return await ai_ide_service.generate_code(request)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "ollama_url": OLLAMA_URL,
        "vector_storage_url": VECTOR_STORAGE_URL,
        "models": {
            "llm_model": LLM_MODEL,
            "architecture_model": ARCHITECTURE_MODEL
        }
    }

@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    result = await response.json()
                    return {"models": [model["name"] for model in result.get("models", [])]}
                else:
                    return {"error": "Could not fetch models"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11050)
