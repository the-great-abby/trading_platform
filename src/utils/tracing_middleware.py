"""
FastAPI Tracing Middleware - Automatic request tracing and correlation
Integrates with distributed tracing system for comprehensive request tracking
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

from .distributed_tracing import (
    distributed_tracer, 
    trace_request, 
    get_trace_context,
    set_attribute,
    add_event
)

logger = logging.getLogger(__name__)

class TracingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic request tracing"""
    
    def __init__(self, app: ASGIApp, service_name: str = None):
        super().__init__(app)
        self.service_name = service_name or "trading-service"
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with automatic tracing"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        
        # Create span attributes
        attributes = {
            "http.method": method,
            "http.url": url,
            "http.path": path,
            "http.request_id": request_id,
            "service.name": self.service_name,
            "http.user_agent": headers.get("user-agent", ""),
            "http.content_length": headers.get("content-length", "0"),
            "http.host": headers.get("host", ""),
            "http.scheme": request.url.scheme,
            "http.target": path
        }
        
        # Add query parameters if present
        if query_params:
            attributes["http.query_params"] = str(query_params)
        
        # Add important headers
        important_headers = ["authorization", "content-type", "accept", "x-forwarded-for"]
        for header in important_headers:
            if header in headers:
                attributes[f"http.header.{header}"] = headers[header]
        
        # Start span for request
        span_name = f"http.{method.lower()}"
        
        with distributed_tracer.span(span_name, attributes) as span:
            try:
                # Add request start event
                add_event("request.start", {
                    "request_id": request_id,
                    "timestamp": time.time()
                })
                
                # Set request ID in headers for downstream services
                request.headers.__dict__["_list"].append(
                    (b"x-request-id", request_id.encode())
                )
                
                # Add trace context to headers
                trace_context = get_trace_context()
                if trace_context.get("trace_id"):
                    request.headers.__dict__["_list"].append(
                        (b"x-trace-id", str(trace_context["trace_id"]).encode())
                    )
                if trace_context.get("span_id"):
                    request.headers.__dict__["_list"].append(
                        (b"x-span-id", str(trace_context["span_id"]).encode())
                    )
                
                # Process request
                start_time = time.time()
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Add response information to span
                if span:
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_size", len(response.body) if hasattr(response, 'body') else 0)
                    span.set_attribute("http.duration", duration)
                    span.set_attribute("http.success", response.status_code < 400)
                
                # Add response headers
                response_headers = dict(response.headers)
                if "content-type" in response_headers:
                    span.set_attribute("http.response.content_type", response_headers["content-type"])
                if "content-length" in response_headers:
                    span.set_attribute("http.response.content_length", response_headers["content-length"])
                
                # Add request end event
                add_event("request.end", {
                    "request_id": request_id,
                    "duration": duration,
                    "status_code": response.status_code,
                    "timestamp": time.time()
                })
                
                # Add request ID to response headers
                response.headers["x-request-id"] = request_id
                
                return response
                
            except Exception as e:
                # Add error information to span
                if span:
                    span.set_attribute("http.error", str(e))
                    span.set_attribute("http.error_type", type(e).__name__)
                    span.set_attribute("http.success", False)
                
                # Add error event
                add_event("request.error", {
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": time.time()
                })
                
                logger.error(f"Request failed: {request_id} - {e}")
                raise

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation IDs across services"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with correlation ID handling"""
        
        # Extract correlation ID from headers
        correlation_id = request.headers.get("x-correlation-id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Extract trace context from headers
        trace_id = request.headers.get("x-trace-id")
        span_id = request.headers.get("x-span-id")
        
        # Set correlation context
        set_attribute("correlation.id", correlation_id)
        if trace_id:
            set_attribute("trace.parent_id", trace_id)
        if span_id:
            set_attribute("span.parent_id", span_id)
        
        # Add correlation ID to request context
        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["x-correlation-id"] = correlation_id
        
        return response

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track performance metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with performance tracking"""
        
        start_time = time.time()
        
        # Track request start
        add_event("performance.request_start", {
            "path": request.url.path,
            "method": request.method,
            "timestamp": start_time
        })
        
        try:
            # Process request
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Track successful request
            add_event("performance.request_end", {
                "path": request.url.path,
                "method": request.method,
                "duration": duration,
                "status_code": response.status_code,
                "timestamp": time.time()
            })
            
            # Set performance attributes
            set_attribute("performance.duration", duration)
            set_attribute("performance.status_code", response.status_code)
            set_attribute("performance.success", response.status_code < 400)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Track failed request
            add_event("performance.request_error", {
                "path": request.url.path,
                "method": request.method,
                "duration": duration,
                "error": str(e),
                "timestamp": time.time()
            })
            
            # Set error attributes
            set_attribute("performance.duration", duration)
            set_attribute("performance.error", str(e))
            set_attribute("performance.success", False)
            
            raise

def setup_tracing_middleware(app, service_name: str = None):
    """Setup tracing middleware for FastAPI app"""
    
    # Add correlation middleware first
    app.add_middleware(CorrelationMiddleware)
    
    # Add performance middleware
    app.add_middleware(PerformanceMiddleware)
    
    # Add tracing middleware last
    app.add_middleware(TracingMiddleware, service_name=service_name)
    
    logger.info(f"✅ Tracing middleware setup complete for {service_name or 'trading-service'}")

def get_request_context(request: Request) -> Dict[str, Any]:
    """Get request context for logging"""
    context = {
        "request_id": getattr(request.state, 'correlation_id', None),
        "path": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None
    }
    
    # Add trace context
    trace_context = get_trace_context()
    context.update(trace_context)
    
    return context

def log_request(request: Request, level: str = "info"):
    """Log request with full context"""
    context = get_request_context(request)
    
    log_message = f"Request: {request.method} {request.url.path}"
    
    if level == "info":
        logger.info(log_message, extra=context)
    elif level == "debug":
        logger.debug(log_message, extra=context)
    elif level == "warning":
        logger.warning(log_message, extra=context)
    elif level == "error":
        logger.error(log_message, extra=context)



