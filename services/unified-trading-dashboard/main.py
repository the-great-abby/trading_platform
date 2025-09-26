#!/usr/bin/env python3
"""
Unified Trading Dashboard Service
Combines trading, performance, health dashboards, and Kubernetes RAG chat into a single service
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import time
import subprocess
import threading
import psutil
import hashlib
import aiohttp
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Trading Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory="templates")

# Configuration
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:10001")
ANALYTICS_API_URL = os.getenv("ANALYTICS_API_URL", "http://backtest-api:10001")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis.redis.svc.cluster.local:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres-timescale-external.postgres-infra.svc.cluster.local:5432/trading_bot")
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://ollama-controller-api-service.ollama-controller.svc.cluster.local:12001")

# New dedicated vector databases
KUBERNETES_VECTOR_DB_URL = os.getenv("KUBERNETES_VECTOR_DB_URL", "postgresql://postgres:postgres@postgres-vector-external.postgres-infra.svc.cluster.local:5432/kubernetes_vectors")
FINANCIAL_VECTOR_DB_URL = os.getenv("FINANCIAL_VECTOR_DB_URL", "postgresql://postgres:postgres@postgres-vector-external.postgres-infra.svc.cluster.local:5432/financial_vectors")

# Redis connection
redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Database connection
def get_database_connection():
    """Get database connection"""
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Kubernetes RAG Chat Models
class ChatRequest(BaseModel):
    question: str
    context: Optional[str] = None
    include_sources: bool = True
    max_tokens: int = 1000
    temperature: float = 0.3

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    timestamp: str
    processing_time: float
    request_id: Optional[str] = None
    status_url: Optional[str] = None

class KubernetesRAGChat:
    """Specialized RAG chat for Kubernetes questions"""
    
    def __init__(self):
        self.llm_proxy_url = LLM_PROXY_URL
        
        # Kubernetes-specific knowledge base
        self.k8s_knowledge = self._load_k8s_knowledge()
        
    def _load_k8s_knowledge(self) -> Dict[str, Any]:
        """Load Kubernetes-specific knowledge from docs"""
        knowledge = {
            "commands": {
                "pod_management": [
                    "kubectl get pods - List all pods",
                    "kubectl describe pod <pod-name> - Detailed pod info",
                    "kubectl logs <pod-name> - View pod logs",
                    "kubectl exec -it <pod-name> -- /bin/bash - Interactive shell",
                    "kubectl delete pod <pod-name> - Delete pod"
                ],
                "deployment_management": [
                    "kubectl get deployments - List deployments",
                    "kubectl scale deployment <name> --replicas=3 - Scale deployment",
                    "kubectl rollout restart deployment <name> - Restart deployment",
                    "kubectl rollout status deployment <name> - Check rollout status"
                ],
                "service_management": [
                    "kubectl get services - List services",
                    "kubectl describe service <service-name> - Service details",
                    "kubectl port-forward svc/<service> 8080:80 - Port forward"
                ],
                "configuration": [
                    "kubectl get configmaps - List configmaps",
                    "kubectl create configmap <name> --from-file=<file> - Create configmap",
                    "kubectl get secrets - List secrets",
                    "kubectl create secret generic <name> --from-literal=<key>=<value> - Create secret"
                ],
                "debugging": [
                    "kubectl get events - List events",
                    "kubectl describe node <node-name> - Node details",
                    "kubectl top pods - Resource usage",
                    "kubectl get endpoints - Service endpoints"
                ]
            },
            "concepts": {
                "pods": "Smallest deployable units in Kubernetes",
                "services": "Abstract way to expose applications",
                "deployments": "Manage pod replicas and updates",
                "configmaps": "Store non-sensitive configuration",
                "secrets": "Store sensitive data",
                "namespaces": "Virtual clusters within a cluster",
                "persistent_volumes": "Storage resources",
                "ingress": "External access to services"
            },
            "troubleshooting": {
                "pod_pending": "Check node resources and scheduling",
                "pod_crashloopbackoff": "Check logs and configuration",
                "service_unreachable": "Check endpoints and labels",
                "image_pull_backoff": "Check image name and registry"
            }
        }
        return knowledge
    
    async def process_question(self, question: str, context: Optional[str] = None) -> ChatResponse:
        """Process a Kubernetes question and return AI response with sources"""
        try:
            logger.info(f"Starting process_question for: {question[:50]}...")
            
            # Search for relevant Kubernetes knowledge
            logger.info("Searching k8s knowledge...")
            k8s_knowledge = await self._search_k8s_knowledge(question)
            logger.info(f"Found {len(k8s_knowledge)} k8s knowledge items")
            
            # Search vector storage for additional context
            logger.info("Searching vector storage...")
            vector_results = await self._search_vector_storage(question)
            logger.info(f"Found {len(vector_results)} vector results")
            
            # Build context from all sources
            logger.info("Building context...")
            context_str = self._build_context(question, k8s_knowledge, vector_results, context)
            logger.info(f"Context built, length: {len(context_str)}")
            
            # Generate AI response
            logger.info(f"About to call _generate_ai_response for question: {question[:50]}...")
            ai_response = await self._generate_ai_response(question, context_str)
            logger.info(f"AI response received: {ai_response}")
            
            # Calculate confidence
            confidence = self._calculate_confidence(k8s_knowledge, vector_results)
            
            # Prepare sources
            sources = []
            for knowledge in k8s_knowledge:
                sources.append({
                    "type": "command",
                    "category": knowledge.get("category", "general"),
                    "content": knowledge.get("content", ""),
                    "relevance": knowledge.get("relevance", 0.5)
                })
            
            for result in vector_results:
                sources.append({
                    "type": "document",
                    "category": result.get("category", "general"),
                    "content": result.get("content", ""),
                    "relevance": result.get("relevance", 0.5)
                })
            
            return ChatResponse(
                answer=ai_response.get("answer", "I'm sorry, I couldn't generate a response."),
                sources=sources,
                confidence=confidence,
                timestamp=datetime.now().isoformat(),
                processing_time=0.0,  # Will be set by the endpoint
                request_id=ai_response.get("request_id"),
                status_url=ai_response.get("status_url")
            )
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return ChatResponse(
                answer=f"I encountered an error while processing your question: {str(e)}",
                sources=[],
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                processing_time=0.0
            )
    
    async def _search_k8s_knowledge(self, question: str) -> List[Dict[str, Any]]:
        """Search Kubernetes-specific knowledge base"""
        relevant_knowledge = []
        question_lower = question.lower()
        
        # Search commands
        for category, commands in self.k8s_knowledge["commands"].items():
            for command in commands:
                if any(keyword in question_lower for keyword in command.lower().split()):
                    relevant_knowledge.append({
                        "type": "command",
                        "category": category,
                        "content": command,
                        "relevance": 0.8
                    })
        
        # Search concepts
        for concept, description in self.k8s_knowledge["concepts"].items():
            if concept.replace("_", " ") in question_lower:
                relevant_knowledge.append({
                    "type": "concept",
                    "category": "concepts",
                    "content": f"{concept}: {description}",
                    "relevance": 0.9
                })
        
        # Search troubleshooting
        for issue, solution in self.k8s_knowledge["troubleshooting"].items():
            if issue.replace("_", " ") in question_lower:
                relevant_knowledge.append({
                    "type": "troubleshooting",
                    "category": "troubleshooting",
                    "content": f"{issue}: {solution}",
                    "relevance": 0.7
                })
        
        return relevant_knowledge
    
    async def _search_vector_storage(self, question: str) -> List[Dict[str, Any]]:
        """Search vector storage for additional context - now question-aware"""
        try:
            # Determine which database to search based on question content
            question_lower = question.lower()
            
            # Keywords that indicate Kubernetes/system questions
            k8s_keywords = [
                'kubernetes', 'k8s', 'pod', 'deployment', 'service', 'configmap', 
                'secret', 'namespace', 'cluster', 'node', 'container', 'docker',
                'helm', 'operator', 'crd', 'rbac', 'network policy', 'ingress',
                'persistent volume', 'statefulset', 'daemonset', 'job', 'cronjob'
            ]
            
            # Keywords that indicate financial/trading questions
            financial_keywords = [
                'stock', 'market', 'trading', 'portfolio', 'investment', 'price',
                'earnings', 'financial', 'revenue', 'profit', 'loss', 'dividend',
                'option', 'futures', 'forex', 'crypto', 'bond', 'etf', 'mutual fund',
                'risk', 'volatility', 'beta', 'alpha', 'sharpe ratio', 'correlation'
            ]
            
            # Count keyword matches
            k8s_score = sum(1 for keyword in k8s_keywords if keyword in question_lower)
            financial_score = sum(1 for keyword in financial_keywords if keyword in question_lower)
            
            # Determine which database to use
            if k8s_score > financial_score:
                db_url = KUBERNETES_VECTOR_DB_URL
                vector_types = ['architecture_kubernetes', 'architecture_monitoring']
                db_name = "Kubernetes"
            else:
                db_url = FINANCIAL_VECTOR_DB_URL
                vector_types = ['architecture_trading', 'architecture_api', 'architecture_database', 'architecture_general']
                db_name = "Financial"
            
            logger.info(f"Question '{question}' classified as {db_name} (k8s: {k8s_score}, financial: {financial_score})")
            
            # Search the appropriate database directly
            results = []
            for vector_type in vector_types:
                try:
                    # Connect to the appropriate database
                    import psycopg2
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()
                    
                    # Search for similar content using vector similarity
                    cursor.execute("""
                        SELECT id, content, meta_info, 
                               embedding <=> %s as distance
                        FROM vector_embeddings 
                        WHERE vector_type = %s
                        ORDER BY embedding <=> %s
                        LIMIT 3
                    """, (self._get_question_embedding(question), vector_type, self._get_question_embedding(question)))
                    
                    type_results = cursor.fetchall()
                    for record in type_results:
                        id_val, content, meta_info, distance = record
                        similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity
                        
                        results.append({
                            "type": "document",
                            "category": meta_info.get("category", "general") if meta_info else "general",
                            "content": content,
                            "relevance": similarity,
                            "source": meta_info.get("file_name", "Unknown") if meta_info else "Unknown",
                            "file_path": meta_info.get("file_path", "") if meta_info else "",
                            "vector_type": vector_type
                        })
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    logger.warning(f"Failed to search {vector_type} in {db_name} database: {e}")
                    continue
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x["relevance"], reverse=True)
            return results[:5]
                        
        except Exception as e:
            logger.warning(f"Vector storage search failed: {e}")
            return []
    
    def _get_question_embedding(self, question: str) -> str:
        """Get a simple embedding representation for the question"""
        # For now, use a simple approach - in production you'd use a proper embedding model
        # This is a placeholder that will be replaced with actual embedding logic
        import hashlib
        return hashlib.md5(question.encode()).hexdigest()[:32]  # Simple hash-based representation
    
    def _build_context(self, question: str, k8s_knowledge: List[Dict[str, Any]], 
                      vector_results: List[Dict[str, Any]], context: Optional[str] = None) -> str:
        """Build context string from all sources - now question-aware"""
        context_parts = []
        
        if context:
            context_parts.append(f"User Context: {context}")
        
        # Only include Kubernetes knowledge for Kubernetes questions
        question_lower = question.lower()
        k8s_keywords = ['kubernetes', 'k8s', 'pod', 'deployment', 'service', 'configmap', 
                       'secret', 'namespace', 'cluster', 'node', 'container', 'docker']
        
        if any(keyword in question_lower for keyword in k8s_keywords) and k8s_knowledge:
            context_parts.append("Kubernetes Knowledge:")
            for knowledge in k8s_knowledge:
                context_parts.append(f"- {knowledge['content']}")
        
        if vector_results:
            # Determine the type of documents found
            if vector_results and 'vector_type' in vector_results[0]:
                vector_type = vector_results[0]['vector_type']
                if 'kubernetes' in vector_type or 'monitoring' in vector_type:
                    context_parts.append("Kubernetes System Documents:")
                elif 'trading' in vector_type or 'api' in vector_type or 'database' in vector_type:
                    context_parts.append("Trading System Documents:")
                else:
                    context_parts.append("Additional Documents:")
            else:
                context_parts.append("Additional Documents:")
                
            for result in vector_results:
                context_parts.append(f"- {result['content']}")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, question: str, context: str) -> Dict[str, Any]:
        """Generate AI response using LLM proxy"""
        try:
            # Prepare the prompt with context - now question-aware
            question_lower = question.lower()
            k8s_keywords = ['kubernetes', 'k8s', 'pod', 'deployment', 'service', 'configmap', 
                           'secret', 'namespace', 'cluster', 'node', 'container', 'docker']
            financial_keywords = ['stock', 'market', 'trading', 'portfolio', 'investment', 'price',
                                'earnings', 'financial', 'revenue', 'profit', 'loss', 'dividend']
            
            if any(keyword in question_lower for keyword in k8s_keywords):
                role = "Kubernetes system administrator and instructor"
                focus = "Kubernetes concepts, commands, and system administration"
            elif any(keyword in question_lower for keyword in financial_keywords):
                role = "financial analyst and trading system expert"
                focus = "trading systems, market data, and financial analysis"
            else:
                role = "AI assistant with knowledge about trading systems and infrastructure"
                focus = "providing helpful, accurate information"
            
            prompt = f"""You are a {role}. Your expertise is in {focus}.

