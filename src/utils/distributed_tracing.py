"""
Distributed Tracing System - OpenTelemetry integration with Jaeger
Provides comprehensive request tracking across all trading system services
"""

import os
import logging
import time
import uuid
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
from datetime import datetime

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.rabbitmq import RabbitMQInstrumentor
    from opentelemetry.instrumentation.prometheus_client import PrometheusClientInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-redis opentelemetry-instrumentation-rabbitmq opentelemetry-instrumentation-prometheus-client opentelemetry-exporter-jaeger")

logger = logging.getLogger(__name__)

class TracingConfig:
    """Configuration for distributed tracing"""
    
    def __init__(self):
        self.enabled = os.getenv('TRACING_ENABLED', 'true').lower() == 'true'
        self.service_name = os.getenv('SERVICE_NAME', 'trading-system')
        self.jaeger_host = os.getenv('JAEGER_HOST', 'jaeger.trading-system.svc.cluster.local')
        self.jaeger_port = int(os.getenv('JAEGER_PORT', '14268'))
        self.sample_rate = float(os.getenv('TRACE_SAMPLE_RATE', '1.0'))
        self.max_attributes = int(os.getenv('TRACE_MAX_ATTRIBUTES', '32'))
        self.max_events = int(os.getenv('TRACE_MAX_EVENTS', '128'))
        self.max_links = int(os.getenv('TRACE_MAX_LINKS', '32'))

class DistributedTracer:
    """Distributed tracing implementation"""
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self.tracer = None
        self.tracer_provider = None
        
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available. Tracing will be disabled.")
            return
            
        if config.enabled:
            self._setup_tracing()
    
    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": "1.0.0",
                "deployment.environment": os.getenv('ENVIRONMENT', 'development')
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(
                resource=resource,
                sampler=trace.sampling.PROBABILITY_SAMPLER(self.config.sample_rate)
            )
            
            # Set up Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_host,
                agent_port=self.config.jaeger_port,
            )
            
            # Add span processor
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            
            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            # Create tracer
            self.tracer = trace.get_tracer(self.config.service_name)
            
            logger.info(f"✅ Distributed tracing initialized for {self.config.service_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize tracing: {e}")
            self.tracer = None
    
    def get_tracer(self):
        """Get the tracer instance"""
        return self.tracer
    
    def get_current_span(self):
        """Get the current active span"""
        if not self.tracer:
            return None
        return trace.get_current_span()
    
    def get_trace_id(self):
        """Get current trace ID"""
        span = self.get_current_span()
        if span:
            return span.get_span_context().trace_id
        return None
    
    def get_span_id(self):
        """Get current span ID"""
        span = self.get_current_span()
        if span:
            return span.get_span_context().span_id
        return None
    
    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """Create a new span"""
        if not self.tracer:
            return None
        
        span = self.tracer.start_span(name, attributes=attributes or {})
        return span
    
    @contextmanager
    def span(self, name: str, attributes: Dict[str, Any] = None):
        """Context manager for creating spans"""
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            yield span
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """Add event to current span"""
        span = self.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span"""
        span = self.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def set_attributes(self, attributes: Dict[str, Any]):
        """Set multiple attributes on current span"""
        span = self.get_current_span()
        if span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

# Global tracer instance
tracer_config = TracingConfig()
distributed_tracer = DistributedTracer(tracer_config)

def trace_function(name: str = None, attributes: Dict[str, Any] = None):
    """Decorator to trace function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            # Add function info to attributes
            func_attributes = attributes or {}
            func_attributes.update({
                "function.name": func.__name__,
                "function.module": func.__module__,
                "function.args_count": len(args),
                "function.kwargs_count": len(kwargs)
            })
            
            with distributed_tracer.span(span_name, func_attributes) as span:
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if span:
                        span.set_attribute("function.duration", duration)
                        span.set_attribute("function.success", True)
                    
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error", str(e))
                        span.set_attribute("function.error_type", type(e).__name__)
                    raise
        return wrapper
    return decorator

