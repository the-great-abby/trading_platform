#!/usr/bin/env python3
"""
Kubernetes RAG Chat Service - Specialized chat for Kubernetes questions
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import hashlib
from pathlib import Path
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kubernetes RAG Chat Service", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://host.docker.internal:12001")
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:11006")
K8S_DOCS_PATH = os.getenv("K8S_DOCS_PATH", "/app/docs")

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
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.k8s_docs_path = K8S_DOCS_PATH
        
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
            # Search for relevant Kubernetes knowledge
            k8s_knowledge = await self._search_k8s_knowledge(question)
            
            # Search vector storage for additional context
            vector_results = await self._search_vector_storage(question)
            
            # Build context from all sources
            context_str = self._build_context(question, k8s_knowledge, vector_results, context)
            
            # Generate AI response
            ai_response = await self._generate_ai_response(question, context_str)
            
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
                    "relevance": 0.85
                })
        
        return relevant_knowledge[:5]  # Return top 5 most relevant
    
    async def _search_vector_storage(self, question: str) -> List[Dict[str, Any]]:
        """Search vector storage for additional context"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.vector_storage_url}/api/search/similar"
                params = {
                    "query": question,
                    "top_k": 3,
                    "vector_type": "kubernetes"
                }
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        results = await response.json()
                        return [
                            {
                                "type": "vector_search",
                                "content": result.get("content", ""),
                                "relevance": result.get("similarity", 0.5)
                            }
                            for result in results
                        ]
                    else:
                        logger.warning(f"Vector storage search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching vector storage: {e}")
            return []
    
    def _build_context(self, question: str, k8s_knowledge: List[Dict], 
                      vector_results: List[Dict], user_context: Optional[str]) -> str:
        """Build comprehensive context for AI response"""
        context_parts = []
        
        # Add Kubernetes knowledge
        if k8s_knowledge:
            context_parts.append("## Kubernetes Knowledge:")
            for knowledge in k8s_knowledge:
                context_parts.append(f"- {knowledge['content']}")
        
        # Add vector search results
        if vector_results:
            context_parts.append("\n## Related Information:")
            for result in vector_results:
                context_parts.append(f"- {result['content']}")
        
        # Add user context
        if user_context:
            context_parts.append(f"\n## User Context:\n{user_context}")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, question: str, context: str) -> Dict[str, Any]:
        """Generate AI response using GPT-OSS model with high priority"""
        try:
            # Build prompt for Kubernetes expert
            prompt = f"""You are an expert Kubernetes administrator and instructor. Answer the following Kubernetes question based on the provided context.

Question: {question}

Context:
{context}

Please provide a comprehensive, practical answer that includes:
1. Clear explanation of the concept or command
2. When and why to use it
3. Practical examples when relevant
4. Common pitfalls or troubleshooting tips
5. Best practices

Answer:"""
            
            # Generate a unique request ID for tracking
            import uuid
            request_id = str(uuid.uuid4())
            
            # Use the /api/generate endpoint which works better
            llm_request = {
                "model": "gpt-oss:20b",
                "prompt": prompt,
                "stream": False,
                "priority": 40,  # Highest priority (40 = highest, 30 = high, 20 = normal, 10 = low)
                "timeout_seconds": 300,  # 5 minutes for the LLM request
                "request_id": request_id,
                "callback_url": f"http://kubernetes-rag-chat:8000/callback/{request_id}",
                "callback_method": "POST"
            }
            
            # Log the request for debugging
            logger.info(f"Sending LLM request with priority {llm_request['priority']}: {llm_request}")
            
            # Use the generate endpoint for external LLM proxy
            url = f"{self.llm_proxy_url}/api/generate"
            
            # Create a session with longer timeout and retry logic
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, keepalive_timeout=60)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                # Submit the request
                async with session.post(url, json=llm_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Check for the correct response format
                        if "request_id" in result and result.get("status") == "queued":
                            # This is an async request, we need to poll for the result
                            actual_request_id = result["request_id"]
                            logger.info(f"Submitted request {actual_request_id} to LLM proxy, now polling for completion")
                            
                                                    # Return immediately with status URL for async processing
                        status_url = f"/status/{actual_request_id}"
                        
                        return {
                            "answer": f"Your request is being processed. This may take a few minutes due to high demand. You can check the status of your request at: <a href='{status_url}' target='_blank' style='color: #007bff; text-decoration: underline;'>{status_url}</a>",
                            "model": "gpt-oss:20b",
                            "request_id": actual_request_id,
                            "status_url": status_url
                        }
                        else:
                            logger.error(f"Unexpected LLM response format: {result}")
                            return {
                                "answer": "I'm having trouble processing the AI response. Please try again later.",
                                "model": "gpt-oss:20b"
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM request failed with status {response.status}: {error_text}")
                        return {
                            "answer": "I'm having trouble connecting to the AI service. Please try again later.",
                            "model": "gpt-oss:20b"
                        }
                        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "answer": f"I encountered an error while generating a response: {str(e)}",
                "model": "gpt-oss:20b"
            }
    
    async def _poll_for_completion(self, session: aiohttp.ClientSession, request_id: str, 
                                  max_wait_time: int = 300, poll_interval: int = 5) -> Optional[Dict[str, Any]]:
        """Poll the status endpoint until the request completes"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status_url = f"{self.llm_proxy_url}/api/status/{request_id}"
                
                async with session.get(status_url, timeout=30) as response:
                    if response.status == 200:
                        status_result = await response.json()
                        current_status = status_result.get("status", "unknown")
                        
                        logger.info(f"Request {request_id} status: {current_status}")
                        
                        if current_status == "completed":
                            # Request completed successfully
                            if "result" in status_result:
                                logger.info(f"Request {request_id} completed successfully")
                                return status_result["result"]
                            else:
                                logger.warning(f"Request {request_id} completed but no result found")
                                return None
                        
                        elif current_status == "failed":
                            # Request failed
                            error_msg = status_result.get("error", "Unknown error")
                            logger.error(f"Request {request_id} failed: {error_msg}")
                            return None
                        
                        elif current_status in ["queued", "processing"]:
                            # Still processing, wait and poll again
                            queue_position = status_result.get("queue_position", "Unknown")
                            logger.info(f"Request {request_id} still {current_status}, queue position: {queue_position}")
                            await asyncio.sleep(poll_interval)
                            continue
                        
                        else:
                            # Unknown status
                            logger.warning(f"Unknown status for request {request_id}: {current_status}")
                            await asyncio.sleep(poll_interval)
                            continue
                    
                    else:
                        logger.warning(f"Failed to get status for request {request_id}: {response.status}")
                        await asyncio.sleep(poll_interval)
                        continue
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout getting status for request {request_id}")
                await asyncio.sleep(poll_interval)
                continue
            except Exception as e:
                logger.error(f"Error polling status for request {request_id}: {e}")
                await asyncio.sleep(poll_interval)
                continue
        
        # Timeout reached
        logger.warning(f"Timeout waiting for request {request_id} to complete after {max_wait_time} seconds")
        return None
    
    def _calculate_confidence(self, k8s_knowledge: List[Dict], vector_results: List[Dict]) -> float:
        """Calculate confidence score based on available knowledge"""
        if not k8s_knowledge and not vector_results:
            return 0.3
        
        # Calculate confidence based on relevance scores
        total_relevance = 0.0
        count = 0
        
        for knowledge in k8s_knowledge:
            total_relevance += knowledge.get("relevance", 0.5)
            count += 1
        
        for result in vector_results:
            total_relevance += result.get("relevance", 0.5)
            count += 1
        
        if count > 0:
            return min(1.0, total_relevance / count)
        
        return 0.5

# Initialize RAG chat service
rag_chat = KubernetesRAGChat()

@app.get("/", response_class=HTMLResponse)
async def chat_interface():
    """Serve the chat interface"""
    try:
        with open("templates/chat.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Kubernetes RAG Chat</title></head>
        <body>
            <h1>Kubernetes RAG Chat</h1>
            <p>Chat interface not found. Please check the templates directory.</p>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kubernetes-rag-chat", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat request and return AI response with sources"""
    start_time = time.time()
    
    # Process the question
    response = await rag_chat.process_question(request.question, request.context)
    
    # Add processing time
    response.processing_time = time.time() - start_time
    
    return response

@app.get("/knowledge")
async def get_knowledge():
    """Get available Kubernetes knowledge"""
    return {
        "commands": rag_chat.k8s_knowledge["commands"],
        "concepts": rag_chat.k8s_knowledge["concepts"],
        "troubleshooting": rag_chat.k8s_knowledge["troubleshooting"]
    }

@app.get("/examples")
async def get_examples():
    """Get example Kubernetes questions"""
    return {
        "examples": [
            "How do I check the status of all pods?",
            "What's the difference between a pod and a deployment?",
            "How do I debug a pod that's in CrashLoopBackOff?",
            "How do I scale a deployment to 3 replicas?",
            "How do I create a ConfigMap from a file?",
            "What's the difference between Docker Desktop Kubernetes and production Kubernetes?",
            "How do I port-forward a service?",
            "How do I view logs for a specific pod?",
            "How do I delete a pod?",
            "How do I check resource usage of pods?"
        ]
    }

@app.post("/callback/{request_id}")
async def handle_callback(request_id: str, request: Dict[str, Any]):
    """Handle callback from external LLM proxy when request completes"""
    try:
        logger.info(f"Received callback for request {request_id}: {request}")
        
        # Store the completed request result (in a real implementation, you'd use a database)
        # For now, we'll just log it
        if request.get("status") == "completed" and request.get("result"):
            logger.info(f"Request {request_id} completed successfully")
            # Here you could store the result in a database or cache
        elif request.get("status") == "failed":
            logger.error(f"Request {request_id} failed: {request.get('error')}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling callback for request {request_id}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/status/{request_id}")
async def check_request_status(request_id: str):
    """Check the status of a request and display the result if completed"""
    try:
        # Check the status with the external LLM proxy
        status_url = f"{rag_chat.llm_proxy_url}/api/status/{request_id}"
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(status_url) as response:
                if response.status == 200:
                    status_result = await response.json()
                    
                    # Create a simple HTML page to display the status
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Request Status - {request_id}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .status {{ padding: 20px; border-radius: 5px; margin: 20px 0; }}
                            .queued {{ background-color: #fff3cd; border: 1px solid #ffeaa7; }}
                            .processing {{ background-color: #d1ecf1; border: 1px solid #bee5eb; }}
                            .completed {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
                            .failed {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
                            .answer {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                            .refresh {{ background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                            .refresh:hover {{ background-color: #0056b3; }}
                        </style>
                        <script>
                            function refreshStatus() {{
                                location.reload();
                            }}
                            
                            // Auto-refresh every 30 seconds if still processing
                            function autoRefresh() {{
                                const status = '{status_result.get("status", "unknown")}';
                                if (status === 'queued' || status === 'processing') {{
                                    setTimeout(refreshStatus, 30000);
                                }}
                            }}
                            
                            window.onload = autoRefresh;
                        </script>
                    </head>
                    <body>
                        <h1>Request Status</h1>
                        <p><strong>Request ID:</strong> {request_id}</p>
                        <p><strong>Created:</strong> {status_result.get('created_at', 'Unknown')}</p>
                        
                        <div class="status {status_result.get('status', 'unknown')}">
                            <h2>Status: {status_result.get('status', 'Unknown').upper()}</h2>
                        </div>
                    """
                    
                    if status_result.get("status") == "completed" and status_result.get("result"):
                        answer = status_result["result"].get("response", "No response generated")
                        html_content += f"""
                        <div class="answer">
                            <h3>Answer:</h3>
                            <p>{answer.replace(chr(10), '<br>')}</p>
                        </div>
                        """
                    elif status_result.get("status") == "failed":
                        error = status_result.get("error", "Unknown error")
                        html_content += f"""
                        <div class="answer">
                            <h3>Error:</h3>
                            <p>{error}</p>
                        </div>
                        """
                    elif status_result.get("status") in ["queued", "processing"]:
                        queue_position = status_result.get("queue_position", "Unknown")
                        estimated_wait = status_result.get("estimated_wait_time", "Unknown")
                        html_content += f"""
                        <div class="answer">
                            <p><strong>Queue Position:</strong> {queue_position}</p>
                            <p><strong>Estimated Wait Time:</strong> {estimated_wait} seconds</p>
                            <p>This page will automatically refresh every 30 seconds to check for updates.</p>
                            <button class="refresh" onclick="refreshStatus()">Refresh Now</button>
                        </div>
                        """
                    
                    html_content += """
                    </body>
                    </html>
                    """
                    
                    return HTMLResponse(content=html_content)
                else:
                    return HTMLResponse(content=f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h1>Error</h1>
                        <p>Failed to retrieve status for request {request_id}</p>
                        <p>Status code: {response.status}</p>
                    </body>
                    </html>
                    """)
                    
    except Exception as e:
        logger.error(f"Error checking status for request {request_id}: {e}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>Failed to check status for request {request_id}</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