Question: {question}

Context from knowledge base:
{context}

Please provide a helpful, accurate answer based on the context provided. If the context doesn't contain relevant information, say so clearly. Focus on being helpful and accurate.

Answer:"""

            # Send to LLM proxy
            async with aiohttp.ClientSession() as session:
                llm_request = {
                    "model": "gpt-oss:20b",
                    "prompt": prompt,
                    "stream": False,
                    "priority": 40,
                    "timeout_seconds": 300,
                    "request_id": str(uuid.uuid4()),
                    "callback_url": f"http://unified-trading-dashboard:80/api/rag/callback/{str(uuid.uuid4())}",
                    "callback_method": "POST"
                }
                
                async with session.post(
                    f"{self.llm_proxy_url}/api/generate",
                    json=llm_request,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Check for the async response format
                        if "request_id" in result and result.get("status") == "queued":
                            # This is an async request, we need to return a status response
                            actual_request_id = result["request_id"]
                            logger.info(f"Submitted request {actual_request_id} to external LLM service")
                            
                            # Return a response indicating the request is being processed
                            status_url = f"/api/rag/status/{actual_request_id}"
                            
                            return {
                                "answer": f"Your request is being processed by the AI service. This may take a few minutes due to high demand. You can check the status of your request at: <a href='{status_url}' target='_blank' style='color: #007bff; text-decoration: underline;'>{status_url}</a>",
                                "model": "gpt-oss:20b",
                                "request_id": actual_request_id,
                                "status_url": status_url
                            }
                        else:
                            logger.error(f"Unexpected LLM response format: {result}")
                            return {"answer": "I'm having trouble processing the AI response. Please try again later."}
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM request failed with status {response.status}: {error_text}")
                        logger.error(f"Request that failed: {llm_request}")
                        logger.error(f"Response headers: {dict(response.headers)}")
                        return {"answer": "I'm having trouble connecting to the AI service. Please try again later."}
                        
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            # Fallback response
            if context:
                return {
                    "answer": f"Based on the available information: {context}",
                    "request_id": hashlib.md5(f"{question}{time.time()}".encode()).hexdigest()[:8]
                }
            else:
                return {
                    "answer": "I'm sorry, I couldn't generate an AI response at this time. Please try rephrasing your question.",
                    "request_id": None
                }
    
    def _calculate_confidence(self, k8s_knowledge: List[Dict[str, Any]], 
                            vector_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on available sources"""
        total_sources = len(k8s_knowledge) + len(vector_results)
        if total_sources == 0:
            return 0.0
        
        # Simple confidence calculation
        confidence = min(0.9, 0.3 + (total_sources * 0.1))
        return round(confidence, 2)

