"""
Logging middleware
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.api.config.logging_config import LoggingConfig

# Configure logger
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware"""
    
    def __init__(self, app, config: Optional[LoggingConfig] = None):
        super().__init__(app)
        self.config = config or LoggingConfig()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.level.value),
            format=self._get_log_format(),
            handlers=self._get_handlers()
        )
    
    def _get_log_format(self) -> str:
        """Get log format string"""
        if self.config.format.value == "JSON":
            return '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        else:
            return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def _get_handlers(self) -> list:
        """Get logging handlers"""
        handlers = []
        
        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            handlers.append(console_handler)
        
        if self.config.enable_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.config.file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            handlers.append(file_handler)
        
        return handlers
    
    async def dispatch(self, request: Request, call_next):
        """Process request with logging"""
        
        # Log request
        start_time = time.time()
        self._log_request(request)
        
        # Process request
        try:
            response = await call_next(request)
            self._log_response(request, response, start_time)
            return response
        except Exception as e:
            self._log_error(request, e, start_time)
            raise
    
    def _log_request(self, request: Request):
        """Log incoming request"""
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
    
    def _log_response(self, request: Request, response: Response, start_time: float):
        """Log response"""
        duration = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} in {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
    
    def _log_error(self, request: Request, error: Exception, start_time: float):
        """Log error"""
        duration = time.time() - start_time
        logger.error(
            f"Error: {str(error)} in {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(error),
                "duration": duration,
                "client_ip": request.client.host if request.client else "unknown"
            },
            exc_info=True
        )
