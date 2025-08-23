#!/usr/bin/env python3
"""
Simple LLM Service for RAG Search
Handles AI generation requests from the unified analytics dashboard
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import time
import uuid
from datetime import datetime

app = FastAPI(title="LLM Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    priority: int = 10
    timeout_seconds: int = 300
    request_id: Optional[str] = None
    callback_url: Optional[str] = None
    callback_method: str = "POST"

class GenerateResponse(BaseModel):
    request_id: str
    status: str
    message: str
    timestamp: str

# Store pending requests (in a real service, this would be in a database)
pending_requests = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "llm-service", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Service",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/generate",
            "/api/status/{request_id}"
        ]
    }

@app.post("/api/generate")
async def generate_text(request: GenerateRequest):
    """Generate text using AI model (simplified for RAG search)"""
    try:
        # Generate a unique request ID if not provided
        if not request.request_id:
            request.request_id = str(uuid.uuid4())
        
        # Store the request
        pending_requests[request.request_id] = {
            "status": "processing",
            "prompt": request.prompt,
            "model": request.model,
            "created_at": datetime.now().isoformat(),
            "priority": request.priority
        }
        
        # For now, return a simple response indicating the request is being processed
        # In a real implementation, this would queue the request for actual AI processing
        
        return GenerateResponse(
            request_id=request.request_id,
            status="submitted",
            message="Request submitted for processing",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{request_id}")
async def get_request_status(request_id: str):
    """Get the status of a generation request"""
    if request_id not in pending_requests:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_data = pending_requests[request_id]
    
    # For demonstration, simulate completion after a delay
    created_time = datetime.fromisoformat(request_data["created_at"])
    elapsed = (datetime.now() - created_time).total_seconds()
    
    if elapsed > 10:  # Simulate completion after 10 seconds
        # Generate a simple AI response based on the prompt
        prompt = request_data["prompt"]
        response = generate_simple_ai_response(prompt)
        
        # Update the request status
        pending_requests[request_id]["status"] = "completed"
        pending_requests[request_id]["response"] = response
        pending_requests[request_id]["completed_at"] = datetime.now().isoformat()
        
        return {
            "request_id": request_id,
            "status": "completed",
            "response": response,
            "created_at": request_data["created_at"],
            "completed_at": pending_requests[request_id]["completed_at"]
        }
    else:
        return {
            "request_id": request_id,
            "status": "processing",
            "message": f"Request is being processed. Elapsed time: {elapsed:.1f}s",
            "created_at": request_data["created_at"]
        }

def generate_simple_ai_response(prompt: str) -> str:
    """Generate a simple AI response based on the prompt"""
    # This is a simplified response generator for demonstration
    # In a real service, this would call an actual AI model
    
    prompt_lower = prompt.lower()
    
    if "stock" in prompt_lower and "aapl" in prompt_lower:
        return """Based on the available data, AAPL stock has shown strong performance in recent quarters. The company continues to demonstrate solid fundamentals with strong iPhone sales, growing services revenue, and expanding into new markets like AI and augmented reality. However, as with any investment, it's important to consider current market conditions, valuation metrics, and your own risk tolerance before making investment decisions."""
    
    elif "market" in prompt_lower and "trend" in prompt_lower:
        return """The current market shows mixed trends with technology stocks experiencing volatility due to AI developments and interest rate concerns. Market sentiment appears cautious as investors weigh economic data against Federal Reserve policy decisions. It's important to maintain a diversified portfolio and consider both short-term market movements and long-term investment fundamentals."""
    
    elif "trading" in prompt_lower and "decision" in prompt_lower:
        return """Successful trading decisions typically involve thorough analysis of both technical and fundamental factors. Key considerations include market trends, company financials, risk management strategies, and maintaining emotional discipline. Remember that past performance doesn't guarantee future results, and it's crucial to have a well-defined trading plan with proper risk controls."""
    
    elif "news" in prompt_lower and "tsla" in prompt_lower:
        return """Recent news affecting TSLA includes developments in electric vehicle competition, autonomous driving technology advances, and regulatory changes in key markets. The company continues to innovate in battery technology and expand its global manufacturing footprint. Investors should monitor these developments as they can significantly impact stock performance."""
    
    else:
        return """I understand you're asking about financial markets and trading. While I can provide general guidance, specific investment decisions should be based on thorough research, consideration of your financial goals, and consultation with qualified financial advisors. The markets are complex and constantly evolving, so staying informed and maintaining a disciplined approach is key to long-term success."""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)