def trace_request(request_id: str = None, service: str = None, operation: str = None):
    """Decorator to trace API requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate request ID if not provided
            if not request_id:
                req_id = str(uuid.uuid4())
            else:
                req_id = request_id
            
            # Determine span name
            span_name = operation or f"{func.__module__}.{func.__name__}"
            
            # Create attributes
            attributes = {
                "request.id": req_id,
                "service.name": service or distributed_tracer.config.service_name,
                "operation.name": span_name,
                "request.timestamp": datetime.utcnow().isoformat()
            }
            
            with distributed_tracer.span(span_name, attributes) as span:
                try:
                    start_time = time.time()
                    
                    # Add request info to span
                    if span:
                        span.set_attribute("request.start_time", start_time)
                    
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if span:
                        span.set_attribute("request.duration", duration)
                        span.set_attribute("request.success", True)
                    
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("request.success", False)
                        span.set_attribute("request.error", str(e))
                        span.set_attribute("request.error_type", type(e).__name__)
                    raise
        return wrapper
    return decorator

def trace_database_operation(operation: str, table: str = None, query: str = None):
    """Decorator to trace database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            span_name = f"database.{operation}"
            
            attributes = {
                "db.operation": operation,
                "db.system": "postgresql",
                "db.name": "trading_bot"
            }
            
            if table:
                attributes["db.table"] = table
            if query:
                attributes["db.statement"] = query
            
            with distributed_tracer.span(span_name, attributes) as span:
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if span:
                        span.set_attribute("db.duration", duration)
                        span.set_attribute("db.success", True)
                    
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("db.success", False)
                        span.set_attribute("db.error", str(e))
                        span.set_attribute("db.error_type", type(e).__name__)
                    raise
        return wrapper
    return decorator

def trace_external_api_call(service: str, endpoint: str, method: str = "GET"):
    """Decorator to trace external API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            span_name = f"http.{method.lower()}"
            
            attributes = {
                "http.method": method,
                "http.url": f"{service}/{endpoint}",
                "http.target": endpoint,
                "peer.service": service
            }
            
            with distributed_tracer.span(span_name, attributes) as span:
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if span:
                        span.set_attribute("http.duration", duration)
                        span.set_attribute("http.status_code", getattr(result, 'status_code', 200))
                        span.set_attribute("http.success", True)
                    
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("http.success", False)
                        span.set_attribute("http.error", str(e))
                        span.set_attribute("http.error_type", type(e).__name__)
                    raise
        return wrapper
    return decorator

def trace_message_queue(operation: str, queue: str, message_type: str = None):
    """Decorator to trace message queue operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            span_name = f"mq.{operation}"
            
            attributes = {
                "mq.operation": operation,
                "mq.queue": queue,
                "mq.system": "rabbitmq"
            }
            
            if message_type:
                attributes["mq.message_type"] = message_type
            
            with distributed_tracer.span(span_name, attributes) as span:
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if span:
                        span.set_attribute("mq.duration", duration)
                        span.set_attribute("mq.success", True)
                    
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("mq.success", False)
                        span.set_attribute("mq.error", str(e))
                        span.set_attribute("mq.error_type", type(e).__name__)
                    raise
        return wrapper
    return decorator

# Utility functions for manual tracing
def start_span(name: str, attributes: Dict[str, Any] = None):
    """Start a new span manually"""
    return distributed_tracer.create_span(name, attributes)

def add_event(name: str, attributes: Dict[str, Any] = None):
    """Add event to current span"""
    distributed_tracer.add_event(name, attributes)

def set_attribute(key: str, value: Any):
    """Set attribute on current span"""
    distributed_tracer.set_attribute(key, value)

def get_trace_id():
    """Get current trace ID"""
    return distributed_tracer.get_trace_id()

def get_span_id():
    """Get current span ID"""
    return distributed_tracer.get_span_id()

def get_trace_context():
    """Get current trace context for logging"""
    trace_id = get_trace_id()
    span_id = get_span_id()
    
    if trace_id and span_id:
        return {
            "trace_id": trace_id,
            "span_id": span_id
        }
    return {}



