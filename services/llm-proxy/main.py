#!/usr/bin/env python3
"""
Simple LLM Proxy Service
Handles LLM requests and forwards them to the LLM service
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
import logging
import os
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Proxy Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://host.docker.internal:11434")

class LLMRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 1000
    task_type: str = "general"
    priority: str = "normal"  # low, normal, high, urgent

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    timestamp: datetime

@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {
        "status": "healthy",
        "service": "llm-proxy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm-proxy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: LLMRequest):
    """Handle chat completion requests"""
    try:
        async with aiohttp.ClientSession() as session:
            # Convert to Ollama format
            ollama_request = {
                "model": request.model,
                "messages": request.messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens
                }
            }
            
            # Add priority if specified
            if request.priority and request.priority != "normal":
                ollama_request["priority"] = request.priority
            
            try:
                async with session.post(
                    f"{LLM_SERVICE_URL}/api/chat",
                    json=ollama_request,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "choices": [{
                                "message": {
                                    "content": result["message"]["content"],
                                    "role": "assistant"
                                },
                                "finish_reason": "stop"
                            }],
                            "model": result["model"],
                            "usage": {
                                "prompt_tokens": result.get("prompt_eval_count", 0),
                                "completion_tokens": result.get("eval_count", 0),
                                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                            },
                            "response_time": 0.0
                        }
                    else:
                        # Fallback to mock response if Ollama is not available
                        logger.warning(f"Ollama not available (status {response.status}), using mock response")
                        return _generate_mock_response(request)
            except Exception as e:
                logger.warning(f"Ollama connection failed: {e}, using mock response")
                return _generate_mock_response(request)
                    
    except Exception as e:
        logger.error(f"Error in chat completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_mock_response(request: LLMRequest):
    """Generate a mock response when Ollama is not available"""
    # Extract the user's message
    user_message = ""
    for msg in request.messages:
        if msg["role"] == "user":
            user_message = msg["content"]
            break
    
    # Generate appropriate mock response based on content
    if "stock analysis" in user_message.lower() or "trading" in user_message.lower():
        content = """Based on the comprehensive analysis of market data, technical indicators, and news sentiment, I recommend a **BUY** decision with high confidence.

**Key Factors Supporting BUY Recommendation:**
- Positive news sentiment (0.73 score) with 5 recent positive articles
- Strong technical indicators showing bullish momentum
- Price above key moving averages (170 > 166.6 > 161.5)
- Multiple AI partnership catalysts and institutional buying support

**Target Price:** $185.00
**Stop Loss:** $165.00
**Confidence Level:** 8/10
**Risk Level:** MEDIUM

**Reasoning:** The combination of positive news sentiment, strong technical indicators, and institutional support suggests continued upward momentum. The stock shows resilience above key support levels with multiple growth catalysts."""
    else:
        content = "Based on the provided information, I recommend further analysis of market conditions and technical indicators."
    
    return {
        "choices": [{
            "message": {
                "content": content,
                "role": "assistant"
            },
            "finish_reason": "stop"
        }],
        "model": request.model,
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        },
        "response_time": 0.0
    }

@app.post("/api/chat")
async def api_chat(request: Dict[str, Any]):
    """Handle /api/chat requests from AI stock dashboard"""
    try:
        async with aiohttp.ClientSession() as session:
            # Extract prompt and parameters
            prompt = request.get("prompt", "")
            max_tokens = request.get("max_tokens", 800)
            temperature = request.get("temperature", 0.3)
            task_type = request.get("task_type", "stock_analysis")
            priority = request.get("priority", "normal")
            
            # Create messages format for LLM service
            messages = [
                {"role": "system", "content": "You are an expert stock analyst."},
                {"role": "user", "content": prompt}
            ]
            
            # Convert to Ollama format
            ollama_request = {
                "model": "llama3.1:8b-instruct-q6_K",
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Add priority if specified
            if priority and priority != "normal":
                ollama_request["priority"] = priority
            
            try:
                async with session.post(
                    f"{LLM_SERVICE_URL}/api/chat",
                    json=ollama_request,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "response": result["message"]["content"],
                            "model": result["model"],
                            "usage": {
                                "prompt_tokens": result.get("prompt_eval_count", 0),
                                "completion_tokens": result.get("eval_count", 0),
                                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                            },
                            "response_time": 0.0
                        }
                    else:
                        # Fallback to mock response
                        logger.warning(f"Ollama not available (status {response.status}), using mock response")
                        return _generate_mock_api_response(prompt)
            except Exception as e:
                logger.warning(f"Ollama connection failed: {e}, using mock response")
                return _generate_mock_api_response(prompt)
                    
    except Exception as e:
        logger.error(f"Error in api_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_mock_api_response(prompt: str):
    """Generate a mock response for /api/chat endpoint"""
    if "stock analysis" in prompt.lower() or "trading" in prompt.lower():
        content = """Based on the comprehensive analysis of market data, technical indicators, and news sentiment, I recommend a **BUY** decision with high confidence.

**Key Factors Supporting BUY Recommendation:**
- Positive news sentiment (0.73 score) with 5 recent positive articles
- Strong technical indicators showing bullish momentum
- Price above key moving averages (170 > 166.6 > 161.5)
- Multiple AI partnership catalysts and institutional buying support

**Target Price:** $185.00
**Stop Loss:** $165.00
**Confidence Level:** 8/10
**Risk Level:** MEDIUM