# Initialize RAG chat
rag_chat = KubernetesRAGChat()

class DashboardConfig:
    """Dashboard configuration"""
    REFRESH_INTERVAL = 30  # seconds
    MAX_RECENT_RUNS = 10
    DEFAULT_PERIOD = "1m"

class UnifiedTradingDashboard:
    """Unified dashboard manager"""
    
    def __init__(self):
        self.backtest_api_url = BACKTEST_API_URL
        self.analytics_api_url = ANALYTICS_API_URL
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from local database"""
        try:
            # Connect to database
            engine = get_database_connection()
            if not engine:
                return {"error": "Database connection failed"}
            
            with engine.connect() as conn:
                # Get performance data from trades
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        SUM(value) as total_volume
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                """))
                performance_data = result.fetchone()
                
                if not performance_data or performance_data[0] == 0:
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "total_pnl": 0.0,
                        "avg_pnl": 0.0,
                        "best_trade": 0.0,
                        "worst_trade": 0.0,
                        "total_volume": 0.0,
                        "profit_factor": 0.0,
                        "avg_win": 0.0,
                        "avg_loss": 0.0,
                        "message": "No recent trades for performance analysis"
                    }
                
                total_trades = performance_data[0]
                winning_trades = performance_data[1]
                losing_trades = performance_data[2]
                total_pnl = performance_data[3] or 0.0
                avg_pnl = performance_data[4] or 0.0
                best_trade = performance_data[5] or 0.0
                worst_trade = performance_data[6] or 0.0
                total_volume = performance_data[7] or 0.0
                
                # Calculate derived metrics
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                # Get average win/loss
                win_result = conn.execute(text("""
                    SELECT AVG(pnl) as avg_win FROM trades 
                    WHERE pnl > 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                avg_win = win_result.fetchone()[0] or 0.0
                
                loss_result = conn.execute(text("""
                    SELECT AVG(pnl) as avg_loss FROM trades 
                    WHERE pnl < 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                avg_loss = abs(loss_result.fetchone()[0] or 0.0)
                
                profit_factor = (avg_win / avg_loss) if avg_loss > 0 else 0.0
                
                return {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(total_pnl, 2),
                    "avg_pnl": round(avg_pnl, 2),
                    "best_trade": round(best_trade, 2),
                    "worst_trade": round(worst_trade, 2),
                    "total_volume": round(total_volume, 2),
                    "profit_factor": round(profit_factor, 2),
                    "avg_win": round(avg_win, 2),
                    "avg_loss": round(avg_loss, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get system health status with Redis metrics"""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis": "connected" if redis_client else "disconnected"
        }
        
        if not redis_client:
            status["status"] = "degraded"
        
        # Add Redis metrics if available
        if redis_client:
            try:
                cache_stats = redis_client.info("memory")
                status["cache_memory"] = cache_stats.get("used_memory_human", "N/A")
                status["cache_keys"] = redis_client.dbsize()
                
                # Get recent logs (if stored in Redis)
                recent_logs = redis_client.lrange("system_logs", 0, 9)
                status["recent_logs"] = [log.decode() for log in recent_logs]
            except Exception as e:
                logger.error(f"Error getting Redis metrics: {e}")
                status["redis_error"] = str(e)
        
        return status
    
    async def get_recent_runs(self) -> Dict[str, Any]:
        """Get recent backtest runs"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backtest_api_url}/api/v1/runs?limit={DashboardConfig.MAX_RECENT_RUNS}")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backtest API returned {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting recent runs: {e}")
            return {"error": str(e)}
    
    async def get_performance_metrics_detailed(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            # Connect to database
            engine = get_database_connection()
            if not engine:
                return {"error": "Database connection failed"}
            
            with engine.connect() as conn:
                # Get performance data from trades
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        SUM(value) as total_volume
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                """))
                performance_data = result.fetchone()
                
                if not performance_data or performance_data[0] == 0:
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "total_pnl": 0.0,
                        "avg_pnl": 0.0,
                        "best_trade": 0.0,
                        "worst_trade": 0.0,
                        "total_volume": 0.0,
                        "profit_factor": 0.0,
                        "avg_win": 0.0,
                        "avg_loss": 0.0,
                        "message": "No recent trades for performance analysis"
                    }
                
                total_trades = performance_data[0]
                winning_trades = performance_data[1]
                losing_trades = performance_data[2]
                total_pnl = float(performance_data[3] or 0)
                avg_pnl = float(performance_data[4] or 0)
                best_trade = float(performance_data[5] or 0)
                worst_trade = float(performance_data[6] or 0)
                total_volume = float(performance_data[7] or 0)
                
                # Calculate derived metrics
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                # Get average win and loss
                win_result = conn.execute(text("""
                    SELECT AVG(pnl) FROM trades 
                    WHERE pnl > 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                avg_win = float(win_result.scalar() or 0)
                
                loss_result = conn.execute(text("""
                    SELECT AVG(pnl) FROM trades 
                    WHERE pnl < 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                avg_loss = float(loss_result.scalar() or 0)
                
                # Calculate profit factor
                total_wins = conn.execute(text("""
                    SELECT SUM(pnl) FROM trades 
                    WHERE pnl > 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                total_wins_value = float(total_wins.scalar() or 0)
                
                total_losses = conn.execute(text("""
                    SELECT SUM(pnl) FROM trades 
                    WHERE pnl < 0 AND timestamp >= NOW() - INTERVAL '30 days'
                """))
                total_losses_value = abs(float(total_losses.scalar() or 0))
                
                profit_factor = total_wins_value / total_losses_value if total_losses_value > 0 else 0.0
                
                # Get performance by strategy
                strategy_performance = conn.execute(text("""
                    SELECT strategy, 
                           COUNT(*) as trades,
                           SUM(pnl) as total_pnl,
                           AVG(pnl) as avg_pnl,
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY strategy
                    ORDER BY total_pnl DESC
                """))
                
                strategies = []
                for row in strategy_performance:
                    strategy_data = {
                        'strategy': row[0] or 'Unknown',
                        'trades': row[1],
                        'total_pnl': float(row[2] or 0),
                        'avg_pnl': float(row[3] or 0),
                        'wins': row[4],
                        'win_rate': (row[4] / row[1] * 100) if row[1] > 0 else 0.0
                    }
                    strategies.append(strategy_data)
                
                return {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "avg_pnl": avg_pnl,
                    "best_trade": best_trade,
                    "worst_trade": worst_trade,
                    "total_volume": total_volume,
                    "profit_factor": profit_factor,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss,
                    "strategies": strategies
                }
                
        except Exception as e:
            logger.error(f"Error getting detailed performance metrics: {e}")
            return {"error": str(e)}
    
    async def get_risk_analysis(self) -> Dict[str, Any]:
        """Get risk analysis data"""
        try:
            # Connect to database
            engine = get_database_connection()
            if not engine:
                return {"error": "Database connection failed"}
            
            with engine.connect() as conn:
                # Get recent trades for risk analysis
                result = conn.execute(text("""
                    SELECT pnl, value, timestamp, strategy 
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                """))
                trades = result.fetchall()
                
                if not trades:
                    return {
                        "total_trades": 0,
                        "current_exposure": 0.0,
                        "max_drawdown": 0.0,
                        "avg_drawdown": 0.0,
                        "risk_score": "low",
                        "var_95": 0.0,
                        "sharpe_ratio": 0.0,
                        "volatility": 0.0,
                        "message": "No recent trades for risk analysis"
                    }
                
                # Calculate risk metrics
                pnl_values = [float(trade[0] or 0) for trade in trades]
                trade_values = [float(trade[1] or 0) for trade in trades]
                
                # Current exposure (sum of recent trade values)
                current_exposure = sum(trade_values[-10:]) if trade_values else 0.0
                
                # Calculate drawdown
                cumulative_pnl = []
                running_total = 0
                for pnl in pnl_values:
                    running_total += pnl
                    cumulative_pnl.append(running_total)
                
                if cumulative_pnl:
                    peak = max(cumulative_pnl)
                    max_drawdown = min(cumulative_pnl) - peak if min(cumulative_pnl) < peak else 0.0
                    avg_drawdown = sum([max(0, peak - val) for val in cumulative_pnl]) / len(cumulative_pnl)
                else:
                    max_drawdown = 0.0
                    avg_drawdown = 0.0
                
                # Calculate Value at Risk (95% confidence)
                if len(pnl_values) > 1:
                    import statistics
                    mean_pnl = statistics.mean(pnl_values)
                    std_pnl = statistics.stdev(pnl_values) if len(pnl_values) > 1 else 0
                    var_95 = mean_pnl - (1.645 * std_pnl)  # 95% VaR
                    
                    # Sharpe ratio (assuming risk-free rate of 0)
                    sharpe_ratio = mean_pnl / std_pnl if std_pnl > 0 else 0.0
                    volatility = std_pnl
                else:
                    var_95 = 0.0
                    sharpe_ratio = 0.0
                    volatility = 0.0
                
                # Risk score based on metrics
                risk_score = "low"
                if max_drawdown < -0.05 or var_95 < -0.02:
                    risk_score = "high"
                elif max_drawdown < -0.02 or var_95 < -0.01:
                    risk_score = "medium"
                
                return {
                    "total_trades": len(trades),
                    "current_exposure": current_exposure,
                    "max_drawdown": max_drawdown,
                    "avg_drawdown": avg_drawdown,
                    "risk_score": risk_score,
                    "var_95": var_95,
                    "sharpe_ratio": sharpe_ratio,
                    "volatility": volatility,
                    "recent_trades_count": len(trades[-10:]) if trades else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting risk analysis: {e}")
            return {"error": str(e)}
    
    async def get_trade_analysis(self) -> Dict[str, Any]:
        """Get trade analysis data"""
        try:
            # Connect to database
            engine = get_database_connection()
            if not engine:
                return {"error": "Database connection failed"}
            
            with engine.connect() as conn:
                # Get recent trades for analysis
                result = conn.execute(text("""
                    SELECT symbol, action, quantity, price, pnl, value, timestamp, strategy
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                """))
                trades = result.fetchall()
                
                if not trades:
                    return {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "avg_trade_value": 0.0,
                        "best_trade": None,
                        "worst_trade": None,
                        "message": "No recent trades for analysis"
                    }
                
                # Analyze trades
                winning_trades = 0
                losing_trades = 0
                total_value = 0.0
                best_trade = None
                worst_trade = None
                
                for trade in trades:
                    pnl = float(trade[4] or 0)
                    value = float(trade[5] or 0)
                    total_value += value
                    
                    if pnl > 0:
                        winning_trades += 1
                        if best_trade is None or pnl > best_trade['pnl']:
                            best_trade = {
                                'symbol': trade[0],
                                'action': trade[1],
                                'quantity': trade[2],
                                'price': trade[3],
                                'pnl': pnl,
                                'timestamp': trade[6].isoformat() if trade[6] else None
                            }
                    elif pnl < 0:
                        losing_trades += 1
                        if worst_trade is None or pnl < worst_trade['pnl']:
                            worst_trade = {
                                'symbol': trade[0],
                                'action': trade[1],
                                'quantity': trade[2],
                                'price': trade[3],
                                'pnl': pnl,
                                'timestamp': trade[6].isoformat() if trade[6] else None
                            }
                
                total_trades = len(trades)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                avg_trade_value = total_value / total_trades if total_trades > 0 else 0.0
                
                # Get trade distribution by strategy
                strategy_stats = {}
                for trade in trades:
                    strategy = trade[7] or 'Unknown'
                    pnl = float(trade[4] or 0)
                    if strategy not in strategy_stats:
                        strategy_stats[strategy] = {'count': 0, 'total_pnl': 0.0}
                    strategy_stats[strategy]['count'] += 1
                    strategy_stats[strategy]['total_pnl'] += pnl
                
                return {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": win_rate,
                    "avg_trade_value": avg_trade_value,
                    "best_trade": best_trade,
                    "worst_trade": worst_trade,
                    "strategy_stats": strategy_stats,
                    "recent_trades": [
                        {
                            'symbol': trade[0],
                            'action': trade[1],
                            'quantity': trade[2],
                            'price': trade[3],
                            'pnl': float(trade[4] or 0),
                            'timestamp': trade[6].isoformat() if trade[6] else None,
                            'strategy': trade[7]
                        }
                        for trade in trades[:10]  # Last 10 trades
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting trade analysis: {e}")
            return {"error": str(e)}
    
    async def get_strategy_comparison(self) -> Dict[str, Any]:
        """Get strategy comparison data"""
        try:
            # Connect to database
            engine = get_database_connection()
            if not engine:
                return {"error": "Database connection failed"}
            
            with engine.connect() as conn:
                # Get strategy comparison data
                result = conn.execute(text("""
                    SELECT 
                        strategy,
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        SUM(value) as total_volume,
                        AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                        AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
                    FROM trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY strategy
                    ORDER BY total_pnl DESC
                """))
                
                strategies = []
                for row in result:
                    total_trades = row[1]
                    winning_trades = row[2]
                    losing_trades = row[3]
                    total_pnl = float(row[4] or 0)
                    avg_pnl = float(row[5] or 0)
                    best_trade = float(row[6] or 0)
                    worst_trade = float(row[7] or 0)
                    total_volume = float(row[8] or 0)
                    avg_win = float(row[9] or 0)
                    avg_loss = float(row[10] or 0)
                    
                    # Calculate win rate
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                    
                    # Calculate profit factor
                    total_wins = winning_trades * avg_win if avg_win > 0 else 0
                    total_losses = abs(losing_trades * avg_loss) if avg_loss < 0 else 0
                    profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
                    
                    strategy_data = {
                        'strategy': row[0] or 'Unknown',
                        'total_trades': total_trades,
                        'winning_trades': winning_trades,
                        'losing_trades': losing_trades,
                        'win_rate': win_rate,
                        'total_pnl': total_pnl,
                        'avg_pnl': avg_pnl,
                        'best_trade': best_trade,
                        'worst_trade': worst_trade,
                        'total_volume': total_volume,
                        'avg_win': avg_win,
                        'avg_loss': avg_loss,
                        'profit_factor': profit_factor
                    }
                    strategies.append(strategy_data)
                
                if not strategies:
                    return {
                        "strategies": [],
                        "message": "No strategy data available for comparison"
                    }
                
                # Calculate overall statistics
                total_trades = sum(s['total_trades'] for s in strategies)
                total_pnl = sum(s['total_pnl'] for s in strategies)
                avg_win_rate = sum(s['win_rate'] for s in strategies) / len(strategies) if strategies else 0
                
                return {
                    "strategies": strategies,
                    "summary": {
                        "total_strategies": len(strategies),
                        "total_trades": total_trades,
                        "total_pnl": total_pnl,
                        "avg_win_rate": avg_win_rate
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting strategy comparison: {e}")
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "backtest_api": "unknown",
                "redis": "unknown",
                "database": "unknown"
            },
            "performance": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0
            },
            "cache": {
                "hit_rate": 0.0,
                "memory_usage": "N/A",
                "keys_count": 0
            }
        }
        
        # Check backtest API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.backtest_api_url}/health")
                status["services"]["backtest_api"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            status["services"]["backtest_api"] = "error"
            logger.error(f"Error checking backtest API: {e}")
        
        # Check Redis
        if redis_client:
            try:
                redis_client.ping()
                status["services"]["redis"] = "healthy"
                cache_stats = redis_client.info("memory")
                status["cache"]["memory_usage"] = cache_stats.get("used_memory_human", "N/A")
                status["cache"]["keys_count"] = redis_client.dbsize()
            except Exception as e:
                status["services"]["redis"] = "error"
                logger.error(f"Error checking Redis: {e}")
        else:
            status["services"]["redis"] = "disconnected"
        
        return status

# Initialize dashboard manager
dashboard_manager = UnifiedTradingDashboard()

# Add paper trading imports and models
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import asyncio
import httpx
from datetime import datetime, timedelta
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import time
import subprocess
import threading
import psutil

# Paper Trading Models
class PaperTradingConfig(BaseModel):
    """Paper trading configuration"""
    initial_capital: float = 100000.0
    max_position_size: float = 0.05
    max_risk_per_trade: float = 0.01
    trading_interval: int = 60
    strategies: List[str] = ["RiskFirst", "MarketRegimeAdaptive", "MultiTimeframe"]
    symbols: List[str] = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    enable_alerts: bool = True
    performance_tracking: bool = True

class PaperTradingStatus(BaseModel):
    """Paper trading status"""
    is_running: bool = False
    start_time: Optional[datetime] = None
    total_trades: int = 0
    total_pnl: float = 0.0
    portfolio_value: float = 0.0
    active_strategies: List[str] = []
    last_trade: Optional[Dict] = None

# Paper Trading State
paper_trading_status = PaperTradingStatus()
paper_trading_config = PaperTradingConfig()
paper_trading_process = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unified-trading-dashboard"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "unified-trading-dashboard"}

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/trading", response_class=HTMLResponse)
async def trading_dashboard(request: Request):
    """Trading dashboard page"""
    return templates.TemplateResponse("trading.html", {"request": request})

@app.get("/performance", response_class=HTMLResponse)
async def performance_dashboard(request: Request):
    """Performance dashboard page"""
    return templates.TemplateResponse("performance.html", {"request": request})

@app.get("/health-dashboard", response_class=HTMLResponse)
async def health_dashboard(request: Request):
    """Health dashboard page"""
    return templates.TemplateResponse("health.html", {"request": request})

@app.get("/paper-trading", response_class=HTMLResponse)
async def paper_trading_dashboard(request: Request):
    """Paper trading dashboard page"""
    return templates.TemplateResponse("paper_trading.html", {"request": request})

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    return await dashboard_manager.get_performance_metrics()

@app.get("/api/health/status")
async def get_health_status():
    """Get health status with Redis metrics"""
    return await dashboard_manager.get_health_status()

@app.get("/api/health/metrics")
async def get_system_metrics():
    """Get system metrics from Redis"""
    metrics = {}
    if redis_client:
        try:
            cache_stats = redis_client.info("memory")
            metrics["cache_memory"] = cache_stats.get("used_memory_human", "N/A")
            metrics["cache_keys"] = redis_client.dbsize()
            metrics["cache_hit_rate"] = 0.0  # Would need to track this
            metrics["timestamp"] = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            metrics["error"] = str(e)
    else:
        metrics["error"] = "Redis not connected"
    
    return metrics

@app.get("/api/recent-runs")
async def get_recent_runs():
    """Get recent backtest runs"""
    return await dashboard_manager.get_recent_runs()

@app.get("/api/performance-metrics")
async def get_performance_metrics_detailed():
    """Get detailed performance metrics"""
    return await dashboard_manager.get_performance_metrics_detailed()

@app.get("/api/risk-analysis")
async def get_risk_analysis():
    """Get risk analysis data"""
    return await dashboard_manager.get_risk_analysis()

@app.get("/api/trade-analysis")
async def get_trade_analysis():
    """Get trade analysis data"""
    return await dashboard_manager.get_trade_analysis()

@app.get("/api/strategy-comparison")
async def get_strategy_comparison():
    """Get strategy comparison data"""
    return await dashboard_manager.get_strategy_comparison()

@app.get("/api/system-status")
async def get_system_status():
    """Get comprehensive system status"""
    return await dashboard_manager.get_system_status()

# Add strategy API endpoints
@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API routing"""
    return {"message": "API routing works", "status": "success"}

@app.get("/api/strategies/")
async def get_strategies():
    """Get all available strategies organized by category"""
    # Simple version that returns hardcoded data
    return {
        "categories": {
            "basic": {
                "name": "basic",
                "strategies": [
                    'BollingerBandsStrategy', 'RSIStrategy', 'MACDStrategy', 'SMACrossoverStrategy',
                    'MomentumStrategy', 'MeanReversionStrategy', 'VolatilityBreakoutStrategy',
                    'VWAPStrategy', 'IchimokuStrategy', 'AdaptiveMomentumStrategy'
                ],
                "count": 10
            },
            "options": {
                "name": "options",
                "strategies": [
                    'GreeksEnhancedStrategy', 'IronCondorStrategy', 'EnhancedIronCondorStrategy',
                    'CashSecuredPutStrategy', 'CoveredCallStrategy', 'CalendarSpreadStrategy',
                    'ButterflySpreadStrategy', 'VolatilityStrategy', 'EarningsStrategy'
                ],
                "count": 9
            },
            "advanced": {
                "name": "advanced",
                "strategies": [
                    'WinningEnsembleStrategy', 'TrailingStopStrategy', 'FibonacciStrategy', 'NeuralNetworkStrategy',
                    'QuantumMomentumStrategy', 'RegimeSwitchingStrategy', 'KalmanFilterStrategy',
                    'MLEnsembleStrategy', 'EnhancedDayTradingStrategy'
                ],
                "count": 9
            },
            "new": {
                "name": "new",
                "strategies": [
                    'RiskFirstStrategy', 'MarketRegimeAdaptiveStrategy', 'MultiTimeframeStrategy'
                ],
                "count": 3
            }
        },
        "all_strategies": [
            'BollingerBandsStrategy', 'RSIStrategy', 'MACDStrategy', 'SMACrossoverStrategy',
            'MomentumStrategy', 'MeanReversionStrategy', 'VolatilityBreakoutStrategy',
            'VWAPStrategy', 'IchimokuStrategy', 'AdaptiveMomentumStrategy',
            'GreeksEnhancedStrategy', 'IronCondorStrategy', 'EnhancedIronCondorStrategy',
            'CashSecuredPutStrategy', 'CoveredCallStrategy', 'CalendarSpreadStrategy',
            'ButterflySpreadStrategy', 'VolatilityStrategy', 'EarningsStrategy',
            'WinningEnsembleStrategy', 'TrailingStopStrategy', 'FibonacciStrategy', 'NeuralNetworkStrategy',
            'QuantumMomentumStrategy', 'RegimeSwitchingStrategy', 'KalmanFilterStrategy',
            'MLEnsembleStrategy', 'EnhancedDayTradingStrategy',
            'RiskFirstStrategy', 'MarketRegimeAdaptiveStrategy', 'MultiTimeframeStrategy'
        ],
        "total_count": 31
    }

@app.get("/api/strategies/categories/{category}")
async def get_strategies_by_category(category: str):
    """Get strategies by category"""
    # Simple version that returns hardcoded data
    strategies_map = {
        "basic": [
            'BollingerBandsStrategy', 'RSIStrategy', 'MACDStrategy', 'SMACrossoverStrategy',
            'MomentumStrategy', 'MeanReversionStrategy', 'VolatilityBreakoutStrategy',
            'VWAPStrategy', 'IchimokuStrategy', 'AdaptiveMomentumStrategy'
        ],
        "options": [
            'GreeksEnhancedStrategy', 'IronCondorStrategy', 'EnhancedIronCondorStrategy',
            'CashSecuredPutStrategy', 'CoveredCallStrategy', 'CalendarSpreadStrategy',
            'ButterflySpreadStrategy', 'VolatilityStrategy', 'EarningsStrategy'
        ],
        "advanced": [
            'WinningEnsembleStrategy', 'TrailingStopStrategy', 'FibonacciStrategy', 'NeuralNetworkStrategy',
            'QuantumMomentumStrategy', 'RegimeSwitchingStrategy', 'KalmanFilterStrategy',
            'MLEnsembleStrategy', 'EnhancedDayTradingStrategy'
        ],
        "new": [
            'RiskFirstStrategy', 'MarketRegimeAdaptiveStrategy', 'MultiTimeframeStrategy'
        ]
    }
    
    strategies = strategies_map.get(category, [])
    return {
        "category": category,
        "strategies": sorted(strategies),
        "count": len(strategies)
    }

# Database-driven API endpoints
@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Get real portfolio summary from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get portfolio summary
            result = conn.execute(text("""
                SELECT 
                    COALESCE(SUM(quantity * current_price), 0) as total_value,
                    COALESCE(SUM(cash), 0) as total_cash,
                    COALESCE(SUM(unrealized_pnl), 0) as total_pnl,
                    COUNT(*) as num_positions
                FROM portfolio_positions
                WHERE active = true
            """))
            
            row = result.fetchone()
            if row:
                return {
                    "total_value": float(row.total_value or 0),
                    "total_cash": float(row.total_cash or 0),
                    "total_pnl": float(row.total_pnl or 0),
                    "num_positions": int(row.num_positions or 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "total_value": 0.0,
                    "total_cash": 0.0,
                    "total_pnl": 0.0,
                    "num_positions": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/trades/recent")
async def get_recent_trades():
    """Get recent trades from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent trades
            result = conn.execute(text("""
                SELECT 
                    bt.timestamp,
                    bt.symbol,
                    bt.action,
                    bt.quantity,
                    bt.price,
                    bt.value,
                    bt.pnl,
                    bt.confidence,
                    br.strategy_name,
                    br.backtest_name
                FROM backtest_trades bt
                JOIN backtest_runs br ON bt.run_id = br.run_id
                WHERE bt.symbol IS NOT NULL AND bt.symbol != '' AND LENGTH(TRIM(bt.symbol)) > 0
                ORDER BY bt.timestamp DESC
                LIMIT 50
            """))
            
            trades = []
            for row in result:
                trades.append({
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "symbol": row.symbol,
                    "action": row.action,
                    "quantity": int(row.quantity or 0),
                    "price": float(row.price or 0),
                    "value": float(row.value or 0),
                    "pnl": float(row.pnl or 0),
                    "confidence": float(row.confidence or 0),
                    "strategy": row.strategy_name,
                    "backtest": row.backtest_name
                })
            
            return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/strategy/events")
async def get_strategy_events():
    """Get recent strategy events from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get strategy events (if table exists)
            try:
                result = conn.execute(text("""
                    SELECT 
                        timestamp,
                        strategy_name,
                        symbol,
                        event_type,
                        action,
                        confidence,
                        metadata
                    FROM strategy_events
                    ORDER BY timestamp DESC
                    LIMIT 100
                """))
                
                events = []
                for row in result:
                    events.append({
                        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                        "strategy": row.strategy_name,
                        "symbol": row.symbol,
                        "event_type": row.event_type,
                        "action": row.action,
                        "confidence": float(row.confidence or 0),
                        "metadata": row.metadata if row.metadata else {}
                    })
                
                return {"events": events, "count": len(events)}
            except Exception as table_error:
                logger.warning(f"Strategy events table not found: {table_error}")
                return {"events": [], "count": 0, "note": "Strategy events table not available"}
    except Exception as e:
        logger.error(f"Error getting strategy events: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/positions/active")
async def get_active_positions():
    """Get active portfolio positions from database"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get active positions
            result = conn.execute(text("""
                SELECT 
                    symbol,
                    quantity,
                    avg_price,
                    current_price,
                    market_value,
                    unrealized_pnl,
                    unrealized_pnl_percent,
                    entry_date,
                    strategy,
                    holding_days
                FROM portfolio_positions
                WHERE active = true
                ORDER BY unrealized_pnl DESC
            """))
            
            positions = []
            for row in result:
                positions.append({
                    "symbol": row.symbol,
                    "quantity": int(row.quantity or 0),
                    "avg_price": float(row.avg_price or 0),
                    "current_price": float(row.current_price or 0),
                    "market_value": float(row.market_value or 0),
                    "unrealized_pnl": float(row.unrealized_pnl or 0),
                    "unrealized_pnl_percent": float(row.unrealized_pnl_percent or 0),
                    "entry_date": row.entry_date.isoformat() if row.entry_date else None,
                    "strategy": row.strategy,
                    "holding_days": int(row.holding_days or 0)
                })
            
            return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Error getting active positions: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Order Management Endpoints
@app.post("/api/orders")
async def create_order(order_data: dict):
    """Create a new trading order"""
    try:
        # Validate required fields
        required_fields = ['symbol', 'side', 'quantity', 'order_type']
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate order type and price requirements
        if order_data['order_type'] == 'LIMIT' and not order_data.get('price'):
            raise HTTPException(status_code=400, detail="Price is required for limit orders")
        
        # Generate order ID
        order_id = f"order_{int(time.time())}_{order_data['symbol']}"
        
        # Store order in database
        engine = get_database_connection()
        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO orders (
                        order_id, timestamp, symbol, action, quantity, price, order_type, 
                        status, created_at
                    ) VALUES (
                        :order_id, NOW(), :symbol, :action, :quantity, :price, :order_type,
                        :status, NOW()
                    )
                """), {
                    'order_id': order_id,
                    'symbol': order_data['symbol'],
                    'action': order_data['side'],
                    'quantity': order_data['quantity'],
                    'price': order_data.get('price') or 0.0,
                    'order_type': order_data['order_type'],
                    'status': 'pending'
                })
                conn.commit()
        
        # Forward to order service if available
        try:
            order_service_url = os.getenv("ORDER_SERVICE_URL", "http://order-service:11106")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{order_service_url}/api/v1/orders", json=order_data)
                if response.status_code == 200:
                    logger.info(f"Order forwarded to order service: {order_id}")
        except Exception as e:
            logger.warning(f"Could not forward order to order service: {e}")
        
        return {
            "order_id": order_id,
            "status": "pending",
            "message": "Order created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.get("/api/orders")
async def get_orders():
    """Get recent orders"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent orders
            result = conn.execute(text("""
                SELECT 
                    order_id,
                    symbol,
                    action as side,
                    quantity,
                    price,
                    order_type,
                    status,
                    created_at,
                    updated_at as filled_at,
                    price as filled_price,
                    quantity as filled_quantity
                FROM orders
                ORDER BY created_at DESC
                LIMIT 50
            """))
            
            orders = []
            for row in result:
                orders.append({
                    "order_id": row.order_id,
                    "symbol": row.symbol,
                    "side": row.side,
                    "quantity": int(row.quantity or 0),
                    "price": float(row.price or 0) if row.price else None,
                    "order_type": row.order_type,
                    "time_in_force": "DAY",  # Default since column doesn't exist
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "filled_at": row.filled_at.isoformat() if row.filled_at else None,
                    "filled_price": float(row.filled_price or 0) if row.filled_price else None,
                    "filled_quantity": int(row.filled_quantity or 0) if row.filled_quantity else None
                })
            
            return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get specific order details"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    order_id,
                    symbol,
                    action as side,
                    quantity,
                    price,
                    order_type,
                    status,
                    created_at,
                    updated_at as filled_at,
                    price as filled_price,
                    quantity as filled_quantity
                FROM orders
                WHERE order_id = :order_id
            """), {'order_id': order_id})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Order not found")
            
            return {
                "order_id": row.order_id,
                "symbol": row.symbol,
                "side": row.side,
                "quantity": int(row.quantity or 0),
                "price": float(row.price or 0) if row.price else None,
                "order_type": row.order_type,
                "time_in_force": row.time_in_force,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "filled_at": row.filled_at.isoformat() if row.filled_at else None,
                "filled_price": float(row.filled_price or 0) if row.filled_price else None,
                "filled_quantity": int(row.filled_quantity or 0) if row.filled_quantity else None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/api/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Check if order exists and is cancellable
            result = conn.execute(text("""
                SELECT status FROM orders WHERE order_id = :order_id
            """), {'order_id': order_id})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Order not found")
            
            if row.status in ['filled', 'cancelled']:
                raise HTTPException(status_code=400, detail=f"Order cannot be cancelled in status: {row.status}")
            
            # Update order status
            conn.execute(text("""
                UPDATE orders SET status = 'cancelled' WHERE order_id = :order_id
            """), {'order_id': order_id})
            conn.commit()
            
            return {"message": "Order cancelled successfully", "order_id": order_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

# ============================================================================
# BACKTEST API ENDPOINTS
# ============================================================================

class BacktestRequest(BaseModel):
    """Backtest request model"""
    symbols: List[str]
    strategies: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    risk_profile: str = "moderate"
    use_llm: bool = False
    parallel_execution: bool = True

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run a backtest with the specified parameters"""
    try:
        # Call the strategy service directly instead of importing locally
        job_id = f"backtest_{int(time.time())}"
        
        # Make HTTP request to strategy service
        import httpx
        async with httpx.AsyncClient() as client:
            strategy_service_url = "http://strategy-service:80/api/backtest/run"
            response = await client.post(
                strategy_service_url,
                json=request.dict(),
                timeout=300.0  # 5 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"🚀 Real backtest completed successfully")
                
                # Store results in Redis for later retrieval
                if redis_client:
                    redis_client.setex(f"backtest_results:{job_id}", 3600, json.dumps({
                        "status": "completed",
                        "results": result.get("results", []),
                        "request": request.dict()
                    }))
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "message": "Real backtest completed successfully"
                }
            else:
                logger.error(f"Strategy service returned error: {response.status_code} - {response.text}")
                raise Exception(f"Strategy service error: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error running real backtest: {e}")
        # Fallback to mock data if real backtest fails
        logger.warning("Falling back to mock data due to real backtest failure")
        
        job_id = f"backtest_{int(time.time())}"
        
        # Simulate backtest results as fallback
        results = []
        for strategy in request.strategies:
            import random
            total_return = random.uniform(-0.2, 0.4)  # -20% to +40%
            sharpe_ratio = random.uniform(-1.0, 2.0)
            max_drawdown = random.uniform(0.05, 0.25)  # 5% to 25%
            win_rate = random.uniform(0.4, 0.7)  # 40% to 70%
            total_trades = random.randint(10, 100)
            profit_factor = random.uniform(0.8, 1.5)
            
            results.append({
                "name": strategy,
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "profit_factor": profit_factor
            })
        
        # Store results in Redis for later retrieval
        if redis_client:
            redis_client.setex(f"backtest_results:{job_id}", 3600, json.dumps({
                "status": "completed",
                "results": results,
                "request": request.dict()
            }))
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Backtest completed (using fallback data)"
        }

@app.get("/api/backtest/status/{job_id}")
async def get_backtest_status(job_id: str):
    """Get the status of a backtest job"""
    try:
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        result_data = redis_client.get(f"backtest_results:{job_id}")
        if not result_data:
            return {"status": "not_found", "message": "Job not found"}
        
        result = json.loads(result_data)
        return result
        
    except Exception as e:
        logger.error(f"Error getting backtest status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backtest status: {str(e)}")

@app.get("/api/backtest/results")
async def get_backtest_results():
    """Get recent backtest results"""
    try:
        if not redis_client:
            return {"results": []}
        
        # Get all backtest results from Redis
        results = []
        for key in redis_client.scan_iter("backtest_results:*"):
            result_data = redis_client.get(key)
            if result_data:
                result = json.loads(result_data)
                if result.get("status") == "completed":
                    results.extend(result.get("results", []))
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return {"results": [], "error": str(e)}

@app.get("/api/market-data/current/{symbol}")
async def get_current_price(symbol: str):
    """Proxy endpoint to get current price from market data service"""
    try:
        logger.info(f"Attempting to get current price for {symbol} from {MARKET_DATA_URL}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{MARKET_DATA_URL}/market-data/current/{symbol}"
            logger.info(f"Making request to: {url}")
            response = await client.get(url)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Market data service returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Market data service unavailable: {response.text}")
    except Exception as e:
        import traceback
        logger.error(f"Error getting current price for {symbol}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching price: {str(e)}")

# Paper Trading Endpoints
@app.post("/api/paper-trading/start")
async def start_paper_trading(config: PaperTradingConfig):
    """Start paper trading system"""
    global paper_trading_status, paper_trading_config, paper_trading_process
    
    try:
        if paper_trading_status.is_running:
            return {"status": "error", "message": "Paper trading is already running"}
        
        # Update configuration
        paper_trading_config = config
        
        # Start paper trading process
        paper_trading_status.is_running = True
        paper_trading_status.start_time = datetime.now()
        paper_trading_status.active_strategies = config.strategies
        paper_trading_status.portfolio_value = config.initial_capital
        
        # Start paper trading in background
        def run_paper_trading():
            try:
                # Create config file for the paper trading script
                config_file = "/tmp/paper_trading_config.json"
                with open(config_file, 'w') as f:
                    json.dump(config.dict(), f)
                
                       # Start the RISK-MANAGED paper trading setup script with config
                       subprocess.run([
                           "python3", "scripts/setup_paper_trading.py", config_file
                       ], check=True)
            except Exception as e:
                logger.error(f"Paper trading error: {e}")
                paper_trading_status.is_running = False
        
        # Start in background thread
        paper_trading_thread = threading.Thread(target=run_paper_trading, daemon=True)
        paper_trading_thread.start()
        
        logger.info("🚀 Paper trading started")
        return {
            "status": "success",
            "message": "Paper trading started successfully",
            "config": config.dict(),
            "status_info": paper_trading_status.dict()
        }
        
    except Exception as e:
        logger.error(f"Error starting paper trading: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/paper-trading/stop")
async def stop_paper_trading():
    """Stop paper trading system"""
    global paper_trading_status, paper_trading_process
    
    try:
        if not paper_trading_status.is_running:
            return {"status": "error", "message": "Paper trading is not running"}
        
        # Stop paper trading
        paper_trading_status.is_running = False
        
        # Kill any running paper trading processes
        if paper_trading_process:
            try:
                paper_trading_process.terminate()
                paper_trading_process.wait(timeout=5)
            except:
                paper_trading_process.kill()
            paper_trading_process = None
        
        # Kill any paper trading related processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any('paper_trading' in cmd for cmd in proc.info['cmdline']):
                    proc.terminate()
            except:
                pass
        
        logger.info("⏹️ Paper trading stopped")
        return {
            "status": "success",
            "message": "Paper trading stopped successfully"
        }
        
    except Exception as e:
        logger.error(f"Error stopping paper trading: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/paper-trading/status")
async def get_paper_trading_status():
    """Get paper trading status"""
    return {
        "status": "success",
        "data": paper_trading_status.dict()
    }

@app.get("/api/paper-trading/config")
async def get_paper_trading_config():
    """Get paper trading configuration"""
    return {
        "status": "success",
        "data": paper_trading_config.dict()
    }

@app.post("/api/paper-trading/config")
async def update_paper_trading_config(config: PaperTradingConfig):
    """Update paper trading configuration"""
    global paper_trading_config
    
    try:
        paper_trading_config = config
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "data": paper_trading_config.dict()
        }
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/paper-trading/trades")
async def get_paper_trading_trades():
    """Get recent paper trading trades from database"""
    try:
        # Connect to database
        engine = get_database_connection()
        if not engine:
            return {"status": "error", "message": "Database connection failed"}
        
        with engine.connect() as conn:
            # Get recent trades from database
            result = conn.execute(text("""
                SELECT symbol, action, quantity, price, realized_pnl as pnl, strategy, timestamp, premium as value
                FROM paper_trades 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                ORDER BY timestamp DESC
                LIMIT 20
            """))
            
            trades = []
            for row in result:
                trades.append({
                    "symbol": row[0],
                    "action": row[1],
                    "quantity": row[2],
                    "price": float(row[3] or 0),
                    "strategy": row[5] or 'Unknown',
                    "pnl": float(row[4] or 0),
                    "timestamp": row[6].isoformat() if row[6] else None,
                    "value": float(row[7] or 0)
                })
            
            return {
                "status": "success",
                "data": trades
            }
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/paper-trading/performance")
async def get_paper_trading_performance():
    """Get paper trading performance metrics from database"""
    try:
        # Connect to database
        engine = get_database_connection()
        if not engine:
            return {"status": "error", "message": "Database connection failed"}
        
        with engine.connect() as conn:
            # Get performance data from paper_trades table
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(realized_pnl) as total_pnl,
                    AVG(realized_pnl) as avg_pnl,
                    MAX(realized_pnl) as best_trade,
                    MIN(realized_pnl) as worst_trade,
                    SUM(premium) as total_volume
                FROM paper_trades 
                WHERE timestamp >= NOW() - INTERVAL '30 days'
            """))
            performance_data = result.fetchone()
            
            if not performance_data or performance_data[0] == 0:
                # No recent trades, return default values
                performance = {
                    "total_trades": 0,
                    "total_pnl": 0.0,
                    "portfolio_value": paper_trading_config.initial_capital,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "strategy_performance": {}
                }
            else:
                total_trades = performance_data[0]
                winning_trades = performance_data[1]
                losing_trades = performance_data[2]
                total_pnl = float(performance_data[3] or 0)
                avg_pnl = float(performance_data[4] or 0)
                best_trade = float(performance_data[5] or 0)
                worst_trade = float(performance_data[6] or 0)
                total_volume = float(performance_data[7] or 0)
                
                # Calculate win rate
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                # Calculate portfolio value (initial capital + total P&L)
                portfolio_value = paper_trading_config.initial_capital + total_pnl
                
                # Get strategy performance
                strategy_result = conn.execute(text("""
                    SELECT strategy, 
                           COUNT(*) as trades,
                           SUM(realized_pnl) as total_pnl,
                           AVG(realized_pnl) as avg_pnl,
                           SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins
                    FROM paper_trades 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY strategy
                    ORDER BY total_pnl DESC
                """))
                
                strategy_performance = {}
                for row in strategy_result:
                    strategy_name = row[0] or 'Unknown'
                    trades = row[1]
                    strategy_pnl = float(row[2] or 0)
                    strategy_avg_pnl = float(row[3] or 0)
                    wins = row[4]
                    strategy_win_rate = (wins / trades * 100) if trades > 0 else 0.0
                    
                    strategy_performance[strategy_name] = {
                        "trades": trades,
                        "win_rate": strategy_win_rate,
                        "pnl": strategy_pnl,
                        "avg_pnl": strategy_avg_pnl
                    }
                
                # Calculate Sharpe ratio (simplified)
                sharpe_ratio = (avg_pnl / (abs(worst_trade) + 0.001)) if worst_trade < 0 else 0.0
                
                # Calculate max drawdown (simplified)
                max_drawdown = abs(worst_trade) / portfolio_value if portfolio_value > 0 else 0.0
                
                performance = {
                    "total_trades": total_trades,
                    "total_pnl": total_pnl,
                    "portfolio_value": portfolio_value,
                    "win_rate": win_rate,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "strategy_performance": strategy_performance
                }
            
            return {
                "status": "success",
                "data": performance
            }
            
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return {"status": "error", "message": str(e)}

# RAG Chat Endpoints
@app.post("/api/rag-chat/ask")
async def ask_rag_chat(request: ChatRequest):
    """Ask a question to the RAG chat"""
    try:
        start_time = time.time()
        response = await rag_chat.process_question(request.question, request.context)
        response.processing_time = time.time() - start_time
        return response.dict()
    except Exception as e:
        logger.error(f"Error processing RAG chat question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process RAG chat question: {str(e)}")

@app.get("/api/rag-chat/health")
async def rag_chat_health():
    """Health check for RAG chat service"""
    return {"status": "healthy", "service": "kubernetes-rag-chat"}

@app.post("/api/rag/callback/{request_id}")
async def handle_rag_callback(request_id: str, request: Dict[str, Any]):
    """Handle callback from external LLM proxy when request completes"""
    try:
        logger.info(f"Received callback for RAG request {request_id}: {request}")
        
        # Store the completed request result (in a real implementation, you'd use a database)
        # For now, we'll just log it
        if request.get("status") == "completed" and request.get("result"):
            logger.info(f"RAG request {request_id} completed successfully")
            # Here you could store the result in a database or cache
        elif request.get("status") == "failed":
            logger.error(f"RAG request {request_id} failed: {request.get('error')}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling callback for RAG request {request_id}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/rag/status/{request_id}")
async def check_rag_request_status(request_id: str):
    """Check the status of a RAG request and display the result if completed"""
    try:
        # In a real implementation, you'd check a database or cache
        # For now, return a placeholder response
        return {
            "request_id": request_id,
            "status": "processing",
            "message": "Request is being processed by the AI service"
        }
    except Exception as e:
        logger.error(f"Error checking RAG request status: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80) 