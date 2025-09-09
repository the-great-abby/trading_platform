"""
Rate limiting middleware
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.api.config.security_config import RateLimitConfig


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.rate_limit_config = RateLimitConfig(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour
        )
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            response = await call_next(request)
            return response
        
        # Get client identifier
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_id, current_time)
        
        # Check rate limits
        if self._is_rate_limited(client_id, current_time):
            return Response(
                content='{"error": "rate_limit", "message": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
        
        # Record request
        self._record_request(client_id, current_time)
        
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use IP address as client identifier
        client_ip = request.client.host if request.client else "unknown"
        return client_ip
    
    def _clean_old_requests(self, client_id: str, current_time: float):
        """Clean old requests from tracking"""
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove requests older than 1 hour
        cutoff_time = current_time - 3600
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]
    
    def _is_rate_limited(self, client_id: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_id not in self.requests:
            return False
        
        client_requests = self.requests[client_id]
        
        # Check per-minute limit
        minute_ago = current_time - 60
        recent_requests = [req_time for req_time in client_requests if req_time > minute_ago]
        if len(recent_requests) >= self.requests_per_minute:
            return True
        
        # Check per-hour limit
        hour_ago = current_time - 3600
        hourly_requests = [req_time for req_time in client_requests if req_time > hour_ago]
        if len(hourly_requests) >= self.requests_per_hour:
            return True
        
        return False
    
    def _record_request(self, client_id: str, current_time: float):
        """Record a request for rate limiting"""
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        self.requests[client_id].append(current_time)
