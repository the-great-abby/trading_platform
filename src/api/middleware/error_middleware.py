"""
Error handling middleware
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Error handling middleware"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with error handling"""
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            return self._handle_http_exception(e)
        except ValueError as e:
            return self._handle_validation_error(e)
        except ConnectionError as e:
            return self._handle_database_error(e)
        except PermissionError as e:
            return self._handle_unauthorized_error(e)
        except Exception as e:
            return self._handle_internal_error(e)
    
    def _handle_http_exception(self, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "timestamp": time.time()
            }
        )
    
    def _handle_validation_error(self, exc: ValueError) -> JSONResponse:
        """Handle validation errors"""
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "message": str(exc),
                "timestamp": time.time()
            }
        )
    
    def _handle_database_error(self, exc: ConnectionError) -> JSONResponse:
        """Handle database errors"""
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "database_error",
                "message": "Database connection failed",
                "timestamp": time.time()
            }
        )
    
    def _handle_unauthorized_error(self, exc: PermissionError) -> JSONResponse:
        """Handle unauthorized errors"""
        logger.error(f"Unauthorized error: {exc}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": str(exc),
                "timestamp": time.time()
            }
        )
    
    def _handle_internal_error(self, exc: Exception) -> JSONResponse:
        """Handle internal server errors"""
        logger.error(f"Internal error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal server error occurred",
                "timestamp": time.time()
            }
        )
