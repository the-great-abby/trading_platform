"""
Metrics middleware
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Metrics collection middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "requests_total": 0,
            "response_time_seconds": 0.0,
            "errors_total": 0
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with metrics collection"""
        
        # Record request
        self.metrics["requests_total"] += 1
        start_time = time.time()
        
        try:
            response = await call_next(request)
            self._record_success(request, response, start_time)
            return response
        except Exception as e:
            self._record_error(request, e, start_time)
            raise
    
    def _record_success(self, request: Request, response: Response, start_time: float):
        """Record successful request metrics"""
        duration = time.time() - start_time
        self.metrics["response_time_seconds"] += duration
        
        logger.info(
            f"Request metrics: {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration
            }
        )
    
    def _record_error(self, request: Request, error: Exception, start_time: float):
        """Record error metrics"""
        duration = time.time() - start_time
        self.metrics["errors_total"] += 1
        
        logger.error(
            f"Error metrics: {request.method} {request.url.path} - {str(error)} - {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(error),
                "duration": duration
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