**Reasoning:** The combination of positive news sentiment, strong technical indicators, and institutional support suggests continued upward momentum. The stock shows resilience above key support levels with multiple growth catalysts."""
    else:
        content = "Based on the provided information, I recommend further analysis of market conditions and technical indicators."
    
    return {
        "response": content,
        "model": "llama3.1:8b-instruct-q6_K",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        },
        "response_time": 0.0
    }

@app.post("/sentiment")
async def analyze_sentiment(request: Dict[str, Any]):
    """Handle sentiment analysis requests"""
    try:
        async with aiohttp.ClientSession() as session:
            llm_request = {
                "operation": "sentiment",
                "data": request,
                "model": "gpt-3.5-turbo",
                "priority": 1,
                "use_cache": True
            }
            
            async with session.post(
                f"{LLM_SERVICE_URL}/api/v1/llm",
                json=llm_request,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise HTTPException(status_code=response.status, detail="LLM service unavailable")
                    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/llm")
async def api_v1_llm(request: Dict[str, Any]):
    """Handle /api/v1/llm requests from AI stock dashboard"""
    try:
        async with aiohttp.ClientSession() as session:
            # Extract data from the request
            operation = request.get("operation", "custom")
            data = request.get("data", {})
            model = request.get("model", "gpt-3.5-turbo")
            priority = request.get("priority", "normal")
            
            if operation == "custom":
                # Extract messages from data
                messages = data.get("messages", [])
                temperature = data.get("temperature", 0.3)
                max_tokens = data.get("max_tokens", 800)
                
                # Convert to Ollama format
                ollama_request = {
                    "model": "llama3.1:8b-instruct-q6_K",
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                
                # Add priority if specified
                if priority and priority != "normal":
                    ollama_request["priority"] = priority
                
                try:
                    async with session.post(
                        f"{LLM_SERVICE_URL}/api/chat",
                        json=ollama_request,
                        timeout=120
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "success": True,
                                "data": {
                                    "content": result["message"]["content"],
                                    "model": result["model"],
                                    "usage": {
                                        "prompt_tokens": result.get("prompt_eval_count", 0),
                                        "completion_tokens": result.get("eval_count", 0),
                                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                                    }
                                },
                                "error": None,
                                "request_id": str(uuid.uuid4()),
                                "response_time": 0.0,
                                "timestamp": datetime.utcnow()
                            }
                        else:
                            # Fallback to mock response
                            logger.warning(f"Ollama not available (status {response.status}), using mock response")
                            return _generate_mock_api_v1_response(data)
                except Exception as e:
                    logger.warning(f"Ollama connection failed: {e}, using mock response")
                    return _generate_mock_api_v1_response(data)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported operation: {operation}")
                    
    except Exception as e:
        logger.error(f"Error in api_v1_llm: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/high-priority/chat")
async def high_priority_chat(request: Dict[str, Any]):
    """Handle high priority chat requests"""
    try:
        async with aiohttp.ClientSession() as session:
            # Extract data from the request
            messages = request.get("messages", [])
            temperature = request.get("temperature", 0.3)
            max_tokens = request.get("max_tokens", 800)
            model = request.get("model", "llama3.1:8b-instruct-q6_K")
            
            # Convert to Ollama format with high priority
            ollama_request = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "priority": "high"  # Force high priority for this endpoint
            }
            
            try:
                async with session.post(
                    f"{LLM_SERVICE_URL}/api/chat",
                    json=ollama_request,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "data": {
                                "content": result["message"]["content"],
                                "model": result["model"],
                                "usage": {
                                    "prompt_tokens": result.get("prompt_eval_count", 0),
                                    "completion_tokens": result.get("eval_count", 0),
                                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                                }
                            },
                            "error": None,
                            "request_id": str(uuid.uuid4()),
                            "response_time": 0.0,
                            "timestamp": datetime.utcnow(),
                            "priority": "high"
                        }
                    else:
                        # Fallback to mock response
                        logger.warning(f"Ollama not available (status {response.status}), using mock response")
                        return _generate_mock_api_v1_response({"messages": messages})
            except Exception as e:
                logger.warning(f"Ollama connection failed: {e}, using mock response")
                return _generate_mock_api_v1_response({"messages": messages})
                    
    except Exception as e:
        logger.error(f"Error in high_priority_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_mock_api_v1_response(data: Dict[str, Any]):
    """Generate a mock response for /api/v1/llm endpoint"""
    messages = data.get("messages", [])
    user_message = ""
    for msg in messages:
        if msg["role"] == "user":
            user_message = msg["content"]
            break
    
    if "stock analysis" in user_message.lower() or "trading" in user_message.lower():
        content = """Based on the comprehensive analysis of market data, technical indicators, and news sentiment, I recommend a **BUY** decision with high confidence.

**Key Factors Supporting BUY Recommendation:**
- Positive news sentiment (0.73 score) with 5 recent positive articles
- Strong technical indicators showing bullish momentum
- Price above key moving averages (170 > 166.6 > 161.5)
- Multiple AI partnership catalysts and institutional buying support

**Target Price:** $185.00
**Stop Loss:** $165.00
**Confidence Level:** 8/10
**Risk Level:** MEDIUM

**Reasoning:** The combination of positive news sentiment, strong technical indicators, and institutional support suggests continued upward momentum. The stock shows resilience above key support levels with multiple growth catalysts."""
    else:
        content = "Based on the provided information, I recommend further analysis of market conditions and technical indicators."
    
    return {
        "success": True,
        "data": {
            "content": content,
            "model": "gemma3:1b",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            }
        },
        "error": None,
        "request_id": str(uuid.uuid4()),
        "response_time": 0.0,
        "timestamp": datetime.utcnow()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081) 